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
import pyodbc
import logging
from PySide2.QtGui import QStandardItemModel, QStandardItem
from metaobject import MetaObject
from widgets.data_store_subwindow_widget import DataStoreWidget
from PySide2.QtCore import Qt, Slot
from widgets.add_connection_string_widget import AddConnectionStringWidget
from widgets.Spine_data_explorer_widget import SpineDataExplorerWidget
from helpers import busy_effect

class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of references (for now it's only database references)
    """
    def __init__(self, parent, name, description, project, references):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._project = project
        self._widget = DataStoreWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        self._widget.make_header_for_data()
        # Make directory for Data Store
        self.references = references
        self.databases = list() # name of imported databases
        self.Spine_data_model = QStandardItemModel()
        self.Spine_data_model.setHorizontalHeaderItem(0, QStandardItem(name))
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Import data into project
        # self.import_references()
        #set connections buttons slot type
        self._widget.ui.toolButton_connector.is_connector = True
        self.add_connection_string_form = None
        self.Spine_data_explorer_form = None
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_explorer)
        self._widget.ui.toolButton_plus.clicked.connect(self.show_add_connection_string_form)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.toolButton_add.clicked.connect(self.import_references)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)
        self._widget.ui.toolButton_connector.clicked.connect(self.draw_links)

    @Slot(name="draw_links")
    def draw_links(self):
        self._parent.ui.graphicsView.draw_links(self._widget.ui.toolButton_connector)

    @Slot(name="open_explorer")
    def open_explorer(self):
        """Open Spine data explorer."""
        self.Spine_data_explorer_form = SpineDataExplorerWidget(self._parent, self)
        self.Spine_data_explorer_form.showMaximized()

    @Slot(name="show_add_connection_string_form")
    def show_add_connection_string_form(self):
        """Show the form for specifying connection strings."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        self.add_connection_string_form = AddConnectionStringWidget(self._parent, self)
        self.add_connection_string_form.show()

    def add_reference(self, reference):
        """Add reference to reference list and populate widget's reference list"""
        self.references.append(reference)
        self._widget.populate_reference_list(self.references)
        # import reference into project
        # self.import_reference(reference)
        # self.databases = [self.Spine_data_model.item(r).text() for r in range(self.Spine_data_model.rowCount())]
        # self._widget.populate_data_list(self.databases)

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
        # TODO: remove reference imported to the project

    @Slot(name="import_references")
    def import_references(self):
        """Import data from selected items in reference list and update database list.
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
        #self.databases = [self.Spine_data_model.item(r).text() for r in range(self.Spine_data_model.rowCount())]
        self._widget.populate_data_list(self.databases)

    @busy_effect
    def import_reference(self, reference):
        """Import database from an ODBC connection reference into Spine data model.
        Args:
            reference (str): The connection string stored as reference.
        """
        cnxn = pyodbc.connect(reference, autocommit=True, timeout=3)
        database_name = cnxn.getinfo(pyodbc.SQL_DATABASE_NAME)
        self._parent.msg.emit("Importing database <b>{0}</b>".format(database_name))
        # Create database item
        database_item = QStandardItem(database_name)
        # Create container for parameter names
        parameter_names = list()
        for row in cnxn.cursor().execute("""
            select COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS
            where TABLE_NAME = 'parameter'
            and TABLE_SCHEMA = ?
        """, database_name):
            # Get rid of `object_name`
            if row.COLUMN_NAME == 'object_name':
                continue
            parameter_names.append(row.COLUMN_NAME)
        # Store parameter names in item's UserRole
        database_item.setData(parameter_names, Qt.UserRole)
        for object_class in cnxn.cursor().execute("select * from object_class"):
            # Create object class item
            object_class_item = QStandardItem(object_class.name)
            for object_ in cnxn.cursor().execute("""
                select * from object where class_name = ?
            """, object_class.name):
                # Create object item
                object_item = QStandardItem(object_.name)
                # Create parameter container
                parameter_data = ParameterContainer()
                # Query object parameters
                for parameter in cnxn.cursor().execute("""
                    select p.*
                    from parameter as p
                    join parameter_definition as pd
                    on p.name = pd.name
                    where pd.object_class_name = ?
                    and p.object_name = ?
                """, [object_class.name, object_.name]):
                    # Get rid of `object_name`
                    parameter = [p for i,p in enumerate(parameter)\
                                if parameter.cursor_description[i][0] != 'object_name']
                    parameter_data.object.append(parameter)
                # Query relationship parameters
                for parameter in cnxn.cursor().execute("""
                    select rc.name, rc.child_class_name, r.child_object_name, p.*
                    from relationship_class as rc
                    join (relationship as r
                    left join parameter as p
                    on r.name = p.object_name)
                    on rc.name = r.class_name
                    where rc.parent_class_name = ?
                    and r.parent_object_name = ?
                """, [object_class.name, object_.name]):
                    # Get rid of `object_name`
                    parameter = [p for i,p in enumerate(parameter)\
                                if parameter.cursor_description[i][0] != 'object_name']
                    parameter_data.relationship.append(parameter)
                # Store parameter data in item's UserRole
                object_item.setData(parameter_data, Qt.UserRole)
                # Attach object to object class
                object_class_item.appendRow(object_item)
            # Attach object class to database
            database_item.appendRow(object_class_item)
        # Find items with the same name as the current database (column 0)
        items = self.Spine_data_model.findItems(database_name, Qt.MatchExactly, column=0)
        if len(items) > 0:
            positon = items[0].index().row() # insert item at the previous position
        else:
            positon = self.Spine_data_model.rowCount() # insert item at the end
            self.databases.append(database_name)
        # Remove existing items with the same name
        for item in items:
            row = item.index().row()
            if not self.Spine_data_model.removeRow(row):
                self.msg_error.emit("Removing item <b>{0}</b> from data store failed".format(database_name))
        self.Spine_data_model.insertRow(positon, database_item)

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

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

class ParameterContainer:
    """A class to store parameter data for a Spine object or relationship.
    It serves to populate models of table views in SpineDataExplorerWidgets.

    """
    def __init__(self):
        self.object = list()
        self.relationship = list()
