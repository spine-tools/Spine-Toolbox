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

from PySide2.QtWidgets import QTreeView
from PySide2.QtCore import Signal, Slot, Qt, QEvent
from PySide2.QtGui import QMouseEvent
from spinetoolbox.widgets.custom_qtreeview import CopyTreeView
from spinetoolbox.helpers import busy_effect


class EntityTreeView(CopyTreeView):
    """Custom QTreeView class for object tree in DataStoreForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    editing_requested = Signal(dict)
    removing_requested = Signal(dict)
    export_requested = Signal(dict)
    entity_selection_changed = Signal(dict)

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.selected_indexes = {}

    def connect_signals(self):
        self.expanded.connect(self._resize_first_column_to_contents)
        self.collapsed.connect(self._resize_first_column_to_contents)
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)

    @Slot("QModelIndex")
    def _resize_first_column_to_contents(self, _index=None):
        self.resizeColumnToContents(0)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_selection_changed(self, selected, deselected):
        """Classifies selection by item type and emits signal."""
        self.selected_indexes.clear()
        model = self.model()
        indexes = self.selectionModel().selectedIndexes()
        for index in indexes:
            if not index.isValid() or index.column() != 0:
                continue
            item_type = model.item_from_index(index).item_type
            self.selected_indexes.setdefault(item_type, {})[index] = None
        if not any(self.selected_indexes.values()):
            return
        self.entity_selection_changed.emit(self.selected_indexes)

    def clear_any_selections(self):
        """Clears the selection if any."""
        selection_model = self.selectionModel()
        if selection_model.hasSelection():
            selection_model.clearSelection()

    @busy_effect
    def fully_expand(self):
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
        self.collapsed.disconnect(self._resize_first_column_to_contents)
        model = self.model()
        for index in self.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in model.visit_all(index):
                self.collapse(model.index_from_item(item))
        self.collapsed.connect(self._resize_first_column_to_contents)
        self._resize_first_column_to_contents()

    @Slot("QModelIndex", "EditTrigger", "QEvent")
    def edit(self, index, trigger, event):
        """Send signal instead of editing item, so
        DataStoreForm can catch this signal and open a custom QDialog
        for edition.
        """
        if trigger == QTreeView.EditKeyPressed:
            self.edit_selected()
        return False

    def has_selection(self):
        return self.selectionModel().hasSelection()

    def edit_selected(self):
        if not self.has_selection():
            return
        self.editing_requested.emit(self.selected_indexes)

    def remove_selected(self):
        if not self.has_selection():
            return
        self.removing_requested.emit(self.selected_indexes)

    def export_selected(self):
        if not self.has_selection():
            return
        self.export_requested.emit(self.selected_indexes)


class StickySelectionEntityTreeView(EntityTreeView):
    """Custom QTreeView class for object tree in DataStoreForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def mousePressEvent(self, event):
        """Overrides selection behaviour if the user has selected sticky
        selection in Settings. If sticky selection is enabled, multi-selection is
        enabled when selecting items in the Object tree. Pressing the Ctrl-button down,
        enables single selection. If sticky selection is disabled, single selection is
        enabled and pressing the Ctrl-button down enables multi-selection.

        Args:
            event (QMouseEvent)
        """
        sticky_selection = self.qsettings.value("appSettings/stickySelection", defaultValue="false")
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


class ParameterValueListTreeView(CopyTreeView):
    """Custom QTreeView class for parameter value list in DataStoreForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def remove_selected(self):
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
                    curr_value_list = list_item.compile_value_list()
                    value_list = [
                        value
                        for value_item, value in zip(list_item.children, curr_value_list)
                        if value_item not in items
                    ]
                    if not value_list:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter value list"].append(
                            {"id": list_item.id, "name": list_item.name}
                        )
                        continue
                    if value_list != curr_value_list:
                        item = {"id": list_item.id, "value_list": value_list}
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
