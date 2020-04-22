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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_source_selector.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_source_selector.ui' applies.
#
# Created: Thu Feb 13 11:54:05 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportSourceSelector(object):
    def setupUi(self, ImportSourceSelector):
        ImportSourceSelector.setObjectName("ImportSourceSelector")
        ImportSourceSelector.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportSourceSelector)
        self.verticalLayout.setObjectName("verticalLayout")
        self.source_list = QtWidgets.QListWidget(ImportSourceSelector)
        self.source_list.setObjectName("source_list")
        self.verticalLayout.addWidget(self.source_list)

        self.retranslateUi(ImportSourceSelector)
        QtCore.QMetaObject.connectSlotsByName(ImportSourceSelector)

    def retranslateUi(self, ImportSourceSelector):
        ImportSourceSelector.setWindowTitle(QtWidgets.QApplication.translate("ImportSourceSelector", "Form", None, -1))

