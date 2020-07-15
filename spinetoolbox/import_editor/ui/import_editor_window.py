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

################################################################################
## Form generated from reading UI file 'import_editor_window.ui'
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

from spinetoolbox.widgets.table_view_with_button_header import TableViewWithButtonHeader


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1197, 697)
        MainWindow.setDockNestingEnabled(True)
        self.actionExportMappings = QAction(MainWindow)
        self.actionExportMappings.setObjectName(u"actionExportMappings")
        self.actionImportMappings = QAction(MainWindow)
        self.actionImportMappings.setObjectName(u"actionImportMappings")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionClose = QAction(MainWindow)
        self.actionClose.setObjectName(u"actionClose")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1197, 28))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(False)
        MainWindow.setStatusBar(self.statusbar)
        self.dockWidget_sources = QDockWidget(MainWindow)
        self.dockWidget_sources.setObjectName(u"dockWidget_sources")
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.source_list = QListWidget(self.dockWidgetContents)
        self.source_list.setObjectName(u"source_list")
        self.source_list.setContextMenuPolicy(Qt.CustomContextMenu)

        self.verticalLayout_2.addWidget(self.source_list)

        self.dockWidget_sources.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget_sources)
        self.dockWidget_source_options = QDockWidget(MainWindow)
        self.dockWidget_source_options.setObjectName(u"dockWidget_source_options")
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName(u"dockWidgetContents_2")
        self.verticalLayout_5 = QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.dockWidget_source_options.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget_source_options)
        self.dockWidget_source_data = QDockWidget(MainWindow)
        self.dockWidget_source_data.setObjectName(u"dockWidget_source_data")
        self.dockWidgetContents_3 = QWidget()
        self.dockWidgetContents_3.setObjectName(u"dockWidgetContents_3")
        self.verticalLayout_6 = QVBoxLayout(self.dockWidgetContents_3)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.source_preview_widget_stack = QStackedWidget(self.dockWidgetContents_3)
        self.source_preview_widget_stack.setObjectName(u"source_preview_widget_stack")
        self.table_page = QWidget()
        self.table_page.setObjectName(u"table_page")
        self.verticalLayout_3 = QVBoxLayout(self.table_page)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.source_data_table = TableViewWithButtonHeader(self.table_page)
        self.source_data_table.setObjectName(u"source_data_table")

        self.verticalLayout_3.addWidget(self.source_data_table)

        self.source_preview_widget_stack.addWidget(self.table_page)
        self.loading_page = QWidget()
        self.loading_page.setObjectName(u"loading_page")
        self.verticalLayout_4 = QVBoxLayout(self.loading_page)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.waiting_label = QLabel(self.loading_page)
        self.waiting_label.setObjectName(u"waiting_label")

        self.horizontalLayout.addWidget(self.waiting_label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.source_preview_widget_stack.addWidget(self.loading_page)

        self.verticalLayout_6.addWidget(self.source_preview_widget_stack)

        self.dockWidget_source_data.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget_source_data)
        self.dockWidget_mappings = QDockWidget(MainWindow)
        self.dockWidget_mappings.setObjectName(u"dockWidget_mappings")
        self.dockWidgetContents_4 = QWidget()
        self.dockWidgetContents_4.setObjectName(u"dockWidgetContents_4")
        self.verticalLayout_7 = QVBoxLayout(self.dockWidgetContents_4)
        self.verticalLayout_7.setSpacing(6)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.new_button = QPushButton(self.dockWidgetContents_4)
        self.new_button.setObjectName(u"new_button")

        self.button_layout.addWidget(self.new_button)

        self.remove_button = QPushButton(self.dockWidgetContents_4)
        self.remove_button.setObjectName(u"remove_button")

        self.button_layout.addWidget(self.remove_button)


        self.verticalLayout_7.addLayout(self.button_layout)

        self.list_view = QListView(self.dockWidgetContents_4)
        self.list_view.setObjectName(u"list_view")

        self.verticalLayout_7.addWidget(self.list_view)

        self.dockWidget_mappings.setWidget(self.dockWidgetContents_4)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget_mappings)
        self.dockWidget_mapping_options = QDockWidget(MainWindow)
        self.dockWidget_mapping_options.setObjectName(u"dockWidget_mapping_options")
        self.dockWidgetContents_5 = QWidget()
        self.dockWidgetContents_5.setObjectName(u"dockWidgetContents_5")
        self.formLayout_2 = QFormLayout(self.dockWidgetContents_5)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setHorizontalSpacing(6)
        self.formLayout_2.setVerticalSpacing(6)
        self.formLayout_2.setContentsMargins(9, 9, 9, 9)
        self.class_type_label = QLabel(self.dockWidgetContents_5)
        self.class_type_label.setObjectName(u"class_type_label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.class_type_label)

        self.class_type_combo_box = QComboBox(self.dockWidgetContents_5)
        self.class_type_combo_box.addItem("")
        self.class_type_combo_box.addItem("")
        self.class_type_combo_box.setObjectName(u"class_type_combo_box")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.class_type_combo_box)

        self.parameter_type_label = QLabel(self.dockWidgetContents_5)
        self.parameter_type_label.setObjectName(u"parameter_type_label")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.parameter_type_label)

        self.parameter_type_combo_box = QComboBox(self.dockWidgetContents_5)
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.addItem("")
        self.parameter_type_combo_box.setObjectName(u"parameter_type_combo_box")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.parameter_type_combo_box)

        self.read_start_row_label = QLabel(self.dockWidgetContents_5)
        self.read_start_row_label.setObjectName(u"read_start_row_label")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.read_start_row_label)

        self.start_read_row_spin_box = QSpinBox(self.dockWidgetContents_5)
        self.start_read_row_spin_box.setObjectName(u"start_read_row_spin_box")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.start_read_row_spin_box)

        self.ignore_columns_label = QLabel(self.dockWidgetContents_5)
        self.ignore_columns_label.setObjectName(u"ignore_columns_label")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.ignore_columns_label)

        self.ignore_columns_button = QPushButton(self.dockWidgetContents_5)
        self.ignore_columns_button.setObjectName(u"ignore_columns_button")

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.ignore_columns_button)

        self.dimension_label = QLabel(self.dockWidgetContents_5)
        self.dimension_label.setObjectName(u"dimension_label")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.dimension_label)

        self.dimension_spin_box = QSpinBox(self.dockWidgetContents_5)
        self.dimension_spin_box.setObjectName(u"dimension_spin_box")
        self.dimension_spin_box.setMinimum(1)

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.dimension_spin_box)

        self.time_series_repeat_check_box = QCheckBox(self.dockWidgetContents_5)
        self.time_series_repeat_check_box.setObjectName(u"time_series_repeat_check_box")

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.time_series_repeat_check_box)

        self.map_dimensions_label = QLabel(self.dockWidgetContents_5)
        self.map_dimensions_label.setObjectName(u"map_dimensions_label")

        self.formLayout_2.setWidget(7, QFormLayout.LabelRole, self.map_dimensions_label)

        self.map_dimension_spin_box = QSpinBox(self.dockWidgetContents_5)
        self.map_dimension_spin_box.setObjectName(u"map_dimension_spin_box")
        self.map_dimension_spin_box.setMinimum(1)

        self.formLayout_2.setWidget(7, QFormLayout.FieldRole, self.map_dimension_spin_box)

        self.import_objects_check_box = QCheckBox(self.dockWidgetContents_5)
        self.import_objects_check_box.setObjectName(u"import_objects_check_box")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.import_objects_check_box)

        self.dockWidget_mapping_options.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget_mapping_options)
        self.dockWidget_mapping_spec = QDockWidget(MainWindow)
        self.dockWidget_mapping_spec.setObjectName(u"dockWidget_mapping_spec")
        self.dockWidgetContents_6 = QWidget()
        self.dockWidgetContents_6.setObjectName(u"dockWidgetContents_6")
        self.verticalLayout_8 = QVBoxLayout(self.dockWidgetContents_6)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.table_view_mappings = QTableView(self.dockWidgetContents_6)
        self.table_view_mappings.setObjectName(u"table_view_mappings")

        self.verticalLayout_8.addWidget(self.table_view_mappings)

        self.dockWidget_mapping_spec.setWidget(self.dockWidgetContents_6)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget_mapping_spec)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionExportMappings)
        self.menuFile.addAction(self.actionImportMappings)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)

        self.retranslateUi(MainWindow)

        self.source_preview_widget_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Import preview", None))
        self.actionExportMappings.setText(QCoreApplication.translate("MainWindow", u"Export mappings...", None))
        self.actionImportMappings.setText(QCoreApplication.translate("MainWindow", u"Import mappings...", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionClose.setText(QCoreApplication.translate("MainWindow", u"Close", None))
#if QT_CONFIG(shortcut)
        self.actionClose.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+W", None))
#endif // QT_CONFIG(shortcut)
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.dockWidget_sources.setWindowTitle(QCoreApplication.translate("MainWindow", u"Sources", None))
        self.dockWidget_source_options.setWindowTitle(QCoreApplication.translate("MainWindow", u"Source options", None))
        self.dockWidget_source_data.setWindowTitle(QCoreApplication.translate("MainWindow", u"Source data", None))
        self.waiting_label.setText(QCoreApplication.translate("MainWindow", u"Loading preview...", None))
        self.dockWidget_mappings.setWindowTitle(QCoreApplication.translate("MainWindow", u"Mappings", None))
        self.new_button.setText(QCoreApplication.translate("MainWindow", u"New", None))
        self.remove_button.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.dockWidget_mapping_options.setWindowTitle(QCoreApplication.translate("MainWindow", u"Mapping options", None))
        self.class_type_label.setText(QCoreApplication.translate("MainWindow", u"Class type:", None))
        self.class_type_combo_box.setItemText(0, QCoreApplication.translate("MainWindow", u"Object", None))
        self.class_type_combo_box.setItemText(1, QCoreApplication.translate("MainWindow", u"Relationship", None))

        self.parameter_type_label.setText(QCoreApplication.translate("MainWindow", u"Parameter type:", None))
        self.parameter_type_combo_box.setItemText(0, QCoreApplication.translate("MainWindow", u"Single value", None))
        self.parameter_type_combo_box.setItemText(1, QCoreApplication.translate("MainWindow", u"Time series", None))
        self.parameter_type_combo_box.setItemText(2, QCoreApplication.translate("MainWindow", u"Time pattern", None))
        self.parameter_type_combo_box.setItemText(3, QCoreApplication.translate("MainWindow", u"Map", None))
        self.parameter_type_combo_box.setItemText(4, QCoreApplication.translate("MainWindow", u"Array", None))
        self.parameter_type_combo_box.setItemText(5, QCoreApplication.translate("MainWindow", u"Definition", None))
        self.parameter_type_combo_box.setItemText(6, QCoreApplication.translate("MainWindow", u"None", None))

        self.read_start_row_label.setText(QCoreApplication.translate("MainWindow", u"Read data from row:", None))
        self.ignore_columns_label.setText(QCoreApplication.translate("MainWindow", u"Ignore columns:", None))
        self.ignore_columns_button.setText("")
        self.dimension_label.setText(QCoreApplication.translate("MainWindow", u"Number of dimensions:", None))
#if QT_CONFIG(tooltip)
        self.time_series_repeat_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Set the repeat flag for all imported time series", None))
#endif // QT_CONFIG(tooltip)
        self.time_series_repeat_check_box.setText(QCoreApplication.translate("MainWindow", u"Repeat time series", None))
        self.map_dimensions_label.setText(QCoreApplication.translate("MainWindow", u"Map dimensions:", None))
        self.import_objects_check_box.setText(QCoreApplication.translate("MainWindow", u"Import objects", None))
        self.dockWidget_mapping_spec.setWindowTitle(QCoreApplication.translate("MainWindow", u"Maping specification", None))
    # retranslateUi

