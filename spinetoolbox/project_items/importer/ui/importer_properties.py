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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\importer\ui\importer_properties.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\importer\ui\importer_properties.ui' applies.
#
# Created: Thu Feb 13 11:53:52 2020
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
        self.label_name = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_name.sizePolicy().hasHeightForWidth())
        self.label_name.setSizePolicy(sizePolicy)
        self.label_name.setMinimumSize(QtCore.QSize(0, 20))
        self.label_name.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(50)
        font.setBold(False)
        self.label_name.setFont(font)
        self.label_name.setStyleSheet("background-color: #ecd8c6;")
        self.label_name.setFrameShape(QtWidgets.QFrame.Box)
        self.label_name.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label_name.setAlignment(QtCore.Qt.AlignCenter)
        self.label_name.setWordWrap(True)
        self.label_name.setObjectName("label_name")
        self.verticalLayout.addWidget(self.label_name)
        self.scrollArea_6 = QtWidgets.QScrollArea(Form)
        self.scrollArea_6.setWidgetResizable(True)
        self.scrollArea_6.setObjectName("scrollArea_6")
        self.scrollAreaWidgetContents_5 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 292, 348))
        self.scrollAreaWidgetContents_5.setObjectName("scrollAreaWidgetContents_5")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_5)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.treeView_files = QtWidgets.QTreeView(self.scrollAreaWidgetContents_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.treeView_files.setFont(font)
        self.treeView_files.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView_files.setTextElideMode(QtCore.Qt.ElideLeft)
        self.treeView_files.setIndentation(5)
        self.treeView_files.setRootIsDecorated(False)
        self.treeView_files.setUniformRowHeights(True)
        self.treeView_files.setObjectName("treeView_files")
        self.verticalLayout_21.addWidget(self.treeView_files)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_21.addItem(spacerItem)
        self.cancel_on_error_checkBox = QtWidgets.QCheckBox(self.scrollAreaWidgetContents_5)
        self.cancel_on_error_checkBox.setChecked(True)
        self.cancel_on_error_checkBox.setObjectName("cancel_on_error_checkBox")
        self.verticalLayout_21.addWidget(self.cancel_on_error_checkBox)
        self.pushButton_import_editor = QtWidgets.QPushButton(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_import_editor.sizePolicy().hasHeightForWidth())
        self.pushButton_import_editor.setSizePolicy(sizePolicy)
        self.pushButton_import_editor.setMinimumSize(QtCore.QSize(75, 23))
        self.pushButton_import_editor.setMaximumSize(QtCore.QSize(16777215, 23))
        self.pushButton_import_editor.setObjectName("pushButton_import_editor")
        self.verticalLayout_21.addWidget(self.pushButton_import_editor)
        self.line_6 = QtWidgets.QFrame(self.scrollAreaWidgetContents_5)
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.verticalLayout_21.addWidget(self.line_6)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem1)
        self.toolButton_open_dir = QtWidgets.QToolButton(self.scrollAreaWidgetContents_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_open_dir.sizePolicy().hasHeightForWidth())
        self.toolButton_open_dir.setSizePolicy(sizePolicy)
        self.toolButton_open_dir.setMinimumSize(QtCore.QSize(22, 22))
        self.toolButton_open_dir.setMaximumSize(QtCore.QSize(22, 22))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/menu_icons/folder-open-solid.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_open_dir.setIcon(icon)
        self.toolButton_open_dir.setObjectName("toolButton_open_dir")
        self.horizontalLayout_13.addWidget(self.toolButton_open_dir)
        self.verticalLayout_21.addLayout(self.horizontalLayout_13)
        self.scrollArea_6.setWidget(self.scrollAreaWidgetContents_5)
        self.verticalLayout.addWidget(self.scrollArea_6)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.label_name.setText(QtWidgets.QApplication.translate("Form", "Name", None, -1))
        self.cancel_on_error_checkBox.setToolTip(QtWidgets.QApplication.translate("Form", "If there are any errors when trying to import data cancel the whole import.", None, -1))
        self.cancel_on_error_checkBox.setText(QtWidgets.QApplication.translate("Form", "Cancel import on error", None, -1))
        self.pushButton_import_editor.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open selected file in Import Editor</p></body></html>", None, -1))
        self.pushButton_import_editor.setText(QtWidgets.QApplication.translate("Form", "Import Editor...", None, -1))
        self.toolButton_open_dir.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open this Importer\'s project directory in file browser</p></body></html>", None, -1))

from spinetoolbox import resources_icons_rc
