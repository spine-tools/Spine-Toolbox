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
## Form generated from reading UI file 'select_database_items.ui'
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
        Form.resize(409, 300)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(Form)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.item_grid_layout = QGridLayout()
        self.item_grid_layout.setObjectName(u"item_grid_layout")

        self.verticalLayout_2.addLayout(self.item_grid_layout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.select_all_button = QPushButton(self.groupBox)
        self.select_all_button.setObjectName(u"select_all_button")

        self.horizontalLayout.addWidget(self.select_all_button)

        self.select_data_items_button = QPushButton(self.groupBox)
        self.select_data_items_button.setObjectName(u"select_data_items_button")

        self.horizontalLayout.addWidget(self.select_data_items_button)

        self.select_scenario_items_button = QPushButton(self.groupBox)
        self.select_scenario_items_button.setObjectName(u"select_scenario_items_button")

        self.horizontalLayout.addWidget(self.select_scenario_items_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.deselect_all_button = QPushButton(self.groupBox)
        self.deselect_all_button.setObjectName(u"deselect_all_button")

        self.horizontalLayout_2.addWidget(self.deselect_all_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addWidget(self.groupBox)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Items", None))
#if QT_CONFIG(tooltip)
        self.select_all_button.setToolTip(QCoreApplication.translate("Form", u"Selects all items.", None))
#endif // QT_CONFIG(tooltip)
        self.select_all_button.setText(QCoreApplication.translate("Form", u"Select all", None))
#if QT_CONFIG(tooltip)
        self.select_data_items_button.setToolTip(QCoreApplication.translate("Form", u"Selects the entity and parameter value items.", None))
#endif // QT_CONFIG(tooltip)
        self.select_data_items_button.setText(QCoreApplication.translate("Form", u"Select entity and value items", None))
#if QT_CONFIG(tooltip)
        self.select_scenario_items_button.setToolTip(QCoreApplication.translate("Form", u"Selects the scenario and alternative items.", None))
#endif // QT_CONFIG(tooltip)
        self.select_scenario_items_button.setText(QCoreApplication.translate("Form", u"Select scenario items", None))
#if QT_CONFIG(tooltip)
        self.deselect_all_button.setToolTip(QCoreApplication.translate("Form", u"Deselects all items.", None))
#endif // QT_CONFIG(tooltip)
        self.deselect_all_button.setText(QCoreApplication.translate("Form", u"Deselect all", None))
    # retranslateUi

