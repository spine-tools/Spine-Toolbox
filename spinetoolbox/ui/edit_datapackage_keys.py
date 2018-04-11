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

# Form implementation generated from reading ui file '../spinetoolbox/ui/edit_datapackage_keys.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.resize(804, 348)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitter = QtWidgets.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(9, 9, 9, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_pks = QtWidgets.QLabel(self.layoutWidget)
        self.label_pks.setObjectName("label_pks")
        self.verticalLayout_2.addWidget(self.label_pks)
        self.tableView_pks = QtWidgets.QTableView(self.layoutWidget)
        self.tableView_pks.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.tableView_pks.setAlternatingRowColors(True)
        self.tableView_pks.setSortingEnabled(False)
        self.tableView_pks.setObjectName("tableView_pks")
        self.tableView_pks.horizontalHeader().setCascadingSectionResizes(True)
        self.tableView_pks.horizontalHeader().setDefaultSectionSize(150)
        self.tableView_pks.horizontalHeader().setMinimumSectionSize(0)
        self.tableView_pks.verticalHeader().setVisible(False)
        self.verticalLayout_2.addWidget(self.tableView_pks)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.toolButton_add_pk = QtWidgets.QToolButton(self.layoutWidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_add_pk.setIcon(icon)
        self.toolButton_add_pk.setObjectName("toolButton_add_pk")
        self.horizontalLayout_3.addWidget(self.toolButton_add_pk)
        self.toolButton_rm_pks = QtWidgets.QToolButton(self.layoutWidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_rm_pks.setIcon(icon1)
        self.toolButton_rm_pks.setObjectName("toolButton_rm_pks")
        self.horizontalLayout_3.addWidget(self.toolButton_rm_pks)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.layoutWidget1 = QtWidgets.QWidget(self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(9, 9, 9, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_fks = QtWidgets.QLabel(self.layoutWidget1)
        self.label_fks.setObjectName("label_fks")
        self.verticalLayout.addWidget(self.label_fks)
        self.tableView_fks = QtWidgets.QTableView(self.layoutWidget1)
        self.tableView_fks.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.tableView_fks.setAlternatingRowColors(True)
        self.tableView_fks.setSortingEnabled(False)
        self.tableView_fks.setObjectName("tableView_fks")
        self.tableView_fks.horizontalHeader().setCascadingSectionResizes(True)
        self.tableView_fks.horizontalHeader().setDefaultSectionSize(150)
        self.tableView_fks.horizontalHeader().setMinimumSectionSize(0)
        self.tableView_fks.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableView_fks)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.toolButton_add_fk = QtWidgets.QToolButton(self.layoutWidget1)
        self.toolButton_add_fk.setIcon(icon)
        self.toolButton_add_fk.setObjectName("toolButton_add_fk")
        self.horizontalLayout_2.addWidget(self.toolButton_add_fk)
        self.toolButton_rm_fks = QtWidgets.QToolButton(self.layoutWidget1)
        self.toolButton_rm_fks.setIcon(icon1)
        self.toolButton_rm_fks.setObjectName("toolButton_rm_fks")
        self.horizontalLayout_2.addWidget(self.toolButton_rm_fks)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.addWidget(self.splitter)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setContentsMargins(0, 6, 0, 6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.pushButton_ok = QtWidgets.QPushButton(Form)
        self.pushButton_ok.setDefault(True)
        self.pushButton_ok.setObjectName("pushButton_ok")
        self.horizontalLayout_4.addWidget(self.pushButton_ok)
        self.pushButton_cancel = QtWidgets.QPushButton(Form)
        self.pushButton_cancel.setDefault(True)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout_4.addWidget(self.pushButton_cancel)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
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
        self.verticalLayout_3.addLayout(self.horizontalLayout_statusbar_placeholder)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Edit Datapackage Keys", None, -1))
        self.label_pks.setText(QtWidgets.QApplication.translate("Form", "<html><head/><body><p><span style=\" font-weight:600;\">Primary keys</span></p></body></html>", None, -1))
        self.tableView_pks.setToolTip(QtWidgets.QApplication.translate("Form", "Double click on a cell to start editing", None, -1))
        self.toolButton_add_pk.setToolTip(QtWidgets.QApplication.translate("Form", "Add foreign key", None, -1))
        self.toolButton_add_pk.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.toolButton_rm_pks.setToolTip(QtWidgets.QApplication.translate("Form", "Remove selected keys", None, -1))
        self.toolButton_rm_pks.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.label_fks.setText(QtWidgets.QApplication.translate("Form", "<b>Foreign keys</b>", None, -1))
        self.tableView_fks.setToolTip(QtWidgets.QApplication.translate("Form", "Double click on a cell to start editing", None, -1))
        self.toolButton_add_fk.setToolTip(QtWidgets.QApplication.translate("Form", "Add foreign key", None, -1))
        self.toolButton_add_fk.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.toolButton_rm_fks.setToolTip(QtWidgets.QApplication.translate("Form", "Remove selected keys", None, -1))
        self.toolButton_rm_fks.setText(QtWidgets.QApplication.translate("Form", "...", None, -1))
        self.pushButton_ok.setText(QtWidgets.QApplication.translate("Form", "Ok", None, -1))
        self.pushButton_cancel.setText(QtWidgets.QApplication.translate("Form", "Cancel", None, -1))

import resources_icons_rc
