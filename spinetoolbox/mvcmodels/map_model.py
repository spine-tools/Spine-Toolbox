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
A model for maps, used by the parameter_value editors.

:authors: A. Soininen (VTT)
:date:    11.2.2020
"""

from numbers import Number
from itertools import takewhile
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtGui import QColor, QFont
from spinedb_api import (
    Array,
    convert_leaf_maps_to_specialized_containers,
    DateTime,
    Duration,
    IndexedValue,
    Map,
    ParameterValueFormatError,
    TimePattern,
    TimeSeries,
)


class MapModel(QAbstractTableModel):
    """
    A model for Map type parameter values.

    This model represents the Map as a 2D table.
    Each row consists of one or more index columns and a value column.
    The last columns of a row are padded with Nones.

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
        self._BOLD = QFont()
        self._BOLD.setBold(True)
        self._EMTPY_COLOR = QColor(255, 240, 240)
        self._EXPANSE_COLOR = QColor(245, 245, 245)

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
            return 1
        return len(self._rows[0]) + 1

    def convert_leaf_maps(self):
        converted = convert_leaf_maps_to_specialized_containers(self.value())
        if isinstance(converted, Map):
            self.reset(converted)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data associated with the given role."""
        row_index = index.row()
        column_index = index.column()
        if role == Qt.BackgroundRole:
            if self._is_in_expanse(row_index, column_index):
                return self._EXPANSE_COLOR
            data_length = len(list(takewhile(lambda x: x is not None, self._rows[row_index])))
            if column_index >= data_length:
                return self._EMTPY_COLOR
            return None
        if role == Qt.EditRole:
            if self._is_in_expanse(row_index, column_index):
                return ""
            return self._rows[row_index][column_index]
        if role == Qt.DisplayRole:
            if self._is_in_expanse(row_index, column_index):
                return ""
            data = self._rows[row_index][column_index]
            if isinstance(data, DateTime):
                return str(data.value)
            if isinstance(data, Duration):
                return str(data)
            if isinstance(data, TimeSeries):
                return "Time series"
            if isinstance(data, TimePattern):
                return "Time pattern"
            if isinstance(data, Array):
                return "Array"
            return data
        if role == Qt.FontRole:
            if self._is_in_expanse(row_index, column_index):
                return None
            row = self._rows[row_index]
            data_length = len(list(takewhile(lambda x: x is not None, row)))
            if column_index == data_length - 1:
                return self._BOLD
        return None

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
            if section < len(self._rows):
                return section + 1
            return None
        if section == 0:
            return "Index"
        if self._rows:
            if section == len(self._rows[0]) - 1:
                return "Value"
            if section == len(self._rows[0]):
                return None
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

    def _is_in_expanse(self, row, column):
        """
        Returns True, if given row and column is in the right or bottom 'expanding' zone

        Args:
            row (int): row index
            column (int): column index

        Returns:
            bool: True if the cell is in the expanse, False otherwise
        """
        if row == len(self._rows):
            return True
        return column == len(self._rows[0])

    def reset(self, map_value):
        """Resets the model to given map_value."""
        self.beginResetModel()
        rows = _as_rows(map_value)
        self._rows = _make_square(rows)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._rows) + 1

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
        if not self._rows or row == len(self._rows):
            return False
        last = min(row + count - 1, len(self._rows) - 1)
        self.beginRemoveRows(parent, row, last)
        self._rows = self._rows[:row] + self._rows[last + 1 :]
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets data in the map.

        Args:
            index (QModelIndex): an index to the model
            value (object): JSON representation of the value
            role (int): a role
        Returns:
            True if the operation was successful
        """
        if not index.isValid() or role != Qt.EditRole:
            return False
        row_index = index.row()
        if row_index == len(self._rows):
            self.insertRow(row_index)
        row = self._rows[row_index]
        column_index = index.column()
        if column_index == len(row):
            self.append_column()
            row = self._rows[row_index]
        if not value:
            row[column_index] = None
            return True
        if not isinstance(value, (str, int, float, Duration, DateTime, IndexedValue)):
            return False
        row[column_index] = value if not isinstance(value, Number) else float(value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.ToolTipRole])
        if column_index > 0:
            top_left = self.index(row_index, 0)
            bottom_right = self.index(row_index, len(row))
            self.dataChanged.emit(top_left, bottom_right, [Qt.FontRole])
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
        tree = _rows_to_dict(self._rows)
        return _reconstruct_map(tree)


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


def _rows_to_dict(rows):
    """
    Turns table into nested dictionaries.

    Args:
        rows (list): a list of row data

    Returns:
        dict: a nested dictionary
    """
    tree = dict()
    for row in rows:
        current = tree
        for i, column in enumerate(row):
            if column is None:
                raise ParameterValueFormatError(f"Index missing on row {rows.index(row) + 1} column {i + 1}.")
            if i < len(row) - 2 and row[i + 2] is not None:
                if not isinstance(column, (str, int, float, DateTime, Duration)):
                    raise ParameterValueFormatError(f"Index on row {rows.index(row) + 1} column {i + 1} is not scalar.")
                current = current.setdefault(column, dict())
            else:
                value = row[i + 1]
                if value is None:
                    raise ParameterValueFormatError(f"Value missing on row {rows.index(row) + 1} column {i + 1}.")
                current[column] = value
                break
    return tree


def _reconstruct_map(tree):
    """
    Constructs a :class:`Map` from a nested dictionary.

    Args:
        tree (dict): a nested dictionary

    Returns:
        Map: reconstructed Map
    """
    indexes = list()
    values = list()
    for key, value in tree.items():
        if isinstance(value, dict):
            value = _reconstruct_map(value)
        indexes.append(key)
        values.append(value)
    return Map(indexes, values)
