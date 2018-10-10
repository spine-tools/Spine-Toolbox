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
Classes for handling models in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: P. Savolainen (VTT)
:date:   23.1.2018
"""

import time  # just to measure loading time and sqlalchemy ORM performance
import logging
import os
from collections import Counter
from PySide2.QtCore import Qt, Signal, Slot, QModelIndex, QAbstractListModel, QAbstractTableModel,\
    QSortFilterProxyModel
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QFont, QIcon, QPixmap
from PySide2.QtWidgets import QMessageBox
from config import INVALID_CHARS, TOOL_OUTPUT_DIR
from helpers import rename_dir
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError


class ProjectItemModel(QStandardItemModel):
    """Class to store project items, e.g. Data Stores, Data Connections, Tools, Views."""
    def __init__(self, toolbox=None):
        super().__init__()
        self._toolbox = toolbox

    def setData(self, index, value, role=Qt.EditRole):
        """Change name of item in index to value.

        Args:
            index (QModelIndex): Item index
            value (str): New name
            role (int): Item data role to set

        Returns:
            Boolean value depending on whether the new name is accepted.
        """
        if not role == Qt.EditRole:
            return super().setData(index, value, role)
        item = self.data(index, Qt.UserRole)
        old_name = item.name
        if value.strip() == '' or value == old_name:
            return False
        # Check that new name is legal
        if any(True for x in value if x in INVALID_CHARS):
            msg = "<b>{0}</b> contains invalid characters.".format(value)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid characters", msg)
            return False
        # Check if project item with the same name already exists
        taken_names = self.return_item_names()
        if value in taken_names:
            msg = "Project item <b>{0}</b> already exists".format(value)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid name", msg)
            return False
        # Check that no existing project item short name matches the new item's short name.
        # This is to prevent two project items from using the same folder.
        new_short_name = value.lower().replace(' ', '_')
        for taken_name in taken_names:
            taken_short_name = taken_name.lower().replace(' ', '_')
            if new_short_name == taken_short_name:
                msg = "Project item using directory <b>{0}</b> already exists".format(taken_short_name)
                # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                QMessageBox.information(self._toolbox, "Invalid name", msg)
                return False
        # Get old data dir which will be renamed
        try:
            old_data_dir = item.data_dir  # Full path
        except AttributeError:
            logging.error("Item does not have a data_dir. "
                          "Make sure that class {0} creates one.".format(item.item_type))
            return False
        # Get project path from the old data dir path
        project_path = os.path.split(old_data_dir)[0]
        # Make path for new data dir
        new_data_dir = os.path.join(project_path, new_short_name)
        # Rename item project directory
        if not rename_dir(self._toolbox, old_data_dir, new_data_dir):
            return False
        # Find item from project refs list
        project_refs = self._toolbox.project_refs
        item_ref = None
        for ref in project_refs:
            if ref.name == old_name:
                ref_index = project_refs.index(ref)
                item_ref = project_refs.pop(ref_index)
                break
        # Change name for item in project ref list
        item_ref.set_name(value)
        self._toolbox.project_refs.append(item_ref)
        # Update DisplayRole of the QStardardItem in Project QTreeView
        q_item = self.find_item(old_name, Qt.MatchExactly | Qt.MatchRecursive)
        q_item.setData(value, Qt.DisplayRole)
        # Rename project item contained in the QStandardItem
        item.set_name(value)
        # Update project item directory variable
        item.data_dir = new_data_dir
        # If item is a Data Connection the QFileSystemWatcher path must be updated
        if item.item_type == "Data Connection":
            item.data_dir_watcher.removePaths(item.data_dir_watcher.directories())
            item.data_dir_watcher.addPath(item.data_dir)
        # If item is a Tool, also output_dir must be updated
        if item.item_type == "Tool":
            item.output_dir = os.path.join(item.data_dir, TOOL_OUTPUT_DIR)
        # Update name in the subwindow widget
        item.get_widget().set_name_label(value)
        # Update name item of the QGraphicsItem
        item.get_icon().update_name_item(value)
        # Change old item names in connection model headers to the new name
        header_index = self._toolbox.connection_model.find_index_in_header(old_name)
        self._toolbox.connection_model.setHeaderData(header_index, Qt.Horizontal, value)
        self._toolbox.connection_model.setHeaderData(header_index, Qt.Vertical, value)
        # Force save project
        self._toolbox.save_project()
        self._toolbox.msg_success.emit("Project item <b>{0}</b> renamed to <b>{1}</b>".format(old_name, value))
        return True

    def n_items(self, typ):
        """Returns the number of items in the project according to type.

        Args:
            typ (str): Type of item to count. "all" returns the number of items in project.
        """
        n = 0
        top_level_items = self.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            if typ == "all":
                if top_level_item.hasChildren():
                    n = n + top_level_item.rowCount()
            elif typ == "Data Stores":
                if top_level_item.data(Qt.DisplayRole) == "Data Stores":
                    n = top_level_item.rowCount()
            elif typ == "Data Connections":
                if top_level_item.data(Qt.DisplayRole) == "Data Connections":
                    n = top_level_item.rowCount()
            elif typ == "Tools":
                if top_level_item.data(Qt.DisplayRole) == "Tools":
                    n = top_level_item.rowCount()
            elif typ == "Views":
                if top_level_item.data(Qt.DisplayRole) == "Views":
                    n = top_level_item.rowCount()
            else:
                logging.error("Unknown type: {0}".format(typ))
        return n

    def new_item_index(self, category):
        """Get index where a new item is appended according to category."""
        if category == "Data Stores":
            # Return number of data stores
            return self.n_items("Data Stores") - 1
        elif category == "Data Connections":
            # Return number of data stores + data connections - 1
            return self.n_items("Data Stores") + self.n_items("Data Connections") - 1
        elif category == "Tools":
            # Return number of data stores + data connections + tools - 1
            return self.n_items("Data Stores") + self.n_items("Data Connections") + self.n_items("Tools") - 1
        elif category == "Views":
            # Return total number of items - 1
            return self.n_items("all") - 1
        else:
            logging.error("Unknown category:{0}".format(category))
            return 0

    def find_item(self, name, match_flags=Qt.MatchExactly):
        """Find item by name in project model (column 0)

        Args:
            name (str): Item name to find
            match_flags (QFlags): Or combination of Qt.MatchFlag types. Use Qt.MatchExactly | Qt.MatchRecursive
                to find project items by name.

        Returns:
            Matching QStandardItem or None if item not found or more than one item with the same name found.
        """
        found_items = self.findItems(name, match_flags, column=0)
        if len(found_items) == 0:
            # logging.debug("Item '{0}' not found in project model".format(name))
            return None
        if len(found_items) > 1:
            logging.error("More than one item with name '{0}' found".format(name))
            return None
        return found_items[0]

    def return_item_names(self):
        """Returns the names of all items in a list."""
        item_names = list()
        top_level_items = self.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            if top_level_item.hasChildren():
                n_children = top_level_item.rowCount()
                for i in range(n_children):
                    child = top_level_item.child(i, 0)
                    item_names.append(child.data(Qt.DisplayRole))
        return item_names


class ToolTemplateModel(QAbstractListModel):
    """Class to store tools that are available in a project e.g. GAMS or Julia models."""
    def __init__(self, toolbox=None):
        super().__init__()
        self._tools = list()
        self._tools.append('No Tool template')  # TODO: Try to get rid of this
        self._toolbox = toolbox

    def rowCount(self, parent=None, *args, **kwargs):
        """Must be reimplemented when subclassing. Returns
        the number of Tools in the model.

        Args:
            parent (QModelIndex): Not used (because this is a list)

        Returns:
            Number of rows (available tools) in the model
        """
        return len(self._tools)

    def data(self, index, role=None):
        """Must be reimplemented when subclassing.

        Args:
            index (QModelIndex): Requested index
            role (int): Data role

        Returns:
            Data according to requested role
        """
        if not index.isValid() or self.rowCount() == 0:
            return None
        row = index.row()
        # TODO: Try to get rid of first item (str: 'No Tool') by just returning 'No Tool' when rowCount == 1 && row==0
        if role == Qt.DisplayRole:
            if row == 0:
                return self._tools[0]
            else:
                toolname = self._tools[row].name
                return toolname
        elif role == Qt.ToolTipRole:
            if row == 0 or row >= self.rowCount():
                return ""
            else:
                return self._tools[row].def_file_path

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRow(self, tool, row=None, parent=QModelIndex(), *args, **kwargs):
        """Insert row (tool) into model.

        Args:
            tool (Tool): Tool added to the model
            row (str): Row to insert tool to
            parent (QModelIndex): Parent of child (not used)

        Returns:
            Void
        """
        if not row:
            row = self.rowCount()
        self.beginInsertRows(parent, row, row)
        self._tools.insert(row, tool)
        self.endInsertRows()

    def removeRow(self, row, parent=QModelIndex(), *args, **kwargs):
        """Remove row (tool) from model.

        Args:
            row (int): Row to remove the tool from
            parent (QModelIndex): Parent of tool on row (not used)

        Returns:
            Boolean variable
        """
        if row < 0 or row > self.rowCount():
            # logging.error("Invalid row number")
            return False
        self.beginRemoveRows(parent, row, row)
        self._tools.pop(row)
        self.endRemoveRows()
        return True

    def update_tool_template(self, tool, row):
        """Update tool template.

        Args:
            tool (ToolTemplate): new tool, to replace the old one
            row (int): Position of the tool to be updated

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self._tools[row] = tool
            return True
        except IndexError:
            return False

    def tool_template(self, row):
        """Returns tool template on given row.

        Args:
            row (int): Row of tool template

        Returns:
            ToolTemplate from tool template list
        """
        return self._tools[row]

    def find_tool_template(self, name):
        """Returns tool template with the given name.

        Args:
            name (str): Name of tool template to find
        """
        for template in self._tools:
            if isinstance(template, str):
                continue
            else:
                if name.lower() == template.name.lower():
                    return template
        return None

    def tool_template_row(self, name):
        """Returns the index (row) on which the given template lives or -1 if not found."""
        for i in range(len(self._tools)):
            if isinstance(self._tools[i], str):
                continue
            else:
                if name == self._tools[i].name:
                    return i
        return -1

    def tool_template_index(self, name):
        """Returns the index (QModelIndex) on which the given template lives or -1 if not found."""
        row = self.tool_template_row(name)
        if row == -1:
            return QModelIndex()
        return self.createIndex(row, 0)


class ConnectionModel(QAbstractTableModel):
    """Table model for storing connections between items."""

    def __init__(self, toolbox=None):
        super().__init__()
        self._toolbox = toolbox  # QMainWindow
        self.connections = []
        self.header = list()

    def flags(self, index):
        """Returns flags for table items."""
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """Number of rows in the model. This should be the same as the number of items in the project."""
        return len(self.connections)

    def columnCount(self, *args, **kwargs):
        """Number of columns in the model. This should be the same as the number of items in the project."""
        try:
            n = len(self.connections[0])
        except IndexError:
            return 0
        return n

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns header data according to given role."""
        if role == Qt.DisplayRole:
            try:
                h = self.header[section]
            except IndexError:
                return None
            return h
        else:
            return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if not role == Qt.EditRole:
            return super().setHeaderData(section, orientation, value, role)
        if orientation == Qt.Horizontal or orientation == Qt.Vertical:
            try:
                self.header[section] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except IndexError:
                return False
        return False

    def data(self, index, role):
        """Returns the data stored under the given role for the item referred to by the index.
        DisplayRole is a string "False" or "True" depending on if a Link is present.

        Args:
            index (QModelIndex): Index of item
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if not self.connections[index.row()][index.column()]:
                return "False"  # If there is no Link return "False"
            else:
                return "True"  # If a link is present return "True"
        elif role == Qt.ToolTipRole:
            row_header = self.headerData(index.row(), Qt.Vertical, Qt.DisplayRole)
            column_header = self.headerData(index.column(), Qt.Horizontal, Qt.DisplayRole)
            if row_header == column_header:
                return row_header + " (Feedback)"
            else:
                return row_header + "->" + column_header + " - " + str(index.row()) + ":" + str(index.column())
        elif role == Qt.UserRole:
            return self.connections[index.row()][index.column()]
        else:
            return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set data of single cell in table. Toggles the checkbox state at index.

        Args:
            index (QModelIndex): Index of data to edit
            value (QVariant): Value to write to index (Link instance)
            role (int): Role for editing
        """
        if not index.isValid():
            return False
        if not role == Qt.EditRole:
            return False
        self.connections[index.row()][index.column()] = value  # Should be a Link or None
        # noinspection PyUnresolvedReferences
        self.dataChanged.emit(index, index)
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.

        Args:
            row (int): Row number where new rows are inserted
            count (int): Number of inserted rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were inserted successfully, False otherwise
        """
        if row < 0 or row > self.rowCount():
            return False
        if not count == 1:
            logging.error("Insert 1 row at a time")
            return False
        # beginInsertRows(const QModelIndex & parent, int first, int last)
        self.beginInsertRows(parent, row, row)
        new_row = list()
        if self.columnCount() == 0:
            new_row.append(None)
        else:
            # noinspection PyUnusedLocal
            [new_row.append(None) for i in range(self.columnCount())]
        # Notice if insert index > rowCount(), new object is inserted to end
        self.connections.insert(row, new_row)
        self.endInsertRows()
        return True

    def insertColumns(self, column, count, parent=QModelIndex()):
        """Inserts count columns into the model before the given column.
        Items in the new column will be children of the item represented
        by the parent model index.

        Args:
            column (int): Column number where new columns are inserted
            count (int): Number of inserted columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were inserted successfully, False otherwise
        """
        if column < 0 or column > self.columnCount():
            return False
        if not count == 1:
            logging.error("Insert 1 column at a time")
            return False
        # beginInsertColumns(const QModelIndex & parent, int first, int last)
        self.beginInsertColumns(parent, column, column)
        if self.rowCount() == 1:
            # This is the feedback cell of a single item (cell already written in insertRows())
            pass
        else:
            for j in range(self.rowCount()):
                # Notice if insert index > rowCount(), new object is inserted to end
                self.connections[j].insert(column, None)
        self.endInsertColumns()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent.

        Args:
            row (int): Row number where to start removing rows
            count (int): Number of removed rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were removed successfully, False otherwise
        """
        if row < 0 or row > self.rowCount():
            return False
        if not count == 1:
            logging.error("Remove 1 row at a time")
            return False
        # beginRemoveRows(const QModelIndex & parent, int first, int last)
        self.beginRemoveRows(parent, row, row)
        # noinspection PyUnusedLocal
        removed_row = self.connections.pop(row)
        # logging.debug("{0} removed from row:{1}".format(removed_link, row))
        self.endRemoveRows()
        return True

    def removeColumns(self, column, count, parent=QModelIndex()):
        """Removes count columns starting with the given column under parent.

        Args:
            column (int): Column number where to start removing columns
            count (int): Number of removed columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were removed successfully, False otherwise
        """
        if column < 0 or column > self.columnCount():
            return False
        if not count == 1:
            logging.error("Remove 1 column at a time")
            return False
        # beginRemoveColumns(const QModelIndex & parent, int first, int last)
        self.beginRemoveColumns(parent, column, column)
        # for loop all rows and remove the column from each
        removed_column = list()  # for testing and debugging
        removing_last_column = False
        if self.columnCount() == 1:
            removing_last_column = True
        for r in self.connections:
            removed_column.append(r.pop(column))
        if removing_last_column:
            self.connections = []
        # logging.debug("{0} removed from column:{1}".format(removed_column, column))
        self.endRemoveColumns()
        return True

    def append_item(self, item, index):
        """Embiggen connections table for a new item.

        Args:
            item (QStandardItem): New item
            index (int): Table row and column where the new item is appended

        Returns:
            True if successful, False otherwise
        """
        item_name = item.data(Qt.UserRole).name
        # logging.debug("Appending item {0} on row and column: {1}".format(item_name, index))
        # logging.debug("Appending {3}. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections, item_name))
        self.header.insert(index, item_name)
        if not self.insertRows(index, 1, parent=QModelIndex()):
            return False
        if not self.insertColumns(index, 1, parent=QModelIndex()):
            return False
        # logging.debug("After append. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections))
        return True

    def remove_item(self, item):
        """Remove project item from connections table.

        Args:
            item: Removed item

        Returns:
            True if successful, False otherwise
        """
        item_name = item.data(Qt.UserRole).name
        try:
            item_index = self.header.index(item_name)
        except ValueError:
            logging.error("{0} not found in connection table header list".format(item_name))
            return False
        # logging.debug("Removing {3}. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections, item_name))
        if not self.removeRows(item_index, 1, parent=QModelIndex()):
            return False
        if not self.removeColumns(item_index, 1, parent=QModelIndex()):
            return False
        self.header.remove(item_name)
        # logging.debug("After remove. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections))
        return True

    def output_items(self, name):
        """Returns a list of input items for the given item."""
        item_row = self.header.index(name)  # Row or column of item in the model
        output_items = list()
        for column in range(self.columnCount()):
            a = self.connections[item_row][column]
            # logging.debug("row:{0} column:{1} is {2}".format(item_row, column, a))
            if a:
                # append the name of output item to list
                output_items.append(self.header[column])
        return output_items

    def input_items(self, name):
        """Returns a list of output items for the given item."""
        item_column = self.header.index(name)  # Row or column of item in the model
        input_items = list()
        for row in range(self.rowCount()):
            a = self.connections[row][item_column]
            # logging.debug("row:{0} column:{1} is {2}".format(row, item_column, a))
            if a:
                # append the name of input item to list
                input_items.append(self.header[row])
        return input_items

    def get_connections(self):
        """Returns the internal data structure of the model."""
        return self.connections

    def connected_links(self, name):
        """Returns a list of connected links for the given item"""
        item_row = self.header.index(name)  # Row or column of item in the model
        row = self.connections[item_row]
        column = [self.connections[i][item_row] for i in range(self.rowCount()) if i != item_row]
        links = [x for x in row if x]
        links.extend([x for x in column if x])
        return links

    def reset_model(self, connection_table):
        """Reset model. Used in replacing the current model
        with a boolean table that represents connections.
        Overwrites the current model with a True or False
        (boolean) table that is read from a project save
        file (.json). This table is updated by restore_links()
        method to add Link instances to True cells and Nones
        to False cells."""
        if not connection_table:
            return
        # logging.debug("resetting model to:\n{0}".format(connection_table))
        self.beginResetModel()
        self.connections = connection_table
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(top_left, bottom_right)

    def find_index_in_header(self, name):
        """Returns the row or column (row==column) of the header item with the given text (item name)."""
        return self.header.index(name)

    def link(self, row, column):
        # TODO: Modify or remove this
        """Returns Link instance stored on row and column."""
        try:
            return self.connections[row][column]
        except IndexError:
            logging.error("IndexError in link()")
            return False


class MinimalTableModel(QAbstractTableModel):
    """Table model for outlining simple tabular data."""

    row_with_data_inserted = Signal(QModelIndex, int, name="row_with_data_inserted")

    def __init__(self, toolbox=None):
        """Initialize class"""
        super().__init__()
        self._toolbox = toolbox  # QMainWindow
        self._data = list()
        self._flags = list()
        self.default_flags = Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self.header = list()
        self.can_grow = False

    def clear(self):
        self.beginResetModel()
        self._data = list()
        self.endResetModel()

    def flags(self, index):
        """Returns flags for table items."""
        if not index.isValid():
            return Qt.NoItemFlags
        return self._flags[index.row()][index.column()]

    def set_flags(self, index, flags):
        """set flags for given index."""
        if not index.isValid():
            return False
        try:
            self._flags[index.row()][index.column()] = flags
            return True
        except IndexError:
            return False

    def rowCount(self, *args, **kwargs):
        """Number of rows in the model."""
        return len(self._data)

    def columnCount(self, *args, **kwargs):
        """Number of columns in the model."""
        return len(self.header)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Get headers."""
        if orientation == Qt.Horizontal:
            try:
                return self.header[section][role]
            except IndexError:
                return None
            except KeyError:
                return None
        elif orientation == Qt.Vertical:
            if role != Qt.DisplayRole:
                return None
            return section + 1

    def set_horizontal_header_labels(self, labels):
        """Set horizontal header labels."""
        if not labels:
            return
        self.header = list()
        for j, value in enumerate(labels):
            if j >= self.columnCount():
                self.header.append({})
            # self.setHeaderData(j, Qt.Horizontal, value, role=Qt.EditRole)
            self.header[j][Qt.DisplayRole] = value
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(labels) - 1)

    def insert_horizontal_header_labels(self, section, labels):
        """Insert horizontal header labels at the given section."""
        if not labels:
            return
        for j, value in enumerate(labels):
            if section + j >= self.columnCount():
                self.header.append({})
            else:
                self.header.insert(section + j, {})
            self.header[section + j][Qt.DisplayRole] = value
        self.headerDataChanged.emit(Qt.Horizontal, section, section + len(labels))

    def horizontal_header_labels(self):
        return [self.headerData(section, Qt.Horizontal, Qt.DisplayRole) for section in range(self.columnCount())]

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if orientation == Qt.Horizontal:
            try:
                self.header[section][role] = value
                if role == Qt.EditRole:
                    self.header[section][Qt.DisplayRole] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except IndexError:
                return False
        return False

    def index(self, row, column, parent=QModelIndex()):
        if row is None or column is None:
            return QModelIndex()
        if self.can_grow:
            last_row = self.rowCount(parent) - 1
            last_column = self.columnCount(parent) - 1
            if row > last_row:
                for i in range(row - last_row):
                    self.insertRows(self.rowCount(parent), 1, parent)
            if column > last_column:
                for j in range(column - last_column):
                    self.insertColumns(self.columnCount(parent), 1, parent)
        return super().index(row, column, parent)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index.

        Args:
            index (QModelIndex): Index of item
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not index.isValid():
            return None
        try:
            return self._data[index.row()][index.column()][role]
        except IndexError:
            logging.debug(index)
            return None
        except KeyError:
            return None

    def row_data(self, row, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the given row.

        Args:
            row (int): Item row
            role (int): Data role

        Returns:
            Row data for given role.
        """
        if not 0 <= row < self.rowCount():
            return None
        return [self.data(self.index(row, column), role) for column in range(self.columnCount())]

    def column_data(self, column, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the given column.

        Args:
            column (int): Item column
            role (int): Data role

        Returns:
            Column data for given role.
        """
        if not 0 <= column < self.columnCount():
            return None
        return [self.data(self.index(row, column), role) for row in range(self.rowCount())]

    def model_data(self, role=Qt.DisplayRole):
        """Returns the data stored under the given role in the entire model.

        Args:
            role (int): Data role

        Returns:
            Model data for given role.
        """
        return [self.row_data(row, role) for row in range(self.rowCount())]

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        roles = [role]
        self._data[index.row()][index.column()][role] = value
        if role == Qt.EditRole:
            self._data[index.row()][index.column()][Qt.DisplayRole] = value
            roles.append(Qt.DisplayRole)
        self.dataChanged.emit(index, index, roles)
        return True

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes."""
        if not indexes:
            return
        if len(indexes) != len(data):
            return
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            self._data[index.row()][index.column()][Qt.EditRole] = data[k]
            self._data[index.row()][index.column()][Qt.DisplayRole] = data[k]
        # TODO: This below assumes some nice ordering in the indexes list. Can we do better?
        # Maybe just emit data changed for the entire model??
        self.dataChanged.emit(indexes[0], indexes[-1], [Qt.EditRole, Qt.DisplayRole])

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.

        Args:
            row (int): Row number where new rows are inserted
            count (int): Number of inserted rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were inserted successfully, False otherwise
        """
        if row < 0 or row > self.rowCount():
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            if self.columnCount() == 0:
                new_row = [{}]
                new_flags_row = [self.default_flags]
            else:
                new_row = [{} for j in range(self.columnCount())]
                new_flags_row = [self.default_flags for j in range(self.columnCount())]
            # Notice if insert index > rowCount(), new object is inserted to end
            self._data.insert(row + i, new_row)
            self._flags.insert(row + i, new_flags_row)
        self.endInsertRows()
        return True

    def insertColumns(self, column, count, parent=QModelIndex()):
        """Inserts count columns into the model before the given column.
        Items in the new column will be children of the item represented
        by the parent model index.

        Args:
            column (int): Column number where new columns are inserted
            count (int): Number of inserted columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were inserted successfully, False otherwise
        """
        if column < 0 or column > self.columnCount():
            return False
        self.beginInsertColumns(parent, column, column + count - 1)
        for j in range(count):
            for i in range(self.rowCount()):
                # Notice if insert index > rowCount(), new object is inserted to end
                self._data[i].insert(column + j, {})
                self._flags[i].insert(column + j, self.default_flags)
        self.endInsertColumns()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent.

        Args:
            row (int): Row number where to start removing rows
            count (int): Number of removed rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were removed successfully, False otherwise
        """
        if row < 0 or row >= self.rowCount():
            return False
        if not count == 1:
            logging.error("Remove 1 row at a time")
            return False
        self.beginRemoveRows(parent, row, row)
        removed_data_row = self._data.pop(row)
        removed_flags_data_row = self._flags.pop(row)
        self.endRemoveRows()
        return True

    def removeColumns(self, column, count, parent=QModelIndex()):
        """Removes count columns starting with the given column under parent.

        Args:
            column (int): Column number where to start removing columns
            count (int): Number of removed columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were removed successfully, False otherwise
        """
        if column < 0 or column >= self.columnCount():
            return False
        if not count == 1:
            logging.error("Remove 1 column at a time")
            return False
        self.beginRemoveColumns(parent, column, column)
        # for loop all rows and remove the column from each
        removed_data_column = list()  # for testing and debugging
        removed_flags_column = list()  # for testing and debugging
        removing_last_column = False
        if self.columnCount() == 1:
            removing_last_column = True
        for r in self._data:
            removed_data_column.append(r.pop(column))
        for r in self._flags:
            removed_flags_column.append(r.pop(column))
        if removing_last_column:
            self._data = []
            self._flags = []
        # logging.debug("{0} removed from column:{1}".format(removed_column, column))
        self.endRemoveColumns()
        return True

    def batch_remove_rows(self, row_set, parent=QModelIndex()):
        """Removes a set of rows under parent.

        Args:
            row_set (set): Set of integer row numbers to remove
            parent (QModelIndex): Parent index

        Returns:
            True if rows were removed successfully, False otherwise
        """
        try:
            first = min(row_set)
            last = max(row_set)
        except ValueError:
            return False
        if first < 0 or last >= self.rowCount():
            return False
        self.beginRemoveRows(parent, first, last)
        for row in reversed(list(row_set)):
            removed_data_row = self._data.pop(row)
            removed_flags_data_row = self._flags.pop(row)
        self.endRemoveRows()
        return True

    def reset_model(self, new_data=None):
        """Reset model."""
        self.beginResetModel()
        self._data = list()
        self._flags = list()
        if new_data:
            for line in new_data:
                new_row = list()
                new_flags_row = list()
                for value in line:
                    new_dict = {
                        Qt.EditRole: value,
                        Qt.DisplayRole: value
                    }
                    new_row.append(new_dict)
                    new_flags_row.append(self.default_flags)
                self._data.append(new_row)
                self._flags.append(new_flags_row)
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.EditRole])
        self.endResetModel()


class ObjectTreeModel(QStandardItemModel):
    """A class to hold Spine data structure in a treeview."""

    def __init__(self, data_store_form):
        """Initialize class"""
        super().__init__(data_store_form)
        self.db_map = data_store_form.db_map
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.ForegroundRole:
            item_type = index.data(Qt.UserRole)
            if item_type.endswith('class') and not self.hasChildren(index):
                return QBrush(Qt.gray)
        if role == Qt.FontRole:
            item_type = index.data(Qt.UserRole)
            if item_type.endswith('class'):
                return self.bold_font
        if role == Qt.DecorationRole:
            item_type = index.data(Qt.UserRole)
            if item_type.startswith('object'):
                return self.object_icon
            elif item_type.startswith('relationship'):
                return self.relationship_icon
        return super().data(index, role)

    def forward_sweep(self, index, call=None):
        """Sweep the tree from the given index towards the leaves, and apply `call` on each."""
        if not self.hasChildren(index):
            return
        current = index
        back_to_parent = False  # True if moving back to the parent index
        while True:
            if call:
                call(current)
            if not back_to_parent:
                # Try and visit first child
                next_ = self.index(0, 0, current)
                if next_.isValid():
                    back_to_parent = False
                    current = next_
                    continue
            # Try and visit next sibling
            next_ = current.sibling(current.row() + 1, 0)
            if next_.isValid():
                back_to_parent = False
                current = next_
                continue
            # Go back to parent
            next_ = self.parent(current)
            if next_ != index:
                back_to_parent = True
                current = next_
                continue
            break

    def build_tree(self, db_name):
        """Create root item and object class items. This triggers a recursion
        that builds up the tree.
        """
        self.clear()
        object_class_list = [x for x in self.db_map.object_class_list()]
        object_list = [x for x in self.db_map.object_list()]
        wide_relationship_class_list = [x for x in self.db_map.wide_relationship_class_list()]
        wide_relationship_list = [x for x in self.db_map.wide_relationship_list()]
        root_item = QStandardItem(db_name)
        root_item.setData('root', Qt.UserRole)
        object_class_item_list = list()
        for object_class in object_class_list:
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setData('object_class', Qt.UserRole)
            object_class_item.setData(object_class._asdict(), Qt.UserRole + 1)
            object_item_list = list()
            for object_ in object_list:
                if object_.class_id != object_class.id:
                    continue
                object_item = QStandardItem(object_.name)
                object_item.setData('object', Qt.UserRole)
                object_item.setData(object_._asdict(), Qt.UserRole + 1)
                relationship_class_item_list = list()
                for wide_relationship_class in wide_relationship_class_list:
                    object_class_id_list = [int(x) for x in wide_relationship_class.object_class_id_list.split(",")]
                    if object_.class_id not in object_class_id_list:
                        continue
                    relationship_class_item = QStandardItem(wide_relationship_class.name)
                    relationship_class_item.setData('relationship_class', Qt.UserRole)
                    relationship_class_item.setData(wide_relationship_class._asdict(), Qt.UserRole + 1)
                    relationship_class_item.setData(wide_relationship_class.object_class_name_list, Qt.ToolTipRole)
                    relationship_item_list = list()
                    for wide_relationship in wide_relationship_list:
                        if wide_relationship.class_id != wide_relationship_class.id:
                            continue
                        if object_.id not in [int(x) for x in wide_relationship.object_id_list.split(",")]:
                            continue
                        relationship_item = QStandardItem(wide_relationship.object_name_list)
                        relationship_item.setData('relationship', Qt.UserRole)
                        relationship_item.setData(wide_relationship._asdict(), Qt.UserRole + 1)
                        relationship_item_list.append(relationship_item)
                    relationship_class_item.appendRows(relationship_item_list)
                    relationship_class_item_list.append(relationship_class_item)
                object_item.appendRows(relationship_class_item_list)
                object_item_list.append(object_item)
            object_class_item.appendRows(object_item_list)
            object_class_item_list.append(object_class_item)
        root_item.appendRows(object_class_item_list)
        self.appendRow(root_item)
        return root_item

    def new_object_class_item(self, object_class):
        """Returns new object class item."""
        object_class_item = QStandardItem(object_class.name)
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData(object_class._asdict(), Qt.UserRole + 1)
        return object_class_item

    def new_object_item(self, object_):
        """Returns new object item."""
        object_item = QStandardItem(object_.name)
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_._asdict(), Qt.UserRole + 1)
        relationship_class_item_list = list()
        for wide_relationship_class in self.db_map.wide_relationship_class_list(object_class_id=object_.class_id):
            relationship_class_item = self.new_relationship_class_item(wide_relationship_class, object_)
            relationship_class_item_list.append(relationship_class_item)
        object_item.appendRows(relationship_class_item_list)
        return object_item

    def new_relationship_class_item(self, wide_relationship_class, object_):
        """Returns new relationship class item."""
        relationship_class_item = QStandardItem(wide_relationship_class.name)
        relationship_class_item.setData(wide_relationship_class._asdict(), Qt.UserRole + 1)
        relationship_class_item.setData('relationship_class', Qt.UserRole)
        relationship_class_item.setData(wide_relationship_class.object_class_name_list, Qt.ToolTipRole)
        return relationship_class_item

    def new_relationship_item(self, wide_relationship):
        """Returns new relationship item."""
        relationship_item = QStandardItem(wide_relationship.object_name_list)
        relationship_item.setData('relationship', Qt.UserRole)
        relationship_item.setData(wide_relationship._asdict(), Qt.UserRole + 1)
        return relationship_item

    def add_object_class(self, object_class):
        """Add object class item to the model."""
        object_class_item = self.new_object_class_item(object_class)
        root_item = self.invisibleRootItem().child(0)
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole + 1)
            if visited_object_class['display_order'] >= object_class.display_order:
                root_item.insertRow(i, QStandardItem())
                root_item.setChild(i, 0, object_class_item)
                return
        row = root_item.rowCount()
        root_item.insertRow(row, QStandardItem())
        root_item.setChild(row, 0, object_class_item)

    def add_object(self, object_):
        """Add object item to the model."""
        # find object class item among the children of the root
        root_item = self.invisibleRootItem().child(0)
        object_class_item = None
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole + 1)
            if visited_object_class['id'] == object_.class_id:
                object_class_item = visited_object_class_item
                break
        if not object_class_item:
            logging.debug("Object class item not found in model. This is probably a bug.")
            return
        object_item = self.new_object_item(object_)
        object_class_item.appendRow(object_item)

    def add_relationship_class(self, wide_relationship_class):
        """Add relationship class."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if not visited_type == 'object':
                continue
            visited_object = visited_item.data(Qt.UserRole + 1)
            object_class_id_list = wide_relationship_class.object_class_id_list
            if visited_object['class_id'] not in [int(x) for x in object_class_id_list.split(',')]:
                continue
            relationship_class_item = self.new_relationship_class_item(wide_relationship_class, visited_object)
            visited_item.appendRow(relationship_class_item)
            # TODO: Don't add duplicate relationship class if parent and child are the same?
            # TODO: Add mirror proto relationship class?

    def add_relationship(self, wide_relationship):
        """Add relationship item to model."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if not visited_type == 'relationship_class':
                continue
            visited_relationship_class = visited_item.data(Qt.UserRole + 1)
            if not visited_relationship_class['id'] == wide_relationship.class_id:
                continue
            visited_object = visited_item.parent().data(Qt.UserRole + 1)
            object_id_list = wide_relationship.object_id_list
            if visited_object['id'] not in [int(x) for x in object_id_list.split(',')]:
                continue
            relationship_item = self.new_relationship_item(wide_relationship)
            visited_item.appendRow(relationship_item)

    def update_object_classes(self, updated_items):
        """Update object classes in the model."""
        items = self.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        updated_items_dict = {x.id: x for x in updated_items}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'object_class':
                continue
            visited_id = visited_item.data(Qt.UserRole + 1)['id']
            try:
                updated_item = updated_items_dict[visited_id]
                visited_item.setData(updated_item._asdict(), Qt.UserRole + 1)
                visited_item.setText(updated_item.name)
            except KeyError:
                continue

    def update_objects(self, updated_items):
        """Update object in the model.
        This of course means updating the object name in relationship items.
        """
        items = self.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        updated_items_dict = {x.id: x for x in updated_items}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type == 'object':
                visited_id = visited_item.data(Qt.UserRole + 1)['id']
                try:
                    updated_item = updated_items_dict[visited_id]
                    visited_item.setData(updated_item._asdict(), Qt.UserRole + 1)
                    visited_item.setText(updated_item.name)
                except KeyError:
                    continue
            elif visited_type == 'relationship':
                relationship = visited_item.data(Qt.UserRole + 1)
                object_id_list = [int(x) for x in relationship['object_id_list'].split(",")]
                object_name_list = relationship['object_name_list'].split(",")
                found = False
                for i, id in enumerate(object_id_list):
                    try:
                        updated_item = updated_items_dict[id]
                        object_name_list[i] = updated_item.name
                        found = True
                    except KeyError:
                        continue
                if found:
                    str_object_name_list = ",".join(object_name_list)
                    relationship['object_name_list'] = str_object_name_list
                    visited_item.setText(str_object_name_list)
                    visited_item.setData(relationship, Qt.UserRole + 1)

    def update_relationship_classes(self, updated_items):
        """Update relationship classes in the model."""
        items = self.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        updated_items_dict = {x.id: x for x in updated_items}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship_class':
                continue
            visited_id = visited_item.data(Qt.UserRole + 1)['id']
            try:
                updated_item = updated_items_dict[visited_id]
                visited_item.setData(updated_item._asdict(), Qt.UserRole + 1)
                visited_item.setText(updated_item.name)
            except KeyError:
                continue

    def update_relationships(self, updated_items):
        """Update relationships in the model.
        This may require moving rows if the objects in the relationship have changed."""
        items = self.findItems("*", Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        updated_items_dict = {x.id: x for x in updated_items}
        items_to_add = set()
        for visited_item in reversed(items):
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != "relationship":
                continue
            visited_id = visited_item.data(Qt.UserRole + 1)['id']
            try:
                updated_item = updated_items_dict[visited_id]
                # Handle changes in object path
                visited_object_id_list = visited_item.data(Qt.UserRole + 1)['object_id_list']
                updated_object_id_list = updated_item.object_id_list
                if visited_object_id_list != updated_object_id_list:
                    visited_index = self.indexFromItem(visited_item)
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
                    items_to_add.add(updated_item)
                else:
                    visited_item.setText(updated_item.object_name_list)
                    visited_item.setData(updated_item._asdict(), Qt.UserRole + 1)
            except KeyError:
                continue
        for item in items_to_add:
            self.add_relationship(item)

    def remove_items(self, removed_type, *removed_ids):
        """Remove all matched items and their orphans."""
        # TODO: try and remove all rows at once, if possible
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in reversed(items):
            visited_type = visited_item.data(Qt.UserRole)
            visited = visited_item.data(Qt.UserRole + 1)
            if visited_type == 'root':
                continue
            # Get visited id
            visited_id = visited['id']
            visited_index = self.indexFromItem(visited_item)
            if visited_type == removed_type and visited_id in removed_ids:
                self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object class, also remove relationship classes that involve it
            if removed_type == 'object_class' and visited_type == 'relationship_class':
                object_class_id_list = visited['object_class_id_list']
                if any([id in [int(x) for x in object_class_id_list.split(',')] for id in removed_ids]):
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object, also remove relationships that involve it
            if removed_type == 'object' and visited_type == 'relationship':
                object_id_list = visited['object_id_list']
                if any([id in [int(x) for x in object_id_list.split(',')] for id in removed_ids]):
                    self.removeRows(visited_index.row(), 1, visited_index.parent())

    def next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        if index.data(Qt.UserRole) != 'relationship':
            return None
        object_name_list = index.data(Qt.DisplayRole)
        class_id = index.data(Qt.UserRole + 1)["class_id"]
        items = [item for item in self.findItems(object_name_list, Qt.MatchExactly | Qt.MatchRecursive, column=0)
                 if item.data(Qt.UserRole + 1)["class_id"] == class_id]
        position = None
        for i, item in enumerate(items):
            if index == self.indexFromItem(item):
                position = i
                break
        if position is None:
            return None
        position = (position + 1) % len(items)
        return self.indexFromItem(items[position])


class DataStoreTableModel(MinimalTableModel):
    """A model to use with parameter and parameter value tables in DataStoreForm."""

    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self._data_store_form = data_store_form
        self.db_map = self._data_store_form.db_map
        self.fixed_columns = list()
        self.gray_brush = self._data_store_form.palette().button() if self._data_store_form else QBrush(Qt.lightGray)

    def set_fixed_columns(self, *column_names):
        """Set the fixed_column attribute from the column names given as argument."""
        header = self.horizontal_header_labels()
        self.fixed_columns = [header.index(name) for name in column_names]

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in model. Call the proper method depending on whether the row
        is a work in progress or not.
        """
        if role != Qt.EditRole:
            return super().setData(index, value, role)
        if not index.isValid():
            return False
        if self.is_work_in_progress(index.row()):
            if not self.set_wip_data(index, value):
                return False
        else:
            if not self.update_data(index, value):
                return False
        self.dataChanged.emit(index, index)
        return True

    def set_wip_data(self, index, value):
        """Set work in progress data. Update model first, then see if the database
        needs to be updated as well.
        """
        self._data[index.row()][index.column()][Qt.EditRole] = value
        self._data[index.row()][index.column()][Qt.DisplayRole] = value
        self.add_items_to_db(self.items_to_add([index]))
        return True

    def update_data(self, index, value):
        """Update non work in progess data. Try and update database first, and if
        successful update model.
        """
        if not self.update_items_in_db(self.items_to_update([index], [value])):
            return False
        self._data[index.row()][index.column()][Qt.EditRole] = value
        self._data[index.row()][index.column()][Qt.DisplayRole] = value
        return True

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes."""
        if not indexes:
            return
        if len(indexes) != len(data):
            return
        wip_indexes = list()
        wip_data = list()
        non_wip_indexes = list()
        non_wip_data = list()
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            if self.is_work_in_progress(index.row()):
                wip_indexes.append(index)
                wip_data.append(data[k])
            else:
                non_wip_indexes.append(index)
                non_wip_data.append(data[k])
        self.batch_set_wip_data(wip_indexes, wip_data)
        self.batch_update_data(non_wip_indexes, non_wip_data)
        # TODO: This below assumes some nice ordering in the indexes list. Can we do better?
        # Maybe just emit data changed for the entire model?? emit layoutChanged?
        self.dataChanged.emit(indexes[0], indexes[-1], [Qt.EditRole, Qt.DisplayRole])

    def batch_set_wip_data(self, indexes, data):
        """Batch set work in progress data. Update model first, then see if the database
        needs to be updated as well."""
        if not indexes:
            return
        if len(indexes) != len(data):
            return
        for k, index in enumerate(indexes):
            self._data[index.row()][index.column()][Qt.EditRole] = data[k]
            self._data[index.row()][index.column()][Qt.DisplayRole] = data[k]
        self.add_items_to_db(self.items_to_add(indexes))

    def batch_update_data(self, indexes, data):
        """Batch update non work in progess data. Try and update database first, and if
        successful update model.
        """
        if not indexes:
            return
        if len(indexes) != len(data):
            return
        if not self.update_items_in_db(self.items_to_update(indexes, data)):
            return
        for k, index in enumerate(indexes):
            self._data[index.row()][index.column()][Qt.EditRole] = data[k]
            self._data[index.row()][index.column()][Qt.DisplayRole] = data[k]

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        return self._flags[row][self.fixed_columns[0]] & Qt.ItemIsEditable

    def make_columns_fixed_for_rows(self, *rows):
        """Set fixed columns as not editable and paint them gray."""
        header = self.horizontal_header_labels()
        for row in rows:
            for column in self.fixed_columns:
                self._data[row][column][Qt.BackgroundRole] = self.gray_brush
                self._flags[row][column] = ~Qt.ItemIsEditable
        try:
            top_left = self.index(rows[0], self.fixed_columns[0])
            bottom_right = self.index(rows[-1], self.fixed_columns[-1])
            self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        except IndexError:
            pass

    def reset_model(self, model_data, fixed_column_names=list()):
        """Reset model while keeping the work in progress rows."""
        wip_row_list = [row for row in range(self.rowCount()) if self.is_work_in_progress(row)]
        for row in wip_row_list:
            row_data = self.row_data(row, role=Qt.DisplayRole)
            model_data.insert(row, row_data)
        super().reset_model(model_data)
        self.set_fixed_columns(*fixed_column_names)
        self.make_columns_fixed_for_rows(*[r for r in range(self.rowCount()) if r not in wip_row_list])


class ParameterModel(DataStoreTableModel):
    """A model to use with parameter tables in DataStoreForm."""

    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)

    def items_to_update(self, indexes, values):
        """Return a list of items (dict) to update in the database."""
        if not indexes:
            return
        if len(indexes) != len(values):
            return
        items_to_update = dict()
        header = self.horizontal_header_labels()
        id_column = header.index('id')
        for k, index in enumerate(indexes):
            row = index.row()
            if self.is_work_in_progress(row):
                continue
            id = index.sibling(row, id_column).data(Qt.EditRole)
            if not id:
                continue
            field_name = header[index.column()]
            if field_name == 'parameter_name':
                field_name = 'name'
            item = {"id": id, field_name: values[k]}
            items_to_update.setdefault(id, dict()).update(item)
        return list(items_to_update.values())

    def add_items_to_db(self, items_to_add):
        """Add items to database and make columns fixed if successful."""
        if not items_to_add:
            return
        try:
            # TODO: Make it flexible rather than all or nothing, but this requires updating database_api
            items = list(items_to_add.values())
            rows = list(items_to_add.keys())
            parameters = self.db_map.add_parameters(*items)
            id_column = self.horizontal_header_labels().index('id')
            for i, parameter in enumerate(parameters):
                self._data[rows[i]][id_column][Qt.EditRole] = parameter.id  # NOTE: DisplayRole not in use
            self.make_columns_fixed_for_rows(*rows)
            self._data_store_form.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new parameters."
            self._data_store_form.msg.emit(msg)
        except SpineIntegrityError as e:
            self._data_store_form.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._data_store_form.msg_error.emit(e.msg)

    def update_items_in_db(self, items_to_update):
        """Try and update parameters in database."""
        if not items_to_update:
            return False
        try:
            self.db_map.update_parameters(*items_to_update)
            self._data_store_form.set_commit_rollback_actions_enabled(True)
            msg = "Parameters successfully updated."
            self._data_store_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._data_store_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._data_store_form.msg_error.emit(e.msg)
            return False


class ParameterValueModel(DataStoreTableModel):
    """A model to use with parameter value tables in DataStoreForm."""

    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)

    def items_to_update(self, indexes, values):
        """Return a list of items (dict) to update in the database."""
        if not indexes:
            return
        if len(indexes) != len(values):
            return
        items_to_update = dict()
        header = self.horizontal_header_labels()
        id_column = header.index('id')
        for k, index in enumerate(indexes):
            row = index.row()
            if self.is_work_in_progress(row):
                continue
            id = index.sibling(row, id_column).data(Qt.EditRole)
            if not id:
                continue
            field_name = header[index.column()]
            item = {"id": id, field_name: values[k]}
            items_to_update.setdefault(id, dict()).update(item)
        return list(items_to_update.values())

    def add_items_to_db(self, items_to_add):
        """Add parameter values to database and make columns fixed if successful."""
        if not items_to_add:
            return
        try:
            items = list(items_to_add.values())
            rows = list(items_to_add.keys())
            parameter_values = self.db_map.add_parameter_values(*items)
            id_column = self.horizontal_header_labels().index('id')
            for i, parameter_value in enumerate(parameter_values):
                self._data[rows[i]][id_column][Qt.EditRole] = parameter_value.id
            self.make_columns_fixed_for_rows(*rows)
            self._data_store_form.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new parameter values."
            self._data_store_form.msg.emit(msg)
        except SpineIntegrityError as e:
            self._data_store_form.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._data_store_form.msg_error.emit(e.msg)

    def update_items_in_db(self, items_to_update):
        """Try and update parameter values in database."""
        if not items_to_update:
            return False
        try:
            self.db_map.update_parameter_values(*items_to_update)
            self._data_store_form.set_commit_rollback_actions_enabled(True)
            msg = "Parameter values successfully updated."
            self._data_store_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._data_store_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._data_store_form.msg_error.emit(e.msg)
            return False


class ObjectParameterModel(ParameterModel):
    """A model to view and edit object parameters in DataStoreForm."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)

    def init_model(self):
        """Initialize model from source database."""
        object_parameter_list = self.db_map.object_parameter_list()
        header = self.db_map.object_parameter_fields()
        self.set_horizontal_header_labels(header)
        model_data = [list(row._asdict().values()) for row in object_parameter_list]
        self.reset_model(model_data, fixed_column_names=['id', 'object_class_name'])

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type != "object_class":
            return
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        column = header_index("object_class_name")
        for row in range(self.rowCount()):
            try:
                curr_name = self._data[row][column][Qt.DisplayRole]
                new_name = names_dict[curr_name]
                self._data[row][column][Qt.EditRole] = new_name
                self._data[row][column][Qt.DisplayRole] = new_name
            except KeyError:
                continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type != "object_class":
            return
        header_index = self.horizontal_header_labels().index
        column = header_index("object_class_name")
        for row in reversed(range(self.rowCount())):
            if self._data[row][column][Qt.DisplayRole] in removed_names:
                super().removeRows(row, 1)

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        object_class_name_column = header.index('object_class_name')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        object_class_dict = {x.name: x.id for x in self.db_map.object_class_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            if not parameter_name:
                continue
            try:
                object_class_id = object_class_dict[object_class_name]
                item = {
                    "object_class_id": object_class_id,
                    "name": parameter_name
                }
                for column in range(parameter_name_column + 1, self.columnCount()):
                    item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
                items_to_add[row] = item
            except KeyError:
                pass
        return items_to_add


class RelationshipParameterModel(ParameterModel):
    """A model to view and edit relationship parameters in DataStoreForm."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)

    def init_model(self):
        """Initialize model from source database."""
        relationship_parameter_list = self.db_map.relationship_parameter_list()
        header = self.db_map.relationship_parameter_fields()
        self.set_horizontal_header_labels(header)
        model_data = [list(row._asdict().values()) for row in relationship_parameter_list]
        self.reset_model(model_data, fixed_column_names=['id', 'relationship_class_name', 'object_class_name_list'])

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("relationship_class", "object_class"):
            return
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        if renamed_type == "relationship_class":
            column = header_index("relationship_class_name")
            for row in range(self.rowCount()):
                try:
                    curr_name = self._data[row][column][Qt.DisplayRole]
                    new_name = names_dict[curr_name]
                    self._data[row][column][Qt.EditRole] = new_name
                    self._data[row][column][Qt.DisplayRole] = new_name
                except KeyError:
                    continue
        elif renamed_type == "object_class":
            column = header_index("object_class_name_list")
            for row in range(self.rowCount()):
                object_class_name_list = self.index(row, column).data(Qt.DisplayRole).split(",")
                for i, object_class_name in enumerate(object_class_name_list):
                    try:
                        object_class_name_list[i] = names_dict[object_class_name]
                    except KeyError:
                        continue
                self._data[row][column][Qt.EditRole] = ",".join(object_class_name_list)
                self._data[row][column][Qt.DisplayRole] = ",".join(object_class_name_list)

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("relationship_class", "object_class"):
            return
        header_index = self.horizontal_header_labels().index
        if removed_type == "relationship_class":
            column = header_index("relationship_class_name")
            for row in reversed(range(self.rowCount())):
                if self._data[row][column][Qt.DisplayRole] in removed_names:
                    super().removeRows(row, 1)
        elif removed_type == "object_class":
            column = header_index("object_class_name_list")
            for row in reversed(range(self.rowCount())):
                object_class_name_list = self.index(row, column).data(Qt.DisplayRole).split(",")
                for object_class_name in object_class_name_list:
                    if object_class_name in removed_names:
                        super().removeRows(row, 1)
                        break

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        relationship_class_name_column = header.index('relationship_class_name')
        parameter_name_column = header.index('parameter_name')
        object_class_name_list_column = header.index('object_class_name_list')
        # Query db and build ad-hoc dicts
        relationship_class_dict = {x.name: {'id': x.id, 'object_class_name_list': x.object_class_name_list}
                                   for x in self.db_map.wide_relationship_class_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            object_class_name_list = self.index(row, object_class_name_list_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            # Autoset the object_class_name_list if possible and needed
            if relationship_class_name and not object_class_name_list:
                try:
                    object_class_name_list = relationship_class_dict[relationship_class_name]['object_class_name_list']
                    self._data[row][object_class_name_list_column][Qt.EditRole] = object_class_name_list
                    self._data[row][object_class_name_list_column][Qt.DisplayRole] = object_class_name_list
                except KeyError:
                    pass
            if not parameter_name:
                continue
            try:
                relationship_class_id = relationship_class_dict[relationship_class_name]['id']
                item = {
                    "relationship_class_id": relationship_class_id,
                    "name": parameter_name
                }
                for column in range(parameter_name_column + 1, self.columnCount()):
                    item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
                items_to_add[row] = item
            except KeyError:
                pass
        return items_to_add


class ObjectParameterValueModel(ParameterValueModel):
    """A model to view and edit object parameter values in DataStoreForm."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)

    def init_model(self):
        """Initialize model from source database."""
        object_parameter_value_list = self.db_map.object_parameter_value_list()
        header = self.db_map.object_parameter_value_fields()
        self.set_horizontal_header_labels(header)
        model_data = [list(row._asdict().values()) for row in object_parameter_value_list]
        self.reset_model(model_data, fixed_column_names=['id', 'object_class_name', 'object_name', 'parameter_name'])

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("object_class", "object", "parameter"):
            return
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        if renamed_type == "object_class":
            column = header_index("object_class_name")
        elif renamed_type == "object":
            column = header_index("object_name")
        elif renamed_type == "parameter":
            column = header_index("parameter_name")
        for row in range(self.rowCount()):
            try:
                curr_name = self._data[row][column][Qt.DisplayRole]
                new_name = names_dict[curr_name]
                self._data[row][column][Qt.EditRole] = new_name
                self._data[row][column][Qt.DisplayRole] = new_name
            except KeyError:
                continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("object_class", "object", "parameter"):
            return
        header_index = self.horizontal_header_labels().index
        if removed_type == "object_class":
            column = header_index("object_class_name")
        elif removed_type == "object":
            column = header_index("object_name")
        elif removed_type == "parameter":
            column = header_index("parameter_name")
        for row in reversed(range(self.rowCount())):
            if self._data[row][column][Qt.DisplayRole] in removed_names:
                super().removeRows(row, 1)

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        object_class_name_column = header.index('object_class_name')
        object_name_column = header.index('object_name')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        object_class_lookup_dict = {x.id: x.name for x in self.db_map.object_class_list()}
        object_dict = {x.name: {'id': x.id, 'class_id': x.class_id} for x in self.db_map.object_list()}
        parameter_dict = {x.name: {'id': x.id, 'object_class_id': x.object_class_id}
                          for x in self.db_map.parameter_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            object_name = self.index(row, object_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            # Autoset the object_class_name if possible and needed
            if (object_name or parameter_name) and not object_class_name:
                try:
                    object_class_id = object_dict[object_name]['class_id']
                except KeyError:
                    try:
                        object_class_id = parameter_dict[parameter_name]['object_class_id']
                    except KeyError:
                        object_class_id = None
                try:
                    object_class_name = object_class_lookup_dict[object_class_id]
                    self._data[row][object_class_name_column][Qt.EditRole] = object_class_name
                    self._data[row][object_class_name_column][Qt.DisplayRole] = object_class_name
                except KeyError:
                    pass
            try:
                object_id = object_dict[object_name]['id']
                parameter_id = parameter_dict[parameter_name]['id']
                item = {
                    "object_id": object_id,
                    "parameter_id": parameter_id
                }
                for column in range(parameter_name_column + 1, self.columnCount()):
                    item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
                items_to_add[row] = item
            except KeyError:
                pass
        return items_to_add


class RelationshipParameterValueModel(ParameterValueModel):
    """A model to view and edit relationship parameter values in DataStoreForm."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.object_name_header = list()

    def init_model(self):
        """Initialize model from source database."""
        relationship_parameter_value_list = self.db_map.relationship_parameter_value_list()
        # Compute header labels: split single 'object_name_list' column into several 'object_name' columns
        header = self.db_map.relationship_parameter_value_fields()
        relationship_class_list = self.db_map.wide_relationship_class_list()
        max_dim_count = max(
            [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=1)
        self.object_name_header = ["object_name_" + str(i + 1) for i in range(max_dim_count)]
        object_name_list_index = header.index("object_name_list")
        header.pop(object_name_list_index)
        for i, x in enumerate(self.object_name_header):
            header.insert(object_name_list_index + i, x)
        self.set_horizontal_header_labels(header)
        # Compute model data: split single 'object_name_list' value into several 'object_name' values
        model_data = list()
        for row in relationship_parameter_value_list:
            row_values_list = list(row._asdict().values())
            object_name_list = row_values_list.pop(object_name_list_index).split(',')
            for i in range(max_dim_count):
                try:
                    value = object_name_list[i]
                except IndexError:
                    value = None
                row_values_list.insert(object_name_list_index + i, value)
            model_data.append(row_values_list)
        fixed_column_names = ['id', 'relationship_class_name', *self.object_name_header, 'parameter_name']
        self.reset_model(model_data, fixed_column_names=fixed_column_names)

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("relationship_class", "object", "parameter"):
            return
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        if renamed_type == "object":
            columns = [header_index(x) for x in self.object_name_header]
            for row in range(self.rowCount()):
                for column in columns:
                    try:
                        curr_name = self._data[row][column][Qt.DisplayRole]
                        new_name = names_dict[curr_name]
                        self._data[row][column][Qt.EditRole] = new_name
                        self._data[row][column][Qt.DisplayRole] = new_name
                    except KeyError:
                        continue
        elif renamed_type in ("relationship_class", "parameter"):
            if renamed_type in "relationship_class":
                column = header_index("relationship_class_name")
            elif renamed_type in "parameter":
                column = header_index("parameter_name")
            for row in range(self.rowCount()):
                try:
                    curr_name = self._data[row][column][Qt.DisplayRole]
                    new_name = names_dict[curr_name]
                    self._data[row][column][Qt.EditRole] = new_name
                    self._data[row][column][Qt.DisplayRole] = new_name
                except KeyError:
                    continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("relationship_class", "object", "parameter"):
            return
        header_index = self.horizontal_header_labels().index
        if removed_type == "object":
            columns = [header_index(x) for x in self.object_name_header]
            for row in reversed(range(self.rowCount())):
                for column in columns:
                    if self._data[row][column][Qt.DisplayRole] in removed_names:
                        super().removeRows(row, 1)
                        break
        elif removed_type in ("relationship_class", "parameter"):
            if removed_type in "relationship_class":
                column = header_index("relationship_class_name")
            elif removed_type in "parameter":
                column = header_index("parameter_name")
            for row in reversed(range(self.rowCount())):
                if self._data[row][column][Qt.DisplayRole] in removed_names:
                    super().removeRows(row, 1)

    def extend_object_name_header(self, max_dim_count):
        """Extend object name header to fit new max dimension count."""
        curr_dim_count = len(self.object_name_header)
        object_name_header_ext = ["object_name_" + str(i + 1) for i in range(curr_dim_count, max_dim_count)]
        if object_name_header_ext:
            header = self.horizontal_header_labels()
            section = header.index(self.object_name_header[-1]) + 1
            self.insertColumns(section, len(object_name_header_ext))
            self.insert_horizontal_header_labels(section, object_name_header_ext)
            self.object_name_header.extend(object_name_header_ext)

    def set_wip_data(self, index, value):
        """Set work in progress data. Update model first, then see if the database
        needs to be updated as well.
        """
        self._data[index.row()][index.column()][Qt.EditRole] = value
        self._data[index.row()][index.column()][Qt.DisplayRole] = value
        relationships_on_the_fly = self.relationships_on_the_fly([index])
        self.add_items_to_db(self.items_to_add([index], relationships_on_the_fly))
        return True

    def batch_set_wip_data(self, indexes, data):
        """Batch set work in progress data. Update model first, then see if the database
        needs to be updated as well."""
        if not indexes:
            return
        if len(indexes) != len(data):
            return
        for k, index in enumerate(indexes):
            self._data[index.row()][index.column()][Qt.EditRole] = data[k]
            self._data[index.row()][index.column()][Qt.DisplayRole] = data[k]
        relationships_on_the_fly = self.relationships_on_the_fly(indexes)
        self.add_items_to_db(self.items_to_add(indexes, relationships_on_the_fly))

    def relationships_on_the_fly(self, indexes):
        """Return a dict of row (int) to relationship items (KeyedTuple),
        either retrieved or added on the fly.
        """
        relationships_on_the_fly = dict()
        relationships_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        relationship_class_name_column = header.index('relationship_class_name')
        object_name_1_column = header.index('object_name_1')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        relationship_class_lookup_dict = {x.id: x.name for x in self.db_map.wide_relationship_class_list()}
        relationship_class_dict = {x.name: {'id': x.id, 'object_class_id_list': x.object_class_id_list}
                                   for x in self.db_map.wide_relationship_class_list()}
        parameter_dict = {x.name: {'id': x.id, 'relationship_class_id': x.relationship_class_id}
                          for x in self.db_map.parameter_list()}
        relationship_dict = {x.id: (x.class_id, [int(y) for y in x.object_id_list.split(",")])
                             for x in self.db_map.wide_relationship_list()}
        object_dict = {x.name: x.id for x in self.db_map.object_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            # Autoset the relationship_class_name if possible and needed
            if parameter_name and not relationship_class_name:
                try:
                    relationship_class_id = parameter_dict[parameter_name]['relationship_class_id']
                    try:
                        relationship_class_name = relationship_class_lookup_dict[relationship_class_id]
                        self._data[row][relationship_class_name_column][Qt.EditRole] = relationship_class_name
                        self._data[row][relationship_class_name_column][Qt.DisplayRole] = relationship_class_name
                    except KeyError:
                        pass
                except KeyError:
                    pass
            try:
                relationship_class = relationship_class_dict[relationship_class_name]
            except KeyError:
                continue
            object_id_list = list()
            object_name_list = list()
            object_class_count = len(relationship_class['object_class_id_list'].split(','))
            for j in range(object_name_1_column, object_name_1_column + object_class_count):
                object_name = self.index(row, j).data(Qt.DisplayRole)
                try:
                    object_id = object_dict[object_name]
                    object_id_list.append(object_id)
                    object_name_list.append(object_name)
                except KeyError:
                    break
            if len(object_id_list) < object_class_count or len(object_name_list) < object_class_count:
                continue
            try:
                value = (relationship_class['id'], object_id_list)
                index = list(relationship_dict.values()).index(value)
                relationship_id = list(relationship_dict.keys())[index]
                relationships_on_the_fly[row] = relationship_id
                continue
            except ValueError:  # (relationship_class_id, object_id_list) not found in relationship_dict
                relationship_name = relationship_class_name + "_" + "__".join(object_name_list)
                relationship = {
                    "name": relationship_name,
                    "object_id_list": object_id_list,
                    "class_id": relationship_class['id']
                }
                relationships_to_add[row] = relationship
        relationships_on_the_fly.update(self.new_relationships(relationships_to_add))
        return relationships_on_the_fly

    def new_relationships(self, relationships_to_add):
        """Add relationships to database on the fly."""
        if not relationships_to_add:
            return {}
        try:
            items = list(relationships_to_add.values())
            rows = list(relationships_to_add.keys())
            relationships = self.db_map.add_wide_relationships(*items)
            msg = "Successfully added new relationships on the fly."
            self._data_store_form.msg.emit(msg)
            return dict(zip(rows, [x.id for x in relationships]))
        except SpineIntegrityError as e:
            self._data_store_form.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._data_store_form.msg_error.emit(e.msg)

    def items_to_add(self, indexes, relationships_on_the_fly):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        parameter_dict = {x.name: x.id for x in self.db_map.parameter_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            try:
                relationship_id = relationships_on_the_fly[row]
                parameter_id = parameter_dict[parameter_name]
                item = {
                    "relationship_id": relationship_id,
                    "parameter_id": parameter_id
                }
                for column in range(parameter_name_column + 1, self.columnCount()):
                    item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
                items_to_add[row] = item
            except KeyError:
                pass
        return items_to_add


class AutoFilterProxy(QSortFilterProxyModel):
    """A custom sort filter proxy model which implementes a autofilter mechanism."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.header_index = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.italic_font = QFont()
        self.italic_font.setItalic(True)
        self.rule_dict = dict()
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.filter_is_valid = True  # Set it to False when filter needs to be applied

    def setSourceModel(self, source_model):
        super().setSourceModel(source_model)
        source_model.headerDataChanged.connect(self.receive_header_data_changed)

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        if orientation == Qt.Horizontal:
            self.header_index = self.sourceModel().horizontal_header_labels().index

    def batch_set_data(self, proxy_indexes, values):
        source_indexes = [self.mapToSource(ind) for ind in proxy_indexes]
        self.sourceModel().batch_set_data(source_indexes, values)

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        return self.sourceModel().is_work_in_progress(self.map_row_to_source(row))

    def map_row_to_source(self, row):
        return self.mapToSource(self.index(row, 0)).row()

    def autofilter_values(self, column):
        """Return values for the autofilter menu of `column`."""
        values = set()
        source_model = self.sourceModel()
        data = source_model._data
        for source_row in range(source_model.rowCount()):
            # Skip values rejected by filter if rwo it's not wip
            if not source_model.is_work_in_progress(source_row) \
                    and not self.filter_accepts_row(source_row, QModelIndex()):
                continue
            # Skip values rejected by autofilters from *other* columns
            if not self.autofilter_accepts_row(source_row, QModelIndex(), skip_source_column=[column]):
                continue
            try:
                value = data[source_row][column][Qt.DisplayRole]
            except KeyError:
                value = ""
            if value is None:
                value = ""
            values.add(value)
        # Get values currently filtered in this column
        try:
            filtered_values = self.rule_dict[column]
        except KeyError:
            filtered_values = set()
        return values, filtered_values

    def add_rule(self, **kwargs):
        """Add positive rules by taking the kwargs as individual statements (key = value).
        Positive rules trigger a violation if met."""
        self.filter_is_valid = False
        for key, value in kwargs.items():
            source_column = self.header_index(key)
            self.rule_dict[source_column] = value
        if value:
            self.sourceModel().setHeaderData(source_column, Qt.Horizontal, self.italic_font, Qt.FontRole)
        else:
            self.sourceModel().setHeaderData(source_column, Qt.Horizontal, None, Qt.FontRole)

    def autofilter_accepts_row(self, source_row, source_parent, skip_source_column=list()):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        All rules need to pass.
        """
        for source_column, value in self.rule_dict.items():
            if source_column in skip_source_column:
                continue
            try:
                data = self.sourceModel()._data[source_row][source_column][self.filterRole()]
            except KeyError:
                data = ""
            if data == None:
                data = ""
            if data in value:
                return False
        return True

    def filter_accepts_row(self, source_row, source_parent):
        """Reimplement this method in subclasses."""
        return True

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false."""
        if not self.autofilter_accepts_row(source_row, source_parent):
            return False
        if self.sourceModel().is_work_in_progress(source_row):
            return True
        return self.filter_accepts_row(source_row, source_parent)

    def apply_filter(self):
        """Trigger filtering."""
        if self.filter_is_valid:
            return
        self.layoutAboutToBeChanged.emit()
        self.invalidateFilter()
        self.layoutChanged.emit()
        self.filter_is_valid = True

    def clear_autofilter(self):
        """Clear all rules."""
        for column in self.rule_dict:
            self.sourceModel().setHeaderData(column, Qt.Horizontal, None, Qt.FontRole)
        self.rule_dict = dict()


class ObjectParameterProxy(AutoFilterProxy):
    """"""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.object_class_name = None
        self.object_class_name_column = None
        self.bold_object_class_name_rows = set()

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_class_name_column = self.header_index("object_class_name")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept rows."""
        row_data = self.sourceModel()._data[source_row]
        if self.object_class_name is not None:
            try:
                object_class_name = row_data[self.object_class_name_column][self.filterRole()]
            except KeyError:
                object_class_name = None
            if object_class_name != self.object_class_name:
                return False
            row_data[self.object_class_name_column][Qt.FontRole] = self.bold_font
            self.bold_object_class_name_rows.add(source_row)
        return True

    def set_object_class_name(self, name):
        if name == self.object_class_name:
            return
        self.object_class_name = name
        self.filter_is_valid = False
        self.clear_autofilter()
        data = self.sourceModel()._data
        for row in self.bold_object_class_name_rows:
            data[row][self.object_class_name_column][Qt.FontRole] = None
        self.bold_object_class_name_rows = set()


class ObjectParameterValueProxy(ObjectParameterProxy):
    """"""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.object_name = None
        self.object_name_column = None
        self.bold_object_name_rows = set()

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_name_column = self.header_index("object_name")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept rows."""
        if not super().filter_accepts_row(source_row, source_parent):
            return False
        row_data = self.sourceModel()._data[source_row]
        if self.object_name is not None:
            try:
                object_name = row_data[self.object_name_column][self.filterRole()]
            except KeyError:
                object_name = None
            if object_name != self.object_name:
                return False
            row_data[self.object_name_column][Qt.FontRole] = self.bold_font
            self.bold_object_name_rows.add(source_row)
        return True

    def set_object_name(self, name):
        if name == self.object_name:
            return
        self.object_name = name
        self.filter_is_valid = False
        self.clear_autofilter()
        data = self.sourceModel()._data
        for row in self.bold_object_name_rows:
            data[row][self.object_name_column][Qt.FontRole] = None
        self.bold_object_name_rows = set()


class RelationshipParameterProxy(AutoFilterProxy):
    """"""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.relationship_class_name_list = None
        self.relationship_class_name_column = None
        self.bold_relationship_class_name_rows = set()

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.relationship_class_name_column = self.header_index("relationship_class_name")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept row."""
        row_data = self.sourceModel()._data[source_row]
        if self.relationship_class_name_list is not None:
            try:
                relationship_class_name = row_data[self.relationship_class_name_column][self.filterRole()]
            except KeyError:
                relationship_class_name = None
            if relationship_class_name not in self.relationship_class_name_list:
                return False
            row_data[self.relationship_class_name_column][Qt.FontRole] = self.bold_font
            self.bold_relationship_class_name_rows.add(source_row)
        return True

    def set_relationship_class_name_list(self, name_list):
        if name_list == self.relationship_class_name_list:
            return
        self.relationship_class_name_list = name_list
        self.filter_is_valid = False
        self.clear_autofilter()
        data = self.sourceModel()._data
        for row in self.bold_relationship_class_name_rows:
            data[row][self.relationship_class_name_column][Qt.FontRole] = None
        self.bold_relationship_class_name_rows = set()


class RelationshipParameterValueProxy(RelationshipParameterProxy):
    """"""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self.object_name_list = None
        self.object_name_columns = list()
        self.bold_object_name_list_rows = set()
        self.object_count = 0

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_name_columns = [self.header_index(x) for x in self.sourceModel().object_name_header]

    def filter_accepts_row(self, source_row, source_parent):
        """Accept row."""
        if not super().filter_accepts_row(source_row, source_parent):
            return False
        # Determine object_name_list for this row
        row_data = self.sourceModel()._data[source_row]
        object_name_list = list()
        for j in self.object_name_columns:
            try:
                object_name = row_data[j][self.filterRole()]
            except KeyError:
                break
            if not object_name:
                break
            object_name_list.append(object_name)
        # Now check filter
        if self.object_name_list is not None:
            if len(self.object_name_list) == 1:
                found = False
                for j, object_name in enumerate(object_name_list):
                    if self.object_name_list[0] == object_name:
                        row_data[self.object_name_columns[0] + j][Qt.FontRole] = self.bold_font
                        self.bold_object_name_list_rows.add(source_row)
                        found = True
                if not found:
                    return False
            elif len(self.object_name_list) > 1:
                if self.object_name_list != object_name_list:
                    return False
                for j in range(len(object_name_list)):
                    row_data[self.object_name_columns[0] + j][Qt.FontRole] = self.bold_font
                self.bold_object_name_list_rows.add(source_row)
        # If this row passes, update the object count
        self.object_count = max(self.object_count, len(object_name_list))
        return True

    def set_object_name_list(self, name_list):
        self.object_count = 0
        if name_list == self.object_name_list:
            return
        self.object_name_list = name_list
        self.filter_is_valid = False
        self.clear_autofilter()
        data = self.sourceModel()._data
        for row in self.bold_object_name_list_rows:
            for j in self.object_name_columns:
                data[row][j][Qt.FontRole] = None
        self.bold_object_name_list_rows = set()


class DatapackageResourcesModel(QStandardItemModel):
    """A class to hold datapackage resources and show them in a tableview."""
    def __init__(self, spine_datapackage_widget=None):
        """Initialize class"""
        super().__init__(spine_datapackage_widget)
        self.datapackage = None
        self.setHorizontalHeaderLabels(["name", "source"])
        self.ok_icon = QIcon(QPixmap(":/icons/ok.png"))
        self.nok_icon = QIcon(QPixmap(":/icons/nok.png"))

    def reset_model(self, datapackage):
        self.datapackage = datapackage
        for row, resource in enumerate(self.datapackage.resources):
            name = resource.name
            source = os.path.basename(resource.source)
            name_item = QStandardItem(name)
            source_item = QStandardItem(source)
            source_item.setFlags(~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.appendRow([name_item, source_item])

    def set_name_valid(self, index, on):
        if on:
            self.setData(index, self.ok_icon, Qt.DecorationRole)
            self.setData(index, None, Qt.ToolTipRole)
        else:
            tool_tip = ("<html>Set this resource's name to one of Spine object classes "
                       "to be able to import it.</html>")
            self.setData(index, self.nok_icon, Qt.DecorationRole)
            self.setData(index, tool_tip, Qt.ToolTipRole)


class DatapackageFieldsModel(QStandardItemModel):
    """A class to hold schema fields and show them in a treeview."""
    def __init__(self, spine_datapackage_widget=None):
        """Initialize class"""
        super().__init__(spine_datapackage_widget)
        self.schema = None

    def reset_model(self, schema):
        self.clear()
        self.setHorizontalHeaderLabels(["name", "type", "primary key?", ""])
        # NOTE: A dummy section is added at the end so primary key field is not stretched
        self.schema = schema
        for field in schema.fields:
            name = field.name
            type_ = field.type
            primary_key = True if name in schema.primary_key else False
            name_item = QStandardItem(name)
            type_item = QStandardItem(type_)
            type_item.setFlags(~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            primary_key_item = QStandardItem(primary_key)
            primary_key_item.setData(primary_key, Qt.EditRole)
            self.appendRow([name_item, type_item, primary_key_item])


class DatapackageForeignKeysModel(MinimalTableModel):
    """A class to hold schema foreign keys and show them in a treeview."""
    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__(parent)
        # TODO: Change parent (attribute name) to something else
        self.schema = None
        self.set_horizontal_header_labels(["fields", "reference resource", "reference fields"])

    def reset_model(self, schema):
        self.schema = schema
        data = list()
        for foreign_key in schema.foreign_keys:
            fields = foreign_key['fields']
            reference_resource = foreign_key['reference']['resource']
            reference_fields = foreign_key['reference']['fields']
            data.append([fields, reference_resource, reference_fields])
        super().reset_model(data)

    def insert_empty_row(self, row):
        self.insertRow(row)
        self.set_work_in_progress(row, True)
        for column in range(self.columnCount()):
            self.setData(self.index(row, column), None, Qt.EditRole)
