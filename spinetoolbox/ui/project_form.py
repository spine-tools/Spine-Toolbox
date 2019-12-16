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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\project_form.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\project_form.ui' applies.
#
# Created: Wed Jan 15 14:45:03 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.resize(500, 400)
        Form.setMinimumSize(QtCore.QSize(500, 400))
        Form.setMaximumSize(QtCore.QSize(500, 400))
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(9, 9, 9, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lineEdit_project_name = QtWidgets.QLineEdit(Form)
        self.lineEdit_project_name.setObjectName("lineEdit_project_name")
        self.verticalLayout_2.addWidget(self.lineEdit_project_name)
        self.textEdit_description = QtWidgets.QTextEdit(Form)
        self.textEdit_description.setTabChangesFocus(True)
        self.textEdit_description.setAcceptRichText(False)
        self.textEdit_description.setObjectName("textEdit_description")
        self.verticalLayout_2.addWidget(self.textEdit_description)
        self.label_folder = QtWidgets.QLabel(Form)
        self.label_folder.setEnabled(False)
        self.label_folder.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.label_folder.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label_folder.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label_folder.setTextFormat(QtCore.Qt.PlainText)
        self.label_folder.setIndent(-1)
        self.label_folder.setObjectName("label_folder")
        self.verticalLayout_2.addWidget(self.label_folder)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(-1, 6, -1, 6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_ok = QtWidgets.QPushButton(Form)
        self.pushButton_ok.setDefault(True)
        self.pushButton_ok.setObjectName("pushButton_ok")
        self.horizontalLayout.addWidget(self.pushButton_ok)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton_cancel = QtWidgets.QPushButton(Form)
        self.pushButton_cancel.setDefault(True)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout.addWidget(self.pushButton_cancel)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.horizontalLayout_statusbar_placeholder = QtWidgets.QHBoxLayout()
        self.horizontalLayout_statusbar_placeholder.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_statusbar_placeholder.setObjectName("horizontalLayout_statusbar_placeholder")
        self.widget_invisible_dummy = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_invisible_dummy.sizePolicy().hasHeightForWidth())
        self.widget_invisible_dummy.setSizePolicy(sizePolicy)
        self.widget_invisible_dummy.setMinimumSize(QtCore.QSize(0, 20))
        self.widget_invisible_dummy.setMaximumSize(QtCore.QSize(0, 20))
        self.widget_invisible_dummy.setObjectName("widget_invisible_dummy")
        self.horizontalLayout_statusbar_placeholder.addWidget(self.widget_invisible_dummy)
        self.verticalLayout.addLayout(self.horizontalLayout_statusbar_placeholder)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.lineEdit_project_name, self.textEdit_description)
        Form.setTabOrder(self.textEdit_description, self.pushButton_ok)
        Form.setTabOrder(self.pushButton_ok, self.pushButton_cancel)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "New Project", None, -1))
        self.lineEdit_project_name.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Project name (Required)</p></body></html>", None, -1))
        self.lineEdit_project_name.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type project name here...", None, -1))
        self.textEdit_description.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Project description (Optional)</p></body></html>", None, -1))
        self.textEdit_description.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type project description here...", None, -1))
        self.label_folder.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Folder name that will be used with the given project name</p></body></html>", None, -1))
        self.label_folder.setText(QtWidgets.QApplication.translate("Form", "Project folder:", None, -1))
        self.pushButton_ok.setText(QtWidgets.QApplication.translate("Form", "Ok", None, -1))
        self.pushButton_cancel.setText(QtWidgets.QApplication.translate("Form", "Cancel", None, -1))

