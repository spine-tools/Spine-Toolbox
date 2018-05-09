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
import pyodbc, sqlite3
import logging
from PySide2.QtGui import QDesktopServices
from metaobject import MetaObject
from widgets.data_store_subwindow_widget import DataStoreWidget
from widgets.data_store_widget import DataStoreForm
from PySide2.QtCore import Qt, Slot, QUrl
from widgets.add_connection_string_widget import AddConnectionStringWidget
from graphics_items import DataStoreImage
from helpers import create_dir

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
        self.references = references
        # Make directory for Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        self.databases = list() # name of imported databases
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = os.listdir(self.data_dir)
        self._widget.populate_data_list(data_files)
        self.add_connection_string_form = None
        self.data_store_form = None
        self._graphics_item = DataStoreImage(self._parent, x, y, 70, 70, self.name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.show_add_connection_string_form)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)
        self._widget.ui.treeView_data.doubleClicked.connect(self.open_file)
        self._widget.ui.toolButton_add.clicked.connect(self.import_references)

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

    @Slot(name="show_add_connection_string_form")
    def show_add_connection_string_form(self):
        """Show the form for specifying connection strings."""
        self.add_connection_string_form = AddConnectionStringWidget(self._parent, self)
        self.add_connection_string_form.show()

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
            except pyodbc.Error as e:
                self._parent.msg_error.emit("[pyodbc.Error] Import failed ({0})".format(e))
                continue
        data_files = os.listdir(self.data_dir)
        self._widget.populate_data_list(data_files)

    def import_reference(self, reference):
        """Import reference database into local SQLite file"""

        database_name = reference["DATABASE"]
        self._parent.msg.emit("Importing database <b>{0}</b>".format(database_name))
        odbc_cnxn_string = '; '.join("{!s}={!s}".format(k,v) for (k,v) in reference.items() if v)
        obdc_cnxn = pyodbc.connect(odbc_cnxn_string, autocommit=True, timeout=3)
        sqlite_cnxn = sqlite3.connect(os.path.join(self.data_dir, database_name + ".sqlite"))
        table_names = [
            'object_class', 'object',
            'relationship_class', 'relationship',
            'parameter', 'parameter_value'
        ]
        for table in table_names:
            sqlite_cnxn.cursor().execute("DROP TABLE IF EXISTS {}".format(table))
            header = list()
            pk = None
            row = obdc_cnxn.cursor().primaryKeys(table=table).fetchone()
            if row:
                pk = row.column_name
            for row in obdc_cnxn.cursor().columns(table=table):
                column = '`' + row.column_name + '`'
                if row.column_name == pk:
                    column += ' INTEGER PRIMARY KEY'
                header.append(column)
            sql = "CREATE TABLE {0} ({1})".format(table, ', '.join(header))
            sqlite_cnxn.cursor().execute(sql)
            for row in obdc_cnxn.cursor().execute("SELECT * FROM {0}".format(table)):
                sql = "INSERT INTO {0} VALUES (".format(table)\
                    + ', '.join(["?" for i in range(len(row))]) + ")"
                sqlite_cnxn.cursor().execute(sql, row)
        sqlite_cnxn.commit()
        self.databases.append(database_name)

    @Slot("QModelIndex", name="open_file")
    def open_file(self, index):
        """Open reference in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            data_file = os.listdir(self.data_dir)[index.row()]
            data_file_path = os.path.join(self.data_dir, data_file)
            self.data_store_form = DataStoreForm(self._parent, data_file_path)
            self.data_store_form.show()

    @Slot(name="show_connections")
    def show_connections(self):
        """Show connections of this item."""
        inputs = self._parent.connection_model.input_items(self.name)
        outputs = self._parent.connection_model.output_items(self.name)
        self._parent.msg.emit("<br/><b>{0}</b>".format(self.name))
        self._parent.msg.emit("Input items")
        if not inputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in inputs:
                self._parent.msg_warning.emit("{0}".format(item))
        self._parent.msg.emit("Output items")
        if not outputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in outputs:
                self._parent.msg_warning.emit("{0}".format(item))

    def data_references(self):
        """Return a list connections strings that are in this item as references (self.references)."""
        return self.references
