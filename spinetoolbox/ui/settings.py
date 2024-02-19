# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractScrollArea, QAbstractSpinBox,
    QApplication, QButtonGroup, QCheckBox, QComboBox,
    QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QPushButton,
    QRadioButton, QSizePolicy, QSlider, QSpacerItem,
    QSpinBox, QSplitter, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_combobox import CustomQComboBox
from spinetoolbox import resources_icons_rc

class Ui_SettingsForm(object):
    def setupUi(self, SettingsForm):
        if not SettingsForm.objectName():
            SettingsForm.setObjectName(u"SettingsForm")
        SettingsForm.setWindowModality(Qt.ApplicationModal)
        SettingsForm.resize(783, 692)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SettingsForm.sizePolicy().hasHeightForWidth())
        SettingsForm.setSizePolicy(sizePolicy)
        SettingsForm.setMinimumSize(QSize(500, 350))
        SettingsForm.setMaximumSize(QSize(16777215, 16777215))
        SettingsForm.setMouseTracking(False)
        SettingsForm.setFocusPolicy(Qt.StrongFocus)
        SettingsForm.setContextMenuPolicy(Qt.NoContextMenu)
        SettingsForm.setAutoFillBackground(False)
        self.verticalLayout_7 = QVBoxLayout(SettingsForm)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.splitter = QSplitter(SettingsForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.listWidget = QListWidget(self.splitter)
        icon = QIcon()
        icon.addFile(u":/icons/sliders-h.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem = QListWidgetItem(self.listWidget)
        __qlistwidgetitem.setIcon(icon);
        __qlistwidgetitem.setFlags(Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        icon1 = QIcon()
        icon1.addFile(u":/icons/project_item_icons/hammer.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem1.setIcon(icon1);
        icon2 = QIcon()
        icon2.addFile(u":/icons/database.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem2.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u":/icons/wrench.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem3.setIcon(icon3);
        icon4 = QIcon()
        icon4.addFile(u":/icons/tractor.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem4 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem4.setIcon(icon4);
        self.listWidget.setObjectName(u"listWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy1)
        self.listWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listWidget.setProperty("showDropIndicator", True)
        self.listWidget.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.listWidget.setDefaultDropAction(Qt.CopyAction)
        self.listWidget.setAlternatingRowColors(False)
        self.listWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listWidget.setMovement(QListView.Static)
        self.listWidget.setFlow(QListView.TopToBottom)
        self.listWidget.setProperty("isWrapping", False)
        self.listWidget.setResizeMode(QListView.Fixed)
        self.listWidget.setLayoutMode(QListView.SinglePass)
        self.listWidget.setSpacing(0)
        self.listWidget.setViewMode(QListView.ListMode)
        self.listWidget.setUniformItemSizes(True)
        self.listWidget.setSelectionRectVisible(True)
        self.splitter.addWidget(self.listWidget)
        self.stackedWidget = QStackedWidget(self.splitter)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(2)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy2)
        self.General = QWidget()
        self.General.setObjectName(u"General")
        self.verticalLayout_6 = QVBoxLayout(self.General)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.groupBox_general = QGroupBox(self.General)
        self.groupBox_general.setObjectName(u"groupBox_general")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_general.sizePolicy().hasHeightForWidth())
        self.groupBox_general.setSizePolicy(sizePolicy3)
        self.groupBox_general.setMinimumSize(QSize(0, 0))
        self.groupBox_general.setMaximumSize(QSize(16777215, 16777215))
        self.groupBox_general.setAutoFillBackground(False)
        self.groupBox_general.setFlat(False)
        self.gridLayout = QGridLayout(self.groupBox_general)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label = QLabel(self.groupBox_general)
        self.label.setObjectName(u"label")

        self.horizontalLayout_6.addWidget(self.label)

        self.lineEdit_work_dir = QLineEdit(self.groupBox_general)
        self.lineEdit_work_dir.setObjectName(u"lineEdit_work_dir")
        self.lineEdit_work_dir.setMinimumSize(QSize(0, 20))
        self.lineEdit_work_dir.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.lineEdit_work_dir)

        self.toolButton_browse_work = QToolButton(self.groupBox_general)
        self.toolButton_browse_work.setObjectName(u"toolButton_browse_work")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.toolButton_browse_work.sizePolicy().hasHeightForWidth())
        self.toolButton_browse_work.setSizePolicy(sizePolicy4)
        icon5 = QIcon()
        icon5.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_browse_work.setIcon(icon5)

        self.horizontalLayout_6.addWidget(self.toolButton_browse_work)


        self.gridLayout.addLayout(self.horizontalLayout_6, 13, 0, 1, 1)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_2 = QLabel(self.groupBox_general)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.project_save_options_combo_box = QComboBox(self.groupBox_general)
        self.project_save_options_combo_box.addItem("")
        self.project_save_options_combo_box.addItem("")
        self.project_save_options_combo_box.setObjectName(u"project_save_options_combo_box")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.project_save_options_combo_box)


        self.gridLayout.addLayout(self.formLayout_2, 5, 0, 1, 1)

        self.checkBox_custom_open_project_dialog = QCheckBox(self.groupBox_general)
        self.checkBox_custom_open_project_dialog.setObjectName(u"checkBox_custom_open_project_dialog")
        self.checkBox_custom_open_project_dialog.setChecked(False)

        self.gridLayout.addWidget(self.checkBox_custom_open_project_dialog, 1, 0, 1, 1)

        self.checkBox_delete_data = QCheckBox(self.groupBox_general)
        self.checkBox_delete_data.setObjectName(u"checkBox_delete_data")

        self.gridLayout.addWidget(self.checkBox_delete_data, 2, 0, 1, 1)

        self.checkBox_exit_prompt = QCheckBox(self.groupBox_general)
        self.checkBox_exit_prompt.setObjectName(u"checkBox_exit_prompt")
        self.checkBox_exit_prompt.setTristate(False)

        self.gridLayout.addWidget(self.checkBox_exit_prompt, 4, 0, 1, 1)

        self.checkBox_open_previous_project = QCheckBox(self.groupBox_general)
        self.checkBox_open_previous_project.setObjectName(u"checkBox_open_previous_project")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.checkBox_open_previous_project.sizePolicy().hasHeightForWidth())
        self.checkBox_open_previous_project.setSizePolicy(sizePolicy5)

        self.gridLayout.addWidget(self.checkBox_open_previous_project, 3, 0, 1, 1)


        self.verticalLayout_6.addWidget(self.groupBox_general)

        self.groupBox_ui = QGroupBox(self.General)
        self.groupBox_ui.setObjectName(u"groupBox_ui")
        self.gridLayout_2 = QGridLayout(self.groupBox_ui)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.checkBox_use_smooth_zoom = QCheckBox(self.groupBox_ui)
        self.checkBox_use_smooth_zoom.setObjectName(u"checkBox_use_smooth_zoom")

        self.gridLayout_2.addWidget(self.checkBox_use_smooth_zoom, 10, 0, 1, 1)

        self.checkBox_datetime = QCheckBox(self.groupBox_ui)
        self.checkBox_datetime.setObjectName(u"checkBox_datetime")

        self.gridLayout_2.addWidget(self.checkBox_datetime, 8, 0, 1, 1)

        self.checkBox_use_curved_links = QCheckBox(self.groupBox_ui)
        self.checkBox_use_curved_links.setObjectName(u"checkBox_use_curved_links")

        self.gridLayout_2.addWidget(self.checkBox_use_curved_links, 4, 0, 1, 1)

        self.checkBox_color_properties_widgets = QCheckBox(self.groupBox_ui)
        self.checkBox_color_properties_widgets.setObjectName(u"checkBox_color_properties_widgets")

        self.gridLayout_2.addWidget(self.checkBox_color_properties_widgets, 3, 0, 1, 1)

        self.checkBox_color_toolbar_icons = QCheckBox(self.groupBox_ui)
        self.checkBox_color_toolbar_icons.setObjectName(u"checkBox_color_toolbar_icons")

        self.gridLayout_2.addWidget(self.checkBox_color_toolbar_icons, 2, 0, 1, 1)

        self.checkBox_prevent_overlapping = QCheckBox(self.groupBox_ui)
        self.checkBox_prevent_overlapping.setObjectName(u"checkBox_prevent_overlapping")

        self.gridLayout_2.addWidget(self.checkBox_prevent_overlapping, 6, 0, 1, 1)

        self.checkBox_use_rounded_items = QCheckBox(self.groupBox_ui)
        self.checkBox_use_rounded_items.setObjectName(u"checkBox_use_rounded_items")

        self.gridLayout_2.addWidget(self.checkBox_use_rounded_items, 7, 0, 1, 1)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_7 = QLabel(self.groupBox_ui)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_7)

        self.frame_2 = QFrame(self.groupBox_ui)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Sunken)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.radioButton_bg_grid = QRadioButton(self.frame_2)
        self.radioButton_bg_grid.setObjectName(u"radioButton_bg_grid")

        self.horizontalLayout_4.addWidget(self.radioButton_bg_grid)

        self.radioButton_bg_tree = QRadioButton(self.frame_2)
        self.radioButton_bg_tree.setObjectName(u"radioButton_bg_tree")

        self.horizontalLayout_4.addWidget(self.radioButton_bg_tree)

        self.radioButton_bg_solid = QRadioButton(self.frame_2)
        self.radioButton_bg_solid.setObjectName(u"radioButton_bg_solid")
        self.radioButton_bg_solid.setChecked(True)

        self.horizontalLayout_4.addWidget(self.radioButton_bg_solid)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.label_9 = QLabel(self.frame_2)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_4.addWidget(self.label_9)

        self.toolButton_bg_color = QToolButton(self.frame_2)
        self.toolButton_bg_color.setObjectName(u"toolButton_bg_color")
        self.toolButton_bg_color.setIconSize(QSize(16, 16))

        self.horizontalLayout_4.addWidget(self.toolButton_bg_color)


        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.frame_2)

        self.label_4 = QLabel(self.groupBox_ui)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.frame_1 = QFrame(self.groupBox_ui)
        self.frame_1.setObjectName(u"frame_1")
        self.frame_1.setFrameShape(QFrame.StyledPanel)
        self.frame_1.setFrameShadow(QFrame.Sunken)
        self.horizontalLayout_17 = QHBoxLayout(self.frame_1)
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_1)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_17.addWidget(self.label_5)

        self.horizontalSlider_data_flow_animation_duration = QSlider(self.frame_1)
        self.horizontalSlider_data_flow_animation_duration.setObjectName(u"horizontalSlider_data_flow_animation_duration")
        self.horizontalSlider_data_flow_animation_duration.setStyleSheet(u"")
        self.horizontalSlider_data_flow_animation_duration.setMinimum(1)
        self.horizontalSlider_data_flow_animation_duration.setMaximum(250)
        self.horizontalSlider_data_flow_animation_duration.setSingleStep(10)
        self.horizontalSlider_data_flow_animation_duration.setPageStep(50)
        self.horizontalSlider_data_flow_animation_duration.setSliderPosition(100)
        self.horizontalSlider_data_flow_animation_duration.setTracking(False)
        self.horizontalSlider_data_flow_animation_duration.setOrientation(Qt.Horizontal)
        self.horizontalSlider_data_flow_animation_duration.setInvertedAppearance(True)
        self.horizontalSlider_data_flow_animation_duration.setInvertedControls(False)

        self.horizontalLayout_17.addWidget(self.horizontalSlider_data_flow_animation_duration)

        self.label_8 = QLabel(self.frame_1)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_17.addWidget(self.label_8)


        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.frame_1)


        self.gridLayout_2.addLayout(self.formLayout, 12, 0, 1, 1)

        self.checkBox_drag_to_draw_links = QCheckBox(self.groupBox_ui)
        self.checkBox_drag_to_draw_links.setObjectName(u"checkBox_drag_to_draw_links")

        self.gridLayout_2.addWidget(self.checkBox_drag_to_draw_links, 5, 0, 1, 1)


        self.verticalLayout_6.addWidget(self.groupBox_ui)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.General)
        self.ExternalTools = QWidget()
        self.ExternalTools.setObjectName(u"ExternalTools")
        self.verticalLayout_13 = QVBoxLayout(self.ExternalTools)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.groupBox_gams = QGroupBox(self.ExternalTools)
        self.groupBox_gams.setObjectName(u"groupBox_gams")
        self.gridLayout_4 = QGridLayout(self.groupBox_gams)
        self.gridLayout_4.setSpacing(6)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_11 = QLabel(self.groupBox_gams)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_4.addWidget(self.label_11, 1, 0, 1, 1)

        self.lineEdit_gams_path = QLineEdit(self.groupBox_gams)
        self.lineEdit_gams_path.setObjectName(u"lineEdit_gams_path")
        self.lineEdit_gams_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_gams_path.setClearButtonEnabled(True)

        self.gridLayout_4.addWidget(self.lineEdit_gams_path, 2, 0, 1, 1)

        self.toolButton_browse_gams = QToolButton(self.groupBox_gams)
        self.toolButton_browse_gams.setObjectName(u"toolButton_browse_gams")
        self.toolButton_browse_gams.setIcon(icon5)

        self.gridLayout_4.addWidget(self.toolButton_browse_gams, 2, 1, 1, 1)


        self.verticalLayout_13.addWidget(self.groupBox_gams)

        self.groupBox_julia = QGroupBox(self.ExternalTools)
        self.groupBox_julia.setObjectName(u"groupBox_julia")
        self.verticalLayout_10 = QVBoxLayout(self.groupBox_julia)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(-1, 9, -1, -1)
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.radioButton_use_julia_basic_console = QRadioButton(self.groupBox_julia)
        self.radioButton_use_julia_basic_console.setObjectName(u"radioButton_use_julia_basic_console")

        self.verticalLayout.addWidget(self.radioButton_use_julia_basic_console)

        self.radioButton_use_julia_jupyter_console = QRadioButton(self.groupBox_julia)
        self.radioButton_use_julia_jupyter_console.setObjectName(u"radioButton_use_julia_jupyter_console")

        self.verticalLayout.addWidget(self.radioButton_use_julia_jupyter_console)


        self.horizontalLayout_14.addLayout(self.verticalLayout)

        self.line_3 = QFrame(self.groupBox_julia)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_14.addWidget(self.line_3)

        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lineEdit_julia_path = QLineEdit(self.groupBox_julia)
        self.lineEdit_julia_path.setObjectName(u"lineEdit_julia_path")
        self.lineEdit_julia_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_julia_path.setClearButtonEnabled(True)

        self.horizontalLayout_8.addWidget(self.lineEdit_julia_path)

        self.toolButton_browse_julia = QToolButton(self.groupBox_julia)
        self.toolButton_browse_julia.setObjectName(u"toolButton_browse_julia")
        self.toolButton_browse_julia.setIcon(icon5)

        self.horizontalLayout_8.addWidget(self.toolButton_browse_julia)


        self.verticalLayout_15.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lineEdit_julia_project_path = QLineEdit(self.groupBox_julia)
        self.lineEdit_julia_project_path.setObjectName(u"lineEdit_julia_project_path")
        self.lineEdit_julia_project_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_julia_project_path.setClearButtonEnabled(True)

        self.horizontalLayout_7.addWidget(self.lineEdit_julia_project_path)

        self.toolButton_browse_julia_project = QToolButton(self.groupBox_julia)
        self.toolButton_browse_julia_project.setObjectName(u"toolButton_browse_julia_project")
        self.toolButton_browse_julia_project.setIcon(icon5)

        self.horizontalLayout_7.addWidget(self.toolButton_browse_julia_project)


        self.verticalLayout_15.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.comboBox_julia_kernel = CustomQComboBox(self.groupBox_julia)
        self.comboBox_julia_kernel.setObjectName(u"comboBox_julia_kernel")
        sizePolicy6 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.comboBox_julia_kernel.sizePolicy().hasHeightForWidth())
        self.comboBox_julia_kernel.setSizePolicy(sizePolicy6)
        self.comboBox_julia_kernel.setContextMenuPolicy(Qt.CustomContextMenu)
        self.comboBox_julia_kernel.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)

        self.horizontalLayout_9.addWidget(self.comboBox_julia_kernel)

        self.pushButton_make_julia_kernel = QPushButton(self.groupBox_julia)
        self.pushButton_make_julia_kernel.setObjectName(u"pushButton_make_julia_kernel")
        sizePolicy5.setHeightForWidth(self.pushButton_make_julia_kernel.sizePolicy().hasHeightForWidth())
        self.pushButton_make_julia_kernel.setSizePolicy(sizePolicy5)

        self.horizontalLayout_9.addWidget(self.pushButton_make_julia_kernel)


        self.verticalLayout_15.addLayout(self.horizontalLayout_9)


        self.horizontalLayout_14.addLayout(self.verticalLayout_15)


        self.verticalLayout_10.addLayout(self.horizontalLayout_14)

        self.line = QFrame(self.groupBox_julia)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_10.addWidget(self.line)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.pushButton_install_julia = QPushButton(self.groupBox_julia)
        self.pushButton_install_julia.setObjectName(u"pushButton_install_julia")

        self.horizontalLayout_12.addWidget(self.pushButton_install_julia)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer)

        self.pushButton_add_up_spine_opt = QPushButton(self.groupBox_julia)
        self.pushButton_add_up_spine_opt.setObjectName(u"pushButton_add_up_spine_opt")

        self.horizontalLayout_12.addWidget(self.pushButton_add_up_spine_opt)


        self.verticalLayout_10.addLayout(self.horizontalLayout_12)


        self.verticalLayout_13.addWidget(self.groupBox_julia)

        self.groupBox_python = QGroupBox(self.ExternalTools)
        self.groupBox_python.setObjectName(u"groupBox_python")
        sizePolicy.setHeightForWidth(self.groupBox_python.sizePolicy().hasHeightForWidth())
        self.groupBox_python.setSizePolicy(sizePolicy)
        self.groupBox_python.setMinimumSize(QSize(0, 95))
        self.verticalLayout_16 = QVBoxLayout(self.groupBox_python)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(-1, 9, -1, -1)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.radioButton_use_python_basic_console = QRadioButton(self.groupBox_python)
        self.radioButton_use_python_basic_console.setObjectName(u"radioButton_use_python_basic_console")

        self.verticalLayout_14.addWidget(self.radioButton_use_python_basic_console)

        self.radioButton_use_python_jupyter_console = QRadioButton(self.groupBox_python)
        self.radioButton_use_python_jupyter_console.setObjectName(u"radioButton_use_python_jupyter_console")

        self.verticalLayout_14.addWidget(self.radioButton_use_python_jupyter_console)


        self.horizontalLayout_5.addLayout(self.verticalLayout_14)

        self.line_2 = QFrame(self.groupBox_python)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_5.addWidget(self.line_2)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.lineEdit_python_path = QLineEdit(self.groupBox_python)
        self.lineEdit_python_path.setObjectName(u"lineEdit_python_path")
        self.lineEdit_python_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_python_path.setClearButtonEnabled(True)

        self.horizontalLayout_10.addWidget(self.lineEdit_python_path)

        self.toolButton_browse_python = QToolButton(self.groupBox_python)
        self.toolButton_browse_python.setObjectName(u"toolButton_browse_python")
        self.toolButton_browse_python.setIcon(icon5)

        self.horizontalLayout_10.addWidget(self.toolButton_browse_python)


        self.verticalLayout_5.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.comboBox_python_kernel = CustomQComboBox(self.groupBox_python)
        self.comboBox_python_kernel.setObjectName(u"comboBox_python_kernel")
        sizePolicy6.setHeightForWidth(self.comboBox_python_kernel.sizePolicy().hasHeightForWidth())
        self.comboBox_python_kernel.setSizePolicy(sizePolicy6)
        self.comboBox_python_kernel.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout_11.addWidget(self.comboBox_python_kernel)

        self.pushButton_make_python_kernel = QPushButton(self.groupBox_python)
        self.pushButton_make_python_kernel.setObjectName(u"pushButton_make_python_kernel")
        sizePolicy5.setHeightForWidth(self.pushButton_make_python_kernel.sizePolicy().hasHeightForWidth())
        self.pushButton_make_python_kernel.setSizePolicy(sizePolicy5)
        self.pushButton_make_python_kernel.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_11.addWidget(self.pushButton_make_python_kernel)


        self.verticalLayout_5.addLayout(self.horizontalLayout_11)


        self.horizontalLayout_5.addLayout(self.verticalLayout_5)


        self.verticalLayout_16.addLayout(self.horizontalLayout_5)


        self.verticalLayout_13.addWidget(self.groupBox_python)

        self.groupBox_2 = QGroupBox(self.ExternalTools)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lineEdit_conda_path = QLineEdit(self.groupBox_2)
        self.lineEdit_conda_path.setObjectName(u"lineEdit_conda_path")
        self.lineEdit_conda_path.setClearButtonEnabled(True)

        self.horizontalLayout_2.addWidget(self.lineEdit_conda_path)

        self.toolButton_browse_conda = QToolButton(self.groupBox_2)
        self.toolButton_browse_conda.setObjectName(u"toolButton_browse_conda")
        self.toolButton_browse_conda.setIcon(icon5)

        self.horizontalLayout_2.addWidget(self.toolButton_browse_conda)


        self.verticalLayout_8.addLayout(self.horizontalLayout_2)


        self.verticalLayout_13.addWidget(self.groupBox_2)

        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_13.addItem(self.verticalSpacer_2)

        self.stackedWidget.addWidget(self.ExternalTools)
        self.SpineDBEditor = QWidget()
        self.SpineDBEditor.setObjectName(u"SpineDBEditor")
        self.verticalLayout_9 = QVBoxLayout(self.SpineDBEditor)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.groupBox_db_editor_general = QGroupBox(self.SpineDBEditor)
        self.groupBox_db_editor_general.setObjectName(u"groupBox_db_editor_general")
        sizePolicy7 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.groupBox_db_editor_general.sizePolicy().hasHeightForWidth())
        self.groupBox_db_editor_general.setSizePolicy(sizePolicy7)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_db_editor_general)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.checkBox_commit_at_exit = QCheckBox(self.groupBox_db_editor_general)
        self.checkBox_commit_at_exit.setObjectName(u"checkBox_commit_at_exit")
        self.checkBox_commit_at_exit.setTristate(True)

        self.verticalLayout_4.addWidget(self.checkBox_commit_at_exit)

        self.checkBox_db_editor_show_undo = QCheckBox(self.groupBox_db_editor_general)
        self.checkBox_db_editor_show_undo.setObjectName(u"checkBox_db_editor_show_undo")

        self.verticalLayout_4.addWidget(self.checkBox_db_editor_show_undo)


        self.verticalLayout_9.addWidget(self.groupBox_db_editor_general)

        self.groupBox_entity_tree = QGroupBox(self.SpineDBEditor)
        self.groupBox_entity_tree.setObjectName(u"groupBox_entity_tree")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_entity_tree)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.checkBox_entity_tree_sticky_selection = QCheckBox(self.groupBox_entity_tree)
        self.checkBox_entity_tree_sticky_selection.setObjectName(u"checkBox_entity_tree_sticky_selection")

        self.verticalLayout_3.addWidget(self.checkBox_entity_tree_sticky_selection)

        self.checkBox_hide_empty_classes = QCheckBox(self.groupBox_entity_tree)
        self.checkBox_hide_empty_classes.setObjectName(u"checkBox_hide_empty_classes")

        self.verticalLayout_3.addWidget(self.checkBox_hide_empty_classes)


        self.verticalLayout_9.addWidget(self.groupBox_entity_tree)

        self.groupBox_entity_graph = QGroupBox(self.SpineDBEditor)
        self.groupBox_entity_graph.setObjectName(u"groupBox_entity_graph")
        self.gridLayout_5 = QGridLayout(self.groupBox_entity_graph)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.checkBox_smooth_entity_graph_rotation = QCheckBox(self.groupBox_entity_graph)
        self.checkBox_smooth_entity_graph_rotation.setObjectName(u"checkBox_smooth_entity_graph_rotation")

        self.gridLayout_5.addWidget(self.checkBox_smooth_entity_graph_rotation, 4, 0, 1, 1)

        self.checkBox_smooth_entity_graph_zoom = QCheckBox(self.groupBox_entity_graph)
        self.checkBox_smooth_entity_graph_zoom.setObjectName(u"checkBox_smooth_entity_graph_zoom")

        self.gridLayout_5.addWidget(self.checkBox_smooth_entity_graph_zoom, 3, 0, 1, 1)

        self.spinBox_layout_algo_max_iterations = QSpinBox(self.groupBox_entity_graph)
        self.spinBox_layout_algo_max_iterations.setObjectName(u"spinBox_layout_algo_max_iterations")
        self.spinBox_layout_algo_max_iterations.setMinimum(1)
        self.spinBox_layout_algo_max_iterations.setMaximum(100)
        self.spinBox_layout_algo_max_iterations.setValue(12)

        self.gridLayout_5.addWidget(self.spinBox_layout_algo_max_iterations, 6, 1, 1, 1)

        self.label_10 = QLabel(self.groupBox_entity_graph)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_5.addWidget(self.label_10, 7, 0, 1, 1)

        self.spinBox_layout_algo_spread_factor = QSpinBox(self.groupBox_entity_graph)
        self.spinBox_layout_algo_spread_factor.setObjectName(u"spinBox_layout_algo_spread_factor")
        self.spinBox_layout_algo_spread_factor.setMinimum(1)
        self.spinBox_layout_algo_spread_factor.setMaximum(100)
        self.spinBox_layout_algo_spread_factor.setValue(100)

        self.gridLayout_5.addWidget(self.spinBox_layout_algo_spread_factor, 7, 1, 1, 1)

        self.label_6 = QLabel(self.groupBox_entity_graph)
        self.label_6.setObjectName(u"label_6")
        sizePolicy8 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy8.setHorizontalStretch(2)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy8)

        self.gridLayout_5.addWidget(self.label_6, 6, 0, 1, 1)

        self.checkBox_auto_expand_entities = QCheckBox(self.groupBox_entity_graph)
        self.checkBox_auto_expand_entities.setObjectName(u"checkBox_auto_expand_entities")

        self.gridLayout_5.addWidget(self.checkBox_auto_expand_entities, 0, 0, 1, 1)

        self.label_16 = QLabel(self.groupBox_entity_graph)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_5.addWidget(self.label_16, 8, 0, 1, 1)

        self.checkBox_snap_entities = QCheckBox(self.groupBox_entity_graph)
        self.checkBox_snap_entities.setObjectName(u"checkBox_snap_entities")

        self.gridLayout_5.addWidget(self.checkBox_snap_entities, 2, 0, 1, 1)

        self.checkBox_merge_dbs = QCheckBox(self.groupBox_entity_graph)
        self.checkBox_merge_dbs.setObjectName(u"checkBox_merge_dbs")

        self.gridLayout_5.addWidget(self.checkBox_merge_dbs, 1, 0, 1, 1)

        self.spinBox_layout_algo_neg_weight_exp = QSpinBox(self.groupBox_entity_graph)
        self.spinBox_layout_algo_neg_weight_exp.setObjectName(u"spinBox_layout_algo_neg_weight_exp")
        self.spinBox_layout_algo_neg_weight_exp.setMinimum(1)
        self.spinBox_layout_algo_neg_weight_exp.setMaximum(100)

        self.gridLayout_5.addWidget(self.spinBox_layout_algo_neg_weight_exp, 8, 1, 1, 1)

        self.label_3 = QLabel(self.groupBox_entity_graph)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_5.addWidget(self.label_3, 5, 0, 1, 1)

        self.spinBox_max_ent_dim_count = QSpinBox(self.groupBox_entity_graph)
        self.spinBox_max_ent_dim_count.setObjectName(u"spinBox_max_ent_dim_count")
        self.spinBox_max_ent_dim_count.setMinimum(2)
        self.spinBox_max_ent_dim_count.setValue(5)

        self.gridLayout_5.addWidget(self.spinBox_max_ent_dim_count, 5, 1, 1, 1)


        self.verticalLayout_9.addWidget(self.groupBox_entity_graph)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_9)

        self.stackedWidget.addWidget(self.SpineDBEditor)
        self.SpecificationEditors = QWidget()
        self.SpecificationEditors.setObjectName(u"SpecificationEditors")
        self.verticalLayout_11 = QVBoxLayout(self.SpecificationEditors)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.groupBox = QGroupBox(self.SpecificationEditors)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_12 = QVBoxLayout(self.groupBox)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.checkBox_save_spec_before_closing = QCheckBox(self.groupBox)
        self.checkBox_save_spec_before_closing.setObjectName(u"checkBox_save_spec_before_closing")
        self.checkBox_save_spec_before_closing.setTristate(True)

        self.verticalLayout_12.addWidget(self.checkBox_save_spec_before_closing)

        self.checkBox_spec_show_undo = QCheckBox(self.groupBox)
        self.checkBox_spec_show_undo.setObjectName(u"checkBox_spec_show_undo")

        self.verticalLayout_12.addWidget(self.checkBox_spec_show_undo)


        self.verticalLayout_11.addWidget(self.groupBox)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.SpecificationEditors)
        self.Engine = QWidget()
        self.Engine.setObjectName(u"Engine")
        self.verticalLayout_19 = QVBoxLayout(self.Engine)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.process_limits_group_box = QGroupBox(self.Engine)
        self.process_limits_group_box.setObjectName(u"process_limits_group_box")
        self.verticalLayout_2 = QVBoxLayout(self.process_limits_group_box)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.unlimited_engine_process_radio_button = QRadioButton(self.process_limits_group_box)
        self.engine_processes_button_group = QButtonGroup(SettingsForm)
        self.engine_processes_button_group.setObjectName(u"engine_processes_button_group")
        self.engine_processes_button_group.addButton(self.unlimited_engine_process_radio_button)
        self.unlimited_engine_process_radio_button.setObjectName(u"unlimited_engine_process_radio_button")

        self.verticalLayout_2.addWidget(self.unlimited_engine_process_radio_button)

        self.automatic_engine_process_limit_radio_button = QRadioButton(self.process_limits_group_box)
        self.engine_processes_button_group.addButton(self.automatic_engine_process_limit_radio_button)
        self.automatic_engine_process_limit_radio_button.setObjectName(u"automatic_engine_process_limit_radio_button")

        self.verticalLayout_2.addWidget(self.automatic_engine_process_limit_radio_button)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.user_defined_engine_process_limit_radio_button = QRadioButton(self.process_limits_group_box)
        self.engine_processes_button_group.addButton(self.user_defined_engine_process_limit_radio_button)
        self.user_defined_engine_process_limit_radio_button.setObjectName(u"user_defined_engine_process_limit_radio_button")

        self.horizontalLayout_16.addWidget(self.user_defined_engine_process_limit_radio_button)

        self.engine_process_limit_spin_box = QSpinBox(self.process_limits_group_box)
        self.engine_process_limit_spin_box.setObjectName(u"engine_process_limit_spin_box")
        self.engine_process_limit_spin_box.setEnabled(False)
        self.engine_process_limit_spin_box.setMinimum(1)

        self.horizontalLayout_16.addWidget(self.engine_process_limit_spin_box)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_7)


        self.verticalLayout_2.addLayout(self.horizontalLayout_16)


        self.verticalLayout_19.addWidget(self.process_limits_group_box)

        self.persistent_process_limits_group_box = QGroupBox(self.Engine)
        self.persistent_process_limits_group_box.setObjectName(u"persistent_process_limits_group_box")
        self.verticalLayout_17 = QVBoxLayout(self.persistent_process_limits_group_box)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.unlimited_persistent_process_radio_button = QRadioButton(self.persistent_process_limits_group_box)
        self.persistent_processes_button_group = QButtonGroup(SettingsForm)
        self.persistent_processes_button_group.setObjectName(u"persistent_processes_button_group")
        self.persistent_processes_button_group.addButton(self.unlimited_persistent_process_radio_button)
        self.unlimited_persistent_process_radio_button.setObjectName(u"unlimited_persistent_process_radio_button")

        self.verticalLayout_17.addWidget(self.unlimited_persistent_process_radio_button)

        self.automatic_persistent_process_limit_radio_button = QRadioButton(self.persistent_process_limits_group_box)
        self.persistent_processes_button_group.addButton(self.automatic_persistent_process_limit_radio_button)
        self.automatic_persistent_process_limit_radio_button.setObjectName(u"automatic_persistent_process_limit_radio_button")

        self.verticalLayout_17.addWidget(self.automatic_persistent_process_limit_radio_button)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.user_defined_persistent_process_limit_radio_button = QRadioButton(self.persistent_process_limits_group_box)
        self.persistent_processes_button_group.addButton(self.user_defined_persistent_process_limit_radio_button)
        self.user_defined_persistent_process_limit_radio_button.setObjectName(u"user_defined_persistent_process_limit_radio_button")

        self.horizontalLayout_15.addWidget(self.user_defined_persistent_process_limit_radio_button)

        self.persistent_process_limit_spin_box = QSpinBox(self.persistent_process_limits_group_box)
        self.persistent_process_limit_spin_box.setObjectName(u"persistent_process_limit_spin_box")
        self.persistent_process_limit_spin_box.setEnabled(False)
        self.persistent_process_limit_spin_box.setMinimum(1)

        self.horizontalLayout_15.addWidget(self.persistent_process_limit_spin_box)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_6)


        self.verticalLayout_17.addLayout(self.horizontalLayout_15)


        self.verticalLayout_19.addWidget(self.persistent_process_limits_group_box)

        self.groupBox_4 = QGroupBox(self.Engine)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.checkBox_enable_remote_exec = QCheckBox(self.groupBox_4)
        self.checkBox_enable_remote_exec.setObjectName(u"checkBox_enable_remote_exec")

        self.verticalLayout_18.addWidget(self.checkBox_enable_remote_exec)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_12 = QLabel(self.groupBox_4)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_3.addWidget(self.label_12, 3, 0, 1, 1)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.lineEdit_secfolder = QLineEdit(self.groupBox_4)
        self.lineEdit_secfolder.setObjectName(u"lineEdit_secfolder")
        self.lineEdit_secfolder.setCursor(QCursor(Qt.ArrowCursor))
        self.lineEdit_secfolder.setReadOnly(False)
        self.lineEdit_secfolder.setClearButtonEnabled(True)

        self.horizontalLayout_18.addWidget(self.lineEdit_secfolder)

        self.toolButton_pick_secfolder = QToolButton(self.groupBox_4)
        self.toolButton_pick_secfolder.setObjectName(u"toolButton_pick_secfolder")
        self.toolButton_pick_secfolder.setMinimumSize(QSize(22, 22))
        self.toolButton_pick_secfolder.setMaximumSize(QSize(22, 22))
        self.toolButton_pick_secfolder.setIcon(icon5)

        self.horizontalLayout_18.addWidget(self.toolButton_pick_secfolder)


        self.gridLayout_3.addLayout(self.horizontalLayout_18, 4, 2, 1, 1)

        self.label_13 = QLabel(self.groupBox_4)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_3.addWidget(self.label_13, 4, 0, 1, 1)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lineEdit_host = QLineEdit(self.groupBox_4)
        self.lineEdit_host.setObjectName(u"lineEdit_host")
        self.lineEdit_host.setClearButtonEnabled(True)

        self.horizontalLayout_19.addWidget(self.lineEdit_host)

        self.label_14 = QLabel(self.groupBox_4)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_19.addWidget(self.label_14)

        self.spinBox_port = QSpinBox(self.groupBox_4)
        self.spinBox_port.setObjectName(u"spinBox_port")
        self.spinBox_port.setFrame(True)
        self.spinBox_port.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spinBox_port.setAccelerated(True)
        self.spinBox_port.setProperty("showGroupSeparator", False)
        self.spinBox_port.setMinimum(49152)
        self.spinBox_port.setMaximum(65535)

        self.horizontalLayout_19.addWidget(self.spinBox_port)


        self.gridLayout_3.addLayout(self.horizontalLayout_19, 0, 2, 1, 1)

        self.label_15 = QLabel(self.groupBox_4)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_3.addWidget(self.label_15, 0, 0, 1, 1)

        self.comboBox_security = QComboBox(self.groupBox_4)
        self.comboBox_security.addItem("")
        self.comboBox_security.addItem("")
        self.comboBox_security.setObjectName(u"comboBox_security")

        self.gridLayout_3.addWidget(self.comboBox_security, 3, 2, 1, 1)


        self.verticalLayout_18.addLayout(self.gridLayout_3)


        self.verticalLayout_19.addWidget(self.groupBox_4)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_19.addItem(self.verticalSpacer_4)

        self.stackedWidget.addWidget(self.Engine)
        self.splitter.addWidget(self.stackedWidget)

        self.verticalLayout_7.addWidget(self.splitter)

        self.buttonBox = QDialogButtonBox(SettingsForm)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout_7.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.checkBox_custom_open_project_dialog, self.checkBox_delete_data)
        QWidget.setTabOrder(self.checkBox_delete_data, self.checkBox_open_previous_project)
        QWidget.setTabOrder(self.checkBox_open_previous_project, self.checkBox_exit_prompt)
        QWidget.setTabOrder(self.checkBox_exit_prompt, self.project_save_options_combo_box)
        QWidget.setTabOrder(self.project_save_options_combo_box, self.lineEdit_work_dir)
        QWidget.setTabOrder(self.lineEdit_work_dir, self.toolButton_browse_work)
        QWidget.setTabOrder(self.toolButton_browse_work, self.checkBox_color_toolbar_icons)
        QWidget.setTabOrder(self.checkBox_color_toolbar_icons, self.checkBox_color_properties_widgets)
        QWidget.setTabOrder(self.checkBox_color_properties_widgets, self.checkBox_use_curved_links)
        QWidget.setTabOrder(self.checkBox_use_curved_links, self.checkBox_drag_to_draw_links)
        QWidget.setTabOrder(self.checkBox_drag_to_draw_links, self.checkBox_prevent_overlapping)
        QWidget.setTabOrder(self.checkBox_prevent_overlapping, self.checkBox_use_rounded_items)
        QWidget.setTabOrder(self.checkBox_use_rounded_items, self.checkBox_datetime)
        QWidget.setTabOrder(self.checkBox_datetime, self.checkBox_use_smooth_zoom)
        QWidget.setTabOrder(self.checkBox_use_smooth_zoom, self.radioButton_bg_grid)
        QWidget.setTabOrder(self.radioButton_bg_grid, self.radioButton_bg_tree)
        QWidget.setTabOrder(self.radioButton_bg_tree, self.radioButton_bg_solid)
        QWidget.setTabOrder(self.radioButton_bg_solid, self.toolButton_bg_color)
        QWidget.setTabOrder(self.toolButton_bg_color, self.horizontalSlider_data_flow_animation_duration)
        QWidget.setTabOrder(self.horizontalSlider_data_flow_animation_duration, self.lineEdit_gams_path)
        QWidget.setTabOrder(self.lineEdit_gams_path, self.toolButton_browse_gams)
        QWidget.setTabOrder(self.toolButton_browse_gams, self.radioButton_use_julia_basic_console)
        QWidget.setTabOrder(self.radioButton_use_julia_basic_console, self.radioButton_use_julia_jupyter_console)
        QWidget.setTabOrder(self.radioButton_use_julia_jupyter_console, self.lineEdit_julia_path)
        QWidget.setTabOrder(self.lineEdit_julia_path, self.toolButton_browse_julia)
        QWidget.setTabOrder(self.toolButton_browse_julia, self.lineEdit_julia_project_path)
        QWidget.setTabOrder(self.lineEdit_julia_project_path, self.toolButton_browse_julia_project)
        QWidget.setTabOrder(self.toolButton_browse_julia_project, self.comboBox_julia_kernel)
        QWidget.setTabOrder(self.comboBox_julia_kernel, self.pushButton_make_julia_kernel)
        QWidget.setTabOrder(self.pushButton_make_julia_kernel, self.pushButton_install_julia)
        QWidget.setTabOrder(self.pushButton_install_julia, self.pushButton_add_up_spine_opt)
        QWidget.setTabOrder(self.pushButton_add_up_spine_opt, self.radioButton_use_python_basic_console)
        QWidget.setTabOrder(self.radioButton_use_python_basic_console, self.radioButton_use_python_jupyter_console)
        QWidget.setTabOrder(self.radioButton_use_python_jupyter_console, self.lineEdit_python_path)
        QWidget.setTabOrder(self.lineEdit_python_path, self.toolButton_browse_python)
        QWidget.setTabOrder(self.toolButton_browse_python, self.comboBox_python_kernel)
        QWidget.setTabOrder(self.comboBox_python_kernel, self.pushButton_make_python_kernel)
        QWidget.setTabOrder(self.pushButton_make_python_kernel, self.lineEdit_conda_path)
        QWidget.setTabOrder(self.lineEdit_conda_path, self.toolButton_browse_conda)
        QWidget.setTabOrder(self.toolButton_browse_conda, self.checkBox_commit_at_exit)
        QWidget.setTabOrder(self.checkBox_commit_at_exit, self.checkBox_db_editor_show_undo)
        QWidget.setTabOrder(self.checkBox_db_editor_show_undo, self.checkBox_save_spec_before_closing)
        QWidget.setTabOrder(self.checkBox_save_spec_before_closing, self.checkBox_spec_show_undo)
        QWidget.setTabOrder(self.checkBox_spec_show_undo, self.unlimited_engine_process_radio_button)
        QWidget.setTabOrder(self.unlimited_engine_process_radio_button, self.automatic_engine_process_limit_radio_button)
        QWidget.setTabOrder(self.automatic_engine_process_limit_radio_button, self.user_defined_engine_process_limit_radio_button)
        QWidget.setTabOrder(self.user_defined_engine_process_limit_radio_button, self.engine_process_limit_spin_box)
        QWidget.setTabOrder(self.engine_process_limit_spin_box, self.unlimited_persistent_process_radio_button)
        QWidget.setTabOrder(self.unlimited_persistent_process_radio_button, self.automatic_persistent_process_limit_radio_button)
        QWidget.setTabOrder(self.automatic_persistent_process_limit_radio_button, self.user_defined_persistent_process_limit_radio_button)
        QWidget.setTabOrder(self.user_defined_persistent_process_limit_radio_button, self.persistent_process_limit_spin_box)
        QWidget.setTabOrder(self.persistent_process_limit_spin_box, self.checkBox_enable_remote_exec)
        QWidget.setTabOrder(self.checkBox_enable_remote_exec, self.lineEdit_host)
        QWidget.setTabOrder(self.lineEdit_host, self.spinBox_port)
        QWidget.setTabOrder(self.spinBox_port, self.comboBox_security)
        QWidget.setTabOrder(self.comboBox_security, self.lineEdit_secfolder)
        QWidget.setTabOrder(self.lineEdit_secfolder, self.toolButton_pick_secfolder)
        QWidget.setTabOrder(self.toolButton_pick_secfolder, self.listWidget)
        QWidget.setTabOrder(self.listWidget, self.checkBox_entity_tree_sticky_selection)
        QWidget.setTabOrder(self.checkBox_entity_tree_sticky_selection, self.checkBox_hide_empty_classes)
        QWidget.setTabOrder(self.checkBox_hide_empty_classes, self.checkBox_smooth_entity_graph_rotation)
        QWidget.setTabOrder(self.checkBox_smooth_entity_graph_rotation, self.checkBox_smooth_entity_graph_zoom)
        QWidget.setTabOrder(self.checkBox_smooth_entity_graph_zoom, self.spinBox_layout_algo_max_iterations)
        QWidget.setTabOrder(self.spinBox_layout_algo_max_iterations, self.spinBox_layout_algo_spread_factor)
        QWidget.setTabOrder(self.spinBox_layout_algo_spread_factor, self.checkBox_auto_expand_entities)
        QWidget.setTabOrder(self.checkBox_auto_expand_entities, self.checkBox_snap_entities)
        QWidget.setTabOrder(self.checkBox_snap_entities, self.checkBox_merge_dbs)
        QWidget.setTabOrder(self.checkBox_merge_dbs, self.spinBox_layout_algo_neg_weight_exp)
        QWidget.setTabOrder(self.spinBox_layout_algo_neg_weight_exp, self.spinBox_max_ent_dim_count)

        self.retranslateUi(SettingsForm)
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)

        self.listWidget.setCurrentRow(-1)
        self.stackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(SettingsForm)
    # setupUi

    def retranslateUi(self, SettingsForm):
        SettingsForm.setWindowTitle(QCoreApplication.translate("SettingsForm", u"Settings", None))

        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("SettingsForm", u"General", None));
        ___qlistwidgetitem1 = self.listWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("SettingsForm", u"Tools", None));
        ___qlistwidgetitem2 = self.listWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("SettingsForm", u"Db editor", None));
        ___qlistwidgetitem3 = self.listWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("SettingsForm", u"Spec. editors", None));
        ___qlistwidgetitem4 = self.listWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("SettingsForm", u"Engine", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.groupBox_general.setTitle(QCoreApplication.translate("SettingsForm", u"Main", None))
        self.label.setText(QCoreApplication.translate("SettingsForm", u"Work directory", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Work directory location. Leave empty to use default.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using default directory", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_work.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Work directory with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("SettingsForm", u"When there are unsaved changes at exit:", None))
        self.project_save_options_combo_box.setItemText(0, QCoreApplication.translate("SettingsForm", u"Ask what to do", None))
        self.project_save_options_combo_box.setItemText(1, QCoreApplication.translate("SettingsForm", u"Automatically save project", None))

#if QT_CONFIG(tooltip)
        self.checkBox_custom_open_project_dialog.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select the type of dialog used in File-&gt;Open project...</p><p>Checking this box shows a custom dialog. Unchecking this box shows the OS provided 'select folder' dialog.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_custom_open_project_dialog.setText(QCoreApplication.translate("SettingsForm", u"Custom open project dialog", None))
#if QT_CONFIG(tooltip)
        self.checkBox_delete_data.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Check this box to delete project item's data when a project item is removed from project. This means, that the project item directory and its contens will be deleted from your HD.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_delete_data.setText(QCoreApplication.translate("SettingsForm", u"Delete data when project item is removed from project", None))
#if QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Checking this shows the 'confirm exit' question box when quitting the app</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setText(QCoreApplication.translate("SettingsForm", u"Always confirm exit", None))
#if QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, application opens the project at startup that was open the last time the application was quit</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setText(QCoreApplication.translate("SettingsForm", u"Open previous project at startup", None))
        self.groupBox_ui.setTitle(QCoreApplication.translate("SettingsForm", u"UI", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or discete zoom is used in Design and Graph Views.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setText(QCoreApplication.translate("SettingsForm", u"Smooth zoom", None))
#if QT_CONFIG(tooltip)
        self.checkBox_datetime.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, date and time string is appended into Event Log messages</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_datetime.setText(QCoreApplication.translate("SettingsForm", u"Show date and time in Event Log messages", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or straight connectors are used in Design View.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setText(QCoreApplication.translate("SettingsForm", u"Curved links", None))
        self.checkBox_color_properties_widgets.setText(QCoreApplication.translate("SettingsForm", u"Color properties widgets", None))
        self.checkBox_color_toolbar_icons.setText(QCoreApplication.translate("SettingsForm", u"Color toolbar icons", None))
        self.checkBox_prevent_overlapping.setText(QCoreApplication.translate("SettingsForm", u"Prevent items from overlapping", None))
        self.checkBox_use_rounded_items.setText(QCoreApplication.translate("SettingsForm", u"Rounded items", None))
        self.label_7.setText(QCoreApplication.translate("SettingsForm", u"Background", None))
        self.radioButton_bg_grid.setText(QCoreApplication.translate("SettingsForm", u"Grid", None))
        self.radioButton_bg_tree.setText(QCoreApplication.translate("SettingsForm", u"Tree of Life", None))
        self.radioButton_bg_solid.setText(QCoreApplication.translate("SettingsForm", u"Solid", None))
        self.label_9.setText(QCoreApplication.translate("SettingsForm", u"Color", None))
#if QT_CONFIG(tooltip)
        self.toolButton_bg_color.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick solid background color</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("SettingsForm", u"Link flash speed", None))
        self.label_5.setText(QCoreApplication.translate("SettingsForm", u"Slow", None))
        self.label_8.setText(QCoreApplication.translate("SettingsForm", u"Fast", None))
        self.checkBox_drag_to_draw_links.setText(QCoreApplication.translate("SettingsForm", u"Drag to draw links", None))
        self.groupBox_gams.setTitle(QCoreApplication.translate("SettingsForm", u"GAMS", None))
        self.label_11.setText(QCoreApplication.translate("SettingsForm", u"GAMS executable", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_gams_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Path to GAMS executable for Tool and GAMS Python bindings. Leave blank to use system's default</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_gams_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using system's default GAMS", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_gams.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick GAMS executable using a file browser (eg. gams.exe on Windows)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.groupBox_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Default settings</span> for new Julia Tool specs. Defaults can be changed for each Tool specification separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_julia.setTitle(QCoreApplication.translate("SettingsForm", u"Julia", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_julia_basic_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Execute Julia Tool specifications in basic Julia REPL.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Julia Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_julia_basic_console.setText(QCoreApplication.translate("SettingsForm", u"Basic Console", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_julia_jupyter_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Use Jupyter Console to execute Julia Tool specs. Select a Julia kernel spec to use this option.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Julia Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_julia_jupyter_console.setText(QCoreApplication.translate("SettingsForm", u"Jupyter Console", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia executable for Basic Console. Leave blank to use the Julia in your system PATH env. If Julia is not in your PATH, this line edit will be empty, indicating that Julia Tool Specs won't execute.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Julia Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia executable in system path", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia executable using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia environment/project directory for Julia Tool specifications. Leave blank to use the default environment.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Julia Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setText("")
        self.lineEdit_julia_project_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia default project", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia project using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setText(QCoreApplication.translate("SettingsForm", u"...", None))
#if QT_CONFIG(tooltip)
        self.comboBox_julia_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select a Julia kernel spec for Jupyter Console.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Julia Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_make_julia_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Creates a Julia kernel for selected Julia executable and Julia project if it does not exist using the <span style=\" font-weight:700;\">IJulia</span> package. Selects a Julia kernel matching the selected Julia executable and Julia project if it already exists. May overwrite a Julia kernel if one for selected Julia executable already exists but the Julia project is different.</p><p>You can also create Julia kernels manually using the <span style=\" font-weight:700;\">IJulia</span> package.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_make_julia_kernel.setText(QCoreApplication.translate("SettingsForm", u"Make Julia Kernel", None))
#if QT_CONFIG(tooltip)
        self.pushButton_install_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Installs the latest Julia on your system using Python's <span style=\" font-weight:700;\">jill</span> package</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_install_julia.setText(QCoreApplication.translate("SettingsForm", u"Install Julia", None))
#if QT_CONFIG(tooltip)
        self.pushButton_add_up_spine_opt.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Adds or updates <span style=\" font-weight:700;\">SpineOpt.jl</span> package using the Julia executable &amp; project selected above</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_add_up_spine_opt.setText(QCoreApplication.translate("SettingsForm", u"Add/Update SpineOpt", None))
#if QT_CONFIG(tooltip)
        self.groupBox_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Default settings</span> for new Python Tool specs. Defaults can be changed for each Tool specification separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_python.setTitle(QCoreApplication.translate("SettingsForm", u"Python", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_python_basic_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Execute Python Tool specifications in basic Python REPL.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_python_basic_console.setText(QCoreApplication.translate("SettingsForm", u"Basic Console", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_python_jupyter_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Use Jupyter Console to execute Python Tool specs. Select a Python kernel spec to use this option.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_python_jupyter_console.setText(QCoreApplication.translate("SettingsForm", u"Jupyter Console", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Python interpreter for Basic Console. Leave blank to use the Python that was used in launching Spine Toolbox.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using current Python interpreter", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Python interpreter using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.comboBox_python_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select a Python kernel spec for Jupyter Console.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_make_python_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Creates a Python kernel for selected Python interpreter if it does not exist using the <span style=\" font-weight:700;\">ipykernel </span>package. Selects a Python kernel matching the selected Python interpreter if it already exists. </p><p>You can also create Python kernels manually using the <span style=\" font-weight:700;\">ipykernel</span> package.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_make_python_kernel.setText(QCoreApplication.translate("SettingsForm", u"Make Python Kernel", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SettingsForm", u"Conda", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_conda_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select Miniconda executable for running Tool specifications in a Conda environment.</p><p>If you started Spine Toolbox in Miniconda, the <span style=\" font-weight:600;\">Conda executable is set up automatically</span>.</p><p>If not on Miniconda, please select <span style=\" font-weight:600;\">&lt;base_env&gt;\\scripts\\conda.exe</span> (on Win10), where <span style=\" font-weight:600;\">&lt;base_env&gt;</span> is the root directory of your Miniconda installation (i.e. base environment location).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_conda_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Select Miniconda executable...", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_conda.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Conda executable using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_browse_conda.setText("")
        self.groupBox_db_editor_general.setTitle(QCoreApplication.translate("SettingsForm", u"General", None))
#if QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Don't commit session and don't show message box</p><p>Partially checked: Show message box (default)</p><p>Checked: Commit session and don't show message box</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setText(QCoreApplication.translate("SettingsForm", u"Commit session before closing", None))
        self.checkBox_db_editor_show_undo.setText(QCoreApplication.translate("SettingsForm", u"Show undo notifications", None))
        self.groupBox_entity_tree.setTitle(QCoreApplication.translate("SettingsForm", u"Entity tree", None))
#if QT_CONFIG(tooltip)
        self.checkBox_entity_tree_sticky_selection.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls how selecting items in Object tree <span style=\" font-weight:600;\">using the left mouse button</span> works. </p><p>When unchecked [default], Single selection is enabled. Pressing the Ctrl-button down enables multiple selection.</p><p>When checked, Multiple selection is enabled. Pressing the Ctrl-button down enables single selection.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_entity_tree_sticky_selection.setText(QCoreApplication.translate("SettingsForm", u"Sticky selection", None))
        self.checkBox_hide_empty_classes.setText(QCoreApplication.translate("SettingsForm", u"Hide empty classes", None))
        self.groupBox_entity_graph.setTitle(QCoreApplication.translate("SettingsForm", u"Entity graph", None))
        self.checkBox_smooth_entity_graph_rotation.setText(QCoreApplication.translate("SettingsForm", u"Smooth rotation", None))
        self.checkBox_smooth_entity_graph_zoom.setText(QCoreApplication.translate("SettingsForm", u"Smooth zoom", None))
        self.spinBox_layout_algo_max_iterations.setSuffix("")
        self.label_10.setText(QCoreApplication.translate("SettingsForm", u"Minimum distance between nodes (%)", None))
        self.label_6.setText(QCoreApplication.translate("SettingsForm", u"Number of build iterations", None))
#if QT_CONFIG(tooltip)
        self.checkBox_auto_expand_entities.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Checked</span>: Whenever an object is included in the Entity graph, the graph automatically includes <span style=\" font-style:italic;\">all</span> its relationships.</p><p><span style=\" font-weight:600;\">Unchecked</span>: Whenever <span style=\" font-style:italic;\">all</span> the objects in a relationship are included in the Entity graph, the graph automatically includes the relationship.</p><p>Note: This setting is a global default, but can be locally overriden in every Spine DB editor session.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_auto_expand_entities.setText(QCoreApplication.translate("SettingsForm", u"Auto-expand entities", None))
        self.label_16.setText(QCoreApplication.translate("SettingsForm", u"Decay rate of attraction with distance", None))
        self.checkBox_snap_entities.setText(QCoreApplication.translate("SettingsForm", u"Snap entities to grid", None))
        self.checkBox_merge_dbs.setText(QCoreApplication.translate("SettingsForm", u"Merge databases", None))
        self.label_3.setText(QCoreApplication.translate("SettingsForm", u"Max. entity dimension count", None))
        self.groupBox.setTitle(QCoreApplication.translate("SettingsForm", u"Specification editors", None))
#if QT_CONFIG(tooltip)
        self.checkBox_save_spec_before_closing.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Don't save specification and don't show message box</p><p>Partially checked: Show message box (default)</p><p>Checked: Save specification and don't show message box</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_save_spec_before_closing.setText(QCoreApplication.translate("SettingsForm", u"Save specification before closing", None))
        self.checkBox_spec_show_undo.setText(QCoreApplication.translate("SettingsForm", u"Show undo notifications", None))
        self.process_limits_group_box.setTitle(QCoreApplication.translate("SettingsForm", u"Maximum number of concurrent processes", None))
        self.unlimited_engine_process_radio_button.setText(QCoreApplication.translate("SettingsForm", u"Unlimited", None))
        self.automatic_engine_process_limit_radio_button.setText(QCoreApplication.translate("SettingsForm", u"Limit to available CPU cores", None))
        self.user_defined_engine_process_limit_radio_button.setText(QCoreApplication.translate("SettingsForm", u"User defined limit:", None))
        self.persistent_process_limits_group_box.setTitle(QCoreApplication.translate("SettingsForm", u"Maximum number of open consoles", None))
        self.unlimited_persistent_process_radio_button.setText(QCoreApplication.translate("SettingsForm", u"Unlimited", None))
#if QT_CONFIG(tooltip)
        self.automatic_persistent_process_limit_radio_button.setToolTip(QCoreApplication.translate("SettingsForm", u"Kills console processes randomly if limit is exceeded.", None))
#endif // QT_CONFIG(tooltip)
        self.automatic_persistent_process_limit_radio_button.setText(QCoreApplication.translate("SettingsForm", u"Limit to available CPU cores", None))
#if QT_CONFIG(tooltip)
        self.user_defined_persistent_process_limit_radio_button.setToolTip(QCoreApplication.translate("SettingsForm", u"Kills console processes randomly if limit is exceeded.", None))
#endif // QT_CONFIG(tooltip)
        self.user_defined_persistent_process_limit_radio_button.setText(QCoreApplication.translate("SettingsForm", u"User defined limit:", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("SettingsForm", u"Remote execution", None))
        self.checkBox_enable_remote_exec.setText(QCoreApplication.translate("SettingsForm", u"Enabled", None))
        self.label_12.setText(QCoreApplication.translate("SettingsForm", u"Security", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_secfolder.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Required for Stonehouse security. Given path should contain '/certificates', '/public_keys', and '/private_keys' directories. </p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_secfolder.setText("")
        self.lineEdit_secfolder.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Select certificate directory...", None))
        self.label_13.setText(QCoreApplication.translate("SettingsForm", u"Certs", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_host.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Host name</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_host.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Enter host name...", None))
        self.label_14.setText(QCoreApplication.translate("SettingsForm", u"Port", None))
#if QT_CONFIG(tooltip)
        self.spinBox_port.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Limited to dynamic/private ports (49152-&gt;65535)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_15.setText(QCoreApplication.translate("SettingsForm", u"Host", None))
        self.comboBox_security.setItemText(0, QCoreApplication.translate("SettingsForm", u"None", None))
        self.comboBox_security.setItemText(1, QCoreApplication.translate("SettingsForm", u"Stonehouse", None))

#if QT_CONFIG(tooltip)
        self.comboBox_security.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>ZMQ security model</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

