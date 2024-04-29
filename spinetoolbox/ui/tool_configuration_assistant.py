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
## Form generated from reading UI file 'tool_configuration_assistant.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QScrollArea, QSizePolicy,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_PackagesForm(object):
    def setupUi(self, PackagesForm):
        if not PackagesForm.objectName():
            PackagesForm.setObjectName(u"PackagesForm")
        PackagesForm.setWindowModality(Qt.ApplicationModal)
        PackagesForm.resize(685, 331)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PackagesForm.sizePolicy().hasHeightForWidth())
        PackagesForm.setSizePolicy(sizePolicy)
        PackagesForm.setMinimumSize(QSize(0, 0))
        PackagesForm.setMaximumSize(QSize(16777215, 16777215))
        PackagesForm.setMouseTracking(False)
        PackagesForm.setFocusPolicy(Qt.StrongFocus)
        PackagesForm.setContextMenuPolicy(Qt.NoContextMenu)
        PackagesForm.setAutoFillBackground(False)
        self.verticalLayout = QVBoxLayout(PackagesForm)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(PackagesForm)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 681, 327))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBox_general = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_general.setObjectName(u"groupBox_general")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_general.sizePolicy().hasHeightForWidth())
        self.groupBox_general.setSizePolicy(sizePolicy1)
        self.groupBox_general.setMinimumSize(QSize(0, 0))
        self.groupBox_general.setMaximumSize(QSize(16777215, 16777215))
        self.groupBox_general.setAutoFillBackground(False)
        self.groupBox_general.setFlat(False)
        self.verticalLayout_6 = QVBoxLayout(self.groupBox_general)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.textBrowser_spine_opt = QTextBrowser(self.groupBox_general)
        self.textBrowser_spine_opt.setObjectName(u"textBrowser_spine_opt")

        self.verticalLayout_6.addWidget(self.textBrowser_spine_opt)


        self.verticalLayout_2.addWidget(self.groupBox_general)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)


        self.verticalLayout.addLayout(self.verticalLayout_3)


        self.retranslateUi(PackagesForm)

        QMetaObject.connectSlotsByName(PackagesForm)
    # setupUi

    def retranslateUi(self, PackagesForm):
        PackagesForm.setWindowTitle(QCoreApplication.translate("PackagesForm", u"Tool configuration assistant", None))
        self.groupBox_general.setTitle(QCoreApplication.translate("PackagesForm", u"SpineOpt.jl", None))
    # retranslateUi

