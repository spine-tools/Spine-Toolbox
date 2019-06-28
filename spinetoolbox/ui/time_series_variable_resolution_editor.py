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

# Form implementation generated from reading ui file '../spinetoolbox/ui/time_series_variable_resolution_editor.ui',
# licensing of '../spinetoolbox/ui/time_series_variable_resolution_editor.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TimeSeriesVariableResolutionEditor(object):
    def setupUi(self, TimeSeriesVariableResolutionEditor):
        TimeSeriesVariableResolutionEditor.setObjectName("TimeSeriesVariableResolutionEditor")
        TimeSeriesVariableResolutionEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(TimeSeriesVariableResolutionEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(TimeSeriesVariableResolutionEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.time_series_table = QtWidgets.QTableView(self.splitter)
        self.time_series_table.setObjectName("time_series_table")
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(TimeSeriesVariableResolutionEditor)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesVariableResolutionEditor)

    def retranslateUi(self, TimeSeriesVariableResolutionEditor):
        TimeSeriesVariableResolutionEditor.setWindowTitle(QtWidgets.QApplication.translate("TimeSeriesVariableResolutionEditor", "Form", None, -1))

