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
## Form generated from reading UI file 'parameter_type_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(278, 178)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.select_all_button = QPushButton(Form)
        self.select_all_button.setObjectName(u"select_all_button")

        self.horizontalLayout.addWidget(self.select_all_button)

        self.clear_all_button = QPushButton(Form)
        self.clear_all_button.setObjectName(u"clear_all_button")

        self.horizontalLayout.addWidget(self.clear_all_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.duration_check_box = QCheckBox(Form)
        self.duration_check_box.setObjectName(u"duration_check_box")

        self.gridLayout.addWidget(self.duration_check_box, 1, 1, 1, 1)

        self.bool_check_box = QCheckBox(Form)
        self.bool_check_box.setObjectName(u"bool_check_box")

        self.gridLayout.addWidget(self.bool_check_box, 0, 2, 1, 1)

        self.float_check_box = QCheckBox(Form)
        self.float_check_box.setObjectName(u"float_check_box")

        self.gridLayout.addWidget(self.float_check_box, 0, 0, 1, 1)

        self.str_check_box = QCheckBox(Form)
        self.str_check_box.setObjectName(u"str_check_box")

        self.gridLayout.addWidget(self.str_check_box, 0, 1, 1, 1)

        self.date_time_check_box = QCheckBox(Form)
        self.date_time_check_box.setObjectName(u"date_time_check_box")

        self.gridLayout.addWidget(self.date_time_check_box, 1, 0, 1, 1)

        self.array_check_box = QCheckBox(Form)
        self.array_check_box.setObjectName(u"array_check_box")

        self.gridLayout.addWidget(self.array_check_box, 2, 0, 1, 1)

        self.time_pattern_check_box = QCheckBox(Form)
        self.time_pattern_check_box.setObjectName(u"time_pattern_check_box")

        self.gridLayout.addWidget(self.time_pattern_check_box, 2, 1, 1, 1)

        self.time_series_check_box = QCheckBox(Form)
        self.time_series_check_box.setObjectName(u"time_series_check_box")

        self.gridLayout.addWidget(self.time_series_check_box, 2, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.map_check_box = QCheckBox(Form)
        self.map_check_box.setObjectName(u"map_check_box")

        self.horizontalLayout_3.addWidget(self.map_check_box)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, -1, 0, -1)
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.map_rank_line_edit = QLineEdit(Form)
        self.map_rank_line_edit.setObjectName(u"map_rank_line_edit")

        self.horizontalLayout_2.addWidget(self.map_rank_line_edit)


        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        QWidget.setTabOrder(self.select_all_button, self.clear_all_button)
        QWidget.setTabOrder(self.clear_all_button, self.float_check_box)
        QWidget.setTabOrder(self.float_check_box, self.str_check_box)
        QWidget.setTabOrder(self.str_check_box, self.bool_check_box)
        QWidget.setTabOrder(self.bool_check_box, self.date_time_check_box)
        QWidget.setTabOrder(self.date_time_check_box, self.duration_check_box)
        QWidget.setTabOrder(self.duration_check_box, self.array_check_box)
        QWidget.setTabOrder(self.array_check_box, self.time_pattern_check_box)
        QWidget.setTabOrder(self.time_pattern_check_box, self.time_series_check_box)
        QWidget.setTabOrder(self.time_series_check_box, self.map_check_box)
        QWidget.setTabOrder(self.map_check_box, self.map_rank_line_edit)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.select_all_button.setText(QCoreApplication.translate("Form", u"Select &all", None))
        self.clear_all_button.setText(QCoreApplication.translate("Form", u"&Clear all", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"No selection means any type is valid.", None))
        self.duration_check_box.setText(QCoreApplication.translate("Form", u"d&uration", None))
        self.bool_check_box.setText(QCoreApplication.translate("Form", u"&bool", None))
        self.float_check_box.setText(QCoreApplication.translate("Form", u"&float", None))
        self.str_check_box.setText(QCoreApplication.translate("Form", u"&str", None))
        self.date_time_check_box.setText(QCoreApplication.translate("Form", u"&date_time", None))
        self.array_check_box.setText(QCoreApplication.translate("Form", u"a&rray", None))
        self.time_pattern_check_box.setText(QCoreApplication.translate("Form", u"time_&pattern", None))
        self.time_series_check_box.setText(QCoreApplication.translate("Form", u"&time_series", None))
        self.map_check_box.setText(QCoreApplication.translate("Form", u"&map", None))
        self.label.setText(QCoreApplication.translate("Form", u"Ranks:", None))
#if QT_CONFIG(tooltip)
        self.map_rank_line_edit.setToolTip(QCoreApplication.translate("Form", u"A comma separated list of valid ranks.", None))
#endif // QT_CONFIG(tooltip)
        self.map_rank_line_edit.setText(QCoreApplication.translate("Form", u"1", None))
    # retranslateUi

