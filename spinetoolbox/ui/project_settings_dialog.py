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
## Form generated from reading UI file 'project_settings_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.description_text_edit = QPlainTextEdit(Form)
        self.description_text_edit.setObjectName(u"description_text_edit")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.description_text_edit)

        self.enable_execute_all_check_box = QCheckBox(Form)
        self.enable_execute_all_check_box.setObjectName(u"enable_execute_all_check_box")
        self.enable_execute_all_check_box.setChecked(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.enable_execute_all_check_box)

        self.name_line_edit = QLineEdit(Form)
        self.name_line_edit.setObjectName(u"name_line_edit")
        self.name_line_edit.setEnabled(False)
        self.name_line_edit.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.name_line_edit)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.item_directory_size_label = QLabel(Form)
        self.item_directory_size_label.setObjectName(u"item_directory_size_label")

        self.horizontalLayout.addWidget(self.item_directory_size_label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.delete_item_files_button = QPushButton(Form)
        self.delete_item_files_button.setObjectName(u"delete_item_files_button")

        self.horizontalLayout.addWidget(self.delete_item_files_button)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.button_box = QDialogButtonBox(Form)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"Name:", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Description:", None))
        self.enable_execute_all_check_box.setText(QCoreApplication.translate("Form", u"Enable \"Execute All\" button", None))
        self.item_directory_size_label.setText(QCoreApplication.translate("Form", u"Calculating item directory sizes...", None))
        self.delete_item_files_button.setText(QCoreApplication.translate("Form", u"Delete files...", None))
    # retranslateUi

