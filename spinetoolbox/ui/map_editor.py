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
## Form generated from reading UI file 'map_editor.ui'
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
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from spinetoolbox.widgets.custom_qtableview import MapTableView

class Ui_MapEditor(object):
    def setupUi(self, MapEditor):
        if not MapEditor.objectName():
            MapEditor.setObjectName(u"MapEditor")
        MapEditor.resize(400, 300)
        self.verticalLayout = QVBoxLayout(MapEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.map_table_view = MapTableView(MapEditor)
        self.map_table_view.setObjectName(u"map_table_view")

        self.verticalLayout.addWidget(self.map_table_view)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.convert_leaves_button = QPushButton(MapEditor)
        self.convert_leaves_button.setObjectName(u"convert_leaves_button")

        self.horizontalLayout.addWidget(self.convert_leaves_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(MapEditor)

        QMetaObject.connectSlotsByName(MapEditor)
    # setupUi

    def retranslateUi(self, MapEditor):
        MapEditor.setWindowTitle(QCoreApplication.translate("MapEditor", u"Form", None))
#if QT_CONFIG(tooltip)
        self.convert_leaves_button.setToolTip(QCoreApplication.translate("MapEditor", u"Converts leaf maps to time series.\n"
"Requires that all indexes are DateTimes\n"
"and values are floats.", None))
#endif // QT_CONFIG(tooltip)
        self.convert_leaves_button.setText(QCoreApplication.translate("MapEditor", u"Convert Leaves to Time Series", None))
    # retranslateUi

