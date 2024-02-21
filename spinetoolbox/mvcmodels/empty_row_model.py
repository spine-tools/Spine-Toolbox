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

""" Contains a table model with an empty last row. """
from PySide6.QtCore import Qt, Slot, QModelIndex
from .minimal_table_model import MinimalTableModel


class EmptyRowModel(MinimalTableModel):
    """A table model with a last empty row."""

    def __init__(self, parent=None, header=None):
        """Init class."""
        super().__init__(parent, header=header)
        self.default_row = {}  # A row of default values to put in any newly inserted row
        self.force_default = False  # Whether or not default values are editable
        self._fetched = False
        self.dataChanged.connect(self._handle_data_changed)
        self.rowsInserted.connect(self._handle_rows_inserted)

    def canFetchMore(self, _parent):
        return not self._fetched

    def fetchMore(self, parent):
        self.insertRows(self.rowCount(), 1, parent)
        self._fetched = True

    def flags(self, index):
        """Return default flags except if forcing defaults."""
        if self.force_default:
            try:
                name = self.header[index.column()]
                if name in self.default_row:
                    return super().flags(index) & ~Qt.ItemIsEditable
            except IndexError:
                pass
        return super().flags(index)

    def set_default_row(self, **kwargs):
        """Set default row data."""
        self.default_row = kwargs

    def clear(self):
        self._fetched = False
        super().clear()

    def reset_model(self, main_data=None):
        self._fetched = False
        super().reset_model(main_data)

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_data_changed(self, top_left, bottom_right, roles=None):
        """Insert a new last empty row in case the previous one has been filled
        with any data other than the defaults."""
        if roles is None:
            roles = list()
        if roles and Qt.ItemDataRole.EditRole not in roles:
            return
        last_row = self.rowCount() - 1
        for column in range(self.columnCount()):
            try:
                field = self.header[column]
            except IndexError:
                field = None
            data = self._main_data[last_row][column]
            default = self.default_row.get(field)
            if (data or default) and data != default:
                self.insertRows(self.rowCount(), 1)
                break

    def removeRows(self, row, count, parent=QModelIndex()):
        """Don't remove the last empty row."""
        if row + count == self.rowCount():
            count -= 1
        return super().removeRows(row, count, parent)

    @Slot(QModelIndex, int, int)
    def _handle_rows_inserted(self, parent, first, last):
        """Handle rowsInserted signal."""
        self.set_rows_to_default(first, last)

    def set_rows_to_default(self, first, last=None):
        """Set default data in newly inserted rows."""
        if last is None:
            last = first
        if first >= self.rowCount() or last < 0:
            return
        default_row = []
        for column in range(self.columnCount()):
            try:
                field = self.header[column]
            except IndexError:
                field = None
            default = self.default_row.get(field)
            default_row.append(default)
        for row in range(first, last + 1):
            self._main_data[row] = default_row.copy()
        top_left = self.index(first, 0)
        bottom_right = self.index(last, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)
