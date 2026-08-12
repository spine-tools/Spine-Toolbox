######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes for custom QTreeViews and QTreeWidgets."""

from PySide6.QtCore import QEvent, QModelIndex, QSettings, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QMouseEvent, Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QMenu, QTreeView, QWidget
from spinedb_api.temp_id import TempId
from spinetoolbox.helpers import CharIconEngine, busy_effect
from spinetoolbox.widgets.custom_qtreeview import CopyPasteTreeView
from ...mvcmodels.shared import DB_MAP_ROLE, ITEM_ID_ROLE
from ..helpers import SearchFocusMixin
from ..mvcmodels import mime_types
from ..mvcmodels.alternative_item import AlternativeItem
from ..mvcmodels.level_filter import FORCE_FETCH_DELAY
from ..mvcmodels.scenario_item import ScenarioAlternativeItem, ScenarioDBItem, ScenarioItem
from .custom_delegates import AddEntityButtonDelegate, AlternativeDelegate, ParameterValueListDelegate, ScenarioDelegate
from .custom_menus import RecursiveChoiceSubMenu


class MultitreeSelection:
    multitree_selection_clearing_requested = Signal(QTreeView)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app_settings: QSettings | None = None

    def set_app_settings(self, app_settings: QSettings) -> None:
        self._app_settings = app_settings

    def mousePressEvent(self, event):
        sticky_selection = self._app_settings.value("appSettings/stickySelection", defaultValue="false")
        if sticky_selection == "true":
            local_pos = event.position()
            window_pos = event.scenePosition()
            screen_pos = event.globalPosition()
            button = event.button()
            buttons = event.buttons()
            modifiers = event.modifiers()
            if (modifiers & Qt.KeyboardModifier.ControlModifier) == Qt.KeyboardModifier.ControlModifier:
                self.multitree_selection_clearing_requested.emit(self)
                modifiers &= ~Qt.KeyboardModifier.ControlModifier
            else:
                modifiers |= Qt.KeyboardModifier.ControlModifier
            source = event.source()
            event = QMouseEvent(
                QEvent.Type.MouseButtonPress, local_pos, window_pos, screen_pos, button, buttons, modifiers, source
            )
        elif (event.modifiers() & Qt.KeyboardModifier.ControlModifier) == Qt.KeyboardModifier.NoModifier:
            self.multitree_selection_clearing_requested.emit(self)
        super().mousePressEvent(event)


class TreeSearchFocusMixin(SearchFocusMixin):
    """Adds keyboard navigation and lower-level-filter auto-expand between a tree view and its filter bar.

    Mirrors the stacked tables' ``ColumnSearchRowMixin``: the Up arrow on the tree's topmost item
    jumps into the filter row, Down from a filter field drops back onto the tree, and the view's
    Alt+N shortcut toggles focus into the filter row.

    On top of navigation it reveals the matches of a *lower-level* regex filter: a QTreeView child only
    shows when its parent is expanded, so while a lower-level filter is active the tree is auto-expanded onto
    the matching leaves (or collapsed if nothing matches) once the filter has settled, and the pre-filter
    expansion is restored when the lower-level filters are cleared. Trees with a single level (the
    alternative tree) never trigger this, since their model reports no lower-level filter.
    """

    def connect_level_filter_bar(self, bar) -> None:
        """Stores the filter bar and wires its focus, navigation and auto-expand signals.

        Args:
            bar (TreeLevelFilterBar): the per-level filter bar sitting above this tree
        """
        self._level_filter_bar = bar
        self._regex_row_was_last = False
        self._lower_filter_session = False
        self._saved_expansion = None
        self._suppress_auto_expand = False
        self._auto_expand_timer = QTimer(self)
        self._auto_expand_timer.setSingleShot(True)
        self._auto_expand_timer.setInterval(FORCE_FETCH_DELAY)
        self._auto_expand_timer.timeout.connect(self._apply_auto_expand)
        bar.editor_focused.connect(self._note_search_row_focused)
        bar.navigate_to_tree.connect(self._focus_tree_top)
        bar.lower_filter_active_changed.connect(self._on_lower_filter_active_changed)
        model = self.model()
        if model is not None:
            model.layoutChanged.connect(self._on_model_layout_changed)

    def reset_level_filter_state(self) -> None:
        """Clears the filter bar and auto-expand state so a (re)loaded tree starts unfiltered.

        Called when the editor (re)builds its trees for a new database set (see
        ``TreeViewMixin.init_models``). It empties the filter bar and drops the captured pre-filter
        expansion and session flags, which otherwise reference the now-destroyed pre-reset items, so a
        stale filter cannot carry over onto the freshly built tree.
        """
        bar = getattr(self, "_level_filter_bar", None)
        if bar is None:
            return
        bar.clear_all()
        self._regex_row_was_last = False
        self._lower_filter_session = False
        self._saved_expansion = None
        self._suppress_auto_expand = False
        self._auto_expand_timer.stop()

    @Slot()
    def _on_model_layout_changed(self) -> None:
        """Restarts the auto-expand debounce, unless the layout change was our own programmatic expand.

        The auto-expander itself expands/collapses the view, which emits ``layoutChanged``; re-arming on
        that would loop. The ``_suppress_auto_expand`` guard swallows exactly those self-inflicted signals.
        """
        if self._suppress_auto_expand:
            return
        self._auto_expand_timer.start()

    @Slot(bool)
    def _on_lower_filter_active_changed(self, active: bool) -> None:
        """Captures the pre-filter expansion on the rising edge so it can be restored faithfully later.

        Args:
            active: whether any cell below the top level now holds text
        """
        if active and not self._lower_filter_session:
            self._saved_expansion = self._capture_expansion()
            self._lower_filter_session = True

    @Slot()
    def _apply_auto_expand(self) -> None:
        """Reveals the matches once the filter has settled, or restores the tree when it is cleared.

        Runs on a debounce restarted by every model ``layoutChanged``, so it only fires once fetching and
        typing have paused. While a lower-level filter is active the tree is expanded onto the matching
        leaves, or collapsed when nothing matches; once the lower-level filters clear, the pre-filter
        expansion is restored.
        """
        model = self.model()
        if model is None or not hasattr(model, "lower_level_filter_active"):
            return
        if model.lower_level_filter_active():
            if not self._lower_filter_session:
                self._saved_expansion = self._capture_expansion()
                self._lower_filter_session = True
            # One walk collects the matches; reused both to decide reveal-vs-collapse and to expand only the
            # branches leading to them - never ``expandAll``, which would materialize the whole tree and,
            # by fetching more rows, feed another layoutChanged back into this handler.
            matches = model.collect_visible_matches()
            self._suppress_auto_expand = True
            try:
                if matches:
                    self._expand_to_items(matches)
                else:
                    self.collapseAll()
            finally:
                self._suppress_auto_expand = False
            return
        if self._lower_filter_session:
            self._suppress_auto_expand = True
            try:
                self._restore_expansion(self._saved_expansion)
            finally:
                self._suppress_auto_expand = False
            self._saved_expansion = None
            self._lower_filter_session = False

    def _expand_to_items(self, items) -> None:
        """Expands just the ancestor chains that reveal the given items, top-down.

        Args:
            items: tree items to make visible (their ancestors get expanded)
        """
        model = self.model()
        if model is None:
            return
        seen = set()
        for item in items:
            chain = []
            ancestor = item.parent_item
            while ancestor is not None and ancestor not in seen:
                index = model.index_from_item(ancestor)
                if not index.isValid():
                    break
                chain.append(index)
                seen.add(ancestor)
                ancestor = ancestor.parent_item
            for index in reversed(chain):
                self.expand(index)

    def _capture_expansion(self) -> set:
        """Returns the set of currently expanded tree items."""
        model = self.model()
        expanded = set()
        if model is None:
            return expanded
        for item in model.visit_all():
            index = model.index_from_item(item)
            if index.isValid() and self.isExpanded(index):
                expanded.add(item)
        return expanded

    def _restore_expansion(self, expanded) -> None:
        """Collapses the tree and re-expands exactly the still-present captured items.

        Args:
            expanded: the set returned by :meth:`_capture_expansion`, or None
        """
        model = self.model()
        if model is None:
            return
        self.collapseAll()
        if not expanded:
            return
        for item in model.visit_all():
            if item in expanded:
                index = model.index_from_item(item)
                if index.isValid():
                    self.expand(index)

    @Slot()
    def _focus_tree_top(self) -> None:
        """Moves focus from the filter bar down onto the first tree item."""
        model = self.model()
        if model is None:
            return
        index = model.index(0, 0)
        if not index.isValid():
            return
        self.setCurrentIndex(index)
        self.setFocus()

    def _search_focus_ready(self) -> bool:
        """See base class; ready once the filter bar has been connected."""
        return getattr(self, "_level_filter_bar", None) is not None

    def _search_row_editor_widgets(self) -> list:
        """See base class."""
        bar = getattr(self, "_level_filter_bar", None)
        return bar.editors() if bar is not None else []

    def _focus_search_row_from_view(self) -> None:
        """See base class; focuses the filter bar's last used cell."""
        self._level_filter_bar.focus_last_used_cell()

    def _restore_search_row_focus(self) -> None:
        """See base class; focuses the filter bar's last used cell."""
        self._level_filter_bar.focus_last_used_cell()

    def _at_top_for_search_focus(self) -> bool:
        """See base class; True when the current item is the tree's topmost row."""
        bar = getattr(self, "_level_filter_bar", None)
        if bar is None:
            return False
        current = self.currentIndex()
        return current.isValid() and not self.indexAbove(current).isValid()


class EntityTreeView(TreeSearchFocusMixin, MultitreeSelection, CopyPasteTreeView):
    """Tree view for entity classes and entities."""

    selection_export_requested = Signal()
    selection_removal_requested = Signal()
    selection_edit_requested = Signal()
    add_entity_classes_dialog_requested = Signal(object)
    add_entities_dialog_requested = Signal(object)
    entity_duplication_requested = Signal(object)
    add_entity_group_dialog_requested = Signal(object)
    manage_members_dialog_requested = Signal(object)
    manage_elements_dialog_requested = Signal(object)
    select_superclass_dialog_requested = Signal(object)

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: parent widget
        """
        super().__init__(parent=parent)
        self.setItemDelegate(AddEntityButtonDelegate(self))
        self.setRootIsDecorated(False)
        self._context_item = None
        self._menu = QMenu(self)
        self._fully_expand_action = None
        self._fully_collapse_action = None
        self._add_entity_classes_action = None
        self._add_entities_action = None
        self._add_entity_group_action = None
        self._duplicate_entity_action = None
        self._manage_elements_action = None
        self._manage_members_action = None
        self._select_superclass_action = None
        self._export_action = None
        self._edit_action = None
        self._remove_action = None
        self._cube_plus_icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        self._cube_minus_icon = QIcon(":/icons/menu_icons/cube_minus.svg")
        self._cube_pen_icon = QIcon(":/icons/menu_icons/cube_pen.svg")
        self._cubes_pen_icon = QIcon(":/icons/menu_icons/cubes_pen.svg")
        self._fetch_more_timer = QTimer(self)
        self._fetch_more_timer.setSingleShot(True)
        self._fetch_more_timer.timeout.connect(self._fetch_more_visible)
        self._find_next_action = None
        self._hide_empty_classes_action = None
        self._entity_index = None
        self._header = self.header()
        self._header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.doubleClicked.connect(self.find_next_entity)

    def finish_init(self, copy_action: QAction) -> None:
        self._create_context_menu(copy_action)

    def set_db_column_visibility(self, visible):
        """Sets the visibility of the db column"""
        if visible:
            self._header.showSection(1)
        else:
            self._header.hideSection(1)
        # The tree header only repeats the "name"/"database" labels; hide it while a single column
        # is visible so the regex filter row sits directly above the tree content.
        self.setHeaderHidden(not visible)

    def _add_middle_actions(self):
        self._add_entity_classes_action = self._menu.addAction(
            self._cube_plus_icon, "Add entity classes...", self.add_entity_classes
        )
        self._add_entities_action = self._menu.addAction(self._cube_plus_icon, "Add entities...", self.add_entities)
        self._add_entity_group_action = self._menu.addAction(
            self._cube_plus_icon, "Add entity group...", self.add_entity_group
        )
        self._manage_elements_action = self._menu.addAction(
            self._cubes_pen_icon, "Manage elements...", self.manage_elements
        )
        self._manage_members_action = self._menu.addAction(
            self._cube_pen_icon, "Manage members...", self.manage_members
        )
        self._select_superclass_action = self._menu.addAction(
            self._cube_pen_icon, "Select superclass...", self.select_superclass
        )
        self._menu.addSeparator()
        self._find_next_action = self._menu.addAction(
            QIcon(CharIconEngine("\uf141")), "Find next occurrence", self.find_next_entity
        )

    def _create_context_menu(self, copy_action: QAction) -> None:
        """Creates a context menu for this view."""
        self._menu.addAction(copy_action)
        self._menu.addSeparator()
        self._add_middle_actions()
        self._menu.addSeparator()
        self._edit_action = self._menu.addAction(self._cube_pen_icon, "Edit...", self.edit_selected)
        self._remove_action = self._menu.addAction(self._cube_minus_icon, "Remove...", self.remove_selected)
        self._duplicate_entity_action = self._menu.addAction(
            self._cube_plus_icon, "Duplicate entity", self.duplicate_entity
        )
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
        self._menu.addSeparator()
        self._hide_empty_classes_action = self._menu.addAction("Hide empty classes", self.toggle_hide_empty_classes)
        self._hide_empty_classes_action.setCheckable(True)
        self._hide_empty_classes_action.setChecked(self.model().hide_empty_classes)

    def toggle_hide_empty_classes(self):
        self.model().hide_empty_classes = self._hide_empty_classes_action.isChecked()
        self.model().save_hide_empty_classes()

    @Slot(QModelIndex, int, QEvent)
    def edit(self, index, trigger, event):
        """Edit all selected items."""
        if trigger == QAbstractItemView.EditTrigger.EditKeyPressed:
            self.edit_selected()
            return True
        return super().edit(index, trigger, event)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        QTimer.singleShot(0, self._do_find_next_entity)

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

    def collapse(self, index):
        """Overridden to prevent the collapse of the root item"""
        if not index.parent().isValid():
            return
        super().collapse(index)

    @Slot()
    def export_selected(self):
        """Exports data from selected indexes using the connected Spine db editor."""
        self.selection_export_requested.emit()

    def remove_selected(self):
        """Removes selected indexes using the connected Spine db editor."""
        self.selection_removal_requested.emit()

    def contextMenuEvent(self, event):
        """Shows context menu."""
        index = self.indexAt(event.pos())
        if index.column() != 0:
            return
        self._context_item = self.model().item_from_index(index)
        self.update_actions_availability()
        self._menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        """Overridden to not allow collapsing of the root item by double click."""
        pos = self.viewport().mapFromGlobal(event.globalPos())
        index = self.indexAt(pos)
        model = index.model()
        if model:
            item = model.item_from_index(index)
            if item.item_type == "root":
                event.ignore()
                return
        super().mouseDoubleClickEvent(event)

    def update_actions_availability(self):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        item = self._context_item
        item_has_children = item.has_children()
        self._fully_expand_action.setEnabled(item_has_children)
        self._fully_collapse_action.setEnabled(item_has_children)
        self._add_entity_classes_action.setEnabled(item.item_type in ("root", "entity_class"))
        self._add_entities_action.setEnabled(
            item.item_type in ("root", "entity_class")
            or (item.item_type == "entity" and item.parent_item.item_type == "entity_class")
        )
        self._add_entity_group_action.setEnabled(item.item_type == "entity_class")
        self._duplicate_entity_action.setEnabled(
            item.item_type == "entity" and not item.is_group and not item.element_name_list
        )
        self._manage_members_action.setEnabled(item.item_type == "entity" and item.is_group)
        self._select_superclass_action.setEnabled(item.item_type == "entity_class")
        self._manage_elements_action.setEnabled(
            item.item_type == "root" or (item.item_type == "entity_class" and item.has_dimensions)
        )
        read_only = item.item_type in ("root", "members")
        self._export_action.setEnabled(not read_only)
        self._edit_action.setEnabled(not read_only)
        self._remove_action.setEnabled(not read_only)
        self._find_next_action.setEnabled(
            item.item_type == "entity" and item.parent_item.parent_item.item_type == "entity_class"
        )

    @Slot()
    def edit_selected(self):
        """Edits all selected indexes using the connected Spine db editor."""
        self.selection_edit_requested.emit()

    def add_entity_classes(self):
        self.add_entity_classes_dialog_requested.emit(self._context_item)

    def add_entities(self):
        self.add_entities_dialog_requested.emit(self._context_item)

    def find_next_entity(self):
        """Finds the next occurrence of the relationship at the current index and expands it."""
        self._entity_index = self.currentIndex()
        self._do_find_next_entity()

    @Slot()
    def _do_find_next_entity(self) -> None:
        if self._entity_index is None:
            return
        next_index = self.model().find_next_entity_index(self._entity_index)
        if not next_index:
            return
        self._entity_index = None
        self.setCurrentIndex(next_index)
        self.scrollTo(next_index)
        self.expand(next_index)

    def duplicate_entity(self):
        """Duplicates the object at the current index using the connected Spine db editor."""
        self.entity_duplication_requested.emit(self._context_item)

    def add_entity_group(self):
        self.add_entity_group_dialog_requested.emit(self._context_item)

    def manage_elements(self):
        self.manage_elements_dialog_requested.emit(self._context_item)

    def manage_members(self):
        self.manage_members_dialog_requested.emit(self._context_item)

    def select_superclass(self):
        self.select_superclass_dialog_requested.emit(self._context_item)


class ItemTreeView(TreeSearchFocusMixin, CopyPasteTreeView):
    """Base class for all non-entity tree views."""

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: parent widget
        """
        super().__init__(parent=parent)
        self._menu = QMenu(self)
        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def finish_init(self, copy_action: QAction, paste_action: QAction) -> None:
        self.populate_context_menu(copy_action, paste_action)

    def rowsInserted(self, parent, start, end):
        super().rowsInserted(parent, start, end)
        self.resizeColumnToContents(0)

    def remove_selected(self):
        """Removes items selected in the view."""
        raise NotImplementedError()

    def update_actions_availability(self, item):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        raise NotImplementedError()

    def populate_context_menu(self, copy_action: QAction, paste_action: QAction) -> None:
        """Creates a context menu for this view."""
        self._menu.addAction(copy_action)
        self._menu.addAction(paste_action)
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


class AlternativeTreeView(MultitreeSelection, ItemTreeView):
    """Custom QTreeView for the alternative tree in SpineDBEditor."""

    scenario_generator_requested = Signal(object, list)

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: parent widget
        """
        super().__init__(parent=parent)
        self._generate_scenarios_action: QAction | None = None
        self._delegate = AlternativeDelegate(self)
        self.setItemDelegateForColumn(0, self._delegate)

    def setModel(self, model):
        if self.model():
            self._delegate.data_committed.disconnect(self.model().setData)
        self._delegate.data_committed.connect(model.setData)
        super().setModel(model)

    def populate_context_menu(self, copy_action: QAction, paste_action: QAction) -> None:
        """See base class."""
        self._generate_scenarios_action = self._menu.addAction("Generate scenarios...", self._open_scenario_generator)
        self._menu.addSeparator()
        super().populate_context_menu(copy_action, paste_action)

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

    def update_actions_availability(self, item):
        """See base class."""
        for index in self.selectionModel().selectedIndexes():
            if index.column() == 0 and (parent := index.parent()).isValid():
                if parent.data(DB_MAP_ROLE) is item.db_map:
                    has_selected_alternatives = True
                    break
        else:
            has_selected_alternatives = False
        self._generate_scenarios_action.setEnabled(
            isinstance(item, AlternativeItem) and item.id is not None and has_selected_alternatives
        )

    def _open_scenario_generator(self) -> None:
        """Opens the scenario generator dialog."""
        item = self.model().item_from_index(self.currentIndex())
        included_ids = set()
        alternatives = []
        db_map = item.db_map
        alternative_table = db_map.mapped_table("alternative")
        for index in self.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            parent_index = index.parent()
            if not parent_index.isValid():
                continue
            if db_map is not parent_index.data(DB_MAP_ROLE):
                continue
            alternative_id = index.data(ITEM_ID_ROLE)
            if alternative_id is None or alternative_id in included_ids:
                continue
            alternatives.append(alternative_table[alternative_id])
            included_ids.add(alternative_id)
        self.scenario_generator_requested.emit(db_map, alternatives)

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


class ScenarioTreeView(MultitreeSelection, ItemTreeView):
    """Custom QTreeView for the scenario tree in SpineDBEditor."""

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: parent widget
        """
        super().__init__(parent=parent)
        self._duplicate_scenario_action: QAction | None = None
        self._delegate = ScenarioDelegate(self)
        self.setItemDelegateForColumn(0, self._delegate)
        self._add_alternatives_submenu: QMenu | None = None
        self._duplicate_with_alternatives_submenu: QMenu | None = None

    def setModel(self, model):
        if self.model():
            self._delegate.data_committed.disconnect(self.model().setData)
        self._delegate.data_committed.connect(model.setData)
        super().setModel(model)

    def populate_context_menu(self, copy_action, paste_action):
        """See base class."""
        super().populate_context_menu(copy_action, paste_action)
        self._duplicate_scenario_action = self._menu.addAction("Duplicate", self._duplicate_scenario)
        self._menu.aboutToShow.connect(self._add_dynamic_menus)

    @Slot()
    def _add_dynamic_menus(self) -> None:
        index = self.currentIndex()
        item = self.model().item_from_index(index)
        if item.item_type == "db" or (item.item_type == "scenario" and item.id is None):
            alternatives = []
        else:
            while item.item_type != "scenario":
                item = item.parent_item
            alternatives = self._available_alternative_names(item)
        self._setup_add_alternatives_submenu(alternatives)
        self._setup_duplicate_with_alternatives_submenu(alternatives)

    def _setup_add_alternatives_submenu(self, alternatives: list[str]) -> None:
        if self._add_alternatives_submenu is not None:
            self._add_alternatives_submenu.rebuild(alternatives)
        else:
            self._add_alternatives_submenu = RecursiveChoiceSubMenu(alternatives, self._menu)
            self._add_alternatives_submenu.setTitle("Add alternatives")
            self._add_alternatives_submenu.choice_made.connect(self._add_alternatives)
            self._menu.addMenu(self._add_alternatives_submenu)
        self._add_alternatives_submenu.menuAction().setEnabled(bool(alternatives))

    def _setup_duplicate_with_alternatives_submenu(self, alternatives: list[str]) -> None:
        if self._duplicate_with_alternatives_submenu is not None:
            self._duplicate_with_alternatives_submenu.rebuild(alternatives)
        else:
            self._duplicate_with_alternatives_submenu = RecursiveChoiceSubMenu(alternatives, self._menu)
            self._duplicate_with_alternatives_submenu.setTitle("Duplicate with alternatives")
            self._duplicate_with_alternatives_submenu.choice_made.connect(self._duplicate_with_alternatives)
            self._menu.addMenu(self._duplicate_with_alternatives_submenu)
        self._duplicate_with_alternatives_submenu.menuAction().setEnabled(bool(alternatives))

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

    @staticmethod
    def _available_alternative_names(scenario_item: ScenarioItem) -> list[str]:
        db_mngr = scenario_item.model.db_mngr
        scenario_alternatives = set(db_mngr.get_scenario_alternative_id_list(scenario_item.db_map, scenario_item.id))
        all_alternatives = db_mngr.get_items(scenario_item.db_map, "alternative")
        return [
            alternative["name"] for alternative in all_alternatives if alternative["id"] not in scenario_alternatives
        ]

    @Slot(list)
    def _add_alternatives(self, alternatives: list[str]) -> None:
        index = self.currentIndex()
        model = self.model()
        item = model.item_from_index(index)
        while item.item_type != "scenario":
            item = item.parent_item
        model.add_scenario_alternatives(item, alternatives[1:])
        self._menu.close()

    @Slot(list)
    def _duplicate_with_alternatives(self, alternatives: list[str]) -> None:
        index = self.currentIndex()
        model = self.model()
        item = model.item_from_index(index)
        while item.item_type != "scenario":
            item = item.parent_item
        model.duplicate_scenario_with_alternatives(item, alternatives[1:])
        self._menu.close()


class ParameterValueListTreeView(ItemTreeView):
    """Custom QTreeView class for parameter_value_list in SpineDBEditor."""

    parameter_value_editor_requested = Signal(QModelIndex)
    plain_parameter_value_editor_requested = Signal(QModelIndex)

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: parent widget
        """
        super().__init__(parent=parent)
        self._open_in_editor_action = None
        self._delegate = ParameterValueListDelegate(self)
        self._delegate.parameter_value_editor_requested.connect(self.parameter_value_editor_requested)
        self.setItemDelegateForColumn(0, self._delegate)

    def setModel(self, model):
        if self.model():
            self._delegate.data_committed.disconnect(self.model().setData)
        self._delegate.data_committed.connect(model.setData)
        super().setModel(model)

    def populate_context_menu(self, copy_action, paste_action):
        """Creates a context menu for this view."""
        super().populate_context_menu(copy_action, paste_action)
        self._menu.addSeparator()
        self._open_in_editor_action = self._menu.addAction("Edit...", self.open_in_editor)

    def update_actions_availability(self, item):
        """See base class."""
        self._open_in_editor_action.setEnabled(item.item_type == "list_value")

    def open_in_editor(self):
        """Opens the parameter_value editor for the first selected cell."""
        index = self.currentIndex()
        self.plain_parameter_value_editor_requested.emit(index)

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
