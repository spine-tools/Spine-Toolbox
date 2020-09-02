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
## Form generated from reading UI file 'parameter_index_settings_window.ui'
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


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.WindowModal)
        Form.resize(784, 422)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_stack = QStackedWidget(Form)
        self.widget_stack.setObjectName(u"widget_stack")
        self.settings_page = QWidget()
        self.settings_page.setObjectName(u"settings_page")
        self.horizontalLayout_2 = QHBoxLayout(self.settings_page)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.splitter = QSplitter(self.settings_page)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.settings_area = QScrollArea(self.splitter)
        self.settings_area.setObjectName(u"settings_area")
        self.settings_area.setWidgetResizable(True)
        self.settings_area_contents = QWidget()
        self.settings_area_contents.setObjectName(u"settings_area_contents")
        self.settings_area_contents.setGeometry(QRect(0, 0, 69, 355))
        self.verticalLayout_3 = QVBoxLayout(self.settings_area_contents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.settings_area_layout = QVBoxLayout()
        self.settings_area_layout.setObjectName(u"settings_area_layout")

        self.verticalLayout_3.addLayout(self.settings_area_layout)

        self.settings_area.setWidget(self.settings_area_contents)
        self.splitter.addWidget(self.settings_area)
        self.additiona_indexing_box = QGroupBox(self.splitter)
        self.additiona_indexing_box.setObjectName(u"additiona_indexing_box")
        self.verticalLayout_5 = QVBoxLayout(self.additiona_indexing_box)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.add_domain_button = QPushButton(self.additiona_indexing_box)
        self.add_domain_button.setObjectName(u"add_domain_button")

        self.horizontalLayout_3.addWidget(self.add_domain_button)

        self.remove_domain_button = QPushButton(self.additiona_indexing_box)
        self.remove_domain_button.setObjectName(u"remove_domain_button")

        self.horizontalLayout_3.addWidget(self.remove_domain_button)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.additional_domains_list_view = QListView(self.additiona_indexing_box)
        self.additional_domains_list_view.setObjectName(u"additional_domains_list_view")
        self.additional_domains_list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout.addWidget(self.additional_domains_list_view)


        self.verticalLayout_5.addLayout(self.verticalLayout)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_2 = QLabel(self.additiona_indexing_box)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.description_edit = QLineEdit(self.additiona_indexing_box)
        self.description_edit.setObjectName(u"description_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.description_edit)

        self.use_expression_radio_button = QRadioButton(self.additiona_indexing_box)
        self.use_expression_radio_button.setObjectName(u"use_expression_radio_button")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.use_expression_radio_button)

        self.expression_edit = QLineEdit(self.additiona_indexing_box)
        self.expression_edit.setObjectName(u"expression_edit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.expression_edit)

        self.extract_from_radio_button = QRadioButton(self.additiona_indexing_box)
        self.extract_from_radio_button.setObjectName(u"extract_from_radio_button")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.extract_from_radio_button)

        self.extract_from_combo_box = QComboBox(self.additiona_indexing_box)
        self.extract_from_combo_box.setObjectName(u"extract_from_combo_box")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.extract_from_combo_box)

        self.label_3 = QLabel(self.additiona_indexing_box)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.length_spin_box = QSpinBox(self.additiona_indexing_box)
        self.length_spin_box.setObjectName(u"length_spin_box")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.length_spin_box)


        self.verticalLayout_5.addLayout(self.formLayout)

        self.splitter.addWidget(self.additiona_indexing_box)

        self.horizontalLayout_2.addWidget(self.splitter)

        self.widget_stack.addWidget(self.settings_page)
        self.empty_message_page = QWidget()
        self.empty_message_page.setObjectName(u"empty_message_page")
        self.verticalLayout_4 = QVBoxLayout(self.empty_message_page)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label = QLabel(self.empty_message_page)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.widget_stack.addWidget(self.empty_message_page)

        self.verticalLayout_2.addWidget(self.widget_stack)

        self.button_box = QDialogButtonBox(Form)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_2.addWidget(self.button_box)


        self.retranslateUi(Form)

        self.widget_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Gdx Parameter Indexing Settings", None))
        self.additiona_indexing_box.setTitle(QCoreApplication.translate("Form", u"Additional indexing domains", None))
        self.add_domain_button.setText(QCoreApplication.translate("Form", u"Add", None))
        self.remove_domain_button.setText(QCoreApplication.translate("Form", u"Remove", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Description:", None))
        self.use_expression_radio_button.setText(QCoreApplication.translate("Form", u"Expression:", None))
        self.extract_from_radio_button.setText(QCoreApplication.translate("Form", u"Extract from:", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Length:", None))
        self.label.setText(QCoreApplication.translate("Form", u"No indexed parameters found in this database.", None))
    # retranslateUi

