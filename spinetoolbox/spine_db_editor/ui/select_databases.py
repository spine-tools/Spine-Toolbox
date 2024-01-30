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
## Form generated from reading UI file 'select_databases.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.databases_group_box = QGroupBox(Form)
        self.databases_group_box.setObjectName(u"databases_group_box")
        self.verticalLayout_2 = QVBoxLayout(self.databases_group_box)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.databases_grid_layout = QGridLayout()
        self.databases_grid_layout.setObjectName(u"databases_grid_layout")

        self.verticalLayout_2.addLayout(self.databases_grid_layout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.select_all_button = QPushButton(self.databases_group_box)
        self.select_all_button.setObjectName(u"select_all_button")

        self.horizontalLayout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton(self.databases_group_box)
        self.deselect_all_button.setObjectName(u"deselect_all_button")

        self.horizontalLayout.addWidget(self.deselect_all_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.databases_group_box)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.databases_group_box.setTitle(QCoreApplication.translate("Form", u"Databases", None))
#if QT_CONFIG(tooltip)
        self.select_all_button.setToolTip(QCoreApplication.translate("Form", u"Select all databases.", None))
#endif // QT_CONFIG(tooltip)
        self.select_all_button.setText(QCoreApplication.translate("Form", u"Select all", None))
#if QT_CONFIG(tooltip)
        self.deselect_all_button.setToolTip(QCoreApplication.translate("Form", u"Deselect all databases.", None))
#endif // QT_CONFIG(tooltip)
        self.deselect_all_button.setText(QCoreApplication.translate("Form", u"Deselect all", None))
    # retranslateUi

