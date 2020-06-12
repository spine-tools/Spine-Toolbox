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
## Form generated from reading UI file 'import_mapping_options.ui'
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


class Ui_ImportMappingOptions(object):
    def setupUi(self, ImportMappingOptions):
        if not ImportMappingOptions.objectName():
            ImportMappingOptions.setObjectName(u"ImportMappingOptions")
        ImportMappingOptions.resize(506, 204)
        self.verticalLayout = QVBoxLayout(ImportMappingOptions)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.options_group = QGroupBox(ImportMappingOptions)
        self.options_group.setObjectName(u"options_group")
        self.horizontalLayout = QHBoxLayout(self.options_group)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.optons_layout = QFormLayout()
        self.optons_layout.setObjectName(u"optons_layout")
        self.class_type_label = QLabel(self.options_group)
        self.class_type_label.setObjectName(u"class_type_label")

        self.optons_layout.setWidget(0, QFormLayout.LabelRole, self.class_type_label)

        self.parameter_type_label = QLabel(self.options_group)
        self.parameter_type_label.setObjectName(u"parameter_type_label")

        self.optons_layout.setWidget(1, QFormLayout.LabelRole, self.parameter_type_label)

        self.class_type_combo_box = QComboBox(self.options_group)
        self.class_type_combo_box.addItem("")
        self.class_type_combo_box.addItem("")
        self.class_type_combo_box.setObjectName(u"class_type_combo_box")

        self.optons_layout.setWidget(0, QFormLayout.FieldRole, self.class_type_combo_box)

        self.parameter_type_combo_box = QComboBox(self.options_group)
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.setObjectName(u"parameter_type_combo_box")

        self.optons_layout.setWidget(1, QFormLayout.FieldRole, self.parameter_type_combo_box)

        self.ignore_columns_label = QLabel(self.options_group)
        self.ignore_columns_label.setObjectName(u"ignore_columns_label")

        self.optons_layout.setWidget(3, QFormLayout.LabelRole, self.ignore_columns_label)

        self.ignore_columns_button = QPushButton(self.options_group)
        self.ignore_columns_button.setObjectName(u"ignore_columns_button")

        self.optons_layout.setWidget(3, QFormLayout.FieldRole, self.ignore_columns_button)

        self.dimension_label = QLabel(self.options_group)
        self.dimension_label.setObjectName(u"dimension_label")

        self.optons_layout.setWidget(4, QFormLayout.LabelRole, self.dimension_label)

        self.dimension_spin_box = QSpinBox(self.options_group)
        self.dimension_spin_box.setObjectName(u"dimension_spin_box")
        self.dimension_spin_box.setMinimum(1)

        self.optons_layout.setWidget(4, QFormLayout.FieldRole, self.dimension_spin_box)

        self.import_objects_check_box = QCheckBox(self.options_group)
        self.import_objects_check_box.setObjectName(u"import_objects_check_box")

        self.optons_layout.setWidget(5, QFormLayout.FieldRole, self.import_objects_check_box)

        self.start_read_row_spin_box = QSpinBox(self.options_group)
        self.start_read_row_spin_box.setObjectName(u"start_read_row_spin_box")

        self.optons_layout.setWidget(2, QFormLayout.FieldRole, self.start_read_row_spin_box)

        self.read_start_row_label = QLabel(self.options_group)
        self.read_start_row_label.setObjectName(u"read_start_row_label")

        self.optons_layout.setWidget(2, QFormLayout.LabelRole, self.read_start_row_label)


        self.horizontalLayout.addLayout(self.optons_layout)

        self.time_series_options_layout = QFormLayout()
        self.time_series_options_layout.setObjectName(u"time_series_options_layout")
        self.time_series_repeat_check_box = QCheckBox(self.options_group)
        self.time_series_repeat_check_box.setObjectName(u"time_series_repeat_check_box")

        self.time_series_options_layout.setWidget(0, QFormLayout.FieldRole, self.time_series_repeat_check_box)

        self.map_dimension_spin_box = QSpinBox(self.options_group)
        self.map_dimension_spin_box.setObjectName(u"map_dimension_spin_box")
        self.map_dimension_spin_box.setMinimum(1)

        self.time_series_options_layout.setWidget(1, QFormLayout.FieldRole, self.map_dimension_spin_box)

        self.map_dimensions_label = QLabel(self.options_group)
        self.map_dimensions_label.setObjectName(u"map_dimensions_label")

        self.time_series_options_layout.setWidget(1, QFormLayout.LabelRole, self.map_dimensions_label)


        self.horizontalLayout.addLayout(self.time_series_options_layout)


        self.verticalLayout.addWidget(self.options_group)


        self.retranslateUi(ImportMappingOptions)

        QMetaObject.connectSlotsByName(ImportMappingOptions)
    # setupUi

    def retranslateUi(self, ImportMappingOptions):
        ImportMappingOptions.setWindowTitle(QCoreApplication.translate("ImportMappingOptions", u"Form", None))
        self.options_group.setTitle(QCoreApplication.translate("ImportMappingOptions", u"Options", None))
        self.class_type_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Class type:", None))
        self.parameter_type_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Parameter type:", None))
        self.class_type_combo_box.setItemText(0, QCoreApplication.translate("ImportMappingOptions", u"Object", None))
        self.class_type_combo_box.setItemText(1, QCoreApplication.translate("ImportMappingOptions", u"Relationship", None))

        self.parameter_type_combo_box.setItemText(0, QCoreApplication.translate("ImportMappingOptions", u"Single value", None))
        self.parameter_type_combo_box.setItemText(1, QCoreApplication.translate("ImportMappingOptions", u"Time series", None))
        self.parameter_type_combo_box.setItemText(2, QCoreApplication.translate("ImportMappingOptions", u"Time pattern", None))
        self.parameter_type_combo_box.setItemText(3, QCoreApplication.translate("ImportMappingOptions", u"Map", None))
        self.parameter_type_combo_box.setItemText(4, QCoreApplication.translate("ImportMappingOptions", u"Array", None))
        self.parameter_type_combo_box.setItemText(5, QCoreApplication.translate("ImportMappingOptions", u"Definition", None))
        self.parameter_type_combo_box.setItemText(6, QCoreApplication.translate("ImportMappingOptions", u"None", None))

        self.ignore_columns_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Ignore columns:", None))
        self.ignore_columns_button.setText("")
        self.dimension_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Dimension:", None))
        self.import_objects_check_box.setText(QCoreApplication.translate("ImportMappingOptions", u"Import objects", None))
        self.read_start_row_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Read data from row:", None))
#if QT_CONFIG(tooltip)
        self.time_series_repeat_check_box.setToolTip(QCoreApplication.translate("ImportMappingOptions", u"Set the repeat flag for all imported time series", None))
#endif // QT_CONFIG(tooltip)
        self.time_series_repeat_check_box.setText(QCoreApplication.translate("ImportMappingOptions", u"Repeat time series", None))
        self.map_dimensions_label.setText(QCoreApplication.translate("ImportMappingOptions", u"Map dimensions:", None))
    # retranslateUi

