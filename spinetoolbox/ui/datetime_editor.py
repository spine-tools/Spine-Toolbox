# -*- coding: utf-8 -*-
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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\datetime_editor.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\datetime_editor.ui' applies.
#
# Created: Thu Feb 13 11:53:57 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_DatetimeEditor(object):
    def setupUi(self, DatetimeEditor):
        DatetimeEditor.setObjectName("DatetimeEditor")
        DatetimeEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(DatetimeEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.layout = QtWidgets.QFormLayout()
        self.layout.setObjectName("layout")
        self.datetime_edit_label = QtWidgets.QLabel(DatetimeEditor)
        self.datetime_edit_label.setObjectName("datetime_edit_label")
        self.layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.datetime_edit_label)
        self.edit_layout = QtWidgets.QVBoxLayout()
        self.edit_layout.setObjectName("edit_layout")
        self.datetime_edit = QtWidgets.QDateTimeEdit(DatetimeEditor)
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setObjectName("datetime_edit")
        self.edit_layout.addWidget(self.datetime_edit)
        self.format_label = QtWidgets.QLabel(DatetimeEditor)
        self.format_label.setObjectName("format_label")
        self.edit_layout.addWidget(self.format_label)
        self.layout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.edit_layout)
        self.verticalLayout.addLayout(self.layout)

        self.retranslateUi(DatetimeEditor)
        QtCore.QMetaObject.connectSlotsByName(DatetimeEditor)

    def retranslateUi(self, DatetimeEditor):
        DatetimeEditor.setWindowTitle(QtWidgets.QApplication.translate("DatetimeEditor", "Form", None, -1))
        self.datetime_edit_label.setText(QtWidgets.QApplication.translate("DatetimeEditor", "Datetime", None, -1))
        self.datetime_edit.setDisplayFormat(QtWidgets.QApplication.translate("DatetimeEditor", "yyyy-MM-ddTHH:mm:ss", None, -1))
        self.format_label.setText(QtWidgets.QApplication.translate("DatetimeEditor", "Format: YYYY-DD-MMThh:mm:ss", None, -1))

