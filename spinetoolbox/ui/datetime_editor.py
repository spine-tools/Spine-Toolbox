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
## Form generated from reading UI file 'datetime_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QDateTimeEdit, QFormLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DatetimeEditor(object):
    def setupUi(self, DatetimeEditor):
        if not DatetimeEditor.objectName():
            DatetimeEditor.setObjectName(u"DatetimeEditor")
        DatetimeEditor.resize(400, 300)
        self.verticalLayout = QVBoxLayout(DatetimeEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.layout = QFormLayout()
        self.layout.setObjectName(u"layout")
        self.datetime_edit_label = QLabel(DatetimeEditor)
        self.datetime_edit_label.setObjectName(u"datetime_edit_label")

        self.layout.setWidget(0, QFormLayout.LabelRole, self.datetime_edit_label)

        self.edit_layout = QVBoxLayout()
        self.edit_layout.setObjectName(u"edit_layout")
        self.datetime_edit = QDateTimeEdit(DatetimeEditor)
        self.datetime_edit.setObjectName(u"datetime_edit")
        self.datetime_edit.setCalendarPopup(True)

        self.edit_layout.addWidget(self.datetime_edit)

        self.format_label = QLabel(DatetimeEditor)
        self.format_label.setObjectName(u"format_label")

        self.edit_layout.addWidget(self.format_label)


        self.layout.setLayout(0, QFormLayout.FieldRole, self.edit_layout)


        self.verticalLayout.addLayout(self.layout)


        self.retranslateUi(DatetimeEditor)

        QMetaObject.connectSlotsByName(DatetimeEditor)
    # setupUi

    def retranslateUi(self, DatetimeEditor):
        DatetimeEditor.setWindowTitle(QCoreApplication.translate("DatetimeEditor", u"Form", None))
        self.datetime_edit_label.setText(QCoreApplication.translate("DatetimeEditor", u"Datetime", None))
        self.datetime_edit.setDisplayFormat(QCoreApplication.translate("DatetimeEditor", u"yyyy-MM-ddTHH:mm:ss", None))
        self.format_label.setText(QCoreApplication.translate("DatetimeEditor", u"Format: YYYY--MM-DDThh:mm:ss", None))
    # retranslateUi

