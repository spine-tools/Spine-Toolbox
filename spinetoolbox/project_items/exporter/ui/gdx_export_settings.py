# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\gdx_export_settings.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\gdx_export_settings.ui' applies.
#
# Created: Fri Nov 29 13:06:33 2019
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.WindowModal)
        Form.resize(603, 325)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.splitter = QtWidgets.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.groupBox = QtWidgets.QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.set_list_view = QtWidgets.QListView(self.groupBox)
        self.set_list_view.setObjectName("set_list_view")
        self.horizontalLayout.addWidget(self.set_list_view)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.set_move_up_button = QtWidgets.QPushButton(self.groupBox)
        self.set_move_up_button.setObjectName("set_move_up_button")
        self.verticalLayout.addWidget(self.set_move_up_button)
        self.set_move_down_button = QtWidgets.QPushButton(self.groupBox)
        self.set_move_down_button.setObjectName("set_move_down_button")
        self.verticalLayout.addWidget(self.set_move_down_button)
        self.set_as_global_parameters_object_class_button = QtWidgets.QPushButton(self.groupBox)
        self.set_as_global_parameters_object_class_button.setObjectName("set_as_global_parameters_object_class_button")
        self.verticalLayout.addWidget(self.set_as_global_parameters_object_class_button)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.groupBox_2 = QtWidgets.QGroupBox(self.splitter)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.record_list_view = QtWidgets.QListView(self.groupBox_2)
        self.record_list_view.setObjectName("record_list_view")
        self.horizontalLayout_2.addWidget(self.record_list_view)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.record_move_up_button = QtWidgets.QPushButton(self.groupBox_2)
        self.record_move_up_button.setObjectName("record_move_up_button")
        self.verticalLayout_2.addWidget(self.record_move_up_button)
        self.record_move_down_button = QtWidgets.QPushButton(self.groupBox_2)
        self.record_move_down_button.setObjectName("record_move_down_button")
        self.verticalLayout_2.addWidget(self.record_move_down_button)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem3)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout_4.addWidget(self.splitter)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.groupBox_3 = QtWidgets.QGroupBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.groupBox_3)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.global_parameters_object_class_line_edit = QtWidgets.QLineEdit(self.groupBox_3)
        self.global_parameters_object_class_line_edit.setObjectName("global_parameters_object_class_line_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.global_parameters_object_class_line_edit)
        self.verticalLayout_3.addLayout(self.formLayout)
        self.horizontalLayout_3.addWidget(self.groupBox_3)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem4)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.button_box = QtWidgets.QDialogButtonBox(Form)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.verticalLayout_4.addWidget(self.button_box)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Gdx Export Settings", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("Form", "Sets", None, -1))
        self.set_move_up_button.setText(QtWidgets.QApplication.translate("Form", "Move Up", None, -1))
        self.set_move_down_button.setText(QtWidgets.QApplication.translate("Form", "Move Down", None, -1))
        self.set_as_global_parameters_object_class_button.setText(QtWidgets.QApplication.translate("Form", "As Global", None, -1))
        self.groupBox_2.setTitle(QtWidgets.QApplication.translate("Form", "Set Contents", None, -1))
        self.record_move_up_button.setText(QtWidgets.QApplication.translate("Form", "Move Up", None, -1))
        self.record_move_down_button.setText(QtWidgets.QApplication.translate("Form", "Move Down", None, -1))
        self.groupBox_3.setTitle(QtWidgets.QApplication.translate("Form", "Global Parameters", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Object Class:", None, -1))

