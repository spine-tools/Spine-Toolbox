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
from ..commands import RenameMapping


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, mapping_specifications, table_name, undo_stack):
        """
        Args:
            mapping_specifications (list of MappingSpecificationModel): mapping specifications
            table_name (str): source table name
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._mapping_specifications = []
        self._table_name = table_name
        self._undo_stack = undo_stack
        self._mapping_specifications = mapping_specifications.copy()
        self._names = [m.mapping_name for m in self._mapping_specifications]
        for k, m in enumerate(self._mapping_specifications):
            if not m.mapping_name:
                self._names[k] = m.mapping_name = self._make_new_mapping_name(counter=k)

    def _make_new_mapping_name(self, prefix="Mapping ", counter=0):
        while True:
            name = prefix + str(counter)
            if name not in self._names:
                return name
            counter += 1

    def flags(self, index):
        """Returns flags for given index."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

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
            return None
        if self._mapping_specifications and role in (Qt.DisplayRole, Qt.EditRole) and index.row() < self.rowCount():
            return self._names[index.row()]

    def setData(self, index, value, role=Qt.EditRole):
        """Renames a mapping."""
        if not value or role != Qt.EditRole or not index.isValid():
            return False
        row = index.row()
        if value in self._names[:row] + self._names[row:]:
            return False
        previous_name = self._names[row]
        self._undo_stack.push(RenameMapping(row, self, value, previous_name))
        return True

    def rename_mapping(self, row, name):
        """
        Renames a mapping.

        Args:
            row (int): mapping's row
            name (str): new name
        """
        self._names[row] = name
        self._mapping_specifications[row].mapping_name = name
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def add_mapping(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        m = ObjectClassMapping()
        name = self._make_new_mapping_name()
        specification = MappingSpecificationModel(self._table_name, name, m, self._undo_stack)
        self._mapping_specifications.append(specification)
        self._names.append(name)
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
            item_mappings (dict): item mappings
            table_name (str): name of the source table
        """
        self.beginResetModel()
        self._mapping_specifications.clear()
        self._names.clear()
        self._table_name = table_name
        for mapping_name, mapping in item_mappings.items():
            self._names.append(mapping_name)
            specification = MappingSpecificationModel(self._table_name, mapping_name, mapping, self._undo_stack)
            self._mapping_specifications.append(specification)
        self.endResetModel()
