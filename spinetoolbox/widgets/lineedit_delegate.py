#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
A delegate to edit table cells with custom QLineEdits.

:author: Manuel Marin <manuelma@kth.se>
:date:   18.5.2018
"""

from PySide2.QtCore import Qt, Slot, Signal, QEvent
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QItemDelegate, QLineEdit
import logging


class LineEditDelegate(QItemDelegate):
    """A delegate that places a fully functioning QLineEdit in every
    cell of the column to which it's applied."""

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomLineEditor. Set up a validator depending on datatype."""
        editor = CustomLineEditor(parent)
        data = index.data(Qt.EditRole)
        # editor.original_data = data
        editor.index = index
        if type(data) is int:
            editor.setValidator(QIntValidator(editor))
        return editor

    def setEditorData(self, editor, index):
        """Init the line editor with previous data from the index."""
        data = index.data(Qt.EditRole)
        if data:
            editor.setText(str(data))

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `closeEditor` signal."""
        pass


class CustomLineEditor(QLineEdit):

    def __init__(self, parent):
        super().__init__(parent)
        # self.original_data = None
        self.index = None
