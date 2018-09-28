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
Module for data store class.

:author: P. Savolainen (VTT)
:date:   18.12.2017
"""

import os
import getpass
import logging
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, Qt
from PySide2.QtWidgets import QInputDialog, QMessageBox, QFileDialog, QFileIconProvider
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from spinedatabase_api import DiffDatabaseMapping, SpineDBAPIError, create_new_spine_database
from widgets.data_store_subwindow_widget import DataStoreWidget
from widgets.data_store_widget import DataStoreForm
from metaobject import MetaObject
from config import SQL_DIALECT_API
from graphics_items import DataStoreImage
from helpers import create_dir, busy_effect
import qsubprocess


class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        reference (dict): Reference to a database
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, reference, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._widget = DataStoreWidget(self, self.item_type)
        self._widget.set_name_label(name)
        self._widget.ui.comboBox_dialect.addItems(list(SQL_DIALECT_API.keys()))
        self._widget.ui.comboBox_dialect.setCurrentIndex(-1)
        # self._widget.ui.toolButton_browse.setIcon(self._widget.style().standardIcon(QStyle.SP_DialogOpenButton))
        icon_provider = QFileIconProvider()
        self._widget.ui.toolButton_browse.setIcon(icon_provider.icon(QFileIconProvider.Folder))
        # Make directory for Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                         " Check permissions.".format(self.data_dir))
        self._graphics_item = DataStoreImage(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self.connect_signals()
        self.load_reference(reference)
        # TODO: try and create reference from first sqlite file in data directory

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open_directory.clicked.connect(self.open_directory)
        self._widget.ui.pushButton_open_treeview.clicked.connect(self.open_treeview)
        self._widget.ui.toolButton_browse.clicked.connect(self.browse_clicked)
        self._widget.ui.comboBox_dialect.currentTextChanged.connect(self.check_dialect)
        self._widget.ui.toolButton_spine.clicked.connect(self.create_new_spine_database)

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    @Slot(name='browse_clicked')
    def browse_clicked(self):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, 'Select SQlite file', self.data_dir, 'SQLite (*.*)')
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self._widget.ui.lineEdit_SQLite_file.setText(file_path)

    def load_reference(self, reference):
        """Update ui so it reflects the stored reference after loading a project."""
        # TODO: now it only handles SQLite references, but should handle all types of reference
        if not reference:
            return
        # Keep compatibility with previous versions where reference was a list
        if isinstance(reference, list):
            reference = reference[0]
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        try:
            dialect_dbapi = db_url.split('://')[0]
        except IndexError:
            self._toolbox.msg_error.emit("Unable to parse stored reference. Please select a new reference.")
            return
        try:
            dialect, dbapi = dialect_dbapi.split('+')
        except ValueError:
            dialect = dialect_dbapi
            dbapi = None
        if dialect not in SQL_DIALECT_API:
            self._toolbox.msg_error.emit("Dialect '{}' of stored reference is not supported.".format(dialect))
            return
        self._widget.ui.comboBox_dialect.setCurrentText(dialect)
        if dbapi and SQL_DIALECT_API[dialect] != dbapi:
            recommended_dbapi = SQL_DIALECT_API[dialect]
            self._toolbox.msg_warning.emit("The stored reference is using dialect '{0}' with driver '{1}', whereas "
                                           "'{2}' is the recommended.".format(dialect, dbapi, recommended_dbapi))
        if dialect == 'sqlite':
            try:
                file_path = db_url.split(':///')[1]
            except IndexError:
                self._toolbox.msg_warning.emit("Unable to determine path of stored SQLite reference. "
                                               "Please select a new one.")
            self._widget.ui.lineEdit_SQLite_file.setText(os.path.abspath(file_path))
            self._widget.ui.lineEdit_database.setText(database)
            self._widget.ui.lineEdit_username.setText(username)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self._widget.ui.comboBox_dsn.setEnabled(True)
        self._widget.ui.lineEdit_SQLite_file.setEnabled(False)
        self._widget.ui.toolButton_browse.setEnabled(False)
        self._widget.ui.lineEdit_host.setEnabled(False)
        self._widget.ui.lineEdit_port.setEnabled(False)
        self._widget.ui.lineEdit_database.setEnabled(False)
        self._widget.ui.lineEdit_username.setEnabled(True)
        self._widget.ui.lineEdit_password.setEnabled(True)
        self._widget.ui.comboBox_dsn.setFocus()

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self._widget.ui.comboBox_dsn.setEnabled(False)
        self._widget.ui.comboBox_dsn.setCurrentIndex(0)
        self._widget.ui.lineEdit_SQLite_file.setEnabled(True)
        self._widget.ui.toolButton_browse.setEnabled(True)
        self._widget.ui.lineEdit_host.setEnabled(False)
        self._widget.ui.lineEdit_port.setEnabled(False)
        self._widget.ui.lineEdit_database.setEnabled(False)
        self._widget.ui.lineEdit_username.setEnabled(False)
        self._widget.ui.lineEdit_password.setEnabled(False)
        self._widget.ui.lineEdit_SQLite_file.setFocus()

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self._widget.ui.comboBox_dsn.setEnabled(False)
        self._widget.ui.comboBox_dsn.setCurrentIndex(0)
        self._widget.ui.lineEdit_SQLite_file.setEnabled(False)
        self._widget.ui.toolButton_browse.setEnabled(False)
        self._widget.ui.lineEdit_host.setEnabled(True)
        self._widget.ui.lineEdit_port.setEnabled(True)
        self._widget.ui.lineEdit_database.setEnabled(True)
        self._widget.ui.lineEdit_username.setEnabled(True)
        self._widget.ui.lineEdit_password.setEnabled(True)
        self._widget.ui.lineEdit_host.setFocus()

    @Slot("str", name="check_dialect")
    def check_dialect(self, dialect):
        """Check if selected dialect is supported. Offer to install DBAPI if not.

        Returns:
            True if dialect is supported, False if not.
        """
        if dialect == 'Select dialect...':
            return
        dbapi = SQL_DIALECT_API[dialect]
        try:
            if dialect == 'sqlite':
                create_engine('sqlite://')
                self.enable_sqlite()
            elif dialect == 'mssql':
                import pyodbc
                dsns = pyodbc.dataSources()
                # Collect dsns which use the msodbcsql driver
                mssql_dsns = list()
                for key, value in dsns.items():
                    if 'msodbcsql' in value.lower():
                        mssql_dsns.append(key)
                if mssql_dsns:
                    self._widget.ui.comboBox_dsn.clear()
                    self._widget.ui.comboBox_dsn.addItems(mssql_dsns)
                    self._widget.ui.comboBox_dsn.setCurrentIndex(-1)
                    self.enable_mssql()
                else:
                    msg = "Please create a SQL Server ODBC Data Source first."
                    self._toolbox.msg_warning.emit(msg)
            else:
                create_engine('{}://username:password@host/database'.format("+".join([dialect, dbapi])))
                self.enable_common()
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
                    self._widget.ui.comboBox_dialect.setCurrentIndex(0)
                    return False
            elif msg.clickedButton() == conda_button:
                if not self.install_dbapi_conda(dbapi):
                    self._widget.ui.comboBox_dialect.setCurrentIndex(0)
                    return False
            else:
                self._widget.ui.comboBox_dialect.setCurrentIndex(0)
                logging.debug("Cancelled")
                msg = "Unable to use dialect '{}'.".format(dialect)
                self._toolbox.msg_error.emit(msg)
                return False
            # Check that dialect is not found
            logging.debug("Checking dialect again")
            if not self.check_dialect(dialect):
                self._widget.ui.comboBox_dialect.setCurrentIndex(0)

    @busy_effect
    def install_dbapi_pip(self, dbapi):
        """Install DBAPI using pip."""
        self._toolbox.msg.emit("Installing module <b>{0}</b> using pip".format(dbapi))
        program = "pip"
        args = list()
        args.append("install")
        args.append("{0}".format(dbapi))
        pip_install = qsubprocess.QSubProcess(self._toolbox, program, args)
        pip_install.start_process()
        if pip_install.wait_for_finished():
            self._toolbox.msg_success.emit("Module <b>{0}</b> successfully installed".format(dbapi))
            return True
        self._toolbox.msg_error.emit("Installing module <b>{0}</b> failed".format(dbapi))
        return False

    @busy_effect
    def install_dbapi_conda(self, dbapi):
        """Install DBAPI using conda. Fails if conda is not installed."""
        try:
            import conda.cli
        except ImportError:
            self._toolbox.msg_error.emit("Conda not found. Installing {0} failed.".format(dbapi))
            self._widget.ui.comboBox_dialect.setCurrentIndex(0)
            return False
        try:
            self._toolbox.msg.emit("Installing module <b>{0}</b> using Conda".format(dbapi))
            conda.cli.main('conda', 'install',  '-y', dbapi)
            self._toolbox.msg_success.emit("Module <b>{0}</b> successfully installed".format(dbapi))
            return True
        except Exception as e:
            logging.exception(e)
            self._toolbox.msg_error.emit("Installing module <b>{0}</b> failed".format(dbapi))
            self._widget.ui.comboBox_dialect.setCurrentIndex(0)
            return False

    def reference(self):
        """Return a reference from user's choices."""
        if self._widget.ui.comboBox_dialect.currentIndex() < 0:
            self._toolbox.msg_warning.emit("Please select dialect first")
            return None
        dialect = self._widget.ui.comboBox_dialect.currentText()
        if dialect == 'mssql':
            if self._widget.ui.comboBox_dsn.currentIndex() < 0:
                self._toolbox.msg_warning.emit("Please select DSN first")
                return None
            dsn = self._widget.ui.comboBox_dsn.currentText()
            username = self._widget.ui.lineEdit_username.text()
            password = self._widget.ui.lineEdit_password.text()
            url = 'mssql+pyodbc://'
            if username:
                url += username
            if password:
                url += ":" + password
            url += '@' + dsn
            # Set database equal to dsn for creating the reference below
            database = dsn
        elif dialect == 'sqlite':
            sqlite_file = self._widget.ui.lineEdit_SQLite_file.text()
            if not os.path.isfile(sqlite_file):
                self._toolbox.msg_warning.emit("Set a path to an SQLite file or click create fresh Spine "
                                               "database button")
                return None
            url = 'sqlite:///{0}'.format(sqlite_file)
            # Set database equal to file's basename for creating the reference below
            database = os.path.basename(sqlite_file)
            username = getpass.getuser()
        else:
            host = self._widget.ui.lineEdit_host.text()
            if not host:
                self._toolbox.msg_warning.emit("Host missing")
                return None
            database = self._widget.ui.lineEdit_database.text()
            if not database:
                self._toolbox.msg_warning.emit("Database missing")
                return None
            port = self._widget.ui.lineEdit_port.text()
            username = self._widget.ui.lineEdit_username.text()
            password = self._widget.ui.lineEdit_password.text()
            dbapi = SQL_DIALECT_API[dialect]
            url = "+".join([dialect, dbapi]) + "://"
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
            self._toolbox.msg_error.emit("Connection failed: {}".format(e.orig.args))
            return None
        if dialect == 'sqlite':
            # Check integrity SQLite database
            try:
                engine.execute('pragma quick_check;')
            except DatabaseError as e:
                self._toolbox.msg_error.emit("The file {0} has integrity issues "
                                             "(not a SQLite database?): {1}".format(database, e.orig.args))
                return None
        # Get system's username if none given
        if not username:
            username = getpass.getuser()
        reference = {
            'database': database,
            'username': username,
            'url': url
        }
        return reference

    @busy_effect
    @Slot(name="open_treeview")
    def open_treeview(self):
        """Open reference in Data Store form."""
        reference = self.reference()
        if not reference:
            return
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        try:
            db_map = DiffDatabaseMapping(db_url, username)
        except SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return
        data_store_form = DataStoreForm(self, db_map, database)
        data_store_form.show()

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in this Data Store's data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    def find_file(self, fname, visited_items):
        """Search for filename in data and return the path if found."""
        # logging.debug("Looking for file {0} in DS {1}.".format(fname, self.name))
        if self in visited_items:
            logging.debug("Infinite loop detected while visiting {0}.".format(self.name))
            return None
        reference = self.reference()
        dialect = self._widget.ui.comboBox_dialect.currentText()
        if dialect != "sqlite":
            return None
        file_path = self._widget.ui.lineEdit_SQLite_file.text()
        if not os.path.exists(file_path):
            return None
        if fname == os.path.basename(file_path):
            # logging.debug("{0} found in DS {1}".format(fname, self.name))
            self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
            return file_path
        visited_items.append(self)
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # Find item from project model
            found_item = self._toolbox.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            if item_data.item_type in ["Data Store", "Data Connection"]:
                path = item_data.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None

    @Slot(name="create_new_spine_database")
    def create_new_spine_database(self):
        """Create new (empty) Spine database file in data directory."""
        answer = QInputDialog.getText(self._toolbox, "Create fresh Spine database", "Database name:")
        database = answer[0]
        if not database:
            return
        filename = os.path.join(self.data_dir, database + ".sqlite")
        try:
            os.remove(filename)
        except OSError:
            pass
        url = "sqlite:///" + filename
        create_new_spine_database(url)
        username = getpass.getuser()
        reference = {
            'database': database,
            'username': username,
            'url': url
        }
        self.load_reference(reference)
