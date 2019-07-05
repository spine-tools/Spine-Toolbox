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
A model for fixed resolution time series, used by the parameter value editors.

:authors: A. Soininen (VTT)
:date:   4.7.2019
"""

import numpy as np
from PySide2.QtCore import QModelIndex, Qt, Slot
from spinedb_api import TimeSeriesFixedResolution
from indexed_value_table_model import IndexedValueTableModel


class TimeSeriesModelFixedResolution(IndexedValueTableModel):
    def __init__(self, series):
        super().__init__(series, "Time stamp", "Values")
        self._index_cache = self._value.indexes

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if index.column() == 0:
            return str(self._index_cache[index.row()])
        return float(self._value.values[index.row()])

    def flags(self, index):
        """Returns flags at index."""
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    @property
    def indexes(self):
        return self._index_cache

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        old_values = self._value.values
        if row == len(old_values):
            new_values = np.append(old_values, np.zeros(count))
        else:
            insert_indexes = range(row, row + count - 1) if count > 1 else row
            new_values = np.insert(old_values, insert_indexes, np.zeros(count))
        self._value = TimeSeriesFixedResolution(
            self._value.start, self._value.resolution, new_values, self._value.ignore_year, self._value.repeat
        )
        self._index_cache = self._value.indexes
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if len(self._value) == 2:
            return False
        if count == len(self._value):
            count = len(self._value) - 2
            row = 2
        self.beginRemoveRows(parent, row, row + count - 1)
        old_values = self._value.values
        remove_indexes = range(row, row + count) if count > 1 else row
        new_values = np.delete(old_values, remove_indexes)
        self._value = TimeSeriesFixedResolution(
            self._value.start, self._value.resolution, new_values, self._value.ignore_year, self._value.repeat
        )
        self._index_cache = self._value.indexes
        self.endRemoveRows()
        return True

    def reset(self, value):
        self.beginResetModel()
        self._value = value
        self._index_cache = self._value.indexes
        self.endResetModel()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        self._value.values[index.row()] = value
        return True

    @Slot(bool, name="set_ignore_year")
    def set_ignore_year(self, ignore_year):
        self._value.ignore_year = ignore_year

    @Slot(bool, name="set_repeat")
    def set_repeat(self, repeat):
        self._value.repeat = repeat

    def set_resolution(self, resolution):
        self._value.resolution = resolution
        self._index_cache = self._value.indexes
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    def set_start(self, start):
        self._value.start = start
        self._index_cache = self._value.indexes
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    @property
    def values(self):
        return self._value.values
