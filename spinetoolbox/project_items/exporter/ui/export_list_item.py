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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\export_list_item.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\export_list_item.ui' applies.
#
# Created: Thu Feb 13 11:53:47 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 117)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.url_field = QtWidgets.QLineEdit(self.frame)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.url_field.setFont(font)
        self.url_field.setFrame(False)
        self.url_field.setReadOnly(True)
        self.url_field.setObjectName("url_field")
        self.verticalLayout.addWidget(self.url_field)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.file_name_label = QtWidgets.QLabel(self.frame)
        self.file_name_label.setObjectName("file_name_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.file_name_label)
        self.out_file_name_edit = QtWidgets.QLineEdit(self.frame)
        self.out_file_name_edit.setObjectName("out_file_name_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.out_file_name_edit)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.notification_label = QtWidgets.QLabel(self.frame)
        self.notification_label.setText("")
        self.notification_label.setTextFormat(QtCore.Qt.RichText)
        self.notification_label.setObjectName("notification_label")
        self.horizontalLayout.addWidget(self.notification_label)
        self.settings_button = QtWidgets.QPushButton(self.frame)
        self.settings_button.setObjectName("settings_button")
        self.horizontalLayout.addWidget(self.settings_button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.file_name_label.setText(QtWidgets.QApplication.translate("Form", "Filename:", None, -1))
        self.out_file_name_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type output file name here...", None, -1))
        self.settings_button.setText(QtWidgets.QApplication.translate("Form", "Settings...", None, -1))

