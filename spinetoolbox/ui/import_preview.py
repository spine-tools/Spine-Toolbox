######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/import_preview.ui',
# licensing of '../spinetoolbox/ui/import_preview.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportPreview(object):
    def setupUi(self, ImportPreview):
        ImportPreview.setObjectName("ImportPreview")
        ImportPreview.resize(806, 632)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportPreview)
        self.verticalLayout.setObjectName("verticalLayout")
        self.main_splitter = QtWidgets.QSplitter(ImportPreview)
        self.main_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.main_splitter.setObjectName("main_splitter")
        self.sources_box = QtWidgets.QGroupBox(self.main_splitter)
        self.sources_box.setObjectName("sources_box")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.sources_box)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.source_splitter = QtWidgets.QSplitter(self.sources_box)
        self.source_splitter.setOrientation(QtCore.Qt.Vertical)
        self.source_splitter.setObjectName("source_splitter")
        self.top_source_splitter = QtWidgets.QSplitter(self.source_splitter)
        self.top_source_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.top_source_splitter.setObjectName("top_source_splitter")
        self.source_list = QtWidgets.QListWidget(self.top_source_splitter)
        self.source_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.source_list.setObjectName("source_list")
        self.source_data_table = QtWidgets.QTableView(self.source_splitter)
        self.source_data_table.setObjectName("source_data_table")
        self.verticalLayout_2.addWidget(self.source_splitter)
        self.mappings_box = QtWidgets.QGroupBox(self.main_splitter)
        self.mappings_box.setObjectName("mappings_box")
        self.verticalLayout.addWidget(self.main_splitter)

        self.retranslateUi(ImportPreview)
        QtCore.QMetaObject.connectSlotsByName(ImportPreview)

    def retranslateUi(self, ImportPreview):
        ImportPreview.setWindowTitle(QtWidgets.QApplication.translate("ImportPreview", "Form", None, -1))
        self.sources_box.setTitle(QtWidgets.QApplication.translate("ImportPreview", "Sources", None, -1))
        self.mappings_box.setTitle(QtWidgets.QApplication.translate("ImportPreview", "Mappings", None, -1))

