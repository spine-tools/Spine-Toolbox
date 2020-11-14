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

from PySide2.QtCore import QAbstractItemModel, QModelIndex, Qt
from ..commands import SetTableChecked


class SourceTableItem:
    """A list item for :class:`_SourceTableListModel`"""

    def __init__(self, name, checked):
        self.name = name
        self.checked = checked


class SourceTableListModel(QAbstractItemModel):
    """Model for source table lists which supports undo/redo functionality."""

    def __init__(self, source, undo_stack):
        """
        Args:
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._root_item = SourceTableItem(source, None)
        self._tables = []
        self._undo_stack = undo_stack

    @property
    def _root_index(self):
        return self.createIndex(0, 0, self._root_item)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return 1
        if parent.internalPointer() == self._root_item:
            return len(self._tables)
        return 0

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            return self.createIndex(row, column, self._root_item)
        return self.createIndex(row, column, self._tables[row])

    def parent(self, index):
        if index.internalPointer() == self._root_item:
            return QModelIndex()
        return self.createIndex(0, 0, self._root_item)

    def checked_table_names(self):
        return [table.name for table in self._tables if table.checked]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return index.internalPointer().name
        if role == Qt.CheckStateRole:
            if index.flags() & Qt.ItemIsUserCheckable:
                return Qt.Checked if index.internalPointer().checked else Qt.Unchecked
        return None

    def flags(self, index):
        if index.internalPointer() == self._root_item:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def reset(self, items):
        self.beginResetModel()
        self._tables = items
        self.endResetModel()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            row = index.row()
            item = self._tables[row]
            checked = value == Qt.Checked
            self._undo_stack.push(SetTableChecked(item.name, self, row, checked))
        return True

    def set_checked(self, row, checked):
        """
        Sets the checked status of a list item.

        Args:
            row (int): item row
            checked (bool): True for checked, False for unchecked
        """
        self._tables[row].checked = checked
        index = self.index(row, 0, parent=self._root_index)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def set_multiple_checked_undoable(self, rows, checked):
        """
        Sets the checked status of multiple list items.

        This action is undoable.

        Args:
            rows (Iterable of int): item rows
            checked (bool): True for checked, False for unchecked
        """
        self._undo_stack.beginMacro("select" if checked else "deselect" + " source tables")
        for row in rows:
            self._undo_stack.push(SetTableChecked(self._tables[row].name, self, row, checked))
        self._undo_stack.endMacro()

    def table_at(self, index):
        if index.internalPointer() == self._root_item:
            return None
        return self._tables[index.row()]

    def table_index(self, table):
        rows = {table.name: i for i, table in enumerate(self._tables)}
        try:
            return self.index(rows[table], 0, parent=self._root_index)
        except KeyError:
            return QModelIndex()

    def table_names(self):
        return [table.name for table in self._tables]
