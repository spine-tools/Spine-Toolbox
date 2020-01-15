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
A model for fixed resolution time series, used by the parameter value editors.

:authors: A. Soininen (VTT)
:date:   4.7.2019
"""

import numpy as np
from PySide2.QtCore import QModelIndex, Qt, Slot, QLocale
from spinedb_api import TimeSeriesFixedResolution
from .indexed_value_table_model import IndexedValueTableModel


class TimeSeriesModelFixedResolution(IndexedValueTableModel):
    """
    A model for fixed resolution time series type parameter values.

    Attributes:
        series (TimeSeriesFixedResolution): a time series
    """

    def __init__(self, series):
        super().__init__(series, "Time stamp", "Values")
        # Cache the time steps so they need not be recalculated every single time they are needed.
        self._index_cache = self._value.indexes
        self.locale = QLocale()

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns the time stamp or the corresponding value at given model index.

        Column index 0 refers to time stamps while index 1 to values.

        Args:
            index (QModelIndex): an index to the model
            role (int): a role
        """
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
        """Returns the time stamps as an array."""
        return self._index_cache

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new values to the series.

        The new values are set to zero. Start time or resolution are left unchanged.

        Args:
            row (int): a numeric index to the first stamp/value to insert
            count (int): number of stamps/values to insert
            parent (QModelIndex): index to a parent model
        Returns:
            True if the operation was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        old_values = self._value.values
        if row == len(old_values):
            new_values = np.append(old_values, np.zeros(count))
        else:
            new_values = np.insert(old_values, row, np.zeros(count))
        self._value = TimeSeriesFixedResolution(
            self._value.start, self._value.resolution, new_values, self._value.ignore_year, self._value.repeat
        )
        self._index_cache = self._value.indexes
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes values from the series.

        Args:
            row (int): a numeric index to the series where to begin removing
            count (int): how many stamps/values to remove
            parent (QModelIndex): an index to the parent model
        Returns:
            True if the operation was successful.
        """
        if len(self._value) == 1:
            return False
        if count == len(self._value):
            count = len(self._value) - 1
            row = 1
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
        """Resets the model with new time series data."""
        self.beginResetModel()
        self._value = value
        self._index_cache = self._value.indexes
        self.endResetModel()

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets a given value in the series.

        Column index 1 refers to values.
        Note it does not make sense to set the time stamps in fixed resolution series.

        Args:
            index (QModelIndex): an index to the model
            value (numpy.datetime64, float): a new stamp or value
            role (int): a role
        Returns:
            True if the operation was successful
        """
        if not index.isValid() or role != Qt.EditRole:
            return False
        if index.column() != 1:
            return False
        self._value.values[index.row()] = value
        self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def batch_set_data(self, indexes, values):
        """
        Sets data for several indexes at once.

        Only the values of the series are modified as the time stamps are immutable.

        Args:
            indexes (Sequence): a sequence of model indexes
            values (Sequence): a sequence of floats corresponding to the indexes
        """
        rows = []
        for index, value in zip(indexes, values):
            if index.column() != 1:
                continue
            row = index.row()
            self._value.values[row] = value
            rows.append(row)
        if not rows:
            return
        top = min(rows)
        bottom = max(rows)
        self.dataChanged.emit(self.index(top, 1), self.index(bottom, 1), [Qt.EditRole])

    @Slot(bool, name="set_ignore_year")
    def set_ignore_year(self, ignore_year):
        """Sets the ignore_year option of the time series."""
        self._value.ignore_year = ignore_year

    @Slot(bool, name="set_repeat")
    def set_repeat(self, repeat):
        """Sets the repeat option of the time series."""
        self._value.repeat = repeat

    def set_resolution(self, resolution):
        """Sets the resolution."""
        self._value.resolution = resolution
        self._index_cache = self._value.indexes
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    def set_start(self, start):
        """Sets the start datetime."""
        self._value.start = start
        self._index_cache = self._value.indexes
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    @property
    def values(self):
        """Returns the values of the time series as an array."""
        return self._value.values
