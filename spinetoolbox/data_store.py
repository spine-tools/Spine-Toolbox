######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Module for data store class.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   18.12.2017
"""

import sys
import os
import getpass
import logging
import fnmatch
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, Qt
from PySide2.QtWidgets import QMessageBox, QFileDialog, QApplication, QCheckBox
from project_item import ProjectItem
from widgets.data_store_widgets import TreeViewForm, GraphViewForm
from widgets.tabular_view_widget import TabularViewForm
from graphics_items import DataStoreIcon
from helpers import create_dir, busy_effect
from config import SQL_DIALECT_API
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
import qsubprocess
import spinedatabase_api


class DataStore(ProjectItem):
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
        # Instance variables for saving selections in shared widgets
        self.selected_dialect = ""
        self.selected_dsn = ""
        self.selected_sqlite_file = ""
        self.selected_host = ""
        self.selected_port = ""
        self.selected_db = ""
        self.selected_username = ""
        self.selected_password = ""
        self.tree_view_form = None
        self.graph_view_form = None
        self.tabular_view_form = None
        # Make project directory for this Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                         " Check permissions.".format(self.data_dir))
        self._graphics_item = DataStoreIcon(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self._reference = reference
        self.load_reference_into_selections()
        self._sigs = self.make_signal_handler_dict()

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_ds_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_ds_tree_view.clicked] = self.open_tree_view
        s[self._toolbox.ui.pushButton_ds_graph_view.clicked] = self.open_graph_view
        s[self._toolbox.ui.pushButton_ds_tabular_view.clicked] = self.open_tabular_view
        s[self._toolbox.ui.toolButton_browse.clicked] = self.browse_clicked
        s[self._toolbox.ui.comboBox_dialect.currentTextChanged] = self.check_dialect
        s[self._toolbox.ui.toolButton_new_spine.clicked] = self.create_new_spine_database
        s[self._toolbox.ui.toolButton_copy_db_url.clicked] = self.copy_db_url
        s[self._toolbox.ui.lineEdit_SQLite_file.file_dropped] = self.set_path_to_sqlite_file
        return s

    def activate(self):
        """Restore selections and connect signals."""
        self.restore_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item {0} deactivation failed".format(self.name))
            return False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_ds_name.setText(self.name)
        if self.selected_dialect:
            self._toolbox.ui.comboBox_dialect.setCurrentText(self.selected_dialect)
        else:
            self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
        # Set widgets enabled/disabled according to selected dialect
        if self.selected_dialect == "":
            self.enable_no_dialect()
        elif self.selected_dialect == "sqlite":
            self.enable_sqlite()
        elif self.selected_dialect == "mssql":
            self.enable_mssql()
        else:
            self.enable_common()
        self._toolbox.ui.comboBox_dsn.setCurrentText(self.selected_dsn)
        self._toolbox.ui.lineEdit_SQLite_file.setText(self.selected_sqlite_file)
        self._toolbox.ui.lineEdit_host.setText(self.selected_host)
        self._toolbox.ui.lineEdit_port.setText(self.selected_port)
        self._toolbox.ui.lineEdit_database.setText(self.selected_db)
        self._toolbox.ui.lineEdit_username.setText(self.selected_username)
        self._toolbox.ui.lineEdit_password.setText(self.selected_password)

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        self.selected_dialect = self._toolbox.ui.comboBox_dialect.currentText()
        self.selected_dsn = self._toolbox.ui.comboBox_dsn.currentText()
        self.selected_sqlite_file = self._toolbox.ui.lineEdit_SQLite_file.text()
        self.selected_host = self._toolbox.ui.lineEdit_host.text()
        self.selected_port = self._toolbox.ui.lineEdit_port.text()
        self.selected_db = self._toolbox.ui.lineEdit_database.text()
        self.selected_username = self._toolbox.ui.lineEdit_username.text()
        self.selected_password = self._toolbox.ui.lineEdit_password.text()

    def set_reference(self, reference):
        """Set reference attribute. Used by Tool when passing on results."""
        self._reference = reference

    def reference(self):
        """Reference attribute."""
        return self._reference

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    @Slot("QString", name="set_path_to_sqlite_file")
    def set_path_to_sqlite_file(self, file_path):
        """Set path to SQLite file."""
        self._toolbox.ui.lineEdit_SQLite_file.setText(file_path)

    @Slot(bool, name='browse_clicked')
    def browse_clicked(self, checked=False):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, 'Select SQlite file', self.data_dir, 'SQLite (*.*)')
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        filename = os.path.split(file_path)[1]
        # Update UI
        self._toolbox.ui.comboBox_dsn.clear()
        self._toolbox.ui.lineEdit_SQLite_file.setText(file_path)
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_database.setText(filename)
        self._toolbox.ui.lineEdit_username.setText(getpass.getuser())
        self._toolbox.ui.lineEdit_password.clear()

    def load_reference_into_selections(self):
        """Load reference attribute into shared widget selections.
        Used when loading the project, and creating a new Spine db."""
        # TODO: now it only handles SQLite references, but should handle all types of reference
        if not self._reference:  # This probably does not happen anymore
            return
        # Keep compatibility with previous versions where reference was a list
        if isinstance(self._reference, list):
            self._reference = self._reference[0]
        db_url = self._reference['url']
        if not db_url or db_url == "":
            # No point in checking further
            return
        database = self._reference['database']
        username = self._reference['username']
        try:
            dialect_dbapi = db_url.split('://')[0]
        except IndexError:
            self._toolbox.msg_error.emit("Error in <b>{0}</b> database reference. Unable to parse stored "
                                         "reference. Please select a new one.".format(self.name))
            return
        try:
            dialect, dbapi = dialect_dbapi.split('+')
        except ValueError:
            dialect = dialect_dbapi
            dbapi = None
        if dialect not in SQL_DIALECT_API:
            self._toolbox.msg_error.emit("Error in <b>{0}</b> database reference. Stored reference "
                                         "dialect <b>{1}</b> is not supported.".format(self.name, dialect))
            return
        self.selected_dialect = dialect
        if dbapi and SQL_DIALECT_API[dialect] != dbapi:
            recommended_dbapi = SQL_DIALECT_API[dialect]
            self._toolbox.msg_warning.emit("Warning regarding <b>{0}</b> database reference. Stored reference "
                                           "is using dialect <b>{1}</b> with driver <b>{2}</b>, whereas "
                                           "<b>{3}</b> is recommended"
                                           .format(self.name, dialect, dbapi, recommended_dbapi))
        if dialect == "sqlite":
            try:
                file_path = os.path.abspath(db_url.split(':///')[1])
                # file_path = os.path.abspath(file_path)
            except IndexError:
                file_path = ""
                self._toolbox.msg_error.emit("Error in <b>{0}</b> database reference. Unable to determine "
                                             "path to SQLite file from stored reference. Please select "
                                             "a new one.".format(self.name))
            if not os.path.isfile(file_path):
                file_path = ""
                self._toolbox.msg_warning.emit("Error in <b>{0}</b> database reference. Invalid path to "
                                               "SQLite file. Maybe it was deleted?".format(self.name))
            self.selected_sqlite_file = os.path.abspath(file_path)
            self.selected_db = database
            self.selected_username = username

    def current_reference(self):
        """Returns the current state of the reference according to user's selections.
        Used when saving the project and by the View item."""
        # If the item is currently selected, we save selections so we can use `dump_selections_into_reference`
        current = self._toolbox.ui.treeView_project.currentIndex()
        current_item = self._toolbox.project_item_model.project_item(current)
        if current_item == self:
            self.save_selections()
        self.dump_selections_into_reference()
        return self._reference

    def dump_selections_into_reference(self):
        """Dump selections into reference attribute."""
        if not self.selected_dialect:
            self._reference = None
            return
        if self.selected_dialect == 'mssql':
            if not self.selected_dsn:
                return None
            dsn = self.selected_dsn
            username = self.selected_username
            password = self.selected_password
            url = 'mssql+pyodbc://'
            if username:
                url += username
            if password:
                url += ":" + password
            url += '@' + dsn
            database = dsn
        elif self.selected_dialect == 'sqlite':
            sqlite_file = self.selected_sqlite_file
            if not sqlite_file:
                return None
            if not os.path.isfile(sqlite_file):
                return None
            url = 'sqlite:///{0}'.format(sqlite_file)
            database = os.path.basename(self.selected_sqlite_file)
            username = getpass.getuser()
        else:
            host = self.selected_host
            if not host:
                return None
            database = self.selected_db
            if not database:
                return None
            port = self.selected_port
            username = self.selected_username
            password = self.selected_password
            dbapi = SQL_DIALECT_API[self.selected_dialect]
            url = "+".join([self.selected_dialect, dbapi]) + "://"
            if username:
                url += username
            if password:
                url += ":" + password
            url += "@" + host
            if port:
                url += ":" + port
            url += "/" + database
        # Set reference attribute
        self._reference = {
            'database': database,
            'username': username,
            'url': url
        }

    def enable_no_dialect(self):
        """Adjust widget enabled status to default when no dialect is selected."""
        self._toolbox.ui.comboBox_dialect.setEnabled(True)
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.lineEdit_SQLite_file.setEnabled(False)
        self._toolbox.ui.toolButton_browse.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(True)
        self._toolbox.ui.lineEdit_SQLite_file.setEnabled(False)
        self._toolbox.ui.toolButton_browse.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.lineEdit_SQLite_file.setEnabled(True)
        self._toolbox.ui.toolButton_browse.setEnabled(True)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.lineEdit_SQLite_file.setEnabled(False)
        self._toolbox.ui.toolButton_browse.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(True)
        self._toolbox.ui.lineEdit_port.setEnabled(True)
        self._toolbox.ui.lineEdit_database.setEnabled(True)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)

    @Slot(str, name="check_dialect")
    def check_dialect(self, dialect):
        """Check if selected dialect is supported. Offer to install DBAPI if not.

        Returns:
            True if dialect is supported, False if not.
        """
        if dialect == "":  # TODO: Set text when index is -1 to 'Select dialect...'
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
                    self._toolbox.ui.comboBox_dsn.clear()
                    self._toolbox.ui.comboBox_dsn.addItems(mssql_dsns)
                    self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
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
                    self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                    return False
            elif msg.clickedButton() == conda_button:
                if not self.install_dbapi_conda(dbapi):
                    self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                    return False
            else:
                self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                msg = "Unable to use dialect '{}'.".format(dialect)
                self._toolbox.msg_error.emit(msg)
                return False
            # Check that dialect is not found
            if not self.check_dialect(dialect):
                self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                return False
            return True

    @busy_effect
    def install_dbapi_pip(self, dbapi):
        """Install DBAPI using pip."""
        self._toolbox.msg.emit("Installing module <b>{0}</b> using pip".format(dbapi))
        program = sys.executable
        args = list()
        args.append("-m")
        args.append("pip")
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
            return False
        try:
            self._toolbox.msg.emit("Installing module <b>{0}</b> using Conda".format(dbapi))
            conda.cli.main('conda', 'install',  '-y', dbapi)
            self._toolbox.msg_success.emit("Module <b>{0}</b> successfully installed".format(dbapi))
            return True
        except Exception as e:
            self._toolbox.msg_error.emit("Installing module <b>{0}</b> failed".format(dbapi))
            return False

    def make_reference(self):
        """Return a reference based on the current state of the ui,
        or None if something is bad/missing.
        Used when opening the data store tree view or graph view forms."""
        if self._toolbox.ui.comboBox_dialect.currentIndex() < 0:
            self._toolbox.msg_warning.emit("Please select dialect first")
            return None
        dialect = self._toolbox.ui.comboBox_dialect.currentText()
        if dialect == 'mssql':
            if self._toolbox.ui.comboBox_dsn.currentIndex() < 0:
                self._toolbox.msg_warning.emit("Please select DSN first")
                return None
            dsn = self._toolbox.ui.comboBox_dsn.currentText()
            username = self._toolbox.ui.lineEdit_username.text()
            password = self._toolbox.ui.lineEdit_password.text()
            url = 'mssql+pyodbc://'
            if username:
                url += username
            if password:
                url += ":" + password
            url += '@' + dsn
            # Set database equal to dsn for creating the reference below
            database = dsn
        elif dialect == 'sqlite':
            sqlite_file = self._toolbox.ui.lineEdit_SQLite_file.text()
            if not sqlite_file:
                self._toolbox.msg_warning.emit("Path to SQLite file missing")
                return None
            if not os.path.isfile(sqlite_file):
                self._toolbox.msg_warning.emit("Invalid path")
                return None
            url = 'sqlite:///{0}'.format(sqlite_file)
            # Set database equal to file's basename for creating the reference below
            database = os.path.basename(sqlite_file)
            username = getpass.getuser()
        else:
            host = self._toolbox.ui.lineEdit_host.text()
            if not host:
                self._toolbox.msg_warning.emit("Host missing")
                return None
            database = self._toolbox.ui.lineEdit_database.text()
            if not database:
                self._toolbox.msg_warning.emit("Database missing")
                return None
            port = self._toolbox.ui.lineEdit_port.text()
            username = self._toolbox.ui.lineEdit_username.text()
            password = self._toolbox.ui.lineEdit_password.text()
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
            # Check integrity of SQLite database
            try:
                engine.execute('pragma quick_check;')
            except DatabaseError as e:
                self._toolbox.msg_error.emit("File {0} has integrity issues "
                                             "(not an SQLite database?): {1}".format(database, e.orig.args))
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

    def get_db_map(self, db_url, username, upgrade=False):
        """Return a DiffDatabaseMapping instance to work with.
        """
        try:
            return spinedatabase_api.DiffDatabaseMapping(db_url, username, upgrade=upgrade)
        except spinedatabase_api.SpineDBVersionError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Incompatible database version")
            msg.setText("The database at <b>{}</b> is from an older version of Spine "\
                        "and needs to be upgraded in order to be used with the current version.".format(db_url))
            msg.setInformativeText("Do you want to upgrade it now?" \
                                   "<p><b>WARNING</b>: After the upgrade, "\
                                   "the database may no longer be used "\
                                   "with previous versions of Spine.")
            msg.addButton(QMessageBox.Cancel)
            msg.addButton("Upgrade", QMessageBox.YesRole)
            ret = msg.exec_()  # Show message box
            if ret == QMessageBox.Cancel:
                return None
            return self.get_db_map(db_url, username, upgrade=True)
        except spinedatabase_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return None

    @Slot(bool, name="open_tree_view")
    def open_tree_view(self, checked=False):
        """Open reference in tree view form."""
        reference = self.make_reference()
        if not reference:
            return
        if self.tree_view_form:
            # If the url hasn't changed, just raise the current form
            if self.tree_view_form.db_map.db_url == reference['url']:
                if self.tree_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.tree_view_form.setWindowState(self.tree_view_form.windowState()
                                                       & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.tree_view_form.activateWindow()
                else:
                    self.tree_view_form.raise_()
                return
            self.tree_view_form.destroyed.disconnect(self.tree_view_form_destroyed)
            self.tree_view_form.close()
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        db_map = self.get_db_map(db_url, username)
        if not db_map:
            return
        self.do_open_tree_view(db_map, database)

    @busy_effect
    def do_open_tree_view(self, db_map, database):
        """Open reference in tree view form."""
        try:
            self.tree_view_form = TreeViewForm(self, db_map, database)
        except:
            db_map.close()
            raise
        self.tree_view_form.show()
        self.tree_view_form.destroyed.connect(self.tree_view_form_destroyed)

    @Slot(name="tree_view_form_destroyed")
    def tree_view_form_destroyed(self):
        self.tree_view_form = None

    @Slot(bool, name="open_graph_view")
    def open_graph_view(self, checked=False):
        """Open reference in graph view form."""
        reference = self.make_reference()
        if not reference:
            return
        if self.graph_view_form:
            # If the url hasn't changed, just raise the current form
            if self.graph_view_form.db_map.db_url == reference['url']:
                if self.graph_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.graph_view_form.setWindowState(self.graph_view_form.windowState()
                                                       & ~Qt.WindowMinimized | Qt.WindowActive)
                    self.graph_view_form.activateWindow()
                else:
                    self.graph_view_form.raise_()
                return
            self.graph_view_form.destroyed.disconnect(self.graph_view_form_destroyed)
            self.graph_view_form.close()
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        db_map = self.get_db_map(db_url, username)
        if not db_map:
            return
        self.do_open_graph_view(db_map, database)

    @busy_effect
    def do_open_graph_view(self, db_map, database):
        """Open reference in graph view form."""
        try:
            self.graph_view_form = GraphViewForm(self, db_map, database, read_only=False)
        except:
            db_map.close()
            raise
        self.graph_view_form.show()
        self.graph_view_form.destroyed.connect(self.graph_view_form_destroyed)

    @Slot(name="graph_view_form_destroyed")
    def graph_view_form_destroyed(self):
        self.graph_view_form = None

    @Slot(bool, name="open_tabular_view")
    def open_tabular_view(self, checked=False):
        """Open reference in Data Store tabular view."""
        if self.tabular_view_form:
            if self.tabular_view_form.windowState() & Qt.WindowMinimized:
                # Remove minimized status and restore window with the previous state (maximized/normal state)
                self.tabular_view_form.setWindowState(self.tabular_view_form.windowState()
                                                    & ~Qt.WindowMinimized | Qt.WindowActive)
                self.tabular_view_form.activateWindow()
            else:
                self.tabular_view_form.raise_()
            return
        if self._toolbox.ui.comboBox_dialect.currentIndex() < 0:
            self._toolbox.msg_warning.emit("Please select dialect first")
            return
        reference = self.make_reference()
        if not reference:
            return
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        db_map = self.get_db_map(db_url, username)
        if not db_map:
            return
        self.do_open_tabular_view(db_map, database)

    @busy_effect
    def do_open_tabular_view(self, db_map, database):
        """Open reference in tabular view form."""
        try:
            self.tabular_view_form = TabularViewForm(self, db_map, database)
        except:
            db_map.close()
            raise
        self.tabular_view_form.destroyed.connect(self.tabular_view_form_destroyed)
        self.tabular_view_form.show()

    @Slot(name="tabular_view_form_destroyed")
    def tabular_view_form_destroyed(self):
        self.tabular_view_form = None

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Open file explorer in this Data Store's data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    def data_files(self):
        """Return a list of files that are in this items data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    def find_file(self, fname, visited_items):
        """Search for filename in data and return the path if found."""
        # logging.debug("Looking for file {0} in DS {1}.".format(fname, self.name))
        if self in visited_items:
            self._toolbox.msg_warning.emit("There seems to be an infinite loop in your project. Please fix the "
                                           "connections and try again. Detected at {0}.".format(self.name))
            return None
        reference = self.current_reference()
        if not reference:
            # Data Store has no reference
            return None
        db_url = reference['url']
        if not db_url.lower().startswith('sqlite'):
            return None
        file_path = os.path.abspath(db_url.split(':///')[1])
        if not os.path.exists(file_path):
            return None
        if fname == os.path.basename(file_path):
            # logging.debug("{0} found in DS {1}".format(fname, self.name))
            self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
            return file_path
        visited_items.append(self)
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # Find item from project model
            item_index = self._toolbox.project_item_model.find_item(input_item)
            if not item_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(item_index)
            if item.item_type in ["Data Store", "Data Connection"]:
                path = item.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None

    def find_files(self, pattern, visited_items):
        """Search for files matching the given pattern (with wildcards) in data directory
        and return a list of matching paths.

        Args:
            pattern (str): File name (no path). May contain wildcards.
            visited_items (list): List of project item names that have been visited

        Returns:
            List of matching paths. List is empty if no matches found.
        """
        paths = list()
        if self in visited_items:
            self._toolbox.msg_warning.emit("There seems to be an infinite loop in your project. Please fix the "
                                           "connections and try again. Detected at {0}.".format(self.name))
            return paths
        # Check the current reference. If it is an sqlite file, this is a possible match
        # If dialect is not sqlite, the reference is ignored
        reference = self.current_reference()
        db_url = reference['url']
        if db_url.lower().startswith('sqlite'):
            file_path = os.path.abspath(db_url.split(':///')[1])
            if os.path.exists(file_path):
                if fnmatch.fnmatch(file_path, pattern):  # fname == os.path.basename(file_path):
                    # self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
                    paths.append(file_path)
        else:  # Not an SQLite reference
            pass
        # Search files that match the pattern from this Data Store's data directory
        for data_file in self.data_files():  # data_file is a filename (no path)
            if fnmatch.fnmatch(data_file, pattern):
                # self._toolbox.msg.emit("\t<b>{0}</b> matches pattern <b>{1}</b> in Data Store <b>{2}</b>"
                #                        .format(data_file, pattern, self.name))
                path = os.path.join(self.data_dir, data_file)
                if path not in paths:  # Skip if the sqlite file was already added from the reference
                    paths.append(path)
        visited_items.append(self)
        # Find items that are connected to this Data Connection
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if item.item_type in ["Data Store", "Data Connection"]:
                matching_paths = item.find_files(pattern, visited_items)
                if matching_paths is not None:
                    paths = paths + matching_paths
                    return paths
        return paths

    @Slot(bool, name="copy_db_url")
    def copy_db_url(self, checked=False):
        """Copy db url to clipboard."""
        reference = self.make_reference()
        if not reference:
            self._toolbox.msg_error.emit("Unable to copy database url to clipboard.")
            return
        db_url = reference['url']
        QApplication.clipboard().setText(db_url)
        self._toolbox.msg.emit("Database url '{}' successfully copied to clipboard.".format(db_url))

    @Slot(bool, name="create_new_spine_database")
    def create_new_spine_database(self, checked=False):
        """Create new (empty) Spine SQLite database file."""
        dialog = QFileDialog(self._toolbox,
                             "Create new Spine SQLite database",
                             self.data_dir,
                             "SQlite database (*.sqlite *.db)")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Only way to add the checkbox
        check_box = QCheckBox("Include specific data structure for Spine Model.", dialog)
        check_box.setChecked(True)
        dialog.layout().addWidget(check_box)
        if not dialog.exec_():
            return
        file_path = dialog.selectedFiles()[0]
        extension = os.path.splitext(file_path)[1]
        if not extension:
            file_path += ".sqlite"
        # We need to remove the file first so `create_new_spine_database` doesn't complain
        try:
            os.remove(file_path)
        except OSError:
            pass
        url = "sqlite:///" + file_path
        for_spine_model = check_box.isChecked()
        spinedatabase_api.create_new_spine_database(url, for_spine_model=for_spine_model)
        database = os.path.basename(file_path)
        username = getpass.getuser()
        # Update UI
        self._toolbox.ui.comboBox_dsn.clear()
        self._toolbox.ui.comboBox_dialect.setCurrentText("sqlite")
        self._toolbox.ui.lineEdit_SQLite_file.setText(os.path.abspath(file_path))
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_database.setText(database)
        self._toolbox.ui.lineEdit_username.setText(username)
        self._toolbox.ui.lineEdit_password.clear()

    def update_name_label(self):
        """Update Data Store tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_ds_name.setText(self.name)
