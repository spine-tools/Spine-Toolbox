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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_mapping.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_mapping.ui' applies.
#
# Created: Thu Feb 13 11:54:00 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportMapping(object):
    def setupUi(self, ImportMapping):
        ImportMapping.setObjectName("ImportMapping")
        ImportMapping.resize(367, 536)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(ImportMapping)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitter = QtWidgets.QSplitter(ImportMapping)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.top_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setObjectName("top_layout")
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setObjectName("button_layout")
        self.new_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.new_button.setObjectName("new_button")
        self.button_layout.addWidget(self.new_button)
        self.remove_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.remove_button.setObjectName("remove_button")
        self.button_layout.addWidget(self.remove_button)
        self.top_layout.addLayout(self.button_layout)
        self.list_view = QtWidgets.QListView(self.verticalLayoutWidget)
        self.list_view.setObjectName("list_view")
        self.top_layout.addWidget(self.list_view)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.bottom_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setObjectName("bottom_layout")
        self.table_view = QtWidgets.QTableView(self.verticalLayoutWidget_2)
        self.table_view.setObjectName("table_view")
        self.bottom_layout.addWidget(self.table_view)
        self.verticalLayout_3.addWidget(self.splitter)

        self.retranslateUi(ImportMapping)
        QtCore.QMetaObject.connectSlotsByName(ImportMapping)

    def retranslateUi(self, ImportMapping):
        ImportMapping.setWindowTitle(QtWidgets.QApplication.translate("ImportMapping", "Form", None, -1))
        self.new_button.setText(QtWidgets.QApplication.translate("ImportMapping", "New", None, -1))
        self.remove_button.setText(QtWidgets.QApplication.translate("ImportMapping", "Remove", None, -1))

