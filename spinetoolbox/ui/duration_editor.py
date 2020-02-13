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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\duration_editor.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\duration_editor.ui' applies.
#
# Created: Thu Feb 13 11:53:58 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_DurationEditor(object):
    def setupUi(self, DurationEditor):
        DurationEditor.setObjectName("DurationEditor")
        DurationEditor.resize(400, 300)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DurationEditor)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.layout = QtWidgets.QFormLayout()
        self.layout.setObjectName("layout")
        self.duration_edit_label = QtWidgets.QLabel(DurationEditor)
        self.duration_edit_label.setObjectName("duration_edit_label")
        self.layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.duration_edit_label)
        self.edit_layout = QtWidgets.QVBoxLayout()
        self.edit_layout.setObjectName("edit_layout")
        self.duration_edit = QtWidgets.QLineEdit(DurationEditor)
        self.duration_edit.setObjectName("duration_edit")
        self.edit_layout.addWidget(self.duration_edit)
        self.units_hint = QtWidgets.QLabel(DurationEditor)
        self.units_hint.setObjectName("units_hint")
        self.edit_layout.addWidget(self.units_hint)
        self.layout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.edit_layout)
        self.verticalLayout_2.addLayout(self.layout)

        self.retranslateUi(DurationEditor)
        QtCore.QMetaObject.connectSlotsByName(DurationEditor)

    def retranslateUi(self, DurationEditor):
        DurationEditor.setWindowTitle(QtWidgets.QApplication.translate("DurationEditor", "Form", None, -1))
        self.duration_edit_label.setText(QtWidgets.QApplication.translate("DurationEditor", "Duration", None, -1))
        self.units_hint.setText(QtWidgets.QApplication.translate("DurationEditor", "Units: s, m, h, D, M, Y", None, -1))

