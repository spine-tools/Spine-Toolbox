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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\plain_parameter_value_editor.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\plain_parameter_value_editor.ui' applies.
#
# Created: Wed Mar 25 13:26:22 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_PlainParameterValueEditor(object):
    def setupUi(self, PlainParameterValueEditor):
        PlainParameterValueEditor.setObjectName("PlainParameterValueEditor")
        PlainParameterValueEditor.resize(518, 224)
        self.verticalLayout = QtWidgets.QVBoxLayout(PlainParameterValueEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(PlainParameterValueEditor)
        self.groupBox.setTitle("")
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.value_edit = QtWidgets.QLineEdit(self.groupBox)
        self.value_edit.setMaximumSize(QtCore.QSize(16777215, 23))
        self.value_edit.setObjectName("value_edit")
        self.gridLayout.addWidget(self.value_edit, 0, 1, 1, 1)
        self.radioButton_number_or_string = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_number_or_string.setObjectName("radioButton_number_or_string")
        self.gridLayout.addWidget(self.radioButton_number_or_string, 0, 0, 1, 1)
        self.radioButton_true = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_true.setObjectName("radioButton_true")
        self.gridLayout.addWidget(self.radioButton_true, 1, 0, 1, 1)
        self.radioButton_false = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_false.setObjectName("radioButton_false")
        self.gridLayout.addWidget(self.radioButton_false, 2, 0, 1, 1)
        self.radioButton_null = QtWidgets.QRadioButton(self.groupBox)
        self.radioButton_null.setObjectName("radioButton_null")
        self.gridLayout.addWidget(self.radioButton_null, 3, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(PlainParameterValueEditor)
        QtCore.QMetaObject.connectSlotsByName(PlainParameterValueEditor)

    def retranslateUi(self, PlainParameterValueEditor):
        PlainParameterValueEditor.setWindowTitle(QtWidgets.QApplication.translate("PlainParameterValueEditor", "Form", None, -1))
        self.radioButton_number_or_string.setText(QtWidgets.QApplication.translate("PlainParameterValueEditor", "number or string:", None, -1))
        self.radioButton_true.setText(QtWidgets.QApplication.translate("PlainParameterValueEditor", "true", None, -1))
        self.radioButton_false.setText(QtWidgets.QApplication.translate("PlainParameterValueEditor", "false", None, -1))
        self.radioButton_null.setText(QtWidgets.QApplication.translate("PlainParameterValueEditor", "null", None, -1))

