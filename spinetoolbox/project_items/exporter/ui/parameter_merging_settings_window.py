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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\parameter_merging_settings_window.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\parameter_merging_settings_window.ui' applies.
#
# Created: Wed Feb 19 16:58:30 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(646, 496)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.add_button = QtWidgets.QPushButton(Form)
        self.add_button.setObjectName("add_button")
        self.horizontalLayout.addWidget(self.add_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.setting_area = QtWidgets.QScrollArea(Form)
        self.setting_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setting_area.setWidgetResizable(True)
        self.setting_area.setObjectName("setting_area")
        self.setting_area_contents = QtWidgets.QWidget()
        self.setting_area_contents.setGeometry(QtCore.QRect(0, 0, 628, 418))
        self.setting_area_contents.setObjectName("setting_area_contents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.setting_area_contents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.settings_area_layout = QtWidgets.QVBoxLayout()
        self.settings_area_layout.setObjectName("settings_area_layout")
        self.verticalLayout_3.addLayout(self.settings_area_layout)
        self.setting_area.setWidget(self.setting_area_contents)
        self.verticalLayout.addWidget(self.setting_area)
        self.button_box = QtWidgets.QDialogButtonBox(Form)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.add_button.setText(QtWidgets.QApplication.translate("Form", "Add", None, -1))

