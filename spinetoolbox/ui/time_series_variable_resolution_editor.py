# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'time_series_variable_resolution_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QHBoxLayout,
    QHeaderView, QSizePolicy, QSpacerItem, QSplitter,
    QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qtableview import IndexedValueTableView
from spinetoolbox.widgets.plot_widget import PlotWidget

class Ui_TimeSeriesVariableResolutionEditor(object):
    def setupUi(self, TimeSeriesVariableResolutionEditor):
        if not TimeSeriesVariableResolutionEditor.objectName():
            TimeSeriesVariableResolutionEditor.setObjectName(u"TimeSeriesVariableResolutionEditor")
        TimeSeriesVariableResolutionEditor.resize(718, 478)
        self.verticalLayout = QVBoxLayout(TimeSeriesVariableResolutionEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter = QSplitter(TimeSeriesVariableResolutionEditor)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.left_layout = QVBoxLayout(self.verticalLayoutWidget)
        self.left_layout.setObjectName(u"left_layout")
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.ignore_year_check_box = QCheckBox(self.verticalLayoutWidget)
        self.ignore_year_check_box.setObjectName(u"ignore_year_check_box")

        self.horizontalLayout_2.addWidget(self.ignore_year_check_box)

        self.repeat_check_box = QCheckBox(self.verticalLayoutWidget)
        self.repeat_check_box.setObjectName(u"repeat_check_box")

        self.horizontalLayout_2.addWidget(self.repeat_check_box)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.left_layout.addLayout(self.horizontalLayout_2)

        self.time_series_table = IndexedValueTableView(self.verticalLayoutWidget)
        self.time_series_table.setObjectName(u"time_series_table")
        self.time_series_table.setMinimumSize(QSize(250, 0))
        self.time_series_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.time_series_table.horizontalHeader().setStretchLastSection(True)

        self.left_layout.addWidget(self.time_series_table)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.plot_widget = PlotWidget(self.splitter)
        self.plot_widget.setObjectName(u"plot_widget")
        self.splitter.addWidget(self.plot_widget)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(TimeSeriesVariableResolutionEditor)

        QMetaObject.connectSlotsByName(TimeSeriesVariableResolutionEditor)
    # setupUi

    def retranslateUi(self, TimeSeriesVariableResolutionEditor):
        TimeSeriesVariableResolutionEditor.setWindowTitle(QCoreApplication.translate("TimeSeriesVariableResolutionEditor", u"Form", None))
        self.ignore_year_check_box.setText(QCoreApplication.translate("TimeSeriesVariableResolutionEditor", u"Ignore year", None))
        self.repeat_check_box.setText(QCoreApplication.translate("TimeSeriesVariableResolutionEditor", u"Repeat", None))
    # retranslateUi

