#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../spinetoolbox/ui/add_relationships.ui',
# licensing of '../spinetoolbox/ui/add_relationships.ui' applies.
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(663, 399)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.comboBox_relationship_class = QtWidgets.QComboBox(Dialog)
        self.comboBox_relationship_class.setObjectName("comboBox_relationship_class")
        self.horizontalLayout_2.addWidget(self.comboBox_relationship_class)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.toolButton_insert_row = QtWidgets.QToolButton(Dialog)
        self.toolButton_insert_row.setObjectName("toolButton_insert_row")
        self.horizontalLayout_2.addWidget(self.toolButton_insert_row)
        self.toolButton_remove_row = QtWidgets.QToolButton(Dialog)
        self.toolButton_remove_row.setObjectName("toolButton_remove_row")
        self.horizontalLayout_2.addWidget(self.toolButton_remove_row)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.tableView = QtWidgets.QTableView(Dialog)
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.tableView.setObjectName("tableView")
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.tableView)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_statusbar_placeholder = QtWidgets.QHBoxLayout()
        self.horizontalLayout_statusbar_placeholder.setObjectName("horizontalLayout_statusbar_placeholder")
        self.widget_invisible_dummy = QtWidgets.QWidget(Dialog)
        self.widget_invisible_dummy.setObjectName("widget_invisible_dummy")
        self.horizontalLayout_statusbar_placeholder.addWidget(self.widget_invisible_dummy)
        self.verticalLayout_2.addLayout(self.horizontalLayout_statusbar_placeholder)
        self.actionInsert_row = QtWidgets.QAction(Dialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionInsert_row.setIcon(icon)
        self.actionInsert_row.setObjectName("actionInsert_row")
        self.actionRemove_row = QtWidgets.QAction(Dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRemove_row.setIcon(icon1)
        self.actionRemove_row.setObjectName("actionRemove_row")

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Add relationships", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Dialog", "Relationship class", None, -1))
        self.toolButton_insert_row.setText(QtWidgets.QApplication.translate("Dialog", "...", None, -1))
        self.toolButton_remove_row.setText(QtWidgets.QApplication.translate("Dialog", "...", None, -1))
        self.actionInsert_row.setText(QtWidgets.QApplication.translate("Dialog", "Insert row", None, -1))
        self.actionInsert_row.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Insert row below current one <span style=\" font-weight:600;\">(Ctrl+Ins)</span></p></body></html>", None, -1))
        self.actionInsert_row.setShortcut(QtWidgets.QApplication.translate("Dialog", "Ctrl+Ins", None, -1))
        self.actionRemove_row.setText(QtWidgets.QApplication.translate("Dialog", "Remove row", None, -1))
        self.actionRemove_row.setToolTip(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p>Remove current row <span style=\" font-weight:600;\">(Ctrl+Del)</span></p></body></html>", None, -1))
        self.actionRemove_row.setShortcut(QtWidgets.QApplication.translate("Dialog", "Ctrl+Del", None, -1))

import resources_icons_rc
