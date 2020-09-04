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
## Form generated from reading UI file 'gimlet_properties.ui'
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

from spinetoolbox.widgets.custom_qlineedits import PropertyQLineEdit

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(395, 396)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_gimlet_name = QLabel(Form)
        self.label_gimlet_name.setObjectName(u"label_gimlet_name")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_gimlet_name.sizePolicy().hasHeightForWidth())
        self.label_gimlet_name.setSizePolicy(sizePolicy)
        self.label_gimlet_name.setMinimumSize(QSize(0, 20))
        self.label_gimlet_name.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_gimlet_name.setFont(font)
        self.label_gimlet_name.setStyleSheet(u"background-color: #ecd8c6;")
        self.label_gimlet_name.setFrameShape(QFrame.Box)
        self.label_gimlet_name.setFrameShadow(QFrame.Sunken)
        self.label_gimlet_name.setAlignment(Qt.AlignCenter)
        self.label_gimlet_name.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_gimlet_name)

        self.scrollArea_4 = QScrollArea(Form)
        self.scrollArea_4.setObjectName(u"scrollArea_4")
        self.scrollArea_4.setWidgetResizable(True)
        self.scrollAreaWidgetContents_4 = QWidget()
        self.scrollAreaWidgetContents_4.setObjectName(u"scrollAreaWidgetContents_4")
        self.scrollAreaWidgetContents_4.setGeometry(QRect(0, 0, 393, 374))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents_4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.checkBox_shell = QCheckBox(self.scrollAreaWidgetContents_4)
        self.checkBox_shell.setObjectName(u"checkBox_shell")
        self.checkBox_shell.setChecked(True)

        self.horizontalLayout.addWidget(self.checkBox_shell)

        self.comboBox_shell = QComboBox(self.scrollAreaWidgetContents_4)
        self.comboBox_shell.setObjectName(u"comboBox_shell")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_shell.sizePolicy().hasHeightForWidth())
        self.comboBox_shell.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.comboBox_shell)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.lineEdit_cmd = PropertyQLineEdit(self.scrollAreaWidgetContents_4)
        self.lineEdit_cmd.setObjectName(u"lineEdit_cmd")
        self.lineEdit_cmd.setClearButtonEnabled(True)

        self.verticalLayout_2.addWidget(self.lineEdit_cmd)

        self.treeView_files = QTreeView(self.scrollAreaWidgetContents_4)
        self.treeView_files.setObjectName(u"treeView_files")
        self.treeView_files.setTextElideMode(Qt.ElideLeft)
        self.treeView_files.setIndentation(5)
        self.treeView_files.setRootIsDecorated(False)
        self.treeView_files.setUniformRowHeights(True)
        self.treeView_files.header().setMinimumSectionSize(54)

        self.verticalLayout_2.addWidget(self.treeView_files)

        self.line_5 = QFrame(self.scrollAreaWidgetContents_4)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.HLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_5)

        self.label = QLabel(self.scrollAreaWidgetContents_4)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.radioButton_default = QRadioButton(self.scrollAreaWidgetContents_4)
        self.radioButton_default.setObjectName(u"radioButton_default")
        self.radioButton_default.setChecked(True)

        self.horizontalLayout_16.addWidget(self.radioButton_default)

        self.radioButton_unique = QRadioButton(self.scrollAreaWidgetContents_4)
        self.radioButton_unique.setObjectName(u"radioButton_unique")

        self.horizontalLayout_16.addWidget(self.radioButton_unique)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_12)

        self.toolButton_gimlet_open_dir = QToolButton(self.scrollAreaWidgetContents_4)
        self.toolButton_gimlet_open_dir.setObjectName(u"toolButton_gimlet_open_dir")
        self.toolButton_gimlet_open_dir.setMinimumSize(QSize(22, 22))
        self.toolButton_gimlet_open_dir.setMaximumSize(QSize(22, 22))
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_gimlet_open_dir.setIcon(icon)

        self.horizontalLayout_16.addWidget(self.toolButton_gimlet_open_dir)


        self.verticalLayout_2.addLayout(self.horizontalLayout_16)

        self.scrollArea_4.setWidget(self.scrollAreaWidgetContents_4)

        self.verticalLayout.addWidget(self.scrollArea_4)

        QWidget.setTabOrder(self.scrollArea_4, self.checkBox_shell)
        QWidget.setTabOrder(self.checkBox_shell, self.comboBox_shell)
        QWidget.setTabOrder(self.comboBox_shell, self.lineEdit_cmd)
        QWidget.setTabOrder(self.lineEdit_cmd, self.treeView_files)
        QWidget.setTabOrder(self.treeView_files, self.radioButton_default)
        QWidget.setTabOrder(self.radioButton_default, self.radioButton_unique)
        QWidget.setTabOrder(self.radioButton_unique, self.toolButton_gimlet_open_dir)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_gimlet_name.setText(QCoreApplication.translate("Form", u"Name", None))
#if QT_CONFIG(tooltip)
        self.checkBox_shell.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>If checked, command is executed with the specified shell.</p><p>If unchecked, command is executed without a shell.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_shell.setText(QCoreApplication.translate("Form", u"Shell", None))
        self.lineEdit_cmd.setPlaceholderText(QCoreApplication.translate("Form", u"Command", None))
        self.label.setText(QCoreApplication.translate("Form", u"Work directory", None))
        self.radioButton_default.setText(QCoreApplication.translate("Form", u"Default", None))
        self.radioButton_unique.setText(QCoreApplication.translate("Form", u"Unique", None))
#if QT_CONFIG(tooltip)
        self.toolButton_gimlet_open_dir.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Open this View's project directory in file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

