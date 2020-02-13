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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\open_project_dialog.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\open_project_dialog.ui' applies.
#
# Created: Thu Feb 13 11:54:07 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 450)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.toolButton_root = QtWidgets.QToolButton(Dialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/slash.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_root.setIcon(icon)
        self.toolButton_root.setObjectName("toolButton_root")
        self.horizontalLayout.addWidget(self.toolButton_root)
        self.toolButton_home = QtWidgets.QToolButton(Dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/home.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_home.setIcon(icon1)
        self.toolButton_home.setObjectName("toolButton_home")
        self.horizontalLayout.addWidget(self.toolButton_home)
        self.toolButton_documents = QtWidgets.QToolButton(Dialog)
        self.toolButton_documents.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/book.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_documents.setIcon(icon2)
        self.toolButton_documents.setObjectName("toolButton_documents")
        self.horizontalLayout.addWidget(self.toolButton_documents)
        self.toolButton_desktop = QtWidgets.QToolButton(Dialog)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/desktop.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_desktop.setIcon(icon3)
        self.toolButton_desktop.setObjectName("toolButton_desktop")
        self.horizontalLayout.addWidget(self.toolButton_desktop)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.comboBox_current_path = QtWidgets.QComboBox(Dialog)
        self.comboBox_current_path.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.comboBox_current_path.setEditable(True)
        self.comboBox_current_path.setObjectName("comboBox_current_path")
        self.verticalLayout.addWidget(self.comboBox_current_path)
        self.treeView_file_system = QtWidgets.QTreeView(Dialog)
        self.treeView_file_system.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.treeView_file_system.setUniformRowHeights(True)
        self.treeView_file_system.setSortingEnabled(True)
        self.treeView_file_system.setAnimated(False)
        self.treeView_file_system.setObjectName("treeView_file_system")
        self.verticalLayout.addWidget(self.treeView_file_system)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.comboBox_current_path, self.treeView_file_system)
        Dialog.setTabOrder(self.treeView_file_system, self.toolButton_root)
        Dialog.setTabOrder(self.toolButton_root, self.toolButton_home)
        Dialog.setTabOrder(self.toolButton_home, self.toolButton_documents)
        Dialog.setTabOrder(self.toolButton_documents, self.toolButton_desktop)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Open project", None, -1))
        self.toolButton_root.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Root</p></body></html>", None, -1))
        self.toolButton_home.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Home</p></body></html>", None, -1))
        self.toolButton_documents.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Documents</p></body></html>", None, -1))
        self.toolButton_desktop.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Desktop</p></body></html>", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Dialog", "Select Spine Toolbox project directory", None, -1))

from spinetoolbox import resources_icons_rc
