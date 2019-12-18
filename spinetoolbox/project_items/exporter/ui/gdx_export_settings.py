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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\gdx_export_settings.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\project_items\exporter\ui\gdx_export_settings.ui' applies.
#
# Created: Wed Jan 15 16:09:05 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.WindowModal)
        Form.resize(603, 367)
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
        self.record_sort_alphabetic = QtWidgets.QPushButton(self.groupBox_2)
        self.record_sort_alphabetic.setObjectName("record_sort_alphabetic")
        self.verticalLayout_2.addWidget(self.record_sort_alphabetic)
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
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.open_indexed_parameter_settings_button = QtWidgets.QPushButton(Form)
        self.open_indexed_parameter_settings_button.setObjectName("open_indexed_parameter_settings_button")
        self.horizontalLayout_4.addWidget(self.open_indexed_parameter_settings_button)
        self.indexing_status_label = QtWidgets.QLabel(Form)
        self.indexing_status_label.setText("")
        self.indexing_status_label.setTextFormat(QtCore.Qt.RichText)
        self.indexing_status_label.setObjectName("indexing_status_label")
        self.horizontalLayout_4.addWidget(self.indexing_status_label)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem4)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.global_parameters_combo_box = QtWidgets.QComboBox(Form)
        self.global_parameters_combo_box.setObjectName("global_parameters_combo_box")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.global_parameters_combo_box)
        self.horizontalLayout_3.addLayout(self.formLayout)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem5)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.button_box = QtWidgets.QDialogButtonBox(Form)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.RestoreDefaults)
        self.button_box.setObjectName("button_box")
        self.verticalLayout_4.addWidget(self.button_box)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Gdx Export Settings", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("Form", "Sets", None, -1))
        self.set_move_up_button.setText(QtWidgets.QApplication.translate("Form", "Move Up", None, -1))
        self.set_move_down_button.setText(QtWidgets.QApplication.translate("Form", "Move Down", None, -1))
        self.groupBox_2.setTitle(QtWidgets.QApplication.translate("Form", "Set Contents", None, -1))
        self.record_sort_alphabetic.setText(QtWidgets.QApplication.translate("Form", "Alphabetic", None, -1))
        self.record_move_up_button.setText(QtWidgets.QApplication.translate("Form", "Move Up", None, -1))
        self.record_move_down_button.setText(QtWidgets.QApplication.translate("Form", "Move Down", None, -1))
        self.open_indexed_parameter_settings_button.setText(QtWidgets.QApplication.translate("Form", "Indexed parameters...", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Global parameters domain:", None, -1))

