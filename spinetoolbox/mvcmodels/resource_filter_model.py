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

""" Contains ResourceFilterModel. """
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem
from spinedb_api.filters.alternative_filter import ALTERNATIVE_FILTER_TYPE
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from ..project_commands import SetFiltersOnlineCommand


class ResourceFilterModel(QStandardItemModel):
    tree_built = Signal()
    _SELECT_ALL = "Select all"
    FILTER_TYPES = {"Scenario filter": SCENARIO_FILTER_TYPE, "Alternative filter": ALTERNATIVE_FILTER_TYPE}
    FILTER_TYPE_TO_TEXT = dict(zip(FILTER_TYPES.values(), FILTER_TYPES.keys()))

    def __init__(self, connection, project, undo_stack, logger):
        """
        Args:
            connection (LoggingConnection): connection whose resources to model
            project (SpineToolboxProject): project
            undo_stack (QUndoStack): an undo stack
            logger (LoggerInterface): a logger
        """
        super().__init__()
        self._connection = connection
        self._project = project
        self._undo_stack = undo_stack
        self._logger = logger

    @property
    def connection(self):
        return self._connection

    def build_tree(self):
        """Rebuilds model's contents."""

        def append_filter_items(parent_item, filter_names, filter_type, online, online_default, enabled):
            for name in filter_names[filter_type]:
                filter_item = QStandardItem(name)
                filter_item.setCheckState(
                    Qt.CheckState.Checked if online.get(name, online_default) else Qt.CheckState.Unchecked
                )
                filter_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                filter_item.setEnabled(enabled)
                parent_item.appendRow(filter_item)

        self.clear()
        self.setHorizontalHeaderItem(0, QStandardItem("DB resource filters"))
        filters = self.fetch_filters()
        for resource_label, filters_by_type in filters.items():
            root_item = QStandardItem(resource_label)
            root_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.appendRow(root_item)
            for type_label, type_ in self.FILTER_TYPES.items():
                filter_parent = QStandardItem(type_label)
                if not filters_by_type.get(type_):
                    no_filters_item = QStandardItem("None available")
                    no_filters_item.setFlags(Qt.ItemIsSelectable)
                    filter_parent.appendRow(no_filters_item)
                    root_item.appendRow(filter_parent)
                    continue
                filter_enabled = self._connection.is_filter_type_enabled(type_)
                filter_parent.setFlags(Qt.ItemIsSelectable)
                filter_parent.setEnabled(filter_enabled)
                select_all_item = QStandardItem(self._SELECT_ALL)
                select_all_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                select_all_item.setCheckState(Qt.CheckState.Unchecked)
                select_all_item.setEnabled(filter_enabled)
                filter_parent.appendRow(select_all_item)
                root_item.appendRow(filter_parent)
                online_filters = self._connection.online_filters(resource_label, type_)
                append_filter_items(
                    filter_parent,
                    filters_by_type,
                    type_,
                    online_filters,
                    self._connection.is_filter_online_by_default,
                    filter_enabled,
                )
                self._set_all_selected_item(resource_label, filter_parent)
        self.tree_built.emit()

    def fetch_filters(self):
        filters = {}
        for resource in self._connection.database_resources:
            url = resource.url
            if not url:
                continue
            for filter_type in (SCENARIO_FILTER_TYPE, ALTERNATIVE_FILTER_TYPE):
                names = self._connection.get_filter_item_names(filter_type, url)
                if names:
                    filters.setdefault(resource.label, {})[filter_type] = names
        return filters

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.CheckStateRole:
            return super().setData(index, value, role)
        self._change_filter_checked_state(index, value == Qt.CheckState.Checked.value)
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
        filter_type = self.FILTER_TYPES[resource_type_item.text()]
        root_item = resource_type_item.parent()
        resource_label = root_item.text()
        if item.text() == self._SELECT_ALL:
            activated = {resource_type_item.child(row).text(): is_on for row in range(1, resource_type_item.rowCount())}
            cmd = SetFiltersOnlineCommand(self._project, self.connection, resource_label, filter_type, activated)
        else:
            cmd = SetFiltersOnlineCommand(
                self._project, self.connection, resource_label, filter_type, {item.text(): is_on}
            )
        self._undo_stack.push(cmd)

    def set_online(self, resource, filter_type, online):
        """Sets the given filters online or offline.

        Args:
            resource (str): Resource label
            filter_type (str): Always SCENARIO_FILTER_TYPE, for now.
            online (dict): mapping from scenario/tool id to online flag
        """
        self.connection.set_online(resource, filter_type, online)
        self.connection.link.update_icons()
        filter_type_item = self._find_filter_type_item(resource, filter_type)
        for row in range(filter_type_item.rowCount()):
            filter_item = filter_type_item.child(row)
            is_on = online.get(filter_item.text(), None)
            if is_on is not None:
                checked = Qt.CheckState.Checked if is_on else Qt.CheckState.Unchecked
                if filter_item.data(Qt.ItemDataRole.CheckStateRole) != checked.value:
                    filter_item.setCheckState(checked)
                    self.dataChanged.emit(filter_item.index(), filter_item.index(), [Qt.ItemDataRole.CheckStateRole])
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
        filter_type_text = self.FILTER_TYPE_TO_TEXT[filter_type]
        for row in range(root_item.rowCount()):
            filter_type_item = root_item.child(row)
            if filter_type_item.text() == filter_type_text:
                break
        return filter_type_item

    def filter_type_items(self, filter_type):
        """An iterator to filter type items.

        Args:
            filter_type (str): filter type

        Yields:
            QStandardItem: filter type item
        """
        filter_text = self.FILTER_TYPE_TO_TEXT[filter_type]
        root_item = self.invisibleRootItem()
        for root_row in range(root_item.rowCount()):
            resource_item = root_item.child(root_row)
            for resource_row in range(resource_item.rowCount()):
                filter_type_item = resource_item.child(resource_row)
                if filter_type_item.text() == filter_text:
                    yield filter_type_item

    def _set_all_selected_item(self, resource, filter_type_item, emit_data_changed=False):
        """Updates 'Select All' item's checked state.

        Args:
            resource (str): resource label
            filter_type_item (QStandardItem): filter type item
            emit_data_changed (bool): if True, emit dataChanged signal if the state was updated
        """
        online_filters = self._connection.online_filters(resource, self.FILTER_TYPES[filter_type_item.text()])
        all_online = all(online_filters.values())
        all_selected_item = filter_type_item.child(0)
        all_selected = all_selected_item.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked.value
        if all_selected != all_online:
            checked = Qt.CheckState.Checked if all_online else Qt.CheckState.Unchecked
            all_selected_item.setCheckState(checked)
            if emit_data_changed:
                self.dataChanged.emit(
                    all_selected_item.index(), all_selected_item.index(), [Qt.ItemDataRole.CheckStateRole]
                )

    def set_filter_type_enabled(self, filter_type, enabled):
        """Enables or disables a filter type.

        Args:
            filter_type (str): filter type
            enabled (bool): whether the filter is enabled
        """
        filter_text = self.FILTER_TYPE_TO_TEXT[filter_type]
        root_item = self.invisibleRootItem()
        for root_row in range(root_item.rowCount()):
            resource_item = root_item.child(root_row)
            for resource_row in range(resource_item.rowCount()):
                filter_type_item = resource_item.child(resource_row)
                if filter_type_item.text() != filter_text:
                    continue
                filter_type_item.setEnabled(enabled)
                for filter_type_row in range(filter_type_item.rowCount()):
                    filter_item = filter_type_item.child(filter_type_row)
                    filter_item.setEnabled(enabled)
