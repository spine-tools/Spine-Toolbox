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
"""DB Editor specific QUndoCommand subclasses."""
from __future__ import annotations
from collections.abc import Iterable
import pickle
from typing import TYPE_CHECKING
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QUndoCommand

if TYPE_CHECKING:
    from .mvcmodels.empty_models import EmptyModelBase


class UpdateEmptyModel(QUndoCommand):
    def __init__(self, model: EmptyModelBase, indexes: Iterable[QModelIndex], values: Iterable):
        super().__init__(f"update unfinished {model.item_type}")
        self._model = model
        self._rows = []
        self._columns = []
        self._undo_values = []
        for index in indexes:
            self._rows.append(index.row())
            self._columns.append(index.column())
            self._undo_values.append(pickle.dumps(index.data()))
        self._redo_values = [pickle.dumps(value) for value in values]

    def redo(self):
        self._apply(self._redo_values)

    def undo(self):
        if not self.isObsolete():
            self._apply(self._undo_values)

    def _apply(self, values: list[bytes]) -> None:
        indexes = [self._model.index(row, column) for row, column in zip(self._rows, self._columns)]
        values = [pickle.loads(x) for x in values]
        if not self._model.do_batch_set_data(indexes, values):
            self.setObsolete(True)


class AppendEmptyRow(QUndoCommand):
    def __init__(self, model: EmptyModelBase):
        super().__init__("append empty row")
        self._model = model

    def redo(self):
        self._model.append_empty_row()

    def undo(self):
        if not self.isObsolete():
            self._model.remove_empty_row()


class InsertEmptyModelRow(QUndoCommand):
    def __init__(self, model: EmptyModelBase, row: int):
        super().__init__("remove row")
        self._model = model
        self._row = row

    def redo(self):
        self._model.do_insert_rows(self._row, 1)

    def undo(self):
        if self._row == self._model.rowCount() - 1:
            self._model.remove_empty_row()
        else:
            self._model.do_remove_rows(self._row, 1)


class RemoveEmptyModelRow(QUndoCommand):
    def __init__(self, model: EmptyModelBase, row: int):
        super().__init__("remove row")
        self._model = model
        self._row = row
        self._undo_data = [
            pickle.dumps(self._model.index(row, column).data()) for column in range(self._model.columnCount())
        ]

    def redo(self):
        self._model.do_remove_rows(self._row, 1)

    def undo(self):
        self._model.do_insert_rows(self._row, 1)
        indexes = [self._model.index(self._row, column) for column in range(self._model.columnCount())]
        values = [pickle.loads(value) for value in self._undo_data]
        self._model.do_batch_set_data(indexes, values)
