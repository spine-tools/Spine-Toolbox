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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1481, 928)
        self.groupBox_6 = QGroupBox(Form)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(910, 40, 191, 611))
        self.groupBox_6.setMinimumSize(QSize(0, 16))
        self.listWidget_2 = QListWidget(self.groupBox_6)
        self.listWidget_2.setObjectName(u"listWidget_2")
        self.listWidget_2.setGeometry(QRect(10, 40, 171, 561))
        self.listWidget_2.setStyleSheet(u"background-color: rgb(240, 240, 240);\n"
"border-color: rgb(240, 240, 240);")
        self.listWidget_2.setProperty("showDropIndicator", True)
        self.groupBox_7 = QGroupBox(Form)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setGeometry(QRect(50, 40, 151, 611))
        self.groupBox_7.setMinimumSize(QSize(0, 16))
        self.pushButton_8 = QPushButton(self.groupBox_7)
        self.pushButton_8.setObjectName(u"pushButton_8")
        self.pushButton_8.setGeometry(QRect(10, 40, 131, 24))
        self.label_2 = QLabel(self.groupBox_7)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(10, 80, 49, 16))
        self.listWidget = QListWidget(self.groupBox_7)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setGeometry(QRect(10, 110, 131, 331))
        self.listWidget.setStyleSheet(u"background-color: rgb(240, 240, 240);\n"
"border-color: rgb(240, 240, 240);")
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(210, 40, 691, 611))
        self.tabWidget.setStyleSheet(u"")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.scrollArea_2 = QScrollArea(self.tab_2)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setGeometry(QRect(10, 10, 661, 561))
        self.scrollArea_2.setStyleSheet(u"")
        self.scrollArea_2.setFrameShape(QFrame.NoFrame)
        self.scrollArea_2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_2.setWidgetResizable(False)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 668, 642))
        self.label_3 = QLabel(self.scrollAreaWidgetContents_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 10, 670, 21))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setUnderline(False)
        self.label_3.setFont(font)
        self.label_3.setLayoutDirection(Qt.LeftToRight)
        self.label_14 = QLabel(self.scrollAreaWidgetContents_3)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setGeometry(QRect(10, 430, 670, 21))
        self.label_14.setFont(font)
        self.label_14.setLayoutDirection(Qt.LeftToRight)
        self.groupBox_4 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(10, 50, 631, 101))
        self.groupBox_10 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.groupBox_10.setGeometry(QRect(10, 170, 631, 111))
        self.groupBox_11 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_11.setObjectName(u"groupBox_11")
        self.groupBox_11.setGeometry(QRect(10, 300, 631, 101))
        self.groupBox_13 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.groupBox_13.setGeometry(QRect(10, 460, 631, 101))
        self.groupBox_9 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.groupBox_9.setGeometry(QRect(10, 580, 631, 101))
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_3)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_3 = QVBoxLayout(self.tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(self.tab)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setEnabled(True)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(False)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 668, 642))
        self.label = QLabel(self.scrollAreaWidgetContents_2)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 670, 21))
        self.label.setFont(font)
        self.label.setLayoutDirection(Qt.LeftToRight)
        self.label_13 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(10, 410, 670, 21))
        self.label_13.setFont(font)
        self.label_13.setLayoutDirection(Qt.LeftToRight)
        self.groupBox_8 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.groupBox_8.setGeometry(QRect(10, 50, 631, 111))
        self.label_5 = QLabel(self.groupBox_8)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(90, 20, 351, 71))
        self.label_5.setTextFormat(Qt.PlainText)
        self.label_5.setScaledContents(False)
        self.label_5.setWordWrap(True)
        self.pushButton_3 = QPushButton(self.groupBox_8)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(460, 40, 141, 24))
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 170, 631, 101))
        self.pushButton_4 = QPushButton(self.groupBox)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setGeometry(QRect(460, 30, 141, 24))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(90, 20, 361, 50))
        self.label_6.setTextFormat(Qt.PlainText)
        self.label_6.setScaledContents(False)
        self.label_6.setWordWrap(True)
        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 280, 631, 111))
        self.pushButton_5 = QPushButton(self.groupBox_2)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setGeometry(QRect(464, 40, 131, 24))
        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(80, 20, 361, 81))
        self.label_8.setTextFormat(Qt.PlainText)
        self.label_8.setScaledContents(False)
        self.label_8.setWordWrap(True)
        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(10, 440, 631, 80))
        self.pushButton_7 = QPushButton(self.groupBox_3)
        self.pushButton_7.setObjectName(u"pushButton_7")
        self.pushButton_7.setGeometry(QRect(471, 30, 121, 24))
        self.label_12 = QLabel(self.groupBox_3)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(70, 20, 371, 50))
        self.label_12.setTextFormat(Qt.PlainText)
        self.label_12.setScaledContents(False)
        self.label_12.setWordWrap(True)
        self.groupBox_5 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setGeometry(QRect(10, 540, 631, 91))
        self.pushButton_6 = QPushButton(self.groupBox_5)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setGeometry(QRect(470, 30, 121, 24))
        self.label_9 = QLabel(self.groupBox_5)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(80, 20, 361, 64))
        self.label_9.setTextFormat(Qt.PlainText)
        self.label_9.setScaledContents(False)
        self.label_9.setWordWrap(True)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.tab, "")

        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("Form", u"Software Info", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("Form", u"Main", None))
        self.pushButton_8.setText(QCoreApplication.translate("Form", u"Open Project", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Recent", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Introductory Learnign Material", None))
        self.label_14.setText(QCoreApplication.translate("Form", u"Advanced Learning Material", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Form", u"Hello World", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("Form", u"Introduction to Spine Data Structure", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("Form", u"Setting up a Workflow", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("Form", u"topic 4 tbd", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("Form", u"Tutorial 6", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"Learning materials", None))
        self.label.setText(QCoreApplication.translate("Form", u"Beginner Templates", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"Advanced Templates", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("Form", u"Simple Energy System", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"This tutorial provides a step-by-step guide to setup a simple energy system with Spine Toolbox for SpineOpt. Spine Toolbox is used to create a workflow with databases and tools and SpineOpt is the tool that simulates/optimizes the energy system.", None))
        self.pushButton_3.setText(QCoreApplication.translate("Form", u"Open", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Reserve Requirement", None))
        self.pushButton_4.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"This tutorial provides a step-by-step guide to include reserve requirements in a simple energy system with Spine Toolbox for SpineOpt.", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Form", u"Hydropower Plant", None))
        self.pushButton_5.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"Welcome to this Spine Toolbox Case Study tutorial. Case Study A5 is one of the Spine Project case studies designed to verify Toolbox and Model capabilities. To this end, it reproduces an already existing study about hydropower on the Skellefte river, which models one week of operation of the fifteen power stations along the river.", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Form", u"TBD?", None))
        self.pushButton_7.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"TO BE Defined", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("Form", u"Coal Plant", None))
        self.pushButton_6.setText(QCoreApplication.translate("Form", u"Open", None))
        self.label_9.setText(QCoreApplication.translate("Form", u"The system contains three demand nodes, connections between them, a coal plant and a wind plant to provide the energy to the time varying demand. The system is run over a 48 hour timeline.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"Templates", None))
    # retranslateUi

