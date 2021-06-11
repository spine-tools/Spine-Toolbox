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
Contains ResourceFilterModel.

:author: M. Marin (KTH)
:date:   26.11.2020
"""
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from ..project_commands import SetFiltersOnlineCommand


class ResourceFilterModel(QStandardItemModel):

    tree_built = Signal()
    _SELECT_ALL = "Select all"
    _FILTER_TYPES = {"Scenario filter": SCENARIO_FILTER_TYPE, "Tool filter": TOOL_FILTER_TYPE}
    _FILTER_TYPE_TO_TEXT = dict(zip(_FILTER_TYPES.values(), _FILTER_TYPES.keys()))
    _ID_ROLE = Qt.UserRole + 1

    def __init__(self, connection, undo_stack, logger):
        """
        Args:
            connection (Connection): link whose resources to model
            undo_stack (QUndoStack): an undo stack
            logger (LoggerInterface): a logger
        """
        super().__init__()
        self._connection = connection
        self._undo_stack = undo_stack
        self._logger = logger

    @property
    def connection(self):
        return self._connection

    def build_tree(self):
        """Rebuilds model's contents."""

        def append_filter_items(parent_item, filters, filter_type):
            for id_, is_on in filters[filter_type].items():
                filter_item = QStandardItem(self._connection.id_to_name(id_, filter_type))
                filter_item.setData(id_, self._ID_ROLE)
                filter_item.setData(Qt.Checked if is_on else Qt.Unchecked, Qt.CheckStateRole)
                filter_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                parent_item.appendRow(filter_item)

        self.clear()
        self.setHorizontalHeaderItem(0, QStandardItem("DB resource filters"))
        self._connection.fetch_database_items()
        for resource_label, filters_by_type in self._connection.resource_filters.items():
            root_item = QStandardItem(resource_label)
            root_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.appendRow(root_item)
            for name, type_ in self._FILTER_TYPES.items():
                filter_parent = QStandardItem(name)
                if not filters_by_type.get(type_):
                    no_filters_item = QStandardItem("None available")
                    no_filters_item.setFlags(Qt.ItemIsSelectable)
                    filter_parent.appendRow(no_filters_item)
                    root_item.appendRow(filter_parent)
                    continue
                filter_parent.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                select_all_item = QStandardItem(self._SELECT_ALL)
                select_all_item.setData(False, Qt.CheckStateRole)
                select_all_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                filter_parent.appendRow(select_all_item)
                root_item.appendRow(filter_parent)
                append_filter_items(filter_parent, filters_by_type, type_)
                self._set_all_selected_item(resource_label, filter_parent)

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.CheckStateRole:
            return super().setData(index, value, role)
        self._change_filter_checked_state(index, value == Qt.Checked)
        return True

    def _change_filter_checked_state(self, index, is_on):
        """Changes the online status of the filter item at index.

        Args:
            index (QModelIndex): item's index
            is_on (bool): True if filter are turned online, False otherwise
        """
        item = self.itemFromIndex(index)
        if item.hasChildren():
            return
        resource_type_item = item.parent()
        filter_type = self._FILTER_TYPES[resource_type_item.text()]
        root_item = resource_type_item.parent()
        resource_label = root_item.text()
        if item.text() == self._SELECT_ALL:
            ids = self._connection.resource_filters.get(resource_label, {}).get(filter_type, {}).keys()
            activated = {id_: is_on for id_ in ids}
            cmd = SetFiltersOnlineCommand(self, resource_label, filter_type, activated)
        else:
            cmd = SetFiltersOnlineCommand(self, resource_label, filter_type, {item.data(self._ID_ROLE): is_on})
        self._undo_stack.push(cmd)

    def set_online(self, resource, filter_type, online):
        """Sets the given filters online or offline.

        Args:
            resource (str): Resource label
            filter_type (str): Either SCENARIO_FILTER_TYPE or TOOL_FILTER_TYPE, for now.
            online (dict): mapping from scenario/tool id to online flag
        """
        self._connection.set_online(resource, filter_type, online)
        filter_type_item = self._find_filter_type_item(resource, filter_type)
        for row in range(filter_type_item.rowCount()):
            filter_item = filter_type_item.child(row)
            is_on = online.get(filter_item.data(self._ID_ROLE), None)
            if is_on is not None:
                checked = Qt.Checked if is_on else Qt.Unchecked
                if filter_item.data(Qt.CheckStateRole) != checked:
                    filter_item.setData(checked, Qt.CheckStateRole)
                    self.dataChanged.emit(filter_item.index(), filter_item.index(), [Qt.CheckStateRole])
        self._set_all_selected_item(resource, filter_type_item, True)

    def _find_filter_type_item(self, resource, filter_type):
        """Searches for filter type item.

        Args:
            resource (str): resource label
            filter_type (str): filter type identifier

        Returns:
            QStandardItem: filter type item or None if not found
        """
        root_item = self.findItems(resource)[0]
        filter_type_item = None
        filter_type_text = self._FILTER_TYPE_TO_TEXT[filter_type]
        for row in range(root_item.rowCount()):
            filter_type_item = root_item.child(row)
            if filter_type_item.text() == filter_type_text:
                break
        return filter_type_item

    def _set_all_selected_item(self, resource, filter_type_item, emit_data_changed=False):
        """Updates 'Select All' item's checked state.

         Args:
             resource (str): resource label
             filter_type_item (QStandardItem): filter type item
             emit_data_changed (bool): if True, emit dataChanged signal if the state was updated
         """
        all_online = all(
            self._connection.resource_filters[resource][self._FILTER_TYPES[filter_type_item.text()]].values()
        )
        all_selected_item = filter_type_item.child(0)
        all_selected = all_selected_item.data(Qt.CheckStateRole) == Qt.Checked
        if all_selected != all_online:
            checked = Qt.Checked if all_online else Qt.Unchecked
            all_selected_item.setData(checked, Qt.CheckStateRole)
            if emit_data_changed:
                self.dataChanged.emit(all_selected_item.index(), all_selected_item.index(), [Qt.CheckStateRole])
