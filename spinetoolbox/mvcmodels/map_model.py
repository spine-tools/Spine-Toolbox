######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""
from copy import deepcopy
from numbers import Number
from itertools import takewhile
import numpy
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QFont
from spinedb_api import (
    Array,
    convert_leaf_maps_to_specialized_containers,
    convert_map_to_table,
    DateTime,
    Duration,
    Map,
    ParameterValueFormatError,
    TimePattern,
    TimeSeries,
)
from .indexed_value_table_model import EXPANSE_COLOR
from .shared import PARSED_ROLE


empty = object()
"""Sentinel for empty cells."""


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

    def __init__(self, map_value, parent):
        """
        Args:
            map_value (Map): a map
            parent (QObject): parent object
        """
        super().__init__(parent)
        self._rows = _numpy_string_to_python_strings(convert_map_to_table(map_value, empty=empty))
        self._index_names = _gather_index_names(map_value)
        self._BOLD = QFont()
        self._BOLD.setBold(True)
        self._EMTPY_COLOR = QColor(255, 240, 240)

    def append_column(self):
        """Appends a new column to the right."""
        if not self._rows:
            return
        first = len(self._rows[0]) + 1
        last = first
        self.beginInsertColumns(QModelIndex(), first, last)
        self._rows = list(map(lambda row: row + [empty], self._rows))
        self._index_names += [Map.DEFAULT_INDEX_NAME]
        self.endInsertColumns()

    def clear(self, indexes):
        """
        Clears table cells.

        Args:
            indexes (list of QModelIndex): indexes to clear
        """
        top = self.rowCount()
        left = self.columnCount()
        bottom = 0
        right = 0
        for index in indexes:
            row = index.row()
            column = index.column()
            if self._is_in_expanse(row, column):
                continue
            top = min(top, row)
            bottom = max(bottom, row)
            left = min(left, column)
            right = max(right, column)
            self._rows[row][column] = empty
        if top <= bottom:
            self.dataChanged.emit(
                self.index(top, left),
                self.index(bottom, right),
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole],
            )
            self.dataChanged.emit(
                self.index(top, 0),
                self.index(bottom, self.columnCount() - 2),
                [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole],
            )

    def columnCount(self, index=QModelIndex()):
        """Returns the number of columns in this model."""
        if not self._rows:
            return len(self._index_names) + 2
        return len(self._rows[0]) + 1

    def convert_leaf_maps(self):
        converted = convert_leaf_maps_to_specialized_containers(self.value())
        if isinstance(converted, Map):
            self.reset(converted)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns the data associated with the given role."""
        row_index = index.row()
        column_index = index.column()
        if role == Qt.ItemDataRole.BackgroundRole:
            if self._is_in_expanse(row_index, column_index):
                return EXPANSE_COLOR
            data_length = _data_length(self._rows[row_index])
            if column_index >= data_length:
                return self._EMTPY_COLOR
            return None
        if role in (Qt.ItemDataRole.EditRole, PARSED_ROLE):
            if self._is_in_expanse(row_index, column_index):
                return ""
            value = self._rows[row_index][column_index]
            return value if value is not empty else ""
        if role == Qt.ItemDataRole.DisplayRole:
            if self._is_in_expanse(row_index, column_index):
                return ""
            data = self._rows[row_index][column_index]
            if isinstance(data, (float, int, Duration)):
                return str(data)
            if isinstance(data, DateTime):
                return str(data.value)
            if isinstance(data, TimeSeries):
                return "Time series"
            if isinstance(data, TimePattern):
                return "Time pattern"
            if isinstance(data, Array):
                return "Array"
            if data is None:
                return "None"
            if data is empty:
                return ""
            return data
        if role == Qt.ItemDataRole.FontRole:
            if self._is_in_expanse(row_index, column_index):
                return None
            row = self._rows[row_index]
            data_length = _data_length(row)
            if column_index == data_length - 1:
                return self._BOLD
        return None

    def flags(self, index):
        """Returns flags at index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Returns row numbers for vertical headers and column titles for horizontal ones."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Vertical:
            if section < len(self._rows):
                return section + 1
            return None
        return (self._index_names + ["Value", None])[section]

    def insertColumns(self, column, count, parent=QModelIndex()):
        """
        Inserts new columns into the map.

        Args:
            column (int): column index where to insert
            count (int): number of new columns
            parent (QModelIndex): ignored

        Return:
            bool: True if insertion was successful, False otherwise
        """
        self.beginInsertColumns(parent, column, column + count - 1)
        if self._rows:
            self._rows = [row[:column] + count * [empty] + row[column:] for row in self._rows]
        self._index_names = self._index_names[:column] + count * [Map.DEFAULT_INDEX_NAME] + self._index_names[column:]
        self.endInsertColumns()
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new rows into the map.

        Args:
            row (int): an index where to insert the new data
            count (int): number of rows to insert
            parent (QModelIndex): an index to a parent model
        Returns:
            bool: True if the operation was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        if self._rows:
            if row == self.rowCount():
                row = len(self._rows)
            if row > 0:
                row_before = self._rows[row - 1]
            else:
                row_before = len(self._rows[0]) * [empty]
        else:
            row_before = (len(self._index_names) + 1) * [empty]
        inserted = list()
        for _ in range(count):
            inserted.append([deepcopy(x) if x is not empty else x for x in row_before])
        self._rows = self._rows[:row] + inserted + self._rows[row:]
        self.endInsertRows()
        return True

    def is_leaf_value(self, index):
        """Checks if given model index contains a leaf value.

        Args:
            index (QModelIndex): index to check

        Returns:
            bool: True if index points to leaf value, False otherwise
        """
        row = index.row()
        column = index.column()
        if self._is_in_expanse(row, column):
            return False
        return column > 0 and column + 1 == _data_length(self._rows[row])

    def _is_in_expanse(self, row, column):
        """
        Returns True, if given row and column is in the right or bottom 'expanding' zone.

        Args:
            row (int): row index
            column (int): column index

        Returns:
            bool: True if the cell is in the expanse, False otherwise
        """
        if not self._rows or row == len(self._rows):
            return True
        return column == len(self._rows[0])

    def is_expanse_column(self, column):
        """
        Returns True if given column is the expanse column.

        Args:
            column (int): column

        Returns:
            bool: True if column is expanse column, False otherwise
        """
        if not self._rows:
            return True
        return column == len(self._rows[0])

    def is_expanse_row(self, row):
        """
        Returns True if given row is the expanse row.

        Args:
            row (int): row

        Returns:
            bool: True if row is the expanse row, False otherwise
        """
        return not self._rows or row == len(self._rows)

    def removeColumns(self, column, count, parent=QModelIndex()):
        """
        Removes columns from the map.

        Args:
            column (int): first column to remove
            count (int): number of columns to remove
            parent (QModelIndex): an index to a parent model

        Returns:
            True if the operation was successful
        """
        if not self._rows or column == len(self._rows[0]):
            return False
        last = min(column + count - 1, len(self._rows[0]) - 1)
        self.beginRemoveColumns(parent, column, last)
        self._rows = [row[:column] + row[column + count :] for row in self._rows]
        self._index_names = self._index_names[:column] + self._index_names[column + count :]
        self.endRemoveColumns()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes rows from the map.

        Args:
            row (int): first row to remove
            count (int): number of rows to remove
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

    def reset(self, map_value):
        """Resets the model to given map_value."""
        self.beginResetModel()
        self._rows = _numpy_string_to_python_strings(convert_map_to_table(map_value, empty=empty))
        self._index_names = _gather_index_names(map_value)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._rows) + 1

    def set_box(self, top_left, bottom_right, data):
        """
        Sets data for several indexes at once.

        Args:
            top_left (QModelIndex): a sequence of model indexes
            bottom_right (QModelIndex): a sequence of values corresponding to the indexes
            data (list of list): box of data
        """
        for row_index in range(top_left.row(), bottom_right.row() + 1):
            data_row = data[row_index - top_left.row()]
            first_column = top_left.column()
            for column_index in range(first_column, bottom_right.column() + 1):
                self._rows[row_index][column_index] = data_row[column_index - first_column]
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole])
        self.dataChanged.emit(
            self.index(top_left.row(), 0),
            self.index(bottom_right.row(), self.columnCount() - 2),
            [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole],
        )

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        Sets data in the map.

        Args:
            index (QModelIndex): an index to the model
            value (object): JSON representation of the value
            role (int): a role
        Returns:
            bool: True if the operation was successful
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row_index = index.row()
        column_index = index.column()
        if row_index == len(self._rows):
            if not value:
                return False
            self.insertRow(row_index + 1)
            row = self._rows[row_index]
            for i in range(column_index + 1, len(row)):
                row[i] = empty
            top_left = self.index(row_index, column_index + 1)
            if top_left.isValid():
                bottom_right = self.index(row_index, len(row))
                self.dataChanged.emit(
                    top_left, bottom_right, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole]
                )
        else:
            row = self._rows[row_index]
        if column_index == len(row):
            if not value:
                return False
            self.append_column()
            row = self._rows[row_index]
        if value is None or (isinstance(value, str) and value.lower() in ("null", "none")):
            row[column_index] = None
        elif value != 0 and not value:
            row[column_index] = empty
        else:
            row[column_index] = value if not isinstance(value, Number) else float(value)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole])
        if column_index > 0:
            top_left = self.index(row_index, 0)
            bottom_right = self.index(row_index, len(row))
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.FontRole])
        return True

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return False
        self._index_names[section] = value
        self.headerDataChanged.emit(orientation, section, section)
        return True

    def trim_columns(self):
        """Removes empty columns from the right."""
        if not self._rows or len(self._rows[0]) == 2:
            return
        max_data_length = 2
        column_count = len(self._rows[0])
        for row in self._rows:
            data_length = _data_length(row)
            max_data_length = max(max_data_length, data_length)
        if max_data_length == column_count:
            return
        first = max_data_length
        last = column_count - 1
        self.beginRemoveColumns(QModelIndex(), first, last)
        self._rows = list(map(lambda row: row[:first], self._rows))
        self._index_names = self._index_names[:max_data_length]
        self.endRemoveColumns()

    def value(self):
        """Returns the Map."""
        tree = _rows_to_dict(self._rows)
        map_value = _reconstruct_map(tree)
        _apply_index_names(map_value, self._index_names)
        return map_value

    def index_name(self, index):
        return (
            self.headerData(index.column(), Qt.Orientation.Horizontal)
            + "("
            + ", ".join(
                f"{self.headerData(c, Qt.Orientation.Horizontal)}={self.data(index.siblingAtColumn(c))}"
                for c in range(index.column())
            )
            + ")"
        )


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
            if i < len(row) - 2 and row[i + 2] is not empty:
                if not isinstance(column, (str, int, float, DateTime, Duration)):
                    raise ParameterValueFormatError(f"Index on row {rows.index(row) + 1} column {i + 1} is not scalar.")
                current = current.setdefault(column, dict())
                if not isinstance(current, dict):
                    raise ParameterValueFormatError(f"Indexing broken on row {rows.index(row) + 1} column {i + 1}.")
            else:
                value = row[i + 1]
                if value is empty:
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
    if len(indexes) > 1:
        first_type = type(indexes[0])
        if first_type == numpy.float_:
            first_type = float
        if any(not isinstance(i, first_type) for i in indexes[1:]):
            raise ParameterValueFormatError(f"Index type mismatch.")
    map_ = Map(indexes, values)
    return map_


def _data_length(row):
    """
    Counts the number of non-empty elements at the beginning of row.

    Args:
        row (list): a row of data

    Returns:
        int: data length
    """
    return len(list(takewhile(lambda x: x is not empty, row)))


def _gather_index_names(map_value):
    """Collects index names from Map.

    Returns only the 'first' index name for nested maps at the same depth.

    Args:
        map_value (Map): map to investigate

    Returns:
        list of str: index names
    """
    nested_names = list()
    for v in map_value.values:
        if isinstance(v, Map):
            new_nested_names = _gather_index_names(v)
            if len(new_nested_names) > len(nested_names):
                nested_names = nested_names + new_nested_names[len(nested_names) :]
    return [map_value.index_name] + nested_names


def _apply_index_names(map_value, index_names):
    """Applies index names to Map.

    Args:
        map_value (Map): target Map
        index_names (list of str): index names
    """
    map_value.index_name = index_names[0]
    for value in map_value.values:
        if isinstance(value, Map):
            _apply_index_names(value, index_names[1:])


def _numpy_string_to_python_strings(rows):
    """Converts instances of ``numpy.str_`` to regular Python strings.

    Args:
        rows (list of list): table rows

    Returns:
        list of list: converted rows
    """
    return [[str(x) if isinstance(x, numpy.str_) else x for x in row] for row in rows]
