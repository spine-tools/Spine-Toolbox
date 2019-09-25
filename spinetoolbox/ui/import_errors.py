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

# Form implementation generated from reading ui file 'spinetoolbox/ui/import_errors.ui',
# licensing of 'spinetoolbox/ui/import_errors.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportErrors(object):
    def setupUi(self, ImportErrors):
        ImportErrors.setObjectName("ImportErrors")
        ImportErrors.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportErrors)
        self.verticalLayout.setObjectName("verticalLayout")
        self.error_count_label = QtWidgets.QLabel(ImportErrors)
        self.error_count_label.setObjectName("error_count_label")
        self.verticalLayout.addWidget(self.error_count_label)
        self.import_count_label = QtWidgets.QLabel(ImportErrors)
        self.import_count_label.setObjectName("import_count_label")
        self.verticalLayout.addWidget(self.import_count_label)
        self.error_list = QtWidgets.QListWidget(ImportErrors)
        self.error_list.setObjectName("error_list")
        self.verticalLayout.addWidget(self.error_list)

        self.retranslateUi(ImportErrors)
        QtCore.QMetaObject.connectSlotsByName(ImportErrors)

    def retranslateUi(self, ImportErrors):
        ImportErrors.setWindowTitle(QtWidgets.QApplication.translate("ImportErrors", "Form", None, -1))
        self.error_count_label.setText(QtWidgets.QApplication.translate("ImportErrors", "Number of errors:", None, -1))
        self.import_count_label.setText(QtWidgets.QApplication.translate("ImportErrors", "Number of imports:", None, -1))

