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
## Form generated from reading UI file 'link_properties.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTreeView, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qwidgets import PropertyQSpinBox
from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(372, 355)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.filter_type_label = QLabel(Form)
        self.filter_type_label.setObjectName(u"filter_type_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.filter_type_label)

        self.filter_type_combo_box = QComboBox(Form)
        self.filter_type_combo_box.setObjectName(u"filter_type_combo_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.filter_type_combo_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.treeView_filters = QTreeView(Form)
        self.treeView_filters.setObjectName(u"treeView_filters")
        self.treeView_filters.setAcceptDrops(True)
        self.treeView_filters.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView_filters.header().setVisible(True)

        self.verticalLayout.addWidget(self.treeView_filters)

        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.auto_check_filters_check_box = QCheckBox(self.frame)
        self.auto_check_filters_check_box.setObjectName(u"auto_check_filters_check_box")
        self.auto_check_filters_check_box.setChecked(True)

        self.horizontalLayout_3.addWidget(self.auto_check_filters_check_box)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.open_filter_validation_menu_button = QPushButton(self.frame)
        self.open_filter_validation_menu_button.setObjectName(u"open_filter_validation_menu_button")

        self.horizontalLayout_3.addWidget(self.open_filter_validation_menu_button)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_write_index = QLabel(self.frame)
        self.label_write_index.setObjectName(u"label_write_index")

        self.horizontalLayout.addWidget(self.label_write_index)

        self.spinBox_write_index = PropertyQSpinBox(self.frame)
        self.spinBox_write_index.setObjectName(u"spinBox_write_index")
        self.spinBox_write_index.setMinimum(1)
        self.spinBox_write_index.setMaximum(999)

        self.horizontalLayout.addWidget(self.spinBox_write_index)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.checkBox_purge_before_writing = QCheckBox(self.frame)
        self.checkBox_purge_before_writing.setObjectName(u"checkBox_purge_before_writing")

        self.horizontalLayout_2.addWidget(self.checkBox_purge_before_writing)

        self.purge_settings_button = QPushButton(self.frame)
        self.purge_settings_button.setObjectName(u"purge_settings_button")

        self.horizontalLayout_2.addWidget(self.purge_settings_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.checkBox_use_memory_db = QCheckBox(self.frame)
        self.checkBox_use_memory_db.setObjectName(u"checkBox_use_memory_db")

        self.verticalLayout_2.addWidget(self.checkBox_use_memory_db)

        self.checkBox_use_datapackage = QCheckBox(self.frame)
        self.checkBox_use_datapackage.setObjectName(u"checkBox_use_datapackage")

        self.verticalLayout_2.addWidget(self.checkBox_use_datapackage)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.filter_type_label.setText(QCoreApplication.translate("Form", u"Filter type:", None))
#if QT_CONFIG(tooltip)
        self.filter_type_combo_box.setToolTip(QCoreApplication.translate("Form", u"Select filter type between mutually exclusive filters.", None))
#endif // QT_CONFIG(tooltip)
        self.auto_check_filters_check_box.setText(QCoreApplication.translate("Form", u"Check new filters automatically", None))
        self.open_filter_validation_menu_button.setText(QCoreApplication.translate("Form", u"Filter validation", None))
        self.label_write_index.setText(QCoreApplication.translate("Form", u"Write index (lower writes earlier):", None))
        self.checkBox_purge_before_writing.setText(QCoreApplication.translate("Form", u"Purge before writing", None))
#if QT_CONFIG(tooltip)
        self.purge_settings_button.setToolTip(QCoreApplication.translate("Form", u"Choose what database items to purge.", None))
#endif // QT_CONFIG(tooltip)
        self.purge_settings_button.setText(QCoreApplication.translate("Form", u"Settings...", None))
        self.checkBox_use_memory_db.setText(QCoreApplication.translate("Form", u"Use memory DB for Tool execution", None))
        self.checkBox_use_datapackage.setText(QCoreApplication.translate("Form", u"Pack CSV files (as datapackage.json)", None))
    # retranslateUi

