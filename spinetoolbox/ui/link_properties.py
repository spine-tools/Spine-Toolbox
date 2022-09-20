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

from spinetoolbox.widgets.custom_qwidgets import PropertyQSpinBox

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(486, 288)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_write_index = QLabel(Form)
        self.label_write_index.setObjectName(u"label_write_index")

        self.horizontalLayout.addWidget(self.label_write_index)

        self.spinBox_write_index = PropertyQSpinBox(Form)
        self.spinBox_write_index.setObjectName(u"spinBox_write_index")
        self.spinBox_write_index.setMinimum(1)
        self.spinBox_write_index.setMaximum(999)

        self.horizontalLayout.addWidget(self.spinBox_write_index)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.treeView_filters = QTreeView(Form)
        self.treeView_filters.setObjectName(u"treeView_filters")
        self.treeView_filters.setAcceptDrops(True)
        self.treeView_filters.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView_filters.header().setVisible(True)

        self.verticalLayout.addWidget(self.treeView_filters)

        self.checkBox_use_memory_db = QCheckBox(Form)
        self.checkBox_use_memory_db.setObjectName(u"checkBox_use_memory_db")

        self.verticalLayout.addWidget(self.checkBox_use_memory_db)

        self.checkBox_use_datapackage = QCheckBox(Form)
        self.checkBox_use_datapackage.setObjectName(u"checkBox_use_datapackage")

        self.verticalLayout.addWidget(self.checkBox_use_datapackage)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_write_index.setText(QCoreApplication.translate("Form", u"Write index (lower writes earlier):", None))
        self.checkBox_use_memory_db.setText(QCoreApplication.translate("Form", u"Use memory DB for tool execution", None))
        self.checkBox_use_datapackage.setText(QCoreApplication.translate("Form", u"Pack CSV files (datapackage.json)", None))
    # retranslateUi

