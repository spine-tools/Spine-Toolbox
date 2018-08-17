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
A delegate to edit table cells with checkboxes.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""

import logging
from PySide2.QtCore import Qt, Signal, QEvent, QPoint, QRect
from PySide2.QtWidgets import QItemDelegate, QStyleOptionButton, QStyle, QApplication


class CheckBoxDelegate(QItemDelegate):
    """A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied."""

    commit_data = Signal("QModelIndex", name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)
        self.checkbox_pressed = False

    def createEditor(self, parent, option, index):
        """Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model."""
        return None

    def paint(self, painter, option, index):
        """Paint a checkbox without the label."""
        checked = True
        if index.data() == "False" or not index.data():
            checked = False
        checkbox_style_option = QStyleOptionButton()
        if (index.flags() & Qt.ItemIsEditable) > 0:
            checkbox_style_option.state |= QStyle.State_Enabled
        else:
            checkbox_style_option.state |= QStyle.State_ReadOnly
        if checked:
            checkbox_style_option.state |= QStyle.State_On
        else:
            checkbox_style_option.state |= QStyle.State_Off
        checkbox_style_option.rect = self.get_checkbox_rect(option)
        # noinspection PyArgumentList
        QApplication.style().drawControl(QStyle.CE_CheckBox, checkbox_style_option, painter)

    def editorEvent(self, event, model, option, index):
        """Change the data in the model and the state of the checkbox
        when user presses left mouse button and this cell is editable.
        Otherwise do nothing."""
        if not (index.flags() & Qt.ItemIsEditable) > 0:
            return False
        # Do nothing on double-click
        if event.type() == QEvent.MouseButtonDblClick:
            return True
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and self.get_checkbox_rect(option).contains(event.pos()):
                self.checkbox_pressed = True
                return True
        if event.type() == QEvent.MouseButtonRelease:
            if self.checkbox_pressed and self.get_checkbox_rect(option).contains(event.pos()):
                # Change the checkbox-state
                # self.setModelData(None, model, index)
                self.commit_data.emit(index)
                self.checkbox_pressed = False
                return True
            self.checkbox_pressed = False
        return False

    def setModelData (self, editor, model, index):
        """Do nothing. Model data is updated by handling the `commit_data` signal."""
        pass

    def get_checkbox_rect(self, option):
        checkbox_style_option = QStyleOptionButton()
        checkbox_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, checkbox_style_option, None)
        checkbox_point = QPoint (option.rect.x() +
                            option.rect.width() / 2 -
                            checkbox_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            checkbox_rect.height() / 2)
        return QRect(checkbox_point, checkbox_rect.size())
