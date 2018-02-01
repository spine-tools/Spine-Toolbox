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

# Form implementation generated from reading ui file '../spinetoolbox/ui/data_store_form.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_DataStoreForm(object):
    def setupUi(self, DataStoreForm):
        DataStoreForm.setObjectName("DataStoreForm")
        DataStoreForm.resize(800, 590)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DataStoreForm)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.treeWidget = QtWidgets.QTreeWidget(DataStoreForm)
        self.treeWidget.setObjectName("treeWidget")
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.NoBrush)
        item_1.setBackground(0, brush)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        self.treeWidget.header().setDefaultSectionSize(186)
        self.horizontalLayout.addWidget(self.treeWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(DataStoreForm)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.treeWidget_2 = QtWidgets.QTreeWidget(DataStoreForm)
        self.treeWidget_2.setObjectName("treeWidget_2")
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)
        self.treeWidget_2.header().setDefaultSectionSize(110)
        self.verticalLayout.addWidget(self.treeWidget_2)
        self.label_2 = QtWidgets.QLabel(DataStoreForm)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.treeWidget_3 = QtWidgets.QTreeWidget(DataStoreForm)
        self.treeWidget_3.setObjectName("treeWidget_3")
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_3)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_3)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget_3)
        self.treeWidget_3.header().setDefaultSectionSize(110)
        self.verticalLayout.addWidget(self.treeWidget_3)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(DataStoreForm)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.pushButton_2 = QtWidgets.QPushButton(DataStoreForm)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.pushButton_3 = QtWidgets.QPushButton(DataStoreForm)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_2.addWidget(self.pushButton_3)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.retranslateUi(DataStoreForm)
        QtCore.QMetaObject.connectSlotsByName(DataStoreForm)

    def retranslateUi(self, DataStoreForm):
        DataStoreForm.setWindowTitle(QtWidgets.QApplication.translate("DataStoreForm", "Data Store", None, -1))
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.headerItem().setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Object Tree", None, -1))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Unit", None, -1))
        self.treeWidget.topLevelItem(0).child(0).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget.topLevelItem(0).child(0).child(0).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_CONTROLAREA", None, -1))
        self.treeWidget.topLevelItem(0).child(0).child(1).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_CONSTRAINT", None, -1))
        self.treeWidget.topLevelItem(0).child(0).child(2).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_AVAILSTS", None, -1))
        self.treeWidget.topLevelItem(0).child(0).child(3).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_AVAILDTS", None, -1))
        self.treeWidget.topLevelItem(0).child(1).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "AA3", None, -1))
        self.treeWidget.topLevelItem(0).child(2).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "AA2", None, -1))
        self.treeWidget.topLevelItem(0).child(3).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "AA1", None, -1))
        self.treeWidget.topLevelItem(1).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Transmission Node", None, -1))
        self.treeWidget.topLevelItem(2).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Transmission Branch", None, -1))
        self.treeWidget.topLevelItem(3).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Time Slice Definition", None, -1))
        self.treeWidget.topLevelItem(4).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Storage", None, -1))
        self.treeWidget.topLevelItem(5).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Reserve", None, -1))
        self.treeWidget.topLevelItem(6).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "Fuel", None, -1))
        self.treeWidget.setSortingEnabled(__sortingEnabled)
        self.label.setText(QtWidgets.QApplication.translate("DataStoreForm", "Object Parameters", None, -1))
        self.treeWidget_2.setSortingEnabled(True)
        self.treeWidget_2.headerItem().setText(0, QtWidgets.QApplication.translate("DataStoreForm", "o_id", None, -1))
        self.treeWidget_2.headerItem().setText(1, QtWidgets.QApplication.translate("DataStoreForm", "p_id", None, -1))
        self.treeWidget_2.headerItem().setText(2, QtWidgets.QApplication.translate("DataStoreForm", "t_id", None, -1))
        __sortingEnabled = self.treeWidget_2.isSortingEnabled()
        self.treeWidget_2.setSortingEnabled(False)
        self.treeWidget_2.topLevelItem(0).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_2.topLevelItem(0).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "FORCED_OUTAGE", None, -1))
        self.treeWidget_2.topLevelItem(0).setText(2, QtWidgets.QApplication.translate("DataStoreForm", "HS", None, -1))
        self.treeWidget_2.topLevelItem(1).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_2.topLevelItem(1).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "SOD", None, -1))
        self.treeWidget_2.topLevelItem(2).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_2.topLevelItem(2).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "MTTR", None, -1))
        self.treeWidget_2.setSortingEnabled(__sortingEnabled)
        self.label_2.setText(QtWidgets.QApplication.translate("DataStoreForm", "Membership Parameters", None, -1))
        self.treeWidget_3.setSortingEnabled(True)
        self.treeWidget_3.headerItem().setText(0, QtWidgets.QApplication.translate("DataStoreForm", "mc_id", None, -1))
        self.treeWidget_3.headerItem().setText(1, QtWidgets.QApplication.translate("DataStoreForm", "o_id1", None, -1))
        self.treeWidget_3.headerItem().setText(2, QtWidgets.QApplication.translate("DataStoreForm", "o_id2", None, -1))
        __sortingEnabled = self.treeWidget_3.isSortingEnabled()
        self.treeWidget_3.setSortingEnabled(False)
        self.treeWidget_3.topLevelItem(0).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_RESERVE", None, -1))
        self.treeWidget_3.topLevelItem(0).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_3.topLevelItem(0).setText(2, QtWidgets.QApplication.translate("DataStoreForm", "SOR", None, -1))
        self.treeWidget_3.topLevelItem(1).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_RESERVE", None, -1))
        self.treeWidget_3.topLevelItem(1).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_3.topLevelItem(1).setText(2, QtWidgets.QApplication.translate("DataStoreForm", "TOR", None, -1))
        self.treeWidget_3.topLevelItem(2).setText(0, QtWidgets.QApplication.translate("DataStoreForm", "UNIT_RESERVE", None, -1))
        self.treeWidget_3.topLevelItem(2).setText(1, QtWidgets.QApplication.translate("DataStoreForm", "CPS_CCGT", None, -1))
        self.treeWidget_3.topLevelItem(2).setText(2, QtWidgets.QApplication.translate("DataStoreForm", "DYN_NI", None, -1))
        self.treeWidget_3.setSortingEnabled(__sortingEnabled)
        self.pushButton.setText(QtWidgets.QApplication.translate("DataStoreForm", "New", None, -1))
        self.pushButton_2.setText(QtWidgets.QApplication.translate("DataStoreForm", "Modify", None, -1))
        self.pushButton_3.setText(QtWidgets.QApplication.translate("DataStoreForm", "Import", None, -1))

