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
## Form generated from reading UI file 'version_inspector.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(750, 477)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableView = QTableView(Form)
        self.tableView.setObjectName(u"tableView")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.horizontalHeader().setProperty("showSortIndicator", True)

        self.verticalLayout.addWidget(self.tableView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_refresh = QPushButton(Form)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")

        self.horizontalLayout_2.addWidget(self.pushButton_refresh)

        self.pushButton_pull = QPushButton(Form)
        self.pushButton_pull.setObjectName(u"pushButton_pull")

        self.horizontalLayout_2.addWidget(self.pushButton_pull)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.tableView_current = QTableView(Form)
        self.tableView_current.setObjectName(u"tableView_current")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tableView_current.sizePolicy().hasHeightForWidth())
        self.tableView_current.setSizePolicy(sizePolicy1)
        self.tableView_current.setMaximumSize(QSize(16777215, 80))
        self.tableView_current.setCornerButtonEnabled(False)

        self.verticalLayout.addWidget(self.tableView_current)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_commit = QPushButton(Form)
        self.pushButton_commit.setObjectName(u"pushButton_commit")

        self.horizontalLayout.addWidget(self.pushButton_commit)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_statusbar = QHBoxLayout()
        self.horizontalLayout_statusbar.setObjectName(u"horizontalLayout_statusbar")

        self.verticalLayout.addLayout(self.horizontalLayout_statusbar)

        QWidget.setTabOrder(self.tableView, self.tableView_current)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Version Inspector", None))
        self.pushButton_refresh.setText(QCoreApplication.translate("Form", u"Refresh", None))
        self.pushButton_pull.setText(QCoreApplication.translate("Form", u"Pull", None))
        self.pushButton_commit.setText(QCoreApplication.translate("Form", u"Commit", None))
    # retranslateUi

