######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/time_series_editor.ui',
# licensing of '../spinetoolbox/ui/time_series_editor.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TimeSeriesEditor(object):
    def setupUi(self, TimeSeriesEditor):
        TimeSeriesEditor.setObjectName("TimeSeriesEditor")
        TimeSeriesEditor.setWindowModality(QtCore.Qt.WindowModal)
        TimeSeriesEditor.resize(563, 418)
        self.verticalLayout = QtWidgets.QVBoxLayout(TimeSeriesEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(TimeSeriesEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.time_series_table = QtWidgets.QTableView(self.splitter)
        self.time_series_table.setObjectName("time_series_table")
        self.verticalLayout.addWidget(self.splitter)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.close_button = QtWidgets.QPushButton(TimeSeriesEditor)
        self.close_button.setObjectName("close_button")
        self.horizontalLayout.addWidget(self.close_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(TimeSeriesEditor)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesEditor)

    def retranslateUi(self, TimeSeriesEditor):
        TimeSeriesEditor.setWindowTitle(QtWidgets.QApplication.translate("TimeSeriesEditor", "Edit time series", None, -1))
        self.close_button.setText(QtWidgets.QApplication.translate("TimeSeriesEditor", "Close", None, -1))

