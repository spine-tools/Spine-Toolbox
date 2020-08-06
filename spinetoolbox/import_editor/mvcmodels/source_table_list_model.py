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
Contains SourceTableListModel and associated list item classes

:author: A. Soininen (VTT)
:date:   6.8.2019
"""

from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt
from ..commands import SetTableChecked


class SourceTableItem:
    """A list item for :class:`_SourceTableListModel`"""

    def __init__(self, name, checked):
        self.name = name
        self.checked = checked


class SourceTableListModel(QAbstractListModel):
    """Model for source table lists which supports undo/redo functionality."""

    def __init__(self, undo_stack):
        """
        Args:
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._tables = []
        self._undo_stack = undo_stack

    def checked_table_names(self):
        return [table.name for table in self._tables if table.checked]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._tables[index.row()].name
        if role == Qt.CheckStateRole:
            return Qt.Checked if self._tables[index.row()].checked else Qt.Unchecked
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return None

    def reset(self, items):
        self.beginResetModel()
        self._tables = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._tables)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            row = index.row()
            item = self._tables[row]
            checked = value == Qt.Checked
            self._undo_stack.push(SetTableChecked(item.name, self, row, checked))
        return False

    def set_checked(self, row, checked):
        self._tables[row].checked = checked
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def table_at(self, row):
        return self._tables[row]

    def table_names(self):
        return [table.name for table in self._tables]
