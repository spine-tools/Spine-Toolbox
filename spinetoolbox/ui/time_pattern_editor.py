# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'time_pattern_editor.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from spinetoolbox.widgets.custom_qtableview import IndexedValueTableView


class Ui_TimePatternEditor(object):
    def setupUi(self, TimePatternEditor):
        if not TimePatternEditor.objectName():
            TimePatternEditor.setObjectName(u"TimePatternEditor")
        TimePatternEditor.resize(586, 443)
        self.verticalLayout = QVBoxLayout(TimePatternEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pattern_edit_table = IndexedValueTableView(TimePatternEditor)
        self.pattern_edit_table.setObjectName(u"pattern_edit_table")

        self.verticalLayout.addWidget(self.pattern_edit_table)


        self.retranslateUi(TimePatternEditor)

        QMetaObject.connectSlotsByName(TimePatternEditor)
    # setupUi

    def retranslateUi(self, TimePatternEditor):
        TimePatternEditor.setWindowTitle(QCoreApplication.translate("TimePatternEditor", u"Form", None))
    # retranslateUi

