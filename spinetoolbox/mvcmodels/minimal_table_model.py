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
Contains a minimal table model.

:authors: M. Marin (KTH)
:date:   20.5.2018
"""

import logging
from PySide2.QtCore import Qt, QModelIndex, QAbstractTableModel


class MinimalTableModel(QAbstractTableModel):
    def __init__(self, parent=None, header=None, lazy=True):
        """Table model for outlining simple tabular data.

        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent)
        if header is None:
            header = []
        self.header = header
        self._main_data = list()
        self._fetched = not lazy

    def clear(self):
        """Clear all data in model."""
        self.beginResetModel()
        self._main_data.clear()
        self.endResetModel()

    def flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def canFetchMore(self, parent=None):
        """Return True if the model hasn't been fetched."""
        return not self._fetched

    def fetchMore(self, parent=None):
        """Fetch data and use it to reset the model."""
        self._fetched = True

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in the model."""
        return len(self._main_data)

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in the model."""
        return len(self.header) or len(next(iter(self._main_data), []))

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Returns headers."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            try:
                return self.header[section]
            except IndexError:
                return None
        if orientation == Qt.Vertical:
            return section + 1

    def set_horizontal_header_labels(self, labels):
        """Set horizontal header labels."""
        if not labels:
            return
        self.header = labels
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(labels) - 1)

    def insert_horizontal_header_labels(self, section, labels):
        """Insert horizontal header labels at the given section."""
        if not labels:
            return
        for j, value in enumerate(labels):
            if section + j >= self.columnCount():
                self.header.append(value)
            else:
                self.header.insert(section + j, value)
        self.headerDataChanged.emit(Qt.Horizontal, section, section + len(labels) - 1)

    def horizontal_header_labels(self):
        return self.header

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if orientation != Qt.Horizontal:
            return False
        if role != Qt.EditRole:
            return False
        try:
            self.header[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        except IndexError:
            return False

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index.

        Args:
            index (QModelIndex): Index of item
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not index.isValid():
            return None
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        try:
            return self._main_data[index.row()][index.column()]
        except IndexError:
            logging.error("Cannot access model data at index %s", index)
            return None

    def row_data(self, row, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the given row.

        Args:
            row (int): Item row
            role (int): Data role

        Returns:
            Row data for given role.
        """
        if not 0 <= row < self.rowCount():
            return None
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        return self._main_data[row]

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in model."""
        if not index.isValid():
            return False
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return False
        return self.batch_set_data([index], [value])

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes."""
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
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right), [Qt.EditRole, Qt.DisplayRole])
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
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            if self.columnCount() == 0:
                new_main_row = [None]
            else:
                new_main_row = [None for j in range(self.columnCount())]
            # Notice if insert index > rowCount(), new object is inserted to end
            self._main_data.insert(row + i, new_main_row)
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
        for i in reversed(range(row, row + count)):
            self._main_data.pop(i)
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
        if column < 0 or column >= self.columnCount():
            return False
        if not count == 1:
            logging.error("Remove 1 column at a time")
            return False
        self.beginRemoveColumns(parent, column, column)
        # for loop all rows and remove the column from each
        removing_last_column = False
        if self.columnCount() == 1:
            removing_last_column = True
        for r in self._main_data:
            r.pop(column)
        if removing_last_column:
            self._main_data = []
        # logging.debug("{0} removed from column:{1}".format(removed_column, column))
        self.endRemoveColumns()
        return True

    def reset_model(self, main_data=None):
        """Reset model."""
        if main_data is None:
            main_data = list()
        self.beginResetModel()
        self._main_data = main_data
        self.endResetModel()
