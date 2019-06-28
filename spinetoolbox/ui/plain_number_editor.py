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

# Form implementation generated from reading ui file '../spinetoolbox/ui/plain_number_editor.ui',
# licensing of '../spinetoolbox/ui/plain_number_editor.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_NumberEditor(object):
    def setupUi(self, NumberEditor):
        NumberEditor.setObjectName("NumberEditor")
        NumberEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(NumberEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.edit_layout = QtWidgets.QFormLayout()
        self.edit_layout.setObjectName("edit_layout")
        self.value_edit_label = QtWidgets.QLabel(NumberEditor)
        self.value_edit_label.setObjectName("value_edit_label")
        self.edit_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.value_edit_label)
        self.value_edit = QtWidgets.QLineEdit(NumberEditor)
        self.value_edit.setObjectName("value_edit")
        self.edit_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.value_edit)
        self.verticalLayout.addLayout(self.edit_layout)

        self.retranslateUi(NumberEditor)
        QtCore.QMetaObject.connectSlotsByName(NumberEditor)

    def retranslateUi(self, NumberEditor):
        NumberEditor.setWindowTitle(QtWidgets.QApplication.translate("NumberEditor", "Form", None, -1))
        self.value_edit_label.setText(QtWidgets.QApplication.translate("NumberEditor", "Parameter value", None, -1))

