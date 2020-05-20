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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\import_editor\ui\import_mappings.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\import_editor\ui\import_mappings.ui' applies.
#
# Created: Thu May 14 14:19:52 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportMappings(object):
    def setupUi(self, ImportMappings):
        ImportMappings.setObjectName("ImportMappings")
        ImportMappings.resize(367, 536)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(ImportMappings)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.mapping_splitter = QtWidgets.QSplitter(ImportMappings)
        self.mapping_splitter.setOrientation(QtCore.Qt.Vertical)
        self.mapping_splitter.setObjectName("mapping_splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.mapping_splitter)
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
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.mapping_splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.bottom_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setObjectName("bottom_layout")
        self.options = ImportMappingOptions(self.verticalLayoutWidget_2)
        self.options.setObjectName("options")
        self.bottom_layout.addWidget(self.options)
        self.table_view = QtWidgets.QTableView(self.verticalLayoutWidget_2)
        self.table_view.setObjectName("table_view")
        self.bottom_layout.addWidget(self.table_view)
        self.verticalLayout_3.addWidget(self.mapping_splitter)

        self.retranslateUi(ImportMappings)
        QtCore.QMetaObject.connectSlotsByName(ImportMappings)

    def retranslateUi(self, ImportMappings):
        ImportMappings.setWindowTitle(QtWidgets.QApplication.translate("ImportMappings", "Form", None, -1))
        self.new_button.setText(QtWidgets.QApplication.translate("ImportMappings", "New", None, -1))
        self.remove_button.setText(QtWidgets.QApplication.translate("ImportMappings", "Remove", None, -1))

from spinetoolbox.import_editor.widgets.import_mapping_options import ImportMappingOptions
