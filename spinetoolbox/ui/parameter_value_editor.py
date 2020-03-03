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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\parameter_value_editor.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\parameter_value_editor.ui' applies.
#
# Created: Tue Feb 11 13:39:41 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ParameterValueEditor(object):
    def setupUi(self, ParameterValueEditor):
        ParameterValueEditor.setObjectName("ParameterValueEditor")
        ParameterValueEditor.resize(700, 400)
        self.verticalLayout = QtWidgets.QVBoxLayout(ParameterValueEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.parameter_type_selector_layout = QtWidgets.QHBoxLayout()
        self.parameter_type_selector_layout.setObjectName("parameter_type_selector_layout")
        self.parameter_type_selector_label = QtWidgets.QLabel(ParameterValueEditor)
        self.parameter_type_selector_label.setObjectName("parameter_type_selector_label")
        self.parameter_type_selector_layout.addWidget(self.parameter_type_selector_label)
        self.parameter_type_selector = QtWidgets.QComboBox(ParameterValueEditor)
        self.parameter_type_selector.setObjectName("parameter_type_selector")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector.addItem("")
        self.parameter_type_selector_layout.addWidget(self.parameter_type_selector)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.parameter_type_selector_layout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.parameter_type_selector_layout)
        self.editor_stack = QtWidgets.QStackedWidget(ParameterValueEditor)
        self.editor_stack.setObjectName("editor_stack")
        self.verticalLayout.addWidget(self.editor_stack)
        self.button_box = QtWidgets.QDialogButtonBox(ParameterValueEditor)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(ParameterValueEditor)
        self.editor_stack.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(ParameterValueEditor)

    def retranslateUi(self, ParameterValueEditor):
        ParameterValueEditor.setWindowTitle(QtWidgets.QApplication.translate("ParameterValueEditor", "Edit parameter value", None, -1))
        self.parameter_type_selector_label.setText(QtWidgets.QApplication.translate("ParameterValueEditor", "Parameter type", None, -1))
        self.parameter_type_selector.setItemText(0, QtWidgets.QApplication.translate("ParameterValueEditor", "Plain value", None, -1))
        self.parameter_type_selector.setItemText(1, QtWidgets.QApplication.translate("ParameterValueEditor", "Map", None, -1))
        self.parameter_type_selector.setItemText(2, QtWidgets.QApplication.translate("ParameterValueEditor", "Time series - fixed resolution", None, -1))
        self.parameter_type_selector.setItemText(3, QtWidgets.QApplication.translate("ParameterValueEditor", "Time series - variable resolution", None, -1))
        self.parameter_type_selector.setItemText(4, QtWidgets.QApplication.translate("ParameterValueEditor", "Time pattern", None, -1))
        self.parameter_type_selector.setItemText(5, QtWidgets.QApplication.translate("ParameterValueEditor", "Datetime", None, -1))
        self.parameter_type_selector.setItemText(6, QtWidgets.QApplication.translate("ParameterValueEditor", "Duration", None, -1))

