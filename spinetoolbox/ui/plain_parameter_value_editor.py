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
## Form generated from reading UI file 'plain_parameter_value_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QLineEdit,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PlainParameterValueEditor(object):
    def setupUi(self, PlainParameterValueEditor):
        if not PlainParameterValueEditor.objectName():
            PlainParameterValueEditor.setObjectName(u"PlainParameterValueEditor")
        PlainParameterValueEditor.resize(518, 225)
        self.verticalLayout = QVBoxLayout(PlainParameterValueEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(PlainParameterValueEditor)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setCheckable(False)
        self.formLayout = QFormLayout(self.groupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.radioButton_number_or_string = QRadioButton(self.groupBox)
        self.radioButton_number_or_string.setObjectName(u"radioButton_number_or_string")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.radioButton_number_or_string)

        self.value_edit = QLineEdit(self.groupBox)
        self.value_edit.setObjectName(u"value_edit")
        self.value_edit.setEnabled(False)
        self.value_edit.setMaximumSize(QSize(16777215, 23))

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.value_edit)

        self.radioButton_string = QRadioButton(self.groupBox)
        self.radioButton_string.setObjectName(u"radioButton_string")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.radioButton_string)

        self.radioButton_true = QRadioButton(self.groupBox)
        self.radioButton_true.setObjectName(u"radioButton_true")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.radioButton_true)

        self.radioButton_false = QRadioButton(self.groupBox)
        self.radioButton_false.setObjectName(u"radioButton_false")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.radioButton_false)

        self.radioButton_null = QRadioButton(self.groupBox)
        self.radioButton_null.setObjectName(u"radioButton_null")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.radioButton_null)

        self.string_value_edit = QLineEdit(self.groupBox)
        self.string_value_edit.setObjectName(u"string_value_edit")
        self.string_value_edit.setEnabled(False)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.string_value_edit)


        self.verticalLayout.addWidget(self.groupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(PlainParameterValueEditor)

        QMetaObject.connectSlotsByName(PlainParameterValueEditor)
    # setupUi

    def retranslateUi(self, PlainParameterValueEditor):
        PlainParameterValueEditor.setWindowTitle(QCoreApplication.translate("PlainParameterValueEditor", u"Form", None))
        self.groupBox.setTitle("")
        self.radioButton_number_or_string.setText(QCoreApplication.translate("PlainParameterValueEditor", u"number or string:", None))
        self.radioButton_string.setText(QCoreApplication.translate("PlainParameterValueEditor", u"string:", None))
        self.radioButton_true.setText(QCoreApplication.translate("PlainParameterValueEditor", u"true", None))
        self.radioButton_false.setText(QCoreApplication.translate("PlainParameterValueEditor", u"false", None))
        self.radioButton_null.setText(QCoreApplication.translate("PlainParameterValueEditor", u"null", None))
    # retranslateUi

