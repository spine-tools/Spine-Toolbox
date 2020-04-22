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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_options.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_options.ui' applies.
#
# Created: Thu Feb 13 11:54:02 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportOptions(object):
    def setupUi(self, ImportOptions):
        ImportOptions.setObjectName("ImportOptions")
        ImportOptions.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.options_box = QtWidgets.QGroupBox(ImportOptions)
        self.options_box.setObjectName("options_box")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.options_box)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.options_layout = QtWidgets.QFormLayout()
        self.options_layout.setObjectName("options_layout")
        self.verticalLayout_2.addLayout(self.options_layout)
        self.verticalLayout.addWidget(self.options_box)

        self.retranslateUi(ImportOptions)
        QtCore.QMetaObject.connectSlotsByName(ImportOptions)

    def retranslateUi(self, ImportOptions):
        ImportOptions.setWindowTitle(QtWidgets.QApplication.translate("ImportOptions", "Form", None, -1))
        self.options_box.setTitle(QtWidgets.QApplication.translate("ImportOptions", "Options", None, -1))

