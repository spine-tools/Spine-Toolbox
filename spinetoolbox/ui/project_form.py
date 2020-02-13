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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\project_form.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\project_form.ui' applies.
#
# Created: Thu Feb 13 11:54:10 2020
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
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit_project_dir = QtWidgets.QLineEdit(Form)
        self.lineEdit_project_dir.setCursor(QtCore.Qt.ArrowCursor)
        self.lineEdit_project_dir.setReadOnly(True)
        self.lineEdit_project_dir.setClearButtonEnabled(True)
        self.lineEdit_project_dir.setObjectName("lineEdit_project_dir")
        self.horizontalLayout_2.addWidget(self.lineEdit_project_dir)
        self.toolButton_select_project_dir = QtWidgets.QToolButton(Form)
        self.toolButton_select_project_dir.setMaximumSize(QtCore.QSize(22, 22))
        self.toolButton_select_project_dir.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/menu_icons/folder-open-solid.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_select_project_dir.setIcon(icon)
        self.toolButton_select_project_dir.setObjectName("toolButton_select_project_dir")
        self.horizontalLayout_2.addWidget(self.toolButton_select_project_dir)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.lineEdit_project_name = QtWidgets.QLineEdit(Form)
        self.lineEdit_project_name.setClearButtonEnabled(True)
        self.lineEdit_project_name.setObjectName("lineEdit_project_name")
        self.verticalLayout.addWidget(self.lineEdit_project_name)
        self.textEdit_description = QtWidgets.QTextEdit(Form)
        self.textEdit_description.setTabChangesFocus(True)
        self.textEdit_description.setAcceptRichText(False)
        self.textEdit_description.setObjectName("textEdit_description")
        self.verticalLayout.addWidget(self.textEdit_description)
        self.label = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
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
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.toolButton_select_project_dir, self.lineEdit_project_name)
        Form.setTabOrder(self.lineEdit_project_name, self.textEdit_description)
        Form.setTabOrder(self.textEdit_description, self.pushButton_ok)
        Form.setTabOrder(self.pushButton_ok, self.pushButton_cancel)
        Form.setTabOrder(self.pushButton_cancel, self.lineEdit_project_dir)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "New Project", None, -1))
        self.lineEdit_project_dir.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Project directory</p></body></html>", None, -1))
        self.lineEdit_project_dir.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Select project directory...", None, -1))
        self.toolButton_select_project_dir.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Click here to select a directory for the new project</p></body></html>", None, -1))
        self.lineEdit_project_name.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Project name (Required)</p></body></html>", None, -1))
        self.lineEdit_project_name.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type project name here...", None, -1))
        self.textEdit_description.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Project description (Optional)</p></body></html>", None, -1))
        self.textEdit_description.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type project description here...", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "1. Select project directory", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("Form", "2. Type project name and description (optional)", None, -1))
        self.pushButton_ok.setText(QtWidgets.QApplication.translate("Form", "Ok", None, -1))
        self.pushButton_cancel.setText(QtWidgets.QApplication.translate("Form", "Cancel", None, -1))

from spinetoolbox import resources_icons_rc
