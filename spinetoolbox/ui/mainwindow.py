#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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

# Form implementation generated from reading ui file '../spinetoolbox/ui/mainwindow.ui'
#
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(993, 565)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.mdiArea = QtWidgets.QMdiArea(self.splitter)
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.mdiArea.setTabsMovable(False)
        self.mdiArea.setObjectName("mdiArea")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox = QtWidgets.QGroupBox(self.verticalLayoutWidget)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.pushButton_add_data_store = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_add_data_store.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_add_data_store.setObjectName("pushButton_add_data_store")
        self.verticalLayout_5.addWidget(self.pushButton_add_data_store)
        self.pushButton_add_data_connection = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_add_data_connection.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_add_data_connection.setObjectName("pushButton_add_data_connection")
        self.verticalLayout_5.addWidget(self.pushButton_add_data_connection)
        self.pushButton_add_tool = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_add_tool.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_add_tool.setObjectName("pushButton_add_tool")
        self.verticalLayout_5.addWidget(self.pushButton_add_tool)
        self.pushButton_add_view = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_add_view.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_add_view.setObjectName("pushButton_add_view")
        self.verticalLayout_5.addWidget(self.pushButton_add_view)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem)
        self.pushButton_test1 = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_test1.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_test1.setObjectName("pushButton_test1")
        self.verticalLayout_5.addWidget(self.pushButton_test1)
        self.pushButton_test2 = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_test2.setMaximumSize(QtCore.QSize(100, 16777215))
        self.pushButton_test2.setObjectName("pushButton_test2")
        self.verticalLayout_5.addWidget(self.pushButton_test2)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setFrameShape(QtWidgets.QFrame.Panel)
        self.label.setFrameShadow(QtWidgets.QFrame.Raised)
        self.label.setLineWidth(1)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.horizontalLayout_4.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 993, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuShow = QtWidgets.QMenu(self.menubar)
        self.menuShow.setObjectName("menuShow")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionData_Store = QtWidgets.QAction(MainWindow)
        self.actionData_Store.setObjectName("actionData_Store")
        self.actionDocumentation = QtWidgets.QAction(MainWindow)
        self.actionDocumentation.setObjectName("actionDocumentation")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionAdd_Data_Connection = QtWidgets.QAction(MainWindow)
        self.actionAdd_Data_Connection.setObjectName("actionAdd_Data_Connection")
        self.actionAdd_Data_Store = QtWidgets.QAction(MainWindow)
        self.actionAdd_Data_Store.setObjectName("actionAdd_Data_Store")
        self.actionAdd_Tool = QtWidgets.QAction(MainWindow)
        self.actionAdd_Tool.setObjectName("actionAdd_Tool")
        self.actionAdd_View = QtWidgets.QAction(MainWindow)
        self.actionAdd_View.setObjectName("actionAdd_View")
        self.menuFile.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionAbout)
        self.menuEdit.addAction(self.actionAdd_Data_Store)
        self.menuEdit.addAction(self.actionAdd_Data_Connection)
        self.menuEdit.addAction(self.actionAdd_Tool)
        self.menuEdit.addAction(self.actionAdd_View)
        self.menuShow.addAction(self.actionData_Store)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuShow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Spine Toolbox", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("MainWindow", "Add Item", None, -1))
        self.pushButton_add_data_store.setText(QtWidgets.QApplication.translate("MainWindow", "Data Store", None, -1))
        self.pushButton_add_data_connection.setText(QtWidgets.QApplication.translate("MainWindow", "Data Connection", None, -1))
        self.pushButton_add_tool.setText(QtWidgets.QApplication.translate("MainWindow", "Tool", None, -1))
        self.pushButton_add_view.setText(QtWidgets.QApplication.translate("MainWindow", "View", None, -1))
        self.pushButton_test1.setText(QtWidgets.QApplication.translate("MainWindow", "Test1", None, -1))
        self.pushButton_test2.setText(QtWidgets.QApplication.translate("MainWindow", "Test2", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Selected Item", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuHelp.setTitle(QtWidgets.QApplication.translate("MainWindow", "Help", None, -1))
        self.menuEdit.setTitle(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.menuShow.setTitle(QtWidgets.QApplication.translate("MainWindow", "Show", None, -1))
        self.actionQuit.setText(QtWidgets.QApplication.translate("MainWindow", "Quit", None, -1))
        self.actionQuit.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+Q", None, -1))
        self.actionData_Store.setText(QtWidgets.QApplication.translate("MainWindow", "Data Store", None, -1))
        self.actionDocumentation.setText(QtWidgets.QApplication.translate("MainWindow", "Documentation", None, -1))
        self.actionAbout.setText(QtWidgets.QApplication.translate("MainWindow", "About", None, -1))
        self.actionAbout.setShortcut(QtWidgets.QApplication.translate("MainWindow", "F12", None, -1))
        self.actionAdd_Data_Connection.setText(QtWidgets.QApplication.translate("MainWindow", "Add Data Connection", None, -1))
        self.actionAdd_Data_Store.setText(QtWidgets.QApplication.translate("MainWindow", "Add Data Store", None, -1))
        self.actionAdd_Tool.setText(QtWidgets.QApplication.translate("MainWindow", "Add Tool", None, -1))
        self.actionAdd_View.setText(QtWidgets.QApplication.translate("MainWindow", "Add View", None, -1))

