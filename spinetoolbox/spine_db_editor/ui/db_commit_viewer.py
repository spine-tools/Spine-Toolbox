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
## Form generated from reading UI file 'db_commit_viewer.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QSizePolicy,
    QSplitter, QStackedWidget, QTextBrowser, QTreeWidget,
    QTreeWidgetItem, QWidget)

class Ui_DBCommitViewer(object):
    def setupUi(self, DBCommitViewer):
        if not DBCommitViewer.objectName():
            DBCommitViewer.setObjectName(u"DBCommitViewer")
        DBCommitViewer.resize(716, 218)
        self.horizontalLayout_2 = QHBoxLayout(DBCommitViewer)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(DBCommitViewer)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.commit_list = QTreeWidget(self.splitter)
        self.commit_list.setObjectName(u"commit_list")
        self.splitter.addWidget(self.commit_list)
        self.affected_items_widget_stack = QStackedWidget(self.splitter)
        self.affected_items_widget_stack.setObjectName(u"affected_items_widget_stack")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.horizontalLayout_3 = QHBoxLayout(self.page)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.affected_items = QTreeWidget(self.page)
        self.affected_items.setObjectName(u"affected_items")

        self.horizontalLayout_3.addWidget(self.affected_items)

        self.affected_items_widget_stack.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.horizontalLayout = QHBoxLayout(self.page_2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.no_affected_items_notice = QTextBrowser(self.page_2)
        self.no_affected_items_notice.setObjectName(u"no_affected_items_notice")
        self.no_affected_items_notice.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.no_affected_items_notice.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.no_affected_items_notice.setOpenLinks(False)

        self.horizontalLayout.addWidget(self.no_affected_items_notice)

        self.affected_items_widget_stack.addWidget(self.page_2)
        self.splitter.addWidget(self.affected_items_widget_stack)

        self.horizontalLayout_2.addWidget(self.splitter)


        self.retranslateUi(DBCommitViewer)

        QMetaObject.connectSlotsByName(DBCommitViewer)
    # setupUi

    def retranslateUi(self, DBCommitViewer):
        self.no_affected_items_notice.setHtml(QCoreApplication.translate("DBCommitViewer", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">No affected items found for selected commit.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Note that we cannot show items that have been removed by this or a later commit.</p></body></html>", None))
        pass
    # retranslateUi

