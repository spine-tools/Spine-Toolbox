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
import getpass
import logging
from PySide2.QtGui import QDesktopServices
from metaobject import MetaObject
from widgets.data_store_subwindow_widget import DataStoreWidget
from widgets.data_store_widget import DataStoreForm
from PySide2.QtCore import Qt, Slot, QUrl, QFileSystemWatcher
from widgets.add_db_reference_widget import AddDbReferenceWidget
from graphics_items import DataStoreImage
from helpers import create_dir, busy_effect
from sqlalchemy import create_engine, Table, MetaData, select, insert

class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of references (for now it's only database references)
    """
    def __init__(self, parent, name, description, project, references, x, y):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._project = project
        self._widget = DataStoreWidget(name, self.item_type)
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
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        self.databases = list() # name of imported databases
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)
        self.add_db_reference_form = None
        self.data_store_form = None
        self._graphics_item = DataStoreImage(self._parent, x, y, 70, 70, self.name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.show_add_db_reference_form)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.treeView_data.doubleClicked.connect(self.open_file)
        self._widget.ui.treeView_references.doubleClicked.connect(self.open_reference)
        self._widget.ui.toolButton_add.clicked.connect(self.import_references)
        self.data_dir_watcher.directoryChanged.connect(self.refresh)

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in Data Connection data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._parent.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(name="show_add_db_reference_form")
    def show_add_db_reference_form(self):
        """Show the form for specifying connection strings."""
        self.add_db_reference_form = AddDbReferenceWidget(self._parent, self)
        self.add_db_reference_form.show()

    def add_reference(self, reference):
        """Add reference to reference list and populate widget's reference list"""
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
            self._parent.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._parent.msg.emit("Selected references removed")
        self._widget.populate_reference_list(self.references)

    @Slot(name="import_references")
    def import_references(self):
        """Import data from selected items in reference list into local SQLite file.
        If no item is selected then import all of them.
        """
        if not self.references:
            self._parent.msg_warning.emit("No data to import")
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
                self._parent.msg_error.emit("Import failed: {}".format(e))
                continue
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

    @busy_effect
    def import_reference(self, reference):
        """Import reference database into local SQLite file"""
        database = reference['database']
        self._parent.msg.emit("Importing database <b>{0}</b>".format(database))
        # Source
        source_url = reference['url']
        source_engine = create_engine(source_url)
        # Destination
        dest_filename = os.path.join(self.data_dir, database + ".sqlite")
        try:
            os.remove(dest_filename)
        except OSError:
            pass
        dest_url = "sqlite:///" + dest_filename
        dest_engine = create_engine(dest_url)#, echo=True)
        # Meta reflection
        meta = MetaData()
        meta.reflect(source_engine)
        meta.create_all(dest_engine)
        # Copy tables
        source_meta = MetaData(bind=source_engine)
        dest_meta = MetaData(bind=dest_engine)
        for t in meta.sorted_tables:
            source_table = Table(t, source_meta, autoload=True)
            dest_table = Table(t, dest_meta, autoload=True)
            sel = select([source_table])
            result = source_engine.execute(sel)
            values = [row for row in result]
            if values:
                ins = dest_table.insert()
                dest_engine.execute(ins, values)
        self.databases.append(database)

    @busy_effect
    @Slot("QModelIndex", name="open_file")
    def open_file(self, index):
        """Open file in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            data_file = self.data_files()[index.row()]
            data_file_path = os.path.join(self.data_dir, data_file)
            reference = {
                'database': data_file,
                'username': getpass.getuser(),
                'url': "sqlite:///" + data_file_path
            }
            self.data_store_form = DataStoreForm(self._parent, reference)
            self.data_store_form.show()

    @busy_effect
    @Slot("QModelIndex", name="open_reference")
    def open_reference(self, index):
        """Open reference in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            reference = self.references[index.row()]
            self.data_store_form = DataStoreForm(self._parent, reference)
            self.data_store_form.show()

    def data_references(self):
        """Return a list connections strings that are in this item as references (self.references)."""
        return self.references

    def data_files(self):
        """Return a list of files that are in the data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    @Slot(name="refresh")
    def refresh(self):
        """Refresh data files QTreeView.
        NOTE: Might lead to performance issues."""
        d = self.data_files()
        self._widget.populate_data_list(d)
