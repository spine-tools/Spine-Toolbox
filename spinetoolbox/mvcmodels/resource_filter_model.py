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

from PySide2.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spinedb_api import DatabaseMapping
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from spinetoolbox.helpers import busy_effect


class ResourceFilterModel(QStandardItemModel):

    tree_built = Signal()
    _SELECT_ALL = "Select all"

    def __init__(self, link, parent):
        """
        Args:
            link (Link)
            parent (QObject)
        """
        super().__init__(parent)
        self._link = link
        self._all_resource_filter_values = {}
        self._worker = _Worker([r for r in link.upstream_resources if r.type_ == "database"], parent)
        self._worker.finished.connect(self._do_build_tree)
        self.destroyed.connect(lambda obj=None: self._worker.tear_down())

    @busy_effect
    def build_tree(self):
        """Builds the tree. Top level items are resource labels. Their children are filter types (scenario or tool).
        The children of filter type items are filter values (available scenario or tool names),
        that the user can check/uncheck to customize the filter.
        """
        self._worker.start()

    @Slot(dict)
    def _do_build_tree(self, resource_filter_values):
        self._all_resource_filter_values = resource_filter_values
        resource_items = []
        for resource, filters in resource_filter_values.items():
            resource_item = QStandardItem(resource)
            resource_items.append(resource_item)
            filter_items = []
            for filter_type, values in filters.items():
                filter_text = {SCENARIO_FILTER_TYPE: "Scenario filter", TOOL_FILTER_TYPE: "Tool filter"}[filter_type]
                filter_item = QStandardItem(filter_text)
                filter_item.setData(filter_type, role=Qt.UserRole + 1)
                filter_items.append(filter_item)
                select_all_item = QStandardItem(self._SELECT_ALL)
                value_items = [select_all_item]
                for value in values:
                    value_item = QStandardItem(value)
                    value_items.append(value_item)
                filter_item.appendRows(value_items)
            resource_item.appendRows(filter_items)
        self.invisibleRootItem().appendRows(resource_items)
        self._worker.tear_down()
        self.tree_built.emit()

    def flags(self, index):  # pylint: disable=no-self-use
        return Qt.ItemIsEnabled

    def _is_leaf_index(self, index):
        """Returns whether or not the given index is a leaf.

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

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.CheckStateRole:
            return super().data(index, role=role)
        if not self._is_leaf_index(index):
            return None
        resource, filter_type = self._get_resource_and_filter_type(index)
        values = self._link.resource_filters.get(resource, {}).get(filter_type, [])
        if index.data(Qt.DisplayRole) == self._SELECT_ALL:
            all_values = self._all_resource_filter_values.get(resource, {}).get(filter_type, [])
            return Qt.Checked if len(values) == len(all_values) > 0 else Qt.Unchecked
        return Qt.Checked if index.data() in values else Qt.Unchecked

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
        if index.data() == self._SELECT_ALL:
            values = self._link.resource_filters.get(resource, {}).get(filter_type, [])
            if index.data(Qt.CheckStateRole) == Qt.Unchecked:
                all_values = self._all_resource_filter_values.get(resource, {}).get(filter_type, [])
                self._link.toggle_filter_values(resource, filter_type, *(set(all_values) - set(values)))
            else:
                self._link.toggle_filter_values(resource, filter_type, *values)
            return
        self._link.toggle_filter_values(resource, filter_type, index.data())

    def refresh_filter(self, resource, filter_type, values):
        """Notifies changes in the model. Called by the underlying Link once changes are successfully done.

        Args:
            resource (str): resource label
            filter_type (str): filter type
            values (Iterable): values that change
        """
        self.layoutChanged.emit()


class _Worker(QObject):

    finished = Signal(dict)

    def __init__(self, resources, parent):
        super().__init__()
        self._resources = resources
        self._thread = QThread(parent)
        self.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)

    def start(self):
        self._thread.start()

    def do_work(self):
        resource_filter_values = {}
        for resource in self._resources:
            db_map = DatabaseMapping(resource.url)
            # pylint: disable=singleton-comparison
            scenarios = [x.name for x in db_map.query(db_map.scenario_sq).filter(db_map.scenario_sq.c.active == True)]
            tools = [x.name for x in db_map.query(db_map.tool_sq)]
            db_map.connection.close()
            resource_filter_values[resource.label] = {SCENARIO_FILTER_TYPE: scenarios, TOOL_FILTER_TYPE: tools}
        self.finished.emit(resource_filter_values)

    def tear_down(self):
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
