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
QWidget that is shown to user when opening Spine data model from a Data Store.
:author: Manuel Marin <manuelma@kth.se>
:date:   21.4.2018
"""

import os
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView
from PySide2.QtCore import Slot, Qt, SIGNAL
from ui.spine_data_explorer import Ui_Form
from config import STATUSBAR_SS, REFERENCE, TABLE, NAME, PARAMETER_HEADER, OBJECT_PARAMETER,\
    PARAMETER_AS_PARENT, PARAMETER_AS_CHILD
from models import MinimalTableModel
from widgets.custom_menus import ObjectTreeContextMenu
from helpers import busy_effect
import logging
import pyodbc

class SpineDataExplorerWidget(QWidget):
    """A widget to show and edit Spine objects in a data store."""

    def __init__(self, parent, data_store):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            data_store (DataStore): The Data Store that owns this widget
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        self._data_store = data_store
        self.object_tree_model = QStandardItemModel()
        self.object_parameter_model = MinimalTableModel()
        self.parameter_as_parent_model = MinimalTableModel()
        self.parameter_as_child_model = MinimalTableModel()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.treeView_object.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.EditKeyPressed)
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.tableView_object_parameter.setModel(self.object_parameter_model)
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_parameter_as_parent.setModel(self.parameter_as_parent_model)
        self.ui.tableView_parameter_as_parent.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_parameter_as_child.setModel(self.parameter_as_child_model)
        self.ui.tableView_parameter_as_child.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.ui.treeView_object.expandAll() # TODO: try to make this work
        # context menus
        self.object_tree_context_menu = None
        self.object_tree_update_qry_parameters = dict()
        self.object_tree_delete_qry_parameters = dict()
        self.object_tree_insert_qry_parameters = dict()
        self.connect_signals()
        self.object_tree_model_item_changed_connection = None
        self.object_tree_model_rows_removed_connection = None

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_commit.clicked.connect(self.commit_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.cancel_clicked)
        self.ui.treeView_object.clicked.connect(self.reset_parameter_models)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)

    def connect_object_tree_model_signals(self):
        """Connect signals from object_tree_model to slots"""
        logging.debug("Connecting object tree model signals")
        self.object_tree_model_item_changed_connection = \
            self.object_tree_model.itemChanged.connect(self.object_tree_model_item_changed)
        self.object_tree_model_rows_removed_connection = \
            self.object_tree_model.rowsAboutToBeRemoved.connect(self.object_tree_model_rows_removed)

    def disconnect_object_tree_model_signals(self):
        """Disconnect signals from object_tree_model if connected"""
        logging.debug("Disconnecting object tree model signals")
        if self.object_tree_model_item_changed_connection:
            self.object_tree_model.itemChanged.disconnect(self.object_tree_model_item_changed)
        if self.object_tree_model_rows_removed_connection:
            self.object_tree_model.rowsAboutToBeRemoved.disconnect(self.object_tree_model_rows_removed)

    @busy_effect
    def import_reference(self, reference):
        """Import database from an ODBC connection reference into object tree model.
        Args:
            reference (str): The connection string stored in the reference.
        """
        self.disconnect_object_tree_model_signals()
        cnxn = pyodbc.connect(reference, autocommit=True, timeout=3)
        database_name = cnxn.getinfo(pyodbc.SQL_DATABASE_NAME)
        self._parent.msg.emit("Importing database <b>{0}</b>".format(database_name))
        # Create database item
        database_item = QStandardItem(database_name)
        database_item.setData(reference, REFERENCE)
        database_item.setEditable(False)
        parameter_header = list()
        for row in cnxn.cursor().columns(table='parameter'):
            # Get rid of `object_name`
            if row.column_name == 'object_name':
                continue
            parameter_header.append(row.column_name)
        database_item.setData(parameter_header, PARAMETER_HEADER)
        for object_class in cnxn.cursor().execute("select * from object_class"):
            # Create object class item
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setData("object_class", TABLE)
            object_class_item.setData(object_class.name, NAME)
            for object_ in cnxn.cursor().execute("""
                select * from object where class_name = ?
            """, object_class.name):
                # Create object item
                object_item = QStandardItem(object_.name)
                object_item.setData("object", TABLE)
                object_item.setData(object_.name, NAME)
                # Query object parameter
                object_parameter = list()
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
                    object_parameter.append(parameter)
                object_item.setData(object_parameter, OBJECT_PARAMETER)
                # Query relationship parameters as parent
                parameter_as_parent = list()
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
                    parameter_as_parent.append(parameter)
                object_item.setData(parameter_as_parent, PARAMETER_AS_PARENT)
                # Query relationship parameter as child
                parameter_as_child = list()
                for parameter in cnxn.cursor().execute("""
                    select rc.name, rc.parent_class_name, r.parent_object_name, p.*
                    from relationship_class as rc
                    join (relationship as r
                    left join parameter as p
                    on r.name = p.object_name)
                    on rc.name = r.class_name
                    where rc.child_class_name = ?
                    and r.child_object_name = ?
                """, [object_class.name, object_.name]):
                    # Get rid of `object_name`
                    parameter = [p for i,p in enumerate(parameter)\
                                if parameter.cursor_description[i][0] != 'object_name']
                    parameter_as_child.append(parameter)
                object_item.setData(parameter_as_child, PARAMETER_AS_CHILD)
                # Attach object to object class
                object_class_item.appendRow(object_item)
            # Attach object class to database
            database_item.appendRow(object_class_item)
        # Find items with the same name as the current database (column 0)
        items = self.object_tree_model.findItems(database_name, Qt.MatchExactly, column=0)
        if len(items) > 0:
            position = items[0].index().row() # item will be inserted at the position it previously had
        else:
            position = self.object_tree_model.rowCount() # item will be inserted at the end
            self._data_store.databases.append(database_name)
        # Remove existing items with the same name
        for item in items:
            row = item.index().row()
            if not self.object_tree_model.removeRow(row):
                self._parent.msg_error.emit("Removing item <b>{0}</b> from data store failed".format(database_name))
        self.object_tree_model.insertRow(position, database_item)
        # clear commit query parameters
        self.object_tree_update_qry_parameters[reference] = dict()
        self.object_tree_delete_qry_parameters[reference] = dict()
        self.object_tree_insert_qry_parameters[reference] = dict()
        self.connect_object_tree_model_signals()
        self.ui.treeView_object.expand(database_item.index())


    @Slot("QStandardItem", name="object_tree_model_item_changed")
    def object_tree_model_item_changed(self, item):
        """Records item changes to commit to database later"""
        logging.debug("tree item changed")
        # Discover root item (ie database)
        root = item
        while root.parent():
            root = root.parent()
        reference = root.data(REFERENCE)
        table = item.data(TABLE)
        new_name = item.text()
        old_name = item.data(NAME)
        self.object_tree_update_qry_parameters.setdefault(reference, dict())
        p = {'table': table, 'new_name': new_name, 'old_name': old_name}
        # Note: the dictionary is so that only the last renaming is applied
        self.object_tree_update_qry_parameters[reference][table,old_name] = p
        logging.debug(self.object_tree_update_qry_parameters)

    @Slot("QModelIndex", "int", "int", name="object_tree_model_rows_removed")
    def object_tree_model_rows_removed(self, parent, first, last):
        """Records item deletions to commit to database later"""
        logging.debug("tree rows removed")
        parent_item = self.object_tree_model.itemFromIndex(parent)
        item = self.object_tree_model.itemFromIndex(parent.child(first, 0))
        # Discover root item (ie database)
        root = item
        while root.parent():
            root = root.parent()
        reference = root.data(REFERENCE)
        self.object_tree_delete_qry_parameters.setdefault(reference, list())
        table = item.data(TABLE)
        name = item.data(NAME)
        if table == "object_class":
            p = {'table': table, 'name': name}
            self.object_tree_delete_qry_parameters[reference].append(p)
        elif table == "object":
            object_class_name = parent_item.data(NAME)
            p = {'table': table, 'object_class_name': object_class_name, 'name': name}
            self.object_tree_delete_qry_parameters[reference].append(p)
        logging.debug(self.object_tree_delete_qry_parameters)

    @Slot(name="commit_clicked")
    def commit_clicked(self):
        """Commit model to database"""
        invisible_root = self.object_tree_model.invisibleRootItem()
        for i in range(invisible_root.rowCount()):
            root = invisible_root.child(i,0)
            reference = root.data(REFERENCE)
            try:
                cnxn = pyodbc.connect(reference, autocommit=False, timeout=3) # TODO: set autocommit=True
            except pyodbc.Error:
                self.statusbar.showMessage("Unable to connect to {}".format(reference), 3000)
                continue
            self.object_tree_delete_qry_parameters.setdefault(reference, list())
            self.object_tree_update_qry_parameters.setdefault(reference, dict())
            for row in self.object_tree_delete_qry_parameters[reference]:
                table = row['table']
                name = row['name']
                if table == 'object_class':
                    sql = "DELETE FROM object_class WHERE name = ?"
                    cnxn.cursor().execute(sql, name)
                    sql = "DELETE FROM object WHERE class_name = ?"
                    cnxn.cursor().execute(sql, name)
                elif table == 'object':
                    object_class_name = row['object_class_name']
                    sql = "DELETE FROM object WHERE class_name = ? and name = ?"
                    cnxn.cursor().execute(sql, [object_class_name, name])
            for key,value in self.object_tree_update_qry_parameters[reference].items():
                table = value['table']
                old_name = value['old_name']
                new_name = value['new_name']
                sql = "UPDATE {} SET name = ? WHERE name = ?".format(table)
                cnxn.cursor().execute(sql, new_name, old_name)
                if table == 'object_class':
                    sql = "UPDATE object SET object_class_name = ? WHERE object_class_name = ?"
                    cnxn.cursor().execute(sql, new_name, old_name)
        self.close()

    @Slot(name="cancel_clicked")
    def cancel_clicked(self):
        # TODO: undo changes to model
        self.close()

    @Slot("QModelIndex", name="reset_parameter_models")
    def reset_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected on the treeView"""
        # logging.debug("reset_parameter_models")
        item = self.object_tree_model.itemFromIndex(index)
        if item.data(TABLE) == "object":
            # Discover root item (ie database)
            root = item
            while root.parent():
                root = root.parent()
            parameter_header = root.data(PARAMETER_HEADER)
            object_parameter = item.data(OBJECT_PARAMETER)
            parameter_as_parent = item.data(PARAMETER_AS_PARENT)
            parameter_as_child = item.data(PARAMETER_AS_CHILD)
            # Set headers
            # object
            self.object_parameter_model.header.clear()
            self.object_parameter_model.header.extend(parameter_header)
            # relationship_as_parent
            self.parameter_as_parent_model.header.clear()
            self.parameter_as_parent_model.header.append("relationship_class_name")
            self.parameter_as_parent_model.header.append("child_class_name")
            self.parameter_as_parent_model.header.append("child_object_name")
            self.parameter_as_parent_model.header.extend(parameter_header)
            # relationship_as_child
            self.parameter_as_child_model.header.clear()
            self.parameter_as_child_model.header.append("relationship_class_name")
            self.parameter_as_child_model.header.append("parent_class_name")
            self.parameter_as_child_model.header.append("parent_object_name")
            self.parameter_as_child_model.header.extend(parameter_header)
            # Reset models
            self.object_parameter_model.reset_model(object_parameter)
            self.parameter_as_parent_model.reset_model(parameter_as_parent)
            self.parameter_as_child_model.reset_model(parameter_as_child)


    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for obejct tree.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, ind)#
        option = self.object_tree_context_menu.get_action()
        if option.startswith("New"):
            self.object_tree_model.insertRow(0, ind)
            self.object_tree_model.setData(ind.child(0,0), option)
            self.ui.treeView_object.setCurrentIndex(ind.child(0,0))
            self.ui.treeView_object.edit(ind.child(0,0))
        elif option == "Rename":
            self.ui.treeView_object.edit(ind)
        elif option == "Remove":
            self.object_tree_model.removeRow(ind.row(), ind.parent())
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

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
