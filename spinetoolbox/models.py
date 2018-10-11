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
Classes for handling models in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: P. Savolainen (VTT)
:date:   23.1.2018
"""

import logging
import os
from PySide2.QtCore import Qt, Signal, QModelIndex, QAbstractListModel, QAbstractTableModel,\
    QSortFilterProxyModel, QAbstractItemModel
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QFont, QIcon, QPixmap
from PySide2.QtWidgets import QMessageBox
from config import INVALID_CHARS, TOOL_OUTPUT_DIR
from helpers import rename_dir


class ProjectItemModel(QAbstractItemModel):
    """Class to store project items, e.g. Data Stores, Data Connections, Tools, Views.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        root (ProjectItem): Root item for the project item tree
    """
    def __init__(self, toolbox, root):
        """Class constructor."""
        super().__init__()
        self._toolbox = toolbox
        self._root = root

    def root(self):
        """Returns root project item."""
        return self._root

    def rowCount(self, parent=QModelIndex()):
        """Reimplemented rowCount method.

        Args:
            parent (QModelIndex): Index of parent item whose children are counted.

        Returns:
            int: Number of children of given parent
        """
        if not parent.isValid():  # Number of category items (children of root)
            return self.root().child_count()
        elif parent.internalPointer().is_category:  # Number of project items in the category
            return parent.internalPointer().child_count()
        else:
            return 0

    def columnCount(self, parent=QModelIndex()):
        """Returns model column count."""
        return 1

    def flags(self, index):
        """Returns flags for the item at given index

        Args:
            index (QModelIndex): Flags of item at this index.
        """
        if not index.internalPointer().is_category:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index=QModelIndex()):
        """Returns index of the parent of given index.

        Args:
            index (QModelIndex): Index of item whose parent is returned

        Returns:
            QModelIndex: Index of parent item
        """
        item = self.project_item(index)
        parent_item = item.parent()
        if not parent_item:
            return QModelIndex()
        if parent_item == self.root():
            return QModelIndex()
        # logging.debug("parent_item: {0}".format(parent_item.name))
        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent=QModelIndex()):
        """Returns index of item with given row, column, and parent.

        Args:
            row (int): Item row
            column (int): Item column
            parent (QModelIndex): Parent item index

        Returns:
            QModelIndex: Item index
        """
        if row < 0 or row >= self.rowCount(parent):
            return QModelIndex()
        if column < 0 or column >= self.columnCount(parent):
            return QModelIndex()
        parent_item = self.project_item(parent)
        child = parent_item.child(row)
        if not child:
            return QModelIndex()
        else:
            return self.createIndex(row, column, child)

    def data(self, index, role=None):
        """Returns data in the given index according to requested role.

        Args:
            index (QModelIndex): Index to query
            role (int): Role to return

        Returns:
            Data depending on role.
        """
        if not index.isValid():
            return None
        project_item = index.internalPointer()
        if role == Qt.DisplayRole:
            return project_item.name
        else:
            return None

    def project_item(self, index):
        """Returns project item at given index.

        Args:
            index (QModelIndex): Index of project item

        Returns:
            ProjectItem: Item at given index or root project item if index is not valid
        """
        if not index.isValid():
            return self.root()
        return index.internalPointer()

    def find_category(self, category_name):
        """Returns the index of the given category name.

        Args:
            category_name (str): Name of category item to find

        Returns:
             QModelIndex of a category item or None if it was not found
        """
        category_names = [category.name for category in self.root().children()]
        # logging.debug("Category names:{0}".format(category_names))
        try:
            row = category_names.index(category_name)
        except ValueError:
            logging.error("Category name {0} not found in {1}".format(category_name, category_names))
            return None
        return self.index(row, 0, QModelIndex())

    def find_item(self, name):
        """Returns the QModelIndex of the project item with the given name

        Args:
            name (str): The searched project item (long) name

        Returns:
            QModelIndex of a project item with the given name or None if not found
        """
        for category in self.root().children():
            # logging.debug("Looking for {0} in category {1}".format(name, category.name))
            category_index = self.find_category(category.name)
            start_index = self.index(0, 0, category_index)
            matching_index = self.match(start_index, Qt.DisplayRole, name,
                                        1, Qt.MatchFixedString | Qt.MatchRecursive)
            if len(matching_index) == 0:
                pass  # no match in this category
            elif len(matching_index) == 1:
                # logging.debug("Found item:{0}".format(matching_index[0].internalPointer().name))
                return matching_index[0]
        return None

    def insert_item(self, item, parent=QModelIndex()):
        """Add new item to model. Fails if parent_item is not a category item or root item.
        Inserts new item as the last item.

        Args:
            item (ProjectItem): Project item to add to model
            parent (QModelIndex): Parent project item

        Returns:
            True if successful, False otherwise
        """
        parent_item = self.project_item(parent)
        row = self.rowCount(parent)  # parent.child_count()
        logging.debug("Inserting item on row:{0} under parent:{1}".format(row, parent_item.name))
        self.beginInsertRows(parent, row, row)
        retval = parent_item.add_child(item)
        self.endInsertRows()
        return retval

    def remove_item(self, item, parent=QModelIndex()):
        """Remove item from model.

        Args:
            item (ProjectItem): Project item to remove
            parent (QModelIndex): Parent of item that is to be removed

        Returns:
            bool: True if item removed successfully, False if item removing failed
        """
        parent_item = self.project_item(parent)
        row = item.row()
        self.beginRemoveRows(parent, row, row)
        retval = parent_item.remove_child(row)
        self.endRemoveRows()
        return retval

    def setData(self, index, value, role=Qt.EditRole):
        # TODO: Test this. Should this emit dataChanged signal at some point?
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
        item = index.internalPointer()
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
        if self.find_item(value):
            msg = "Project item <b>{0}</b> already exists".format(value)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid name", msg)
            return False
        # Check that no existing project item short name matches the new item's short name.
        # This is to prevent two project items from using the same folder.
        new_short_name = value.lower().replace(' ', '_')
        if self._toolbox.project_item_model.short_name_reserved(new_short_name):
            msg = "Project item using directory <b>{0}</b> already exists".format(new_short_name)
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
        # Rename project item
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
        item.update_tab()
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

    def items(self, category_name=None):
        """Returns a list of items in model according to category name. If no category name given,
        returns all items in a list.

        Args:
            category_name (str): Item category. Data Connections, Data Stores, Tools or Views permitted.

        Returns:
            :obj:'list' of :obj:'ProjectItem': Depending on category_name argument, returns all items or only
            items according to category. An empty list is returned if there are no items in the given category
            or if an unknown category name was given.
        """
        if not category_name:
            items = list()
            for category in self.root().children():
                items += category.children()
            return items
        else:
            category_item = self.find_category(category_name)
            if not category_item:
                logging.error("Category item '{0}' not found".format(category_name))
                return list()
            return category_item.internalPointer().children()

    def n_items(self):
        """Return the number of all project items in the model excluding category items and root."""
        return len(self.items())

    def return_item_names(self):
        """Returns the names of all items in a list."""
        return [item.name for item in self.items()]

    def new_item_index(self, category):
        """Get index where a new item is appended according to category. This is needed for
        appending the connection model.

        Args:
            category (str): Display Role of the parent

        Returns:
            Number of items according to category
        """
        n_data_stores = self.rowCount(self.find_category("Data Stores"))
        n_data_connections = self.rowCount(self.find_category("Data Connections"))
        n_tools = self.rowCount(self.find_category("Tools"))
        n_views = self.rowCount(self.find_category("Views"))
        if category == "Data Stores":
            # Return number of data stores
            return n_data_stores - 1
        elif category == "Data Connections":
            # Return number of data stores + data connections - 1
            return n_data_stores + n_data_connections - 1
        elif category == "Tools":
            # Return number of data stores + data connections + tools - 1
            return n_data_stores + n_data_connections + n_tools - 1
        elif category == "Views":
            # Return total number of items - 1
            return self.n_items() - 1
        else:
            logging.error("Unknown category:{0}".format(category))
            return 0

    def short_name_reserved(self, short_name):
        """Check if folder name derived from the name of the given item is in use.

        Args:
            short_name (str): Item short name

        Returns:
            bool: True if short name is taken, False if it is available.
        """
        project_items = self.items()
        for item in project_items:
            if item.short_name == short_name:
                return True
        return False


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

    def append_item(self, name, index):
        """Embiggen connections table by a new item.

        Args:
            name (str): New item name
            index (int): Table row and column where the new item is appended

        Returns:
            True if successful, False otherwise
        """
        # item_name = item.name
        logging.debug("Appending item {0} on row and column: {1}".format(name, index))
        # logging.debug("Appending {3}. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections, item_name))
        self.header.insert(index, name)
        if not self.insertRows(index, 1, parent=QModelIndex()):
            return False
        if not self.insertColumns(index, 1, parent=QModelIndex()):
            return False
        # logging.debug("After append. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections))
        return True

    def remove_item(self, name):
        """Remove project item from connections table.

        Args:
            name (str): Name of removed item

        Returns:
            True if successful, False otherwise
        """
        try:
            item_index = self.header.index(name)
        except ValueError:
            logging.error("{0} not found in connection table header list".format(name))
            return False
        # logging.debug("Removing {3}. rows:{0} columns:{1} data:\n{2}"
        #               .format(self.rowCount(), self.columnCount(), self.connections, item_name))
        if not self.removeRows(item_index, 1, parent=QModelIndex()):
            return False
        if not self.removeColumns(item_index, 1, parent=QModelIndex()):
            return False
        self.header.remove(name)
        logging.debug("After remove. rows:{0} columns:{1} data:\n{2}"
                      .format(self.rowCount(), self.columnCount(), self.connections))
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
        self.is_being_reset = False
        self.modelAboutToBeReset.connect(lambda: self.set_being_reset(True))
        self.modelReset.connect(lambda: self.set_being_reset(False))
        self.wip_row_list = list()
        self.rowsInserted.connect(self.rows_inserted)
        self.rowsRemoved.connect(self.rows_removed)

    def set_being_reset(self, on):
        self.is_being_reset = on

    def rows_inserted(self, parent, first, last):
        """Update work in progress row list."""
        for i, row in enumerate(self.wip_row_list):
            if first <= row:
                self.wip_row_list[i] += 1

    def rows_removed(self, parent, first, last):
        """Update work in progress row list."""
        try:
            self.wip_row_list.remove(first)
        except ValueError:
            pass
        for i, row in enumerate(self.wip_row_list):
            if first < row:
                self.wip_row_list[i] -= 1

    def set_work_in_progress(self, row, on):
        """Add row into list of work in progress."""
        if on and row not in self.wip_row_list:
            self.wip_row_list.append(row)
        else:
            try:
                self.wip_row_list.remove(row)
            except ValueError:
                pass

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        return row in self.wip_row_list

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

    def insert_row_with_data(self, row, row_data, role=Qt.EditRole, parent=QModelIndex()):
        if not self.insertRows(row, 1, parent):
            return False
        for column, value in enumerate(row_data):
            self.setData(self.index(row, column), value, role)
        self.row_with_data_inserted.emit(parent, row)
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
        if row < 0 or row > self.rowCount():
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
        if column < 0 or column > self.columnCount():
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
        self.mapping = data_store_form.mapping
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
            else:
                return self.relationship_icon
        return super().data(index, role)

    def build_tree(self, db_name):
        """Create root item and object class items. This triggers a recursion
        that builds up the tree.
        """
        self.clear()
        root_item = QStandardItem(db_name)
        root_item.setData('root', Qt.UserRole)
        for object_class in self.mapping.object_class_list():
            object_class_item = self.new_object_class_item(object_class._asdict())
            root_item.appendRow(object_class_item)
        self.appendRow(root_item)
        return root_item

    def new_object_class_item(self, object_class):
        """Returns new object class item.

        Args:
            object_class (dict)
        """
        object_class_item = QStandardItem(object_class['name'])
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData(object_class, Qt.UserRole+1)
        object_list = self.mapping.object_list(class_id=object_class['id'])
        wide_relationship_class_list = self.mapping.wide_relationship_class_list(object_class_id=object_class['id'])
        for object_ in object_list:
            object_item = self.new_object_item(object_._asdict(), wide_relationship_class_list)
            object_class_item.appendRow(object_item)
        return object_class_item

    def new_object_item(self, object_, wide_relationship_class_list=None):
        """Returns new object item.

        Args:
            object_ (dict)
            wide_relationship_class_list (query)
        """
        object_item = QStandardItem(object_['name'])
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_, Qt.UserRole+1)
        # create and append relationship class items
        for wide_relationship_class in wide_relationship_class_list:
            relationship_class_item = self.new_relationship_class_item(wide_relationship_class._asdict(), object_)
            object_item.appendRow(relationship_class_item)
        return object_item

    def new_relationship_class_item(self, wide_relationship_class, object_):
        """Returns new relationship class item.

        Args:
            wide_relationship_class (dict): relationship class in wide format
            object_ (dict): object which is the parent item in the tree
        """
        relationship_class_item = QStandardItem(wide_relationship_class['name'])
        relationship_class_item.setData(wide_relationship_class, Qt.UserRole+1)
        relationship_class_item.setData('relationship_class', Qt.UserRole)
        relationship_class_item.setData(wide_relationship_class['object_class_name_list'], Qt.ToolTipRole)
        # get relationship involving the present object and class in wide format
        wide_relationship_list = self.mapping.wide_relationship_list(
            class_id=wide_relationship_class['id'],
            object_id=object_['id'])
        for wide_relationship in wide_relationship_list:
            relationship_item = self.new_relationship_item(wide_relationship._asdict())
            relationship_class_item.appendRow(relationship_item)
        return relationship_class_item

    def new_relationship_item(self, wide_relationship):
        """Returns new relationship item.

        Args:
            wide_relationship (dict)
        """
        relationship_item = QStandardItem(wide_relationship['name'])
        relationship_item.setData('relationship', Qt.UserRole)
        relationship_item.setData(wide_relationship, Qt.UserRole+1)
        relationship_item.setData(wide_relationship['object_name_list'], Qt.ToolTipRole)
        return relationship_item

    def add_object_class(self, object_class):
        """Add object class item to the model.

        Args:
            object_class (dict)
        """
        object_class_item = self.new_object_class_item(object_class)
        root_item = self.invisibleRootItem().child(0)
        row = root_item.rowCount()
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['display_order'] > object_class['display_order']:
                root_item.insertRow(i, QStandardItem())
                root_item.setChild(i, 0, object_class_item)
                break

    def add_object(self, object_):
        """Add object item to the model.

        Args:
            object_ (dict)
        """
        # find object class item among the children of the root
        root_item = self.invisibleRootItem().child(0)
        object_class_item = None
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['id'] == object_['class_id']:
                object_class_item = visited_object_class_item
                break
        if not object_class_item:
            logging.debug("Object class item not found in model. This is probably a bug.")
            return
        wide_relationship_class_list = self.mapping.wide_relationship_class_list(object_['class_id'])
        object_item = self.new_object_item(object_, wide_relationship_class_list)
        object_class_item.appendRow(object_item)

    def add_relationship_class(self, wide_relationship_class): # TODO
        """Add proto relationship class."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type == 'root':
                continue
            if not visited_type == 'object':
                continue
            visited_object = visited_item.data(Qt.UserRole+1)
            object_class_id_list = wide_relationship_class['object_class_id_list']
            if visited_object['class_id'] not in [int(x) for x in object_class_id_list.split(',')]:
                continue
            relationship_class_item = self.new_relationship_class_item(wide_relationship_class, visited_object)
            visited_item.appendRow(relationship_class_item)
            # TODO: Don't add duplicate relationship class if parent and child are the same?
            # TODO: Add mirror proto relationship class?

    def add_relationship(self, wide_relationship):
        """Add relationship item to model.

        Args:
            wide_relationship (dict): the relationship to add
        """
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type == 'root':
                continue
            if not visited_type == 'relationship_class':
                continue
            visited_relationship_class = visited_item.data(Qt.UserRole+1)
            if not visited_relationship_class['id'] == wide_relationship['class_id']:
                continue
            visited_object = visited_item.parent().data(Qt.UserRole+1)
            object_id_list = wide_relationship['object_id_list']
            if visited_object['id'] not in [int(x) for x in object_id_list.split(',')]:
                continue
            relationship_item = self.new_relationship_item(wide_relationship)
            visited_item.appendRow(relationship_item)

    def rename_item(self, new_name, curr_name, renamed_type, renamed_id):
        """Rename all matched items."""
        items = self.findItems(curr_name, Qt.MatchExactly | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type == 'root':
                continue
            visited = visited_item.data(Qt.UserRole+1)
            visited_id = visited['id']
            if visited_type == renamed_type and visited_id == renamed_id:
                visited['name'] = new_name
                visited_item.setData(visited, Qt.UserRole+1)
                visited_item.setText(new_name)

    def remove_item(self, removed_type, removed_id):
        """Remove all matched items and their orphans."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in reversed(items):
            visited_type = visited_item.data(Qt.UserRole)
            visited = visited_item.data(Qt.UserRole+1)
            if visited_type == 'root':
                continue
            # Get visited id
            visited_id = visited['id']
            visited_index = self.indexFromItem(visited_item)
            if visited_type == removed_type and visited_id == removed_id:
                self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object class, also remove relationship classes that involve it
            if removed_type == 'object_class' and visited_type == 'relationship_class':
                object_class_id_list = visited['object_class_id_list']
                if removed_id in [int(x) for x in object_class_id_list.split(',')]:
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object, also remove relationships that involve it
            if removed_type == 'object' and visited_type == 'relationship':
                object_id_list = visited['object_id_list']
                if removed_id in [int(x) for x in object_id_list.split(',')]:
                    self.removeRows(visited_index.row(), 1, visited_index.parent())

    def next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        if index.data(Qt.UserRole) != 'relationship':
            return None
        relationship = index.data(Qt.UserRole+1)
        items = self.findItems(relationship['name'], Qt.MatchExactly | Qt.MatchRecursive, column=0)
        position = None
        for i, item in enumerate(items):
            if index == self.indexFromItem(item):
                position = i
                break
        if position is None:
            return None
        position = (position+1) % len(items)
        return self.indexFromItem(items[position])


class ParameterTableModel(MinimalTableModel):
    """A model to use with parameter tables in DataStoreForm."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self._data_store_form = data_store_form
        self.gray_brush = self._data_store_form.palette().button() if self._data_store_form else QBrush(Qt.lightGray)

    def make_columns_fixed(self, *column_names, skip_wip=False):
        """Set columns as fixed so they are not editable and painted gray."""
        for row in range(self.rowCount()):
            if skip_wip and row in self.wip_row_list:
                continue
            self.make_columns_fixed_for_row(row, *column_names)

    def make_columns_fixed_for_row(self, row, *column_names):
        """Set background role data and flags for row and column names."""
        for name in column_names:
            column = self.horizontal_header_labels().index(name)
            index = self.index(row, column)
            self.setData(index, self.gray_brush, Qt.BackgroundRole)
            self.set_flags(index, ~Qt.ItemIsEditable)


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """A custom sort filter proxy model."""
    def __init__(self, data_store_form=None):
        """Initialize class."""
        super().__init__(data_store_form)
        self._data_store_form = data_store_form
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.italic_font = QFont()
        self.italic_font.setItalic(True)
        self.h = None
        # List of rules. Each rule is a dict. Items are the terms of an 'or' statement
        self.rule_dict_list = list()
        self.subrule_dict = dict()
        self.rejected_column_list = list()
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view

    def setSourceModel(self, source_model):
        super().setSourceModel(source_model)
        source_model.headerDataChanged.connect(self.update_h)
        self.update_h()

    def update_h(self):
        self.h = self.sourceModel().horizontal_header_labels().index

    def set_work_in_progress(self, row, on):
        """Add row into list of work in progress."""
        index = self.index(row, 0)
        source_index = self.mapToSource(index)
        source_row = source_index.row()
        self.sourceModel().set_work_in_progress(source_row, on)

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        index = self.index(row, 0)
        source_index = self.mapToSource(index)
        source_row = source_index.row()
        return self.sourceModel().is_work_in_progress(source_row)

    def clear_filter(self):
        """Clear all rules, unbold all bolded items."""
        self.rejected_column_list = list()
        for rule_dict in self.rule_dict_list:
            for source_column in rule_dict:
                for source_row in range(self.sourceModel().rowCount()):
                    source_index = self.sourceModel().index(source_row, source_column)
                    self.sourceModel().setData(source_index, None, Qt.FontRole)
        self.rule_dict_list = list()
        self.subrule_dict = dict()

    def apply_filter(self):
        """Trigger filtering."""
        self.setFilterRegExp("")
        # Italize header in case the subrule is met
        for column in self.subrule_dict:
            self.sourceModel().setHeaderData(column, Qt.Horizontal, self.italic_font, Qt.FontRole)

    def reject_column(self, *names):
        """Add rejected columns."""
        for name in names:
            self.rejected_column_list.append(self.h(name))

    def add_rule(self, **kwargs):
        """Add NEGATIVE rules by joining the kwargs into a 'or' statement.
        Negative rules trigger a violation if not met."""
        rule_dict = {}
        for key, value in kwargs.items():
            column = self.h(key)
            rule_dict[column] = value
        self.rule_dict_list.append(rule_dict)

    def add_subrule(self, **kwargs):
        """Add POSITIVE subrules by taking the kwargs as individual statements (key = value).
        Positive rules trigger a violation if met."""
        for key, value in kwargs.items():
            column = self.h(key)
            self.subrule_dict[column] = value

    def remove_subrule(self, *args):
        """Remove subrules."""
        for field_name in args:
            column = self.h(field_name)
            try:
                del self.subrule_dict[column]
                self.sourceModel().setHeaderData(column, Qt.Horizontal, None, Qt.FontRole)
            except KeyError:
                pass

    def filter_accept_rows(self, source_row, source_parent):
        """Sweep rules. """
        for rule_dict in self.rule_dict_list:
            result = False
            for column, value in rule_dict.items():
                source_index = self.sourceModel().index(source_row, column, source_parent)
                data = self.sourceModel().data(source_index, self.filterRole())
                if data is None:
                    continue
                if isinstance(value, list):
                    cond = (data in value)
                else:
                    cond = (data == value)
                if cond:
                    result = True
                    self.sourceModel().setData(source_index, self.bold_font, Qt.FontRole)
            if not result:
                return False
        return True

    def subfilter_accept_rows(self, source_row, source_parent, skip_source_column=list()):
        for column, value in self.subrule_dict.items():
            if column in skip_source_column:
                continue
            source_index = self.sourceModel().index(source_row, column, source_parent)
            data = self.sourceModel().data(source_index, self.filterRole())
            if data is None:
                return False
            if data in value:
                return False
        return True

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        All the rules and subrules need to pass.
        """
        if self.sourceModel().is_work_in_progress(source_row):
            return True
        if not self.filter_accept_rows(source_row, source_parent):
            return False
        if not self.subfilter_accept_rows(source_row, source_parent):
            return False
        return True

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if not self.rejected_column_list:
            return True
        return source_column not in self.rejected_column_list


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
