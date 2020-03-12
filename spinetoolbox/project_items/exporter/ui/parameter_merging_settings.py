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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\parameter_merging_settings.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\parameter_merging_settings.ui' applies.
#
# Created: Thu Feb 20 15:54:08 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(776, 593)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_4 = QtWidgets.QLabel(self.frame)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.parameter_name_edit = QtWidgets.QLineEdit(self.frame)
        self.parameter_name_edit.setObjectName("parameter_name_edit")
        self.horizontalLayout.addWidget(self.parameter_name_edit)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.remove_button = QtWidgets.QPushButton(self.frame)
        self.remove_button.setObjectName("remove_button")
        self.horizontalLayout.addWidget(self.remove_button)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.message_label = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_label.sizePolicy().hasHeightForWidth())
        self.message_label.setSizePolicy(sizePolicy)
        self.message_label.setObjectName("message_label")
        self.verticalLayout_2.addWidget(self.message_label)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.label_3 = QtWidgets.QLabel(self.frame)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.indexing_domains_label = QtWidgets.QLabel(self.frame)
        self.indexing_domains_label.setTextFormat(QtCore.Qt.RichText)
        self.indexing_domains_label.setObjectName("indexing_domains_label")
        self.horizontalLayout_2.addWidget(self.indexing_domains_label)
        self.move_domain_left_button = QtWidgets.QPushButton(self.frame)
        self.move_domain_left_button.setObjectName("move_domain_left_button")
        self.horizontalLayout_2.addWidget(self.move_domain_left_button)
        self.move_domain_right_button = QtWidgets.QPushButton(self.frame)
        self.move_domain_right_button.setObjectName("move_domain_right_button")
        self.horizontalLayout_2.addWidget(self.move_domain_right_button)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.splitter = QtWidgets.QSplitter(self.frame)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.domains_list_view = QtWidgets.QListView(self.splitter)
        self.domains_list_view.setObjectName("domains_list_view")
        self.parameter_name_list_view = QtWidgets.QListView(self.splitter)
        self.parameter_name_list_view.setObjectName("parameter_name_list_view")
        self.formLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.formLayoutWidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.domain_description_edit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.domain_description_edit.setObjectName("domain_description_edit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.domain_description_edit)
        self.domain_name_edit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.domain_name_edit.setObjectName("domain_name_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.domain_name_edit)
        self.verticalLayout.addWidget(self.splitter)
        self.verticalLayout_4.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("Form", "Parameter name:", None, -1))
        self.parameter_name_edit.setToolTip(QtWidgets.QApplication.translate("Form", "Name of the merged parameter", None, -1))
        self.parameter_name_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type merged parameter name here...", None, -1))
        self.remove_button.setText(QtWidgets.QApplication.translate("Form", "Remove", None, -1))
        self.message_label.setText(QtWidgets.QApplication.translate("Form", "Message", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("Form", "Indexing domains:", None, -1))
        self.indexing_domains_label.setText(QtWidgets.QApplication.translate("Form", "(<b>unnamed</b>)", None, -1))
        self.move_domain_left_button.setText(QtWidgets.QApplication.translate("Form", "Move Left", None, -1))
        self.move_domain_right_button.setText(QtWidgets.QApplication.translate("Form", "Move Right", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Domain name:", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("Form", "Description:", None, -1))
        self.domain_description_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type explanatory text here...", None, -1))
        self.domain_name_edit.setToolTip(QtWidgets.QApplication.translate("Form", "Name of the domain that\n"
"holds the original parameter names.", None, -1))
        self.domain_name_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type new domain name here...", None, -1))

