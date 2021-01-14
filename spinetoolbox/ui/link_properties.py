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
## Form generated from reading UI file 'link_properties.ui'
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

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(386, 462)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(Form)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.treeView_resources = QTreeView(self.groupBox_2)
        self.treeView_resources.setObjectName(u"treeView_resources")
        self.treeView_resources.setAcceptDrops(True)
        self.treeView_resources.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView_resources.header().setVisible(False)

        self.verticalLayout_5.addWidget(self.treeView_resources)


        self.gridLayout.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.label_link_name = QLabel(Form)
        self.label_link_name.setObjectName(u"label_link_name")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_link_name.sizePolicy().hasHeightForWidth())
        self.label_link_name.setSizePolicy(sizePolicy)
        self.label_link_name.setMinimumSize(QSize(0, 20))
        self.label_link_name.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_link_name.setFont(font)
        self.label_link_name.setStyleSheet(u"background-color: #ecd8c6;")
        self.label_link_name.setFrameShape(QFrame.Box)
        self.label_link_name.setFrameShadow(QFrame.Sunken)
        self.label_link_name.setAlignment(Qt.AlignCenter)
        self.label_link_name.setWordWrap(True)

        self.gridLayout.addWidget(self.label_link_name, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Form", u"Resource filters", None))
        self.label_link_name.setText(QCoreApplication.translate("Form", u"Name", None))
    # retranslateUi

