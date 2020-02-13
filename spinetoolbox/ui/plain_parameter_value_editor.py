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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\plain_parameter_value_editor.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\plain_parameter_value_editor.ui' applies.
#
# Created: Thu Feb 13 11:54:09 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_PlainParameterValueEditor(object):
    def setupUi(self, PlainParameterValueEditor):
        PlainParameterValueEditor.setObjectName("PlainParameterValueEditor")
        PlainParameterValueEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(PlainParameterValueEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.edit_layout = QtWidgets.QFormLayout()
        self.edit_layout.setObjectName("edit_layout")
        self.value_edit_label = QtWidgets.QLabel(PlainParameterValueEditor)
        self.value_edit_label.setObjectName("value_edit_label")
        self.edit_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.value_edit_label)
        self.value_edit = QtWidgets.QLineEdit(PlainParameterValueEditor)
        self.value_edit.setObjectName("value_edit")
        self.edit_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.value_edit)
        self.verticalLayout.addLayout(self.edit_layout)

        self.retranslateUi(PlainParameterValueEditor)
        QtCore.QMetaObject.connectSlotsByName(PlainParameterValueEditor)

    def retranslateUi(self, PlainParameterValueEditor):
        PlainParameterValueEditor.setWindowTitle(QtWidgets.QApplication.translate("PlainParameterValueEditor", "Form", None, -1))
        self.value_edit_label.setText(QtWidgets.QApplication.translate("PlainParameterValueEditor", "Parameter value", None, -1))

