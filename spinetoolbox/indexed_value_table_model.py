######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
A model for indexed parameter values, used by the parameter value editors editors.

:authors: A. Soininen (VTT)
:date:   18.6.2019
"""

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal


class IndexedValueTableModel(QAbstractTableModel):

    def __init__(self, indexes, values, text_to_index, text_to_value, parent=None):
        super().__init__(parent)
        self._indexes = indexes
        self._index_header = ""
        self._fixed_indexes = False
        self._text_to_index = text_to_index
        self._values = values
        self._value_header = ""
        self._text_to_value = text_to_value

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        if index.column() == 0:
            return str(self._indexes[index.row()])
        return float(self._values[index.row()])

    def flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 0 and self._fixed_indexes:
            return Qt.ItemIsSelectable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        return self._index_header if section == 0 else self._value_header

    def reset(self, indexes, values):
        self.beginResetModel()
        self._indexes = indexes
        self._values = values
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._indexes)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        if index.column() == 0:
            try:
                self._indexes[index.row()] = self._text_to_index(value)
            except ValueError:
                return False
        else:
            try:
                self._values[index.row()] = self._text_to_value(value)
            except ValueError:
                return False
        self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def set_fixed_indexes(self, fixed):
        self._fixed_indexes = fixed

    def set_index_header(self, header):
        self._index_header = header

    def set_value_header(self, header):
        self._value_header = header

    @property
    def indexes(self):
        return self._indexes

    @property
    def values(self):
        return self._values
