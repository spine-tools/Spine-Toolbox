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

# Form implementation generated from reading ui file '../spinetoolbox/ui/time_pattern_editor.ui',
# licensing of '../spinetoolbox/ui/time_pattern_editor.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TimePatternEditor(object):
    def setupUi(self, TimePatternEditor):
        TimePatternEditor.setObjectName("TimePatternEditor")
        TimePatternEditor.resize(586, 443)
        self.verticalLayout = QtWidgets.QVBoxLayout(TimePatternEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.length_edit_label = QtWidgets.QLabel(TimePatternEditor)
        self.length_edit_label.setObjectName("length_edit_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.length_edit_label)
        self.length_edit = QtWidgets.QSpinBox(TimePatternEditor)
        self.length_edit.setMinimum(1)
        self.length_edit.setMaximum(999999)
        self.length_edit.setObjectName("length_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.length_edit)
        self.verticalLayout.addLayout(self.formLayout)
        self.pattern_edit_table = QtWidgets.QTableView(TimePatternEditor)
        self.pattern_edit_table.setObjectName("pattern_edit_table")
        self.verticalLayout.addWidget(self.pattern_edit_table)

        self.retranslateUi(TimePatternEditor)
        QtCore.QMetaObject.connectSlotsByName(TimePatternEditor)

    def retranslateUi(self, TimePatternEditor):
        TimePatternEditor.setWindowTitle(QtWidgets.QApplication.translate("TimePatternEditor", "Form", None, -1))
        self.length_edit_label.setText(QtWidgets.QApplication.translate("TimePatternEditor", "Length", None, -1))

