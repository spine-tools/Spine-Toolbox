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
## Form generated from reading UI file 'parameter_value_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialogButtonBox,
    QHBoxLayout, QLabel, QSizePolicy, QSpacerItem,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_ParameterValueEditor(object):
    def setupUi(self, ParameterValueEditor):
        if not ParameterValueEditor.objectName():
            ParameterValueEditor.setObjectName(u"ParameterValueEditor")
        ParameterValueEditor.resize(700, 400)
        self.reject_action = QAction(ParameterValueEditor)
        self.reject_action.setObjectName(u"reject_action")
        self.accept_action = QAction(ParameterValueEditor)
        self.accept_action.setObjectName(u"accept_action")
        self.verticalLayout = QVBoxLayout(ParameterValueEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.parameter_type_selector_layout = QHBoxLayout()
        self.parameter_type_selector_layout.setObjectName(u"parameter_type_selector_layout")
        self.parameter_type_selector_label = QLabel(ParameterValueEditor)
        self.parameter_type_selector_label.setObjectName(u"parameter_type_selector_label")

        self.parameter_type_selector_layout.addWidget(self.parameter_type_selector_label)

        self.parameter_type_selector = QComboBox(ParameterValueEditor)
        self.parameter_type_selector.setObjectName(u"parameter_type_selector")

        self.parameter_type_selector_layout.addWidget(self.parameter_type_selector)

        self.parameter_type_selector_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.parameter_type_selector_layout.addItem(self.parameter_type_selector_spacer)


        self.verticalLayout.addLayout(self.parameter_type_selector_layout)

        self.editor_stack = QStackedWidget(ParameterValueEditor)
        self.editor_stack.setObjectName(u"editor_stack")

        self.verticalLayout.addWidget(self.editor_stack)

        self.button_box = QDialogButtonBox(ParameterValueEditor)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(ParameterValueEditor)

        self.editor_stack.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(ParameterValueEditor)
    # setupUi

    def retranslateUi(self, ParameterValueEditor):
        ParameterValueEditor.setWindowTitle(QCoreApplication.translate("ParameterValueEditor", u"Edit parameter_value", None))
        self.reject_action.setText(QCoreApplication.translate("ParameterValueEditor", u"Close", None))
#if QT_CONFIG(shortcut)
        self.reject_action.setShortcut(QCoreApplication.translate("ParameterValueEditor", u"Esc", None))
#endif // QT_CONFIG(shortcut)
        self.accept_action.setText(QCoreApplication.translate("ParameterValueEditor", u"OK", None))
#if QT_CONFIG(shortcut)
        self.accept_action.setShortcut(QCoreApplication.translate("ParameterValueEditor", u"Ctrl+Return", None))
#endif // QT_CONFIG(shortcut)
        self.parameter_type_selector_label.setText(QCoreApplication.translate("ParameterValueEditor", u"Parameter type", None))
    # retranslateUi

