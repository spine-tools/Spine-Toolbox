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
## Form generated from reading UI file 'mini_kernel_editor_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QSizePolicy,
    QSpacerItem, QSplitter, QStackedWidget, QTextBrowser,
    QVBoxLayout, QWidget)
from spinetoolbox import resources_icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(735, 432)
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.widget = QWidget(self.splitter)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_message = QLabel(self.widget)
        self.label_message.setObjectName(u"label_message")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.label_message.sizePolicy().hasHeightForWidth())
        self.label_message.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_message.setFont(font)
        self.label_message.setAlignment(Qt.AlignCenter)
        self.label_message.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_message)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.splitter.addWidget(self.widget)
        self.textBrowser_process = QTextBrowser(self.splitter)
        self.textBrowser_process.setObjectName(u"textBrowser_process")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.textBrowser_process.sizePolicy().hasHeightForWidth())
        self.textBrowser_process.setSizePolicy(sizePolicy1)
        self.splitter.addWidget(self.textBrowser_process)

        self.verticalLayout_2.addWidget(self.splitter)

        self.stackedWidget = QStackedWidget(Dialog)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy2)
        self.stackedWidgetPage1 = QWidget()
        self.stackedWidgetPage1.setObjectName(u"stackedWidgetPage1")
        self.formLayout_3 = QFormLayout(self.stackedWidgetPage1)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_3 = QLabel(self.stackedWidgetPage1)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.lineEdit_python_interpreter = QLineEdit(self.stackedWidgetPage1)
        self.lineEdit_python_interpreter.setObjectName(u"lineEdit_python_interpreter")
        self.lineEdit_python_interpreter.setEnabled(True)
        self.lineEdit_python_interpreter.setCursor(QCursor(Qt.IBeamCursor))
        self.lineEdit_python_interpreter.setFocusPolicy(Qt.StrongFocus)
        self.lineEdit_python_interpreter.setReadOnly(True)
        self.lineEdit_python_interpreter.setClearButtonEnabled(False)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.lineEdit_python_interpreter)

        self.stackedWidget.addWidget(self.stackedWidgetPage1)
        self.stackedWidgetPage2 = QWidget()
        self.stackedWidgetPage2.setObjectName(u"stackedWidgetPage2")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidgetPage2.sizePolicy().hasHeightForWidth())
        self.stackedWidgetPage2.setSizePolicy(sizePolicy3)
        self.formLayout_4 = QFormLayout(self.stackedWidgetPage2)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_6 = QLabel(self.stackedWidgetPage2)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_6)

        self.lineEdit_julia_executable = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_executable.setObjectName(u"lineEdit_julia_executable")
        self.lineEdit_julia_executable.setFocusPolicy(Qt.StrongFocus)
        self.lineEdit_julia_executable.setFrame(True)
        self.lineEdit_julia_executable.setReadOnly(True)
        self.lineEdit_julia_executable.setClearButtonEnabled(False)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.lineEdit_julia_executable)

        self.label_9 = QLabel(self.stackedWidgetPage2)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_9)

        self.lineEdit_julia_project = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_project.setObjectName(u"lineEdit_julia_project")
        self.lineEdit_julia_project.setReadOnly(True)
        self.lineEdit_julia_project.setClearButtonEnabled(False)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.lineEdit_julia_project)

        self.stackedWidget.addWidget(self.stackedWidgetPage2)

        self.verticalLayout_2.addWidget(self.stackedWidget)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Kernel specification editor", None))
        self.label_message.setText(QCoreApplication.translate("Dialog", u"Finalizing tool configuration...", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Interpreter", None))
        self.lineEdit_python_interpreter.setPlaceholderText("")
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Executable", None))
        self.lineEdit_julia_executable.setPlaceholderText("")
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Project", None))
        self.lineEdit_julia_project.setPlaceholderText("")
    # retranslateUi

