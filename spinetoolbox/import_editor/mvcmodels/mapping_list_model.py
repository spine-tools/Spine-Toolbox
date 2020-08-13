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
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt
from spinedb_api import ObjectClassMapping
from .mapping_specification_model import MappingSpecificationModel


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, item_mappings, table_name, undo_stack):
        super().__init__()
        self._mapping_specifications = []
        self._names = []
        self._counter = 1
        self._table_name = table_name
        self._undo_stack = undo_stack
        for m in item_mappings:
            name = "Mapping " + str(self._counter)
            self._names.append(name)
            specification = MappingSpecificationModel(self._table_name, name, m, self._undo_stack)
            self._mapping_specifications.append(specification)
            self._counter += 1

    def get_mappings(self):
        return [m.mapping for m in self._mapping_specifications]

    @property
    def mapping_specifications(self):
        return self._mapping_specifications

    def mapping_specification(self, name):
        try:
            row = self._names.index(name)
        except ValueError:
            return None
        return self._mapping_specifications[row]

    def mapping_name_at(self, row):
        return self._names[row]

    def rowCount(self, index=None):
        if not self._mapping_specifications:
            return 0
        return len(self._mapping_specifications)

    def row_for_mapping(self, name):
        try:
            return self._names.index(name)
        except ValueError:
            return None

    def data_mapping(self, index):
        if self._mapping_specifications and index.row() < len(self._mapping_specifications):
            return self._mapping_specifications[index.row()]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if self._mapping_specifications and role == Qt.DisplayRole and index.row() < self.rowCount():
            return self._names[index.row()]

    def add_mapping(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        m = ObjectClassMapping()
        name = "Mapping " + str(self._counter)
        specification = MappingSpecificationModel(self._table_name, name, m, self._undo_stack)
        self._mapping_specifications.append(specification)
        self._names.append(name)
        self._counter += 1
        self.endInsertRows()
        return name

    def insert_mapping_specification(self, name, row, specification):
        self.beginInsertRows(QModelIndex(), row, row)
        self._names.insert(row, name)
        self._mapping_specifications.insert(row, specification)
        self.endInsertRows()

    def remove_mapping(self, row):
        if row < 0 or row >= len(self._mapping_specifications):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        specification = self._mapping_specifications.pop(row)
        self._names.pop(row)
        self.endRemoveRows()
        return specification

    def check_mapping_validity(self):
        """
        Checks if there are any issues with the mappings.

        Returns:
             dict: a map from mapping name to discovered issue; contains only mappings that have issues
        """
        issues = dict()
        for name, mapping in zip(self._names, self._mapping_specifications):
            issue = mapping.check_mapping_validity()
            if issue:
                issues[name] = issue
        return issues

    def reset(self, item_mappings, table_name):
        """
        Resets the model.

        Args:
            item_mappings (Iterable): item mappings
            table_name (src): name of the source table
        """
        self.beginResetModel()
        self._mapping_specifications.clear()
        self._names.clear()
        self._counter = 1
        self._table_name = table_name
        for m in item_mappings:
            name = "Mapping " + str(self._counter)
            self._names.append(name)
            specification = MappingSpecificationModel(self._table_name, name, m, self._undo_stack)
            self._mapping_specifications.append(specification)
            self._counter += 1
        self.endResetModel()
