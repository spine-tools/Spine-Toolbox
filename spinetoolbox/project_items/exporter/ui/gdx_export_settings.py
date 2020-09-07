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
## Form generated from reading UI file 'gdx_export_settings.ui'
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
        Form.resize(603, 406)
        self.verticalLayout_4 = QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.splitter = QSplitter(Form)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.set_group_box = QGroupBox(self.splitter)
        self.set_group_box.setObjectName(u"set_group_box")
        self.horizontalLayout = QHBoxLayout(self.set_group_box)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.set_list_view = QListView(self.set_group_box)
        self.set_list_view.setObjectName(u"set_list_view")

        self.horizontalLayout.addWidget(self.set_list_view)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.set_move_up_button = QPushButton(self.set_group_box)
        self.set_move_up_button.setObjectName(u"set_move_up_button")

        self.verticalLayout.addWidget(self.set_move_up_button)

        self.set_move_down_button = QPushButton(self.set_group_box)
        self.set_move_down_button.setObjectName(u"set_move_down_button")

        self.verticalLayout.addWidget(self.set_move_down_button)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.splitter.addWidget(self.set_group_box)
        self.contents_group_box = QGroupBox(self.splitter)
        self.contents_group_box.setObjectName(u"contents_group_box")
        self.horizontalLayout_2 = QHBoxLayout(self.contents_group_box)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.record_list_view = QListView(self.contents_group_box)
        self.record_list_view.setObjectName(u"record_list_view")

        self.horizontalLayout_2.addWidget(self.record_list_view)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.record_sort_alphabetic = QPushButton(self.contents_group_box)
        self.record_sort_alphabetic.setObjectName(u"record_sort_alphabetic")

        self.verticalLayout_2.addWidget(self.record_sort_alphabetic)

        self.record_move_up_button = QPushButton(self.contents_group_box)
        self.record_move_up_button.setObjectName(u"record_move_up_button")

        self.verticalLayout_2.addWidget(self.record_move_up_button)

        self.record_move_down_button = QPushButton(self.contents_group_box)
        self.record_move_down_button.setObjectName(u"record_move_down_button")

        self.verticalLayout_2.addWidget(self.record_move_down_button)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_4)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.splitter.addWidget(self.contents_group_box)

        self.verticalLayout_4.addWidget(self.splitter)

        self.misc_control_holder = QWidget(Form)
        self.misc_control_holder.setObjectName(u"misc_control_holder")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.misc_control_holder.sizePolicy().hasHeightForWidth())
        self.misc_control_holder.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.misc_control_holder)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.open_indexed_parameter_settings_button = QPushButton(self.misc_control_holder)
        self.open_indexed_parameter_settings_button.setObjectName(u"open_indexed_parameter_settings_button")

        self.horizontalLayout_4.addWidget(self.open_indexed_parameter_settings_button)

        self.indexing_status_label = QLabel(self.misc_control_holder)
        self.indexing_status_label.setObjectName(u"indexing_status_label")
        self.indexing_status_label.setTextFormat(Qt.RichText)

        self.horizontalLayout_4.addWidget(self.indexing_status_label)

        self.open_parameter_merging_settings_button = QPushButton(self.misc_control_holder)
        self.open_parameter_merging_settings_button.setObjectName(u"open_parameter_merging_settings_button")

        self.horizontalLayout_4.addWidget(self.open_parameter_merging_settings_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.misc_control_holder)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.global_parameters_combo_box = QComboBox(self.misc_control_holder)
        self.global_parameters_combo_box.setObjectName(u"global_parameters_combo_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.global_parameters_combo_box)

        self.label_2 = QLabel(self.misc_control_holder)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.none_export_combo_box = QComboBox(self.misc_control_holder)
        self.none_export_combo_box.addItem("")
        self.none_export_combo_box.addItem("")
        self.none_export_combo_box.setObjectName(u"none_export_combo_box")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.none_export_combo_box)

        self.label_3 = QLabel(self.misc_control_holder)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_3)

        self.none_fallback_combo_box = QComboBox(self.misc_control_holder)
        self.none_fallback_combo_box.addItem("")
        self.none_fallback_combo_box.addItem("")
        self.none_fallback_combo_box.setObjectName(u"none_fallback_combo_box")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.none_fallback_combo_box)


        self.horizontalLayout_3.addLayout(self.formLayout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)


        self.verticalLayout_4.addWidget(self.misc_control_holder)

        self.button_box = QDialogButtonBox(Form)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok|QDialogButtonBox.RestoreDefaults)

        self.verticalLayout_4.addWidget(self.button_box)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Gdx Export Settings", None))
        self.set_group_box.setTitle(QCoreApplication.translate("Form", u"Sets", None))
        self.set_move_up_button.setText(QCoreApplication.translate("Form", u"Move Up", None))
        self.set_move_down_button.setText(QCoreApplication.translate("Form", u"Move Down", None))
        self.contents_group_box.setTitle(QCoreApplication.translate("Form", u"Set Contents", None))
#if QT_CONFIG(tooltip)
        self.record_sort_alphabetic.setToolTip(QCoreApplication.translate("Form", u"Sort set contents alphabetically.", None))
#endif // QT_CONFIG(tooltip)
        self.record_sort_alphabetic.setText(QCoreApplication.translate("Form", u"Alphabetic", None))
        self.record_move_up_button.setText(QCoreApplication.translate("Form", u"Move Up", None))
        self.record_move_down_button.setText(QCoreApplication.translate("Form", u"Move Down", None))
#if QT_CONFIG(tooltip)
        self.open_indexed_parameter_settings_button.setToolTip(QCoreApplication.translate("Form", u"Set up indexing for time series and other indexed parameters.", None))
#endif // QT_CONFIG(tooltip)
        self.open_indexed_parameter_settings_button.setText(QCoreApplication.translate("Form", u"Indexed Parameters...", None))
        self.indexing_status_label.setText("")
#if QT_CONFIG(tooltip)
        self.open_parameter_merging_settings_button.setToolTip(QCoreApplication.translate("Form", u"Merge multiple parameters into one.", None))
#endif // QT_CONFIG(tooltip)
        self.open_parameter_merging_settings_button.setText(QCoreApplication.translate("Form", u"Parameter Merging...", None))
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("Form", u"Selected domain's parameters are exported as GAMS scalars.\n"
"The domain itself is not exported.", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("Form", u"Global parameters domain:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"None values:", None))
        self.none_export_combo_box.setItemText(0, QCoreApplication.translate("Form", u"Do not export", None))
        self.none_export_combo_box.setItemText(1, QCoreApplication.translate("Form", u"Export as not-a-number", None))

        self.label_3.setText(QCoreApplication.translate("Form", u"If parameter value is None:", None))
        self.none_fallback_combo_box.setItemText(0, QCoreApplication.translate("Form", u"Use it", None))
        self.none_fallback_combo_box.setItemText(1, QCoreApplication.translate("Form", u"Replace by default value", None))

    # retranslateUi

