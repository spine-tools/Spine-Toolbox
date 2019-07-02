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
        TimeSeriesVariableResolutionEditor.resize(570, 391)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(TimeSeriesVariableResolutionEditor)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(TimeSeriesVariableResolutionEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.length_edit = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.length_edit.setMinimum(2)
        self.length_edit.setMaximum(999999)
        self.length_edit.setObjectName("length_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.length_edit)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.ignore_year_check_box = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.ignore_year_check_box.setObjectName("ignore_year_check_box")
        self.horizontalLayout_2.addWidget(self.ignore_year_check_box)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.repeat_check_box = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.repeat_check_box.setObjectName("repeat_check_box")
        self.horizontalLayout_2.addWidget(self.repeat_check_box)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.time_series_table = QtWidgets.QTableView(self.verticalLayoutWidget)
        self.time_series_table.setObjectName("time_series_table")
        self.verticalLayout.addWidget(self.time_series_table)
        self.verticalLayout_2.addWidget(self.splitter)

        self.retranslateUi(TimeSeriesVariableResolutionEditor)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesVariableResolutionEditor)

    def retranslateUi(self, TimeSeriesVariableResolutionEditor):
        TimeSeriesVariableResolutionEditor.setWindowTitle(QtWidgets.QApplication.translate("TimeSeriesVariableResolutionEditor", "Form", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("TimeSeriesVariableResolutionEditor", "Length", None, -1))
        self.ignore_year_check_box.setText(QtWidgets.QApplication.translate("TimeSeriesVariableResolutionEditor", "Ignore year", None, -1))
        self.repeat_check_box.setText(QtWidgets.QApplication.translate("TimeSeriesVariableResolutionEditor", "Repeat", None, -1))

