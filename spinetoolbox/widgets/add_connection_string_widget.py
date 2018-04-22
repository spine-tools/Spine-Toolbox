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
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget, QStatusBar
from PySide2.QtCore import Slot, Qt
from ui.add_connection_string import Ui_Form
from config import STATUSBAR_SS, APPLICATION_PATH
from helpers import custom_getopenfilename
import logging
import pyodbc
from config import CS_REQUIRED_KEYS


class AddConnectionStringWidget(QWidget):
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
        self.string_dict = dict()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.comboBox_dsn.addItem("Select data source name...")
        self.data_sources = pyodbc.dataSources() # this is a dict
        self.ui.comboBox_dsn.addItems(list(self.data_sources.keys()))
        self.ui.comboBox_dsn.setFocus()
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_browse.clicked.connect(self.select_driver_file)
        self.ui.comboBox_dsn.currentIndexChanged.connect(self.unpack_dsn)
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot("int", name="unpack_dsn")
    def unpack_dsn(self, row):
        """Whenever a new dsn is selected, populate form with data from it"""
        if row == 0: # Dummy entry 'Select data source name...' is selected
            return
        dsn = self.ui.comboBox_dsn.currentText()
        driver = self.data_sources[dsn]
        self.ui.lineEdit_driver.setText(driver)
        try:
            cnxn = pyodbc.connect(DSN=dsn, autocommit=True, timeout=3)
        except pyodbc.OperationalError:
            self.statusbar.showMessage("Unable to connect to {}".format(dsn), 3000)
            return
        server_name = cnxn.getinfo(pyodbc.SQL_SERVER_NAME)
        database_name = cnxn.getinfo(pyodbc.SQL_DATABASE_NAME)
        username = cnxn.getinfo(pyodbc.SQL_USER_NAME)
        self.ui.lineEdit_server.setText(server_name)
        self.ui.lineEdit_database.setText(database_name)
        self.ui.lineEdit_username.setText(username)

    @Slot(name="select_driver_file")
    def select_driver_file(self):
        """Let user select a driver file from computer."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        path = APPLICATION_PATH # TODO: make it a more relevant path
        answer = custom_getopenfilename(self._parent.ui.graphicsView, self, "Select driver file", path, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.ui.lineEdit_driver.setText(file_path)

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Check that everything is valid, create string and add it to data store."""
        if self.ui.comboBox_dsn.currentIndex() > 0:
            self.string_dict['DSN'] = self.ui.comboBox_dsn.currentText()
        self.string_dict['DRIVER'] = self.ui.lineEdit_driver.text()
        self.string_dict['SERVER'] = self.ui.lineEdit_server.text()
        self.string_dict['DATABASE'] = self.ui.lineEdit_database.text()
        self.string_dict['UID'] = self.ui.lineEdit_username.text()
        self.string_dict['PWD'] = self.ui.lineEdit_password.text()
        for k in CS_REQUIRED_KEYS:
            if not self.string_dict[k]:
                self.statusbar.showMessage("{} missing".format(k.capitalize()), 3000)
                return
        connection_string = '; '.join("{!s}={!s}".format(k,v) for (k,v) in self.string_dict.items() if v)
        try:
            cnxn = pyodbc.connect(connection_string, autocommit=True, timeout=3)
        except:
            self.statusbar.showMessage("Connection failed.")
            return
        self._data_store.add_reference(connection_string)
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
