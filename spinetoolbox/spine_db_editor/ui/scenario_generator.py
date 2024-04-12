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
## Form generated from reading UI file 'scenario_generator.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QComboBox, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(451, 463)
        self.accept_action = QAction(Form)
        self.accept_action.setObjectName(u"accept_action")
        self.reject_action = QAction(Form)
        self.reject_action.setObjectName(u"reject_action")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.scenario_prefix_label = QLabel(Form)
        self.scenario_prefix_label.setObjectName(u"scenario_prefix_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.scenario_prefix_label)

        self.scenario_prefix_edit = QLineEdit(Form)
        self.scenario_prefix_edit.setObjectName(u"scenario_prefix_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.scenario_prefix_edit)

        self.operation_label = QLabel(Form)
        self.operation_label.setObjectName(u"operation_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.operation_label)

        self.operation_combo_box = QComboBox(Form)
        self.operation_combo_box.setObjectName(u"operation_combo_box")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.operation_combo_box)

        self.use_base_alternative_check_box = QCheckBox(Form)
        self.use_base_alternative_check_box.setObjectName(u"use_base_alternative_check_box")
        self.use_base_alternative_check_box.setChecked(True)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.use_base_alternative_check_box)

        self.base_alternative_combo_box = QComboBox(Form)
        self.base_alternative_combo_box.setObjectName(u"base_alternative_combo_box")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.base_alternative_combo_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.groupBox = QGroupBox(Form)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.alternative_list = QListWidget(self.groupBox)
        self.alternative_list.setObjectName(u"alternative_list")
        self.alternative_list.setDragEnabled(True)
        self.alternative_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.alternative_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.horizontalLayout.addWidget(self.alternative_list)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.groupBox)

        self.button_box = QDialogButtonBox(Form)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.accept_action.setText(QCoreApplication.translate("Form", u"OK", None))
#if QT_CONFIG(shortcut)
        self.accept_action.setShortcut(QCoreApplication.translate("Form", u"Ctrl+Return", None))
#endif // QT_CONFIG(shortcut)
        self.reject_action.setText(QCoreApplication.translate("Form", u"Cancel", None))
#if QT_CONFIG(shortcut)
        self.reject_action.setShortcut(QCoreApplication.translate("Form", u"Esc", None))
#endif // QT_CONFIG(shortcut)
        self.scenario_prefix_label.setText(QCoreApplication.translate("Form", u"Scenario name prefix:", None))
#if QT_CONFIG(tooltip)
        self.scenario_prefix_edit.setToolTip(QCoreApplication.translate("Form", u"Generate scenario names will have this prefix appended by a number.", None))
#endif // QT_CONFIG(tooltip)
        self.scenario_prefix_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Enter scenario name prefix here...", None))
        self.operation_label.setText(QCoreApplication.translate("Form", u"Operation:", None))
#if QT_CONFIG(tooltip)
        self.use_base_alternative_check_box.setToolTip(QCoreApplication.translate("Form", u"When checked, selected base alternative is added to all scenarios.", None))
#endif // QT_CONFIG(tooltip)
        self.use_base_alternative_check_box.setText(QCoreApplication.translate("Form", u"Use base alternative:", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Alternatives by rank", None))
#if QT_CONFIG(tooltip)
        self.alternative_list.setToolTip(QCoreApplication.translate("Form", u"Alternatives at bottom have priority. Drag and drop to reorder the list.", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

