######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Custom editors for model/view programming.


:author: M. Marin (KTH)
:date:   2.9.2018
"""
from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtWidgets import QComboBox, QLineEdit, QToolButton, QMenu, QWidget, QVBoxLayout, \
    QTextEdit, QPushButton
from PySide2.QtGui import QIntValidator
from widgets.custom_menus import QOkMenu


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
        index (QModelIndex): the model index being edited
        items (list): list of items to populate the combobox
    """
    def __init__(self, parent, index, items):
        super().__init__(parent)
        self.text = self.currentText
        self._index = index
        self.row = index.row()
        self.column = index.column()
        self.previous_data = index.data(Qt.EditRole)
        self.addItems(items)
        self.setCurrentIndex(-1)  # force index change
        self.currentIndexChanged.connect(self.close)

    def index(self):
        return self._index


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
        index (QModelIndex): the model index being edited
    """
    def __init__(self, parent, index):
        super().__init__(parent)
        self._index = index
        data = index.data(Qt.EditRole)
        if type(data) is int:
            self.setValidator(QIntValidator(self))

    def index(self):
        return self._index


class CustomTextEditor(QWidget):
    """A custom QWidget with a QTextEdit and a QPushButton to edit JSON data.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
        index (QModelIndex): the model index being edited
    """
    commit_data = Signal("QWidget", name="commit_data")

    def __init__(self, parent, index):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.text_edit = QTextEdit(self)
        self.push_button = QPushButton("Ok", self)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.push_button)
        self.setLayout(layout)
        self.text = self.text_edit.toPlainText
        self.push_button.clicked.connect(self._handle_ok_clicked)
        self._index = index

    def index(self):
        return self._index

    @Slot("bool", name="_handle_ok_clicked")
    def _handle_ok_clicked(self, checked=False):
        self.commit_data.emit(self)
        self.close()


# NOTE: Only in use by ForeignKeysDelegate at the moment
class CustomSimpleToolButtonEditor(QToolButton):
    """A custom QToolButton to popup a Qmenu.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
        index (QModelIndex): the model index being edited
        field_name_list (list): list of all field names in the datapackage
        current_field_name_list (list): list of currently selected field names
    """
    def __init__(self, parent, index, field_name_list, current_field_name_list):
        """Initialize class."""
        super().__init__(parent)
        self._text = None
        self._index = index
        self.setPopupMode(QToolButton.InstantPopup)
        self.menu = QOkMenu(parent)
        for field_name in field_name_list:
            action = self.menu.addAction(field_name)
            action.setCheckable(True)
            if field_name in current_field_name_list:
                action.setChecked(True)
        self.menu.addSeparator()
        action_ok = self.menu.addAction("Ok")
        action_ok.triggered.connect(self._handle_ok_clicked)
        self.setMenu(self.menu)

    @Slot("bool", name="_handle_ok_clicked")
    def _handle_ok_clicked(self, checked=False):
        field_name_list = list()
        for action in self.menu.actions():
            if action.isChecked():
                field_name_list.append(action.text())
        self._text = ",".join(field_name_list)
        self.close()

    def index(self):
        return self._index

    def text(self):
        return self._text
