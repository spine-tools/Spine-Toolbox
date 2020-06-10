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
## Form generated from reading UI file 'plain_parameter_value_editor.ui'
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


class Ui_PlainParameterValueEditor(object):
    def setupUi(self, PlainParameterValueEditor):
        if not PlainParameterValueEditor.objectName():
            PlainParameterValueEditor.setObjectName(u"PlainParameterValueEditor")
        PlainParameterValueEditor.resize(518, 224)
        self.verticalLayout = QVBoxLayout(PlainParameterValueEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(PlainParameterValueEditor)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setCheckable(False)
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.value_edit = QLineEdit(self.groupBox)
        self.value_edit.setObjectName(u"value_edit")
        self.value_edit.setMaximumSize(QSize(16777215, 23))

        self.gridLayout.addWidget(self.value_edit, 0, 1, 1, 1)

        self.radioButton_number_or_string = QRadioButton(self.groupBox)
        self.radioButton_number_or_string.setObjectName(u"radioButton_number_or_string")

        self.gridLayout.addWidget(self.radioButton_number_or_string, 0, 0, 1, 1)

        self.radioButton_true = QRadioButton(self.groupBox)
        self.radioButton_true.setObjectName(u"radioButton_true")

        self.gridLayout.addWidget(self.radioButton_true, 1, 0, 1, 1)

        self.radioButton_false = QRadioButton(self.groupBox)
        self.radioButton_false.setObjectName(u"radioButton_false")

        self.gridLayout.addWidget(self.radioButton_false, 2, 0, 1, 1)

        self.radioButton_null = QRadioButton(self.groupBox)
        self.radioButton_null.setObjectName(u"radioButton_null")

        self.gridLayout.addWidget(self.radioButton_null, 3, 0, 1, 1)


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
        self.radioButton_true.setText(QCoreApplication.translate("PlainParameterValueEditor", u"true", None))
        self.radioButton_false.setText(QCoreApplication.translate("PlainParameterValueEditor", u"false", None))
        self.radioButton_null.setText(QCoreApplication.translate("PlainParameterValueEditor", u"null", None))
    # retranslateUi

