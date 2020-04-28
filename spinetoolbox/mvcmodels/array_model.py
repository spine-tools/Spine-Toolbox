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
Contains logic for the fixed step time series editor widget.

:author: A. Soininen (VTT)
:date:   14.6.2019
"""

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtGui import QColor
from spinedb_api import Array, from_database, ParameterValueFormatError, to_database


class ArrayModel(QAbstractTableModel):
    """
    Model for the Array parameter value type.

    Even if the array is empty this model's rowCount() will still return 1.
    This is to show an empty row in the table view.
    """

    def __init__(self):
        super().__init__()
        self._data = list()
        self._data_type = float

    def array(self):
        """Returns the array modeled by this model."""
        return Array(self._data, self._data_type)

    def batch_set_data(self, indexes, values):
        """Sets data at multiple indexes at once."""
        if not indexes:
            return
        top_row = indexes[0].row()
        bottom_row = top_row
        for index, value in zip(indexes, values):
            row = index.row()
            top_row = min(top_row, row)
            bottom_row = max(bottom_row, row)
            self._set_data(index, value)
        top_left = self.index(top_row, 0)
        bottom_right = self.index(bottom_row, 0)
        self.dataChanged.emit(
            top_left, bottom_right, [Qt.BackgroundColorRole, Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]
        )

    def columnCount(self, parent=QModelIndex()):
        """Returns 1."""
        return 1

    def data(self, index, role=Qt.DisplayRole):
        """Returns model's data for given role."""
        if not index.isValid() or not self._data:
            return None
        if role == Qt.DisplayRole:
            element = self._data[index.row()]
            if isinstance(element, (float, str)):
                return element
            if isinstance(element, _ErrorCell):
                return "Error"
            return str(element)
        if role == Qt.EditRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return element.edit_value
            return to_database(self._data[index.row()])
        if role == Qt.ToolTipRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return element.tooltip
            return str(element)
        if role == Qt.BackgroundColorRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return QColor(255, 128, 128)
            return None
        return None

    def flags(self, index):
        """Returns table cell's flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns header data."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section
        return "Value"

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts rows to the array."""
        # In case the array is initially empty we need to add an extra cell to account for the virtual empty cell.
        self.beginInsertRows(parent, row, row + count - 1)
        filler_size = count if self._data else count + 1
        filler = filler_size * [self._data_type()]
        self._data = self._data[:row] + filler + self._data[row:]
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes rows from the array."""
        # Some special handling is needed if the array becomes empty after the operation.
        if not self._data:
            return False
        if row == 0:
            if len(self._data) == 1:
                self._data.clear()
                self.dataChanged.emit(
                    self.index(0, 0), self.index(0, 0), [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundColorRole]
                )
                return False
        first_row = row if count < len(self._data) else 1
        self.beginRemoveRows(parent, first_row, row + count - 1)
        self._data = self._data[:row] + self._data[row + count :]
        self.endRemoveRows()
        if not self._data:
            self.dataChanged.emit(
                self.index(0, 0), self.index(0, 0), [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundColorRole]
            )
        return True

    def reset(self, value):
        """
        Resets the model to a new array.

        Args:
            value (Array): a new array to model
        """
        self.beginResetModel()
        self._data = list(value.values)
        self._data_type = value.value_type
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the length of the array.

        Note: returns 1 even if the array is empty.
        """
        if not self._data:
            return 1
        return len(self._data)

    def set_array_type(self, new_type):
        """Changes the data type of array's elements."""
        if new_type == self._data_type:
            return
        self.beginResetModel()
        try:
            self._data = [new_type(x) for x in self._data]
        except (ParameterValueFormatError, TypeError, ValueError):
            self._data = len(self._data) * [new_type()]
        self._data_type = new_type
        self.endResetModel()

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the value at given index."""
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            self._set_data(index, value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundColorRole])
            return True
        return False

    def _set_data(self, index, value):
        """
        Sets data for given index.

        In case of errors the value at index is replaced by an ``_ErrorCell`` sentinel.

        Args:
            index (QModelIndex): an index
            value (str): value in database format
        """
        if not self._data:
            self._data = [None]
        try:
            element = from_database(value)
        except ParameterValueFormatError as error:
            self._data[index.row()] = _ErrorCell(value, f"Cannot parse: {error}")
        else:
            if not isinstance(element, self._data_type):
                self._data[index.row()] = _ErrorCell(
                    value, f"Expected '{self._data_type.__name__}', not {type(element).__name__}"
                )
            else:
                self._data[index.row()] = element


class _ErrorCell:
    """A sentinel class to mark erroneous cells in the table."""

    def __init__(self, edit_value, tooltip):
        """
        Args:
            edit_value (str): the JSON string that caused the error
            tooltip (str): tooltip that should be shown on the table cell
        """
        self.edit_value = edit_value
        self.tooltip = tooltip
