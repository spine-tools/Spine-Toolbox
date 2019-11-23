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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_mapping_options.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\import_mapping_options.ui' applies.
#
# Created: Fri Nov 22 18:44:17 2019
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_ImportMappingOptions(object):
    def setupUi(self, ImportMappingOptions):
        ImportMappingOptions.setObjectName("ImportMappingOptions")
        ImportMappingOptions.resize(400, 177)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImportMappingOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.options_group = QtWidgets.QGroupBox(ImportMappingOptions)
        self.options_group.setObjectName("options_group")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.options_group)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.optons_layout = QtWidgets.QFormLayout()
        self.optons_layout.setObjectName("optons_layout")
        self.class_type_label = QtWidgets.QLabel(self.options_group)
        self.class_type_label.setObjectName("class_type_label")
        self.optons_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.class_type_label)
        self.parameter_type_label = QtWidgets.QLabel(self.options_group)
        self.parameter_type_label.setObjectName("parameter_type_label")
        self.optons_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.parameter_type_label)
        self.class_type_combo_box = QtWidgets.QComboBox(self.options_group)
        self.class_type_combo_box.setObjectName("class_type_combo_box")
        self.class_type_combo_box.addItem("")
        self.class_type_combo_box.addItem("")
        self.optons_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.class_type_combo_box)
        self.parameter_type_combo_box = QtWidgets.QComboBox(self.options_group)
        self.parameter_type_combo_box.setObjectName("parameter_type_combo_box")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.optons_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.parameter_type_combo_box)
        self.ignore_columns_label = QtWidgets.QLabel(self.options_group)
        self.ignore_columns_label.setObjectName("ignore_columns_label")
        self.optons_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.ignore_columns_label)
        self.ignore_columns_button = QtWidgets.QPushButton(self.options_group)
        self.ignore_columns_button.setText("")
        self.ignore_columns_button.setObjectName("ignore_columns_button")
        self.optons_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.ignore_columns_button)
        self.dimension_label = QtWidgets.QLabel(self.options_group)
        self.dimension_label.setObjectName("dimension_label")
        self.optons_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.dimension_label)
        self.dimension_spin_box = QtWidgets.QSpinBox(self.options_group)
        self.dimension_spin_box.setMinimum(1)
        self.dimension_spin_box.setObjectName("dimension_spin_box")
        self.optons_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.dimension_spin_box)
        self.import_objects_check_box = QtWidgets.QCheckBox(self.options_group)
        self.import_objects_check_box.setObjectName("import_objects_check_box")
        self.optons_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.import_objects_check_box)
        self.verticalLayout_2.addLayout(self.optons_layout)
        self.verticalLayout.addWidget(self.options_group)

        self.retranslateUi(ImportMappingOptions)
        QtCore.QMetaObject.connectSlotsByName(ImportMappingOptions)

    def retranslateUi(self, ImportMappingOptions):
        ImportMappingOptions.setWindowTitle(QtWidgets.QApplication.translate("ImportMappingOptions", "Form", None, -1))
        self.options_group.setTitle(QtWidgets.QApplication.translate("ImportMappingOptions", "Options", None, -1))
        self.class_type_label.setText(QtWidgets.QApplication.translate("ImportMappingOptions", "Class type:", None, -1))
        self.parameter_type_label.setText(QtWidgets.QApplication.translate("ImportMappingOptions", "Parameter type:", None, -1))
        self.class_type_combo_box.setItemText(0, QtWidgets.QApplication.translate("ImportMappingOptions", "Object", None, -1))
        self.class_type_combo_box.setItemText(1, QtWidgets.QApplication.translate("ImportMappingOptions", "Relationship", None, -1))
        self.parameter_type_combo_box.setItemText(0, QtWidgets.QApplication.translate("ImportMappingOptions", "Single value", None, -1))
        self.parameter_type_combo_box.setItemText(1, QtWidgets.QApplication.translate("ImportMappingOptions", "Time series", None, -1))
        self.parameter_type_combo_box.setItemText(2, QtWidgets.QApplication.translate("ImportMappingOptions", "Time pattern", None, -1))
        self.parameter_type_combo_box.setItemText(3, QtWidgets.QApplication.translate("ImportMappingOptions", "Definition", None, -1))
        self.parameter_type_combo_box.setItemText(4, QtWidgets.QApplication.translate("ImportMappingOptions", "List", None, -1))
        self.parameter_type_combo_box.setItemText(5, QtWidgets.QApplication.translate("ImportMappingOptions", "None", None, -1))
        self.ignore_columns_label.setText(QtWidgets.QApplication.translate("ImportMappingOptions", "Ignore columns:", None, -1))
        self.dimension_label.setText(QtWidgets.QApplication.translate("ImportMappingOptions", "Dimension:", None, -1))
        self.import_objects_check_box.setText(QtWidgets.QApplication.translate("ImportMappingOptions", "Import objects", None, -1))

