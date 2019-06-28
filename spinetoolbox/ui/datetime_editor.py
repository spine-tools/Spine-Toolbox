######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/datetime_editor.ui',
# licensing of '../spinetoolbox/ui/datetime_editor.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_DatetimeEditor(object):
    def setupUi(self, DatetimeEditor):
        DatetimeEditor.setObjectName("DatetimeEditor")
        DatetimeEditor.resize(400, 300)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DatetimeEditor)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.layout = QtWidgets.QFormLayout()
        self.layout.setObjectName("layout")
        self.datetime_edit_label = QtWidgets.QLabel(DatetimeEditor)
        self.datetime_edit_label.setObjectName("datetime_edit_label")
        self.layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.datetime_edit_label)
        self.edit_layout = QtWidgets.QVBoxLayout()
        self.edit_layout.setObjectName("edit_layout")
        self.datetime_edit = QtWidgets.QLineEdit(DatetimeEditor)
        self.datetime_edit.setObjectName("datetime_edit")
        self.edit_layout.addWidget(self.datetime_edit)
        self.datetime_edit_label_2 = QtWidgets.QLabel(DatetimeEditor)
        self.datetime_edit_label_2.setObjectName("datetime_edit_label_2")
        self.edit_layout.addWidget(self.datetime_edit_label_2)
        self.layout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.edit_layout)
        self.verticalLayout_2.addLayout(self.layout)

        self.retranslateUi(DatetimeEditor)
        QtCore.QMetaObject.connectSlotsByName(DatetimeEditor)

    def retranslateUi(self, DatetimeEditor):
        DatetimeEditor.setWindowTitle(QtWidgets.QApplication.translate("DatetimeEditor", "Form", None, -1))
        self.datetime_edit_label.setText(QtWidgets.QApplication.translate("DatetimeEditor", "Datetime", None, -1))
        self.datetime_edit_label_2.setText(QtWidgets.QApplication.translate("DatetimeEditor", "Format: YYYY-DD-MMThh:mm:ss", None, -1))

