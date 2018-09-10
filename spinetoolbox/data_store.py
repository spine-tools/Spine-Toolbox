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

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   18.12.2017
"""

import os
import shutil
import getpass
import logging
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher, Qt
from PySide2.QtWidgets import QInputDialog
from metaobject import MetaObject
from spinedatabase_api import DatabaseMapping, SpineDBAPIError, create_new_spine_database, copy_database
from widgets.data_store_subwindow_widget import DataStoreWidget
from widgets.data_store_widget import DataStoreForm
from widgets.add_db_reference_widget import AddDbReferenceWidget
from graphics_items import DataStoreImage
from helpers import create_dir, busy_effect


class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        references (list): List of references (for now it's only database references)
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, references, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._widget = DataStoreWidget(self, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        self._widget.make_header_for_data()
        self.data_dir_watcher = QFileSystemWatcher(self)
        # Make directory for Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.references = references
        try:
            create_dir(self.data_dir)
            self.data_dir_watcher.addPath(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        self.databases = list()  # name of imported databases NOTE: Not in use at the moment
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)
        self.add_db_reference_form = None
        self._graphics_item = DataStoreImage(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.show_add_db_reference_form)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.toolButton_Spine.clicked.connect(self.create_new_spine_database)
        self._widget.ui.treeView_data.doubleClicked.connect(self.open_data_file)
        self._widget.ui.treeView_references.doubleClicked.connect(self.open_reference)
        self._widget.ui.treeView_references.file_dropped.connect(self.add_file_to_references)
        self._widget.ui.treeView_data.file_dropped.connect(self.add_file_to_data_dir)
        self._widget.ui.toolButton_add.clicked.connect(self.import_references)
        self.data_dir_watcher.directoryChanged.connect(self.refresh)

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

    @Slot("QString", name="add_file_to_references")
    def add_file_to_references(self, path):
        """Add filepath to reference list"""
        url = os.path.abspath(path)
        if not url.lower().endswith('sqlite'):
            self._toolbox.msg_warning.emit("File name has unsupported extension. Only .sqlite files supported")
            return
        if url in [ref['url'] for ref in self.references]:
            self._toolbox.msg_warning.emit("Reference to file <b>{0}</b> already available".format(url))
            return
        reference = {
            'database': os.path.basename(url),
            'username': getpass.getuser(),
            'url': 'sqlite:///' + url
        }
        self.references.append(reference)
        self._widget.populate_reference_list(self.references)

    @Slot("QString", name="add_file_to_data_dir")
    def add_file_to_data_dir(self, file_path):
        """Add file to data directory"""
        src_dir, filename = os.path.split(file_path)
        self._toolbox.msg.emit("Copying file <b>{0}</b>".format(filename))
        try:
            shutil.copy(file_path, self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Copying failed")
            return
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in this Data Store's data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(name="show_add_db_reference_form")
    def show_add_db_reference_form(self):
        """Show the form for querying database connection options."""
        self.add_db_reference_form = AddDbReferenceWidget(self._toolbox, self)
        self.add_db_reference_form.show()

    def add_reference(self, reference):
        """Add reference to reference list and populate widget's reference list."""
        self.references.append(reference)
        self._widget.populate_reference_list(self.references)

    @Slot(name="remove_references")
    def remove_references(self):
        """Remove selected references from reference list.
        Removes all references if nothing is selected.
        """
        indexes = self._widget.ui.treeView_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self.references.clear()
            self._toolbox.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._toolbox.msg.emit("Selected references removed")
        self._widget.populate_reference_list(self.references)

    @Slot(name="import_references")
    def import_references(self):
        """Import data from selected items in reference list into local SQLite file.
        If no item is selected then import all of them.
        """
        if not self.references:
            self._toolbox.msg_warning.emit("No data to import")
            return
        indexes = self._widget.ui.treeView_references.selectedIndexes()
        if not indexes:  # Nothing selected, import all
            references_to_import = self.references
        else:
            references_to_import = [self.references[ind.row()] for ind in indexes]
        for reference in references_to_import:
            try:
                self.import_reference(reference)
            except Exception as e:
                self._toolbox.msg_error.emit("Import failed: {}".format(e))
                continue
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

    @busy_effect
    def import_reference(self, reference):
        """Import reference database into local SQLite file"""
        database = reference['database']
        self._toolbox.msg.emit("Importing database <b>{0}</b>".format(database))
        # Source
        source_url = reference['url']
        # Destination
        if source_url.startswith('sqlite'):
            dest_filename = os.path.join(self.data_dir, database)
        else:
            dest_filename = os.path.join(self.data_dir, database + ".sqlite")
        try:
            os.remove(dest_filename)
        except OSError:
            pass
        dest_url = "sqlite:///" + dest_filename
        copy_database(dest_url, source_url)
        self.databases.append(database)

    @busy_effect
    @Slot("QModelIndex", name="open_data_file")
    def open_data_file(self, index):
        """Open file in Data Store form."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        data_file = self.data_files()[index.row()]
        data_file_path = os.path.join(self.data_dir, data_file)
        db_url = "sqlite:///" + data_file_path
        username = getpass.getuser()
        try:
            mapping = DatabaseMapping(db_url, username)
        except SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return
        database = data_file
        data_store_form = DataStoreForm(self, mapping, database)
        data_store_form.show()

    @busy_effect
    @Slot("QModelIndex", name="open_reference")
    def open_reference(self, index):
        """Open reference in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        reference = self.references[index.row()]
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        try:
            mapping = DatabaseMapping(db_url, username)
        except SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return
        data_store_form = DataStoreForm(self, mapping, database)
        data_store_form.show()

    def data_references(self):
        """Returns a list of connection strings that are in this item as references (self.references)."""
        return self.references

    def data_files(self):
        """Return a list of files in the data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    @Slot(name="refresh")
    def refresh(self):
        """Refresh data files QTreeView.
        NOTE: Might lead to performance issues."""
        d = self.data_files()
        self._widget.populate_data_list(d)

    def find_file(self, fname, visited_items):
        """Search for filename in data and return the path if found."""
        # logging.debug("Looking for file {0} in DS {1}.".format(fname, self.name))
        if self in visited_items:
            logging.debug("Infinite loop detected while visiting {0}.".format(self.name))
            return None
        if fname in self.data_files():
            # logging.debug("{0} found in DS {1}".format(fname, self.name))
            self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
            path = os.path.join(self.data_dir, fname)
            return path
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
