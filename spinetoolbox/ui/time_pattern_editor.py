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
## Form generated from reading UI file 'time_pattern_editor.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHeaderView, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qtableview import IndexedValueTableView

class Ui_TimePatternEditor(object):
    def setupUi(self, TimePatternEditor):
        if not TimePatternEditor.objectName():
            TimePatternEditor.setObjectName(u"TimePatternEditor")
        TimePatternEditor.resize(586, 443)
        self.verticalLayout = QVBoxLayout(TimePatternEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(TimePatternEditor)
        self.label.setObjectName(u"label")
        self.label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.label)

        self.pattern_edit_table = IndexedValueTableView(TimePatternEditor)
        self.pattern_edit_table.setObjectName(u"pattern_edit_table")
        self.pattern_edit_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.pattern_edit_table.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout.addWidget(self.pattern_edit_table)


        self.retranslateUi(TimePatternEditor)

        QMetaObject.connectSlotsByName(TimePatternEditor)
    # setupUi

    def retranslateUi(self, TimePatternEditor):
        TimePatternEditor.setWindowTitle(QCoreApplication.translate("TimePatternEditor", u"Form", None))
        self.label.setText(QCoreApplication.translate("TimePatternEditor", u"<html><head/><body><p><a href=\"https://spine-toolbox.readthedocs.io/en/latest/parameter_value_editor.html#time-patterns\"><span style=\" text-decoration: underline; color:#0000ff;\">Link</span></a> to time period syntax.</p></body></html>", None))
    # retranslateUi

