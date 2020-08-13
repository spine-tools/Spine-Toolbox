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
from functools import partial
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QListView


class MultiCheckableListView(QListView):
    """A list view which allows all selected items to be checked/unchecked with space bar."""

    def __init__(self, parent):
        """
        Args
            parent (QWidget): a parent widget
        """
        super().__init__(parent)

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
        first = selected[0]
        check_state = Qt.Unchecked if first.data(Qt.CheckStateRole) == Qt.Checked else Qt.Checked
        model = self.model()
        check_item = partial(model.setData, value=check_state, role=Qt.CheckStateRole)
        for index in selected:
            check_item(index)
