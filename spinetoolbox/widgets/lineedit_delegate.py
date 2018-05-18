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
A delegate to edit table cells with custom lineEdits.

:author: Manuel Marin <manuelma@kth.se>
:date:   18.5.2018
"""
from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import QItemDelegate, QLineEdit, QSpinBox
import logging

class LineEditDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    commit_data = Signal(QLineEdit, name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        data = index.data(Qt.DisplayRole)
        if type(data) == int:
            editor.setValidator(QIntValidator(editor))
        return editor

    def setEditorData(self, editor, index):
        data = index.data(Qt.DisplayRole)
        if type(data) == int:
            data = str(data)
        editor.setText(data)

    def setModelData(self, editor, model, index):
        # do nothing here, we want to control it
        pass

    #@Slot(int, name='current_index_changed')
    #def current_index_changed(self):
    #    self.commit_data.emit(self.sender())
