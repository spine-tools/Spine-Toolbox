#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
QWidget that is shown to user when adding Connection strings to a Data Store.

:author: Manuel Marin <manuelma@kth.se>
:date:   21.4.2018
"""

import os
from PySide2.QtWidgets import QWidget, QStatusBar
from PySide2.QtCore import Slot, Qt
from ui.add_db_reference import Ui_Form
from config import STATUSBAR_SS
from helpers import busy_effect
import logging
from sqlalchemy import create_engine
from config import DB_REF_REQUIRED_KEYS


class AddDbReferenceWidget(QWidget):
    """A widget to query user's input for a new connection string"""

    def __init__(self, parent, data_store):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            data_store (DataStore): A data store instance
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        self._data_store = data_store
        self.dialects = list()
        self.string_dict = dict()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.refresh_dialects()
        self.ui.comboBox_dialect.addItem("Select dialect...")
        self.ui.comboBox_dialect.addItems(self.dialects)
        self.ui.comboBox_dialect.setFocus()
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @busy_effect
    @Slot(name="refresh_dialects")
    def refresh_dialects(self):
        """Find out which dialects are possible and populate the list"""
        # TODO: explore whether is there a better way to do this
        self.dialects[:] = []
        try:
            create_engine('mysql://username:password@host/database')
            self.dialects.append("mysql")
        except:
            pass
        try:
            create_engine('sqlite://')
            self.dialects.append("sqlite")
        except:
            pass
        try:
            create_engine('postgresql://username:password@host/database')
            self.dialects.append("postgresql")
        except:
            pass

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Check that everything is valid, create string and add it to data store."""
        answer = dict()
        if self.ui.comboBox_dialect.currentIndex() > 0:
            answer['dialect'] = self.ui.comboBox_dialect.currentText()
        else:
            answer['dialect'] = None
        answer['host'] = self.ui.lineEdit_host.text()
        answer['port'] = self.ui.lineEdit_port.text()
        answer['database'] = self.ui.lineEdit_database.text()
        answer['username'] = self.ui.lineEdit_username.text()
        answer['password'] = self.ui.lineEdit_password.text()
        for k in DB_REF_REQUIRED_KEYS:
            if not answer[k]:
                self.statusbar.showMessage("{} missing".format(k), 3000)
                return
        url = answer['dialect'] + "://"
        if answer['username']:
            url += answer['username']
        if answer['password']:
            url += ":" + answer['password']
        if answer['host']:
            url += "@" + answer['host']
        if answer['port']:
            url += ":" + answer['port']
        if answer['database']:
            url += "/" + answer['database']
        engine = create_engine(url)
        try:
            engine.connect()
        except Exception as e:
            self.statusbar.showMessage("Connection failed: {}".format(e))
            return
        reference = {
            'database': answer['database'],
            'username': answer['username'],
            'url': url
        }
        self._data_store.add_reference(reference)
        self.close()

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
