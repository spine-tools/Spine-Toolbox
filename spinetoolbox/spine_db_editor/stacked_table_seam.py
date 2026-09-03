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
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent, Qt


class AboveSeam:
    focus_to_bottom_table_requested = Signal(int)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Down and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            current_index = self.currentIndex()
            if current_index.row() == self.model().rowCount() - 1:
                self.focus_to_bottom_table_requested.emit(current_index.column())
                return
        super().keyPressEvent(event)


class BelowSeam:
    focus_to_top_table_requested = Signal(int)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Up and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            current_index = self.currentIndex()
            if current_index.row() == 0:
                self.focus_to_top_table_requested.emit(current_index.column())
                return
        super().keyPressEvent(event)


class StackedTableSeam:
    """'Glues' a stacked table and corresponding empty table together
    so that keyboard navigation is possible between them."""

    def __init__(self, top_table: AboveSeam, bottom_table: BelowSeam):
        self._top_table = top_table
        self._top_table.focus_to_bottom_table_requested.connect(self._focus_to_bottom)
        self._bottom_table = bottom_table
        self._bottom_table.focus_to_top_table_requested.connect(self._focus_to_top)

    def _focus_to_top(self, column: int) -> None:
        top_model = self._top_table.model()
        last_row = top_model.rowCount() - 1
        self._top_table.setCurrentIndex(top_model.index(last_row, column))
        self._top_table.setFocus()

    def _focus_to_bottom(self, column: int) -> None:
        bottom_model = self._bottom_table.model()
        self._bottom_table.setCurrentIndex(bottom_model.index(0, column))
        self._bottom_table.setFocus()
