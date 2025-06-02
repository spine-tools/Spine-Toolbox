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

""" Contains a minimal table model. """
from collections.abc import Iterable, Sequence
from typing import Any, Generic, Optional, TypeVar
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

T = TypeVar("T")
TableData = list[T]


class MinimalTableModel(QAbstractTableModel, Generic[T]):
    """Table model for outlining simple tabular data."""

    def __init__(self, parent: Optional[QObject] = None, header: Optional[list[str]] = None, lazy: bool = True):
        """
        Args:
            parent: the parent object
            header: header labels
            lazy: if True, fetches data lazily
        """
        super().__init__(parent)
        if header is None:
            header = []
        self._parent = parent
        self.header = header
        self._main_data: TableData = []
        self._fetched = not lazy
        self._paste = False

    def clear(self):
        """Clears all data in model."""
        self.beginResetModel()
        self._main_data.clear()
        self.endResetModel()

    def flags(self, index):
        """Returns index flags."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def canFetchMore(self, parent):
        """Returns True if the model hasn't been fetched."""
        return not self._fetched

    def fetchMore(self, parent):
        """Fetches data and uses it to reset the model."""
        self._fetched = True

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model."""
        return len(self._main_data)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns in the model."""
        return len(self.header) or len(next(iter(self._main_data), []))

    def headerData(self, section, orientation=Qt.Orientation.Horizontal, role=Qt.ItemDataRole.DisplayRole):
        """Returns headers."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            try:
                return self.header[section]
            except IndexError:
                return None
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        raise RuntimeError(f"logic error: unknown orientation {orientation}")

    def set_horizontal_header_labels(self, labels: list[str]) -> None:
        """Sets horizontal header labels."""
        if not labels:
            return
        self.header = labels
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(labels) - 1)

    def insert_horizontal_header_labels(self, section: int, labels: Sequence[str]) -> None:
        """Inserts horizontal header labels at the given section."""
        if not labels:
            return
        for j, value in enumerate(labels):
            if section + j >= self.columnCount():
                self.header.append(value)
            else:
                self.header.insert(section + j, value)
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, section, section + len(labels) - 1)

    def horizontal_header_labels(self) -> list[str]:
        return self.header

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.EditRole:
            return False
        try:
            self.header[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        except IndexError:
            return False

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index.

        Args:
            index (QModelIndex): Index of item
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not index.isValid():
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        try:
            return self._main_data[index.row()][index.column()]
        except IndexError:
            return None

    def row_data(self, row: int, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Optional[Any]:
        """Returns the data stored under the given role for the given row.

        Args:
            row: Item row
            role: Data role

        Returns:
            Row data for given role.
        """
        if not 0 <= row < self.rowCount():
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        return self._main_data[row]

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Sets data in model."""
        if not index.isValid():
            return False
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.UserRole):
            return False
        return self.batch_set_data([index], [value])

    def batch_set_data(self, indexes: Iterable[QModelIndex], data: Iterable) -> bool:
        """Batch sets data for given indexes.

        Args:
            indexes: model indexes
            data: data at each index

        Returns:
            True if data was set successfully, False otherwise
        """
        if not indexes or not data:
            return False
        rows = []
        columns = []
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            self._main_data[row][column] = value
            rows.append(row)
            columns.append(column)
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(
            self.index(top, left), self.index(bottom, right), [Qt.ItemDataRole.EditRole, Qt.ItemDataRole.DisplayRole]
        )
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.

        Args:
            row (int): Row number where new rows are inserted
            count (int): Number of inserted rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were inserted successfully, False otherwise
        """
        if row < 0 or row > self.rowCount() or count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        template_row = max(self.columnCount(), 1) * [None]
        self._main_data.insert(row, template_row)
        for i in range(1, count):
            self._main_data.insert(row + i, template_row.copy())
        self.endInsertRows()
        return True

    def insertColumns(self, column, count, parent=QModelIndex()):
        """Inserts count columns into the model before the given column.
        Items in the new column will be children of the item represented
        by the parent model index.

        Args:
            column (int): Column number where new columns are inserted
            count (int): Number of inserted columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were inserted successfully, False otherwise
        """
        if column < 0 or column > self.columnCount():
            return False
        if count < 1:
            return False
        self.beginInsertColumns(parent, column, column + count - 1)
        for j in range(count):
            for i in range(self.rowCount()):
                self._main_data[i].insert(column + j, None)
        self.endInsertColumns()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent.

        Args:
            row (int): Row number where to start removing rows
            count (int): Number of removed rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were removed successfully, False otherwise
        """
        if row < 0 or count < 1 or row + count > self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        self._main_data[row : row + count] = []
        self.endRemoveRows()
        return True

    def removeColumns(self, column, count, parent=QModelIndex()):
        """Removes count columns starting with the given column under parent.

        Args:
            column (int): Column number where to start removing columns
            count (int): Number of removed columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were removed successfully, False otherwise
        """
        if column < 0 or count < 1 or column + count > self.columnCount():
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        # for loop all rows and remove the column from each
        for row in self._main_data:
            row[column : column + count] = []
        self.endRemoveColumns()
        return True

    def reset_model(self, main_data: Optional[TableData] = None) -> None:
        """Resets model."""
        if main_data is None:
            main_data = []
        self.beginResetModel()
        self._main_data = main_data
        self.endResetModel()

    def begin_paste(self) -> None:
        """Marks that data pasting has begun."""
        self._paste = True

    def end_paste(self) -> None:
        """Marks that data pasting has ended."""
        self._paste = False
