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
## Form generated from reading UI file 'jump_properties.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QToolButton,
    QTreeView, QVBoxLayout, QWidget)

from spinetoolbox.widgets.code_text_edit import CodeTextEdit
from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(520, 628)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_condition = QGroupBox(Form)
        self.groupBox_condition.setObjectName(u"groupBox_condition")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_condition)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioButton_tool_spec = QRadioButton(self.groupBox_condition)
        self.radioButton_tool_spec.setObjectName(u"radioButton_tool_spec")

        self.horizontalLayout_2.addWidget(self.radioButton_tool_spec)

        self.comboBox_tool_spec = QComboBox(self.groupBox_condition)
        self.comboBox_tool_spec.setObjectName(u"comboBox_tool_spec")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_tool_spec.sizePolicy().hasHeightForWidth())
        self.comboBox_tool_spec.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.comboBox_tool_spec)

        self.toolButton_edit_tool_spec = QToolButton(self.groupBox_condition)
        self.toolButton_edit_tool_spec.setObjectName(u"toolButton_edit_tool_spec")
        icon = QIcon()
        icon.addFile(u":/icons/wrench.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_edit_tool_spec.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.toolButton_edit_tool_spec)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.radioButton_py_script = QRadioButton(self.groupBox_condition)
        self.radioButton_py_script.setObjectName(u"radioButton_py_script")

        self.verticalLayout_2.addWidget(self.radioButton_py_script)

        self.condition_script_edit = CodeTextEdit(self.groupBox_condition)
        self.condition_script_edit.setObjectName(u"condition_script_edit")

        self.verticalLayout_2.addWidget(self.condition_script_edit)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.pushButton_save_script = QPushButton(self.groupBox_condition)
        self.pushButton_save_script.setObjectName(u"pushButton_save_script")

        self.horizontalLayout_3.addWidget(self.pushButton_save_script)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.verticalLayout.addWidget(self.groupBox_condition)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.toolButton_add_arg = QToolButton(Form)
        self.toolButton_add_arg.setObjectName(u"toolButton_add_arg")
        icon1 = QIcon()
        icon1.addFile(u":/icons/file-upload.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_add_arg.setIcon(icon1)

        self.horizontalLayout.addWidget(self.toolButton_add_arg)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.toolButton_remove_arg = QToolButton(Form)
        self.toolButton_remove_arg.setObjectName(u"toolButton_remove_arg")
        icon2 = QIcon()
        icon2.addFile(u":/icons/minus.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_remove_arg.setIcon(icon2)

        self.horizontalLayout.addWidget(self.toolButton_remove_arg)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.treeView_input_files = QTreeView(Form)
        self.treeView_input_files.setObjectName(u"treeView_input_files")
        self.treeView_input_files.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView_input_files.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.gridLayout.addWidget(self.treeView_input_files, 2, 0, 1, 1)

        self.treeView_cmd_line_args = QTreeView(Form)
        self.treeView_cmd_line_args.setObjectName(u"treeView_cmd_line_args")
        self.treeView_cmd_line_args.setDragDropMode(QAbstractItemView.DragDrop)

        self.gridLayout.addWidget(self.treeView_cmd_line_args, 0, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_condition.setTitle(QCoreApplication.translate("Form", u"Condition", None))
        self.radioButton_tool_spec.setText(QCoreApplication.translate("Form", u"Tool specification", None))
        self.toolButton_edit_tool_spec.setText(QCoreApplication.translate("Form", u"...", None))
        self.radioButton_py_script.setText(QCoreApplication.translate("Form", u"Python script", None))
        self.pushButton_save_script.setText(QCoreApplication.translate("Form", u"Save script", None))
        self.toolButton_add_arg.setText(QCoreApplication.translate("Form", u"...", None))
        self.toolButton_remove_arg.setText(QCoreApplication.translate("Form", u"...", None))
    # retranslateUi

