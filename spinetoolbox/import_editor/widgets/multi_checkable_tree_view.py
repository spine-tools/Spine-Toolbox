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
Contains :class:`MultiCheckableListView`.

:author: A. Soininen (VTT)
:date:   13.8.2020
"""
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeView


class MultiCheckableTreeView(QTreeView):
    """A list view which allows all selected items to be checked/unchecked with space bar."""

    def keyPressEvent(self, event):
        """Handles key press events."""
        if event.key() != Qt.Key_Space or event.modifiers() != Qt.NoModifier:
            super().keyPressEvent(event)
            return
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            super().keyPressEvent(event)
            return
        selected = selection_model.selectedIndexes()
        model = self.model()
        check_state = Qt.Unchecked if selected[0].data(Qt.CheckStateRole) == Qt.Checked else Qt.Checked
        if len(selected) == 1:
            model.setData(selected[0], check_state, Qt.CheckStateRole)
        else:
            rows = [index.row() for index in selected]
            model.set_multiple_checked_undoable(rows, check_state)
