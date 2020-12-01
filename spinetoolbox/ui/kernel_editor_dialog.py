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
## Form generated from reading UI file 'kernel_editor_dialog.ui'
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

from spinetoolbox import resources_icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(824, 625)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.tableView_kernel_list = QTableView(self.splitter)
        self.tableView_kernel_list.setObjectName(u"tableView_kernel_list")
        self.tableView_kernel_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_kernel_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView_kernel_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView_kernel_list.setShowGrid(True)
        self.tableView_kernel_list.setCornerButtonEnabled(False)
        self.splitter.addWidget(self.tableView_kernel_list)
        self.tableView_kernel_list.horizontalHeader().setMinimumSectionSize(30)
        self.tableView_kernel_list.horizontalHeader().setDefaultSectionSize(100)
        self.tableView_kernel_list.horizontalHeader().setStretchLastSection(True)
        self.tableView_kernel_list.verticalHeader().setMinimumSectionSize(20)
        self.tableView_kernel_list.verticalHeader().setDefaultSectionSize(32)
        self.stackedWidget = QStackedWidget(self.splitter)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidgetPage1 = QWidget()
        self.stackedWidgetPage1.setObjectName(u"stackedWidgetPage1")
        self.gridLayout_2 = QGridLayout(self.stackedWidgetPage1)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_8 = QLabel(self.stackedWidgetPage1)
        self.label_8.setObjectName(u"label_8")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy)
        self.label_8.setMinimumSize(QSize(0, 26))
        self.label_8.setMaximumSize(QSize(16777215, 26))

        self.gridLayout_2.addWidget(self.label_8, 0, 0, 1, 2)

        self.label_3 = QLabel(self.stackedWidgetPage1)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 1, 0, 1, 1)

        self.lineEdit_python_interpreter = QLineEdit(self.stackedWidgetPage1)
        self.lineEdit_python_interpreter.setObjectName(u"lineEdit_python_interpreter")
        self.lineEdit_python_interpreter.setEnabled(True)
        self.lineEdit_python_interpreter.setCursor(QCursor(Qt.IBeamCursor))
        self.lineEdit_python_interpreter.setFocusPolicy(Qt.StrongFocus)
        self.lineEdit_python_interpreter.setReadOnly(False)
        self.lineEdit_python_interpreter.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_python_interpreter, 1, 1, 1, 1)

        self.toolButton_select_python = QToolButton(self.stackedWidgetPage1)
        self.toolButton_select_python.setObjectName(u"toolButton_select_python")
        icon = QIcon()
        icon.addFile(u":/icons/menu_icons/folder-open-solid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButton_select_python.setIcon(icon)

        self.gridLayout_2.addWidget(self.toolButton_select_python, 1, 2, 1, 1)

        self.label_2 = QLabel(self.stackedWidgetPage1)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 2, 0, 1, 1)

        self.lineEdit_python_kernel_name = QLineEdit(self.stackedWidgetPage1)
        self.lineEdit_python_kernel_name.setObjectName(u"lineEdit_python_kernel_name")
        self.lineEdit_python_kernel_name.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_python_kernel_name, 2, 1, 1, 1)

        self.label_5 = QLabel(self.stackedWidgetPage1)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setMinimumSize(QSize(0, 26))
        self.label_5.setMaximumSize(QSize(16777215, 26))

        self.gridLayout_2.addWidget(self.label_5, 3, 0, 1, 1)

        self.lineEdit_python_kernel_display_name = QLineEdit(self.stackedWidgetPage1)
        self.lineEdit_python_kernel_display_name.setObjectName(u"lineEdit_python_kernel_display_name")
        self.lineEdit_python_kernel_display_name.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_python_kernel_display_name, 3, 1, 1, 1)

        self.label_python_cmd = QLabel(self.stackedWidgetPage1)
        self.label_python_cmd.setObjectName(u"label_python_cmd")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_python_cmd.sizePolicy().hasHeightForWidth())
        self.label_python_cmd.setSizePolicy(sizePolicy1)
        self.label_python_cmd.setMinimumSize(QSize(0, 26))
        self.label_python_cmd.setMaximumSize(QSize(16777215, 26))
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(False)
        font.setUnderline(True)
        font.setWeight(50)
        self.label_python_cmd.setFont(font)
        self.label_python_cmd.setToolTipDuration(-1)
        self.label_python_cmd.setStyleSheet(u"color: rgb(0, 0, 255);")
        self.label_python_cmd.setTextFormat(Qt.AutoText)
        self.label_python_cmd.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_python_cmd, 4, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_make_python_kernel = QPushButton(self.stackedWidgetPage1)
        self.pushButton_make_python_kernel.setObjectName(u"pushButton_make_python_kernel")

        self.horizontalLayout.addWidget(self.pushButton_make_python_kernel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout_2.addLayout(self.horizontalLayout, 5, 0, 1, 2)

        self.stackedWidget.addWidget(self.stackedWidgetPage1)
        self.stackedWidgetPage2 = QWidget()
        self.stackedWidgetPage2.setObjectName(u"stackedWidgetPage2")
        self.gridLayout_3 = QGridLayout(self.stackedWidgetPage2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_4 = QLabel(self.stackedWidgetPage2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(0, 26))
        self.label_4.setMaximumSize(QSize(16777215, 26))

        self.gridLayout_3.addWidget(self.label_4, 0, 0, 1, 2)

        self.label_6 = QLabel(self.stackedWidgetPage2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_3.addWidget(self.label_6, 1, 0, 1, 1)

        self.lineEdit_julia_executable = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_executable.setObjectName(u"lineEdit_julia_executable")
        self.lineEdit_julia_executable.setFocusPolicy(Qt.StrongFocus)
        self.lineEdit_julia_executable.setFrame(True)
        self.lineEdit_julia_executable.setReadOnly(False)
        self.lineEdit_julia_executable.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.lineEdit_julia_executable, 1, 1, 1, 1)

        self.toolButton_select_julia = QToolButton(self.stackedWidgetPage2)
        self.toolButton_select_julia.setObjectName(u"toolButton_select_julia")
        self.toolButton_select_julia.setIcon(icon)

        self.gridLayout_3.addWidget(self.toolButton_select_julia, 1, 2, 1, 1)

        self.label_7 = QLabel(self.stackedWidgetPage2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMinimumSize(QSize(0, 26))
        self.label_7.setMaximumSize(QSize(16777215, 26))

        self.gridLayout_3.addWidget(self.label_7, 2, 0, 1, 1)

        self.lineEdit_julia_kernel_name = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_kernel_name.setObjectName(u"lineEdit_julia_kernel_name")
        self.lineEdit_julia_kernel_name.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.lineEdit_julia_kernel_name, 2, 1, 1, 1)

        self.label_9 = QLabel(self.stackedWidgetPage2)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_3.addWidget(self.label_9, 3, 0, 1, 1)

        self.lineEdit_julia_project = QLineEdit(self.stackedWidgetPage2)
        self.lineEdit_julia_project.setObjectName(u"lineEdit_julia_project")
        self.lineEdit_julia_project.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.lineEdit_julia_project, 3, 1, 1, 1)

        self.toolButton_select_julia_project = QToolButton(self.stackedWidgetPage2)
        self.toolButton_select_julia_project.setObjectName(u"toolButton_select_julia_project")
        self.toolButton_select_julia_project.setIcon(icon)

        self.gridLayout_3.addWidget(self.toolButton_select_julia_project, 3, 2, 1, 1)

        self.checkBox_rebuild_ijulia = QCheckBox(self.stackedWidgetPage2)
        self.checkBox_rebuild_ijulia.setObjectName(u"checkBox_rebuild_ijulia")
        self.checkBox_rebuild_ijulia.setMinimumSize(QSize(0, 26))
        self.checkBox_rebuild_ijulia.setMaximumSize(QSize(16777215, 26))
        self.checkBox_rebuild_ijulia.setChecked(True)

        self.gridLayout_3.addWidget(self.checkBox_rebuild_ijulia, 4, 0, 1, 1)

        self.label_julia_cmd = QLabel(self.stackedWidgetPage2)
        self.label_julia_cmd.setObjectName(u"label_julia_cmd")
        self.label_julia_cmd.setMinimumSize(QSize(0, 26))
        self.label_julia_cmd.setMaximumSize(QSize(16777215, 26))
        font1 = QFont()
        font1.setPointSize(9)
        font1.setUnderline(True)
        self.label_julia_cmd.setFont(font1)
        self.label_julia_cmd.setMouseTracking(True)
        self.label_julia_cmd.setStyleSheet(u"color: rgb(0, 0, 255);")

        self.gridLayout_3.addWidget(self.label_julia_cmd, 5, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_make_julia_kernel = QPushButton(self.stackedWidgetPage2)
        self.pushButton_make_julia_kernel.setObjectName(u"pushButton_make_julia_kernel")

        self.horizontalLayout_2.addWidget(self.pushButton_make_julia_kernel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 6, 0, 1, 2)

        self.stackedWidget.addWidget(self.stackedWidgetPage2)
        self.splitter.addWidget(self.stackedWidget)

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)

        self.textBrowser_process = QTextBrowser(Dialog)
        self.textBrowser_process.setObjectName(u"textBrowser_process")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.textBrowser_process.sizePolicy().hasHeightForWidth())
        self.textBrowser_process.setSizePolicy(sizePolicy2)
        self.textBrowser_process.setMaximumSize(QSize(16777215, 120))

        self.gridLayout.addWidget(self.textBrowser_process, 2, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        font2 = QFont()
        font2.setItalic(True)
        font2.setStrikeOut(False)
        self.label.setFont(font2)
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        QWidget.setTabOrder(self.tableView_kernel_list, self.lineEdit_python_interpreter)
        QWidget.setTabOrder(self.lineEdit_python_interpreter, self.toolButton_select_python)
        QWidget.setTabOrder(self.toolButton_select_python, self.lineEdit_python_kernel_name)
        QWidget.setTabOrder(self.lineEdit_python_kernel_name, self.lineEdit_python_kernel_display_name)
        QWidget.setTabOrder(self.lineEdit_python_kernel_display_name, self.pushButton_make_python_kernel)
        QWidget.setTabOrder(self.pushButton_make_python_kernel, self.lineEdit_julia_executable)
        QWidget.setTabOrder(self.lineEdit_julia_executable, self.toolButton_select_julia)
        QWidget.setTabOrder(self.toolButton_select_julia, self.lineEdit_julia_kernel_name)
        QWidget.setTabOrder(self.lineEdit_julia_kernel_name, self.lineEdit_julia_project)
        QWidget.setTabOrder(self.lineEdit_julia_project, self.toolButton_select_julia_project)
        QWidget.setTabOrder(self.toolButton_select_julia_project, self.checkBox_rebuild_ijulia)
        QWidget.setTabOrder(self.checkBox_rebuild_ijulia, self.pushButton_make_julia_kernel)
        QWidget.setTabOrder(self.pushButton_make_julia_kernel, self.textBrowser_process)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Kernel specification editor", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Make new Python kernel specs", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Interpeter", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_interpreter.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Python interpreter for the new kernel. </p><p>Use the browse button to select a different Python.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_interpreter.setPlaceholderText(QCoreApplication.translate("Dialog", u"Python interpreter for the new kernel", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Name", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_kernel_name.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>New kernel name. e.g. Python-3.7</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_kernel_name.setPlaceholderText(QCoreApplication.translate("Dialog", u"Type kernel name here...", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Display name", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_python_kernel_display_name.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Kernel display name. e.g. Python-3.7_spinetoolbox</p><p>Leave blank to use default (kernel name + &quot;_spinetoolbox&quot;)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_python_kernel_display_name.setPlaceholderText(QCoreApplication.translate("Dialog", u"Type kernel display name here...", None))
        self.label_python_cmd.setText(QCoreApplication.translate("Dialog", u"Command", None))
#if QT_CONFIG(tooltip)
        self.pushButton_make_python_kernel.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Creates a new Python kernel according to selections</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_make_python_kernel.setText(QCoreApplication.translate("Dialog", u"Make kernel specification", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Make new Julia kernel specs", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Executable", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_executable.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Julia executable for the new kernel.</p><p>Use the browse button to select different Julia.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_executable.setPlaceholderText(QCoreApplication.translate("Dialog", u"Julia executable for the new kernel", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"Display name", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_kernel_name.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Julia kernel display name. Julia version will be appended to the name automatically.</p><p>The kernel name will be stripped of whitespace and uncapitalized automatically.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_kernel_name.setText("")
        self.lineEdit_julia_kernel_name.setPlaceholderText(QCoreApplication.translate("Dialog", u"Type kernel display name here...", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Project", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_julia_project.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Julia project for the new kernel</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_julia_project.setPlaceholderText(QCoreApplication.translate("Dialog", u"@.", None))
        self.toolButton_select_julia_project.setText("")
#if QT_CONFIG(tooltip)
        self.checkBox_rebuild_ijulia.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Rebuilds IJulia before installing kernel</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox_rebuild_ijulia.setText(QCoreApplication.translate("Dialog", u"Rebuild IJulia", None))
        self.label_julia_cmd.setText(QCoreApplication.translate("Dialog", u"Command", None))
#if QT_CONFIG(tooltip)
        self.pushButton_make_julia_kernel.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Creates a new Julia kernel according to selections</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pushButton_make_julia_kernel.setText(QCoreApplication.translate("Dialog", u"Make kernel specification", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Kernel specifications", None))
    # retranslateUi

