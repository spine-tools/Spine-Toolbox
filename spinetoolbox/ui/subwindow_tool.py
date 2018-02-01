#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/subwindow_tool.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setEnabled(True)
        Form.resize(208, 157)
        Form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_name = QtWidgets.QLabel(Form)
        self.label_name.setEnabled(True)
        self.label_name.setWordWrap(True)
        self.label_name.setObjectName("label_name")
        self.verticalLayout.addWidget(self.label_name)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_tool = QtWidgets.QLabel(Form)
        self.label_tool.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.label_tool.setObjectName("label_tool")
        self.horizontalLayout_2.addWidget(self.label_tool)
        self.lineEdit_tool = QtWidgets.QLineEdit(Form)
        self.lineEdit_tool.setEnabled(False)
        self.lineEdit_tool.setCursor(QtCore.Qt.ArrowCursor)
        self.lineEdit_tool.setFocusPolicy(QtCore.Qt.NoFocus)
        self.lineEdit_tool.setReadOnly(True)
        self.lineEdit_tool.setClearButtonEnabled(False)
        self.lineEdit_tool.setObjectName("lineEdit_tool")
        self.horizontalLayout_2.addWidget(self.lineEdit_tool)
        self.pushButton_x = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_x.sizePolicy().hasHeightForWidth())
        self.pushButton_x.setSizePolicy(sizePolicy)
        self.pushButton_x.setMinimumSize(QtCore.QSize(20, 20))
        self.pushButton_x.setMaximumSize(QtCore.QSize(20, 20))
        self.pushButton_x.setObjectName("pushButton_x")
        self.horizontalLayout_2.addWidget(self.pushButton_x)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_args = QtWidgets.QLabel(Form)
        self.label_args.setObjectName("label_args")
        self.horizontalLayout_3.addWidget(self.label_args)
        self.lineEdit_tool_args = QtWidgets.QLineEdit(Form)
        self.lineEdit_tool_args.setEnabled(False)
        self.lineEdit_tool_args.setCursor(QtCore.Qt.ArrowCursor)
        self.lineEdit_tool_args.setFocusPolicy(QtCore.Qt.NoFocus)
        self.lineEdit_tool_args.setReadOnly(True)
        self.lineEdit_tool_args.setObjectName("lineEdit_tool_args")
        self.horizontalLayout_3.addWidget(self.lineEdit_tool_args)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_details = QtWidgets.QPushButton(Form)
        self.pushButton_details.setEnabled(True)
        self.pushButton_details.setMaximumSize(QtCore.QSize(75, 23))
        self.pushButton_details.setAutoFillBackground(False)
        self.pushButton_details.setObjectName("pushButton_details")
        self.horizontalLayout.addWidget(self.pushButton_details)
        self.pushButton_execute = QtWidgets.QPushButton(Form)
        self.pushButton_execute.setMaximumSize(QtCore.QSize(75, 23))
        self.pushButton_execute.setObjectName("pushButton_execute")
        self.horizontalLayout.addWidget(self.pushButton_execute)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.lineEdit_tool_args, self.pushButton_details)
        Form.setTabOrder(self.pushButton_details, self.pushButton_execute)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Tool", None, -1))
        self.label_name.setText(QtWidgets.QApplication.translate("Form", "Name", None, -1))
        self.label_tool.setText(QtWidgets.QApplication.translate("Form", "Tool", None, -1))
        self.pushButton_x.setText(QtWidgets.QApplication.translate("Form", "X", None, -1))
        self.label_args.setText(QtWidgets.QApplication.translate("Form", "Args", None, -1))
        self.lineEdit_tool_args.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Tool command line arguments. Edit tool definition file to change these.</p></body></html>", None, -1))
        self.pushButton_details.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Show selected Tool details</p></body></html>", None, -1))
        self.pushButton_details.setText(QtWidgets.QApplication.translate("Form", "Details", None, -1))
        self.pushButton_execute.setText(QtWidgets.QApplication.translate("Form", "Execute", None, -1))

