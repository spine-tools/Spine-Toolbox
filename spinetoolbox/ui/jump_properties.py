# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from spinetoolbox.widgets.code_text_edit import CodeTextEdit

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(386, 462)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(Form)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 384, 460))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter = QSplitter(self.scrollAreaWidgetContents)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.condition_edit = CodeTextEdit(self.splitter)
        self.condition_edit.setObjectName(u"condition_edit")
        self.splitter.addWidget(self.condition_edit)
        self.treeView_cmd_line_args = QTreeView(self.splitter)
        self.treeView_cmd_line_args.setObjectName(u"treeView_cmd_line_args")
        font = QFont()
        font.setPointSize(10)
        self.treeView_cmd_line_args.setFont(font)
        self.treeView_cmd_line_args.setDragDropMode(QAbstractItemView.DragDrop)
        self.splitter.addWidget(self.treeView_cmd_line_args)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.gridLayout = QGridLayout(self.verticalLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.toolButton_add_arg = QToolButton(self.verticalLayoutWidget)
        self.toolButton_add_arg.setObjectName(u"toolButton_add_arg")
        icon = QIcon()
        icon.addFile(u":/icons/file-upload.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_add_arg.setIcon(icon)

        self.horizontalLayout.addWidget(self.toolButton_add_arg)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.toolButton_remove_arg = QToolButton(self.verticalLayoutWidget)
        self.toolButton_remove_arg.setObjectName(u"toolButton_remove_arg")
        icon1 = QIcon()
        icon1.addFile(u":/icons/minus.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_remove_arg.setIcon(icon1)

        self.horizontalLayout.addWidget(self.toolButton_remove_arg)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.treeView_input_files = QTreeView(self.verticalLayoutWidget)
        self.treeView_input_files.setObjectName(u"treeView_input_files")
        self.treeView_input_files.setFont(font)
        self.treeView_input_files.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView_input_files.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.gridLayout.addWidget(self.treeView_input_files, 1, 0, 1, 1)

        self.splitter.addWidget(self.verticalLayoutWidget)

        self.verticalLayout.addWidget(self.splitter)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.toolButton_add_arg.setText(QCoreApplication.translate("Form", u"...", None))
        self.toolButton_remove_arg.setText(QCoreApplication.translate("Form", u"...", None))
    # retranslateUi

