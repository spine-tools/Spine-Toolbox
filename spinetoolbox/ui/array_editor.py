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

# Form implementation generated from reading ui file 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\array_editor.ui',
# licensing of 'C:\data\src\toolbox\bin\..\spinetoolbox\ui\array_editor.ui' applies.
#
# Created: Fri Mar 27 09:28:15 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(569, 420)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.splitter = QtWidgets.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.value_type_combo_box = QtWidgets.QComboBox(self.verticalLayoutWidget)
        self.value_type_combo_box.setObjectName("value_type_combo_box")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.value_type_combo_box.addItem("")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.value_type_combo_box)
        self.verticalLayout_3.addLayout(self.formLayout)
        self.array_table_view = CopyPasteTableView(self.verticalLayoutWidget)
        self.array_table_view.setObjectName("array_table_view")
        self.verticalLayout_3.addWidget(self.array_table_view)
        self.plot_widget_stack = QtWidgets.QStackedWidget(self.splitter)
        self.plot_widget_stack.setObjectName("plot_widget_stack")
        self.cannot_plot_page = QtWidgets.QWidget()
        self.cannot_plot_page.setObjectName("cannot_plot_page")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.cannot_plot_page)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.label = QtWidgets.QLabel(self.cannot_plot_page)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem3)
        self.plot_widget_stack.addWidget(self.cannot_plot_page)
        self.plot_page = QtWidgets.QWidget()
        self.plot_page.setObjectName("plot_page")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.plot_page)
        self.verticalLayout.setObjectName("verticalLayout")
        self.plot_widget = PlotWidget(self.plot_page)
        self.plot_widget.setObjectName("plot_widget")
        self.verticalLayout.addWidget(self.plot_widget)
        self.plot_widget_stack.addWidget(self.plot_page)
        self.verticalLayout_4.addWidget(self.splitter)

        self.retranslateUi(Form)
        self.plot_widget_stack.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("Form", "Value type:", None, -1))
        self.value_type_combo_box.setItemText(0, QtWidgets.QApplication.translate("Form", "Float", None, -1))
        self.value_type_combo_box.setItemText(1, QtWidgets.QApplication.translate("Form", "Datetime", None, -1))
        self.value_type_combo_box.setItemText(2, QtWidgets.QApplication.translate("Form", "Duration", None, -1))
        self.value_type_combo_box.setItemText(3, QtWidgets.QApplication.translate("Form", "String", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Cannot plot this data type.", None, -1))

from spinetoolbox.widgets.plot_widget import PlotWidget
from spinetoolbox.widgets.custom_qtableview import CopyPasteTableView
