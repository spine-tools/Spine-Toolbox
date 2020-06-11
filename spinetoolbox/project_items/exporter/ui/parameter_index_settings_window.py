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
## Form generated from reading UI file 'parameter_index_settings_window.ui'
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


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.WindowModal)
        Form.resize(680, 472)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_stack = QStackedWidget(Form)
        self.widget_stack.setObjectName(u"widget_stack")
        self.settings_page = QWidget()
        self.settings_page.setObjectName(u"settings_page")
        self.verticalLayout_2 = QVBoxLayout(self.settings_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.settings_area = QScrollArea(self.settings_page)
        self.settings_area.setObjectName(u"settings_area")
        self.settings_area.setWidgetResizable(True)
        self.settings_area_contents = QWidget()
        self.settings_area_contents.setObjectName(u"settings_area_contents")
        self.settings_area_contents.setGeometry(QRect(0, 0, 642, 405))
        self.verticalLayout_3 = QVBoxLayout(self.settings_area_contents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.settings_area_layout = QVBoxLayout()
        self.settings_area_layout.setObjectName(u"settings_area_layout")

        self.verticalLayout_3.addLayout(self.settings_area_layout)

        self.settings_area.setWidget(self.settings_area_contents)

        self.verticalLayout_2.addWidget(self.settings_area)

        self.widget_stack.addWidget(self.settings_page)
        self.empty_message_page = QWidget()
        self.empty_message_page.setObjectName(u"empty_message_page")
        self.verticalLayout_4 = QVBoxLayout(self.empty_message_page)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label = QLabel(self.empty_message_page)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.widget_stack.addWidget(self.empty_message_page)

        self.verticalLayout.addWidget(self.widget_stack)

        self.button_box = QDialogButtonBox(Form)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(Form)

        self.widget_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Gdx Parameter Indexing Settings", None))
        self.label.setText(QCoreApplication.translate("Form", u"No indexed parameters found in this database.", None))
    # retranslateUi

