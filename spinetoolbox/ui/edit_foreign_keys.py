#############################################################################\
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland\
#\
# This file is part of Spine Toolbox.\
#\
# Spine Toolbox is free software: you can redistribute it and\/or modify\
# it under the terms of the GNU Lesser General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# This program is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU Lesser General Public License for more details.\
#\
# You should have received a copy of the GNU Lesser General Public License\
# along with this program.  If not, see <http:\/\/www.gnu.org\/licenses\/>.\
#############################################################################\

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/edit_foreign_keys.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.resize(558, 348)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(9, 9, 9, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_fks = QtWidgets.QLabel(Form)
        self.label_fks.setObjectName("label_fks")
        self.verticalLayout.addWidget(self.label_fks)
        self.tableView_fks = QtWidgets.QTableView(Form)
        self.tableView_fks.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.tableView_fks.setObjectName("tableView_fks")
        self.tableView_fks.horizontalHeader().setCascadingSectionResizes(True)
        self.tableView_fks.horizontalHeader().setDefaultSectionSize(150)
        self.tableView_fks.horizontalHeader().setMinimumSectionSize(0)
        self.tableView_fks.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableView_fks)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.toolButton_add_fk = QtWidgets.QToolButton(Form)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_add_fk.setIcon(icon)
        self.toolButton_add_fk.setObjectName("toolButton_add_fk")
        self.horizontalLayout_2.addWidget(self.toolButton_add_fk)
        self.toolButton_rm_fks = QtWidgets.QToolButton(Form)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_rm_fks.setIcon(icon1)
        self.toolButton_rm_fks.setObjectName("toolButton_rm_fks")
        self.horizontalLayout_2.addWidget(self.toolButton_rm_fks)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 6, 0, 6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton_ok = QtWidgets.QPushButton(Form)
        self.pushButton_ok.setDefault(True)
        self.pushButton_ok.setObjectName("pushButton_ok")
        self.horizontalLayout.addWidget(self.pushButton_ok)
        self.pushButton_cancel = QtWidgets.QPushButton(Form)
        self.pushButton_cancel.setDefault(True)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_statusbar_placeholder = QtWidgets.QHBoxLayout()
        self.horizontalLayout_statusbar_placeholder.setObjectName("horizontalLayout_statusbar_placeholder")
        self.widget_invisible_dummy = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_invisible_dummy.sizePolicy().hasHeightForWidth())
        self.widget_invisible_dummy.setSizePolicy(sizePolicy)
        self.widget_invisible_dummy.setMinimumSize(QtCore.QSize(0, 20))
        self.widget_invisible_dummy.setObjectName("widget_invisible_dummy")
        self.horizontalLayout_statusbar_placeholder.addWidget(self.widget_invisible_dummy)
        self.verticalLayout_2.addLayout(self.horizontalLayout_statusbar_placeholder)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.pushButton_ok, self.pushButton_cancel)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Edit Foreign Keys", None, -1))
        self.label_fks.setText(QtWidgets.QApplication.translate("Form", "<b>Foreign keys</b>", None, -1))
        self.tableView_fks.setToolTip(QtWidgets.QApplication.translate("Form", "Double click on a cell to start editing", None, -1))
        self.toolButton_add_fk.setToolTip(QtWidgets.QApplication.translate("Form", "Add foreign key", None, -1))
        self.toolButton_add_fk.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.toolButton_rm_fks.setToolTip(QtWidgets.QApplication.translate("Form", "Remove selected keys", None, -1))
        self.toolButton_rm_fks.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.pushButton_ok.setText(QtWidgets.QApplication.translate("Form", "Ok", None, -1))
        self.pushButton_cancel.setText(QtWidgets.QApplication.translate("Form", "Cancel", None, -1))

import resources_icons_rc
