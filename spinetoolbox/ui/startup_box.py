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
## Form generated from reading UI file 'startup_box.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)
from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(879, 708)
        self.horizontalLayout_2 = QHBoxLayout(Form)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.groupBox_7 = QGroupBox(Form)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setMinimumSize(QSize(0, 16))
        self.verticalLayout = QVBoxLayout(self.groupBox_7)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pushButton_9 = QPushButton(self.groupBox_7)
        self.pushButton_9.setObjectName(u"pushButton_9")

        self.verticalLayout.addWidget(self.pushButton_9)

        self.pushButton_8 = QPushButton(self.groupBox_7)
        self.pushButton_8.setObjectName(u"pushButton_8")

        self.verticalLayout.addWidget(self.pushButton_8)

        self.label_2 = QLabel(self.groupBox_7)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.listWidget = QListWidget(self.groupBox_7)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setStyleSheet(u"background-color: rgb(240, 240, 240);\n"
"border-color: rgb(240, 240, 240);")

        self.verticalLayout.addWidget(self.listWidget)


        self.horizontalLayout_2.addWidget(self.groupBox_7)

        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setStyleSheet(u"")
        self.tabWidget.setUsesScrollButtons(False)
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_6 = QVBoxLayout(self.tab_2)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_3 = QScrollArea(self.tab_2)
        self.scrollArea_3.setObjectName(u"scrollArea_3")
        self.scrollArea_3.setEnabled(True)
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 359, 659))
        self.scrollAreaWidgetContents.setAutoFillBackground(True)
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setUnderline(False)
        self.label_3.setFont(font)
        self.label_3.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.verticalLayout_4.addWidget(self.label_3)

        self.groupBox_4 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_10 = QLabel(self.groupBox_4)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMaximumSize(QSize(75, 75))
        self.label_10.setPixmap(QPixmap(u":/startupbox/startupbox_images/say_hello_thumbnail.png"))
        self.label_10.setScaledContents(True)

        self.horizontalLayout_3.addWidget(self.label_10)

        self.label_6 = QLabel(self.groupBox_4)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setWordWrap(True)
        self.label_6.setMargin(5)

        self.horizontalLayout_3.addWidget(self.label_6)

        self.pushButton = QPushButton(self.groupBox_4)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_3.addWidget(self.pushButton)


        self.verticalLayout_4.addWidget(self.groupBox_4)

        self.groupBox_10 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.horizontalLayout = QHBoxLayout(self.groupBox_10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_11 = QLabel(self.groupBox_10)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setMaximumSize(QSize(75, 75))
        self.label_11.setPixmap(QPixmap(u":/startupbox/startupbox_images/data_structure_thumbnail.png"))
        self.label_11.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label_11)

        self.label_7 = QLabel(self.groupBox_10)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setWordWrap(True)
        self.label_7.setMargin(5)

        self.horizontalLayout.addWidget(self.label_7)

        self.pushButton_2 = QPushButton(self.groupBox_10)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout_4.addWidget(self.groupBox_10)

        self.groupBox_13 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_13)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_16 = QLabel(self.groupBox_13)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setMaximumSize(QSize(75, 75))
        self.label_16.setPixmap(QPixmap(u":/startupbox/startupbox_images/advanced_material_thumbmail.png"))
        self.label_16.setScaledContents(True)

        self.horizontalLayout_4.addWidget(self.label_16)

        self.label_9 = QLabel(self.groupBox_13)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setWordWrap(True)
        self.label_9.setMargin(5)

        self.horizontalLayout_4.addWidget(self.label_9)

        self.pushButton_5 = QPushButton(self.groupBox_13)
        self.pushButton_5.setObjectName(u"pushButton_5")

        self.horizontalLayout_4.addWidget(self.pushButton_5)


        self.verticalLayout_4.addWidget(self.groupBox_13)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.label_14 = QLabel(self.scrollAreaWidgetContents)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font)
        self.label_14.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.verticalLayout_4.addWidget(self.label_14)

        self.groupBox_11 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_11.setObjectName(u"groupBox_11")
        self.horizontalLayout_5 = QHBoxLayout(self.groupBox_11)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_15 = QLabel(self.groupBox_11)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setMaximumSize(QSize(75, 75))
        self.label_15.setPixmap(QPixmap(u":/startupbox/startupbox_images/workflow_thumbnail.png"))
        self.label_15.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.label_15)

        self.label_8 = QLabel(self.groupBox_11)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setWordWrap(True)
        self.label_8.setMargin(5)

        self.horizontalLayout_5.addWidget(self.label_8)

        self.pushButton_4 = QPushButton(self.groupBox_11)
        self.pushButton_4.setObjectName(u"pushButton_4")

        self.horizontalLayout_5.addWidget(self.pushButton_4)


        self.verticalLayout_4.addWidget(self.groupBox_11)


        self.verticalLayout_5.addLayout(self.verticalLayout_4)

        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_6.addWidget(self.scrollArea_3)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_3 = QVBoxLayout(self.tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(self.tab)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 341, 641))
        self.horizontalLayout_9 = QHBoxLayout(self.scrollAreaWidgetContents_3)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.label = QLabel(self.scrollAreaWidgetContents_3)
        self.label.setObjectName(u"label")
        self.label.setFont(font)
        self.label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.verticalLayout_11.addWidget(self.label)

        self.groupBox_8 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_8.setObjectName(u"groupBox_8")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_8.sizePolicy().hasHeightForWidth())
        self.groupBox_8.setSizePolicy(sizePolicy)
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox_8)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_18 = QLabel(self.groupBox_8)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setMaximumSize(QSize(75, 75))
        self.label_18.setPixmap(QPixmap(u":/startupbox/startupbox_images/data_import_export.png"))
        self.label_18.setScaledContents(True)

        self.horizontalLayout_7.addWidget(self.label_18)

        self.label_5 = QLabel(self.groupBox_8)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setTextFormat(Qt.TextFormat.PlainText)
        self.label_5.setScaledContents(False)
        self.label_5.setWordWrap(True)

        self.horizontalLayout_7.addWidget(self.label_5)

        self.pushButton_3 = QPushButton(self.groupBox_8)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.horizontalLayout_7.addWidget(self.pushButton_3)


        self.verticalLayout_11.addWidget(self.groupBox_8)

        self.label_13 = QLabel(self.scrollAreaWidgetContents_3)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font)
        self.label_13.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.verticalLayout_11.addWidget(self.label_13)

        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.horizontalLayout_8 = QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(75, 75))
        self.label_4.setPixmap(QPixmap(u":/startupbox/startupbox_images/simple_system_schematic.png"))
        self.label_4.setScaledContents(True)

        self.horizontalLayout_8.addWidget(self.label_4)

        self.label_12 = QLabel(self.groupBox_3)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setTextFormat(Qt.TextFormat.PlainText)
        self.label_12.setScaledContents(False)
        self.label_12.setWordWrap(True)

        self.horizontalLayout_8.addWidget(self.label_12)

        self.pushButton_7 = QPushButton(self.groupBox_3)
        self.pushButton_7.setObjectName(u"pushButton_7")

        self.horizontalLayout_8.addWidget(self.pushButton_7)


        self.verticalLayout_11.addWidget(self.groupBox_3)

        self.label_19 = QLabel(self.scrollAreaWidgetContents_3)
        self.label_19.setObjectName(u"label_19")
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setBold(True)
        self.label_19.setFont(font1)

        self.verticalLayout_11.addWidget(self.label_19)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_2)


        self.horizontalLayout_9.addLayout(self.verticalLayout_11)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_3)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.tab, "")

        self.horizontalLayout_2.addWidget(self.tabWidget)

        self.groupBox_6 = QGroupBox(Form)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setMinimumSize(QSize(0, 16))
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_17 = QLabel(self.groupBox_6)
        self.label_17.setObjectName(u"label_17")
        font2 = QFont()
        font2.setFamilies([u"Artifakt Element Black"])
        font2.setPointSize(11)
        font2.setBold(True)
        font2.setItalic(False)
        self.label_17.setFont(font2)
        self.label_17.setAutoFillBackground(False)
        self.label_17.setStyleSheet(u"")
        self.label_17.setFrameShape(QFrame.Shape.StyledPanel)
        self.label_17.setFrameShadow(QFrame.Shadow.Raised)
        self.label_17.setLineWidth(1)
        self.label_17.setScaledContents(False)

        self.verticalLayout_2.addWidget(self.label_17)

        self.listWidget_2 = QListWidget(self.groupBox_6)
        self.listWidget_2.setObjectName(u"listWidget_2")
        self.listWidget_2.setStyleSheet(u"background-color: rgb(240, 240, 240);\n"
"border-color: rgb(240, 240, 240);")
        self.listWidget_2.setProperty(u"showDropIndicator", True)
        self.listWidget_2.setProperty(u"isWrapping", False)
        self.listWidget_2.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.listWidget_2)


        self.horizontalLayout_2.addWidget(self.groupBox_6)


        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("Form", u"Main", None))
        self.pushButton_9.setText(QCoreApplication.translate("Form", u"New Project", None))
        self.pushButton_8.setText(QCoreApplication.translate("Form", u"Open Project", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Recent", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Introductory Learning Material", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Form", u"Hello World", None))
        self.label_10.setText("")
        self.label_6.setText(QCoreApplication.translate("Form", u"In this guide you will learn two ways of running a 'Hello, World!' program on Spine Toolbox.", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Open", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("Form", u"Introduction to Spine Data Structure", None))
        self.label_11.setText("")
        self.label_7.setText(QCoreApplication.translate("Form", u"Learn more on the Spine Data Structure through this GitHub document.", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Open", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("Form", u"Executing Projects", None))
        self.label_16.setText("")
        self.label_9.setText(QCoreApplication.translate("Form", u"This document describes how executing a project works and what resources are passed between project items at execution time.", None))
        self.pushButton_5.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_14.setText(QCoreApplication.translate("Form", u"Advanced Learning Material", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("Form", u"Setting up a Workflow", None))
        self.label_15.setText("")
        self.label_8.setText(QCoreApplication.translate("Form", u"This document will show how to add a Tool item to your project.", None))
        self.pushButton_4.setText(QCoreApplication.translate("Form", u"Open", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"Learning materials", None))
        self.label.setText(QCoreApplication.translate("Form", u"Spine Toolbox", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("Form", u"Basic Modelling Workflow", None))
        self.label_18.setText("")
        self.label_5.setText(QCoreApplication.translate("Form", u"This template explains the different ways of importing and exporting data to and from a Spine database", None))
        self.pushButton_3.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"Model specific workflows", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Form", u"SpineOpt - Simple Energy System", None))
        self.label_4.setText("")
        self.label_12.setText(QCoreApplication.translate("Form", u"This template provides a step-by-step guide to setup a simple energy system with Spine Toolbox for SpineOpt.", None))
        self.pushButton_7.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_19.setText(QCoreApplication.translate("Form", u"Prerequisite: SpineOpt", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"Templates", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("Form", u"Software Info", None))
        self.label_17.setText(QCoreApplication.translate("Form", u"<html><head/><body><p><span style=\" font-weight:700; font-style:normal; color:#000000;\">TextLabel</span></p></body></html>", None))
    # retranslateUi

