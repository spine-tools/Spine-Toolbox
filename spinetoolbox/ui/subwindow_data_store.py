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

# Form implementation generated from reading ui file '../spinetoolbox/ui/subwindow_data_store.ui',
# licensing of '../spinetoolbox/ui/subwindow_data_store.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.NonModal)
        Form.resize(200, 304)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(200, 275))
        Form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        Form.setToolTip("")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setSpacing(4)
        self.verticalLayout_3.setContentsMargins(4, -1, 4, 4)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_name = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_name.sizePolicy().hasHeightForWidth())
        self.label_name.setSizePolicy(sizePolicy)
        self.label_name.setMinimumSize(QtCore.QSize(0, 18))
        self.label_name.setMaximumSize(QtCore.QSize(16777215, 18))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.label_name.setFont(font)
        self.label_name.setStyleSheet("background-color: rgb(0,255, 255);\n"
"color: rgb(255, 255, 255);")
        self.label_name.setAlignment(QtCore.Qt.AlignCenter)
        self.label_name.setWordWrap(True)
        self.label_name.setObjectName("label_name")
        self.verticalLayout_3.addWidget(self.label_name)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeView_references = ReferencesTreeView(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.treeView_references.setFont(font)
        self.treeView_references.setAcceptDrops(True)
        self.treeView_references.setRootIsDecorated(False)
        self.treeView_references.setObjectName("treeView_references")
        self.treeView_references.header().setMinimumSectionSize(27)
        self.verticalLayout.addWidget(self.treeView_references)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.toolButton_plus = QtWidgets.QToolButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_plus.sizePolicy().hasHeightForWidth())
        self.toolButton_plus.setSizePolicy(sizePolicy)
        self.toolButton_plus.setMinimumSize(QtCore.QSize(20, 20))
        self.toolButton_plus.setMaximumSize(QtCore.QSize(20, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.toolButton_plus.setFont(font)
        self.toolButton_plus.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_plus.setIcon(icon)
        self.toolButton_plus.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.toolButton_plus.setObjectName("toolButton_plus")
        self.horizontalLayout_2.addWidget(self.toolButton_plus)
        self.toolButton_minus = QtWidgets.QToolButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_minus.sizePolicy().hasHeightForWidth())
        self.toolButton_minus.setSizePolicy(sizePolicy)
        self.toolButton_minus.setMinimumSize(QtCore.QSize(20, 20))
        self.toolButton_minus.setMaximumSize(QtCore.QSize(20, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.toolButton_minus.setFont(font)
        self.toolButton_minus.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_minus.setIcon(icon1)
        self.toolButton_minus.setObjectName("toolButton_minus")
        self.horizontalLayout_2.addWidget(self.toolButton_minus)
        self.toolButton_add = QtWidgets.QToolButton(Form)
        self.toolButton_add.setMaximumSize(QtCore.QSize(20, 20))
        self.toolButton_add.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/import.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_add.setIcon(icon2)
        self.toolButton_add.setObjectName("toolButton_add")
        self.horizontalLayout_2.addWidget(self.toolButton_add)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.toolButton_Spine = QtWidgets.QToolButton(Form)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/Spine_db_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_Spine.setIcon(icon3)
        self.toolButton_Spine.setObjectName("toolButton_Spine")
        self.horizontalLayout_2.addWidget(self.toolButton_Spine)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.treeView_data = DataTreeView(Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.treeView_data.setFont(font)
        self.treeView_data.setAcceptDrops(True)
        self.treeView_data.setRootIsDecorated(False)
        self.treeView_data.setObjectName("treeView_data")
        self.treeView_data.header().setMinimumSectionSize(27)
        self.verticalLayout_2.addWidget(self.treeView_data)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton_open = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_open.sizePolicy().hasHeightForWidth())
        self.pushButton_open.setSizePolicy(sizePolicy)
        self.pushButton_open.setMaximumSize(QtCore.QSize(120, 23))
        self.pushButton_open.setObjectName("pushButton_open")
        self.horizontalLayout.addWidget(self.pushButton_open)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_4.addLayout(self.verticalLayout_3)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.toolButton_plus, self.toolButton_minus)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Data Store", None, -1))
        self.label_name.setText(QtWidgets.QApplication.translate("Form", "Name", None, -1))
        self.toolButton_plus.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Add references</p></body></html>", None, -1))
        self.toolButton_minus.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Remove selected references or all if nothing is selected</p></body></html>", None, -1))
        self.toolButton_add.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Add references to project.  Copies selected references into SQLite files in Data store\'s directory.</p></body></html>", None, -1))
        self.toolButton_Spine.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Create fresh (empty) Spine database into an SQLite file in Data store\'s directory.</p></body></html>", None, -1))
        self.toolButton_Spine.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.treeView_data.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Drag-and-drop files here, they will be copied to the data directory.</p></body></html>", None, -1))
        self.pushButton_open.setToolTip(QtWidgets.QApplication.translate("Form", "<html><head/><body><p>Open Data Store directory in file browser</p></body></html>", None, -1))
        self.pushButton_open.setText(QtWidgets.QApplication.translate("Form", "Open directory...", None, -1))

from widgets.custom_qtreeview import ReferencesTreeView, DataTreeView
import resources_icons_rc
