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


class Ui_dialog(object):
    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(563, 418)
        self.verticalLayoutWidget = QtWidgets.QWidget(dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(9, 10, 551, 401))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.top_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setObjectName("top_layout")
        self.edit_area_layout = QtWidgets.QHBoxLayout()
        self.edit_area_layout.setObjectName("edit_area_layout")
        self.time_series_table = QtWidgets.QTableView(self.verticalLayoutWidget)
        self.time_series_table.setObjectName("time_series_table")
        self.edit_area_layout.addWidget(self.time_series_table)
        self.plot_widget = QtWidgets.QWidget(self.verticalLayoutWidget)
        self.plot_widget.setObjectName("plot_widget")
        self.edit_area_layout.addWidget(self.plot_widget)
        self.top_layout.addLayout(self.edit_area_layout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.close_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.close_button.setObjectName("close_button")
        self.horizontalLayout.addWidget(self.close_button)
        self.top_layout.addLayout(self.horizontalLayout)

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog):
        dialog.setWindowTitle(QtWidgets.QApplication.translate("dialog", "Dialog", None, -1))
        self.close_button.setText(QtWidgets.QApplication.translate("dialog", "Close", None, -1))
