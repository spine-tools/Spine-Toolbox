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
## Form generated from reading UI file 'data_store_properties.ui'
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

from spinetoolbox.widgets.custom_qlineedits import CustomQLineEdit
from spinetoolbox.widgets.custom_qlineedits import PropertyQLineEdit

from spinetoolbox import resources_icons_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(415, 382)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_ds_name = QLabel(Form)
        self.label_ds_name.setObjectName(u"label_ds_name")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_ds_name.sizePolicy().hasHeightForWidth())
        self.label_ds_name.setSizePolicy(sizePolicy)
        self.label_ds_name.setMinimumSize(QSize(0, 20))
        self.label_ds_name.setMaximumSize(QSize(16777215, 20))
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        font.setKerning(True)
        self.label_ds_name.setFont(font)
        self.label_ds_name.setStyleSheet(u"background-color: #ecd8c6;")
        self.label_ds_name.setFrameShape(QFrame.Box)
        self.label_ds_name.setFrameShadow(QFrame.Sunken)
        self.label_ds_name.setLineWidth(1)
        self.label_ds_name.setScaledContents(False)
        self.label_ds_name.setAlignment(Qt.AlignCenter)
        self.label_ds_name.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_ds_name)

        self.scrollArea_5 = QScrollArea(Form)
        self.scrollArea_5.setObjectName(u"scrollArea_5")
        self.scrollArea_5.setWidgetResizable(True)
        self.scrollAreaWidgetContents_7 = QWidget()
        self.scrollAreaWidgetContents_7.setObjectName(u"scrollAreaWidgetContents_7")
        self.scrollAreaWidgetContents_7.setGeometry(QRect(0, 0, 413, 360))
        self.verticalLayout_25 = QVBoxLayout(self.scrollAreaWidgetContents_7)
        self.verticalLayout_25.setObjectName(u"verticalLayout_25")
        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents_7)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_26 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_26.setSpacing(6)
        self.verticalLayout_26.setObjectName(u"verticalLayout_26")
        self.verticalLayout_26.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_database = QLabel(self.groupBox_3)
        self.label_database.setObjectName(u"label_database")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_database.sizePolicy().hasHeightForWidth())
        self.label_database.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(8)
        self.label_database.setFont(font1)

        self.gridLayout_3.addWidget(self.label_database, 5, 0, 1, 1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.comboBox_dialect = QComboBox(self.groupBox_3)
        self.comboBox_dialect.setObjectName(u"comboBox_dialect")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comboBox_dialect.sizePolicy().hasHeightForWidth())
        self.comboBox_dialect.setSizePolicy(sizePolicy2)
        self.comboBox_dialect.setMinimumSize(QSize(0, 24))
        self.comboBox_dialect.setMaximumSize(QSize(16777215, 24))
        self.comboBox_dialect.setFont(font1)

        self.horizontalLayout_12.addWidget(self.comboBox_dialect)


        self.gridLayout_3.addLayout(self.horizontalLayout_12, 0, 2, 1, 2)

        self.comboBox_dsn = QComboBox(self.groupBox_3)
        self.comboBox_dsn.setObjectName(u"comboBox_dsn")
        self.comboBox_dsn.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.comboBox_dsn.sizePolicy().hasHeightForWidth())
        self.comboBox_dsn.setSizePolicy(sizePolicy2)
        self.comboBox_dsn.setMinimumSize(QSize(0, 24))
        self.comboBox_dsn.setMaximumSize(QSize(16777215, 24))
        self.comboBox_dsn.setFont(font1)

        self.gridLayout_3.addWidget(self.comboBox_dsn, 1, 2, 1, 2)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setSpacing(0)
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.lineEdit_database = CustomQLineEdit(self.groupBox_3)
        self.lineEdit_database.setObjectName(u"lineEdit_database")
        self.lineEdit_database.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.lineEdit_database.sizePolicy().hasHeightForWidth())
        self.lineEdit_database.setSizePolicy(sizePolicy2)
        self.lineEdit_database.setMinimumSize(QSize(0, 24))
        self.lineEdit_database.setMaximumSize(QSize(16777215, 24))
        self.lineEdit_database.setFont(font1)
        self.lineEdit_database.setCursor(QCursor(Qt.IBeamCursor))
        self.lineEdit_database.setClearButtonEnabled(True)

        self.horizontalLayout_24.addWidget(self.lineEdit_database)

        self.toolButton_open_sqlite_file = QToolButton(self.groupBox_3)
        self.toolButton_open_sqlite_file.setObjectName(u"toolButton_open_sqlite_file")
        self.toolButton_open_sqlite_file.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.toolButton_open_sqlite_file.sizePolicy().hasHeightForWidth())
        self.toolButton_open_sqlite_file.setSizePolicy(sizePolicy2)
        self.toolButton_open_sqlite_file.setMinimumSize(QSize(22, 22))
        self.toolButton_open_sqlite_file.setMaximumSize(QSize(22, 22))
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/folder-open-regular.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_open_sqlite_file.setIcon(icon)

        self.horizontalLayout_24.addWidget(self.toolButton_open_sqlite_file)


        self.gridLayout_3.addLayout(self.horizontalLayout_24, 5, 2, 1, 2)

        self.label_dialect = QLabel(self.groupBox_3)
        self.label_dialect.setObjectName(u"label_dialect")
        sizePolicy1.setHeightForWidth(self.label_dialect.sizePolicy().hasHeightForWidth())
        self.label_dialect.setSizePolicy(sizePolicy1)
        self.label_dialect.setMaximumSize(QSize(16777215, 16777215))
        self.label_dialect.setFont(font1)

        self.gridLayout_3.addWidget(self.label_dialect, 0, 0, 1, 1)

        self.label_dsn = QLabel(self.groupBox_3)
        self.label_dsn.setObjectName(u"label_dsn")
        sizePolicy1.setHeightForWidth(self.label_dsn.sizePolicy().hasHeightForWidth())
        self.label_dsn.setSizePolicy(sizePolicy1)
        self.label_dsn.setFont(font1)

        self.gridLayout_3.addWidget(self.label_dsn, 1, 0, 1, 1)

        self.lineEdit_username = PropertyQLineEdit(self.groupBox_3)
        self.lineEdit_username.setObjectName(u"lineEdit_username")
        self.lineEdit_username.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.lineEdit_username.sizePolicy().hasHeightForWidth())
        self.lineEdit_username.setSizePolicy(sizePolicy2)
        self.lineEdit_username.setMinimumSize(QSize(0, 24))
        self.lineEdit_username.setMaximumSize(QSize(5000, 24))
        self.lineEdit_username.setFont(font1)
        self.lineEdit_username.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.lineEdit_username, 2, 2, 1, 2)

        self.label_username = QLabel(self.groupBox_3)
        self.label_username.setObjectName(u"label_username")
        sizePolicy1.setHeightForWidth(self.label_username.sizePolicy().hasHeightForWidth())
        self.label_username.setSizePolicy(sizePolicy1)
        self.label_username.setFont(font1)

        self.gridLayout_3.addWidget(self.label_username, 2, 0, 1, 1)

        self.lineEdit_password = PropertyQLineEdit(self.groupBox_3)
        self.lineEdit_password.setObjectName(u"lineEdit_password")
        self.lineEdit_password.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.lineEdit_password.sizePolicy().hasHeightForWidth())
        self.lineEdit_password.setSizePolicy(sizePolicy2)
        self.lineEdit_password.setMinimumSize(QSize(0, 24))
        self.lineEdit_password.setMaximumSize(QSize(5000, 24))
        self.lineEdit_password.setFont(font1)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)
        self.lineEdit_password.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.lineEdit_password, 3, 2, 1, 2)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.lineEdit_host = PropertyQLineEdit(self.groupBox_3)
        self.lineEdit_host.setObjectName(u"lineEdit_host")
        self.lineEdit_host.setEnabled(False)
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(3)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_host.sizePolicy().hasHeightForWidth())
        self.lineEdit_host.setSizePolicy(sizePolicy3)
        self.lineEdit_host.setMinimumSize(QSize(0, 24))
        self.lineEdit_host.setMaximumSize(QSize(5000, 24))
        self.lineEdit_host.setFont(font1)
        self.lineEdit_host.setClearButtonEnabled(True)

        self.horizontalLayout_23.addWidget(self.lineEdit_host)

        self.label_port = QLabel(self.groupBox_3)
        self.label_port.setObjectName(u"label_port")
        sizePolicy4 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(1)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_port.sizePolicy().hasHeightForWidth())
        self.label_port.setSizePolicy(sizePolicy4)
        self.label_port.setFont(font1)

        self.horizontalLayout_23.addWidget(self.label_port)

        self.lineEdit_port = PropertyQLineEdit(self.groupBox_3)
        self.lineEdit_port.setObjectName(u"lineEdit_port")
        self.lineEdit_port.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.lineEdit_port.sizePolicy().hasHeightForWidth())
        self.lineEdit_port.setSizePolicy(sizePolicy2)
        self.lineEdit_port.setMinimumSize(QSize(0, 24))
        self.lineEdit_port.setMaximumSize(QSize(80, 24))
        self.lineEdit_port.setFont(font1)
        self.lineEdit_port.setInputMethodHints(Qt.ImhNone)

        self.horizontalLayout_23.addWidget(self.lineEdit_port)


        self.gridLayout_3.addLayout(self.horizontalLayout_23, 4, 2, 1, 2)

        self.label_password = QLabel(self.groupBox_3)
        self.label_password.setObjectName(u"label_password")
        sizePolicy1.setHeightForWidth(self.label_password.sizePolicy().hasHeightForWidth())
        self.label_password.setSizePolicy(sizePolicy1)
        self.label_password.setFont(font1)

        self.gridLayout_3.addWidget(self.label_password, 3, 0, 1, 1)

        self.label_host = QLabel(self.groupBox_3)
        self.label_host.setObjectName(u"label_host")
        sizePolicy1.setHeightForWidth(self.label_host.sizePolicy().hasHeightForWidth())
        self.label_host.setSizePolicy(sizePolicy1)
        self.label_host.setFont(font1)

        self.gridLayout_3.addWidget(self.label_host, 4, 0, 1, 1)


        self.verticalLayout_26.addLayout(self.gridLayout_3)


        self.verticalLayout_25.addWidget(self.groupBox_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_25.addItem(self.verticalSpacer_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_create_new_spine_db = QPushButton(self.scrollAreaWidgetContents_7)
        self.pushButton_create_new_spine_db.setObjectName(u"pushButton_create_new_spine_db")
        self.pushButton_create_new_spine_db.setMinimumSize(QSize(85, 23))
        self.pushButton_create_new_spine_db.setMaximumSize(QSize(16777215, 23))
        icon1 = QIcon()
        icon1.addFile(u":/symbols/Spine_symbol.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_create_new_spine_db.setIcon(icon1)

        self.horizontalLayout.addWidget(self.pushButton_create_new_spine_db)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_ds_open_editor = QPushButton(self.scrollAreaWidgetContents_7)
        self.pushButton_ds_open_editor.setObjectName(u"pushButton_ds_open_editor")
        sizePolicy5 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButton_ds_open_editor.sizePolicy().hasHeightForWidth())
        self.pushButton_ds_open_editor.setSizePolicy(sizePolicy5)
        self.pushButton_ds_open_editor.setMinimumSize(QSize(75, 23))
        self.pushButton_ds_open_editor.setMaximumSize(QSize(16777215, 23))

        self.horizontalLayout.addWidget(self.pushButton_ds_open_editor)


        self.verticalLayout_25.addLayout(self.horizontalLayout)

        self.line_8 = QFrame(self.scrollAreaWidgetContents_7)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_25.addWidget(self.line_8)

        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.toolButton_copy_url = QToolButton(self.scrollAreaWidgetContents_7)
        self.toolButton_copy_url.setObjectName(u"toolButton_copy_url")
        self.toolButton_copy_url.setMinimumSize(QSize(22, 22))
        self.toolButton_copy_url.setMaximumSize(QSize(22, 22))
        icon2 = QIcon()
        icon2.addFile(u":/icons/menu_icons/copy.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_copy_url.setIcon(icon2)

        self.horizontalLayout_27.addWidget(self.toolButton_copy_url)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_16)

        self.toolButton_ds_open_dir = QToolButton(self.scrollAreaWidgetContents_7)
        self.toolButton_ds_open_dir.setObjectName(u"toolButton_ds_open_dir")
        sizePolicy1.setHeightForWidth(self.toolButton_ds_open_dir.sizePolicy().hasHeightForWidth())
        self.toolButton_ds_open_dir.setSizePolicy(sizePolicy1)
        self.toolButton_ds_open_dir.setMinimumSize(QSize(22, 22))
        self.toolButton_ds_open_dir.setMaximumSize(QSize(22, 22))
        icon3 = QIcon()
        icon3.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_ds_open_dir.setIcon(icon3)

        self.horizontalLayout_27.addWidget(self.toolButton_ds_open_dir)


        self.verticalLayout_25.addLayout(self.horizontalLayout_27)

        self.scrollArea_5.setWidget(self.scrollAreaWidgetContents_7)

        self.verticalLayout.addWidget(self.scrollArea_5)

        QWidget.setTabOrder(self.scrollArea_5, self.comboBox_dialect)
        QWidget.setTabOrder(self.comboBox_dialect, self.comboBox_dsn)
        QWidget.setTabOrder(self.comboBox_dsn, self.lineEdit_username)
        QWidget.setTabOrder(self.lineEdit_username, self.lineEdit_password)
        QWidget.setTabOrder(self.lineEdit_password, self.lineEdit_host)
        QWidget.setTabOrder(self.lineEdit_host, self.lineEdit_port)
        QWidget.setTabOrder(self.lineEdit_port, self.lineEdit_database)
        QWidget.setTabOrder(self.lineEdit_database, self.toolButton_open_sqlite_file)
        QWidget.setTabOrder(self.toolButton_open_sqlite_file, self.pushButton_create_new_spine_db)
        QWidget.setTabOrder(self.pushButton_create_new_spine_db, self.pushButton_ds_open_editor)
        QWidget.setTabOrder(self.pushButton_ds_open_editor, self.toolButton_copy_url)
        QWidget.setTabOrder(self.toolButton_copy_url, self.toolButton_ds_open_dir)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_ds_name.setText(QCoreApplication.translate("Form", u"Name", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Form", u"URL", None))
        self.label_database.setText(QCoreApplication.translate("Form", u"Database", None))
        self.lineEdit_database.setPlaceholderText("")
#if QT_CONFIG(tooltip)
        self.toolButton_open_sqlite_file.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Open SQLite file.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_dialect.setText(QCoreApplication.translate("Form", u"Dialect", None))
        self.label_dsn.setText(QCoreApplication.translate("Form", u"DSN", None))
        self.lineEdit_username.setPlaceholderText("")
        self.label_username.setText(QCoreApplication.translate("Form", u"Username", None))
        self.lineEdit_password.setPlaceholderText("")
        self.lineEdit_host.setPlaceholderText("")
        self.label_port.setText(QCoreApplication.translate("Form", u"Port", None))
        self.lineEdit_port.setPlaceholderText("")
        self.label_password.setText(QCoreApplication.translate("Form", u"Password", None))
        self.label_host.setText(QCoreApplication.translate("Form", u"Host", None))
#if QT_CONFIG(tooltip)
        self.pushButton_create_new_spine_db.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Create new Spine database at the selected URL, or at a default one if the selected is not valid.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_create_new_spine_db.setText(QCoreApplication.translate("Form", u"New Spine db", None))
#if QT_CONFIG(tooltip)
        self.pushButton_ds_open_editor.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Open URL in Spine database editor</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_ds_open_editor.setText(QCoreApplication.translate("Form", u"Open editor", None))
#if QT_CONFIG(tooltip)
        self.toolButton_copy_url.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Copy current database url to clipboard.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_copy_url.setText(QCoreApplication.translate("Form", u"...", None))
#if QT_CONFIG(tooltip)
        self.toolButton_ds_open_dir.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Open this Data Store's project directory in file browser</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toolButton_ds_open_dir.setText("")
    # retranslateUi

