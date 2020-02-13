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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\tool_configuration_assistant.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\tool_configuration_assistant.ui' applies.
#
# Created: Thu Feb 13 11:54:16 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_PackagesForm(object):
    def setupUi(self, PackagesForm):
        PackagesForm.setObjectName("PackagesForm")
        PackagesForm.setWindowModality(QtCore.Qt.ApplicationModal)
        PackagesForm.resize(685, 331)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PackagesForm.sizePolicy().hasHeightForWidth())
        PackagesForm.setSizePolicy(sizePolicy)
        PackagesForm.setMinimumSize(QtCore.QSize(0, 0))
        PackagesForm.setMaximumSize(QtCore.QSize(16777215, 16777215))
        PackagesForm.setMouseTracking(False)
        PackagesForm.setFocusPolicy(QtCore.Qt.StrongFocus)
        PackagesForm.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        PackagesForm.setAutoFillBackground(False)
        self.verticalLayout = QtWidgets.QVBoxLayout(PackagesForm)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.scrollArea = QtWidgets.QScrollArea(PackagesForm)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 681, 327))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_general = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_general.sizePolicy().hasHeightForWidth())
        self.groupBox_general.setSizePolicy(sizePolicy)
        self.groupBox_general.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox_general.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_general.setAutoFillBackground(False)
        self.groupBox_general.setFlat(False)
        self.groupBox_general.setObjectName("groupBox_general")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox_general)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.textBrowser_spine_model = QtWidgets.QTextBrowser(self.groupBox_general)
        self.textBrowser_spine_model.setObjectName("textBrowser_spine_model")
        self.verticalLayout_6.addWidget(self.textBrowser_spine_model)
        self.verticalLayout_2.addWidget(self.groupBox_general)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)
        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.retranslateUi(PackagesForm)
        QtCore.QMetaObject.connectSlotsByName(PackagesForm)

    def retranslateUi(self, PackagesForm):
        PackagesForm.setWindowTitle(QtWidgets.QApplication.translate("PackagesForm", "Tool configuration assistant", None, -1))
        self.groupBox_general.setTitle(QtWidgets.QApplication.translate("PackagesForm", "SpineModel.jl", None, -1))

