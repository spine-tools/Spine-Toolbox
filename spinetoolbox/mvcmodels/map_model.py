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
A model for maps, used by the parameter value editors.

:authors: A. Soininen (VTT)
:date:    11.2.2020
"""

from itertools import takewhile
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from spinedb_api import DateTime, Duration, from_database, Map, ParameterValueFormatError, to_database


class MapModel(QAbstractTableModel):
    """
    A model for Map type parameter values.

    This model represents the Map as a 2D table.
    Each row consists of one or more index columns and a value column.
    The last columns of a row are padded with None.

    Example:
        ::

            Map {
                "A": 1.0
                "B": Map {"a": -1.0}
                "C": 3.0
            }

        The table corresponding to the above map:

        === === ====
        "A" 1.0 None
        "B" "a" -1.0
        "C" 3.0 None
        === === ====
    """

    def __init__(self, map_value):
        """
        Args:
            map_value (Map): a map
        """
        super().__init__()
        rows = _as_rows(map_value)
        self._rows = _make_square(rows)

    def append_column(self):
        """Appends a new column to the right."""
        if not self._rows:
            return
        first = len(self._rows[0])
        last = first
        self.beginInsertColumns(QModelIndex(), first, last)
        self._rows = list(map(lambda row: row + [None], self._rows))
        self.endInsertColumns()

    def columnCount(self, index=QModelIndex()):
        """Returns the number of columns in this model."""
        if not self._rows:
            return 0
        return len(self._rows[0])

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data associated with the given role."""
        if role not in (Qt.DisplayRole, Qt.EditRole) or not index.isValid():
            return None
        row_index = index.row()
        column_index = index.column()
        row = self._rows[row_index]
        if (
            role == Qt.DisplayRole
            and column_index < len(row) - 1
            and row[column_index + 1] is not None
            and row_index > 0
        ):
            indexes_above = self._rows[row_index - 1][: column_index + 1]
            current_indexes = self._rows[row_index][: column_index + 1]
            if current_indexes == indexes_above:
                return None
        data = row[column_index]
        if role == Qt.EditRole:
            return to_database(data if data is not None else "")
        if hasattr(data, "to_text"):
            return data.to_text()
        if isinstance(data, DateTime):
            return str(data.value)
        return data

    def flags(self, index):
        """Returns flags at index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns row numbers for vertical headers and column titles for horizontal ones."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        if section == 0:
            return "Index"
        if self._rows and section == len(self._rows[0]) - 1:
            return "Value"
        return "Index or value"

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new rows into the map.

        Args:
            row (int): an index where to insert the new data
            count (int): number of rows to insert
            parent (QModelIndex): an index to a parent model
        Returns:
            True if the operation was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        if row > 0:
            row_before = self._rows[row - 1]
        else:
            if self._rows:
                row_before = len(self._rows[0]) * [None]
            else:
                row_before = [None, None]
        template = row_before[:-2] + ["key", 0.0]
        self._rows = self._rows[:row] + count * [template] + self._rows[row:]
        self.endInsertRows()
        return True

    def reset(self, map_value):
        """Resets the model to given map_value."""
        self.beginResetModel()
        rows = _as_rows(map_value)
        self._rows = _make_square(rows)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._rows)

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes rows from the map.

        Args:
            row (int): an index where to remove the data
            count (int): number of rows pairs to remove
            parent (QModelIndex): an index to a parent model

        Returns:
            True if the operation was successful
        """
        if not self._rows:
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        self._rows = self._rows[:row] + self._rows[row + count :]
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets data in the map.

        Args:
            index (QModelIndex): an index to the model
            value (str): JSON representation of the value
            role (int): a role
        Returns:
            True if the operation was successful
        """
        if not index.isValid() or role != Qt.EditRole:
            return False
        if not value:
            self._rows[index.row()][index.column()] = None
            return True
        try:
            new_value = from_database(value)
        except ParameterValueFormatError:
            return False
        if not isinstance(new_value, (str, float, Duration, DateTime)):
            return False
        self._rows[index.row()][index.column()] = from_database(value)
        return True

    def trim_columns(self):
        """Removes empty columns from the right."""
        if not self._rows or len(self._rows[0]) == 2:
            return
        max_data_length = 2
        column_count = len(self._rows[0])
        for row in self._rows:
            data_length = sum(1 for _ in takewhile(lambda x: x is not None, row))
            max_data_length = max(max_data_length, data_length)
        if max_data_length == column_count:
            return
        first = max_data_length
        last = column_count - 1
        self.beginRemoveColumns(QModelIndex(), first, last)
        self._rows = list(map(lambda row: row[:first], self._rows))
        self.endRemoveColumns()

    def value(self):
        """Returns the Map."""
        return _reconstruct_map(self._rows, 0, len(self._rows) - 1, 0)


def _as_rows(map_value, row_this_far=None):
    """Converts given Map into list of rows recursively."""
    if row_this_far is None:
        row_this_far = list()
    rows = list()
    for index, value in zip(map_value.indexes, map_value.values):
        if not isinstance(value, Map):
            rows.append(row_this_far + [index, value])
        else:
            rows += _as_rows(value, row_this_far + [index])
    return rows


def _make_square(rows):
    """Makes a list of rows a 2D table by appending None to the row ends."""
    max_length = 0
    for row in rows:
        max_length = max(max_length, len(row))
    equal_length_rows = list()
    for row in rows:
        equal_length_row = row + (max_length - len(row)) * [None]
        equal_length_rows.append(equal_length_row)
    return equal_length_rows


def _reconstruct_map(rows, first_row, last_row, column_index):
    if not rows:
        return Map([], [])
    block_start_row = first_row
    index = None
    indexes = list()
    values = list()
    for row_index in range(first_row, last_row + 1):
        row = rows[row_index][column_index:]
        if index is None:
            index = row[0]
            if index is None:
                raise ParameterValueFormatError(f"Index missing on row {first_row + row_index} column {column_index}.")
        is_leaf = len(row) == 2 or row[2] is None
        if is_leaf:
            indexes.append(index)
            value = row[1]
            if value is None:
                raise ParameterValueFormatError(f"Value missing on row {first_row + row_index} column {column_index}.")
            values.append(value)
            index = None
            block_start_row = row_index + 1
            continue
        if row_index < last_row:
            next_index = rows[row_index + 1][column_index]
            if next_index == index:
                continue
            value = _reconstruct_map(rows, block_start_row, row_index, column_index + 1)
            indexes.append(index)
            values.append(value)
            index = None
            block_start_row = row_index + 1
            continue
        value = _reconstruct_map(rows, block_start_row, row_index, column_index + 1)
        indexes.append(index)
        values.append(value)
    return Map(indexes, values)
