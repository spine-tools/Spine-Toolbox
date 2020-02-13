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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\view\ui\view_properties.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\view\ui\view_properties.ui' applies.
#
# Created: Thu Feb 13 11:53:53 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(395, 396)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_view_name = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_view_name.sizePolicy().hasHeightForWidth())
        self.label_view_name.setSizePolicy(sizePolicy)
        self.label_view_name.setMinimumSize(QtCore.QSize(0, 20))
        self.label_view_name.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(50)
        font.setBold(False)
        self.label_view_name.setFont(font)
        self.label_view_name.setStyleSheet("background-color: #ecd8c6;")
        self.label_view_name.setFrameShape(QtWidgets.QFrame.Box)
        self.label_view_name.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label_view_name.setAlignment(QtCore.Qt.AlignCenter)
        self.label_view_name.setWordWrap(True)
        self.label_view_name.setObjectName("label_view_name")
        self.verticalLayout.addWidget(self.label_view_name)
        self.scrollArea_4 = QtWidgets.QScrollArea(Form)
        self.scrollArea_4.setWidgetResizable(True)
        self.scrollArea_4.setObjectName("scrollArea_4")
        self.scrollAreaWidgetContents_4 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_4.setGeometry(QtCore.QRect(0, 0, 393, 374))
        self.scrollAreaWidgetContents_4.setObjectName("scrollAreaWidgetContents_4")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_4)
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.treeView_view = ReferencesTreeView(self.scrollAreaWidgetContents_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.treeView_view.setFont(font)
        self.treeView_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView_view.setAcceptDrops(True)
        self.treeView_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeView_view.setTextElideMode(QtCore.Qt.ElideLeft)
        self.treeView_view.setRootIsDecorated(False)
        self.treeView_view.setObjectName("treeView_view")
        self.verticalLayout_18.addWidget(self.treeView_view)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem)
        self.pushButton_view_open_ds_view = QtWidgets.QPushButton(self.scrollAreaWidgetContents_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_view_open_ds_view.sizePolicy().hasHeightForWidth())
        self.pushButton_view_open_ds_view.setSizePolicy(sizePolicy)
        self.pushButton_view_open_ds_view.setMinimumSize(QtCore.QSize(75, 23))
        self.pushButton_view_open_ds_view.setMaximumSize(QtCore.QSize(16777215, 23))
        self.pushButton_view_open_ds_view.setObjectName("pushButton_view_open_ds_view")
        self.horizontalLayout_8.addWidget(self.pushButton_view_open_ds_view)
        self.verticalLayout_18.addLayout(self.horizontalLayout_8)
        self.line_5 = QtWidgets.QFrame(self.scrollAreaWidgetContents_4)
        self.line_5.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.verticalLayout_18.addWidget(self.line_5)
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_16.addItem(spacerItem1)
        self.toolButton_view_open_dir = QtWidgets.QToolButton(self.scrollAreaWidgetContents_4)
        self.toolButton_view_open_dir.setMinimumSize(QtCore.QSize(22, 22))
        self.toolButton_view_open_dir.setMaximumSize(QtCore.QSize(22, 22))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/menu_icons/folder-open-solid.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_view_open_dir.setIcon(icon)
        self.toolButton_view_open_dir.setObjectName("toolButton_view_open_dir")
        self.horizontalLayout_16.addWidget(self.toolButton_view_open_dir)
        self.verticalLayout_18.addLayout(self.horizontalLayout_16)
        self.scrollArea_4.setWidget(self.scrollAreaWidgetContents_4)
        self.verticalLayout.addWidget(self.scrollArea_4)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.label_view_name.setText(QtWidgets.QApplication.translate("Form", "Name", None, -1))
        self.pushButton_view_open_ds_view.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open Data store view for selected db references</p></body></html>", None, -1))
        self.pushButton_view_open_ds_view.setText(QtWidgets.QApplication.translate("Form", "Open view", None, -1))
        self.toolButton_view_open_dir.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open this View\'s project directory in file browser</p></body></html>", None, -1))

from spinetoolbox.widgets.custom_qtreeview import ReferencesTreeView
from spinetoolbox import resources_icons_rc
