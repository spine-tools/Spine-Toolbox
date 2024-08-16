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
## Form generated from reading UI file 'mainwindowlite.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QColumnView, QComboBox, QGraphicsView,
    QGroupBox, QHBoxLayout, QMainWindow, QMenu,
    QMenuBar, QScrollArea, QSizePolicy, QSplitter,
    QStatusBar, QToolButton, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qgraphicsviews import DesignQGraphicsView
from spinetoolbox import resources_icons_rc

class Ui_MainWindowLite(object):
    def setupUi(self, MainWindowLite):
        if not MainWindowLite.objectName():
            MainWindowLite.setObjectName(u"MainWindowLite")
        MainWindowLite.resize(800, 600)
        self.actionSwitch_to_expert_mode = QAction(MainWindowLite)
        self.actionSwitch_to_expert_mode.setObjectName(u"actionSwitch_to_expert_mode")
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/retweet.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSwitch_to_expert_mode.setIcon(icon)
        self.actionExecute_group = QAction(MainWindowLite)
        self.actionExecute_group.setObjectName(u"actionExecute_group")
        icon1 = QIcon()
        icon1.addFile(u":/icons/menu_icons/play-circle-regular.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionExecute_group.setIcon(icon1)
        self.actionExecute_group.setMenuRole(QAction.MenuRole.NoRole)
        self.actionStop = QAction(MainWindowLite)
        self.actionStop.setObjectName(u"actionStop")
        icon2 = QIcon()
        icon2.addFile(u":/icons/menu_icons/stop-circle-regular.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionStop.setIcon(icon2)
        self.actionStop.setMenuRole(QAction.MenuRole.NoRole)
        self.actionShow_event_log_console = QAction(MainWindowLite)
        self.actionShow_event_log_console.setObjectName(u"actionShow_event_log_console")
        icon3 = QIcon()
        icon3.addFile(u":/icons/menu_icons/edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionShow_event_log_console.setIcon(icon3)
        self.actionShow_event_log_console.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(MainWindowLite)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.scrollArea = QScrollArea(self.splitter)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setAutoFillBackground(False)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 780, 293))
        self.horizontalLayout = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox_2 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.toolButton_execute_group = QToolButton(self.groupBox_2)
        self.toolButton_execute_group.setObjectName(u"toolButton_execute_group")
        self.toolButton_execute_group.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.verticalLayout_4.addWidget(self.toolButton_execute_group)

        self.comboBox_groups = QComboBox(self.groupBox_2)
        self.comboBox_groups.setObjectName(u"comboBox_groups")

        self.verticalLayout_4.addWidget(self.comboBox_groups)

        self.toolButton_stop = QToolButton(self.groupBox_2)
        self.toolButton_stop.setObjectName(u"toolButton_stop")
        self.toolButton_stop.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.verticalLayout_4.addWidget(self.toolButton_stop)


        self.horizontalLayout.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolButton_show_event_log = QToolButton(self.groupBox)
        self.toolButton_show_event_log.setObjectName(u"toolButton_show_event_log")
        self.toolButton_show_event_log.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.verticalLayout.addWidget(self.toolButton_show_event_log)

        self.toolButton_to_expert_mode = QToolButton(self.groupBox)
        self.toolButton_to_expert_mode.setObjectName(u"toolButton_to_expert_mode")
        self.toolButton_to_expert_mode.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.verticalLayout.addWidget(self.toolButton_to_expert_mode)


        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.columnView = QColumnView(self.groupBox_3)
        self.columnView.setObjectName(u"columnView")
        self.columnView.setMinimumSize(QSize(50, 30))

        self.verticalLayout_5.addWidget(self.columnView)


        self.horizontalLayout.addWidget(self.groupBox_3)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.splitter.addWidget(self.scrollArea)
        self.graphicsView = DesignQGraphicsView(self.splitter)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.TextAntialiasing)
        self.graphicsView.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphicsView.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.graphicsView.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.graphicsView.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.graphicsView.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemBoundingRect)
        self.splitter.addWidget(self.graphicsView)

        self.verticalLayout_2.addWidget(self.splitter)

        MainWindowLite.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindowLite)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindowLite.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindowLite)
        self.statusbar.setObjectName(u"statusbar")
        MainWindowLite.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindowLite)

        QMetaObject.connectSlotsByName(MainWindowLite)
    # setupUi

    def retranslateUi(self, MainWindowLite):
        MainWindowLite.setWindowTitle(QCoreApplication.translate("MainWindowLite", u"Spine Toolbox [user mode]", None))
        self.actionSwitch_to_expert_mode.setText(QCoreApplication.translate("MainWindowLite", u"Switch to expert mode", None))
#if QT_CONFIG(shortcut)
        self.actionSwitch_to_expert_mode.setShortcut(QCoreApplication.translate("MainWindowLite", u"\u00a7", None))
#endif // QT_CONFIG(shortcut)
        self.actionExecute_group.setText(QCoreApplication.translate("MainWindowLite", u"Execute group", None))
        self.actionStop.setText(QCoreApplication.translate("MainWindowLite", u"Stop", None))
        self.actionShow_event_log_console.setText(QCoreApplication.translate("MainWindowLite", u"Show event log and console", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindowLite", u"Execution", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindowLite", u"Actions", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindowLite", u"Scenarios", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindowLite", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindowLite", u"Help", None))
    # retranslateUi

