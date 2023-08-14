######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom QTreeView.
"""
import pickle

from PySide6.QtWidgets import QApplication, QMenu, QAbstractItemView
from PySide6.QtCore import Signal, Slot, Qt, QEvent, QTimer, QModelIndex, QItemSelection, QSignalBlocker
from PySide6.QtGui import QMouseEvent, QIcon, QGuiApplication

from spinetoolbox.widgets.custom_qtreeview import CopyPasteTreeView
from spinetoolbox.helpers import busy_effect, CharIconEngine
from spinetoolbox.widgets.custom_qwidgets import ResizingViewMixin
from .custom_delegates import ScenarioDelegate, ToolFeatureDelegate, AlternativeDelegate, ParameterValueListDelegate
from .scenario_generator import ScenarioGenerator
from ..mvcmodels import mime_types
from ..mvcmodels.alternative_item import AlternativeItem
from ..mvcmodels.scenario_item import ScenarioDBItem, ScenarioAlternativeItem, ScenarioItem


class ResizableTreeView(ResizingViewMixin, CopyPasteTreeView):
    def _do_resize(self):
        self.resizeColumnToContents(0)


class EntityTreeView(ResizableTreeView):
    """Tree view base class for object and relationship tree views."""

    relationship_selection_changed = Signal(dict, bool)
    object_selection_changed = Signal(dict, bool)

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._context_item = None
        self._selected_indexes = {}
        self._menu = QMenu(self)
        self._spine_db_editor = None
        self._fully_expand_action = None
        self._fully_collapse_action = None
        self._add_relationship_classes_action = None
        self._add_relationships_action = None
        self._manage_relationships_action = None
        self._export_action = None
        self._edit_action = None
        self._remove_action = None
        self._cube_plus_icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        self._cube_minus_icon = QIcon(":/icons/menu_icons/cube_minus.svg")
        self._cube_pen_icon = QIcon(":/icons/menu_icons/cube_pen.svg")
        self._cubes_plus_icon = QIcon(":/icons/menu_icons/cubes_plus.svg")
        self._cubes_pen_icon = QIcon(":/icons/menu_icons/cubes_pen.svg")
        self._fetch_more_timer = QTimer(self)
        self._fetch_more_timer.setSingleShot(True)
        self._fetch_more_timer.setInterval(100)
        self._fetch_more_timer.timeout.connect(self._fetch_more_visible)

    def reset(self):
        super().reset()
        self._selected_indexes = {}

    def connect_spine_db_editor(self, spine_db_editor):
        """Connects a Spine db editor to work with this view.

        Args:
             spine_db_editor (SpineDBEditor)
        """
        self._spine_db_editor = spine_db_editor
        self._create_context_menu()
        self.connect_signals()

    def _add_middle_actions(self):
        """Adds action at the middle of the context menu.
        Subclasses can reimplement at will.
        """

    def _create_context_menu(self):
        """Creates a context menu for this view."""
        self._menu.addAction(self._spine_db_editor.ui.actionCopy)
        self._menu.addSeparator()
        self._add_middle_actions()
        self._menu.addSeparator()
        self._edit_action = self._menu.addAction(self._cube_pen_icon, "Edit...", self.edit_selected)
        self._remove_action = self._menu.addAction(self._cube_minus_icon, "Remove...", self.remove_selected)
        self._menu.addSeparator()
        self._export_action = self._menu.addAction(
            QIcon(":/icons/menu_icons/database-export.svg"), "Export", self.export_selected
        )
        self._menu.addSeparator()
        self._fully_expand_action = self._menu.addAction(
            QIcon(CharIconEngine("\uf101")), "Fully expand", self.fully_expand
        )
        self._fully_collapse_action = self._menu.addAction(
            QIcon(CharIconEngine("\uf100")), "Fully collapse", self.fully_collapse
        )

    @Slot(QModelIndex, int, QEvent)
    def edit(self, index, trigger, event):
        """Edit all selected items."""
        if trigger == QAbstractItemView.EditTrigger.EditKeyPressed:
            self.edit_selected()
            return True
        return super().edit(index, trigger, event)

    def connect_signals(self):
        """Connects signals."""
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self._refresh_selected_indexes()

    def rowsRemoved(self, parent, start, end):
        super().rowsRemoved(parent, start, end)
        self._refresh_selected_indexes()

    def setModel(self, model):
        old_model = self.model()
        if old_model:
            old_model.layoutChanged.disconnect(self._fetch_more_timer.start)
        super().setModel(model)
        model.layoutChanged.connect(self._fetch_more_timer.start)

    @Slot()
    def _fetch_more_visible(self):
        model = self.model()
        for item in model.visit_all(view=self):
            index = model.index_from_item(item)
            last = model.index(model.rowCount(index) - 1, 0, index)
            if self.visualRect(last).intersects(self.viewport().rect()) and model.canFetchMore(index):
                model.fetchMore(index)

    def verticalScrollbarValueChanged(self, value):
        super().verticalScrollbarValueChanged(value)
        self._fetch_more_timer.start()

    @Slot(QItemSelection, QItemSelection)
    def _handle_selection_changed(self, selected, deselected):
        """Classifies selection by item type and emits signal."""
        self._spine_db_editor.refresh_copy_paste_actions()
        self._refresh_selected_indexes()
        self.object_selection_changed.emit(self._selected_indexes, True)
        self.relationship_selection_changed.emit(self._selected_indexes, False)

    def _refresh_selected_indexes(self):
        self._selected_indexes.clear()
        model = self.model()
        indexes = self.selectionModel().selectedIndexes()
        for index in indexes:
            if not index.isValid() or index.column() != 0:
                continue
            item = model.item_from_index(index)
            self._selected_indexes.setdefault(item.item_type, {})[index] = None

    def clear_any_selections(self):
        """Clears the selection if any."""
        selection_model = self.selectionModel()
        if Qt.KeyboardModifier.ControlModifier in QGuiApplication.keyboardModifiers():
            return
        if selection_model.hasSelection():
            with QSignalBlocker(selection_model) as _:
                selection_model.clearSelection()

    @busy_effect
    def fully_expand(self):
        """Expands selected indexes and all their children."""
        model = self.model()
        indexes = [index for index in self.selectionModel().selectedIndexes() if index.column() == 0]
        for index in indexes:
            for item in model.visit_all(index):
                self.expand(model.index_from_item(item))

    @busy_effect
    def fully_collapse(self):
        """Collapses selected indexes and all their children."""
        model = self.model()
        indexes = [index for index in self.selectionModel().selectedIndexes() if index.column() == 0]
        for index in indexes:
            for item in model.visit_all(index):
                self.collapse(model.index_from_item(item))

    def export_selected(self):
        """Exports data from selected indexes using the connected Spine db editor."""
        self._spine_db_editor.export_selected(self._selected_indexes)

    def remove_selected(self):
        """Removes selected indexes using the connected Spine db editor."""
        self._spine_db_editor.remove_entity_tree_items(self._selected_indexes)

    def manage_relationships(self):
        self._spine_db_editor.show_manage_relationships_form(self._context_item)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        if index.column() != 0:
            return
        self._context_item = self.model().item_from_index(index)
        self.update_actions_availability()
        self._menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        """Overrides selection behaviour if the user has selected sticky selection in Settings.
        If sticky selection is enabled, multiple-selection is enabled when selecting items in the Object tree.
        Pressing the Ctrl-button down, enables single selection.

        Args:
            event (QMouseEvent)
        """
        sticky_selection = self._spine_db_editor.qsettings.value("appSettings/stickySelection", defaultValue="false")
        if sticky_selection == "false":
            super().mousePressEvent(event)
            return
        local_pos = event.localPos()
        window_pos = event.windowPos()
        screen_pos = event.screenPos()
        button = event.button()
        buttons = event.buttons()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            modifiers &= ~Qt.ControlModifier
        else:
            modifiers |= Qt.ControlModifier
        source = event.source()
        new_event = QMouseEvent(
            QEvent.MouseButtonPress, local_pos, window_pos, screen_pos, button, buttons, modifiers, source
        )
        super().mousePressEvent(new_event)

    def _add_relationship_actions(self):
        self._add_relationship_classes_action = self._menu.addAction(
            self._cubes_plus_icon, "Add relationship classes", self.add_relationship_classes
        )
        self._add_relationships_action = self._menu.addAction(
            self._cubes_plus_icon, "Add relationships", self.add_relationships
        )
        self._manage_relationships_action = self._menu.addAction(
            self._cubes_pen_icon, "Manage relationships", self.manage_relationships
        )

    def update_actions_availability(self):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        item = self._context_item
        item_has_children = item.has_children()
        self._fully_expand_action.setEnabled(item_has_children)
        self._fully_collapse_action.setEnabled(item_has_children)
        self._add_relationships_action.setEnabled(item.item_type == "relationship_class")
        self._manage_relationships_action.setEnabled(item.item_type in ("root", "relationship_class"))
        read_only = item.item_type in ("root", "members")
        self._export_action.setEnabled(not read_only)
        self._edit_action.setEnabled(not read_only)
        self._remove_action.setEnabled(not read_only)

    def edit_selected(self):
        """Edits all selected indexes using the connected Spine db editor."""
        self._spine_db_editor.edit_entity_tree_items(self._selected_indexes)


class ObjectTreeView(EntityTreeView):
    """Custom QTreeView class for the object tree in SpineDBEditor."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._add_objects_action = None
        self._add_object_classes_action = None
        self._add_object_group_action = None
        self._manage_members_action = None
        self._duplicate_object_action = None
        self._find_next_action = None
        self._relationship_index = None

    def update_actions_availability(self):
        super().update_actions_availability()
        item = self._context_item
        self._add_object_classes_action.setEnabled(item.item_type == "root")
        self._add_objects_action.setEnabled(item.item_type in ("root", "object_class"))
        self._add_object_group_action.setEnabled(item.item_type == "object_class")
        self._add_relationship_classes_action.setEnabled(item.item_type in ("root", "object_class"))
        self._manage_members_action.setEnabled(item.item_type == "members")
        self._duplicate_object_action.setEnabled(item.item_type == "object" and not item.is_group)
        self._find_next_action.setEnabled(item.item_type == "relationship")

    def _add_middle_actions(self):
        self._add_object_classes_action = self._menu.addAction(
            self._cube_plus_icon, "Add object classes", self.add_object_classes
        )
        self._add_objects_action = self._menu.addAction(self._cube_plus_icon, "Add objects", self.add_objects)
        self._add_relationship_actions()
        self._menu.addSeparator()
        self._find_next_action = self._menu.addAction(
            QIcon(CharIconEngine("\uf141")), "Find next relationship", self.find_next_relationship
        )
        self._add_object_group_action = self._menu.addAction(
            self._cube_plus_icon, "Add object group", self.add_object_group
        )
        self._manage_members_action = self._menu.addAction(self._cube_pen_icon, "Manage members", self.manage_members)
        self._duplicate_object_action = self._menu.addAction(
            self._cube_plus_icon, "Duplicate object", self.duplicate_object
        )

    def connect_signals(self):
        super().connect_signals()
        self.doubleClicked.connect(self.find_next_relationship)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self._do_find_next_relationship()

    def add_object_classes(self):
        self._spine_db_editor.show_add_object_classes_form()

    def add_objects(self):
        self._spine_db_editor.show_add_objects_form(self._context_item)

    def add_relationship_classes(self):
        self._spine_db_editor.show_add_relationship_classes_form(self._context_item)

    def add_relationships(self):
        self._spine_db_editor.show_add_relationships_form(self._context_item)

    def find_next_relationship(self):
        """Finds the next occurrence of the relationship at the current index and expands it."""
        self._relationship_index = self.currentIndex()
        self._do_find_next_relationship()

    def _do_find_next_relationship(self):
        if self._relationship_index is None:
            return
        next_index = self.model().find_next_relationship_index(self._relationship_index)
        if not next_index:
            return
        self._relationship_index = None
        self.setCurrentIndex(next_index)
        self.scrollTo(next_index)
        self.expand(next_index)

    def duplicate_object(self):
        """Duplicates the object at the current index using the connected Spine db editor."""
        object_item = self.currentIndex().internalPointer()
        self._spine_db_editor.duplicate_object(object_item)

    def add_object_group(self):
        index = self.currentIndex()
        item = index.internalPointer()
        self._spine_db_editor.show_add_object_group_form(item)

    def manage_members(self):
        index = self.currentIndex()
        item = index.internalPointer().parent_item
        self._spine_db_editor.show_manage_members_form(item)


class RelationshipTreeView(EntityTreeView):
    """Custom QTreeView class for the relationship tree in SpineDBEditor."""

    def _add_middle_actions(self):
        self._add_relationship_actions()

    def update_actions_availability(self):
        super().update_actions_availability()
        item = self._context_item
        self._add_relationship_classes_action.setEnabled(item.item_type == "root")

    def add_relationship_classes(self):
        self._spine_db_editor.show_add_relationship_classes_form(self._context_item)

    def add_relationships(self):
        self._spine_db_editor.show_add_relationships_form(self._context_item)


class ItemTreeView(ResizableTreeView):
    """Base class for all non-entity tree views."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._spine_db_editor = None
        self._menu = QMenu(self)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self.resizeColumnToContents(0)

    def connect_signals(self):
        """Connects signals."""
        self.selectionModel().selectionChanged.connect(self._refresh_copy_paste_actions)

    def remove_selected(self):
        """Removes items selected in the view."""
        raise NotImplementedError()

    def update_actions_availability(self, item):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        raise NotImplementedError()

    def connect_spine_db_editor(self, spine_db_editor):
        """Prepares the view to work with the DB editor.

        Args:
            spine_db_editor (SpineDBEditor): editor instance
        """
        self._spine_db_editor = spine_db_editor
        self.populate_context_menu()
        self.connect_signals()

    def populate_context_menu(self):
        """Creates a context menu for this view."""
        self._menu.addAction(self._spine_db_editor.ui.actionCopy)
        self._menu.addAction(self._spine_db_editor.ui.actionPaste)
        self._menu.addAction("Remove", self.remove_selected)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        if index.column() != 0:
            return
        item = index.model().item_from_index(index)
        self.update_actions_availability(item)
        self._menu.exec(event.globalPos())

    @Slot(QModelIndex, QModelIndex)
    def _refresh_copy_paste_actions(self, _, __):
        """Refreshes copy and paste actions enabled state."""
        self._spine_db_editor.refresh_copy_paste_actions()


class ToolFeatureTreeView(ItemTreeView):
    """Custom QTreeView class for tools and features in SpineDBEditor."""

    def connect_spine_db_editor(self, spine_db_editor):
        """see base class"""
        super().connect_spine_db_editor(spine_db_editor)
        delegate = ToolFeatureDelegate(self._spine_db_editor)
        delegate.data_committed.connect(self.model().setData)
        self.setItemDelegateForColumn(0, delegate)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {
                "feature": set(),
                "tool": set(),
                "tool_feature": set(),
                "tool_feature_method": set(),
            }
            for feat_item in reversed(db_item.child(0).children[:-1]):
                if feat_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["feature"].add(feat_item.id)
            for tool_item in reversed(db_item.child(1).children[:-1]):
                if tool_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["tool"].add(tool_item.id)
                    continue
                tool_feat_root_item = tool_item.child(0)
                for tool_feat_item in reversed(tool_feat_root_item.children):
                    if tool_feat_item in items:
                        db_map_typed_data_to_rm[db_item.db_map]["tool_feature"].add(tool_feat_item.id)
                        continue
                    tool_feat_meth_root_item = tool_feat_item.child(1)
                    if tool_feat_meth_root_item is None:
                        continue
                    for tool_feat_meth_item in reversed(tool_feat_meth_root_item.children):
                        if tool_feat_meth_item in items:
                            db_map_typed_data_to_rm[db_item.db_map]["tool_feature_method"].add(tool_feat_meth_item.id)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def update_actions_availability(self, item):
        """See base class."""

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        index = self.indexAt(event.position().toPoint())
        item = self.model().item_from_index(index)
        if item and item.item_type == "tool":
            self.expand(index)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.source() is self:
            event.accept()


class AlternativeTreeView(ItemTreeView):
    """Custom QTreeView for the alternative tree in SpineDBEditor."""

    alternative_selection_changed = Signal(object)

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._selected_alternative_ids = dict()
        self._generate_scenarios_action = None

    @property
    def selected_alternative_ids(self):
        return self._selected_alternative_ids

    def reset(self):
        super().reset()
        self._selected_alternative_ids.clear()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    def connect_spine_db_editor(self, spine_db_editor):
        """see base class"""
        super().connect_spine_db_editor(spine_db_editor)
        delegate = AlternativeDelegate(self._spine_db_editor)
        delegate.data_committed.connect(self.model().setData)
        self.setItemDelegateForColumn(0, delegate)

    def populate_context_menu(self):
        """See base class."""
        self._generate_scenarios_action = self._menu.addAction("Generate scenarios...", self._open_scenario_generator)
        self._menu.addSeparator()
        super().populate_context_menu()

    def _db_map_alt_ids_from_selection(self, selection):
        """Gather alternative ids per database map from selection.

        Args:
            selection (QItemSelection): selection

        Returns:
            dict: mapping from database map to set of alternative ids
        """
        db_map_ids = {}
        for index in selection.indexes():
            if index.column() != 0:
                continue
            item = self.model().item_from_index(index)
            if isinstance(item, AlternativeItem) and item.id is not None:
                db_map_ids.setdefault(item.db_map, set()).add(item.id)
        return db_map_ids

    @Slot(QItemSelection, QItemSelection)
    def _handle_selection_changed(self, selected, deselected):
        """Emits alternative_selection_changed with the current selection."""
        selected_db_map_alt_ids = self._db_map_alt_ids_from_selection(selected)
        deselected_db_map_alt_ids = self._db_map_alt_ids_from_selection(deselected)
        for db_map, ids in deselected_db_map_alt_ids.items():
            self._selected_alternative_ids[db_map].difference_update(ids)
        for db_map, ids in selected_db_map_alt_ids.items():
            self._selected_alternative_ids.setdefault(db_map, set()).update(ids)
        self.alternative_selection_changed.emit(self._selected_alternative_ids)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"alternative": set()}
            for alt_item in db_item.children[:-1]:
                if alt_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["alternative"].add(alt_item.id)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def update_actions_availability(self, item):
        """See base class."""
        self._generate_scenarios_action.setEnabled(
            isinstance(item, AlternativeItem) and bool(self._selected_alternative_ids.get(item.db_map))
        )

    def _open_scenario_generator(self):
        """Opens the scenario generator dialog."""
        item = self.model().item_from_index(self.currentIndex())
        if not isinstance(item, AlternativeItem):
            return
        included_ids = set()
        alternatives = list()
        db_map = item.db_map
        for id_ in self._selected_alternative_ids.get(db_map, ()):
            if id_ not in included_ids:
                alternatives.append(self._spine_db_editor.db_mngr.get_item(db_map, "alternative", id_))
                included_ids.add(id_)
        generator = ScenarioGenerator(self, db_map, alternatives, self._spine_db_editor)
        generator.show()

    def can_copy(self):
        """See base class."""
        selection = self.selectionModel().selection()
        if selection.isEmpty():
            return False
        model = self.model()
        for index in selection.indexes():
            item = model.item_from_index(index)
            if isinstance(item, AlternativeItem) and item.id is not None:
                return True
        return False

    def can_paste(self):
        """See base class."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data is None or not mime_data.hasFormat(mime_types.ALTERNATIVE_DATA):
            return False
        return True

    def copy(self):
        """See base class."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        model = self.model()
        indexes = []
        for index in selection.indexes():
            item = model.item_from_index(index)
            if not isinstance(item, AlternativeItem) or item.id is None:
                continue
            indexes.append(index)
        if not indexes:
            return False
        mime_data = self.model().mimeData(indexes)
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        return True

    def paste(self):
        """Pastes alternatives from clipboard to the tree.

        This makes sense only when pasting alternatives from one database to another.
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data is None or not mime_data.hasFormat(mime_types.ALTERNATIVE_DATA):
            return
        index = self.selectionModel().currentIndex()
        model = self.model()
        item = model.item_from_index(index)
        if isinstance(item, AlternativeItem):
            item = item.parent_item
        model.paste_alternative_mime_data(mime_data, item)


class ScenarioTreeView(ItemTreeView):
    """Custom QTreeView for the scenario tree in SpineDBEditor."""

    scenario_selection_changed = Signal(object)

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._selected_alternative_ids = dict()
        self._duplicate_scenario_action = None

    @property
    def selected_alternative_ids(self):
        return self._selected_alternative_ids

    def reset(self):
        super().reset()
        self._selected_alternative_ids.clear()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    def connect_spine_db_editor(self, spine_db_editor):
        """see base class"""
        super().connect_spine_db_editor(spine_db_editor)
        delegate = ScenarioDelegate(self._spine_db_editor)
        delegate.data_committed.connect(self.model().setData)
        self.setItemDelegateForColumn(0, delegate)

    def populate_context_menu(self):
        """See base class."""
        super().populate_context_menu()
        self._duplicate_scenario_action = self._menu.addAction("Duplicate", self._duplicate_scenario)

    def _db_map_alternative_ids_from_selection(self, selection):
        """Collects database maps and alternative ids within given selection.

        Args:
            selection (Sequence of QModelIndex): selection indices

        Returns:
            dict: mapping from database map to set of alternative ids
        """
        db_map_ids = {}
        for index in selection.indexes():
            if index.column() != 0:
                continue
            item = self.model().item_from_index(index)
            if isinstance(item, ScenarioItem) and item.id is not None:
                db_map_ids.setdefault(item.db_map, set()).update(item.alternative_id_list)
            elif isinstance(item, ScenarioAlternativeItem) and item.alternative_id is not None:
                db_map_ids.setdefault(item.db_map, set()).add(item.alternative_id)
        return db_map_ids

    @Slot(QItemSelection, QItemSelection)
    def _handle_selection_changed(self, selected, deselected):
        """Emits scenario_selection_changed with the current selection."""
        self._selected_alternative_ids.clear()
        for index in self.selectionModel().selectedRows(column=0):
            item = self.model().item_from_index(index)
            if isinstance(item, ScenarioItem) and item.id is not None:
                self._selected_alternative_ids.setdefault(item.db_map, set()).update(item.alternative_id_list)
            elif isinstance(item, ScenarioAlternativeItem) and item.alternative_id is not None:
                self._selected_alternative_ids.setdefault(item.db_map, set()).add(item.alternative_id)
        self.scenario_selection_changed.emit(self._selected_alternative_ids)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        db_map_scen_alt_data = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"scenario": set()}
            db_map_scen_alt_data[db_item.db_map] = []
            for scen_item in db_item.children[:-1]:
                if scen_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["scenario"].add(scen_item.id)
                    continue
                if not scen_item.non_empty_children:
                    continue
                curr_alt_id_list = list(scen_item.alternative_id_list)
                new_alt_id_list = [
                    id_
                    for alt_item, id_ in zip(scen_item.non_empty_children, curr_alt_id_list)
                    if alt_item not in items
                ]
                if new_alt_id_list != curr_alt_id_list:
                    item = {"id": scen_item.id, "alternative_id_list": new_alt_id_list}
                    db_map_scen_alt_data[db_item.db_map].append(item)
        self.model().db_mngr.set_scenario_alternatives(db_map_scen_alt_data)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        index = self.indexAt(event.position().toPoint())
        item = self.model().item_from_index(index)
        if item and item.item_type == "scenario":
            self.expand(index)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.source() is self:
            event.accept()

    def update_actions_availability(self, item):
        """See base class"""
        self._duplicate_scenario_action.setEnabled(isinstance(item, ScenarioItem) and item.id is not None)

    def copy(self):
        """See base class."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        model = self.model()
        mime_data = model.mimeData(selection.indexes())
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        return True

    def can_paste(self):
        """See base class."""
        index = self.selectionModel().currentIndex()
        model = self.model()
        item = model.item_from_index(index)
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data is None:
            return False
        if mime_data.hasFormat(mime_types.ALTERNATIVE_DATA):
            if isinstance(item, ScenarioItem):
                return item.id is not None
            return isinstance(item, ScenarioAlternativeItem)
        if mime_data.hasFormat(mime_types.SCENARIO_DATA):
            return isinstance(item, (ScenarioDBItem, ScenarioItem))
        return False

    def paste(self):
        """Pastes alternatives and scenarios from clipboard to the tree."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data is None:
            return
        index = self.selectionModel().currentIndex()
        model = self.model()
        item = model.item_from_index(index)
        if mime_data.hasFormat(mime_types.ALTERNATIVE_DATA):
            if isinstance(item, ScenarioAlternativeItem):
                target_row = index.row()
                scenario_item = item.parent_item
            elif isinstance(item, ScenarioItem):
                target_row = -1
                scenario_item = item
            else:
                return
            if scenario_item.id is None:
                return
            model.paste_alternative_mime_data(mime_data, target_row, scenario_item)
        elif mime_data.hasFormat(mime_types.SCENARIO_DATA):
            if isinstance(item, ScenarioItem):
                database_item = item.parent_item
            elif isinstance(item, ScenarioDBItem):
                database_item = item
            else:
                return
            model.paste_scenario_mime_data(mime_data, database_item)

    def _duplicate_scenario(self):
        """Duplicates selected scenarios."""
        selection = self.selectionModel().selection()
        if selection.isEmpty():
            return
        model = self.model()
        # Remove duplicates while keeping the order.
        items = list(dict.fromkeys(model.item_from_index(index) for index in selection.indexes()))
        for item in items:
            if not isinstance(item, ScenarioItem) or item.id is None:
                continue
            model.duplicate_scenario(item)


class ParameterValueListTreeView(ItemTreeView):
    """Custom QTreeView class for parameter_value_list in SpineDBEditor."""

    def __init__(self, parent):
        """
        Args:
            parent(QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._open_in_editor_action = None

    def connect_spine_db_editor(self, spine_db_editor):
        """see base class"""
        super().connect_spine_db_editor(spine_db_editor)
        delegate = ParameterValueListDelegate(self._spine_db_editor)
        delegate.data_committed.connect(self.model().setData)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)
        self.setItemDelegateForColumn(0, delegate)

    def populate_context_menu(self):
        """Creates a context menu for this view."""
        super().populate_context_menu()
        self._menu.addSeparator()
        self._open_in_editor_action = self._menu.addAction("Edit...", self.open_in_editor)

    def update_actions_availability(self, item):
        """See base class."""
        self._open_in_editor_action.setEnabled(item.item_type == "list_value")

    def open_in_editor(self):
        """Opens the parameter_value editor for the first selected cell."""
        index = self.currentIndex()
        self._spine_db_editor.show_parameter_value_editor(index, plain=True)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"parameter_value_list": set(), "list_value": set()}
            for list_item in db_item.children[:-1]:
                if list_item.id is None:
                    continue
                if list_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["parameter_value_list"].add(list_item.id)
                    continue
                removed_value_item_ids = {x.id for x in list_item.children[:-1] if x in items}
                db_map_typed_data_to_rm[db_item.db_map]["list_value"].update(removed_value_item_ids)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()
