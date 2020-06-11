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
## Form generated from reading UI file 'parameter_index_settings.ui'
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
        Form.resize(588, 433)
        self.verticalLayout_5 = QVBoxLayout(Form)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.box = QGroupBox(Form)
        self.box.setObjectName(u"box")
        self.verticalLayout_3 = QVBoxLayout(self.box)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.message_label = QLabel(self.box)
        self.message_label.setObjectName(u"message_label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_label.sizePolicy().hasHeightForWidth())
        self.message_label.setSizePolicy(sizePolicy)
        self.message_label.setTextFormat(Qt.RichText)

        self.verticalLayout_3.addWidget(self.message_label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(self.box)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.indexing_domains_label = QLabel(self.box)
        self.indexing_domains_label.setObjectName(u"indexing_domains_label")
        self.indexing_domains_label.setTextFormat(Qt.RichText)

        self.horizontalLayout_2.addWidget(self.indexing_domains_label)

        self.move_domain_left_button = QPushButton(self.box)
        self.move_domain_left_button.setObjectName(u"move_domain_left_button")

        self.horizontalLayout_2.addWidget(self.move_domain_left_button)

        self.move_domain_right_button = QPushButton(self.box)
        self.move_domain_right_button.setObjectName(u"move_domain_right_button")

        self.horizontalLayout_2.addWidget(self.move_domain_right_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.splitter = QSplitter(self.box)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.verticalLayoutWidget_3 = QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayout_4 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.use_existing_domain_radio_button = QRadioButton(self.verticalLayoutWidget_3)
        self.use_existing_domain_radio_button.setObjectName(u"use_existing_domain_radio_button")
        self.use_existing_domain_radio_button.setChecked(True)

        self.verticalLayout_6.addWidget(self.use_existing_domain_radio_button)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.existing_domains_combo = QComboBox(self.verticalLayoutWidget_3)
        self.existing_domains_combo.setObjectName(u"existing_domains_combo")

        self.horizontalLayout.addWidget(self.existing_domains_combo)


        self.verticalLayout_6.addLayout(self.horizontalLayout)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.pick_expression_label = QLabel(self.verticalLayoutWidget_3)
        self.pick_expression_label.setObjectName(u"pick_expression_label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.pick_expression_label)

        self.pick_expression_edit = QLineEdit(self.verticalLayoutWidget_3)
        self.pick_expression_edit.setObjectName(u"pick_expression_edit")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.pick_expression_edit)


        self.verticalLayout_6.addLayout(self.formLayout_3)


        self.verticalLayout_4.addLayout(self.verticalLayout_6)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.create_domain_radio_button = QRadioButton(self.verticalLayoutWidget_3)
        self.create_domain_radio_button.setObjectName(u"create_domain_radio_button")

        self.verticalLayout.addWidget(self.create_domain_radio_button)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.domain_name_label = QLabel(self.verticalLayoutWidget_3)
        self.domain_name_label.setObjectName(u"domain_name_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.domain_name_label)

        self.domain_name_edit = QLineEdit(self.verticalLayoutWidget_3)
        self.domain_name_edit.setObjectName(u"domain_name_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.domain_name_edit)

        self.domain_description_label = QLabel(self.verticalLayoutWidget_3)
        self.domain_description_label.setObjectName(u"domain_description_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.domain_description_label)

        self.domain_description_edit = QLineEdit(self.verticalLayoutWidget_3)
        self.domain_description_edit.setObjectName(u"domain_description_edit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.domain_description_edit)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.generator_expression_label = QLabel(self.verticalLayoutWidget_3)
        self.generator_expression_label.setObjectName(u"generator_expression_label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.generator_expression_label)

        self.generator_expression_edit = QLineEdit(self.verticalLayoutWidget_3)
        self.generator_expression_edit.setObjectName(u"generator_expression_edit")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.generator_expression_edit)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.extract_indexes_button = QPushButton(self.verticalLayoutWidget_3)
        self.extract_indexes_button.setObjectName(u"extract_indexes_button")

        self.verticalLayout_2.addWidget(self.extract_indexes_button)


        self.verticalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout_4.addLayout(self.verticalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.splitter.addWidget(self.verticalLayoutWidget_3)
        self.index_table_view = QTableView(self.splitter)
        self.index_table_view.setObjectName(u"index_table_view")
        self.splitter.addWidget(self.index_table_view)
        self.index_table_view.horizontalHeader().setVisible(True)

        self.verticalLayout_3.addWidget(self.splitter)


        self.verticalLayout_5.addWidget(self.box)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.box.setTitle(QCoreApplication.translate("Form", u"Parameter name", None))
        self.message_label.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.label.setText(QCoreApplication.translate("Form", u"Indexing domains:", None))
        self.indexing_domains_label.setText(QCoreApplication.translate("Form", u"(<b>unnamed</b>)", None))
        self.move_domain_left_button.setText(QCoreApplication.translate("Form", u"Move Left", None))
        self.move_domain_right_button.setText(QCoreApplication.translate("Form", u"Move Right", None))
        self.use_existing_domain_radio_button.setText(QCoreApplication.translate("Form", u"Use existing domain", None))
#if QT_CONFIG(tooltip)
        self.pick_expression_label.setToolTip(QCoreApplication.translate("Form", u"Select rows for which this Python expression evaluates to True. Use <i>i</i> as the row index.", None))
#endif // QT_CONFIG(tooltip)
        self.pick_expression_label.setText(QCoreApplication.translate("Form", u"Label picking expression:", None))
        self.pick_expression_edit.setPlaceholderText("")
        self.create_domain_radio_button.setText(QCoreApplication.translate("Form", u"Create new index domain", None))
        self.domain_name_label.setText(QCoreApplication.translate("Form", u"Domain name:", None))
        self.domain_name_edit.setText("")
        self.domain_name_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Type domain's name here...", None))
        self.domain_description_label.setText(QCoreApplication.translate("Form", u"Description:", None))
        self.domain_description_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Type explanatory text here...", None))
#if QT_CONFIG(tooltip)
        self.generator_expression_label.setToolTip(QCoreApplication.translate("Form", u"Generate index labels from Python expression. Use <i>i</i> as the row number.", None))
#endif // QT_CONFIG(tooltip)
        self.generator_expression_label.setText(QCoreApplication.translate("Form", u"Generator expression:", None))
        self.extract_indexes_button.setText(QCoreApplication.translate("Form", u"Extract index from parameter", None))
    # retranslateUi

