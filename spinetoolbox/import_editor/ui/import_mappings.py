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

################################################################################
## Form generated from reading UI file 'import_mappings.ui'
##
## Created by: Qt User Interface Compiler version 5.14.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *

from spinetoolbox.import_editor.widgets.import_mapping_options import ImportMappingOptions


class Ui_ImportMappings(object):
    def setupUi(self, ImportMappings):
        if not ImportMappings.objectName():
            ImportMappings.setObjectName(u"ImportMappings")
        ImportMappings.resize(367, 536)
        self.verticalLayout_3 = QVBoxLayout(ImportMappings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.mapping_splitter = QSplitter(ImportMappings)
        self.mapping_splitter.setObjectName(u"mapping_splitter")
        self.mapping_splitter.setOrientation(Qt.Vertical)
        self.verticalLayoutWidget = QWidget(self.mapping_splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.top_layout = QVBoxLayout(self.verticalLayoutWidget)
        self.top_layout.setObjectName(u"top_layout")
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.new_button = QPushButton(self.verticalLayoutWidget)
        self.new_button.setObjectName(u"new_button")

        self.button_layout.addWidget(self.new_button)

        self.remove_button = QPushButton(self.verticalLayoutWidget)
        self.remove_button.setObjectName(u"remove_button")

        self.button_layout.addWidget(self.remove_button)


        self.top_layout.addLayout(self.button_layout)

        self.list_view = QListView(self.verticalLayoutWidget)
        self.list_view.setObjectName(u"list_view")

        self.top_layout.addWidget(self.list_view)

        self.mapping_splitter.addWidget(self.verticalLayoutWidget)
        self.verticalLayoutWidget_2 = QWidget(self.mapping_splitter)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.bottom_layout = QVBoxLayout(self.verticalLayoutWidget_2)
        self.bottom_layout.setObjectName(u"bottom_layout")
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.options = ImportMappingOptions(self.verticalLayoutWidget_2)
        self.options.setObjectName(u"options")

        self.bottom_layout.addWidget(self.options)

        self.table_view = QTableView(self.verticalLayoutWidget_2)
        self.table_view.setObjectName(u"table_view")

        self.bottom_layout.addWidget(self.table_view)

        self.mapping_splitter.addWidget(self.verticalLayoutWidget_2)

        self.verticalLayout_3.addWidget(self.mapping_splitter)


        self.retranslateUi(ImportMappings)

        QMetaObject.connectSlotsByName(ImportMappings)
    # setupUi

    def retranslateUi(self, ImportMappings):
        ImportMappings.setWindowTitle(QCoreApplication.translate("ImportMappings", u"Form", None))
        self.new_button.setText(QCoreApplication.translate("ImportMappings", u"New", None))
        self.remove_button.setText(QCoreApplication.translate("ImportMappings", u"Remove", None))
    # retranslateUi

