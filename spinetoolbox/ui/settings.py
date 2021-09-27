# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from spinetoolbox.widgets.custom_qcombobox import CustomQComboBox

from spinetoolbox import resources_icons_rc

class Ui_SettingsForm(object):
    def setupUi(self, SettingsForm):
        if not SettingsForm.objectName():
            SettingsForm.setObjectName(u"SettingsForm")
        SettingsForm.setWindowModality(Qt.ApplicationModal)
        SettingsForm.resize(677, 547)
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
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(9, 9, 9, 9)
        self.splitter = QSplitter(SettingsForm)
        self.splitter.setObjectName(u"splitter")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy1)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.listWidget = QListWidget(self.splitter)
        icon = QIcon()
        icon.addFile(u":/icons/sliders-h.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem = QListWidgetItem(self.listWidget)
        __qlistwidgetitem.setTextAlignment(Qt.AlignLeading|Qt.AlignVCenter);
        __qlistwidgetitem.setIcon(icon);
        __qlistwidgetitem.setFlags(Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        icon1 = QIcon()
        icon1.addFile(u":/icons/project-diagram.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem1.setIcon(icon1);
        icon2 = QIcon()
        icon2.addFile(u":/icons/project_item_icons/hammer.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem2.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u":/icons/database.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem3.setIcon(icon3);
        icon4 = QIcon()
        icon4.addFile(u":/icons/wrench.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem4 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem4.setIcon(icon4);
        self.listWidget.setObjectName(u"listWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy2)
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
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(2)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy3)
        self.General = QWidget()
        self.General.setObjectName(u"General")
        self.verticalLayout_6 = QVBoxLayout(self.General)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.groupBox_general = QGroupBox(self.General)
        self.groupBox_general.setObjectName(u"groupBox_general")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_general.sizePolicy().hasHeightForWidth())
        self.groupBox_general.setSizePolicy(sizePolicy4)
        self.groupBox_general.setMinimumSize(QSize(0, 0))
        self.groupBox_general.setMaximumSize(QSize(16777215, 16777215))
        self.groupBox_general.setAutoFillBackground(False)
        self.groupBox_general.setFlat(False)
        self.gridLayout = QGridLayout(self.groupBox_general)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(self.groupBox_general)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setPointSize(10)
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 20, 0, 1, 1)

        self.checkBox_delete_data = QCheckBox(self.groupBox_general)
        self.checkBox_delete_data.setObjectName(u"checkBox_delete_data")

        self.gridLayout.addWidget(self.checkBox_delete_data, 4, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.radioButton_bg_grid = QRadioButton(self.groupBox_general)
        self.radioButton_bg_grid.setObjectName(u"radioButton_bg_grid")

        self.horizontalLayout_4.addWidget(self.radioButton_bg_grid)

        self.radioButton_bg_tree = QRadioButton(self.groupBox_general)
        self.radioButton_bg_tree.setObjectName(u"radioButton_bg_tree")

        self.horizontalLayout_4.addWidget(self.radioButton_bg_tree)

        self.radioButton_bg_solid = QRadioButton(self.groupBox_general)
        self.radioButton_bg_solid.setObjectName(u"radioButton_bg_solid")
        self.radioButton_bg_solid.setChecked(True)

        self.horizontalLayout_4.addWidget(self.radioButton_bg_solid)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.label_9 = QLabel(self.groupBox_general)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_4.addWidget(self.label_9)

        self.toolButton_bg_color = QToolButton(self.groupBox_general)
        self.toolButton_bg_color.setObjectName(u"toolButton_bg_color")
        self.toolButton_bg_color.setIconSize(QSize(16, 16))

        self.horizontalLayout_4.addWidget(self.toolButton_bg_color)


        self.gridLayout.addLayout(self.horizontalLayout_4, 19, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lineEdit_work_dir = QLineEdit(self.groupBox_general)
        self.lineEdit_work_dir.setObjectName(u"lineEdit_work_dir")
        self.lineEdit_work_dir.setMinimumSize(QSize(0, 20))
        self.lineEdit_work_dir.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.lineEdit_work_dir)

        self.toolButton_browse_work = QToolButton(self.groupBox_general)
        self.toolButton_browse_work.setObjectName(u"toolButton_browse_work")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.toolButton_browse_work.sizePolicy().hasHeightForWidth())
        self.toolButton_browse_work.setSizePolicy(sizePolicy5)
        icon5 = QIcon()
        icon5.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_browse_work.setIcon(icon5)

        self.horizontalLayout_6.addWidget(self.toolButton_browse_work)


        self.gridLayout.addLayout(self.horizontalLayout_6, 14, 0, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_5 = QLabel(self.groupBox_general)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

        self.label_8 = QLabel(self.groupBox_general)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_5.addWidget(self.label_8)


        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.horizontalSlider_data_flow_animation_duration = QSlider(self.groupBox_general)
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

        self.verticalLayout_3.addWidget(self.horizontalSlider_data_flow_animation_duration)


        self.gridLayout.addLayout(self.verticalLayout_3, 21, 0, 1, 1)

        self.label = QLabel(self.groupBox_general)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout.addWidget(self.label, 13, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox_general)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font)

        self.gridLayout.addWidget(self.label_7, 18, 0, 1, 1)

        self.checkBox_custom_open_project_dialog = QCheckBox(self.groupBox_general)
        self.checkBox_custom_open_project_dialog.setObjectName(u"checkBox_custom_open_project_dialog")
        self.checkBox_custom_open_project_dialog.setChecked(False)

        self.gridLayout.addWidget(self.checkBox_custom_open_project_dialog, 5, 0, 1, 1)

        self.checkBox_exit_prompt = QCheckBox(self.groupBox_general)
        self.checkBox_exit_prompt.setObjectName(u"checkBox_exit_prompt")
        self.checkBox_exit_prompt.setTristate(False)

        self.gridLayout.addWidget(self.checkBox_exit_prompt, 2, 0, 1, 1)

        self.checkBox_use_smooth_zoom = QCheckBox(self.groupBox_general)
        self.checkBox_use_smooth_zoom.setObjectName(u"checkBox_use_smooth_zoom")

        self.gridLayout.addWidget(self.checkBox_use_smooth_zoom, 10, 0, 1, 1)

        self.checkBox_use_curved_links = QCheckBox(self.groupBox_general)
        self.checkBox_use_curved_links.setObjectName(u"checkBox_use_curved_links")

        self.gridLayout.addWidget(self.checkBox_use_curved_links, 11, 0, 1, 1)

        self.checkBox_datetime = QCheckBox(self.groupBox_general)
        self.checkBox_datetime.setObjectName(u"checkBox_datetime")

        self.gridLayout.addWidget(self.checkBox_datetime, 6, 0, 1, 1)

        self.checkBox_save_project_before_closing = QCheckBox(self.groupBox_general)
        self.checkBox_save_project_before_closing.setObjectName(u"checkBox_save_project_before_closing")
        self.checkBox_save_project_before_closing.setTristate(True)

        self.gridLayout.addWidget(self.checkBox_save_project_before_closing, 3, 0, 1, 1)

        self.checkBox_open_previous_project = QCheckBox(self.groupBox_general)
        self.checkBox_open_previous_project.setObjectName(u"checkBox_open_previous_project")
        sizePolicy6 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.checkBox_open_previous_project.sizePolicy().hasHeightForWidth())
        self.checkBox_open_previous_project.setSizePolicy(sizePolicy6)

        self.gridLayout.addWidget(self.checkBox_open_previous_project, 1, 0, 1, 1)

        self.checkBox_color_toolbar_icons = QCheckBox(self.groupBox_general)
        self.checkBox_color_toolbar_icons.setObjectName(u"checkBox_color_toolbar_icons")

        self.gridLayout.addWidget(self.checkBox_color_toolbar_icons, 9, 0, 1, 1)

        self.checkBox_prevent_overlapping = QCheckBox(self.groupBox_general)
        self.checkBox_prevent_overlapping.setObjectName(u"checkBox_prevent_overlapping")

        self.gridLayout.addWidget(self.checkBox_prevent_overlapping, 12, 0, 1, 1)


        self.verticalLayout_6.addWidget(self.groupBox_general)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.General)
        self.Project = QWidget()
        self.Project.setObjectName(u"Project")
        self.verticalLayout_10 = QVBoxLayout(self.Project)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.groupBox_project = QGroupBox(self.Project)
        self.groupBox_project.setObjectName(u"groupBox_project")
        sizePolicy4.setHeightForWidth(self.groupBox_project.sizePolicy().hasHeightForWidth())
        self.groupBox_project.setSizePolicy(sizePolicy4)
        self.groupBox_project.setMinimumSize(QSize(250, 150))
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_project)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_2 = QLabel(self.groupBox_project)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.verticalLayout_2.addWidget(self.label_2)

        self.lineEdit_project_name = QLineEdit(self.groupBox_project)
        self.lineEdit_project_name.setObjectName(u"lineEdit_project_name")
        self.lineEdit_project_name.setMinimumSize(QSize(0, 20))
        self.lineEdit_project_name.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_project_name.setCursor(QCursor(Qt.IBeamCursor))
        self.lineEdit_project_name.setFocusPolicy(Qt.StrongFocus)
        self.lineEdit_project_name.setReadOnly(False)
        self.lineEdit_project_name.setClearButtonEnabled(False)

        self.verticalLayout_2.addWidget(self.lineEdit_project_name)

        self.label_3 = QLabel(self.groupBox_project)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.verticalLayout_2.addWidget(self.label_3)

        self.textEdit_project_description = QTextEdit(self.groupBox_project)
        self.textEdit_project_description.setObjectName(u"textEdit_project_description")
        self.textEdit_project_description.viewport().setProperty("cursor", QCursor(Qt.IBeamCursor))
        self.textEdit_project_description.setFocusPolicy(Qt.StrongFocus)
        self.textEdit_project_description.setStyleSheet(u":focus {border: 1px solid black;}")
        self.textEdit_project_description.setTabChangesFocus(True)
        self.textEdit_project_description.setReadOnly(False)
        self.textEdit_project_description.setAcceptRichText(False)

        self.verticalLayout_2.addWidget(self.textEdit_project_description)


        self.verticalLayout_10.addWidget(self.groupBox_project)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_10)

        self.stackedWidget.addWidget(self.Project)
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
        self.label_11.setFont(font)

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
        self.verticalLayout_16 = QVBoxLayout(self.groupBox_julia)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
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
        sizePolicy7 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.comboBox_julia_kernel.sizePolicy().hasHeightForWidth())
        self.comboBox_julia_kernel.setSizePolicy(sizePolicy7)
        self.comboBox_julia_kernel.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)

        self.horizontalLayout_9.addWidget(self.comboBox_julia_kernel)

        self.pushButton_open_kernel_editor_julia = QPushButton(self.groupBox_julia)
        self.pushButton_open_kernel_editor_julia.setObjectName(u"pushButton_open_kernel_editor_julia")
        sizePolicy6.setHeightForWidth(self.pushButton_open_kernel_editor_julia.sizePolicy().hasHeightForWidth())
        self.pushButton_open_kernel_editor_julia.setSizePolicy(sizePolicy6)

        self.horizontalLayout_9.addWidget(self.pushButton_open_kernel_editor_julia)


        self.verticalLayout_15.addLayout(self.horizontalLayout_9)


        self.horizontalLayout_14.addLayout(self.verticalLayout_15)


        self.verticalLayout_16.addLayout(self.horizontalLayout_14)

        self.line = QFrame(self.groupBox_julia)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_16.addWidget(self.line)

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


        self.verticalLayout_16.addLayout(self.horizontalLayout_12)


        self.verticalLayout_13.addWidget(self.groupBox_julia)

        self.groupBox_python = QGroupBox(self.ExternalTools)
        self.groupBox_python.setObjectName(u"groupBox_python")
        sizePolicy.setHeightForWidth(self.groupBox_python.sizePolicy().hasHeightForWidth())
        self.groupBox_python.setSizePolicy(sizePolicy)
        self.groupBox_python.setMinimumSize(QSize(0, 95))
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox_python)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.radioButton_use_python_basic_console = QRadioButton(self.groupBox_python)
        self.radioButton_use_python_basic_console.setObjectName(u"radioButton_use_python_basic_console")

        self.verticalLayout_14.addWidget(self.radioButton_use_python_basic_console)

        self.radioButton_use_python_jupyter_console = QRadioButton(self.groupBox_python)
        self.radioButton_use_python_jupyter_console.setObjectName(u"radioButton_use_python_jupyter_console")

        self.verticalLayout_14.addWidget(self.radioButton_use_python_jupyter_console)


        self.horizontalLayout_3.addLayout(self.verticalLayout_14)

        self.line_2 = QFrame(self.groupBox_python)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_2)

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
        sizePolicy7.setHeightForWidth(self.comboBox_python_kernel.sizePolicy().hasHeightForWidth())
        self.comboBox_python_kernel.setSizePolicy(sizePolicy7)
        self.comboBox_python_kernel.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)

        self.horizontalLayout_11.addWidget(self.comboBox_python_kernel)

        self.pushButton_open_kernel_editor_python = QPushButton(self.groupBox_python)
        self.pushButton_open_kernel_editor_python.setObjectName(u"pushButton_open_kernel_editor_python")
        sizePolicy6.setHeightForWidth(self.pushButton_open_kernel_editor_python.sizePolicy().hasHeightForWidth())
        self.pushButton_open_kernel_editor_python.setSizePolicy(sizePolicy6)
        self.pushButton_open_kernel_editor_python.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_11.addWidget(self.pushButton_open_kernel_editor_python)


        self.verticalLayout_5.addLayout(self.horizontalLayout_11)


        self.horizontalLayout_3.addLayout(self.verticalLayout_5)


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
        self.groupBox_spine_db_editor = QGroupBox(self.SpineDBEditor)
        self.groupBox_spine_db_editor.setObjectName(u"groupBox_spine_db_editor")
        sizePolicy8 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.groupBox_spine_db_editor.sizePolicy().hasHeightForWidth())
        self.groupBox_spine_db_editor.setSizePolicy(sizePolicy8)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_spine_db_editor)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.checkBox_commit_at_exit = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_commit_at_exit.setObjectName(u"checkBox_commit_at_exit")
        self.checkBox_commit_at_exit.setTristate(True)

        self.verticalLayout_4.addWidget(self.checkBox_commit_at_exit)

        self.checkBox_db_editor_show_undo = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_db_editor_show_undo.setObjectName(u"checkBox_db_editor_show_undo")

        self.verticalLayout_4.addWidget(self.checkBox_db_editor_show_undo)

        self.checkBox_object_tree_sticky_selection = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_object_tree_sticky_selection.setObjectName(u"checkBox_object_tree_sticky_selection")

        self.verticalLayout_4.addWidget(self.checkBox_object_tree_sticky_selection)

        self.checkBox_relationship_items_follow = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_relationship_items_follow.setObjectName(u"checkBox_relationship_items_follow")

        self.verticalLayout_4.addWidget(self.checkBox_relationship_items_follow)

        self.checkBox_smooth_entity_graph_zoom = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_smooth_entity_graph_zoom.setObjectName(u"checkBox_smooth_entity_graph_zoom")

        self.verticalLayout_4.addWidget(self.checkBox_smooth_entity_graph_zoom)

        self.checkBox_smooth_entity_graph_rotation = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_smooth_entity_graph_rotation.setObjectName(u"checkBox_smooth_entity_graph_rotation")

        self.verticalLayout_4.addWidget(self.checkBox_smooth_entity_graph_rotation)

        self.checkBox_auto_expand_objects = QCheckBox(self.groupBox_spine_db_editor)
        self.checkBox_auto_expand_objects.setObjectName(u"checkBox_auto_expand_objects")

        self.verticalLayout_4.addWidget(self.checkBox_auto_expand_objects)


        self.verticalLayout_9.addWidget(self.groupBox_spine_db_editor)

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

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_3)


        self.verticalLayout_11.addWidget(self.groupBox)

        self.stackedWidget.addWidget(self.SpecificationEditors)
        self.splitter.addWidget(self.stackedWidget)

        self.verticalLayout_7.addWidget(self.splitter)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.buttonBox = QDialogButtonBox(SettingsForm)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.verticalLayout_7.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.listWidget, self.checkBox_open_previous_project)
        QWidget.setTabOrder(self.checkBox_open_previous_project, self.checkBox_exit_prompt)
        QWidget.setTabOrder(self.checkBox_exit_prompt, self.checkBox_save_project_before_closing)
        QWidget.setTabOrder(self.checkBox_save_project_before_closing, self.checkBox_datetime)
        QWidget.setTabOrder(self.checkBox_datetime, self.checkBox_color_toolbar_icons)
        QWidget.setTabOrder(self.checkBox_color_toolbar_icons, self.checkBox_use_smooth_zoom)
        QWidget.setTabOrder(self.checkBox_use_smooth_zoom, self.checkBox_use_curved_links)
        QWidget.setTabOrder(self.checkBox_use_curved_links, self.lineEdit_work_dir)
        QWidget.setTabOrder(self.lineEdit_work_dir, self.toolButton_browse_work)
        QWidget.setTabOrder(self.toolButton_browse_work, self.radioButton_bg_grid)
        QWidget.setTabOrder(self.radioButton_bg_grid, self.radioButton_bg_tree)
        QWidget.setTabOrder(self.radioButton_bg_tree, self.radioButton_bg_solid)
        QWidget.setTabOrder(self.radioButton_bg_solid, self.toolButton_bg_color)
        QWidget.setTabOrder(self.toolButton_bg_color, self.horizontalSlider_data_flow_animation_duration)
        QWidget.setTabOrder(self.horizontalSlider_data_flow_animation_duration, self.lineEdit_project_name)
        QWidget.setTabOrder(self.lineEdit_project_name, self.textEdit_project_description)
        QWidget.setTabOrder(self.textEdit_project_description, self.lineEdit_gams_path)
        QWidget.setTabOrder(self.lineEdit_gams_path, self.toolButton_browse_gams)
        QWidget.setTabOrder(self.toolButton_browse_gams, self.radioButton_use_julia_basic_console)
        QWidget.setTabOrder(self.radioButton_use_julia_basic_console, self.radioButton_use_julia_jupyter_console)
        QWidget.setTabOrder(self.radioButton_use_julia_jupyter_console, self.lineEdit_julia_path)
        QWidget.setTabOrder(self.lineEdit_julia_path, self.toolButton_browse_julia)
        QWidget.setTabOrder(self.toolButton_browse_julia, self.lineEdit_julia_project_path)
        QWidget.setTabOrder(self.lineEdit_julia_project_path, self.toolButton_browse_julia_project)
        QWidget.setTabOrder(self.toolButton_browse_julia_project, self.comboBox_julia_kernel)
        QWidget.setTabOrder(self.comboBox_julia_kernel, self.pushButton_open_kernel_editor_julia)
        QWidget.setTabOrder(self.pushButton_open_kernel_editor_julia, self.pushButton_install_julia)
        QWidget.setTabOrder(self.pushButton_install_julia, self.pushButton_add_up_spine_opt)
        QWidget.setTabOrder(self.pushButton_add_up_spine_opt, self.radioButton_use_python_basic_console)
        QWidget.setTabOrder(self.radioButton_use_python_basic_console, self.radioButton_use_python_jupyter_console)
        QWidget.setTabOrder(self.radioButton_use_python_jupyter_console, self.lineEdit_python_path)
        QWidget.setTabOrder(self.lineEdit_python_path, self.toolButton_browse_python)
        QWidget.setTabOrder(self.toolButton_browse_python, self.comboBox_python_kernel)
        QWidget.setTabOrder(self.comboBox_python_kernel, self.pushButton_open_kernel_editor_python)
        QWidget.setTabOrder(self.pushButton_open_kernel_editor_python, self.lineEdit_conda_path)
        QWidget.setTabOrder(self.lineEdit_conda_path, self.toolButton_browse_conda)
        QWidget.setTabOrder(self.toolButton_browse_conda, self.checkBox_commit_at_exit)
        QWidget.setTabOrder(self.checkBox_commit_at_exit, self.checkBox_object_tree_sticky_selection)
        QWidget.setTabOrder(self.checkBox_object_tree_sticky_selection, self.checkBox_relationship_items_follow)
        QWidget.setTabOrder(self.checkBox_relationship_items_follow, self.checkBox_smooth_entity_graph_zoom)
        QWidget.setTabOrder(self.checkBox_smooth_entity_graph_zoom, self.checkBox_smooth_entity_graph_rotation)
        QWidget.setTabOrder(self.checkBox_smooth_entity_graph_rotation, self.checkBox_auto_expand_objects)
        QWidget.setTabOrder(self.checkBox_auto_expand_objects, self.checkBox_save_spec_before_closing)
        QWidget.setTabOrder(self.checkBox_save_spec_before_closing, self.checkBox_spec_show_undo)

        self.retranslateUi(SettingsForm)
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)

        self.listWidget.setCurrentRow(-1)
        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SettingsForm)
    # setupUi

    def retranslateUi(self, SettingsForm):
        SettingsForm.setWindowTitle(QCoreApplication.translate("SettingsForm", u"Settings", None))

        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("SettingsForm", u"General", None));
        ___qlistwidgetitem1 = self.listWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("SettingsForm", u"Project", None));
        ___qlistwidgetitem2 = self.listWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("SettingsForm", u"Tools", None));
        ___qlistwidgetitem3 = self.listWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("SettingsForm", u"Db editor", None));
        ___qlistwidgetitem4 = self.listWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("SettingsForm", u"Spec. editors", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.groupBox_general.setTitle(QCoreApplication.translate("SettingsForm", u"General", None))
        self.label_4.setText(QCoreApplication.translate("SettingsForm", u"Data flow animation speed", None))
#if QT_CONFIG(tooltip)
        self.checkBox_delete_data.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Check this box to delete project item's data when a project item is removed from project. This means, that the project item directory and its contens will be deleted from your HD.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_delete_data.setText(QCoreApplication.translate("SettingsForm", u"Delete data when project item is removed from project", None))
        self.radioButton_bg_grid.setText(QCoreApplication.translate("SettingsForm", u"Grid", None))
        self.radioButton_bg_tree.setText(QCoreApplication.translate("SettingsForm", u"Tree of Life", None))
        self.radioButton_bg_solid.setText(QCoreApplication.translate("SettingsForm", u"Solid", None))
        self.label_9.setText(QCoreApplication.translate("SettingsForm", u"Color", None))
#if QT_CONFIG(tooltip)
        self.toolButton_bg_color.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick solid background color</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Work directory location. Leave empty to use default (\\work).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using default directory", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_work.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Work directory with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("SettingsForm", u"Slow", None))
        self.label_8.setText(QCoreApplication.translate("SettingsForm", u"Fast", None))
        self.label.setText(QCoreApplication.translate("SettingsForm", u"Work directory", None))
        self.label_7.setText(QCoreApplication.translate("SettingsForm", u"Design View background", None))
#if QT_CONFIG(tooltip)
        self.checkBox_custom_open_project_dialog.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select the type of dialog used in File-&gt;Open project...</p><p>Checking this box shows a custom dialog. Unchecking this box shows the OS provided 'select folder' dialog.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_custom_open_project_dialog.setText(QCoreApplication.translate("SettingsForm", u"Custom open project dialog", None))
#if QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Checking this shows the 'confirm exit' question box when quitting the app</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setText(QCoreApplication.translate("SettingsForm", u"Confirm exit", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or discete zoom is used in Design and Graph Views.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setText(QCoreApplication.translate("SettingsForm", u"Smooth zoom", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or straight connectors are used in Design View.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setText(QCoreApplication.translate("SettingsForm", u"Curved links", None))
#if QT_CONFIG(tooltip)
        self.checkBox_datetime.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, date and time string is appended into Event Log messages</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_datetime.setText(QCoreApplication.translate("SettingsForm", u"Show date and time in Event Log messages", None))
#if QT_CONFIG(tooltip)
        self.checkBox_save_project_before_closing.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select what to do if there are unsaved changes when closing a project or when quitting the app.</p><p>Unchecked: Don't save project and don't show question box</p><p>Partially checked: Show question box</p><p>Checked: Save project and don't show question box</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_save_project_before_closing.setText(QCoreApplication.translate("SettingsForm", u"Save project before closing", None))
#if QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, application opens the project at startup that was open the last time the application was quit</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setText(QCoreApplication.translate("SettingsForm", u"Open previous project at startup", None))
        self.checkBox_color_toolbar_icons.setText(QCoreApplication.translate("SettingsForm", u"Color toolbar icons", None))
        self.checkBox_prevent_overlapping.setText(QCoreApplication.translate("SettingsForm", u"Prevent items from overlapping", None))
        self.groupBox_project.setTitle(QCoreApplication.translate("SettingsForm", u"Project", None))
        self.label_2.setText(QCoreApplication.translate("SettingsForm", u"Name", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_project_name.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Change project name by typing a new name here</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_project_name.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"No project open", None))
        self.label_3.setText(QCoreApplication.translate("SettingsForm", u"Description", None))
#if QT_CONFIG(tooltip)
        self.textEdit_project_description.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Project description</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.textEdit_project_description.setHtml(QCoreApplication.translate("SettingsForm", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2'; font-size:8.25pt;\"><br /></p></body></html>", None))
        self.textEdit_project_description.setPlaceholderText("")
        self.groupBox_gams.setTitle(QCoreApplication.translate("SettingsForm", u"GAMS", None))
        self.label_11.setText(QCoreApplication.translate("SettingsForm", u"GAMS executable", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_gams_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Path to GAMS executable for Tool and GAMS Python bindings. Leave blank to use system's default</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_gams_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using system's default GAMS", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_gams.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick GAMS executable using a file browser (eg. gams.exe on Windows)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_julia.setTitle(QCoreApplication.translate("SettingsForm", u"Julia", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_julia_basic_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Use basic Julia REPL to execute Julia Tool specs</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_julia_basic_console.setText(QCoreApplication.translate("SettingsForm", u"Basic Console", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_julia_jupyter_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Use Jupyter Console to execute Julia Tool specs. Select a Julia kernel spec to use this option.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_julia_jupyter_console.setText(QCoreApplication.translate("SettingsForm", u"Jupyter Console", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia executable. Leave blank to use Julia defined in your system path.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia executable in system path", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia executable using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia environment/project directory for Julia Tool specifications. Leave blank to use the default environment.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setText("")
        self.lineEdit_julia_project_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia default project", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia project using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setText(QCoreApplication.translate("SettingsForm", u"...", None))
#if QT_CONFIG(tooltip)
        self.comboBox_julia_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select a Julia kernel spec for Jupyter Console. Open Kernel spec editor to view/add new ones.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_open_kernel_editor_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Open Julia kernel spec editor</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_open_kernel_editor_julia.setText(QCoreApplication.translate("SettingsForm", u"Kernel spec editor", None))
        self.pushButton_install_julia.setText(QCoreApplication.translate("SettingsForm", u"Install Julia", None))
        self.pushButton_add_up_spine_opt.setText(QCoreApplication.translate("SettingsForm", u"Add/Update SpineOpt", None))
#if QT_CONFIG(tooltip)
        self.groupBox_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Default settings</span> for new Python Tool specs. Defaults can be changed for each Tool specification separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_python.setTitle(QCoreApplication.translate("SettingsForm", u"Python (default settings)", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_python_basic_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Execute Python Tool specifications in basic Python REPL.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_python_basic_console.setText(QCoreApplication.translate("SettingsForm", u"Basic Console", None))
#if QT_CONFIG(tooltip)
        self.radioButton_use_python_jupyter_console.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Use Jupyter Console to execute Python Tool specs. Select a Python kernel spec to use this option.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_use_python_jupyter_console.setText(QCoreApplication.translate("SettingsForm", u"Jupyter Console", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Python interpreter for Python Console. Leave blank to use the Python that was used in launching Spine Toolbox.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using current Python interpreter", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Python interpreter using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.comboBox_python_kernel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select a Python kernel spec for Jupyter Console. Open Kernel spec editor to view/add new ones.</p><p><span style=\" font-weight:600;\">NOTE:</span> This is the <span style=\" font-weight:600;\">default setting</span> for new Python Tool specs. You can override this for each Tool spec separately.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.pushButton_open_kernel_editor_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Open Python kernel spec editor</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_open_kernel_editor_python.setText(QCoreApplication.translate("SettingsForm", u"Kernel spec editor", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SettingsForm", u"Conda", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_conda_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Select Conda executable for running Tool specifications in a Conda environment.</p><p>If you started Spine Toolbox in Conda, the <span style=\" font-weight:600;\">Conda executable is set up automatically</span>.</p><p>If not on Conda, please select <span style=\" font-weight:600;\">&lt;base_env&gt;\\scripts\\conda.exe</span> (on Win10), where <span style=\" font-weight:600;\">&lt;base_env&gt;</span> is the root directory of your Conda installation (i.e. base environment location).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_conda_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Select Conda executable...", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_conda.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Conda executable using a file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_browse_conda.setText("")
        self.groupBox_spine_db_editor.setTitle(QCoreApplication.translate("SettingsForm", u"Spine database editor", None))
#if QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Don't commit session and don't show message box</p><p>Partially checked: Show message box (default)</p><p>Checked: Commit session and don't show message box</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setText(QCoreApplication.translate("SettingsForm", u"Commit session before closing", None))
        self.checkBox_db_editor_show_undo.setText(QCoreApplication.translate("SettingsForm", u"Show undo notifications", None))
#if QT_CONFIG(tooltip)
        self.checkBox_object_tree_sticky_selection.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls how selecting items in Object tree <span style=\" font-weight:600;\">using the left mouse button</span> works. </p><p>When unchecked [default], Single selection is enabled. Pressing the Ctrl-button down enables multiple selection.</p><p>When checked, Multiple selection is enabled. Pressing the Ctrl-button down enables single selection.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_object_tree_sticky_selection.setText(QCoreApplication.translate("SettingsForm", u"Sticky selection in Entity trees", None))
#if QT_CONFIG(tooltip)
        self.checkBox_relationship_items_follow.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>When checked [default], moving Object items causes connected Relationship items to follow.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_relationship_items_follow.setText(QCoreApplication.translate("SettingsForm", u"Move relationships along with objects in Entity graph", None))
        self.checkBox_smooth_entity_graph_zoom.setText(QCoreApplication.translate("SettingsForm", u"Smooth Entity graph zoom", None))
        self.checkBox_smooth_entity_graph_rotation.setText(QCoreApplication.translate("SettingsForm", u"Smooth Entity graph rotation", None))
#if QT_CONFIG(tooltip)
        self.checkBox_auto_expand_objects.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Checked</span>: Whenever an object is included in the Entity graph, the graph automatically includes <span style=\" font-style:italic;\">all</span> its relationships.</p><p><span style=\" font-weight:600;\">Unchecked</span>: Whenever <span style=\" font-style:italic;\">all</span> the objects in a relationship are included in the Entity graph, the graph automatically includes the relationship.</p><p>Note: This setting is a global default, but can be locally overriden in every Spine DB editor session.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_auto_expand_objects.setText(QCoreApplication.translate("SettingsForm", u"Auto-expand objects by default in Entity graph", None))
        self.groupBox.setTitle(QCoreApplication.translate("SettingsForm", u"Specification editors", None))
#if QT_CONFIG(tooltip)
        self.checkBox_save_spec_before_closing.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Don't save specification and don't show message box</p><p>Partially checked: Show message box (default)</p><p>Checked: Save specification and don't show message box</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_save_spec_before_closing.setText(QCoreApplication.translate("SettingsForm", u"Save specification before closing", None))
        self.checkBox_spec_show_undo.setText(QCoreApplication.translate("SettingsForm", u"Show undo notifications", None))
    # retranslateUi

