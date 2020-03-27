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
    def __init__(self):
        super().__init__()
        self._data = list()
        self._data_type = float

    def array(self):
        return Array(self._data, self._data_type)

    def batch_set_data(self, indexes, values):
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
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            element = self._data[index.row()]
            if isinstance(element, (float, str)):
                return element
            elif isinstance(element, _ErrorCell):
                return "Error"
            return str(element)
        elif role == Qt.EditRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return element.edit_value
            return to_database(self._data[index.row()])
        elif role == Qt.ToolTipRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return element.tooltip
            return str(element)
        elif role == Qt.BackgroundColorRole:
            element = self._data[index.row()]
            if isinstance(element, _ErrorCell):
                return QColor(255, 128, 128)
            return None
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section
        return "Value"

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        filler = count * [self._data_type()]
        self._data = self._data[:row] + filler + self._data[row:]
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        self._data = self._data[:row] + self._data[row + count :]
        self.endRemoveRows()
        return True

    def reset(self, value):
        self.beginResetModel()
        self._data = list(value.values)
        self._data_type = value.value_type
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def set_array_type(self, new_type):
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
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            self._set_data(index, value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundColorRole])
            return True
        return False

    def _set_data(self, index, value):
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
    def __init__(self, edit_value, tooltip):
        self.edit_value = edit_value
        self.tooltip = tooltip
