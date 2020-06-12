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
## Form generated from reading UI file 'parameter_merging_settings.ui'
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
        Form.resize(776, 593)
        self.verticalLayout_4 = QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.parameter_name_edit = QLineEdit(self.frame)
        self.parameter_name_edit.setObjectName(u"parameter_name_edit")

        self.horizontalLayout.addWidget(self.parameter_name_edit)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.remove_button = QPushButton(self.frame)
        self.remove_button.setObjectName(u"remove_button")

        self.horizontalLayout.addWidget(self.remove_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.message_label = QLabel(self.frame)
        self.message_label.setObjectName(u"message_label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_label.sizePolicy().hasHeightForWidth())
        self.message_label.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.message_label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_2.addWidget(self.label_3)

        self.indexing_domains_label = QLabel(self.frame)
        self.indexing_domains_label.setObjectName(u"indexing_domains_label")
        self.indexing_domains_label.setTextFormat(Qt.RichText)

        self.horizontalLayout_2.addWidget(self.indexing_domains_label)

        self.move_domain_left_button = QPushButton(self.frame)
        self.move_domain_left_button.setObjectName(u"move_domain_left_button")

        self.horizontalLayout_2.addWidget(self.move_domain_left_button)

        self.move_domain_right_button = QPushButton(self.frame)
        self.move_domain_right_button.setObjectName(u"move_domain_right_button")

        self.horizontalLayout_2.addWidget(self.move_domain_right_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.splitter = QSplitter(self.frame)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.domains_list_view = QListView(self.splitter)
        self.domains_list_view.setObjectName(u"domains_list_view")
        self.splitter.addWidget(self.domains_list_view)
        self.parameter_name_list_view = QListView(self.splitter)
        self.parameter_name_list_view.setObjectName(u"parameter_name_list_view")
        self.splitter.addWidget(self.parameter_name_list_view)
        self.formLayoutWidget = QWidget(self.splitter)
        self.formLayoutWidget.setObjectName(u"formLayoutWidget")
        self.formLayout = QFormLayout(self.formLayoutWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.formLayoutWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.label_2 = QLabel(self.formLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.domain_description_edit = QLineEdit(self.formLayoutWidget)
        self.domain_description_edit.setObjectName(u"domain_description_edit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.domain_description_edit)

        self.domain_name_edit = QLineEdit(self.formLayoutWidget)
        self.domain_name_edit.setObjectName(u"domain_name_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.domain_name_edit)

        self.splitter.addWidget(self.formLayoutWidget)

        self.verticalLayout.addWidget(self.splitter)


        self.verticalLayout_4.addWidget(self.frame)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Parameter name:", None))
#if QT_CONFIG(tooltip)
        self.parameter_name_edit.setToolTip(QCoreApplication.translate("Form", u"Name of the merged parameter", None))
#endif // QT_CONFIG(tooltip)
        self.parameter_name_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Type merged parameter name here...", None))
        self.remove_button.setText(QCoreApplication.translate("Form", u"Remove", None))
        self.message_label.setText(QCoreApplication.translate("Form", u"Message", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Indexing domains:", None))
        self.indexing_domains_label.setText(QCoreApplication.translate("Form", u"(<b>unnamed</b>)", None))
        self.move_domain_left_button.setText(QCoreApplication.translate("Form", u"Move Left", None))
        self.move_domain_right_button.setText(QCoreApplication.translate("Form", u"Move Right", None))
        self.label.setText(QCoreApplication.translate("Form", u"Domain name:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Description:", None))
        self.domain_description_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Type explanatory text here...", None))
#if QT_CONFIG(tooltip)
        self.domain_name_edit.setToolTip(QCoreApplication.translate("Form", u"Name of the domain that\n"
"holds the original parameter names.", None))
#endif // QT_CONFIG(tooltip)
        self.domain_name_edit.setPlaceholderText(QCoreApplication.translate("Form", u"Type new domain name here...", None))
    # retranslateUi

