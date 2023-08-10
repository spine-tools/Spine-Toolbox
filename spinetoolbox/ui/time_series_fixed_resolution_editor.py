# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'time_series_fixed_resolution_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.4.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout,
    QWidget)

from spinetoolbox.widgets.custom_qtableview import TimeSeriesFixedResolutionTableView
from spinetoolbox.widgets.plot_widget import PlotWidget

class Ui_TimeSeriesFixedResolutionEditor(object):
    def setupUi(self, TimeSeriesFixedResolutionEditor):
        if not TimeSeriesFixedResolutionEditor.objectName():
            TimeSeriesFixedResolutionEditor.setObjectName(u"TimeSeriesFixedResolutionEditor")
        TimeSeriesFixedResolutionEditor.resize(581, 439)
        self.verticalLayout = QVBoxLayout(TimeSeriesFixedResolutionEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter = QSplitter(TimeSeriesFixedResolutionEditor)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.left_layout = QVBoxLayout(self.verticalLayoutWidget)
        self.left_layout.setObjectName(u"left_layout")
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.start_time_label = QLabel(self.verticalLayoutWidget)
        self.start_time_label.setObjectName(u"start_time_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.start_time_label)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.start_time_edit = QLineEdit(self.verticalLayoutWidget)
        self.start_time_edit.setObjectName(u"start_time_edit")

        self.horizontalLayout.addWidget(self.start_time_edit)

        self.calendar_button = QPushButton(self.verticalLayoutWidget)
        self.calendar_button.setObjectName(u"calendar_button")

        self.horizontalLayout.addWidget(self.calendar_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.start_time_format_label = QLabel(self.verticalLayoutWidget)
        self.start_time_format_label.setObjectName(u"start_time_format_label")

        self.verticalLayout_2.addWidget(self.start_time_format_label)


        self.formLayout.setLayout(0, QFormLayout.FieldRole, self.verticalLayout_2)

        self.resolution_label = QLabel(self.verticalLayoutWidget)
        self.resolution_label.setObjectName(u"resolution_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.resolution_label)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.resolution_edit = QLineEdit(self.verticalLayoutWidget)
        self.resolution_edit.setObjectName(u"resolution_edit")

        self.verticalLayout_3.addWidget(self.resolution_edit)

        self.resolution_format_label = QLabel(self.verticalLayoutWidget)
        self.resolution_format_label.setObjectName(u"resolution_format_label")

        self.verticalLayout_3.addWidget(self.resolution_format_label)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.verticalLayout_3)


        self.left_layout.addLayout(self.formLayout)

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

        self.time_series_table = TimeSeriesFixedResolutionTableView(self.verticalLayoutWidget)
        self.time_series_table.setObjectName(u"time_series_table")
        self.time_series_table.horizontalHeader().setStretchLastSection(True)

        self.left_layout.addWidget(self.time_series_table)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.plot_widget = PlotWidget(self.splitter)
        self.plot_widget.setObjectName(u"plot_widget")
        self.splitter.addWidget(self.plot_widget)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(TimeSeriesFixedResolutionEditor)

        QMetaObject.connectSlotsByName(TimeSeriesFixedResolutionEditor)
    # setupUi

    def retranslateUi(self, TimeSeriesFixedResolutionEditor):
        TimeSeriesFixedResolutionEditor.setWindowTitle(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Form", None))
        self.start_time_label.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Start time", None))
        self.calendar_button.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Calendar", None))
        self.start_time_format_label.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Format: YYYY-MM-DDThh:mm:ss", None))
        self.resolution_label.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Resolution", None))
        self.resolution_format_label.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Available units: s, m, h, D, M, Y", None))
        self.ignore_year_check_box.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Ignore year", None))
        self.repeat_check_box.setText(QCoreApplication.translate("TimeSeriesFixedResolutionEditor", u"Repeat", None))
    # retranslateUi

