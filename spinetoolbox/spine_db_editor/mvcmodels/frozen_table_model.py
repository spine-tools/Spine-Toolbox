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
Contains FrozenTableModel class.

:author: P. Vennström (VTT)
:date:   24.9.2019
"""
from itertools import product

from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, Signal
from .colors import SELECTED_COLOR
from ...helpers import rows_to_row_count_tuples


class FrozenTableModel(QAbstractTableModel):
    """Used by custom_qtableview.FrozenTableView"""

    selected_row_changed = Signal()

    def __init__(self, db_mngr, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            parent (QObject, optional): parent object
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self._data = []
        self._selected_row = None

    def set_headers(self, headers):
        """Sets headers for the header row wiping data.

        This method does nothing if the new headers are equal to existing ones.

        Args:
            headers (Iterable of str): headers
        """
        headers = list(headers)
        if self._data and headers == self._data[0]:
            return
        self.beginResetModel()
        self._data = [headers]
        self.endResetModel()

    def clear_model(self):
        self.beginResetModel()
        self._data.clear()
        self._selected_row = None
        self.endResetModel()

    def add_values(self, data):
        """Adds more frozen values that aren't in the table already.

        Args:
            data (set of tuple): frozen values
        """
        unique_data = set(self._data[1:])
        new_values = [value for value in data if value not in unique_data]
        if not new_values:
            return
        old_size = len(self._data)
        self.beginInsertRows(QModelIndex(), old_size, old_size + len(new_values) - 1)
        self._data += new_values
        self.endInsertRows()

    def remove_values(self, data):
        """Removes frozen values from the table.

        Args:
            data (set of tuple): frozen values
        """
        removed_i = set()
        for removed_row in data:
            for i, row in enumerate(self._data[1:]):
                if row == removed_row:
                    removed_i.add(i + 1)
                    break
        if not removed_i:
            return
        frozen_value = self._data[self._selected_row]
        intervals = rows_to_row_count_tuples(removed_i)
        for interval in reversed(intervals):
            end = interval[0] + interval[1]
            self.beginRemoveRows(QModelIndex(), interval[0], end - 1)
            del self._data[interval[0] : end]
            self.endRemoveRows()
        if self._selected_row in removed_i:
            self._selected_row = min(self._selected_row, len(self._data) - 1)
            self.selected_row_changed.emit()
        else:
            selected_row = self._find_first(frozen_value)
            if selected_row != self._selected_row:
                self._selected_row = selected_row
                self.selected_row_changed.emit()

    def clear_selected(self):
        """Clears selected row."""
        top_left = self.index(self._selected_row, 0)
        bottom_right = self.index(self._selected_row, self.columnCount() - 1)
        self._selected_row = None
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.BackgroundRole])
        self.selected_row_changed.emit()

    def set_selected(self, row):
        """Changes selected row.

        Args:
            row (int): row index
        """
        last_column = self.columnCount() - 1
        previous = self._selected_row
        self._selected_row = row
        if previous is not None:
            old_top_left = self.index(previous, 0)
            old_bottom_right = self.index(previous, last_column)
            self.dataChanged.emit(old_top_left, old_bottom_right, [Qt.ItemDataRole.BackgroundRole])
        new_top_left = self.index(self._selected_row, 0)
        new_bottom_right = self.index(self._selected_row, last_column)
        self.dataChanged.emit(new_bottom_right, new_top_left, [Qt.ItemDataRole.BackgroundRole])
        self.selected_row_changed.emit()

    def get_frozen_value(self):
        """Return currently selected frozen value.

        Returns:
            tuple: frozen value
        """
        if self._selected_row is None:
            return self.columnCount() * (None,)
        return self._data[self._selected_row]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def row(self, index):
        return self._data[index.row()] if index.isValid() else None

    def insert_column_data(self, header, values, column):
        """Inserts new column with given header.

        Args:
            header (str): frozen header
            values (set of tuple): column's values
            column (int): position
        """
        if not self._data:
            self.beginResetModel()
            self._data.append([header])
            self._data += [(value,) for value in values]
            self._selected_row = 1 if len(values) > 0 else None
            self.endResetModel()
            return
        headers = self._data[0]
        if len(self._data) == 1:
            self.beginInsertColumns(QModelIndex(), column, column)
            self._data[0] = headers[:column] + [header] + headers[column:]
            self.endInsertColumns()
            return
        column_values = self._unique_values()
        new_data = [row for row in product(*column_values[:column], values, *column_values[column:])]
        previous_selected_value = self._data[self._selected_row] if self._selected_row is not None else None
        self.beginResetModel()
        self._data[0] = headers[:column] + [header] + headers[column:]
        self._data[1:] = new_data
        self._selected_row = self._find_first(previous_selected_value, column)
        self.endResetModel()

    def remove_column(self, column):
        """Removes column and makes rows unique.

        Args:
            column (int): column to remove
        """
        if not self._data:
            return
        if len(self._data[0]) == 1:
            self.clear_model()
            return
        headers = self._data[0]
        if len(self._data) == 1:
            self.beginRemoveColumns(QModelIndex(), column, column)
            self._data[0] = headers[:column] + headers[column + 1 :]
            self.endRemoveColumns()
            return
        column_values = self._unique_values()
        new_data = [row for row in product(*column_values[:column], *column_values[column + 1 :])]
        selected_data = self._data[self._selected_row]
        self.beginResetModel()
        self._data[0] = headers[:column] + headers[column + 1 :]
        self._data[1:] = new_data
        self._selected_row = self._find_first(selected_data[:column] + selected_data[column + 1 :])
        self.endResetModel()

    def moveColumns(self, sourceParent, sourceColumn, count, destinationParent, destinationChild):
        fixed_rows = []
        moved_rows = []
        for row in self._data:
            fixed_rows.append(row[:sourceColumn] + row[sourceColumn + count :])
            moved_rows.append(row[sourceColumn : sourceColumn + count])
        data = []
        destination = destinationChild if destinationChild < sourceColumn else destinationChild - count
        for fixed, moved in zip(fixed_rows, moved_rows):
            data.append(fixed[:destination] + moved + fixed[destination:])
        self.beginMoveColumns(sourceParent, sourceColumn, sourceColumn + count - 1, destinationParent, destinationChild)
        self._data = data
        self.endMoveColumns()
        return True

    def _unique_values(self):
        """Turns non-header data into sets of unique values on each column.

        Returns:
            list of set: each column's unique values
        """
        columns = None
        for row in self._data[1:]:
            if columns is None:
                columns = [set() for _ in range(len(row))]
            for i, x in enumerate(row):
                columns[i].add(x)
        return columns

    def _find_first(self, row_data, mask_column=None):
        """Finds first row that matches given row data.

        Args:
            row_data (tuple): row data to search for
            mask_column (int, optional): ignored column

        Returns:
            int: row index
        """
        if len(self._data) < 2:
            return None
        if mask_column is None:
            for i, row in enumerate(self._data[1:]):
                if row_data == row:
                    return i + 1
        else:
            for i, row in enumerate(self._data[1:]):
                if row_data == row[:mask_column] + row[mask_column + 1 :]:
                    return i + 1
        raise RuntimeError("Logic error: cannot find row in frozen table.")

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            row = index.row()
            column = index.column()
            header_id = self._data[row][column]
            if row == 0:
                return header_id
            index_id = self._data[0][column]
            if index_id == "parameter":
                db_map, id_ = header_id
                item = self.db_mngr.get_item(db_map, "parameter_definition", id_)
                name = item.get("parameter_name")
            elif index_id == "alternative":
                db_map, id_ = header_id
                item = self.db_mngr.get_item(db_map, "alternative", id_)
                name = item.get("name")
            elif index_id == "index":
                index = header_id[1]
                item = {}
                name = str(index)
            elif index_id == "database":
                item = {}
                name = header_id.codename
            else:
                db_map, id_ = header_id
                item = self.db_mngr.get_item(db_map, "object", id_)
                name = item.get("name")
            if role == Qt.ItemDataRole.DisplayRole:
                return name
            description = item.get("description")
            if not description:
                description = name
            return description
        if role == Qt.ItemDataRole.BackgroundRole:
            if index.row() == self._selected_row:
                return SELECTED_COLOR
            return None
        return None

    @property
    def headers(self):
        return self._data[0] if self._data else []
