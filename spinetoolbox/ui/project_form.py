# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'project_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.ApplicationModal)
        Form.resize(500, 400)
        Form.setMinimumSize(QSize(500, 400))
        Form.setMaximumSize(QSize(500, 400))
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lineEdit_project_dir = QLineEdit(Form)
        self.lineEdit_project_dir.setObjectName(u"lineEdit_project_dir")
        self.lineEdit_project_dir.setCursor(QCursor(Qt.ArrowCursor))
        self.lineEdit_project_dir.setReadOnly(True)
        self.lineEdit_project_dir.setClearButtonEnabled(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_project_dir)

        self.toolButton_select_project_dir = QToolButton(Form)
        self.toolButton_select_project_dir.setObjectName(u"toolButton_select_project_dir")
        self.toolButton_select_project_dir.setMaximumSize(QSize(22, 22))
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_select_project_dir.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.toolButton_select_project_dir)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.lineEdit_project_name = QLineEdit(Form)
        self.lineEdit_project_name.setObjectName(u"lineEdit_project_name")
        self.lineEdit_project_name.setClearButtonEnabled(True)

        self.verticalLayout.addWidget(self.lineEdit_project_name)

        self.textEdit_description = QTextEdit(Form)
        self.textEdit_description.setObjectName(u"textEdit_description")
        self.textEdit_description.setTabChangesFocus(True)
        self.textEdit_description.setAcceptRichText(False)

        self.verticalLayout.addWidget(self.textEdit_description)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 6, -1, 6)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_ok = QPushButton(Form)
        self.pushButton_ok.setObjectName(u"pushButton_ok")

        self.horizontalLayout.addWidget(self.pushButton_ok)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.pushButton_cancel = QPushButton(Form)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")

        self.horizontalLayout.addWidget(self.pushButton_cancel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.toolButton_select_project_dir, self.lineEdit_project_name)
        QWidget.setTabOrder(self.lineEdit_project_name, self.textEdit_description)
        QWidget.setTabOrder(self.textEdit_description, self.pushButton_ok)
        QWidget.setTabOrder(self.pushButton_ok, self.pushButton_cancel)
        QWidget.setTabOrder(self.pushButton_cancel, self.lineEdit_project_dir)

        self.retranslateUi(Form)

        self.pushButton_ok.setDefault(True)
        self.pushButton_cancel.setDefault(True)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"New Project", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_project_dir.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Project directory</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_project_dir.setPlaceholderText(QCoreApplication.translate("Form", u"Select project directory...", None))
#if QT_CONFIG(tooltip)
        self.toolButton_select_project_dir.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Click here to select a directory for the new project</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_select_project_dir.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_project_name.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Project name (Required)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_project_name.setPlaceholderText(QCoreApplication.translate("Form", u"Type project name here...", None))
#if QT_CONFIG(tooltip)
        self.textEdit_description.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Project description (Optional)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.textEdit_description.setPlaceholderText(QCoreApplication.translate("Form", u"Type project description here...", None))
        self.label.setText(QCoreApplication.translate("Form", u"1. Select project directory", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"2. Type project name and description (optional)", None))
        self.pushButton_ok.setText(QCoreApplication.translate("Form", u"Ok", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("Form", u"Cancel", None))
    # retranslateUi

