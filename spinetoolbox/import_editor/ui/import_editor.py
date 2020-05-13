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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\import_editor\ui\import_editor.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\import_editor\ui\import_editor.ui' applies.
#
# Created: Wed May 13 09:22:01 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportEditor(object):
    def setupUi(self, ImportEditor):
        ImportEditor.setObjectName("ImportEditor")
        ImportEditor.resize(806, 632)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.main_splitter = QtWidgets.QSplitter(ImportEditor)
        self.main_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.main_splitter.setObjectName("main_splitter")
        self.sources_box = QtWidgets.QGroupBox(self.main_splitter)
        self.sources_box.setObjectName("sources_box")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.sources_box)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.sources_splitter = QtWidgets.QSplitter(self.sources_box)
        self.sources_splitter.setOrientation(QtCore.Qt.Vertical)
        self.sources_splitter.setObjectName("sources_splitter")
        self.top_source_splitter = QtWidgets.QSplitter(self.sources_splitter)
        self.top_source_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.top_source_splitter.setObjectName("top_source_splitter")
        self.source_list = QtWidgets.QListWidget(self.top_source_splitter)
        self.source_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.source_list.setObjectName("source_list")
        self.source_preview_widget_stack = QtWidgets.QStackedWidget(self.sources_splitter)
        self.source_preview_widget_stack.setObjectName("source_preview_widget_stack")
        self.table_page = QtWidgets.QWidget()
        self.table_page.setObjectName("table_page")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.table_page)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.source_data_table = TableViewWithButtonHeader(self.table_page)
        self.source_data_table.setObjectName("source_data_table")
        self.verticalLayout_2.addWidget(self.source_data_table)
        self.source_preview_widget_stack.addWidget(self.table_page)
        self.loading_page = QtWidgets.QWidget()
        self.loading_page.setObjectName("loading_page")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.loading_page)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.waiting_label = QtWidgets.QLabel(self.loading_page)
        self.waiting_label.setObjectName("waiting_label")
        self.horizontalLayout.addWidget(self.waiting_label)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.source_preview_widget_stack.addWidget(self.loading_page)
        self.verticalLayout_4.addWidget(self.sources_splitter)
        self.mappings_box = QtWidgets.QGroupBox(self.main_splitter)
        self.mappings_box.setObjectName("mappings_box")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.mappings_box)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.mapper = ImportMappings(self.mappings_box)
        self.mapper.setObjectName("mapper")
        self.verticalLayout_5.addWidget(self.mapper)
        self.verticalLayout.addWidget(self.main_splitter)

        self.retranslateUi(ImportEditor)
        self.source_preview_widget_stack.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ImportEditor)

    def retranslateUi(self, ImportEditor):
        ImportEditor.setWindowTitle(QtWidgets.QApplication.translate("ImportEditor", "Form", None, -1))
        self.sources_box.setTitle(QtWidgets.QApplication.translate("ImportEditor", "Sources", None, -1))
        self.waiting_label.setText(QtWidgets.QApplication.translate("ImportEditor", "Loading preview...", None, -1))
        self.mappings_box.setTitle(QtWidgets.QApplication.translate("ImportEditor", "Mappings", None, -1))

from spinetoolbox.import_editor.widgets.import_mappings import ImportMappings
from spinetoolbox.widgets.table_view_with_button_header import TableViewWithButtonHeader
