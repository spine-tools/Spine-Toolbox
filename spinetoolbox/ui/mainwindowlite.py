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
from PySide6.QtWidgets import (QApplication, QColumnView, QDockWidget, QGraphicsView,
    QGroupBox, QHBoxLayout, QMainWindow, QMenu,
    QMenuBar, QScrollArea, QSizePolicy, QSplitter,
    QStatusBar, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qgraphicsviews import DesignQGraphicsView
from spinetoolbox.widgets.custom_qtextbrowser import CustomQTextBrowserLite
from spinetoolbox import resources_icons_rc

class Ui_MainWindowLite(object):
    def setupUi(self, MainWindowLite):
        if not MainWindowLite.objectName():
            MainWindowLite.setObjectName(u"MainWindowLite")
        MainWindowLite.resize(761, 600)
        self.actionSwitch_to_design_mode = QAction(MainWindowLite)
        self.actionSwitch_to_design_mode.setObjectName(u"actionSwitch_to_design_mode")
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/retweet.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSwitch_to_design_mode.setIcon(icon)
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
        self.actionShow_event_log = QAction(MainWindowLite)
        self.actionShow_event_log.setObjectName(u"actionShow_event_log")
        icon3 = QIcon()
        icon3.addFile(u":/icons/menu_icons/edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionShow_event_log.setIcon(icon3)
        self.actionShow_event_log.setMenuRole(QAction.MenuRole.NoRole)
        self.actionShow_console = QAction(MainWindowLite)
        self.actionShow_console.setObjectName(u"actionShow_console")
        icon4 = QIcon()
        icon4.addFile(u":/icons/menu_icons/terminal.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionShow_console.setIcon(icon4)
        self.actionShow_console.setMenuRole(QAction.MenuRole.NoRole)
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 741, 169))
        self.horizontalLayout = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.columnView = QColumnView(self.groupBox)
        self.columnView.setObjectName(u"columnView")
        self.columnView.setMinimumSize(QSize(50, 30))

        self.verticalLayout_5.addWidget(self.columnView)


        self.horizontalLayout.addWidget(self.groupBox)

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
        self.menubar.setGeometry(QRect(0, 0, 761, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindowLite.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindowLite)
        self.statusbar.setObjectName(u"statusbar")
        MainWindowLite.setStatusBar(self.statusbar)
        self.dockWidget_event_log = QDockWidget(MainWindowLite)
        self.dockWidget_event_log.setObjectName(u"dockWidget_event_log")
        self.dockWidget_event_log.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.dockWidget_event_log.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_3 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.textBrowser = CustomQTextBrowserLite(self.dockWidgetContents)
        self.textBrowser.setObjectName(u"textBrowser")

        self.verticalLayout_3.addWidget(self.textBrowser)

        self.dockWidget_event_log.setWidget(self.dockWidgetContents)
        MainWindowLite.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockWidget_event_log)
        self.dockWidget_console = QDockWidget(MainWindowLite)
        self.dockWidget_console.setObjectName(u"dockWidget_console")
        self.dockWidget_console.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.dockWidget_console.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName(u"dockWidgetContents_2")
        self.dockWidget_console.setWidget(self.dockWidgetContents_2)
        MainWindowLite.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockWidget_console)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindowLite)

        QMetaObject.connectSlotsByName(MainWindowLite)
    # setupUi

    def retranslateUi(self, MainWindowLite):
        MainWindowLite.setWindowTitle(QCoreApplication.translate("MainWindowLite", u"Spine Toolbox [user mode]", None))
        self.actionSwitch_to_design_mode.setText(QCoreApplication.translate("MainWindowLite", u"Switch to design mode", None))
#if QT_CONFIG(tooltip)
        self.actionSwitch_to_design_mode.setToolTip(QCoreApplication.translate("MainWindowLite", u"Switch to design mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionSwitch_to_design_mode.setShortcut(QCoreApplication.translate("MainWindowLite", u"\u00a7", None))
#endif // QT_CONFIG(shortcut)
        self.actionExecute_group.setText(QCoreApplication.translate("MainWindowLite", u"Execute group", None))
        self.actionStop.setText(QCoreApplication.translate("MainWindowLite", u"Stop", None))
        self.actionShow_event_log.setText(QCoreApplication.translate("MainWindowLite", u"Show event log", None))
#if QT_CONFIG(tooltip)
        self.actionShow_event_log.setToolTip(QCoreApplication.translate("MainWindowLite", u"Show event log", None))
#endif // QT_CONFIG(tooltip)
        self.actionShow_console.setText(QCoreApplication.translate("MainWindowLite", u"Show console", None))
#if QT_CONFIG(tooltip)
        self.actionShow_console.setToolTip(QCoreApplication.translate("MainWindowLite", u"Show console", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox.setTitle(QCoreApplication.translate("MainWindowLite", u"Scenarios", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindowLite", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindowLite", u"Help", None))
        self.dockWidget_event_log.setWindowTitle(QCoreApplication.translate("MainWindowLite", u"Event Log", None))
        self.dockWidget_console.setWindowTitle(QCoreApplication.translate("MainWindowLite", u"Console", None))
    # retranslateUi

