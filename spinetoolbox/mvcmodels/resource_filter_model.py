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
Contains ResourceFilterModel.

:author: M. Marin (KTH)
:date:   26.11.2020
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spinedb_api import DatabaseMapping
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from spinetoolbox.helpers import busy_effect


class ResourceFilterModel(QStandardItemModel):
    _SELECT_ALL = "Select all"

    def __init__(self, link, parent=None):
        """
        Args:
            link (Link)
            parent (QObject,optional)
        """
        super().__init__(parent)
        self._link = link
        self._resources = {}
        self._block_updates = False
        self._setup_filter_methods = {
            SCENARIO_FILTER_TYPE: self._setup_scenario_filter,
            TOOL_FILTER_TYPE: self._setup_tool_filter,
        }

    @busy_effect
    def build_tree(self):
        """Builds the tree. Top level items are resource labels. Their children are filter types (scenario or tool).
        The children of filter type items are filter values (available scenario or tool names),
        that the user can check/uncheck to customize the filter.
        """
        self._resources.clear()
        resource_items = []
        for resource in self._link.upstream_resources:
            if resource.type_ != "database":
                continue
            resource_item = QStandardItem(resource.label)
            resource_items.append(resource_item)
            self._resources[resource.label] = resource
            filter_values = self._link.resource_filters.get(resource.label, {})
            for filter_type in filter_values:
                self._setup_filter(resource_item, filter_type)
        self.invisibleRootItem().appendRows(resource_items)

    def _is_leaf_index(self, index):
        """Whether or not the given index is a leaf.

        Args:
            QModelIndex

        Returns:
            bool
        """
        return index.parent().isValid() and self.rowCount(index) == 0

    @staticmethod
    def _get_resource_and_filter_type(index):
        """Returns the resource label and filter type corresponding to given leaf index.

        Args:
            QModelIndex

        Returns:
            tuple(str,str)
        """
        filter_index = index.parent()
        resource_index = filter_index.parent()
        filter_type = filter_index.data(Qt.UserRole + 1)
        resource = resource_index.data()
        return resource, filter_type

    def flags(self, index):  # pylint: disable=no-self-use
        flags = Qt.ItemIsEnabled
        if not index.parent().isValid():
            return flags | Qt.ItemIsDropEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.CheckStateRole:
            return super().data(index, role=role)
        if not self._is_leaf_index(index):
            return None
        resource, filter_type = self._get_resource_and_filter_type(index)
        if index.data() in self._link.resource_filters.get(resource, {}).get(filter_type, []):
            return Qt.Checked
        return Qt.Unchecked

    @Slot("QModelIndex")
    def _handle_index_clicked(self, index):
        """Toggles the checked state of the index if it's a leaf.
        This calls a method in the underlying Link object which in turn pushes a command to the undo stack...

        Args:
            QModelIndex
        """
        if not self._is_leaf_index(index):
            return
        resource, filter_type = self._get_resource_and_filter_type(index)
        self._link.toggle_filter_value(resource, filter_type, index.data())

    def refresh_filter(self, resource, filter_type, value):
        """Notifies changes in the model. Called by the underlying Link once changes are successfully done.

        Args:
            resource (str): resource label
            filter_type (str): filter type
            value (str): value that changes
        """
        self.layoutChanged.emit()
        # TODO: Try something better

    @property
    def resource_labels_iterator(self):
        """Yields resource labels in the model.

        Returns:
            Iterator
        """
        for row in range(self.invisibleRootItem().rowCount()):
            yield self.invisibleRootItem().child(row).text()

    def _filter_types_iterator(self, parent):
        """Yields filter types under given resource index.

        Args:
            parent (QModelIndex)

        Returns:
            Iterator
        """
        for row in range(self.rowCount(parent)):
            yield self.index(row, 0, parent).data()

    def canDropMimeData(self, data, drop_action, row, column, parent):
        filter_type = data.text()
        return (
            row == column == -1
            and parent.data() in set(self.resource_labels_iterator)
            and filter_type in self._setup_filter_methods
            and filter_type not in set(self._filter_types_iterator(parent))
        )

    def dropMimeData(self, data, drop_action, row, column, parent):
        filter_type = data.text()
        resource_item = self.itemFromIndex(parent)
        if filter_type in set(self._filter_types_iterator(parent)):
            return False
        self._setup_filter(resource_item, filter_type)
        return True

    def _setup_filter(self, resource_item, filter_type):
        """Creates a child for given resource item with given filter type.

        Args:
            resource_item (QStandardItem)
            filter_type (str)
        """
        filter_text = {SCENARIO_FILTER_TYPE: "Scenario filter", TOOL_FILTER_TYPE: "Tool filter"}[filter_type]
        filter_item = QStandardItem(filter_text)
        filter_item.setData(filter_type, role=Qt.UserRole + 1)
        resource_item.appendRow(filter_item)
        resource = self._resources[resource_item.text()]
        self._setup_filter_methods[filter_type](filter_item, resource)

    @staticmethod
    def _get_active_scenarios(resource):
        """Queries given resource for active scenarios and yields their names.

        Args:
            resource (ProjectItemResource)
        Returns:
            Iterator(str): scenario names
        """
        db_map = DatabaseMapping(resource.url)
        # pylint: disable=singleton-comparison
        for scenario in db_map.query(db_map.scenario_sq).filter(db_map.scenario_sq.c.active == True):
            yield scenario.name
        db_map.connection.close()

    @staticmethod
    def _get_tools(resource):
        """Queries given resource for tools and yields their names.

        Args:
            resource (ProjectItemResource)
        Returns:
            Iterator(str): scenario names
        """
        db_map = DatabaseMapping(resource.url)
        for tool in db_map.query(db_map.tool_sq):
            yield tool.name
        db_map.connection.close()

    def _setup_scenario_filter(self, filter_item, resource):
        """Creates children for given scenario filter item with active scenarios available from given resource.

        Args:
            filter_item (QStandardItem)
            resource (ProjectItemResource)
        """
        # FIXME
        # select_all_item = QStandardItem(self._SELECT_ALL)
        # scenario_items = [select_all_item]
        scenario_items = []
        for scenario in self._get_active_scenarios(resource):
            scenario_item = QStandardItem(scenario)
            scenario_items.append(scenario_item)
        filter_item.appendRows(scenario_items)

    def _setup_tool_filter(self, filter_item, resource):
        """Creates children for given tool filter item with tools available from given resource.

        Args:
            filter_item (QStandardItem)
            resource (ProjectItemResource)
        """
        # FIXME
        # select_all_item = QStandardItem(self._SELECT_ALL)
        # tool_items = [select_all_item]
        tool_items = []
        for tool in self._get_tools(resource):
            tool_item = QStandardItem(tool)
            tool_items.append(tool_item)
        filter_item.appendRows(tool_items)
