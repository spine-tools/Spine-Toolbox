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
Custom editors for model/view programming.

:author: Manuel Marin <manuelma@kth.se>
:date:   2.9.2018
"""
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QComboBox, QLineEdit, QToolButton, QMenu, QAction, QWidgetAction, QWidget, \
    QHBoxLayout, QActionGroup
from PySide2.QtGui import QStandardItemModel, QStandardItem, QIntValidator
import logging


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models."""
    def __init__(self, parent, index, items):
        super().__init__(parent)
        self.text = self.currentText
        self._index = index
        self.row = index.row()
        self.column = index.column()
        self.previous_data = index.data(Qt.EditRole)
        self.addItems(items)
        self.setCurrentIndex(-1) # force index change
        self.currentIndexChanged.connect(self.close)

    def index(self):
        return self._index

class CustomCheckableComboEditor(QComboBox):
    """A custom QComboBox to handle data from models."""
    def __init__(self, parent, index, items):
        super().__init__(parent)
        self.text = self.currentText
        self.index = index
        self.row = index.row()
        self.column = index.column()
        self.previous_data = index.data(Qt.EditRole)
        model = QStandardItemModel()
        for item in items:
            q_item = QStandardItem(item)
            q_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            q_item.setData(Qt.Unchecked, Qt.CheckStateRole)
            model.appendRow(q_item)
        self.setModel(model)


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models."""
    def __init__(self, parent, index):
        super().__init__(parent)
        self._index = index
        data = index.data(Qt.EditRole)
        if type(data) is int:
            self.setValidator(QIntValidator(self))

    def index(self):
        return self._index


class CustomToolButtonEditor(QToolButton):
    """A custom QToolButton to handle data from models."""
    def __init__(self, parent, index, object_class_name_list, **object_name_dict):
        """Initialize class."""
        super().__init__(parent)
        self._text = None
        self._index = index
        self.setPopupMode(QToolButton.InstantPopup)
        #self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setText(index.data(Qt.DisplayRole))
        self.menu = QMenu(parent)
        widget = QWidget(self)
        widget.setLayout(QHBoxLayout(widget))
        widget.layout().setContentsMargins(6, 6, 6, 6)
        widget.layout().setSpacing(6)
        for object_class_name in object_class_name_list:
            object_name_list = object_name_dict[object_class_name]
            submenu = QMenu(self.menu)
            submenu.addSection(object_class_name)
            action_group = QActionGroup(submenu)
            for object_name in object_name_list:
                action = submenu.addAction(object_name)
                action.setCheckable(True)
                action_group.addAction(action)
            widget.layout().addWidget(submenu)
        self.widget_action = QWidgetAction(self.menu)
        self.widget_action.setDefaultWidget(widget)
        self.menu.addAction(self.widget_action)
        action_ok = QAction("Ok", self.menu)
        action_ok.triggered.connect(self.commit_data)
        self.menu.addAction(action_ok)
        self.setMenu(self.menu)

    @Slot("bool", name="commit_data")
    def commit_data(self, checked):
        #self.setPopupMode(QToolButton.DelayedPopup)
        layout = self.widget_action.defaultWidget().layout()
        object_name_list = list()
        for i in range(layout.count()):
            submenu = layout.itemAt(i).widget()
            for action in submenu.actions():
                if action.isChecked():
                    object_name_list.append(action.text())
                    break
        self._text = ",".join(object_name_list)
        self.close()

    def index(self):
        return self._index

    def text(self):
        return self._text
