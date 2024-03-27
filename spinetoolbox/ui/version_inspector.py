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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(750, 300)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.tableView = QTableView(Form)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout.addWidget(self.tableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_add_row = QPushButton(Form)
        self.pushButton_add_row.setObjectName(u"pushButton_add_row")

        self.horizontalLayout.addWidget(self.pushButton_add_row)

        self.pushButton_refresh = QPushButton(Form)
        self.pushButton_refresh.setObjectName(u"pushButton_refresh")

        self.horizontalLayout.addWidget(self.pushButton_refresh)

        self.pushButton_commit = QPushButton(Form)
        self.pushButton_commit.setObjectName(u"pushButton_commit")

        self.horizontalLayout.addWidget(self.pushButton_commit)

        self.pushButton_pull = QPushButton(Form)
        self.pushButton_pull.setObjectName(u"pushButton_pull")

        self.horizontalLayout.addWidget(self.pushButton_pull)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.horizontalLayout_statusbar = QHBoxLayout()
        self.horizontalLayout_statusbar.setObjectName(u"horizontalLayout_statusbar")

        self.verticalLayout_2.addLayout(self.horizontalLayout_statusbar)

        QWidget.setTabOrder(self.tableView, self.pushButton_add_row)
        QWidget.setTabOrder(self.pushButton_add_row, self.pushButton_refresh)
        QWidget.setTabOrder(self.pushButton_refresh, self.pushButton_commit)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Version Inspector", None))
        self.pushButton_add_row.setText(QCoreApplication.translate("Form", u"Add row", None))
        self.pushButton_refresh.setText(QCoreApplication.translate("Form", u"Refresh", None))
        self.pushButton_commit.setText(QCoreApplication.translate("Form", u"Commit", None))
        self.pushButton_pull.setText(QCoreApplication.translate("Form", u"Pull", None))
    # retranslateUi

