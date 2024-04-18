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

"""Contains FrozenTableModel class."""
from itertools import product
from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, Signal
from .colors import SELECTED_COLOR
from ...helpers import plain_to_tool_tip, rows_to_row_count_tuples


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

        Returns:
            bool: True if model was reset, False otherwise
        """
        headers = list(headers)
        if self._data and headers == self._data[0]:
            return False
        self.beginResetModel()
        self._data = [headers]
        self._selected_row = None
        self.endResetModel()
        return True

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
        had_data_before = bool(unique_data)
        self._keep_sorted(update_selected_row=had_data_before)

    def remove_values(self, data):
        """Removes frozen values from the table.

        Args:
            data (set of tuple): frozen values
        """
        removed_rows = {i + 1 for i, val in enumerate(self._data[1:]) if val in data}
        if not removed_rows:
            return
        if self._selected_row is not None and self._selected_row not in removed_rows:
            frozen_value = self._data[self._selected_row]
        else:
            frozen_value = None
        for first, count in reversed(rows_to_row_count_tuples(removed_rows)):
            last = first + count - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            del self._data[first : last + 1]
            self.endRemoveRows()
        if frozen_value is not None:
            selected_row = self._find_first(frozen_value)
        else:
            selected_row = 1 if len(self._data) > 1 else None
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

    def get_selected(self):
        """Returns selected row.

        Returns:
            int: row index or None if no row is selected
        """
        return self._selected_row

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
        new_data = list(product(*column_values[:column], values, *column_values[column:]))
        previously_selected_value = self._data[self._selected_row] if self._selected_row is not None else None
        self.beginResetModel()
        self._data[0] = headers[:column] + [header] + headers[column:]
        self._data[1:] = new_data
        self._selected_row = self._find_first(previously_selected_value, column)
        self.endResetModel()
        self._keep_sorted()

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
        new_data = list(product(*column_values[:column], *column_values[column + 1 :]))
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
        self._keep_sorted()
        return True

    def _keep_sorted(self, update_selected_row=True):
        """Sorts the data table."""
        if len(self._data) < 3:
            return
        frozen_value = self.get_frozen_value() if self._selected_row is not None else None
        self.layoutAboutToBeChanged["QList<QPersistentModelIndex>", "QAbstractItemModel::LayoutChangeHint"].emit(
            [], QAbstractTableModel.LayoutChangeHint.VerticalSortHint
        )
        header = self._data[0]
        column_count = self.columnCount()
        data = sorted(
            self._data[1:],
            key=lambda x: tuple(self._name_from_data(x[column], header[column]) for column in range(column_count)),
        )
        self._data[1:] = data
        selected_row_changed = False
        if frozen_value is not None:
            if update_selected_row:
                candidate = self._find_first(frozen_value)
                if self._selected_row != candidate:
                    self._selected_row = candidate
                    selected_row_changed = True
            elif frozen_value != self.get_frozen_value():
                # The row did not change but the frozen value did.
                selected_row_changed = True
        self.layoutChanged["QList<QPersistentModelIndex>", "QAbstractItemModel::LayoutChangeHint"].emit(
            [], QAbstractTableModel.LayoutChangeHint.VerticalSortHint
        )
        if selected_row_changed:
            self.selected_row_changed.emit()

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
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            if row == 0:
                return self._data[row][index.column()]
            column = index.column()
            return self._name_from_data(self._data[row][column], self._data[0][column])
        if role == Qt.ItemDataRole.ToolTipRole:
            row = index.row()
            if row == 0:
                return self._data[row][index.column()]
            return self._tooltip_from_data(row, index.column())
        if role == Qt.ItemDataRole.BackgroundRole:
            if index.row() == self._selected_row:
                return SELECTED_COLOR
            return None
        return None

    def _tooltip_from_data(self, row, column):
        """Resolves item tooltip which is usually its description.

        Args:
            row (int): row
            column (int): column

        Returns:
            str: value's tooltip
        """
        value = self._data[row][column]
        header = self._data[0][column]
        if header == "parameter":
            db_map, id_ = value
            tool_tip = self.db_mngr.get_item(db_map, "parameter_definition", id_).get("description")
        elif header == "alternative":
            db_map, id_ = value
            tool_tip = self.db_mngr.get_item(db_map, "alternative", id_).get("description")
        elif header == "index":
            tool_tip = str(value[1])
        elif header == "database":
            tool_tip = value.codename
        elif header == "entity":
            db_map, id_ = value
            tool_tip = self.db_mngr.get_item(db_map, "entity", id_).get("description")
        else:
            raise RuntimeError(f"Logic error: unknown header '{header}'")
        return plain_to_tool_tip(tool_tip)

    def _name_from_data(self, value, header):
        """Resolves item name.

        Args:
            value (tuple or DatabaseMapping): cell value
            header (str): column header

        Returns:
            str: value's name
        """
        if header == "parameter":
            db_map, id_ = value
            item = self.db_mngr.get_item(db_map, "parameter_definition", id_)
            return item.get("name")
        if header == "alternative":
            db_map, id_ = value
            item = self.db_mngr.get_item(db_map, "alternative", id_)
            return item.get("name")
        if header == "index":
            return str(value[1])
        if header == "database":
            return value.codename
        db_map, id_ = value
        item = self.db_mngr.get_item(db_map, "entity", id_)
        return item.get("name")

    @property
    def headers(self):
        return self._data[0] if self._data else []
