# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'select_database_items_dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)
        self.root_layout = QVBoxLayout(Dialog)
        self.root_layout.setObjectName(u"root_layout")
        self.databases_group_box = QGroupBox(Dialog)
        self.databases_group_box.setObjectName(u"databases_group_box")
        self.verticalLayout_2 = QVBoxLayout(self.databases_group_box)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.databases_grid_layout = QGridLayout()
        self.databases_grid_layout.setObjectName(u"databases_grid_layout")

        self.verticalLayout_2.addLayout(self.databases_grid_layout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.select_all_button = QPushButton(self.databases_group_box)
        self.select_all_button.setObjectName(u"select_all_button")

        self.horizontalLayout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton(self.databases_group_box)
        self.deselect_all_button.setObjectName(u"deselect_all_button")

        self.horizontalLayout.addWidget(self.deselect_all_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.root_layout.addWidget(self.databases_group_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.root_layout.addItem(self.verticalSpacer)

        self.button_box = QDialogButtonBox(Dialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.root_layout.addWidget(self.button_box)


        self.retranslateUi(Dialog)
        self.button_box.accepted.connect(Dialog.accept)
        self.button_box.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.databases_group_box.setTitle(QCoreApplication.translate("Dialog", u"Databases", None))
#if QT_CONFIG(tooltip)
        self.select_all_button.setToolTip(QCoreApplication.translate("Dialog", u"Select all databases.", None))
#endif // QT_CONFIG(tooltip)
        self.select_all_button.setText(QCoreApplication.translate("Dialog", u"Select all", None))
#if QT_CONFIG(tooltip)
        self.deselect_all_button.setToolTip(QCoreApplication.translate("Dialog", u"Deselect all databases.", None))
#endif // QT_CONFIG(tooltip)
        self.deselect_all_button.setText(QCoreApplication.translate("Dialog", u"Deselect all", None))
    # retranslateUi

