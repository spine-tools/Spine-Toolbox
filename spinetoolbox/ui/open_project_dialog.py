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
## Form generated from reading UI file 'open_project_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
    QSizePolicy, QSpacerItem, QToolButton, QTreeView,
    QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_combobox import OpenProjectDialogComboBox
from spinetoolbox import resources_icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 450)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.toolButton_root = QToolButton(Dialog)
        self.toolButton_root.setObjectName(u"toolButton_root")
        icon = QIcon()
        icon.addFile(u":/icons/slash.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_root.setIcon(icon)

        self.horizontalLayout.addWidget(self.toolButton_root)

        self.toolButton_home = QToolButton(Dialog)
        self.toolButton_home.setObjectName(u"toolButton_home")
        icon1 = QIcon()
        icon1.addFile(u":/icons/home.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_home.setIcon(icon1)

        self.horizontalLayout.addWidget(self.toolButton_home)

        self.toolButton_documents = QToolButton(Dialog)
        self.toolButton_documents.setObjectName(u"toolButton_documents")
        icon2 = QIcon()
        icon2.addFile(u":/icons/book.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_documents.setIcon(icon2)

        self.horizontalLayout.addWidget(self.toolButton_documents)

        self.toolButton_desktop = QToolButton(Dialog)
        self.toolButton_desktop.setObjectName(u"toolButton_desktop")
        icon3 = QIcon()
        icon3.addFile(u":/icons/desktop.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_desktop.setIcon(icon3)

        self.horizontalLayout.addWidget(self.toolButton_desktop)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.comboBox_current_path = OpenProjectDialogComboBox(Dialog)
        self.comboBox_current_path.setObjectName(u"comboBox_current_path")
        self.comboBox_current_path.setContextMenuPolicy(Qt.CustomContextMenu)
        self.comboBox_current_path.setEditable(True)

        self.verticalLayout.addWidget(self.comboBox_current_path)

        self.treeView_file_system = QTreeView(Dialog)
        self.treeView_file_system.setObjectName(u"treeView_file_system")
        self.treeView_file_system.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.treeView_file_system.setUniformRowHeights(True)
        self.treeView_file_system.setSortingEnabled(True)
        self.treeView_file_system.setAnimated(False)

        self.verticalLayout.addWidget(self.treeView_file_system)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.comboBox_current_path, self.treeView_file_system)
        QWidget.setTabOrder(self.treeView_file_system, self.toolButton_root)
        QWidget.setTabOrder(self.toolButton_root, self.toolButton_home)
        QWidget.setTabOrder(self.toolButton_home, self.toolButton_documents)
        QWidget.setTabOrder(self.toolButton_documents, self.toolButton_desktop)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Open project", None))
#if QT_CONFIG(tooltip)
        self.toolButton_root.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Root</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.toolButton_home.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Home</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.toolButton_documents.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Documents</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_documents.setText("")
#if QT_CONFIG(tooltip)
        self.toolButton_desktop.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Desktop</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("Dialog", u"Select Spine Toolbox project directory", None))
    # retranslateUi

