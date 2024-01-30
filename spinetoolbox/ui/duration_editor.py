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
## Form generated from reading UI file 'duration_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_DurationEditor(object):
    def setupUi(self, DurationEditor):
        if not DurationEditor.objectName():
            DurationEditor.setObjectName(u"DurationEditor")
        DurationEditor.resize(400, 300)
        self.verticalLayout_2 = QVBoxLayout(DurationEditor)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.layout = QFormLayout()
        self.layout.setObjectName(u"layout")
        self.duration_edit_label = QLabel(DurationEditor)
        self.duration_edit_label.setObjectName(u"duration_edit_label")

        self.layout.setWidget(0, QFormLayout.LabelRole, self.duration_edit_label)

        self.edit_layout = QVBoxLayout()
        self.edit_layout.setObjectName(u"edit_layout")
        self.duration_edit = QLineEdit(DurationEditor)
        self.duration_edit.setObjectName(u"duration_edit")

        self.edit_layout.addWidget(self.duration_edit)

        self.units_hint = QLabel(DurationEditor)
        self.units_hint.setObjectName(u"units_hint")

        self.edit_layout.addWidget(self.units_hint)


        self.layout.setLayout(0, QFormLayout.FieldRole, self.edit_layout)


        self.verticalLayout_2.addLayout(self.layout)


        self.retranslateUi(DurationEditor)

        QMetaObject.connectSlotsByName(DurationEditor)
    # setupUi

    def retranslateUi(self, DurationEditor):
        DurationEditor.setWindowTitle(QCoreApplication.translate("DurationEditor", u"Form", None))
        self.duration_edit_label.setText(QCoreApplication.translate("DurationEditor", u"Duration", None))
        self.units_hint.setText(QCoreApplication.translate("DurationEditor", u"Units: s, m, h, D, M, Y", None))
    # retranslateUi

