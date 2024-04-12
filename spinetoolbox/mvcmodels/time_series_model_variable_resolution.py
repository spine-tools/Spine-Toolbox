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

"""A model for variable resolution time series, used by the parameter_value editors."""
import numpy as np
from PySide6.QtCore import QModelIndex, Qt, Slot
from spinedb_api import TimeSeriesVariableResolution
from .indexed_value_table_model import IndexedValueTableModel


class TimeSeriesModelVariableResolution(IndexedValueTableModel):
    """A model for variable resolution time series type parameter values."""

    def flags(self, index):
        """Returns the flags for given model index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    @property
    def indexes(self):
        """Returns the time stamps as an array."""
        return self._value.indexes

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new time stamps and values to the series.

        When inserting in the middle of the series the new time stamps are distributed evenly
        among the time span between the two time stamps around the insertion point.
        When inserting at the beginning or at the end of the series the duration between
        the new time stamps is set equal to the first/last duration in the original series.

        The new values are set to zero.

        Args:
            row (int): a numeric index to the first stamp/value to insert
            count (int): number of stamps/values to insert
            parent (QModelIndex): index to a parent model
        Returns:
            bool: True if the insertion was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        old_indexes = self._value.indexes
        old_values = self._value.values
        new_indexes = np.empty(len(old_indexes) + count, dtype=old_indexes.dtype)
        if row == len(old_values):
            # Append to the end
            # find time step, default 1h
            last_time_stamp = old_indexes[-1]
            if len(old_indexes) > 1:
                last_time_step = last_time_stamp - old_indexes[-2]
            else:
                last_time_step = np.timedelta64(1, "h")

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
                if len(old_indexes) > 1:
                    time_step = old_indexes[1] - first_time_stamp
                else:
                    time_step = np.timedelta64(1, "h")
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
            new_values = np.insert(old_values, row, np.zeros(count))
        self._value = TimeSeriesVariableResolution(new_indexes, new_values, self._value.ignore_year, self._value.repeat)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes time stamps/values from the series.

        Args:
            row (int): a numeric index to the series where to begin removing
            count (int): how many stamps/values to remove
            parent (QModelIndex): an index to the parent model
        Returns:
            bool: True if the operation was successful.
        """
        if len(self._value) == 1:
            return False
        if count == len(self._value):
            count = len(self._value) - 1
            row = 1
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
        """Resets the model with new time series data."""
        self.beginResetModel()
        self._value = value
        self.endResetModel()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        Sets a given time stamp or value in the series.

        Column index 0 refers to time stamps while index 1 to values.

        Args:
            index (QModelIndex): an index to the model
            value (numpy.datetime64, float): a new stamp or value
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
            except ValueError:
                self._value.indexes[row] = np.datetime64()
        else:
            try:
                self._value.values[row] = value
            except ValueError:
                self._value.values[row] = np.nan
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return True

    def batch_set_data(self, indexes, values):
        """
        Sets data for several indexes at once.

        Args:
            indexes (Sequence): a sequence of model indexes
            values (Sequence): a sequence of datetimes/floats corresponding to the indexes
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

    @Slot(bool, name="set_ignore_year")
    def set_ignore_year(self, ignore_year):
        """Sets the ignore_year option of the time series."""
        self._value.ignore_year = ignore_year

    @Slot(bool, name="set_repeat")
    def set_repeat(self, repeat):
        """Sets the repeat option of the time series."""
        self._value.repeat = repeat

    @property
    def values(self):
        """Returns the values of the time series as an array."""
        return self._value.values
