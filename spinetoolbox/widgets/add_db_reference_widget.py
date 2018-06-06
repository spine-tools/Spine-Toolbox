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
import getpass
import logging
from PySide2.QtWidgets import QWidget, QStatusBar, QMessageBox, QFileDialog
from PySide2.QtCore import Slot, Qt
from ui.add_db_reference import Ui_Form
from config import STATUSBAR_SS
from helpers import busy_effect, blocking_updates
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from config import SQL_DIALECT_API, APPLICATION_PATH
# import conda.cli
import qsubprocess


class AddDbReferenceWidget(QWidget):
    """A widget to query user's input for a new connection string"""

    def __init__(self, parent, data_store):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            data_store (DataStore): A data store instance
        """
        super().__init__(f=Qt.Window)
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        self._data_store = data_store
        self.dialects = list(SQL_DIALECT_API.keys())
        self.string_dict = dict()
        self.pip_install = None # pip install process (QSubProcess)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        # self.refresh_dialects()
        self.ui.comboBox_dialect.addItem("Select dialect...")
        self.ui.comboBox_dsn.addItem("Select ODBC DSN...")
        self.ui.comboBox_dialect.addItems(self.dialects)
        self.ui.comboBox_dialect.setFocus()
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        self.ui.pushButton_browse.clicked.connect(self.browse_clicked)
        self.ui.comboBox_dialect.currentTextChanged.connect(self.check_dialect)


    @Slot(name='browse_clicked')
    def browse_clicked(self):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        func = blocking_updates(self._parent.ui.graphicsView, QFileDialog.getOpenFileName)
        answer = func(self, 'Select SQlite file', APPLICATION_PATH, 'SQLite (*.*)')
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.ui.lineEdit_SQLite_file.setText(file_path)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self.ui.comboBox_dsn.setEnabled(True)
        self.ui.lineEdit_SQLite_file.setEnabled(False)
        self.ui.pushButton_browse.setEnabled(False)
        self.ui.lineEdit_host.setEnabled(False)
        self.ui.lineEdit_port.setEnabled(False)
        self.ui.lineEdit_database.setEnabled(False)
        self.ui.lineEdit_username.setEnabled(True)
        self.ui.lineEdit_password.setEnabled(True)
        self.ui.comboBox_dsn.setFocus()

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self.ui.comboBox_dsn.setEnabled(False)
        self.ui.comboBox_dsn.setCurrentIndex(0)
        self.ui.lineEdit_SQLite_file.setEnabled(True)
        self.ui.pushButton_browse.setEnabled(True)
        self.ui.lineEdit_host.setEnabled(False)
        self.ui.lineEdit_port.setEnabled(False)
        self.ui.lineEdit_database.setEnabled(False)
        self.ui.lineEdit_username.setEnabled(False)
        self.ui.lineEdit_password.setEnabled(False)
        self.ui.lineEdit_SQLite_file.setFocus()

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self.ui.comboBox_dsn.setEnabled(False)
        self.ui.comboBox_dsn.setCurrentIndex(0)
        self.ui.lineEdit_SQLite_file.setEnabled(False)
        self.ui.pushButton_browse.setEnabled(False)
        self.ui.lineEdit_host.setEnabled(True)
        self.ui.lineEdit_port.setEnabled(True)
        self.ui.lineEdit_database.setEnabled(True)
        self.ui.lineEdit_username.setEnabled(True)
        self.ui.lineEdit_password.setEnabled(True)
        self.ui.lineEdit_host.setFocus()

    @Slot("str", name="check_dialect")
    def check_dialect(self, dialect):
        """Check if selected dialect is supported. Offer to install DBAPI if not.

        Returns:
            True if dialect is supported, False if not.
        """
        if dialect == 'Select dialect...':
            return
        try:
            if dialect == 'sqlite':
                create_engine('sqlite://')
                self.enable_sqlite()
            elif dialect == 'mssql':
                import pyodbc
                dsns = pyodbc.dataSources()
                mssql_dsns = list()
                for k, v in dsns.items():
                    if 'msodbcsql' in v.lower():
                        mssql_dsns.append(k)
                if mssql_dsns:
                    self.ui.comboBox_dsn.addItems(mssql_dsns)
                    self.enable_mssql()
                else:
                    msg = "Please create a SQL Server ODBC Data Source first."
                    self.statusbar.showMessage(msg)
            else:
                self.enable_common()
                create_engine('{}://username:password@host/database'.format(dialect))
            return True
        except ModuleNotFoundError:
            dbapi = SQL_DIALECT_API[dialect]
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Dialect not supported")
            msg.setText("There is no DBAPI installed for dialect '{0}'. "
                        "The default one is '{1}'.".format(dialect, dbapi))
            msg.setInformativeText("Do you want to install it using pip or conda?")
            pip_button = msg.addButton("pip", QMessageBox.YesRole)
            conda_button = msg.addButton("conda", QMessageBox.NoRole)
            cancel_button = msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()  # Show message box
            if msg.clickedButton() == pip_button:
                if not self.install_dbapi_pip(dbapi):
                    self.ui.comboBox_dialect.setCurrentIndex(0)
                    return False
            elif msg.clickedButton() == conda_button:
                if not self.install_dbapi_conda(dbapi):
                    self.ui.comboBox_dialect.setCurrentIndex(0)
                    return False
            else:
                self.ui.comboBox_dialect.setCurrentIndex(0)
                logging.debug("Cancelled")
                msg = "Unable to use dialect '{}'.".format(dialect)
                self.statusbar.showMessage(msg, 3000)
                return False
            # Check that dialect is not found
            logging.debug("Checking dialect again")
            if not self.check_dialect(dialect):
                self.ui.comboBox_dialect.setCurrentIndex(0)

    @busy_effect
    def install_dbapi_pip(self, dbapi):
        """Install DBAPI using pip."""
        msg = "Installing module '{}' via 'pip'.".format(dbapi)
        self.statusbar.showMessage(msg)
        command = 'pip install {0}'.format(dbapi)
        self.pip_install = qsubprocess.QSubProcess(self._parent, command)
        self.pip_install.start_process()
        if self.pip_install.wait_for_finished():
            msg = "Module '{}' successfully installed via 'pip'.".format(dbapi)
            self.statusbar.showMessage(msg, 3000)
            logging.debug("pip installation succeeded")
            return True
        logging.error("Failed to install module '{}' with pip.".format(dbapi))
        msg = "Failed to install module '{}' with pip.".format(dbapi)
        self.statusbar.showMessage(msg, 3000)
        return False

    @busy_effect
    def install_dbapi_conda(self, dbapi):
        """Install DBAPI using conda. Fails if conda is not installed."""
        try:
            import conda.cli
        except ImportError:
            logging.debug("Could not find conda. Installing {0} failed.".format(dbapi))
            msg = "Conda is missing"
            self.statusbar.showMessage(msg, 3000)
            self.ui.comboBox_dialect.setCurrentIndex(0)
            return False
        try:
            msg = "Installing module '{}' via 'conda'.".format(dbapi)
            self.statusbar.showMessage(msg)
            conda.cli.main('conda', 'install',  '-y', dbapi)
            msg = "Module '{}' successfully installed via 'conda'.".format(dbapi)
            self.statusbar.showMessage(msg, 3000)
            logging.debug("conda installation succeeded")
            return True
        except Exception as e:
            logging.exception(e)
            logging.error("Failed to install module '{}' with conda.".format(dbapi))
            msg = "Failed to install module '{}' with conda.".format(dbapi)
            self.statusbar.showMessage(msg, 3000)
            self.ui.comboBox_dialect.setCurrentIndex(0)
            return False

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Check that everything is valid, create string and add it to data store."""
        answer = dict()
        # Check that dialect is selected
        if self.ui.comboBox_dialect.currentIndex() == 0:
            self.statusbar.showMessage("Please select dialect first", 3000)
            return
        dialect = self.ui.comboBox_dialect.currentText()
        if dialect == 'mssql':
            if self.ui.comboBox_dsn.currentIndex() == 0:
                self.statusbar.showMessage("Please select DSN first", 3000)
                return
            dsn = self.ui.comboBox_dsn.currentText()
            username = self.ui.lineEdit_username.text()
            password = self.ui.lineEdit_password.text()
            url = 'mssql+pyodbc://'
            if username:
                url += username
            if password:
                url += ":" + password
            url += '@' + dsn
            # Set database equal to dsn for creating the reference below
            database = dsn
        elif dialect == 'sqlite':
            sqlite_file = self.ui.lineEdit_SQLite_file.text()
            url = 'sqlite:///{0}'.format(sqlite_file)
            # Set database equal to file's basename for creating the reference below
            database = os.path.basename(sqlite_file)
            username = getpass.getuser()
        else:
            host = self.ui.lineEdit_host.text()
            if not host:
                self.statusbar.showMessage("Host missing")
                return
            database = self.ui.lineEdit_database.text()
            if not database:
                self.statusbar.showMessage("Database missing")
                return
            port = self.ui.lineEdit_port.text()
            username = self.ui.lineEdit_username.text()
            password = self.ui.lineEdit_password.text()
            url = dialect + "://"
            if username:
                url += username
            if password:
                url += ":" + password
            url += "@" + host
            if port:
                url += ":" + port
            url += "/" + database
        engine = create_engine(url)
        try:
            engine.connect()
        except SQLAlchemyError as e:
            self.statusbar.showMessage("Connection failed: {}".format(e.orig.args))
            return
        if dialect == 'sqlite':
            # check if SQLite database
            try:
                engine.execute('pragma quick_check;')
            except DatabaseError as e:
                self.statusbar.showMessage("Could not open {} as SQLite database: {}".format(database, e.orig.args))
                return
        # Get system's username if none given
        if not username:
            username = getpass.getuser()
        reference = {
            'database': database,
            'username': username,
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
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.ok_clicked()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
