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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\time_series_fixed_resolution_editor.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\time_series_fixed_resolution_editor.ui' applies.
#
# Created: Thu Feb 13 11:54:14 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TimeSeriesFixedResolutionEditor(object):
    def setupUi(self, TimeSeriesFixedResolutionEditor):
        TimeSeriesFixedResolutionEditor.setObjectName("TimeSeriesFixedResolutionEditor")
        TimeSeriesFixedResolutionEditor.resize(296, 341)
        self.verticalLayout = QtWidgets.QVBoxLayout(TimeSeriesFixedResolutionEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(TimeSeriesFixedResolutionEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.left_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setObjectName("left_layout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.start_time_label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.start_time_label.setObjectName("start_time_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.start_time_label)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.start_time_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.start_time_edit.setObjectName("start_time_edit")
        self.horizontalLayout.addWidget(self.start_time_edit)
        self.calendar_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.calendar_button.setObjectName("calendar_button")
        self.horizontalLayout.addWidget(self.calendar_button)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.start_time_format_label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.start_time_format_label.setObjectName("start_time_format_label")
        self.verticalLayout_2.addWidget(self.start_time_format_label)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.verticalLayout_2)
        self.resolution_label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.resolution_label.setObjectName("resolution_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.resolution_label)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.resolution_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.resolution_edit.setObjectName("resolution_edit")
        self.verticalLayout_3.addWidget(self.resolution_edit)
        self.resolution_format_label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.resolution_format_label.setObjectName("resolution_format_label")
        self.verticalLayout_3.addWidget(self.resolution_format_label)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.verticalLayout_3)
        self.left_layout.addLayout(self.formLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.ignore_year_check_box = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.ignore_year_check_box.setObjectName("ignore_year_check_box")
        self.horizontalLayout_2.addWidget(self.ignore_year_check_box)
        self.repeat_check_box = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.repeat_check_box.setObjectName("repeat_check_box")
        self.horizontalLayout_2.addWidget(self.repeat_check_box)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.left_layout.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(TimeSeriesFixedResolutionEditor)
        QtCore.QMetaObject.connectSlotsByName(TimeSeriesFixedResolutionEditor)

    def retranslateUi(self, TimeSeriesFixedResolutionEditor):
        TimeSeriesFixedResolutionEditor.setWindowTitle(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Form", None, -1))
        self.start_time_label.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Start time", None, -1))
        self.calendar_button.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Calendar", None, -1))
        self.start_time_format_label.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Format: YYYY-MM-DDThh:mm:ss", None, -1))
        self.resolution_label.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Resolution", None, -1))
        self.resolution_format_label.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Available units: s, m, h, D, M, Y", None, -1))
        self.ignore_year_check_box.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Ignore year", None, -1))
        self.repeat_check_box.setText(QtWidgets.QApplication.translate("TimeSeriesFixedResolutionEditor", "Repeat", None, -1))

