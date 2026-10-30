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
## Form generated from reading UI file 'python_kernel_manager.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTextBrowser, QVBoxLayout,
    QWidget)
from spinetoolbox import resources_icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(390, 274)
        self.verticalLayout_3 = QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.stackedWidget = QStackedWidget(Dialog)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.verticalLayout = QVBoxLayout(self.page)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_message = QLabel(self.page)
        self.label_message.setObjectName(u"label_message")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(True)
        self.label_message.setFont(font)

        self.verticalLayout.addWidget(self.label_message)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.label = QLabel(self.page)
        self.label.setObjectName(u"label")

        self.verticalLayout_6.addWidget(self.label)

        self.comboBox_python_interpreter = QComboBox(self.page)
        self.comboBox_python_interpreter.setObjectName(u"comboBox_python_interpreter")
        self.comboBox_python_interpreter.setStyleSheet(u"QComboBox[invalid=\"true\"] {color: red;}")

        self.verticalLayout_6.addWidget(self.comboBox_python_interpreter)


        self.verticalLayout.addLayout(self.verticalLayout_6)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.pushButton_make_kernel = QPushButton(self.page)
        self.pushButton_make_kernel.setObjectName(u"pushButton_make_kernel")
        icon = QIcon()
        icon.addFile(u":/symbols/Jupyter-logo.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_make_kernel.setIcon(icon)

        self.horizontalLayout_3.addWidget(self.pushButton_make_kernel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.verticalLayout_2 = QVBoxLayout(self.page_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_status = QLabel(self.page_2)
        self.label_status.setObjectName(u"label_status")
        self.label_status.setFont(font)

        self.verticalLayout_2.addWidget(self.label_status)

        self.progressBar = QProgressBar(self.page_2)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.verticalLayout_2.addWidget(self.progressBar)

        self.label_in_progress_msg = QLabel(self.page_2)
        self.label_in_progress_msg.setObjectName(u"label_in_progress_msg")

        self.verticalLayout_2.addWidget(self.label_in_progress_msg)

        self.textBrowser = QTextBrowser(self.page_2)
        self.textBrowser.setObjectName(u"textBrowser")

        self.verticalLayout_2.addWidget(self.textBrowser)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.verticalLayout_4 = QVBoxLayout(self.page_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_success_icon = QLabel(self.page_3)
        self.label_success_icon.setObjectName(u"label_success_icon")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_success_icon.sizePolicy().hasHeightForWidth())
        self.label_success_icon.setSizePolicy(sizePolicy)
        self.label_success_icon.setMinimumSize(QSize(16, 16))
        self.label_success_icon.setMaximumSize(QSize(16, 16))
        self.label_success_icon.setPixmap(QPixmap(u":/icons/menu_icons/check_green.svg"))
        self.label_success_icon.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.label_success_icon)

        self.label_success_status = QLabel(self.page_3)
        self.label_success_status.setObjectName(u"label_success_status")
        self.label_success_status.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_success_status)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_4 = QLabel(self.page_3)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_5.addWidget(self.label_4)

        self.label_interpreter = QLabel(self.page_3)
        self.label_interpreter.setObjectName(u"label_interpreter")

        self.verticalLayout_5.addWidget(self.label_interpreter)


        self.verticalLayout_4.addLayout(self.verticalLayout_5)

        self.stackedWidget.addWidget(self.page_3)

        self.verticalLayout_3.addWidget(self.stackedWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_5)

        self.pushButton_close = QPushButton(Dialog)
        self.pushButton_close.setObjectName(u"pushButton_close")

        self.horizontalLayout.addWidget(self.pushButton_close)


        self.verticalLayout_3.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Python Kernel Manager", None))
        self.label_message.setText(QCoreApplication.translate("Dialog", u"Configuration", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Interpreter", None))
        self.pushButton_make_kernel.setText(QCoreApplication.translate("Dialog", u"Make kernel", None))
        self.label_status.setText(QCoreApplication.translate("Dialog", u"Creating kernel", None))
        self.label_in_progress_msg.setText(QCoreApplication.translate("Dialog", u"This operation may take up to 5 minutes. Please be patient.", None))
        self.label_success_icon.setText("")
        self.label_success_status.setText(QCoreApplication.translate("Dialog", u"Kernel created successfully!", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Interpreter", None))
        self.label_interpreter.setText(QCoreApplication.translate("Dialog", u"python.exe", None))
        self.pushButton_close.setText(QCoreApplication.translate("Dialog", u"Close", None))
    # retranslateUi

