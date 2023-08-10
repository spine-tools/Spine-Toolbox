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
## Form generated from reading UI file 'array_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QSizePolicy, QSpacerItem,
    QSplitter, QStackedWidget, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qtableview import ArrayTableView
from spinetoolbox.widgets.plot_widget import PlotWidget

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(569, 420)
        self.verticalLayout_4 = QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.splitter = QSplitter(Form)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.value_type_combo_box = QComboBox(self.verticalLayoutWidget)
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.setObjectName(u"value_type_combo_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.value_type_combo_box)


        self.verticalLayout_3.addLayout(self.formLayout)

        self.array_table_view = ArrayTableView(self.verticalLayoutWidget)
        self.array_table_view.setObjectName(u"array_table_view")
        self.array_table_view.horizontalHeader().setStretchLastSection(True)
        self.array_table_view.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.array_table_view)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.plot_widget_stack = QStackedWidget(self.splitter)
        self.plot_widget_stack.setObjectName(u"plot_widget_stack")
        self.cannot_plot_page = QWidget()
        self.cannot_plot_page.setObjectName(u"cannot_plot_page")
        self.verticalLayout_2 = QVBoxLayout(self.cannot_plot_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label = QLabel(self.cannot_plot_page)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.plot_widget_stack.addWidget(self.cannot_plot_page)
        self.plot_page = QWidget()
        self.plot_page.setObjectName(u"plot_page")
        self.verticalLayout = QVBoxLayout(self.plot_page)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.plot_widget = PlotWidget(self.plot_page)
        self.plot_widget.setObjectName(u"plot_widget")

        self.verticalLayout.addWidget(self.plot_widget)

        self.plot_widget_stack.addWidget(self.plot_page)
        self.splitter.addWidget(self.plot_widget_stack)

        self.verticalLayout_4.addWidget(self.splitter)


        self.retranslateUi(Form)

        self.plot_widget_stack.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Value type:", None))
        self.value_type_combo_box.setItemText(0, QCoreApplication.translate("Form", u"Float", None))
        self.value_type_combo_box.setItemText(1, QCoreApplication.translate("Form", u"Datetime", None))
        self.value_type_combo_box.setItemText(2, QCoreApplication.translate("Form", u"Duration", None))
        self.value_type_combo_box.setItemText(3, QCoreApplication.translate("Form", u"String", None))

        self.label.setText(QCoreApplication.translate("Form", u"Cannot plot this data type.", None))
    # retranslateUi

