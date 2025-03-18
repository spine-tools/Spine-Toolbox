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
## Form generated from reading UI file 'mini_kernel_editor_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QSizePolicy, QSpacerItem, QSplitter, QStackedWidget,
    QTextBrowser, QVBoxLayout, QWidget)
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
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_message = QLabel(self.layoutWidget)
        self.label_message.setObjectName(u"label_message")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.label_message.sizePolicy().hasHeightForWidth())
        self.label_message.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_message.setFont(font)
        self.label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_message.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_message)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.splitter.addWidget(self.layoutWidget)
        self.textBrowser_process = QTextBrowser(self.splitter)
        self.textBrowser_process.setObjectName(u"textBrowser_process")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.textBrowser_process.sizePolicy().hasHeightForWidth())
        self.textBrowser_process.setSizePolicy(sizePolicy1)
        self.splitter.addWidget(self.textBrowser_process)
        self.stackedWidget = QStackedWidget(self.splitter)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
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

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.comboBox_python_interpreter = QComboBox(self.stackedWidgetPage1)
        self.comboBox_python_interpreter.setObjectName(u"comboBox_python_interpreter")

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.comboBox_python_interpreter)

        self.label = QLabel(self.stackedWidgetPage1)
        self.label.setObjectName(u"label")

        self.formLayout_3.setWidget(5, QFormLayout.LabelRole, self.label)

        self.lineEdit_python_kernel_name_prefix = QLineEdit(self.stackedWidgetPage1)
        self.lineEdit_python_kernel_name_prefix.setObjectName(u"lineEdit_python_kernel_name_prefix")
        self.lineEdit_python_kernel_name_prefix.setEnabled(True)

        self.formLayout_3.setWidget(5, QFormLayout.FieldRole, self.lineEdit_python_kernel_name_prefix)

        self.label_python_kernel_name = QLabel(self.stackedWidgetPage1)
        self.label_python_kernel_name.setObjectName(u"label_python_kernel_name")

        self.formLayout_3.setWidget(6, QFormLayout.FieldRole, self.label_python_kernel_name)

        self.stackedWidget.addWidget(self.stackedWidgetPage1)
        self.stackedWidgetPage2 = QWidget()
        self.stackedWidgetPage2.setObjectName(u"stackedWidgetPage2")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidgetPage2.sizePolicy().hasHeightForWidth())
        self.stackedWidgetPage2.setSizePolicy(sizePolicy3)
        self.formLayout_4 = QFormLayout(self.stackedWidgetPage2)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.label_6 = QLabel(self.stackedWidgetPage2)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_6)

        self.comboBox_julia_executable = QComboBox(self.stackedWidgetPage2)
        self.comboBox_julia_executable.setObjectName(u"comboBox_julia_executable")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.comboBox_julia_executable)

        self.label_9 = QLabel(self.stackedWidgetPage2)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.label_9)

        self.comboBox_julia_project = QComboBox(self.stackedWidgetPage2)
        self.comboBox_julia_project.setObjectName(u"comboBox_julia_project")

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.comboBox_julia_project)

        self.label_2 = QLabel(self.stackedWidgetPage2)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.lineEdit_julia_kernel_name_prefix = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_kernel_name_prefix.setObjectName(u"lineEdit_julia_kernel_name_prefix")
        self.lineEdit_julia_kernel_name_prefix.setEnabled(True)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.lineEdit_julia_kernel_name_prefix)

        self.label_julia_kernel_name = QLabel(self.stackedWidgetPage2)
        self.label_julia_kernel_name.setObjectName(u"label_julia_kernel_name")

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.label_julia_kernel_name)

        self.stackedWidget.addWidget(self.stackedWidgetPage2)
        self.splitter.addWidget(self.stackedWidget)

        self.verticalLayout_2.addWidget(self.splitter)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Close)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout_2.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.textBrowser_process, self.comboBox_python_interpreter)
        QWidget.setTabOrder(self.comboBox_python_interpreter, self.lineEdit_python_kernel_name_prefix)
        QWidget.setTabOrder(self.lineEdit_python_kernel_name_prefix, self.comboBox_julia_executable)
        QWidget.setTabOrder(self.comboBox_julia_executable, self.comboBox_julia_project)
        QWidget.setTabOrder(self.comboBox_julia_project, self.lineEdit_julia_kernel_name_prefix)

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
        self.label.setText(QCoreApplication.translate("Dialog", u"Kernel name prefix", None))
        self.label_python_kernel_name.setText(QCoreApplication.translate("Dialog", u"Kernel name", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Executable", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Project", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Kernel name prefix", None))
        self.label_julia_kernel_name.setText(QCoreApplication.translate("Dialog", u"Kernel name", None))
    # retranslateUi

