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
Contains undo and redo commands for Import editor.

:author: A. Soininen (VTT)
:date:   4.8.2020
"""
from PySide2.QtWidgets import QUndoCommand


class SetTableChecked(QUndoCommand):
    def __init__(self, table_name, table_list_model, row, checked):
        text = ("select" if checked else "deselect") + f" '{table_name}'"
        super().__init__(text)
        self._model = table_list_model
        self._row = row
        self._checked = checked

    def redo(self):
        self._model.set_checked(self._row, self._checked)

    def undo(self):
        self._model.set_checked(self._row, not self._checked)
