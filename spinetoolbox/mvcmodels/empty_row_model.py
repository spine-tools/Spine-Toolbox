######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a table model with an empty last row.

:authors: M. Marin (KTH)
:date:   20.5.2018
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from mvcmodels.minimal_table_model import MinimalTableModel


class EmptyRowModel(MinimalTableModel):
    """A table model with a last empty row."""

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.default_row = {}  # A row of default values to put in any newly inserted row
        self.force_default = False  # Whether or not default values are editable
        self._fetched = False
        self.dataChanged.connect(self._handle_data_changed)
        self.rowsRemoved.connect(self._handle_rows_removed)
        self.rowsInserted.connect(self._handle_rows_inserted)

    def canFetchMore(self, parent=None):
        return not self._fetched

    def fetchMore(self, parent=None):
        self.insertRows(self.rowCount(), 1, QModelIndex())
        self._fetched = True

    def flags(self, index):
        """Return default flags except if forcing defaults."""
        if not index.isValid():
            return Qt.NoItemFlags
        if self.force_default:
            try:
                name = self.header[index.column()]
                if name in self.default_row:
                    return self.default_flags & ~Qt.ItemIsEditable
            except IndexError:
                pass
        return self.default_flags

    def set_default_row(self, **kwargs):
        """Set default row data."""
        self.default_row = kwargs

    def clear(self):
        self._fetched = False
        super().clear()

    def reset_model(self, main_data=None):
        self._fetched = False
        super().reset_model(main_data)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_data_changed")
    def _handle_data_changed(self, top_left, bottom_right, roles=None):
        """Insert a new last empty row in case the previous one has been filled
        with any data other than the defaults."""
        if roles is None:
            roles = list()
        if roles and Qt.EditRole not in roles:
            return
        last_row = self.rowCount() - 1
        for column in range(self.columnCount()):
            try:
                name = self.header[column]
            except IndexError:
                name = None
            data = self._main_data[last_row][column]
            default = self.default_row.get(name)
            if not data and not default:
                continue
            if data != default:
                self.insertRows(self.rowCount(), 1)
                break

    @Slot("QModelIndex", "int", "int", name="_handle_rows_removed")
    def _handle_rows_removed(self, parent, first, last):
        """Insert a new empty row in case it's been removed."""
        last_row = self.rowCount()
        if last_row in range(first, last + 1):
            self.insertRows(self.rowCount(), 1)

    @Slot("QModelIndex", "int", "int", name="_handle_rows_inserted")
    def _handle_rows_inserted(self, parent, first, last):
        """Handle rowsInserted signal."""
        self.set_rows_to_default(first, last)

    def set_rows_to_default(self, first, last):
        """Set default data in newly inserted rows."""
        left = None
        right = None
        for column in range(self.columnCount()):
            try:
                name = self.header[column]
            except IndexError:
                name = None
            default = self.default_row.get(name)
            if left is None:
                left = column
            right = column
            for row in range(first, last + 1):
                self._main_data[row][column] = default
        if left is None:
            return
        top_left = self.index(first, left)
        bottom_right = self.index(last, right)
        self.dataChanged.emit(top_left, bottom_right)
