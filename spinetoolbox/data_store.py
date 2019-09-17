######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

import os
import logging
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, Qt
from PySide2.QtWidgets import QMessageBox, QFileDialog, QApplication
import spinedb_api
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url, URL
from project_item import ProjectItem
from widgets.tree_view_widget import TreeViewForm
from widgets.graph_view_widget import GraphViewForm
from widgets.tabular_view_widget import TabularViewForm
from graphics_items import DataStoreIcon
from helpers import create_dir, busy_effect, get_db_map, create_log_file_timestamp


class DataStore(ProjectItem):
    """Data Store class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        url (str or dict): SQLAlchemy url
        reference (dict): reference, contains SQLAlchemy url (keeps compatibility with older project files)
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """

    def __init__(self, toolbox, name, description, x, y, url=None, reference=None):
        """Class constructor."""
        super().__init__(toolbox, name, description)
        self._project = self._toolbox.project()
        self.item_type = "Data Store"
        if type(reference) == dict and "url" in reference:
            url = reference["url"]
        self._url = self.parse_url(url)
        self.tree_view_form = None
        self.graph_view_form = None
        self.tabular_view_form = None
        # Make project directory for this Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.logs_dir = os.path.join(self.data_dir, "logs")
        try:
            create_dir(self.data_dir)
            create_dir(self.logs_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed. Check permissions.".format(self.data_dir)
            )
        self._graphics_item = DataStoreIcon(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self._sigs = self.make_signal_handler_dict()

    def parse_url(self, url):
        """Return a complete url dictionary from the given dict or string"""
        base_url = dict(dialect=None, username=None, password=None, host=None, port=None, database=None)
        if isinstance(url, dict):
            base_url.update(url)
        elif isinstance(url, str):
            sa_url = make_url(url)
            base_url["dialect"] = sa_url.get_dialect().name
            base_url.update(sa_url.translate_connect_args())
        else:
            self._toolbox.msg_error.emit(
                "Unable to parse URL for <b>{0}</b>: unsupported type '{1}'".format(self.name, type(url))
            )
        return base_url

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_ds_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_ds_tree_view.clicked] = self.open_tree_view
        s[self._toolbox.ui.pushButton_ds_graph_view.clicked] = self.open_graph_view
        s[self._toolbox.ui.pushButton_ds_tabular_view.clicked] = self.open_tabular_view
        s[self._toolbox.ui.toolButton_open_sqlite_file.clicked] = self.open_sqlite_file
        s[self._toolbox.ui.toolButton_create_new_spine_db.clicked] = self.create_new_spine_database
        s[self._toolbox.ui.toolButton_copy_url.clicked] = self.copy_url
        s[self._toolbox.ui.comboBox_dialect.currentTextChanged] = self.refresh_dialect
        s[self._toolbox.ui.lineEdit_database.file_dropped] = self.set_path_to_sqlite_file
        s[self._toolbox.ui.lineEdit_username.textChanged] = self.refresh_username
        s[self._toolbox.ui.lineEdit_password.textChanged] = self.refresh_password
        s[self._toolbox.ui.lineEdit_host.textChanged] = self.refresh_host
        s[self._toolbox.ui.lineEdit_port.textChanged] = self.refresh_port
        s[self._toolbox.ui.lineEdit_database.textChanged] = self.refresh_database
        return s

    def activate(self):
        """Load url into selections and connect signals."""
        self._toolbox.ui.label_ds_name.setText(self.name)
        self.load_url_into_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Disconnect signals."""
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        return True

    def url(self):
        """Return the url attribute, for saving the project."""
        return self._url

    @busy_effect
    def make_url(self, log_errors=True):
        """Return a sqlalchemy url from the current url attribute or None if not valid."""
        if not self._url:
            if log_errors:
                self._toolbox.msg_error.emit(
                    "No URL specified for <b>{0}</b>. Please specify one and try again".format(self.name)
                )
            return None
        try:
            url_copy = dict(self._url)
            dialect = url_copy.pop("dialect")
            if not dialect:
                if log_errors:
                    self._toolbox.msg_error.emit(
                        "Unable to generate URL from <b>{0}</b> selections: invalid dialect {1}. "
                        "<br>Please select a new dialect and try again.".format(self.name, dialect)
                    )
                return None
            if dialect == 'sqlite':
                url = URL('sqlite', **url_copy)  # pylint: disable=unexpected-keyword-arg
            else:
                db_api = spinedb_api.SUPPORTED_DIALECTS[dialect]
                drivername = f"{dialect}+{db_api}"
                url = URL(drivername, **url_copy)  # pylint: disable=unexpected-keyword-arg
        except Exception as e:  # pylint: disable=broad-except
            # This is in case one of the keys has invalid format
            if log_errors:
                self._toolbox.msg_error.emit(
                    "Unable to generate URL from <b>{0}</b> selections: {1} "
                    "<br>Please make new selections and try again.".format(self.name, e)
                )
            return None
        if dialect == "sqlite" and not url.database:
            if log_errors:
                self._toolbox.msg_error.emit(
                    "Unable to generate URL from <b>{0}</b> selections: database missing. "
                    "<br>Please select a database and try again.".format(self.name)
                )
            return None
        # Small hack to make sqlite file paths relative to this DS directory
        if dialect == "sqlite" and not os.path.isabs(url.database):
            url.database = os.path.join(self.data_dir, url.database)
            self._toolbox.ui.lineEdit_database.setText(url.database)
        # Final check
        try:
            engine = create_engine(url)
            with engine.connect():
                pass
        except Exception as e:  # pylint: disable=broad-except
            if log_errors:
                self._toolbox.msg_error.emit(
                    "Unable to generate URL from <b>{0}</b> selections: {1} "
                    "<br>Please make new selections and try again.".format(self.name, e)
                )
            return None
        return url

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    @Slot("QString", name="set_path_to_sqlite_file")
    def set_path_to_sqlite_file(self, file_path):
        """Set path to SQLite file."""
        self._toolbox.ui.lineEdit_database.setText(file_path)

    @Slot(bool, name='open_sqlite_file')
    def open_sqlite_file(self, checked=False):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, 'Select SQlite file', self.data_dir)
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        # Update UI
        self._toolbox.ui.lineEdit_database.setText(file_path)

    def load_url_into_selections(self):
        """Load url attribute into shared widget selections.
        Used when activating the item, and creating a new Spine db."""
        # TODO: Test what happens when Tool item calls this and this item is selected.
        self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_database.clear()
        self._toolbox.ui.lineEdit_username.clear()
        self._toolbox.ui.lineEdit_password.clear()
        if not self._url:
            return
        dialect = self._url["dialect"]
        self.enable_dialect(dialect)
        self._toolbox.ui.comboBox_dialect.setCurrentText(dialect)
        if self._url["host"]:
            self._toolbox.ui.lineEdit_host.setText(self._url["host"])
        if self._url["port"]:
            self._toolbox.ui.lineEdit_port.setText(str(self._url["port"]))
        if self._url["database"]:
            self._toolbox.ui.lineEdit_database.setText(self._url["database"])
        if self._url["username"]:
            self._toolbox.ui.lineEdit_username.setText(self._url["username"])
        if self._url["password"]:
            self._toolbox.ui.lineEdit_password.setText(self._url["password"])

    def set_url_key(self, key, value):
        """Set url key to value."""
        self._url[key] = value
        self.item_changed.emit()

    @Slot("QString", name="refresh_host")
    def refresh_host(self, host):
        """Refresh host from selections."""
        self.set_url_key("host", host)

    @Slot("QString", name="refresh_port")
    def refresh_port(self, port):
        """Refresh port from selections."""
        self.set_url_key("port", port)

    @Slot("QString", name="refresh_database")
    def refresh_database(self, database):
        """Refresh database from selections."""
        self.set_url_key("database", database)

    @Slot("QString", name="refresh_username")
    def refresh_username(self, username):
        """Refresh username from selections."""
        self.set_url_key("username", username)

    @Slot("QString", name="refresh_password")
    def refresh_password(self, password):
        """Refresh password from selections."""
        self.set_url_key("password", password)

    @Slot("QString", name="refresh_dialect")
    def refresh_dialect(self, dialect):
        self.set_url_key("dialect", dialect)
        self.enable_dialect(dialect)

    def enable_dialect(self, dialect):
        """Enable the given dialect in the item controls."""
        if dialect == 'sqlite':
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
            self.enable_common()

    def enable_no_dialect(self):
        """Adjust widget enabled status to default when no dialect is selected."""
        self._toolbox.ui.comboBox_dialect.setEnabled(True)
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(True)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_database.clear()

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(True)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(True)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_username.clear()
        self._toolbox.ui.lineEdit_password.clear()

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(True)
        self._toolbox.ui.lineEdit_port.setEnabled(True)
        self._toolbox.ui.lineEdit_database.setEnabled(True)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)

    @Slot(bool, name="open_tree_view")
    def open_tree_view(self, checked=False):
        """Open url in tree view form."""
        url = self.make_url()
        if not url:
            return
        if self.tree_view_form:
            # If the url hasn't changed, just raise the current form
            if self.tree_view_form.db_maps[0].db_url == url:
                if self.tree_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.tree_view_form.setWindowState(
                        self.tree_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.tree_view_form.activateWindow()
                else:
                    self.tree_view_form.raise_()
                return
            self.tree_view_form.destroyed.disconnect(self.tree_view_form_destroyed)
            self.tree_view_form.close()
        try:
            db_map = get_db_map(url)
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            db_map = None
        if not db_map:
            return
        self.do_open_tree_view(db_map)

    @busy_effect
    def do_open_tree_view(self, db_map):
        """Open url in tree view form."""
        self.tree_view_form = TreeViewForm(self._project, {self.name: db_map})
        self.tree_view_form.show()
        self.tree_view_form.destroyed.connect(self.tree_view_form_destroyed)

    @Slot(name="tree_view_form_destroyed")
    def tree_view_form_destroyed(self):
        """Notify that tree view form has been destroyed."""
        self.tree_view_form = None

    @Slot(bool, name="open_graph_view")
    def open_graph_view(self, checked=False):
        """Open url in graph view form."""
        url = self.make_url()
        if not url:
            return
        if self.graph_view_form:
            # If the url hasn't changed, just raise the current form
            if self.graph_view_form.db_map.db_url == url:
                if self.graph_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.graph_view_form.setWindowState(
                        self.graph_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.graph_view_form.activateWindow()
                else:
                    self.graph_view_form.raise_()
                return
            self.graph_view_form.destroyed.disconnect(self.graph_view_form_destroyed)
            self.graph_view_form.close()
        try:
            db_map = get_db_map(url)
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            db_map = None
        if not db_map:
            return
        self.do_open_graph_view(db_map)

    @busy_effect
    def do_open_graph_view(self, db_map):
        """Open url in graph view form."""
        self.graph_view_form = GraphViewForm(self._project, {self.name: db_map}, read_only=False)
        self.graph_view_form.show()
        self.graph_view_form.destroyed.connect(self.graph_view_form_destroyed)

    @Slot(name="graph_view_form_destroyed")
    def graph_view_form_destroyed(self):
        """Notify that graph view form has been destroyed."""
        self.graph_view_form = None

    @Slot(bool, name="open_tabular_view")
    def open_tabular_view(self, checked=False):
        """Open url in Data Store tabular view."""
        url = self.make_url()
        if not url:
            return
        if self.tabular_view_form:
            # If the url hasn't changed, just raise the current form
            if self.tabular_view_form.db_map.db_url == url:
                if self.tabular_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.tabular_view_form.setWindowState(
                        self.tabular_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.tabular_view_form.activateWindow()
                else:
                    self.tabular_view_form.raise_()
                return
            self.tabular_view_form.destroyed.disconnect(self.tabular_view_form_destroyed)
            self.tabular_view_form.close()
        try:
            db_map = get_db_map(url)
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            db_map = None
        if not db_map:
            return
        self.do_open_tabular_view(db_map, url.database)

    @busy_effect
    def do_open_tabular_view(self, db_map, database):
        """Open url in tabular view form."""
        self.tabular_view_form = TabularViewForm(self, db_map, database)
        self.tabular_view_form.destroyed.connect(self.tabular_view_form_destroyed)
        self.tabular_view_form.show()
        self.destroyed.connect(self.tabular_view_form.close)

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

    @Slot(bool, name="copy_url")
    def copy_url(self, checked=False):
        """Copy db url to clipboard."""
        url = self.make_url()
        if not url:
            return
        url.password = None
        QApplication.clipboard().setText(str(url))
        self._toolbox.msg.emit("Database url '{}' successfully copied to clipboard.".format(url))

    @Slot(bool, name="create_new_spine_database")
    def create_new_spine_database(self, checked=False):
        """Create new (empty) Spine database."""
        for_spine_model = self._toolbox.ui.checkBox_for_spine_model.isChecked()
        url = self.make_url(log_errors=False)
        if not url:
            self._toolbox.msg_warning.emit(
                "Unable to generate URL from <b>{0}</b> selections. Defaults will be used...".format(self.name)
            )
            self._toolbox.ui.comboBox_dialect.setCurrentText("sqlite")
            self._toolbox.ui.lineEdit_database.setText(os.path.join(self.data_dir, self.name + ".sqlite"))
            url = self.make_url(log_errors=True)
            if not url:
                return
        try:
            if not spinedb_api.is_empty(url):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText("The database at <b>'{0}'</b> is not empty.".format(url))
                msg.setInformativeText("Do you want to overwrite it?")
                msg.addButton("Overwrite", QMessageBox.AcceptRole)
                msg.addButton("Cancel", QMessageBox.RejectRole)
                ret = msg.exec_()  # Show message box
                if ret != QMessageBox.AcceptRole:
                    return
            self.do_create_new_spine_database(url, for_spine_model)
            self._toolbox.msg_success.emit("New Spine db successfully created at '{0}'.".format(url))
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit("Unable to create new Spine db at '{0}': {1}.".format(url, e))

    @busy_effect
    def do_create_new_spine_database(self, url, for_spine_model):  # pylint: disable=no-self-use
        """Separate method so 'busy_effect' don't overlay any message box."""
        spinedb_api.create_new_spine_database(url, for_spine_model=for_spine_model)

    def update_name_label(self):
        """Update Data Store tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_ds_name.setText(self.name)

    def execute(self):
        """Executes this Data Store."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Store <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        inst = self._toolbox.project().execution_instance
        url = self.make_url()
        if not url:
            # Invalid url, nothing else to do here
            self._toolbox.msg_warning.emit(
                "No database url set. Please provide a <i>path</i> to an "
                "SQLite file or <i>host</i>, <i>port</i>, and <i>username</i> "
                "& <i>password</i> for other database dialects."
            )
        else:
            inst.add_ds_url(self.name, url)
            # Import mapped data from Data Interfaces in the execution instance
            try:
                db_map = spinedb_api.DiffDatabaseMapping(url, upgrade=False, username="Mapper")
            except (spinedb_api.SpineDBAPIError, spinedb_api.SpineDBVersionError) as err:
                self._toolbox.msg_error.emit(
                    "<b>{0}:</b> Unable to create database mapping, all import operations will be omitted.".format(err)
                )
                db_map = None
            if db_map:
                all_import_errors = []
                for (di_name, all_data) in inst.di_data_at_sight(self.name):
                    self._toolbox.msg_proc.emit("Importing data from <b>{0}</b> into '{1}'".format(di_name, url))
                    for data in all_data:
                        import_num, import_errors = spinedb_api.import_data(db_map, **data)
                        if import_errors:
                            db_map.rollback_session()
                            all_import_errors += import_errors
                        else:
                            db_map.commit_session("imported with mapper")
                            self._toolbox.msg.emit(
                                "<b>{0}:</b> Inserted {1} data with {2} errors into {3}".format(
                                    self.name, import_num, len(import_errors), db_map.db_url
                                )
                            )
                if all_import_errors:
                    # Log errors in a time stamped file into the logs directory
                    timestamp = create_log_file_timestamp()
                    logfilepath = os.path.abspath(os.path.join(self.logs_dir, timestamp + "_error.log"))
                    with open(logfilepath, 'w') as f:
                        for err in all_import_errors:
                            f.write("{}\n".format(err.msg))
                    # Make error log file anchor with path as tooltip
                    logfile_anchor = (
                        "<a style='color:#BB99FF;' title='"
                        + logfilepath
                        + "' href='file:///"
                        + logfilepath
                        + "'>error log</a>"
                    )
                    self._toolbox.msg.emit(
                        "There where import errors while executing <b>{0}</b>, rolling back: "
                        "{1}".format(self.name, logfile_anchor)
                    )
        self._toolbox.msg.emit("***")
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Store."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-2)

    def simulate_execution(self, inst):
        """Simulates executing this Data Store."""
        super().simulate_execution(inst)
        url = self.make_url(log_errors=False)
        if url:
            inst.add_ds_url(self.name, url)
        else:
            self.add_notification(
                "The URL for this Data Store is not correctly set. " "Set it in the Data Store Properties panel."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["url"] = self.url()
        return d
