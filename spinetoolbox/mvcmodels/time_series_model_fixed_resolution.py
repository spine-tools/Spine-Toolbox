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

"""A model for fixed resolution time series, used by the parameter_value editors."""
import numpy as np
from PySide6.QtCore import QModelIndex, Qt, Slot, QLocale
from spinedb_api import TimeSeriesFixedResolution
from .indexed_value_table_model import IndexedValueTableModel


class TimeSeriesModelFixedResolution(IndexedValueTableModel):
    """A model for fixed resolution time series type parameter values."""

    def __init__(self, series, parent):
        """
        Args:
            series (TimeSeriesFixedResolution): a time series
            parent (QObject): parent object
        """
        super().__init__(series, parent)
        self.locale = QLocale()

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
        return self._value.indexes

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
        self.endRemoveRows()
        return True

    def reset(self, value):
        """Resets the model with new time series data."""
        self.beginResetModel()
        self._value = value
        self.endResetModel()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
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
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        if index.column() != 1:
            return False
        row = index.row()
        if row == len(self._value):
            self.insertRow(row)
        try:
            self._value.values[row] = value
        except ValueError:
            self._value.values[row] = np.nan
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
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
        self.dataChanged.emit(self.index(top, 1), self.index(bottom, 1), [Qt.ItemDataRole.EditRole])

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
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    def set_start(self, start):
        """Sets the start datetime."""
        self._value.start = start
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._value) - 1, 0))

    @property
    def values(self):
        """Returns the values of the time series as an array."""
        return self._value.values
