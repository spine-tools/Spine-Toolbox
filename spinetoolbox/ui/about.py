# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from spinetoolbox import resources_icons_rc
from spinetoolbox import resources_logos_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.ApplicationModal)
        Form.resize(400, 550)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(400, 550))
        Form.setMaximumSize(QSize(400, 550))
        font = QFont()
        font.setStyleStrategy(QFont.PreferDefault)
        Form.setFont(font)
        Form.setAutoFillBackground(False)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget_8 = QWidget(Form)
        self.widget_8.setObjectName(u"widget_8")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_8.sizePolicy().hasHeightForWidth())
        self.widget_8.setSizePolicy(sizePolicy1)
        self.widget_8.setMinimumSize(QSize(400, 150))
        self.widget_8.setMaximumSize(QSize(400, 150))
        self.horizontalLayout = QHBoxLayout(self.widget_8)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.widget_8)
        self.widget.setObjectName(u"widget")
        sizePolicy1.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy1)
        self.widget.setMinimumSize(QSize(200, 150))
        self.widget.setMaximumSize(QSize(200, 150))
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Base, brush)
        palette.setBrush(QPalette.Active, QPalette.Window, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.widget.setPalette(palette)
        self.widget.setAutoFillBackground(True)
        self.horizontalLayout_10 = QHBoxLayout(self.widget)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(150, 150))
        self.label.setMaximumSize(QSize(150, 150))
        self.label.setPixmap(QPixmap(u":/symbols/Spine_symbol.png"))
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_10.addWidget(self.label)


        self.horizontalLayout.addWidget(self.widget)

        self.widget_9 = QWidget(self.widget_8)
        self.widget_9.setObjectName(u"widget_9")
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.Base, brush)
        brush1 = QBrush(QColor(0, 74, 194, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        self.widget_9.setPalette(palette1)
        self.widget_9.setAutoFillBackground(True)
        self.verticalLayout = QVBoxLayout(self.widget_9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_spine_toolbox = QLabel(self.widget_9)
        self.label_spine_toolbox.setObjectName(u"label_spine_toolbox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_spine_toolbox.sizePolicy().hasHeightForWidth())
        self.label_spine_toolbox.setSizePolicy(sizePolicy2)
        self.label_spine_toolbox.setMinimumSize(QSize(0, 0))
        self.label_spine_toolbox.setMaximumSize(QSize(16777215, 16777215))
        self.label_spine_toolbox.setBaseSize(QSize(0, 0))
        font1 = QFont()
        font1.setFamily(u"Arial Black")
        font1.setPointSize(6)
        font1.setBold(False)
        font1.setWeight(50)
        font1.setStyleStrategy(QFont.PreferDefault)
        self.label_spine_toolbox.setFont(font1)
        self.label_spine_toolbox.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.label_spine_toolbox.setScaledContents(True)
        self.label_spine_toolbox.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_toolbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label_spinedb_api = QLabel(self.widget_9)
        self.label_spinedb_api.setObjectName(u"label_spinedb_api")
        sizePolicy2.setHeightForWidth(self.label_spinedb_api.sizePolicy().hasHeightForWidth())
        self.label_spinedb_api.setSizePolicy(sizePolicy2)
        font2 = QFont()
        font2.setFamily(u"Arial Black")
        font2.setPointSize(6)
        font2.setStyleStrategy(QFont.PreferDefault)
        self.label_spinedb_api.setFont(font2)
        self.label_spinedb_api.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.label_spinedb_api.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spinedb_api)

        self.label_spine_engine = QLabel(self.widget_9)
        self.label_spine_engine.setObjectName(u"label_spine_engine")
        sizePolicy2.setHeightForWidth(self.label_spine_engine.sizePolicy().hasHeightForWidth())
        self.label_spine_engine.setSizePolicy(sizePolicy2)
        self.label_spine_engine.setFont(font2)
        self.label_spine_engine.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.label_spine_engine.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_engine)

        self.label_spine_items = QLabel(self.widget_9)
        self.label_spine_items.setObjectName(u"label_spine_items")
        sizePolicy2.setHeightForWidth(self.label_spine_items.sizePolicy().hasHeightForWidth())
        self.label_spine_items.setSizePolicy(sizePolicy2)
        self.label_spine_items.setFont(font2)
        self.label_spine_items.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.label_spine_items.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_spine_items)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)


        self.horizontalLayout.addWidget(self.widget_9)


        self.verticalLayout_2.addWidget(self.widget_8)

        self.widget_3 = QWidget(Form)
        self.widget_3.setObjectName(u"widget_3")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy3)
        self.widget_3.setMinimumSize(QSize(400, 60))
        self.widget_3.setMaximumSize(QSize(400, 1000))
        palette2 = QPalette()
        palette2.setBrush(QPalette.Active, QPalette.Base, brush)
        palette2.setBrush(QPalette.Active, QPalette.Window, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette2.setBrush(QPalette.Disabled, QPalette.Base, brush)
        palette2.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.widget_3.setPalette(palette2)
        self.widget_3.setAutoFillBackground(True)
        self.horizontalLayout_4 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.textBrowser = QTextBrowser(self.widget_3)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setMinimumSize(QSize(0, 0))
        self.textBrowser.setMaximumSize(QSize(400, 1000))
        font3 = QFont()
        font3.setPointSize(7)
        font3.setStyleStrategy(QFont.PreferDefault)
        self.textBrowser.setFont(font3)
        self.textBrowser.setFrameShape(QFrame.StyledPanel)
        self.textBrowser.setFrameShadow(QFrame.Sunken)
        self.textBrowser.setLineWidth(1)
        self.textBrowser.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
        self.textBrowser.setOpenExternalLinks(True)

        self.horizontalLayout_4.addWidget(self.textBrowser)


        self.verticalLayout_2.addWidget(self.widget_3)

        self.widget_2 = QWidget(Form)
        self.widget_2.setObjectName(u"widget_2")
        sizePolicy1.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
        self.widget_2.setSizePolicy(sizePolicy1)
        self.widget_2.setMinimumSize(QSize(400, 255))
        self.widget_2.setMaximumSize(QSize(400, 255))
        palette3 = QPalette()
        palette3.setBrush(QPalette.Active, QPalette.Base, brush)
        brush2 = QBrush(QColor(118, 168, 246, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette3.setBrush(QPalette.Active, QPalette.Window, brush2)
        palette3.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Window, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Base, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Window, brush2)
        self.widget_2.setPalette(palette3)
        self.widget_2.setAutoFillBackground(True)
        self.verticalLayout_3 = QVBoxLayout(self.widget_2)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.widget_5 = QWidget(self.widget_2)
        self.widget_5.setObjectName(u"widget_5")
        sizePolicy2.setHeightForWidth(self.widget_5.sizePolicy().hasHeightForWidth())
        self.widget_5.setSizePolicy(sizePolicy2)
        self.widget_5.setMinimumSize(QSize(0, 255))
        self.widget_5.setMaximumSize(QSize(16777215, 255))
        palette4 = QPalette()
        palette4.setBrush(QPalette.Active, QPalette.Base, brush)
        brush3 = QBrush(QColor(153, 204, 51, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette4.setBrush(QPalette.Active, QPalette.Window, brush3)
        palette4.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette4.setBrush(QPalette.Inactive, QPalette.Window, brush3)
        palette4.setBrush(QPalette.Disabled, QPalette.Base, brush3)
        palette4.setBrush(QPalette.Disabled, QPalette.Window, brush3)
        self.widget_5.setPalette(palette4)
        self.widget_5.setAutoFillBackground(True)
        self.horizontalLayout_5 = QHBoxLayout(self.widget_5)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.widget_6 = QWidget(self.widget_5)
        self.widget_6.setObjectName(u"widget_6")
        palette5 = QPalette()
        palette5.setBrush(QPalette.Active, QPalette.Base, brush)
        palette5.setBrush(QPalette.Active, QPalette.Window, brush)
        palette5.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette5.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette5.setBrush(QPalette.Disabled, QPalette.Base, brush)
        palette5.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.widget_6.setPalette(palette5)
        self.widget_6.setAutoFillBackground(True)
        self.verticalLayout_6 = QVBoxLayout(self.widget_6)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.widget_4 = QWidget(self.widget_6)
        self.widget_4.setObjectName(u"widget_4")
        sizePolicy1.setHeightForWidth(self.widget_4.sizePolicy().hasHeightForWidth())
        self.widget_4.setSizePolicy(sizePolicy1)
        self.widget_4.setMinimumSize(QSize(200, 85))
        self.widget_4.setMaximumSize(QSize(200, 85))
        self.horizontalLayout_2 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.widget_4)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(16777215, 16777215))
        self.label_5.setPixmap(QPixmap(u":/partner_logos/VTT_Multicolour_Logo.jpg"))
        self.label_5.setScaledContents(True)
        self.label_5.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_5)


        self.verticalLayout_6.addWidget(self.widget_4)

        self.widget_10 = QWidget(self.widget_6)
        self.widget_10.setObjectName(u"widget_10")
        sizePolicy1.setHeightForWidth(self.widget_10.sizePolicy().hasHeightForWidth())
        self.widget_10.setSizePolicy(sizePolicy1)
        self.widget_10.setMinimumSize(QSize(200, 85))
        self.widget_10.setMaximumSize(QSize(200, 16777215))
        self.horizontalLayout_3 = QHBoxLayout(self.widget_10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_7 = QLabel(self.widget_10)
        self.label_7.setObjectName(u"label_7")
        sizePolicy1.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy1)
        self.label_7.setMaximumSize(QSize(67, 67))
        self.label_7.setPixmap(QPixmap(u":/partner_logos/UCD_Dublin_logo.png"))
        self.label_7.setScaledContents(True)
        self.label_7.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_7)


        self.verticalLayout_6.addWidget(self.widget_10)

        self.widget_11 = QWidget(self.widget_6)
        self.widget_11.setObjectName(u"widget_11")
        sizePolicy1.setHeightForWidth(self.widget_11.sizePolicy().hasHeightForWidth())
        self.widget_11.setSizePolicy(sizePolicy1)
        self.widget_11.setMinimumSize(QSize(200, 85))
        self.widget_11.setMaximumSize(QSize(200, 85))
        self.horizontalLayout_6 = QHBoxLayout(self.widget_11)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_6 = QLabel(self.widget_11)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMaximumSize(QSize(68, 68))
        self.label_6.setPixmap(QPixmap(u":/partner_logos/KTH_logo.png"))
        self.label_6.setScaledContents(True)
        self.label_6.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_6)


        self.verticalLayout_6.addWidget(self.widget_11)


        self.horizontalLayout_5.addWidget(self.widget_6)

        self.widget_7 = QWidget(self.widget_5)
        self.widget_7.setObjectName(u"widget_7")
        palette6 = QPalette()
        palette6.setBrush(QPalette.Active, QPalette.Base, brush)
        palette6.setBrush(QPalette.Active, QPalette.Window, brush)
        palette6.setBrush(QPalette.Inactive, QPalette.Base, brush)
        palette6.setBrush(QPalette.Inactive, QPalette.Window, brush)
        palette6.setBrush(QPalette.Disabled, QPalette.Base, brush)
        palette6.setBrush(QPalette.Disabled, QPalette.Window, brush)
        self.widget_7.setPalette(palette6)
        self.widget_7.setAutoFillBackground(True)
        self.verticalLayout_5 = QVBoxLayout(self.widget_7)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.widget_12 = QWidget(self.widget_7)
        self.widget_12.setObjectName(u"widget_12")
        sizePolicy1.setHeightForWidth(self.widget_12.sizePolicy().hasHeightForWidth())
        self.widget_12.setSizePolicy(sizePolicy1)
        self.widget_12.setMinimumSize(QSize(200, 85))
        self.widget_12.setMaximumSize(QSize(200, 85))
        self.horizontalLayout_7 = QHBoxLayout(self.widget_12)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_4 = QLabel(self.widget_12)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        self.label_4.setMaximumSize(QSize(166, 34))
        self.label_4.setPixmap(QPixmap(u":/partner_logos/Energy_Reform_logo.png"))
        self.label_4.setScaledContents(True)
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.label_4)


        self.verticalLayout_5.addWidget(self.widget_12)

        self.widget_13 = QWidget(self.widget_7)
        self.widget_13.setObjectName(u"widget_13")
        sizePolicy1.setHeightForWidth(self.widget_13.sizePolicy().hasHeightForWidth())
        self.widget_13.setSizePolicy(sizePolicy1)
        self.widget_13.setMinimumSize(QSize(200, 85))
        self.widget_13.setMaximumSize(QSize(200, 85))
        self.horizontalLayout_8 = QHBoxLayout(self.widget_13)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_2 = QLabel(self.widget_13)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setMaximumSize(QSize(90, 32))
        self.label_2.setPixmap(QPixmap(u":/partner_logos/KU_Leuven_logo.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_8.addWidget(self.label_2)


        self.verticalLayout_5.addWidget(self.widget_13)

        self.widget_14 = QWidget(self.widget_7)
        self.widget_14.setObjectName(u"widget_14")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.widget_14.sizePolicy().hasHeightForWidth())
        self.widget_14.setSizePolicy(sizePolicy4)
        self.widget_14.setMinimumSize(QSize(0, 85))
        self.widget_14.setMaximumSize(QSize(16777215, 85))
        self.horizontalLayout_9 = QHBoxLayout(self.widget_14)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.widget_14)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setMinimumSize(QSize(200, 85))
        self.label_3.setMaximumSize(QSize(200, 85))
        font4 = QFont()
        font4.setFamily(u"Arial Black")
        font4.setPointSize(8)
        font4.setBold(True)
        font4.setWeight(75)
        font4.setStyleStrategy(QFont.PreferDefault)
        self.label_3.setFont(font4)
        self.label_3.setStyleSheet(u"background-color: rgb(0, 74, 194);")
        self.label_3.setTextFormat(Qt.RichText)
        self.label_3.setAlignment(Qt.AlignCenter)
        self.label_3.setMargin(0)
        self.label_3.setOpenExternalLinks(True)

        self.horizontalLayout_9.addWidget(self.label_3)


        self.verticalLayout_5.addWidget(self.widget_14)


        self.horizontalLayout_5.addWidget(self.widget_7)


        self.verticalLayout_3.addWidget(self.widget_5)


        self.verticalLayout_2.addWidget(self.widget_2)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"About Spine Toolbox", None))
        self.label_spine_toolbox.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>Spine Toolbox</p></body></html>", None))
        self.label_spinedb_api.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spinedb_api</p></body></html>", None))
        self.label_spine_engine.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spine_engine</p></body></html>", None))
        self.label_spine_items.setText(QCoreApplication.translate("Form", u"<html><head/><body><p>spine_items</p></body></html>", None))
        self.textBrowser.setDocumentTitle("")
        self.textBrowser.setHtml(QCoreApplication.translate("Form", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:7pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8.25pt;\"><br /></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"<html><head/><body><p><a href=\"http://www.spine-model.org\"><span style=\" color:#ffffff; text-decoration: none\">www.spine-model.org</span></a></p></body></html>", None))
    # retranslateUi

