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
Classes for custom item delegates.

:author: Manuel Marin <manuelma@kth.se>
:date:   12.4.2018
"""
import logging
from PySide2.QtCore import Slot, Signal
from PySide2.QtWidgets import QItemDelegate, QComboBox, QToolButton, QStyleOptionButton, QStyle, QApplication
from PySide2.QtCore import Slot, Qt, QEvent, QPoint, QRect

class ComboBoxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    commit_data = Signal(QComboBox, name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.row = index.row()
        combo.column = index.column()
        combo.previous_data = index.model().data(index)
        combo_items = index.model().combo_items_method
        items = combo_items(index)
        if items:
            combo.addItems(items)
            combo.setCurrentIndex(-1)   #force index change
            combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

    def setEditorData(self, editor, index):
        editor.showPopup()

    def setModelData(self, editor, model, index):
        pass

    @Slot(int, name='current_index_changed')
    def current_index_changed(self):
        self.commit_data.emit(self.sender())



class ToolButtonDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QToolButton in every
    cell of the column to which it's applied
    """
    commit_data = Signal(QToolButton, name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        button = QToolButton(parent)
        button.row = index.row()
        button.column = index.column()
        button.clicked.connect(self.clicked)
        return button

    def setEditorData(self, editor, index):
        editor.showPopup()

    def setModelData(self, editor, model, index):
        pass

    @Slot(int, name='clicked')
    def clicked(self):
        self.commit_data.emit(self.sender())



class CheckBoxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        '''
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        '''
        return None

    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''

        checked = index.data()
        check_box_style_option = QStyleOptionButton()

        if (index.flags() & Qt.ItemIsEditable) > 0:
            check_box_style_option.state |= QStyle.State_Enabled
        else:
            check_box_style_option.state |= QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QStyle.State_On
        else:
            check_box_style_option.state |= QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        QApplication.style().drawControl(QStyle.CE_CheckBox, check_box_style_option, painter)

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable.
        Otherwise do nothing.
        '''
        if not (index.flags() & Qt.ItemIsEditable) > 0:
            return False

        # Do not change the checkbox-state
        if event.type() == QEvent.MouseButtonPress:
            return False
        if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.MouseButtonDblClick:
            if event.button() != Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                return True

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        newValue = not index.data()
        model.setData(index, newValue, Qt.DisplayRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QPoint (option.rect.x() +
                            option.rect.width() / 2 -
                            check_box_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            check_box_rect.height() / 2)
        return QRect(check_box_point, check_box_rect.size())
