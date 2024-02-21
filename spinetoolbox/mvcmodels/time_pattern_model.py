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

"""A model for time patterns, used by the parameter_value editors."""
import numpy as np
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QMessageBox
from spinedb_api import TimePattern, ParameterValueFormatError
from .indexed_value_table_model import IndexedValueTableModel


class TimePatternModel(IndexedValueTableModel):
    """A model for time pattern type parameter values."""

    def flags(self, index):
        """Returns flags at index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new time period - value pairs into the pattern.

        New time periods are initialized to empty strings and the corresponding values to zeros.

        Args:
            row (int): an index where to insert the new data
            count (int): number of time period - value pairs to insert
            parent (QModelIndex): an index to a parent model
        Returns:
            bool: True if the operation was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        old_indexes = self._value.indexes
        old_values = self._value.values
        new_indexes = list(old_indexes)
        for _ in range(count):
            new_indexes.insert(row, "")
        if row == len(old_values):
            new_values = np.append(old_values, np.zeros(count))
        else:
            new_values = np.insert(old_values, row, np.zeros(count))
        self._value = TimePattern(new_indexes, new_values)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes time period - value pairs from the pattern.

        Args:
            row (int): an index where to remove the data
            count (int): number of time period - value pairs to remove
            parent (QModelIndex): an index to a parent model

        Returns:
            bool: True if the operation was successful
        """
        if len(self._value) == 1:
            return False
        if count == len(self._value):
            count = len(self._value) - 1
            row = 1
        self.beginRemoveRows(parent, row, row + count - 1)
        old_indexes = self._value.indexes
        old_values = self._value.values
        new_indexes = list(old_indexes)
        del new_indexes[row : row + count]
        remove_indexes = range(row, row + count) if count > 1 else row
        new_values = np.delete(old_values, remove_indexes)
        self._value = TimePattern(new_indexes, new_values)
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        Sets a time period or a value in the pattern.

        Column index 0 corresponds to the time periods while 1 corresponds to the values.

        Args:
            index (QModelIndex): an index to the model
            value (str, float): a new time period or value
            role (int): a role
        Returns:
            bool: True if the operation was successful
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row = index.row()
        if row == len(self._value):
            self.insertRow(row)
        if index.column() == 0:
            try:
                self._value.indexes[row] = value
            except ParameterValueFormatError as error:
                QMessageBox.warning(self.parent(), "Error", str(error))
                return False
        else:
            self._value.values[row] = value
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
        return True

    def batch_set_data(self, indexes, values):
        """
        Sets data for several indexes at once.

        Args:
            indexes (Sequence): a sequence of model indexes
            values (Sequence): a sequence of time periods/floats corresponding to the indexes
        """
        modified_rows = list()
        modified_columns = list()
        for index, value in zip(indexes, values):
            row = index.row()
            modified_rows.append(row)
            column = index.column()
            modified_columns.append(column)
            if column == 0:
                self._value.indexes[row] = value
            else:
                self._value.values[row] = value
        left_top = self.index(min(modified_rows), min(modified_columns))
        right_bottom = self.index(max(modified_rows), max(modified_columns))
        self.dataChanged.emit(left_top, right_bottom, [Qt.ItemDataRole.EditRole])
