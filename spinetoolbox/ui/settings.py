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

from spinetoolbox import resources_icons_rc

class Ui_SettingsForm(object):
    def setupUi(self, SettingsForm):
        if not SettingsForm.objectName():
            SettingsForm.setObjectName(u"SettingsForm")
        SettingsForm.setWindowModality(Qt.ApplicationModal)
        SettingsForm.resize(700, 550)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SettingsForm.sizePolicy().hasHeightForWidth())
        SettingsForm.setSizePolicy(sizePolicy)
        SettingsForm.setMinimumSize(QSize(700, 550))
        SettingsForm.setMaximumSize(QSize(16777215, 16777215))
        SettingsForm.setMouseTracking(False)
        SettingsForm.setFocusPolicy(Qt.StrongFocus)
        SettingsForm.setContextMenuPolicy(Qt.NoContextMenu)
        SettingsForm.setAutoFillBackground(False)
        self.verticalLayout_7 = QVBoxLayout(SettingsForm)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.listWidget = QListWidget(SettingsForm)
        icon = QIcon()
        icon.addFile(u":/icons/sliders-h.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem = QListWidgetItem(self.listWidget)
        __qlistwidgetitem.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem.setIcon(icon);
        __qlistwidgetitem.setFlags(Qt.ItemIsSelectable|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        icon1 = QIcon()
        icon1.addFile(u":/icons/project-diagram.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem1.setIcon(icon1);
        icon2 = QIcon()
        icon2.addFile(u":/icons/tools.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem2.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u":/icons/eye.svg", QSize(), QIcon.Normal, QIcon.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem3.setIcon(icon3);
        self.listWidget.setObjectName(u"listWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy1)
        self.listWidget.setMaximumSize(QSize(112, 16777215))
        self.listWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listWidget.setProperty("showDropIndicator", True)
        self.listWidget.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.listWidget.setDefaultDropAction(Qt.CopyAction)
        self.listWidget.setAlternatingRowColors(False)
        self.listWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listWidget.setMovement(QListView.Static)
        self.listWidget.setFlow(QListView.LeftToRight)
        self.listWidget.setProperty("isWrapping", True)
        self.listWidget.setResizeMode(QListView.Fixed)
        self.listWidget.setSpacing(0)
        self.listWidget.setViewMode(QListView.ListMode)
        self.listWidget.setUniformItemSizes(False)
        self.listWidget.setSelectionRectVisible(True)

        self.horizontalLayout_2.addWidget(self.listWidget)

        self.stackedWidget = QStackedWidget(SettingsForm)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
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
        self.gridLayout.setObjectName(u"gridLayout")
        self.checkBox_open_previous_project = QCheckBox(self.groupBox_general)
        self.checkBox_open_previous_project.setObjectName(u"checkBox_open_previous_project")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.checkBox_open_previous_project.sizePolicy().hasHeightForWidth())
        self.checkBox_open_previous_project.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.checkBox_open_previous_project, 0, 0, 1, 1)

        self.checkBox_exit_prompt = QCheckBox(self.groupBox_general)
        self.checkBox_exit_prompt.setObjectName(u"checkBox_exit_prompt")
        self.checkBox_exit_prompt.setTristate(False)

        self.gridLayout.addWidget(self.checkBox_exit_prompt, 1, 0, 1, 1)

        self.checkBox_save_at_exit = QCheckBox(self.groupBox_general)
        self.checkBox_save_at_exit.setObjectName(u"checkBox_save_at_exit")
        self.checkBox_save_at_exit.setTristate(True)

        self.gridLayout.addWidget(self.checkBox_save_at_exit, 2, 0, 1, 1)

        self.checkBox_datetime = QCheckBox(self.groupBox_general)
        self.checkBox_datetime.setObjectName(u"checkBox_datetime")

        self.gridLayout.addWidget(self.checkBox_datetime, 3, 0, 1, 1)

        self.checkBox_delete_data = QCheckBox(self.groupBox_general)
        self.checkBox_delete_data.setObjectName(u"checkBox_delete_data")

        self.gridLayout.addWidget(self.checkBox_delete_data, 4, 0, 1, 1)

        self.label = QLabel(self.groupBox_general)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(7)
        self.label.setFont(font)

        self.gridLayout.addWidget(self.label, 5, 0, 1, 1)

        self.checkBox_use_smooth_zoom = QCheckBox(self.groupBox_general)
        self.checkBox_use_smooth_zoom.setObjectName(u"checkBox_use_smooth_zoom")

        self.gridLayout.addWidget(self.checkBox_use_smooth_zoom, 7, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox_general)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font)

        self.gridLayout.addWidget(self.label_7, 10, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lineEdit_work_dir = QLineEdit(self.groupBox_general)
        self.lineEdit_work_dir.setObjectName(u"lineEdit_work_dir")
        self.lineEdit_work_dir.setMinimumSize(QSize(0, 20))
        self.lineEdit_work_dir.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_work_dir.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.lineEdit_work_dir)

        self.toolButton_browse_work = QToolButton(self.groupBox_general)
        self.toolButton_browse_work.setObjectName(u"toolButton_browse_work")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.toolButton_browse_work.sizePolicy().hasHeightForWidth())
        self.toolButton_browse_work.setSizePolicy(sizePolicy5)
        self.toolButton_browse_work.setMaximumSize(QSize(22, 22))
        icon4 = QIcon()
        icon4.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_browse_work.setIcon(icon4)

        self.horizontalLayout_6.addWidget(self.toolButton_browse_work)


        self.gridLayout.addLayout(self.horizontalLayout_6, 6, 0, 1, 1)

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
        self.toolButton_bg_color.setMaximumSize(QSize(22, 22))
        self.toolButton_bg_color.setIconSize(QSize(16, 16))

        self.horizontalLayout_4.addWidget(self.toolButton_bg_color)


        self.gridLayout.addLayout(self.horizontalLayout_4, 11, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox_general)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 12, 0, 1, 1)

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


        self.gridLayout.addLayout(self.verticalLayout_3, 13, 0, 1, 1)

        self.checkBox_use_curved_links = QCheckBox(self.groupBox_general)
        self.checkBox_use_curved_links.setObjectName(u"checkBox_use_curved_links")

        self.gridLayout.addWidget(self.checkBox_use_curved_links, 8, 0, 1, 1)


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
        sizePolicy3.setHeightForWidth(self.groupBox_project.sizePolicy().hasHeightForWidth())
        self.groupBox_project.setSizePolicy(sizePolicy3)
        self.groupBox_project.setMinimumSize(QSize(250, 150))
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_project)
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
        self.verticalLayout_8 = QVBoxLayout(self.ExternalTools)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
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
        self.lineEdit_gams_path.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_gams_path.setClearButtonEnabled(True)

        self.gridLayout_4.addWidget(self.lineEdit_gams_path, 2, 0, 1, 1)

        self.toolButton_browse_gams = QToolButton(self.groupBox_gams)
        self.toolButton_browse_gams.setObjectName(u"toolButton_browse_gams")
        self.toolButton_browse_gams.setMaximumSize(QSize(22, 22))
        self.toolButton_browse_gams.setIcon(icon4)

        self.gridLayout_4.addWidget(self.toolButton_browse_gams, 2, 1, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_gams)

        self.groupBox_julia = QGroupBox(self.ExternalTools)
        self.groupBox_julia.setObjectName(u"groupBox_julia")
        self.gridLayout_5 = QGridLayout(self.groupBox_julia)
        self.gridLayout_5.setSpacing(6)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.toolButton_browse_julia_project = QToolButton(self.groupBox_julia)
        self.toolButton_browse_julia_project.setObjectName(u"toolButton_browse_julia_project")
        self.toolButton_browse_julia_project.setMaximumSize(QSize(22, 22))
        self.toolButton_browse_julia_project.setIcon(icon4)

        self.gridLayout_5.addWidget(self.toolButton_browse_julia_project, 4, 1, 1, 1)

        self.lineEdit_julia_project_path = QLineEdit(self.groupBox_julia)
        self.lineEdit_julia_project_path.setObjectName(u"lineEdit_julia_project_path")
        self.lineEdit_julia_project_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_julia_project_path.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_julia_project_path.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.lineEdit_julia_project_path, 4, 0, 1, 1)

        self.toolButton_browse_julia = QToolButton(self.groupBox_julia)
        self.toolButton_browse_julia.setObjectName(u"toolButton_browse_julia")
        self.toolButton_browse_julia.setMaximumSize(QSize(22, 22))
        self.toolButton_browse_julia.setIcon(icon4)

        self.gridLayout_5.addWidget(self.toolButton_browse_julia, 3, 1, 1, 1)

        self.lineEdit_julia_path = QLineEdit(self.groupBox_julia)
        self.lineEdit_julia_path.setObjectName(u"lineEdit_julia_path")
        self.lineEdit_julia_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_julia_path.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_julia_path.setClearButtonEnabled(True)

        self.gridLayout_5.addWidget(self.lineEdit_julia_path, 3, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_julia)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font)

        self.gridLayout_5.addWidget(self.label_12, 2, 0, 1, 1)

        self.checkBox_use_embedded_julia = QCheckBox(self.groupBox_julia)
        self.checkBox_use_embedded_julia.setObjectName(u"checkBox_use_embedded_julia")

        self.gridLayout_5.addWidget(self.checkBox_use_embedded_julia, 6, 0, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_julia)

        self.groupBox_python = QGroupBox(self.ExternalTools)
        self.groupBox_python.setObjectName(u"groupBox_python")
        self.groupBox_python.setMinimumSize(QSize(0, 95))
        self.gridLayout_6 = QGridLayout(self.groupBox_python)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label_13 = QLabel(self.groupBox_python)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font)

        self.gridLayout_6.addWidget(self.label_13, 0, 0, 1, 1)

        self.lineEdit_python_path = QLineEdit(self.groupBox_python)
        self.lineEdit_python_path.setObjectName(u"lineEdit_python_path")
        self.lineEdit_python_path.setMinimumSize(QSize(0, 20))
        self.lineEdit_python_path.setMaximumSize(QSize(16777215, 20))
        self.lineEdit_python_path.setClearButtonEnabled(True)

        self.gridLayout_6.addWidget(self.lineEdit_python_path, 1, 0, 1, 1)

        self.checkBox_use_embedded_python = QCheckBox(self.groupBox_python)
        self.checkBox_use_embedded_python.setObjectName(u"checkBox_use_embedded_python")

        self.gridLayout_6.addWidget(self.checkBox_use_embedded_python, 2, 0, 1, 1)

        self.toolButton_browse_python = QToolButton(self.groupBox_python)
        self.toolButton_browse_python.setObjectName(u"toolButton_browse_python")
        self.toolButton_browse_python.setMaximumSize(QSize(22, 22))
        self.toolButton_browse_python.setIcon(icon4)

        self.gridLayout_6.addWidget(self.toolButton_browse_python, 1, 1, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_python)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_7)

        self.verticalSpacer_8 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_8)

        self.stackedWidget.addWidget(self.ExternalTools)
        self.Views = QWidget()
        self.Views.setObjectName(u"Views")
        self.verticalLayout_9 = QVBoxLayout(self.Views)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.groupBox_data_store = QGroupBox(self.Views)
        self.groupBox_data_store.setObjectName(u"groupBox_data_store")
        sizePolicy6 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.groupBox_data_store.sizePolicy().hasHeightForWidth())
        self.groupBox_data_store.setSizePolicy(sizePolicy6)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_data_store)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.checkBox_commit_at_exit = QCheckBox(self.groupBox_data_store)
        self.checkBox_commit_at_exit.setObjectName(u"checkBox_commit_at_exit")
        self.checkBox_commit_at_exit.setTristate(True)

        self.verticalLayout_4.addWidget(self.checkBox_commit_at_exit)

        self.checkBox_object_tree_sticky_selection = QCheckBox(self.groupBox_data_store)
        self.checkBox_object_tree_sticky_selection.setObjectName(u"checkBox_object_tree_sticky_selection")

        self.verticalLayout_4.addWidget(self.checkBox_object_tree_sticky_selection)

        self.checkBox_relationship_items_follow = QCheckBox(self.groupBox_data_store)
        self.checkBox_relationship_items_follow.setObjectName(u"checkBox_relationship_items_follow")

        self.verticalLayout_4.addWidget(self.checkBox_relationship_items_follow)

        self.checkBox_smooth_entity_graph_zoom = QCheckBox(self.groupBox_data_store)
        self.checkBox_smooth_entity_graph_zoom.setObjectName(u"checkBox_smooth_entity_graph_zoom")

        self.verticalLayout_4.addWidget(self.checkBox_smooth_entity_graph_zoom)

        self.checkBox_smooth_entity_graph_rotation = QCheckBox(self.groupBox_data_store)
        self.checkBox_smooth_entity_graph_rotation.setObjectName(u"checkBox_smooth_entity_graph_rotation")

        self.verticalLayout_4.addWidget(self.checkBox_smooth_entity_graph_rotation)


        self.verticalLayout_9.addWidget(self.groupBox_data_store)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_9)

        self.stackedWidget.addWidget(self.Views)

        self.horizontalLayout_2.addWidget(self.stackedWidget)


        self.verticalLayout_7.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 9, -1, 18)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.pushButton_ok = QPushButton(SettingsForm)
        self.pushButton_ok.setObjectName(u"pushButton_ok")
        self.pushButton_ok.setMinimumSize(QSize(75, 23))
        self.pushButton_ok.setMaximumSize(QSize(75, 23))

        self.horizontalLayout.addWidget(self.pushButton_ok)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_cancel = QPushButton(SettingsForm)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")
        self.pushButton_cancel.setMinimumSize(QSize(75, 23))
        self.pushButton_cancel.setMaximumSize(QSize(75, 23))

        self.horizontalLayout.addWidget(self.pushButton_cancel)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout_7.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.listWidget, self.checkBox_open_previous_project)
        QWidget.setTabOrder(self.checkBox_open_previous_project, self.checkBox_exit_prompt)
        QWidget.setTabOrder(self.checkBox_exit_prompt, self.checkBox_save_at_exit)
        QWidget.setTabOrder(self.checkBox_save_at_exit, self.checkBox_datetime)
        QWidget.setTabOrder(self.checkBox_datetime, self.checkBox_delete_data)
        QWidget.setTabOrder(self.checkBox_delete_data, self.lineEdit_work_dir)
        QWidget.setTabOrder(self.lineEdit_work_dir, self.toolButton_browse_work)
        QWidget.setTabOrder(self.toolButton_browse_work, self.checkBox_use_smooth_zoom)
        QWidget.setTabOrder(self.checkBox_use_smooth_zoom, self.radioButton_bg_grid)
        QWidget.setTabOrder(self.radioButton_bg_grid, self.radioButton_bg_solid)
        QWidget.setTabOrder(self.radioButton_bg_solid, self.toolButton_bg_color)
        QWidget.setTabOrder(self.toolButton_bg_color, self.horizontalSlider_data_flow_animation_duration)
        QWidget.setTabOrder(self.horizontalSlider_data_flow_animation_duration, self.lineEdit_project_name)
        QWidget.setTabOrder(self.lineEdit_project_name, self.textEdit_project_description)
        QWidget.setTabOrder(self.textEdit_project_description, self.lineEdit_gams_path)
        QWidget.setTabOrder(self.lineEdit_gams_path, self.toolButton_browse_gams)
        QWidget.setTabOrder(self.toolButton_browse_gams, self.lineEdit_julia_path)
        QWidget.setTabOrder(self.lineEdit_julia_path, self.toolButton_browse_julia)
        QWidget.setTabOrder(self.toolButton_browse_julia, self.lineEdit_julia_project_path)
        QWidget.setTabOrder(self.lineEdit_julia_project_path, self.toolButton_browse_julia_project)
        QWidget.setTabOrder(self.toolButton_browse_julia_project, self.checkBox_use_embedded_julia)
        QWidget.setTabOrder(self.checkBox_use_embedded_julia, self.lineEdit_python_path)
        QWidget.setTabOrder(self.lineEdit_python_path, self.toolButton_browse_python)
        QWidget.setTabOrder(self.toolButton_browse_python, self.checkBox_use_embedded_python)
        QWidget.setTabOrder(self.checkBox_use_embedded_python, self.checkBox_commit_at_exit)
        QWidget.setTabOrder(self.checkBox_commit_at_exit, self.checkBox_object_tree_sticky_selection)
        QWidget.setTabOrder(self.checkBox_object_tree_sticky_selection, self.pushButton_ok)
        QWidget.setTabOrder(self.pushButton_ok, self.pushButton_cancel)

        self.retranslateUi(SettingsForm)
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)

        self.listWidget.setCurrentRow(-1)
        self.stackedWidget.setCurrentIndex(3)


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
        ___qlistwidgetitem3.setText(QCoreApplication.translate("SettingsForm", u"View", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.groupBox_general.setTitle(QCoreApplication.translate("SettingsForm", u"General", None))
#if QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, Application opens the project at startup that was open the last time the application was exited</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_open_previous_project.setText(QCoreApplication.translate("SettingsForm", u"Open previous project at startup", None))
#if QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, confirm exit prompt is shown. If unchecked, application exits without prompt.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_exit_prompt.setText(QCoreApplication.translate("SettingsForm", u"Show confirm exit prompt", None))
#if QT_CONFIG(tooltip)
        self.checkBox_save_at_exit.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Does not save project and does not show message box</p><p>Partially checked: Shows message box (default)</p><p>Checked: Saves project and does not show message box</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_save_at_exit.setText(QCoreApplication.translate("SettingsForm", u"Save project at exit", None))
#if QT_CONFIG(tooltip)
        self.checkBox_datetime.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, date and time string is appended into Event Log messages</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_datetime.setText(QCoreApplication.translate("SettingsForm", u"Show date and time in Event Log messages", None))
#if QT_CONFIG(tooltip)
        self.checkBox_delete_data.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Check this box to delete project item's data when a project item is removed from project. This means, that the project item directory and its contens will be deleted from your HD.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_delete_data.setText(QCoreApplication.translate("SettingsForm", u"Delete data when project item is removed from project", None))
        self.label.setText(QCoreApplication.translate("SettingsForm", u"Work directory", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or discete zoom is used in Design and Graph Views.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_smooth_zoom.setText(QCoreApplication.translate("SettingsForm", u"Smooth zoom", None))
        self.label_7.setText(QCoreApplication.translate("SettingsForm", u"Design View background", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Work directory location. Leave empty to use default (\\work).</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_work_dir.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using default directory", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_work.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Work directory with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radioButton_bg_grid.setText(QCoreApplication.translate("SettingsForm", u"Grid", None))
        self.radioButton_bg_tree.setText(QCoreApplication.translate("SettingsForm", u"Tree of Life", None))
        self.radioButton_bg_solid.setText(QCoreApplication.translate("SettingsForm", u"Solid", None))
        self.label_9.setText(QCoreApplication.translate("SettingsForm", u"Color", None))
#if QT_CONFIG(tooltip)
        self.toolButton_bg_color.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick solid background color</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("SettingsForm", u"Data flow animation speed", None))
        self.label_5.setText(QCoreApplication.translate("SettingsForm", u"Slow", None))
        self.label_8.setText(QCoreApplication.translate("SettingsForm", u"Fast", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Controls whether smooth or straight connectors are used in Design View.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_curved_links.setText(QCoreApplication.translate("SettingsForm", u"Curved links", None))
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
        self.toolButton_browse_gams.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick GAMS executable with file browser (eg. gams.exe on Windows)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_julia.setTitle(QCoreApplication.translate("SettingsForm", u"Julia", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia project with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_browse_julia_project.setText(QCoreApplication.translate("SettingsForm", u"...", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia project</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_project_path.setText("")
        self.lineEdit_julia_project_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia home project", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Julia executable with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Julia executable. Leave blank to use Julia defined in your system path.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Julia executable in system path", None))
        self.label_12.setText(QCoreApplication.translate("SettingsForm", u"Julia executable", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_embedded_julia.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, Julia Tools and scripts will be executed in the embedded Julia Console (Shell). If unchecked, Julia Tools and scripts will be executed in a terminal as an individual process. I.e. the same as running `julia script.jl` in terminal.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_embedded_julia.setText(QCoreApplication.translate("SettingsForm", u"Use embedded Julia Console", None))
        self.groupBox_python.setTitle(QCoreApplication.translate("SettingsForm", u"Python", None))
        self.label_13.setText(QCoreApplication.translate("SettingsForm", u"Python interpreter", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_path.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Python interpreter. Leave blank to use Python defined in your system path.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_path.setPlaceholderText(QCoreApplication.translate("SettingsForm", u"Using Python interpreter in system path", None))
#if QT_CONFIG(tooltip)
        self.checkBox_use_embedded_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>If checked, Python Tools and scripts will be executed in the embedded Python Console (Shell). If unchecked, Python Tools and scripts will be executed in a terminal as an individual process. I.e. the same as running `python script.py` in terminal.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_use_embedded_python.setText(QCoreApplication.translate("SettingsForm", u"Use embedded Python Console", None))
#if QT_CONFIG(tooltip)
        self.toolButton_browse_python.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Pick Python interpreter with file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_data_store.setTitle(QCoreApplication.translate("SettingsForm", u"Data store form", None))
#if QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Unchecked: Does not commit session and does not show message box</p><p>Partially checked: Shows message box (default)</p><p>Checked: Commits session and does not show message box</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_commit_at_exit.setText(QCoreApplication.translate("SettingsForm", u"Commit session when form is closed", None))
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
        self.pushButton_ok.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Saves changes and closes the window</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_ok.setText(QCoreApplication.translate("SettingsForm", u"Ok", None))
#if QT_CONFIG(tooltip)
        self.pushButton_cancel.setToolTip(QCoreApplication.translate("SettingsForm", u"<html><head/><body><p>Closes the window without saving changes</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_cancel.setText(QCoreApplication.translate("SettingsForm", u"Cancel", None))
    # retranslateUi

