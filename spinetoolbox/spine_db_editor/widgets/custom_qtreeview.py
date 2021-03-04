######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

:author: M. Marin (KTH)
:date:   25.4.2018
"""

from PySide2.QtWidgets import QMenu
from PySide2.QtCore import Signal, Slot, Qt, QEvent
from PySide2.QtGui import QMouseEvent, QIcon
from spinetoolbox.widgets.custom_qtreeview import CopyTreeView
from spinetoolbox.helpers import busy_effect, CharIconEngine
from .custom_delegates import ToolFeatureDelegate, AlternativeScenarioDelegate, ParameterValueListDelegate


class EntityTreeView(CopyTreeView):
    """Tree view base class for object and relationship tree views."""

    tree_selection_changed = Signal(dict)

    def __init__(self, parent):
        """Initialize the view."""
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
        self._show_entity_metadata_action = None
        self._export_action = None
        self._edit_action = None
        self._remove_action = None
        self._cube_plus_icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        self._cube_minus_icon = QIcon(":/icons/menu_icons/cube_minus.svg")
        self._cube_pen_icon = QIcon(":/icons/menu_icons/cube_pen.svg")
        self._cubes_plus_icon = QIcon(":/icons/menu_icons/cubes_plus.svg")
        self._cubes_pen_icon = QIcon(":/icons/menu_icons/cubes_pen.svg")

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
        self._show_entity_metadata_action = self._menu.addAction(
            QIcon(CharIconEngine("\uf4ad")), "View metadata", self.show_entity_metadata
        )
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

    @Slot("QModelIndex", "EditTrigger", "QEvent")
    def edit(self, index, trigger, event):
        """Edit all selected items."""
        if trigger == self.EditKeyPressed:
            self.edit_selected()
            return True
        return super().edit(index, trigger, event)

    def connect_signals(self):
        """Connects signals."""
        self.expanded.connect(self._resize_first_column_to_contents)
        self.collapsed.connect(self._resize_first_column_to_contents)
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)
        self._menu.aboutToShow.connect(self._spine_db_editor.refresh_copy_paste_actions)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self._refresh_selected_indexes()

    def rowsRemoved(self, parent, start, end):
        super().rowsRemoved(parent, start, end)
        self._refresh_selected_indexes()

    @Slot("QModelIndex")
    def _resize_first_column_to_contents(self, _index=None):
        self.resizeColumnToContents(0)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_selection_changed(self, selected, deselected):
        """Classifies selection by item type and emits signal."""
        self._refresh_selected_indexes()
        if not self.selectionModel().hasSelection():
            return
        self.tree_selection_changed.emit(self._selected_indexes)

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
        if selection_model.hasSelection():
            selection_model.clearSelection()

    @busy_effect
    def fully_expand(self):
        """Expands selected indexes and all their children."""
        self.expanded.disconnect(self._resize_first_column_to_contents)
        model = self.model()
        indexes = [index for index in self.selectionModel().selectedIndexes() if index.column() == 0]
        for index in indexes:
            for item in model.visit_all(index):
                self.expand(model.index_from_item(item))
        self.expanded.connect(self._resize_first_column_to_contents)
        self._resize_first_column_to_contents()

    @busy_effect
    def fully_collapse(self):
        """Collapses selected indexes and all their children."""
        self.collapsed.disconnect(self._resize_first_column_to_contents)
        model = self.model()
        indexes = [index for index in self.selectionModel().selectedIndexes() if index.column() == 0]
        for index in indexes:
            for item in model.visit_all(index):
                self.collapse(model.index_from_item(item))
        self.collapsed.connect(self._resize_first_column_to_contents)
        self._resize_first_column_to_contents()

    def export_selected(self):
        """Exports data from selected indexes using the connected Spine db editor."""
        self._spine_db_editor.export_selected(self._selected_indexes)

    def remove_selected(self):
        """Removes selected indexes using the connected Spine db editor."""
        self._spine_db_editor.show_remove_entity_tree_items_form(self._selected_indexes)

    def manage_relationships(self):
        item = self._context_item
        relationship_class_key = item.display_id
        self._spine_db_editor.show_manage_relationships_form(relationship_class_key=relationship_class_key)

    def show_entity_metadata(self):
        """Shows entity's metadata."""
        db_map_ids = {}
        for index in set(self._selected_indexes.get("object", {})) | set(
            self._selected_indexes.get("relationship", {})
        ):
            item = self.model().item_from_index(index)
            for db_map, id_ in item.db_map_ids.items():
                db_map_ids.setdefault(db_map, list()).append(id_)
        self._spine_db_editor.show_db_map_entity_metadata(db_map_ids)

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
        self._menu.exec_(event.globalPos())

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
        self._add_relationships_action.setEnabled(item.item_type in ("root", "relationship_class"))
        self._manage_relationships_action.setEnabled(item.item_type in ("root", "relationship_class"))
        self._show_entity_metadata_action.setEnabled(item.item_type in ("object", "relationship"))
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
        """Initialize the view."""
        super().__init__(parent=parent)
        self._add_objects_action = None
        self._add_object_classes_action = None
        self._add_object_group_action = None
        self._manage_members_action = None
        self._duplicate_object_action = None
        self._find_next_action = None

    def update_actions_availability(self):
        super().update_actions_availability()
        item = self._context_item
        self._add_object_classes_action.setEnabled(item.item_type == "root")
        self._add_objects_action.setEnabled(item.item_type in ("root", "object_class"))
        self._add_object_group_action.setEnabled(item.item_type == "object_class")
        self._add_relationship_classes_action.setEnabled(item.item_type in ("root", "object_class"))
        self._manage_members_action.setEnabled(item.item_type == "members")
        self._duplicate_object_action.setEnabled(item.item_type == "object" and not item.is_group())
        self._find_next_action.setEnabled(item.item_type == "relationship")

    def _add_middle_actions(self):
        self._add_object_classes_action = self._menu.addAction(
            self._cube_plus_icon, "Add objects classes", self.add_object_classes
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

    def add_object_classes(self):
        self._spine_db_editor.show_add_object_classes_form()

    def add_objects(self):
        item = self._context_item
        class_name = item.display_data if item.item_type != "root" else None
        self._spine_db_editor.show_add_objects_form(class_name=class_name)

    def add_relationship_classes(self):
        item = self._context_item
        object_class_one_name = item.display_data if item.item_type != "root" else None
        self._spine_db_editor.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def add_relationships(self):
        item = self._context_item
        relationship_class_key = item.display_id
        if item.item_type != "root":
            object_name = item.parent_item.display_data
            object_class_name = item.parent_item.parent_item.display_data
            object_names_by_class_name = {object_class_name: object_name}
        else:
            object_names_by_class_name = None
        self._spine_db_editor.show_add_relationships_form(
            relationship_class_key=relationship_class_key, object_names_by_class_name=object_names_by_class_name
        )

    def find_next_relationship(self):
        """Finds the next occurrence of the relationship at the current index and expands it."""
        index = self.currentIndex()
        next_index = self.model().find_next_relationship_index(index)
        if not next_index:
            return
        self.setCurrentIndex(next_index)
        self.scrollTo(next_index)
        self.expand(next_index)

    def duplicate_object(self):
        """Duplicates the object at the current index using the connected Spine db editor."""
        index = self.currentIndex()
        self._spine_db_editor.duplicate_object(index)

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
        self._spine_db_editor.show_add_relationship_classes_form()

    def add_relationships(self):
        relationship_class_key = self._context_item.display_id
        self._spine_db_editor.show_add_relationships_form(relationship_class_key=relationship_class_key)


class ItemTreeView(CopyTreeView):
    """Base class for all non-entity tree views."""

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._spine_db_editor = None
        self._menu = QMenu(self)

    def connect_signals(self):
        """Connects signals."""
        self.expanded.connect(self._resize_first_column_to_contents)
        self.collapsed.connect(self._resize_first_column_to_contents)
        self._menu.aboutToShow.connect(self._spine_db_editor.refresh_copy_paste_actions)

    @Slot("QModelIndex")
    def _resize_first_column_to_contents(self, _index=None):
        self.resizeColumnToContents(0)

    def remove_selected(self):
        """Removes items selected in the view."""
        raise NotImplementedError()

    def update_actions_availability(self, item):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        raise NotImplementedError()

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        self.populate_context_menu()
        self.connect_signals()

    def populate_context_menu(self):
        """Creates a context menu for this view."""
        self._menu.addAction(self._spine_db_editor.ui.actionCopy)
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
        self._menu.exec_(event.globalPos())


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
                    for tool_feat_meth_item in reversed(tool_feat_meth_root_item.children):
                        if tool_feat_meth_item in items:
                            db_map_typed_data_to_rm[db_item.db_map]["tool_feature_method"].add(tool_feat_meth_item.id)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def update_actions_availability(self, item):
        """See base class."""

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        index = self.indexAt(event.pos())
        item = self.model().item_from_index(index)
        if item and item.item_type == "tool":
            self.expand(index)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.source() is self:
            event.accept()


class AlternativeScenarioTreeView(ItemTreeView):
    """Custom QTreeView class for the alternative scenario tree in SpineDBEditor."""

    alternative_selection_changed = Signal(dict)

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._selected_alternative_ids = dict()
        self.setMouseTracking(True)

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    def connect_spine_db_editor(self, spine_db_editor):
        """see base class"""
        super().connect_spine_db_editor(spine_db_editor)
        delegate = AlternativeScenarioDelegate(self._spine_db_editor)
        delegate.data_committed.connect(self.model().setData)
        self.setItemDelegateForColumn(0, delegate)

    def _db_map_alt_ids_from_selection(self, selection):
        db_map_ids = {}
        for index in selection.indexes():
            if index.column() != 0:
                continue
            item = self.model().item_from_index(index)
            if item.item_type == "alternative" and item.id:
                db_map_ids.setdefault(item.db_map, set()).add(item.id)
        return db_map_ids

    def _db_map_scen_alt_ids_from_selection(self, selection):
        db_map_ids = {}
        for index in selection.indexes():
            if index.column() != 0:
                continue
            item = self.model().item_from_index(index)
            if item.item_type == "scenario_alternative root":
                db_map_ids.setdefault(item.db_map, set()).update(item.alternative_id_list)
        return db_map_ids

    @Slot("QItemSelection", "QItemSelection")
    def _handle_selection_changed(self, selected, deselected):
        """Emits alternative_selection_changed with the current selection."""
        selected_db_map_alt_ids = self._db_map_alt_ids_from_selection(selected)
        deselected_db_map_alt_ids = self._db_map_alt_ids_from_selection(deselected)
        selected_db_map_scen_alt_ids = self._db_map_scen_alt_ids_from_selection(selected)
        deselected_db_map_scen_alt_ids = self._db_map_scen_alt_ids_from_selection(deselected)
        # NOTE: remove deselected scenario alternatives *before* adding selected alternatives, for obvious reasons
        for db_map, ids in deselected_db_map_alt_ids.items():
            self._selected_alternative_ids[db_map].difference_update(ids)
        for db_map, ids in deselected_db_map_scen_alt_ids.items():
            self._selected_alternative_ids[db_map].difference_update(ids)
        for db_map, ids in selected_db_map_alt_ids.items():
            self._selected_alternative_ids.setdefault(db_map, set()).update(ids)
        for db_map, ids in selected_db_map_scen_alt_ids.items():
            self._selected_alternative_ids.setdefault(db_map, set()).update(ids)
        self.alternative_selection_changed.emit(self._selected_alternative_ids)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        db_map_scen_alt_data = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"alternative": set(), "scenario": set()}
            db_map_scen_alt_data[db_item.db_map] = []
            for alt_item in reversed(db_item.child(0).children[:-1]):
                if alt_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["alternative"].add(alt_item.id)
            for scen_item in reversed(db_item.child(1).children[:-1]):
                if scen_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["scenario"].add(scen_item.id)
                    continue
                scen_alt_root_item = scen_item.scenario_alternative_root_item
                curr_alt_id_list = scen_alt_root_item.alternative_id_list
                new_alt_id_list = [
                    id_ for alt_item, id_ in zip(scen_alt_root_item.children, curr_alt_id_list) if alt_item not in items
                ]
                if new_alt_id_list != curr_alt_id_list:
                    item = {"id": scen_item.id, "alternative_id_list": ",".join([str(id_) for id_ in new_alt_id_list])}
                    db_map_scen_alt_data[db_item.db_map].append(item)
        self.model().db_mngr.set_scenario_alternatives(db_map_scen_alt_data)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def update_actions_availability(self, item):
        """See base class."""

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        index = self.indexAt(event.pos())
        item = self.model().item_from_index(index)
        if item and item.item_type == "scenario":
            self.expand(index)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.source() is self:
            event.accept()


class ParameterValueListTreeView(ItemTreeView):
    """Custom QTreeView class for parameter_value_list in SpineDBEditor.
    """

    def __init__(self, parent):
        """Initialize the view."""
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
        self._open_in_editor_action = self._menu.addAction("Open in editor...", self.open_in_editor)

    def update_actions_availability(self, item):
        """See base class."""
        self._open_in_editor_action.setEnabled(item.item_type == "value")

    def open_in_editor(self):
        """Opens the parameter_value editor for the first selected cell."""
        index = self.currentIndex()
        self._spine_db_editor.show_parameter_value_editor(index)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        db_map_data_to_upd = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"parameter_value_list": set()}
            db_map_data_to_upd[db_item.db_map] = []
            for list_item in reversed(db_item.children[:-1]):
                if list_item.id:
                    if list_item in items:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter_value_list"].add(list_item.id)
                        continue
                    curr_value_list = list_item.value_list
                    new_value_list = [
                        value
                        for value_item, value in zip(list_item.children, curr_value_list)
                        if value_item not in items
                    ]
                    if not new_value_list:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter_value_list"].add(list_item.id)
                        continue
                    if new_value_list != curr_value_list:
                        item = {"id": list_item.id, "value_list": new_value_list}
                        db_map_data_to_upd[db_item.db_map].append(item)
                else:
                    # WIP lists, just remove everything selected
                    if list_item in items:
                        db_item.remove_children(list_item.child_number(), list_item.child_number())
                        continue
                    for value_item in reversed(list_item.children[:-1]):
                        if value_item in items:
                            list_item.remove_children(value_item.child_number(), value_item.child_number())
        self.model().db_mngr.update_parameter_value_lists(db_map_data_to_upd)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()


class ParameterTagTreeView(ItemTreeView):
    """Custom QTreeView class for the parameter_tag tree in SpineDBEditor."""

    tag_selection_changed = Signal(dict)

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._selected_tag_ids = dict()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"parameter_tag": set()}
            for tag_item in reversed(db_item.children[:-1]):
                if tag_item.id and tag_item in items:
                    db_map_typed_data_to_rm[db_item.db_map]["parameter_tag"].add(tag_item.id)
        self.model().db_mngr.remove_items(db_map_typed_data_to_rm)
        self.selectionModel().clearSelection()

    def update_actions_availability(self, item):
        """See base class."""

    @Slot("QItemSelection", "QItemSelection")
    def _handle_selection_changed(self, selected, deselected):
        """Emits tag_selection_changed with the current selection."""
        selected_db_map_ids = self._db_map_tag_ids_from_selection(selected)
        deselected_db_map_ids = self._db_map_tag_ids_from_selection(deselected)
        for db_map, ids in selected_db_map_ids.items():
            self._selected_tag_ids.setdefault(db_map, set()).update(ids)
        for db_map, ids in deselected_db_map_ids.items():
            self._selected_tag_ids[db_map].difference_update(ids)
        self._selected_tag_ids = {db_map: ids for db_map, ids in self._selected_tag_ids.items() if ids}
        self.tag_selection_changed.emit(self._selected_tag_ids)

    def _db_map_tag_ids_from_selection(self, selection):
        db_map_ids = {}
        for index in selection.indexes():
            if index.column() != 0:
                continue
            item = self.model().item_from_index(index)
            if item.item_type == "parameter_tag" and item.id:
                db_map_ids.setdefault(item.db_map, set()).add(item.id)
        return db_map_ids
