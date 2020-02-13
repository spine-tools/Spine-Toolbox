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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\parameter_index_settings_window.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\parameter_index_settings_window.ui' applies.
#
# Created: Thu Feb 13 11:53:50 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.WindowModal)
        Form.resize(680, 472)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_stack = QtWidgets.QStackedWidget(Form)
        self.widget_stack.setObjectName("widget_stack")
        self.settings_page = QtWidgets.QWidget()
        self.settings_page.setObjectName("settings_page")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.settings_page)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.settings_area = QtWidgets.QScrollArea(self.settings_page)
        self.settings_area.setWidgetResizable(True)
        self.settings_area.setObjectName("settings_area")
        self.settings_area_contents = QtWidgets.QWidget()
        self.settings_area_contents.setGeometry(QtCore.QRect(0, 0, 642, 405))
        self.settings_area_contents.setObjectName("settings_area_contents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.settings_area_contents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.settings_area_layout = QtWidgets.QVBoxLayout()
        self.settings_area_layout.setObjectName("settings_area_layout")
        self.verticalLayout_3.addLayout(self.settings_area_layout)
        self.settings_area.setWidget(self.settings_area_contents)
        self.verticalLayout_2.addWidget(self.settings_area)
        self.widget_stack.addWidget(self.settings_page)
        self.empty_message_page = QtWidgets.QWidget()
        self.empty_message_page.setObjectName("empty_message_page")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.empty_message_page)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(self.empty_message_page)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.widget_stack.addWidget(self.empty_message_page)
        self.verticalLayout.addWidget(self.widget_stack)
        self.button_box = QtWidgets.QDialogButtonBox(Form)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(Form)
        self.widget_stack.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Gdx Parameter Indexing Settings", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "No indexed parameters found in this database.", None, -1))

