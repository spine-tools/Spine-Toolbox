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
A model for variable resolution time series, used by the parameter value editors.

:authors: A. Soininen (VTT)
:date:   5.7.2019
"""

import numpy as np
from PySide2.QtCore import QModelIndex, Qt, Slot
from spinedb_api import TimeSeriesVariableResolution
from indexed_value_table_model import IndexedValueTableModel


class TimeSeriesModelVariableResolution(IndexedValueTableModel):
    def __init__(self, series):
        super().__init__(series, "Time stamp", "Values")

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if index.column() == 0:
            return str(self._value.indexes[index.row()])
        return float(self._value.values[index.row()])

    def flags(self, index):
        """Returns flags at index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    @property
    def indexes(self):
        return self._value.indexes

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        old_indexes = self._value.indexes
        old_values = self._value.values
        new_indexes = np.empty(len(old_indexes) + count, dtype=old_indexes.dtype)
        if row == len(old_values):
            # Append to the end
            last_time_stamp = old_indexes[-1]
            last_time_step = last_time_stamp - old_indexes[-2]
            new_indexes[: len(old_indexes)] = old_indexes
            for i in range(count):
                new_indexes[len(old_indexes) + i] = last_time_stamp + (i + 1) * last_time_step
            new_values = np.append(old_values, np.zeros(count))
        else:
            # Insert in the middle/beginning
            if row == 0:
                # If inserting in the beginning
                # the time step is the first step in the old series
                first_time_stamp = old_indexes[0]
                time_step = old_indexes[1] - first_time_stamp
                for i in range(count):
                    new_indexes[i] = first_time_stamp - (count - i) * time_step
                new_indexes[count:] = old_indexes
            else:
                # If inserting in the middle
                # the new time stamps are distributed between the stamps before and after the insertion point
                new_indexes[:row] = old_indexes[:row]
                base_time_stamp = old_indexes[row - 1]
                time_step = (old_indexes[row] - base_time_stamp) / float(count + 1)
                for i in range(count):
                    new_indexes[row + i] = base_time_stamp + (i + 1) * time_step
                new_indexes[row + count :] = old_indexes[row:]
            insert_indexes = range(row, row + count - 1) if count > 1 else row
            new_values = np.insert(old_values, insert_indexes, np.zeros(count))
        self._value = TimeSeriesVariableResolution(new_indexes, new_values, self._value.ignore_year, self._value.repeat)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if len(self._value) == 2:
            return False
        if count == len(self._value):
            count = len(self._value) - 2
            row = 2
        self.beginRemoveRows(parent, row, row + count - 1)
        old_indexes = self._value.indexes
        old_values = self._value.values
        removed = range(row, row + count) if count > 1 else row
        new_indexes = np.delete(old_indexes, removed)
        new_values = np.delete(old_values, removed)
        self._value = TimeSeriesVariableResolution(new_indexes, new_values, self._value.ignore_year, self._value.repeat)
        self.endRemoveRows()
        return True

    def reset(self, value):
        self.beginResetModel()
        self._value = value
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

    @property
    def values(self):
        return self._value.values
