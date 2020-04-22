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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\exporter_properties.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\exporter_properties.ui' applies.
#
# Created: Thu Feb 13 11:53:46 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(294, 370)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.item_name_label = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.item_name_label.sizePolicy().hasHeightForWidth())
        self.item_name_label.setSizePolicy(sizePolicy)
        self.item_name_label.setMinimumSize(QtCore.QSize(0, 20))
        self.item_name_label.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(50)
        font.setBold(False)
        self.item_name_label.setFont(font)
        self.item_name_label.setStyleSheet("background-color: #ecd8c6;")
        self.item_name_label.setFrameShape(QtWidgets.QFrame.Box)
        self.item_name_label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.item_name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.item_name_label.setWordWrap(True)
        self.item_name_label.setObjectName("item_name_label")
        self.verticalLayout.addWidget(self.item_name_label)
        self.scrollArea_6 = QtWidgets.QScrollArea(Form)
        self.scrollArea_6.setWidgetResizable(True)
        self.scrollArea_6.setObjectName("scrollArea_6")
        self.scrollAreaWidgetContents_5 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 292, 348))
        self.scrollAreaWidgetContents_5.setObjectName("scrollAreaWidgetContents_5")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_5)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.databases_list_layout = QtWidgets.QVBoxLayout()
        self.databases_list_layout.setObjectName("databases_list_layout")
        self.verticalLayout_21.addLayout(self.databases_list_layout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_21.addItem(spacerItem)
        self.line_6 = QtWidgets.QFrame(self.scrollAreaWidgetContents_5)
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.verticalLayout_21.addWidget(self.line_6)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem1)
        self.open_directory_button = QtWidgets.QToolButton(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.open_directory_button.sizePolicy().hasHeightForWidth())
        self.open_directory_button.setSizePolicy(sizePolicy)
        self.open_directory_button.setMinimumSize(QtCore.QSize(22, 22))
        self.open_directory_button.setMaximumSize(QtCore.QSize(22, 22))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/menu_icons/folder-open-solid.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.open_directory_button.setIcon(icon)
        self.open_directory_button.setObjectName("open_directory_button")
        self.horizontalLayout_13.addWidget(self.open_directory_button)
        self.verticalLayout_21.addLayout(self.horizontalLayout_13)
        self.scrollArea_6.setWidget(self.scrollAreaWidgetContents_5)
        self.verticalLayout.addWidget(self.scrollArea_6)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.item_name_label.setText(QtWidgets.QApplication.translate("Form", "Name", None, -1))
        self.open_directory_button.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open this Exporter\'s project directory in file browser</p></body></html>", None, -1))

from spinetoolbox import resources_icons_rc
