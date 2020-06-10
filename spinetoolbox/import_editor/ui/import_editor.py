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
## Form generated from reading UI file 'import_editor.ui'
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

from spinetoolbox.widgets.table_view_with_button_header import TableViewWithButtonHeader
from spinetoolbox.import_editor.widgets.import_mappings import ImportMappings


class Ui_ImportEditor(object):
    def setupUi(self, ImportEditor):
        if not ImportEditor.objectName():
            ImportEditor.setObjectName(u"ImportEditor")
        ImportEditor.resize(806, 632)
        self.verticalLayout = QVBoxLayout(ImportEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.main_splitter = QSplitter(ImportEditor)
        self.main_splitter.setObjectName(u"main_splitter")
        self.main_splitter.setOrientation(Qt.Horizontal)
        self.sources_box = QGroupBox(self.main_splitter)
        self.sources_box.setObjectName(u"sources_box")
        self.verticalLayout_4 = QVBoxLayout(self.sources_box)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.sources_splitter = QSplitter(self.sources_box)
        self.sources_splitter.setObjectName(u"sources_splitter")
        self.sources_splitter.setOrientation(Qt.Vertical)
        self.top_source_splitter = QSplitter(self.sources_splitter)
        self.top_source_splitter.setObjectName(u"top_source_splitter")
        self.top_source_splitter.setOrientation(Qt.Horizontal)
        self.source_list = QListWidget(self.top_source_splitter)
        self.source_list.setObjectName(u"source_list")
        self.source_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.top_source_splitter.addWidget(self.source_list)
        self.sources_splitter.addWidget(self.top_source_splitter)
        self.source_preview_widget_stack = QStackedWidget(self.sources_splitter)
        self.source_preview_widget_stack.setObjectName(u"source_preview_widget_stack")
        self.table_page = QWidget()
        self.table_page.setObjectName(u"table_page")
        self.verticalLayout_2 = QVBoxLayout(self.table_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.source_data_table = TableViewWithButtonHeader(self.table_page)
        self.source_data_table.setObjectName(u"source_data_table")

        self.verticalLayout_2.addWidget(self.source_data_table)

        self.source_preview_widget_stack.addWidget(self.table_page)
        self.loading_page = QWidget()
        self.loading_page.setObjectName(u"loading_page")
        self.verticalLayout_3 = QVBoxLayout(self.loading_page)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.waiting_label = QLabel(self.loading_page)
        self.waiting_label.setObjectName(u"waiting_label")

        self.horizontalLayout.addWidget(self.waiting_label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.source_preview_widget_stack.addWidget(self.loading_page)
        self.sources_splitter.addWidget(self.source_preview_widget_stack)

        self.verticalLayout_4.addWidget(self.sources_splitter)

        self.main_splitter.addWidget(self.sources_box)
        self.mappings_box = QGroupBox(self.main_splitter)
        self.mappings_box.setObjectName(u"mappings_box")
        self.verticalLayout_5 = QVBoxLayout(self.mappings_box)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.mapper = ImportMappings(self.mappings_box)
        self.mapper.setObjectName(u"mapper")

        self.verticalLayout_5.addWidget(self.mapper)

        self.main_splitter.addWidget(self.mappings_box)

        self.verticalLayout.addWidget(self.main_splitter)


        self.retranslateUi(ImportEditor)

        self.source_preview_widget_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ImportEditor)
    # setupUi

    def retranslateUi(self, ImportEditor):
        ImportEditor.setWindowTitle(QCoreApplication.translate("ImportEditor", u"Form", None))
        self.sources_box.setTitle(QCoreApplication.translate("ImportEditor", u"Sources", None))
        self.waiting_label.setText(QCoreApplication.translate("ImportEditor", u"Loading preview...", None))
        self.mappings_box.setTitle(QCoreApplication.translate("ImportEditor", u"Mappings", None))
    # retranslateUi

