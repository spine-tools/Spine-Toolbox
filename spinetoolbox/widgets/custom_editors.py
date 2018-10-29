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
from PySide2.QtWidgets import QComboBox, QLineEdit, QToolButton, QMenu, QTableView
from PySide2.QtGui import QIntValidator
from widgets.custom_menus import QOkMenu
from models import JSONModel


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    commit_data = Signal("QWidget", name="commit_data")

    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, current_text, items):
        self.addItems(items)
        if current_text:
            self.setCurrentText(current_text)
        else:
            self.setCurrentIndex(-1)
        self.activated.connect(self.close)
        self.showPopup()

    def data(self):
        return self.currentText()


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, data):
        if data is not None:
            self.setText(str(data))
        if type(data) is int:
            self.setValidator(QIntValidator(self))

    def data(self):
        return self.text()


class JSONEditor(QTableView):
    """A custom QTableView to edit JSON data.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.json_model = JSONModel(self)
        self.setModel(self.json_model)
        self.verticalHeader().setDefaultSectionSize(parent.parent().verticalHeader().defaultSectionSize())

    def set_data(self, data):
        self.json_model.reset_model(data)

    def data(self):
        return self.json_model.json()


class CustomSimpleToolButtonEditor(QToolButton):
    """A custom QToolButton to popup a Qmenu.

    Attributes:
        parent (SpineDatapackageWidget): spine datapackage widget
    """
    commit_data = Signal("QWidget", name="commit_data")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._text = None
        self.setPopupMode(QToolButton.InstantPopup)
        self.menu = QOkMenu(parent)

    @Slot("bool", name="_handle_ok_clicked")
    def _handle_ok_clicked(self, checked=False):
        field_name_list = list()
        for action in self.menu.actions():
            if action.isChecked():
                field_name_list.append(action.text())
        self._text = ",".join(field_name_list)
        self.commit_data.emit(self)
        self.close()

    def set_data(self, field_name_list, current_field_name_list):
        for field_name in field_name_list:
            action = self.menu.addAction(field_name)
            action.setCheckable(True)
            if field_name in current_field_name_list:
                action.setChecked(True)
        self.menu.addSeparator()
        action_ok = self.menu.addAction("Ok")
        action_ok.triggered.connect(self._handle_ok_clicked)
        self.setMenu(self.menu)
        self.click()

    def data(self):
        return self._text
