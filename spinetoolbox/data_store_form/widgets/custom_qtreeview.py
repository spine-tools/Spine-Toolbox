######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

from PySide2.QtWidgets import QTreeView, QMenu
from PySide2.QtCore import Signal, Slot, Qt, QEvent
from PySide2.QtGui import QMouseEvent, QIcon
from spinetoolbox.widgets.custom_qtreeview import CopyTreeView
from spinetoolbox.helpers import busy_effect


class EntityTreeView(CopyTreeView):
    """Tree view base class for object and relationship tree views."""

    tree_selection_changed = Signal(dict)

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._selected_indexes = {}
        self._menu = QMenu(self)
        self._data_store_form = None
        self._fully_expand_action = None
        self._fully_collapse_action = None
        self._add_relationship_classes_action = None
        self._add_relationships_action = None
        self._manage_relationships_action = None

    def connect_data_store_form(self, data_store_form):
        """Connects a data store form to work with this view.

        Args:
             data_store_form (DataStoreForm)
        """
        self._data_store_form = data_store_form
        self._create_context_menu()
        self.connect_signals()

    def _add_middle_actions(self):
        """Adds action at the middle of the context menu.
        Subclasses can reimplement at will.
        """

    def _create_context_menu(self):
        """Creates a context menu for this view."""
        self._menu.addAction(self._data_store_form.ui.actionCopy)
        self._menu.addSeparator()
        self._add_middle_actions()
        self._menu.addSeparator()
        self._menu.addAction(self._data_store_form.ui.actionEdit_selected)
        self._menu.addAction(self._data_store_form.ui.actionRemove_selected)
        self._menu.addSeparator()
        self._fully_expand_action = self._menu.addAction(
            QIcon(":/icons/menu_icons/angle-double-right.svg"), "Fully expand", self.fully_expand
        )
        self._fully_collapse_action = self._menu.addAction(
            QIcon(":/icons/menu_icons/angle-double-left.svg"), "Fully collapse", self.fully_collapse
        )
        self._menu.addSeparator()
        self._menu.addAction("Export selected", self.export_selected)

    def connect_signals(self):
        """Connects signals."""
        self.expanded.connect(self._resize_first_column_to_contents)
        self.collapsed.connect(self._resize_first_column_to_contents)
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

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
        self.refresh_active_member_indexes()
        parents = set(ind.parent() for ind in deselected)
        self.model().emit_data_changed_for_column(0, parents)
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

    def refresh_active_member_indexes(self):
        active_member_indexes = set(
            index.sibling(row, 0)
            for index in self._selected_indexes.get("object", ())
            for row in index.internalPointer().member_rows
        )
        self.model().set_active_member_indexes(active_member_indexes)

    @Slot("QModelIndex", "EditTrigger", "QEvent")
    def edit(self, index, trigger, event):
        """Edit all selected items."""
        if trigger == QTreeView.EditKeyPressed:
            self.edit_selected()
        return super().edit(index, trigger, event)

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
        for index in self.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in model.visit_all(index):
                self.expand(model.index_from_item(item))
        self.expanded.connect(self._resize_first_column_to_contents)
        self._resize_first_column_to_contents()

    @busy_effect
    def fully_collapse(self):
        """Collapses selected indexes and all their children."""
        self.collapsed.disconnect(self._resize_first_column_to_contents)
        model = self.model()
        for index in self.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in model.visit_all(index):
                self.collapse(model.index_from_item(item))
        self.collapsed.connect(self._resize_first_column_to_contents)
        self._resize_first_column_to_contents()

    def export_selected(self):
        """Exports data from selected indexes using the connected data store form."""
        self._data_store_form.export_selected(self._selected_indexes)

    def remove_selected(self):
        """Removes selected indexes using the connected data store form."""
        self._data_store_form.show_remove_entity_tree_items_form(self._selected_indexes)

    def manage_relationships(self):
        index = self.currentIndex()
        item = index.internalPointer()
        relationship_class_key = item.display_id
        self._data_store_form.show_manage_relationships_form(relationship_class_key=relationship_class_key)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        if index.column() != 0:
            return
        item = index.model().item_from_index(index)
        self.update_actions_visibility(item)
        self._menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        """Overrides selection behaviour if the user has selected sticky selection in Settings.
        If sticky selection is enabled, multiple-selection is enabled when selecting items in the Object tree.
        Pressing the Ctrl-button down, enables single selection.

        Args:
            event (QMouseEvent)
        """
        sticky_selection = self._data_store_form.qsettings.value("appSettings/stickySelection", defaultValue="false")
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
            self._data_store_form.ui.actionAdd_relationship_classes.icon(),
            "Add relationship classes",
            self.add_relationship_classes,
        )
        self._add_relationships_action = self._menu.addAction(
            self._data_store_form.ui.actionAdd_relationships.icon(), "Add relationships", self.add_relationships
        )
        self._manage_relationships_action = self._menu.addAction(
            self._data_store_form.ui.actionManage_relationships.icon(),
            "Manage relationships",
            self.manage_relationships,
        )

    def update_actions_visibility(self, item):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        item_has_children = item.has_children()
        self._fully_expand_action.setVisible(item_has_children)
        self._fully_collapse_action.setVisible(item_has_children)
        self._add_relationships_action.setVisible(item.item_type == "relationship class")
        self._manage_relationships_action.setVisible(item.item_type == "relationship class")

    def edit_selected(self):
        """Edits all selected indexes using the connected data store form."""
        self._data_store_form.edit_entity_tree_items(self._selected_indexes)


class ObjectTreeView(EntityTreeView):
    """Custom QTreeView class for the object tree in DataStoreForm."""

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.add_objects_action = None
        self.add_object_classes_action = None
        self.add_object_group_action = None
        self.manage_object_group_action = None
        self.duplicate_object_action = None
        self.find_next_action = None

    def update_actions_visibility(self, item):
        super().update_actions_visibility(item)
        self.add_object_classes_action.setVisible(item.item_type == "root")
        self.add_objects_action.setVisible(item.item_type == "object class")
        self.add_object_group_action.setVisible(item.item_type == "object class")
        self._add_relationship_classes_action.setVisible(item.item_type == "object class")
        self.manage_object_group_action.setVisible(item.item_type == "object" and item.is_group())
        self.duplicate_object_action.setVisible(item.item_type == "object" and not item.is_group())
        self.find_next_action.setVisible(item.item_type == "relationship")

    def _add_middle_actions(self):
        self.add_object_classes_action = self._menu.addAction(
            self._data_store_form.ui.actionAdd_object_classes.icon(), "Add objects classes", self.add_object_classes
        )
        self.add_objects_action = self._menu.addAction(
            self._data_store_form.ui.actionAdd_objects.icon(), "Add objects", self.add_objects
        )
        self.add_object_group_action = self._menu.addAction("Add object group", self.add_object_group)
        self._add_relationship_actions()
        self._menu.addSeparator()
        self.find_next_action = self._menu.addAction(
            QIcon(":/icons/menu_icons/ellipsis-h.png"), "Find next", self.find_next_relationship
        )
        self.manage_object_group_action = self._menu.addAction("Manage object group", self.manage_object_group)
        self.duplicate_object_action = self._menu.addAction(
            self._data_store_form.ui.actionAdd_objects.icon(), "Duplicate object", self.duplicate_object
        )
        self._menu.addSeparator()

    def connect_signals(self):
        super().connect_signals()
        self.doubleClicked.connect(self.find_next_relationship)

    def add_object_classes(self):
        self._data_store_form.show_add_object_classes_form()

    def add_objects(self):
        index = self.currentIndex()
        class_name = index.internalPointer().display_data
        self._data_store_form.show_add_objects_form(class_name=class_name)

    def add_relationship_classes(self):
        index = self.currentIndex()
        object_class_one_name = index.internalPointer().display_data
        self._data_store_form.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def add_relationships(self):
        index = self.currentIndex()
        item = index.internalPointer()
        relationship_class_key = item.display_id
        object_name = item.parent_item.display_data
        object_class_name = item.parent_item.parent_item.display_data
        object_names_by_class_name = {object_class_name: object_name}
        self._data_store_form.show_add_relationships_form(
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
        """Duplicate the object at the current index using the connected data store form."""
        index = self.currentIndex()
        self._data_store_form.duplicate_object(index)

    def add_object_group(self):
        index = self.currentIndex()
        item = index.internalPointer()
        self._data_store_form.show_add_object_group_form(item)

    def manage_object_group(self):
        index = self.currentIndex()
        item = index.internalPointer()
        self._data_store_form.show_manage_object_group_form(item)


class RelationshipTreeView(EntityTreeView):
    """Custom QTreeView class for the relationship tree in DataStoreForm."""

    def _add_middle_actions(self):
        self._add_relationship_actions()

    def update_actions_visibility(self, item):
        super().update_actions_visibility(item)
        self._add_relationship_classes_action.setVisible(item.item_type == "root")

    def add_relationship_classes(self):
        self._data_store_form.show_add_relationship_classes_form()

    def add_relationships(self):
        index = self.currentIndex()
        item = index.internalPointer()
        relationship_class_key = item.display_id
        self._data_store_form.show_add_relationships_form(relationship_class_key=relationship_class_key)


class ItemTreeView(CopyTreeView):
    """Custom QTreeView class for parameter value list in DataStoreForm.
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._data_store_form = None
        self._menu = QMenu(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects signals."""
        self.expanded.connect(self._resize_first_column_to_contents)
        self.collapsed.connect(self._resize_first_column_to_contents)

    @Slot("QModelIndex")
    def _resize_first_column_to_contents(self, _index=None):
        self.resizeColumnToContents(0)

    def remove_selected(self):
        """Removes items selected in the view."""
        raise NotImplementedError()

    def update_actions_visibility(self, item):
        """Updates the visible property of actions according to whether or not they apply to given item."""
        raise NotImplementedError()

    def connect_data_store_form(self, data_store_form):
        self._data_store_form = data_store_form
        self.create_context_menu()

    def create_context_menu(self):
        """Creates a context menu for this view."""
        self._menu.addAction(self._data_store_form.ui.actionCopy)
        self._menu.addAction(self._data_store_form.ui.actionRemove_selected)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        if index.column() != 0:
            return
        item = index.model().item_from_index(index)
        self.update_actions_visibility(item)
        self._menu.exec_(event.globalPos())


class AlternativeScenarioTreeView(ItemTreeView):
    """Custom QTreeView class for the alternative scenario tree in DataStoreForm."""

    def remove_selected(self):
        """See base class."""
        raise NotImplementedError()

    def update_actions_visibility(self, item):
        """See base class."""
        raise NotImplementedError()


class ParameterValueListTreeView(ItemTreeView):
    """Custom QTreeView class for parameter value list in DataStoreForm.
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.open_in_editor_action = None

    def create_context_menu(self):
        """Creates a context menu for this view."""
        super().create_context_menu()
        self.open_in_editor_action = self._menu.addAction("Open in editor...", self.open_in_editor)

    def update_actions_visibility(self, item):
        """See base class."""
        self.open_in_editor_action.setVisible(item.item_type == "value")

    def open_in_editor(self):
        """Opens the parameter value editor for the first selected cell."""
        index = self.currentIndex()
        self._data_store_form.show_parameter_value_editor(index)

    def remove_selected(self):
        """See base class."""
        if not self.selectionModel().hasSelection():
            return
        db_map_typed_data_to_rm = {}
        db_map_data_to_upd = {}
        items = [self.model().item_from_index(index) for index in self.selectionModel().selectedIndexes()]
        for db_item in self.model()._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"parameter value list": []}
            db_map_data_to_upd[db_item.db_map] = []
            for list_item in reversed(db_item.children[:-1]):
                if list_item.id:
                    if list_item in items:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter value list"].append(
                            {"id": list_item.id, "name": list_item.name}
                        )
                        continue
                    curr_value_list = list_item.value_list
                    new_value_list = [
                        value
                        for value_item, value in zip(list_item.children, curr_value_list)
                        if value_item not in items
                    ]
                    if not new_value_list:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter value list"].append(
                            {"id": list_item.id, "name": list_item.name}
                        )
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
