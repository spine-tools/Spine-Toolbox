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
Contains the mapping list model.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from PySide2.QtCore import Qt, QAbstractListModel
from spinedb_api import (
    ObjectClassMapping,
)
from .mapping_specification_model import MappingSpecificationModel


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, mapping_list, table_name, parent=None):
        super().__init__(parent)
        self._qmappings = []
        self._names = []
        self._counter = 1
        self._table_name = table_name
        self.set_model(mapping_list)

    def set_model(self, model):
        self.beginResetModel()
        self._names = []
        self._qmappings = []
        for m in model:
            self._names.append("Mapping " + str(self._counter))
            self._qmappings.append(MappingSpecificationModel(m, self._table_name))
            self._counter += 1
        self.endResetModel()

    def get_mappings(self):
        return [m._item_mapping for m in self._qmappings]

    def rowCount(self, index=None):
        if not self._qmappings:
            return 0
        return len(self._qmappings)

    def data_mapping(self, index):
        if self._qmappings and index.row() < len(self._qmappings):
            return self._qmappings[index.row()]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if self._qmappings and role == Qt.DisplayRole and index.row() < self.rowCount():
            return self._names[index.row()]

    def add_mapping(self):
        self.beginInsertRows(self.index(self.rowCount(), 0), self.rowCount(), self.rowCount())
        m = ObjectClassMapping()
        self._qmappings.append(MappingSpecificationModel(m, self._table_name))
        self._names.append("Mapping " + str(self._counter))
        self._counter += 1
        self.endInsertRows()

    def remove_mapping(self, row):
        if self._qmappings and row < len(self._qmappings):
            self.beginRemoveRows(self.index(row, 0), row, row)
            self._qmappings.pop(row)
            self._names.pop(row)
            self.endRemoveRows()

    def check_mapping_validity(self):
        """
        Checks if there are any issues with the mappings.

        Returns:
             dict: a map from mapping name to discovered issue; contains only mappings that have issues
        """
        issues = dict()
        for name, mapping in zip(self._names, self._qmappings):
            issue = mapping.check_mapping_validity()
            if issue:
                issues[name] = issue
        return issues
