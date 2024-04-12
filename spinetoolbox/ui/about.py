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
## Form generated from reading UI file 'about.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QSizePolicy, QSpacerItem, QTextBrowser,
    QToolButton, QVBoxLayout, QWidget)
from spinetoolbox import resources_icons_rc
from spinetoolbox import resources_logos_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.ApplicationModal)
        Form.resize(400, 614)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Base, brush)
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush)
        Form.setPalette(palette)
        Form.setAutoFillBackground(True)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMaximumSize(QSize(199, 132))
        self.label.setFrameShape(QFrame.NoFrame)
        self.label.setPixmap(QPixmap(u":/symbols/spinetoolbox_on_wht.png"))
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(False)
        self.label.setMargin(15)
        self.label.setIndent(-1)

        self.horizontalLayout.addWidget(self.label)

        self.frame_9 = QFrame(Form)
        self.frame_9.setObjectName(u"frame_9")
        sizePolicy.setHeightForWidth(self.frame_9.sizePolicy().hasHeightForWidth())
        self.frame_9.setSizePolicy(sizePolicy)
        self.frame_9.setMaximumSize(QSize(199, 215))
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.Base, brush)
        brush1 = QBrush(QColor(0, 74, 194, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        self.frame_9.setPalette(palette1)
        self.frame_9.setCursor(QCursor(Qt.ArrowCursor))
        self.frame_9.setAutoFillBackground(True)
        self.verticalLayout = QVBoxLayout(self.frame_9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, -1, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_spine_toolbox = QLabel(self.frame_9)
        self.label_spine_toolbox.setObjectName(u"label_spine_toolbox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_spine_toolbox.sizePolicy().hasHeightForWidth())
        self.label_spine_toolbox.setSizePolicy(sizePolicy2)
        self.label_spine_toolbox.setMinimumSize(QSize(0, 0))
        self.label_spine_toolbox.setMaximumSize(QSize(16777215, 16777215))
        self.label_spine_toolbox.setBaseSize(QSize(0, 0))
        font = QFont()
        font.setFamilies([u"Arial Black"])
        font.setPointSize(6)
        font.setBold(False)
        font.setStyleStrategy(QFont.PreferDefault)
        self.label_spine_toolbox.setFont(font)
        self.label_spine_toolbox.setStyleSheet(u"QLabel {color: rgb(255, 255, 255);}")
        self.label_spine_toolbox.setScaledContents(True)
        self.label_spine_toolbox.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_toolbox)

        self.label_spinedb_api = QLabel(self.frame_9)
        self.label_spinedb_api.setObjectName(u"label_spinedb_api")
        sizePolicy2.setHeightForWidth(self.label_spinedb_api.sizePolicy().hasHeightForWidth())
        self.label_spinedb_api.setSizePolicy(sizePolicy2)
        font1 = QFont()
        font1.setFamilies([u"Arial Black"])
        font1.setPointSize(6)
        font1.setStyleStrategy(QFont.PreferDefault)
        self.label_spinedb_api.setFont(font1)
        self.label_spinedb_api.setStyleSheet(u"QLabel {color: rgb(255, 255, 255);}")
        self.label_spinedb_api.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spinedb_api)

        self.label_spine_engine = QLabel(self.frame_9)
        self.label_spine_engine.setObjectName(u"label_spine_engine")
        sizePolicy2.setHeightForWidth(self.label_spine_engine.sizePolicy().hasHeightForWidth())
        self.label_spine_engine.setSizePolicy(sizePolicy2)
        self.label_spine_engine.setFont(font1)
        self.label_spine_engine.setStyleSheet(u"QLabel {color: rgb(255, 255, 255);}")
        self.label_spine_engine.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_engine)

        self.label_spine_items = QLabel(self.frame_9)
        self.label_spine_items.setObjectName(u"label_spine_items")
        sizePolicy2.setHeightForWidth(self.label_spine_items.sizePolicy().hasHeightForWidth())
        self.label_spine_items.setSizePolicy(sizePolicy2)
        self.label_spine_items.setFont(font1)
        self.label_spine_items.setStyleSheet(u"QLabel {color: rgb(255, 255, 255);}")
        self.label_spine_items.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_items)

        self.label_python = QLabel(self.frame_9)
        self.label_python.setObjectName(u"label_python")
        sizePolicy2.setHeightForWidth(self.label_python.sizePolicy().hasHeightForWidth())
        self.label_python.setSizePolicy(sizePolicy2)
        self.label_python.setFont(font1)
        self.label_python.setStyleSheet(u"QLabel {color: rgb(255, 255, 255);}")
        self.label_python.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_python)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer)

        self.toolButton_copy_to_clipboard = QToolButton(self.frame_9)
        self.toolButton_copy_to_clipboard.setObjectName(u"toolButton_copy_to_clipboard")
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/copy.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_copy_to_clipboard.setIcon(icon)

        self.horizontalLayout_8.addWidget(self.toolButton_copy_to_clipboard)


        self.verticalLayout.addLayout(self.horizontalLayout_8)


        self.horizontalLayout.addWidget(self.frame_9)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.textBrowser = QTextBrowser(Form)
        self.textBrowser.setObjectName(u"textBrowser")
        font2 = QFont()
        font2.setPointSize(7)
        font2.setStyleStrategy(QFont.PreferDefault)
        self.textBrowser.setFont(font2)
        self.textBrowser.setFrameShape(QFrame.StyledPanel)
        self.textBrowser.setFrameShadow(QFrame.Sunken)
        self.textBrowser.setLineWidth(1)
        self.textBrowser.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
        self.textBrowser.setOpenExternalLinks(True)

        self.horizontalLayout_7.addWidget(self.textBrowser)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_7 = QLabel(Form)
        self.label_7.setObjectName(u"label_7")
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)
        self.label_7.setMaximumSize(QSize(67, 67))
        self.label_7.setPixmap(QPixmap(u":/partner_logos/UCD_Dublin_logo.png"))
        self.label_7.setScaledContents(True)
        self.label_7.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_7)


        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_5 = QLabel(Form)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(89, 60))
        self.label_5.setPixmap(QPixmap(u":/partner_logos/VTT_Multicolour_Logo.jpg"))
        self.label_5.setScaledContents(True)
        self.label_5.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_5)


        self.gridLayout.addLayout(self.horizontalLayout_6, 1, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_6 = QLabel(Form)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMaximumSize(QSize(68, 68))
        self.label_6.setPixmap(QPixmap(u":/partner_logos/KTH_logo.png"))
        self.label_6.setScaledContents(True)
        self.label_6.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_6)


        self.gridLayout.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy3)
        self.label_3.setMinimumSize(QSize(200, 0))
        font3 = QFont()
        font3.setFamilies([u"Arial Black"])
        font3.setPointSize(8)
        font3.setBold(True)
        font3.setStyleStrategy(QFont.PreferDefault)
        self.label_3.setFont(font3)
        self.label_3.setStyleSheet(u"background-color: rgb(0, 74, 194);")
        self.label_3.setTextFormat(Qt.RichText)
        self.label_3.setScaledContents(True)
        self.label_3.setAlignment(Qt.AlignCenter)
        self.label_3.setMargin(1)
        self.label_3.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.label_3, 3, 1, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setMaximumSize(QSize(166, 34))
        self.label_4.setPixmap(QPixmap(u":/partner_logos/Energy_Reform_logo.png"))
        self.label_4.setScaledContents(True)
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_5.addWidget(self.label_4)


        self.gridLayout.addLayout(self.horizontalLayout_5, 1, 1, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMaximumSize(QSize(90, 32))
        self.label_2.setPixmap(QPixmap(u":/partner_logos/KU_Leuven_logo.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_4.addWidget(self.label_2)


        self.gridLayout.addLayout(self.horizontalLayout_4, 2, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"About Spine Toolbox", None))
        self.label_spine_toolbox.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>Spine Toolbox</p></body></html>", None))
        self.label_spinedb_api.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spinedb_api</p></body></html>", None))
        self.label_spine_engine.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spine_engine</p></body></html>", None))
        self.label_spine_items.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spine_items</p></body></html>", None))
        self.label_python.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>Python</p></body></html>", None))
#if QT_CONFIG(tooltip)
        self.toolButton_copy_to_clipboard.setToolTip(QCoreApplication.translate("Form", u"Copy to clipboard", None))
#endif // QT_CONFIG(tooltip)
        self.textBrowser.setHtml(QCoreApplication.translate("Form", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:7pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2'; font-size:8.25pt;\"><br /></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"<html><head/><body><p><a href=\"http://www.spine-model.org\"><span style=\" color:#ffffff; text-decoration: none\">www.spine-model.org</span></a></p></body></html>", None))
    # retranslateUi

