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
## Form generated from reading UI file 'import_errors.ui'
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


class Ui_ImportErrors(object):
    def setupUi(self, ImportErrors):
        if not ImportErrors.objectName():
            ImportErrors.setObjectName(u"ImportErrors")
        ImportErrors.resize(400, 300)
        self.verticalLayout = QVBoxLayout(ImportErrors)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.error_count_label = QLabel(ImportErrors)
        self.error_count_label.setObjectName(u"error_count_label")

        self.verticalLayout.addWidget(self.error_count_label)

        self.import_count_label = QLabel(ImportErrors)
        self.import_count_label.setObjectName(u"import_count_label")

        self.verticalLayout.addWidget(self.import_count_label)

        self.error_list = QListWidget(ImportErrors)
        self.error_list.setObjectName(u"error_list")

        self.verticalLayout.addWidget(self.error_list)


        self.retranslateUi(ImportErrors)

        QMetaObject.connectSlotsByName(ImportErrors)
    # setupUi

    def retranslateUi(self, ImportErrors):
        ImportErrors.setWindowTitle(QCoreApplication.translate("ImportErrors", u"Form", None))
        self.error_count_label.setText(QCoreApplication.translate("ImportErrors", u"Number of errors:", None))
        self.import_count_label.setText(QCoreApplication.translate("ImportErrors", u"Number of imports:", None))
    # retranslateUi

