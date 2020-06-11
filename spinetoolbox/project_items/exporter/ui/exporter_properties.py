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
## Form generated from reading UI file 'exporter_properties.ui'
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

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(294, 370)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.item_name_label = QLabel(Form)
        self.item_name_label.setObjectName(u"item_name_label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.item_name_label.sizePolicy().hasHeightForWidth())
        self.item_name_label.setSizePolicy(sizePolicy)
        self.item_name_label.setMinimumSize(QSize(0, 20))
        self.item_name_label.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.item_name_label.setFont(font)
        self.item_name_label.setStyleSheet(u"background-color: #ecd8c6;")
        self.item_name_label.setFrameShape(QFrame.Box)
        self.item_name_label.setFrameShadow(QFrame.Sunken)
        self.item_name_label.setAlignment(Qt.AlignCenter)
        self.item_name_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.item_name_label)

        self.scrollArea_6 = QScrollArea(Form)
        self.scrollArea_6.setObjectName(u"scrollArea_6")
        self.scrollArea_6.setWidgetResizable(True)
        self.scrollAreaWidgetContents_5 = QWidget()
        self.scrollAreaWidgetContents_5.setObjectName(u"scrollAreaWidgetContents_5")
        self.scrollAreaWidgetContents_5.setGeometry(QRect(0, 0, 292, 348))
        self.verticalLayout_21 = QVBoxLayout(self.scrollAreaWidgetContents_5)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.databases_list_layout = QVBoxLayout()
        self.databases_list_layout.setObjectName(u"databases_list_layout")

        self.verticalLayout_21.addLayout(self.databases_list_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_21.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.cancel_on_error_check_box = QCheckBox(self.scrollAreaWidgetContents_5)
        self.cancel_on_error_check_box.setObjectName(u"cancel_on_error_check_box")
        self.cancel_on_error_check_box.setChecked(True)

        self.horizontalLayout.addWidget(self.cancel_on_error_check_box)


        self.verticalLayout_21.addLayout(self.horizontalLayout)

        self.line_6 = QFrame(self.scrollAreaWidgetContents_5)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.HLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_21.addWidget(self.line_6)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_17)

        self.open_directory_button = QToolButton(self.scrollAreaWidgetContents_5)
        self.open_directory_button.setObjectName(u"open_directory_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.open_directory_button.sizePolicy().hasHeightForWidth())
        self.open_directory_button.setSizePolicy(sizePolicy1)
        self.open_directory_button.setMinimumSize(QSize(22, 22))
        self.open_directory_button.setMaximumSize(QSize(22, 22))
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.open_directory_button.setIcon(icon)

        self.horizontalLayout_13.addWidget(self.open_directory_button)


        self.verticalLayout_21.addLayout(self.horizontalLayout_13)

        self.scrollArea_6.setWidget(self.scrollAreaWidgetContents_5)

        self.verticalLayout.addWidget(self.scrollArea_6)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.item_name_label.setText(QCoreApplication.translate("Form", u"Name", None))
        self.cancel_on_error_check_box.setText(QCoreApplication.translate("Form", u"Cancel export on error", None))
#if QT_CONFIG(tooltip)
        self.open_directory_button.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Open this Exporter's project directory in file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

