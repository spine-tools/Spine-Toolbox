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
Classes for handling models in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.

:authors: P. Savolainen (VTT), M. Marin (KTH), P. Vennström (VTT)
:date:   23.1.2018
"""

import logging
import os
from PySide2.QtCore import Qt, Slot, QModelIndex, QAbstractListModel, QAbstractTableModel, QAbstractItemModel
from PySide2.QtWidgets import QMessageBox
from config import INVALID_CHARS, TOOL_OUTPUT_DIR
from helpers import rename_dir
from project_item import CategoryProjectItem


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
        if isinstance(parent.internalPointer(), CategoryProjectItem):  # Number of project items in the category
            return parent.internalPointer().child_count()
        return 0

    def columnCount(self, parent=QModelIndex()):
        """Returns model column count."""
        return 1

    def flags(self, index):
        """Returns flags for the item at given index

        Args:
            index (QModelIndex): Flags of item at this index.
        """
        if not isinstance(index.internalPointer(), CategoryProjectItem):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled  # | Qt.ItemIsSelectable

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
        return self.createIndex(row, column, child)

    def data(self, index, role=None):
        """Returns data in the given index according to requested role.

        Args:
            index (QModelIndex): Index to query
            role (int): Role to return

        Returns:
            object: Data depending on role.
        """
        if not index.isValid():
            return None
        project_item = index.internalPointer()
        if role == Qt.DisplayRole:
            return project_item.name
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
             QModelIndex: index of a category item or None if it was not found
        """
        category_names = [category.name for category in self.root().children()]
        # logging.debug("Category names:{0}".format(category_names))
        try:
            row = category_names.index(category_name)
        except ValueError:
            logging.error("Category name %s not found in %s", category_name, category_names)
            return None
        return self.index(row, 0, QModelIndex())

    def find_item(self, name):
        """Returns the QModelIndex of the project item with the given name

        Args:
            name (str): The searched project item (long) name

        Returns:
            QModelIndex: Index of a project item with the given name or None if not found
        """
        for category in self.root().children():
            # logging.debug("Looking for {0} in category {1}".format(name, category.name))
            category_index = self.find_category(category.name)
            start_index = self.index(0, 0, category_index)
            matching_index = self.match(start_index, Qt.DisplayRole, name, 1, Qt.MatchFixedString | Qt.MatchRecursive)
            if not matching_index:
                pass  # no match in this category
            elif len(matching_index) == 1:
                # logging.debug("Found item:{0}".format(matching_index[0].internalPointer().name))
                return matching_index[0]
        return None

    def insert_item(self, item, parent=QModelIndex()):
        """Adds a new item to model. Fails if given parent is not
        a category item nor a root item. New item is inserted as
        the last item.

        Args:
            item (ProjectItem): Project item to add to model
            parent (QModelIndex): Parent project item

        Returns:
            bool: True if successful, False otherwise
        """
        parent_item = self.project_item(parent)
        row = self.rowCount(parent)  # parent.child_count()
        # logging.debug("Inserting item on row:{0} under parent:{1}".format(row, parent_item.name))
        self.beginInsertRows(parent, row, row)
        retval = parent_item.add_child(item)
        self.endInsertRows()
        return retval

    def remove_item(self, item, parent=QModelIndex()):
        """Removes item from model.

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
        """Changes the name of the project item at given index to given value.
        # TODO: If the item is a Data Store the reference sqlite path must be updated.

        Args:
            index (QModelIndex): Project item index
            value (str): New project item name
            role (int): Item data role to set

        Returns:
            bool: True or False depending on whether the new name is acceptable.
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
            logging.error("Item does not have a data_dir. " "Make sure that class %s creates one.", item.item_type)
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
        elif item.item_type == "Tool":
            item.output_dir = os.path.join(item.data_dir, TOOL_OUTPUT_DIR)
        # Update name label in tab
        item.update_name_label()
        # Update name item of the QGraphicsItem
        item.icon.update_name_item(value)
        # Change old item names in connection model headers to the new name
        header_index = self._toolbox.connection_model.find_index_in_header(old_name)
        self._toolbox.connection_model.setHeaderData(header_index, Qt.Horizontal, value)
        self._toolbox.connection_model.setHeaderData(header_index, Qt.Vertical, value)
        # Rename node and edges in the graph (dag) that contains this project item
        self._toolbox.project().dag_handler.rename_node(old_name, value)
        # Force save project
        self._toolbox.save_project()
        self._toolbox.msg_success.emit("Project item <b>{0}</b> renamed to <b>{1}</b>".format(old_name, value))
        # If item is a Data Store and an SQLite path is set, give the user a notice that this must be updated manually
        if item.item_type == "Data Store":
            if not self._toolbox.ui.lineEdit_database.text().strip() == "":
                self._toolbox.msg_warning.emit("<b>Note: Please update database path</b>")
        return True

    def items(self, category_name=None):
        """Returns a list of items in model according to category name. If no category name given,
        returns all project items in a list.

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
        category_item = self.find_category(category_name)
        if not category_item:
            logging.error("Category item '%s' not found", category_name)
            return list()
        return category_item.internalPointer().children()

    def n_items(self):
        """Returns the number of all project items in the model excluding category items and root.

        Returns:
            int: Number of items
        """
        return len(self.items())

    def item_names(self):
        """Returns all project item names in a list.

        Returns:
            obj:'list' of obj:'str': Item names
        """
        return [item.name for item in self.items()]

    def new_item_index(self, category):
        """Returns the index where a new item can be appended according
        to category. This is needed for appending the connection model.

        Args:
            category (str): Display Role of the parent

        Returns:
            int: Number of items according to category
        """
        count = self.rowCount(self.find_category("Data Stores"))
        if category == "Data Stores":
            # Return number of data stores
            return count - 1
        count += self.rowCount(self.find_category("Data Connections"))
        if category == "Data Connections":
            # Return number of data stores + data connections - 1
            return count - 1
        count += self.rowCount(self.find_category("Tools"))
        if category == "Tools":
            # Return number of data stores + data connections + tools - 1
            return count - 1
        count += self.rowCount(self.find_category("Views"))
        if category == "Views":
            # Return number of data stores + data connections + tools + views - 1
            return count - 1
        count += self.rowCount(self.find_category("Data Interfaces"))
        if category == "Data Interfaces":
            # Return total number of items - 1
            return count - 1
        if category == "Exporting":
            return self.n_items() - 1
        logging.error("Unknown category: %s", category)
        return 0

    def short_name_reserved(self, short_name):
        """Checks if the directory name derived from the name of the given item is in use.

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
        self._toolbox = toolbox

    def rowCount(self, parent=None):
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
        if role == Qt.DisplayRole:
            toolname = self._tools[row].name
            return toolname
        if role == Qt.ToolTipRole:
            if row >= self.rowCount():
                return ""
            return self._tools[row].def_file_path

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRow(self, tool, row=None, parent=QModelIndex()):
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

    def removeRow(self, row, parent=QModelIndex()):
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
            ToolTemplate from tool template list or None if given row is zero
        """
        return self._tools[row]

    def find_tool_template(self, name):
        """Returns tool template with the given name.

        Args:
            name (str): Name of tool template to find
        """
        for template in self._tools:
            if name.lower() == template.name.lower():
                return template
        return None

    def tool_template_row(self, name):
        """Returns the row on which the given template is located or -1 if it is not found."""
        for i in range(len(self._tools)):
            if name == self._tools[i].name:
                return i
        return -1

    def tool_template_index(self, name):
        """Returns the QModelIndex on which a tool template with
        the given name is located or invalid index if it is not found."""
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
            return len(self.connections[0])
        except IndexError:
            return 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns header data according to given role."""
        if role == Qt.DisplayRole:
            try:
                return self.header[section]
            except IndexError:
                return None
        else:
            return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if role != Qt.EditRole:
            return super().setHeaderData(section, orientation, value, role)
        if orientation in [Qt.Horizontal, Qt.Vertical]:
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
            return "True"  # If a link is present return "True"
        if role == Qt.ToolTipRole:
            header = self.headerData(index.row(), Qt.Vertical, Qt.DisplayRole)
            return header + " (Feedback)"
        if role == Qt.UserRole:
            return self.connections[index.row()][index.column()]
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
        if role != Qt.EditRole:
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
            # logging.error("Insert 1 row at a time")
            return False
        # beginInsertRows(const QModelIndex & parent, int first, int last)
        self.beginInsertRows(parent, row, row)
        new_row = list()
        if self.columnCount() == 0:
            new_row.append(None)
        else:
            new_row += self.columnCount() * [None]
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
            # logging.error("Insert 1 column at a time")
            return False
        # beginInsertColumns(const QModelIndex & parent, int first, int last)
        self.beginInsertColumns(parent, column, column)
        for j in range(self.rowCount()):
            # Notice if insert index > rowCount(), new object is inserted to end
            self.connections[j].insert(column, None)
        self.endInsertColumns()
        return True

    def _rowRemovalPossible(self, row, count):
        return 0 <= row < self.rowCount() and count == 1

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent.

        Args:
            row (int): Row number where to start removing rows
            count (int): Number of removed rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were removed successfully, False otherwise
        """
        if not self._rowRemovalPossible(row, count):
            if count != 1:
                # logging.error("Remove 1 row at a time")
                pass
            return False
        # beginRemoveRows(const QModelIndex & parent, int first, int last)
        self.beginRemoveRows(parent, row, row)
        self.connections.pop(row)
        self.endRemoveRows()
        return True

    def _columnRemovalPossible(self, column, count):
        return 0 <= column < self.columnCount() and count == 1

    def removeColumns(self, column, count, parent=QModelIndex()):
        """Removes count columns starting with the given column under parent.

        Args:
            column (int): Column number where to start removing columns
            count (int): Number of removed columns
            parent (QModelIndex): Parent index

        Returns:
            True if columns were removed successfully, False otherwise
        """
        if not self._columnRemovalPossible(column, count):
            if count != 1:
                # logging.error("Remove 1 column at a time")
                pass
            return False
        self.beginRemoveColumns(parent, column, column)
        # for loop all rows and remove the column from each
        removed_column = list()  # for testing and debugging
        removing_last_column = self.columnCount() == 1
        for r in self.connections:
            removed_column.append(r.pop(column))
        if removing_last_column:
            self.connections = []
        self.endRemoveColumns()
        return True

    def append_item(self, name, index):
        """Embiggens connections table by a new item.

        Args:
            name (str): New item name
            index (int): Table row and column where the new item is appended

        Returns:
            True if successful, False otherwise
        """
        if not self.insertRows(index, 1, parent=QModelIndex()):
            return False
        if self.rowCount() > 1:
            # The first call to insertRows() also creates the first column
            if not self.insertColumns(index, 1, parent=QModelIndex()):
                # Roll back row insertion.
                self.removeRows(index, 1)
                return False
        self.header.insert(index, name)
        return True

    def remove_item(self, name):
        """Removes project item from connections table.

        Args:
            name (str): Name of removed item

        Returns:
            True if successful, False otherwise
        """
        try:
            item_index = self.header.index(name)
        except ValueError:
            # logging.error("%s not found in connection table header list", name)
            return False
        if not self._rowRemovalPossible(item_index, 1) or not self._columnRemovalPossible(item_index, 1):
            return False
        self.removeRows(item_index, 1, parent=QModelIndex())
        if self.rowCount() > 0:
            self.removeColumns(item_index, 1, parent=QModelIndex())
        self.header.remove(name)
        return True

    def output_items(self, name):
        """Returns a list of output items for the given item.

        Args:
            name (str): Project item name

        Returns:
            (list): Output project item names in a list if they
            exist or an empty list if they don't.
        """
        item_row = self.header.index(name)  # Row or column of item in the model
        output_items = list()
        for column in range(self.columnCount()):
            is_output = self.connections[item_row][column]
            if is_output:
                # append the name of output item to list
                output_items.append(self.header[column])
        return output_items

    def input_items(self, name):
        """Returns a list of input items for the given item.

        Args:
            name (str): Project item name

        Returns:
            (list): Input project item names in a list if they
            exist or an empty list if they don't.
        """
        item_column = self.header.index(name)  # Row or column of item in the model
        input_items = list()
        for row in range(self.rowCount()):
            is_input = self.connections[row][item_column]
            if is_input:
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
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
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
    """Table model for outlining simple tabular data.

    Attributes:
        parent (QMainWindow): the parent widget, usually an instance of TreeViewForm
    """

    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent
        self._main_data = list()  # DisplayRole and EditRole
        self.default_flags = Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self.header = list()  # DisplayRole and EditRole
        self.aux_header = list()  # All the other roles, each entry in the list is a dict

    def clear(self):
        """Clear all data in model."""
        self.beginResetModel()
        self._main_data = list()
        self.endResetModel()

    def flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return self.default_flags

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in the model."""
        return len(self._main_data)

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in the model."""
        try:
            return len(self._main_data[0])
        except IndexError:
            return len(self.header)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Get headers."""
        if role != Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                try:
                    return self.aux_header[section][role]
                except IndexError:
                    return None
                except KeyError:
                    return None
            return None
        if orientation == Qt.Horizontal:
            try:
                return self.header[section]
            except IndexError:
                return None
        if orientation == Qt.Vertical:
            return section + 1

    def set_horizontal_header_labels(self, labels):
        """Set horizontal header labels."""
        if not labels:
            return
        self.header = labels
        self.aux_header = [{} for _ in range(len(labels))]
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(labels) - 1)

    def insert_horizontal_header_labels(self, section, labels):
        """Insert horizontal header labels at the given section."""
        if not labels:
            return
        for j, value in enumerate(labels):
            if section + j >= self.columnCount():
                self.header.append(value)
                self.aux_header.append({})
            else:
                self.header.insert(section + j, value)
                self.aux_header.insert(section + j, {})
        self.headerDataChanged.emit(Qt.Horizontal, section, section + len(labels) - 1)

    def horizontal_header_labels(self):
        return self.header

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if orientation != Qt.Horizontal:
            return False
        if role != Qt.EditRole:
            try:
                self.aux_header[section][role] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except IndexError:
                return False
        try:
            self.header[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        except IndexError:
            return False

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
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        try:
            return self._main_data[index.row()][index.column()]
        except IndexError:
            logging.error("Cannot access model data at index %s", index)
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
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        return self._main_data[row]

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
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        return [self._main_data[row][column] for row in range(self.rowCount())]

    def model_data(self, role=Qt.DisplayRole):
        """Returns the data stored under the given role in the entire model.

        Args:
            role (int): Data role

        Returns:
            Model data for given role.
        """
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._main_data
        return [self.row_data(row, role) for row in range(self.rowCount())]

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in model."""
        if not index.isValid():
            return False
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return False
        return self.batch_set_data([index], [value])

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes."""
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            self._main_data[index.row()][index.column()] = data[k]
        # Find square envelope of indexes to emit dataChanged
        top = min(ind.row() for ind in indexes)
        bottom = max(ind.row() for ind in indexes)
        left = min(ind.column() for ind in indexes)
        right = max(ind.column() for ind in indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right), [Qt.EditRole, Qt.DisplayRole])
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
        if count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            if self.columnCount() == 0:
                new_main_row = [None]
            else:
                new_main_row = [None for j in range(self.columnCount())]
            # Notice if insert index > rowCount(), new object is inserted to end
            self._main_data.insert(row + i, new_main_row)
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
        if count < 1:
            return False
        self.beginInsertColumns(parent, column, column + count - 1)
        for j in range(count):
            for i in range(self.rowCount()):
                self._main_data[i].insert(column + j, None)
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
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        for i in reversed(range(row, row + count)):
            self._main_data.pop(i)
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
        removing_last_column = False
        if self.columnCount() == 1:
            removing_last_column = True
        for r in self._main_data:
            r.pop(column)
        if removing_last_column:
            self._main_data = []
        # logging.debug("{0} removed from column:{1}".format(removed_column, column))
        self.endRemoveColumns()
        return True

    def reset_model(self, main_data=None):
        """Reset model."""
        if main_data is None:
            main_data = list()
        self.beginResetModel()
        self._main_data = main_data
        self.endResetModel()


class EmptyRowModel(MinimalTableModel):
    """A table model with a last empty row."""

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.default_row = {}  # A row of default values to put in any newly inserted row
        self.force_default = False  # Whether or not default values are editable
        self.dataChanged.connect(self._handle_data_changed)
        self.rowsRemoved.connect(self._handle_rows_removed)
        self.rowsInserted.connect(self._handle_rows_inserted)

    def flags(self, index):
        """Return default flags except if forcing defaults."""
        if not index.isValid():
            return Qt.NoItemFlags
        if self.force_default:
            try:
                name = self.header[index.column()]
                if name in self.default_row:
                    return self.default_flags & ~Qt.ItemIsEditable
            except IndexError:
                pass
        return self.default_flags

    def set_default_row(self, **kwargs):
        """Set default row data."""
        self.default_row = kwargs

    def clear(self):
        super().clear()
        self.insertRows(self.rowCount(), 1, QModelIndex())

    def reset_model(self, data):
        super().reset_model(data)
        self.insertRows(self.rowCount(), 1, QModelIndex())

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_data_changed")
    def _handle_data_changed(self, top_left, bottom_right, roles=None):
        """Insert a new last empty row in case the previous one has been filled
        with any data other than the defaults."""
        if roles is None:
            roles = list()
        if roles and Qt.EditRole not in roles:
            return
        last_row = self.rowCount() - 1
        for column in range(self.columnCount()):
            try:
                name = self.header[column]
            except IndexError:
                name = None
            data = self._main_data[last_row][column]
            default = self.default_row.get(name)
            if not data and not default:
                continue
            if data != default:
                self.insertRows(self.rowCount(), 1)
                break

    @Slot("QModelIndex", "int", "int", name="_handle_rows_removed")
    def _handle_rows_removed(self, parent, first, last):
        """Insert a new empty row in case it's been removed."""
        last_row = self.rowCount()
        if last_row in range(first, last + 1):
            self.insertRows(self.rowCount(), 1)

    @Slot("QModelIndex", "int", "int", name="_handle_rows_inserted")
    def _handle_rows_inserted(self, parent, first, last):
        """Handle rowsInserted signal."""
        self.set_rows_to_default(first, last)

    def set_rows_to_default(self, first, last):
        """Set default data in newly inserted rows."""
        left = None
        right = None
        for column in range(self.columnCount()):
            try:
                name = self.header[column]
            except IndexError:
                name = None
            default = self.default_row.get(name)
            if left is None:
                left = column
            right = column
            for row in range(first, last + 1):
                self._main_data[row][column] = default
        if left is None:
            return
        top_left = self.index(first, left)
        bottom_right = self.index(last, right)
        self.dataChanged.emit(top_left, bottom_right)


class HybridTableModel(MinimalTableModel):
    """A model that concatenates two models,
    one for existing items and another one for new items.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self._parent = parent
        self.existing_item_model = MinimalTableModel(self)
        self.new_item_model = EmptyRowModel(self)

    def flags(self, index):
        """Return flags for given index.
        Depending on the index's row we will land on one of the two models.
        """
        row = index.row()
        column = index.column()
        if row < self.existing_item_model.rowCount():
            return self.existing_item_model.index(row, column).flags()
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.index(row, column).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Depending on the index's row we will land on one of the two models.
        """
        row = index.row()
        column = index.column()
        if row < self.existing_item_model.rowCount():
            return self.existing_item_model.index(row, column).data(role)
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.index(row, column).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in the two models.
        """
        return self.existing_item_model.rowCount() + self.new_item_model.rowCount()

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        Distribute indexes and data among the two models
        and call batch_set_data on each of them."""
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        existing_model_indexes = []
        existing_model_data = []
        new_model_indexes = []
        new_model_data = []
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            if row < self.existing_item_model.rowCount():
                existing_model_indexes.append(self.existing_item_model.index(row, column))
                existing_model_data.append(data[k])
            else:
                row -= self.existing_item_model.rowCount()
                new_model_indexes.append(self.new_item_model.index(row, column))
                new_model_data.append(data[k])
        self.existing_item_model.batch_set_data(existing_model_indexes, existing_model_data)
        self.new_item_model.batch_set_data(new_model_indexes, new_model_data)
        # Find square envelope of indexes to emit dataChanged
        top = min(ind.row() for ind in indexes)
        bottom = max(ind.row() for ind in indexes)
        left = min(ind.column() for ind in indexes)
        right = max(ind.column() for ind in indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-model (or the empty model) and call insertRows on it."""
        if row < self.existing_item_model.rowCount():
            self.rowsInserted.emit()
            return self.existing_item_model.insertRows(row, count)
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.insertRows(row, count)

    def removeRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-models (or empty model) and call removeRows on them."""
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        if row < self.existing_item_model.rowCount():
            # split count across models
            existing_count = min(count, self.existing_item_model.rowCount() - row)
            self.existing_item_model.removeRows(row, existing_count)
            new_count = count - existing_count
            if new_count > 0:
                self.new_item_model.removeRows(row, new_count)
        else:
            row -= self.existing_item_model.rowCount()
            self.new_item_model.removeRows(row, count)
        self.endRemoveRows()
        return True

    def set_horizontal_header_labels(self, labels):
        super().set_horizontal_header_labels(labels)
        self.new_item_model.set_horizontal_header_labels(labels)

    def reset_model(self, data):
        """Reset model data."""
        self.beginResetModel()
        self.existing_item_model.reset_model(data)
        self.new_item_model.clear()
        self.new_item_model.rowsInserted.connect(self._handle_new_item_model_rows_inserted)
        self.endResetModel()

    @Slot("QModelIndex", "int", "int", name="_handle_new_item_model_rows_inserted")
    def _handle_new_item_model_rows_inserted(self, parent, first, last):
        offset = self.existing_item_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), offset + first, offset + last)


class DatapackageResourcesModel(MinimalTableModel):
    """A model of datapackage resource data, used by SpineDatapackageWidget.

    Attributes:
        parent (SpineDatapackageWidget)
    """

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)

    def reset_model(self, resources):
        self.clear()
        self.set_horizontal_header_labels(["name", "source"])
        data = list()
        for resource in resources:
            name = resource.name
            source = os.path.basename(resource.source)
            data.append([name, source])
        super().reset_model(data)

    def flags(self, index):
        if index.column() == 1:
            return ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable
        return super().flags(index)


class DatapackageFieldsModel(MinimalTableModel):
    """A model of datapackage field data, used by SpineDatapackageWidget.

    Attributes:
        parent (SpineDatapackageWidget)
    """

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)

    def reset_model(self, schema):
        self.clear()
        self.set_horizontal_header_labels(["name", "type", "primary key?"])
        data = list()
        for field in schema.fields:
            name = field.name
            type_ = field.type
            primary_key = name in schema.primary_key
            data.append([name, type_, primary_key])
        super().reset_model(data)


class DatapackageForeignKeysModel(EmptyRowModel):
    """A model of datapackage foreign key data, used by SpineDatapackageWidget.

    Attributes:
        parent (SpineDatapackageWidget)
    """

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent

    def reset_model(self, foreign_keys):
        self.clear()
        self.set_horizontal_header_labels(["fields", "reference resource", "reference fields", ""])
        data = list()
        for foreign_key in foreign_keys:
            fields = ",".join(foreign_key['fields'])
            reference_resource = foreign_key['reference']['resource']
            reference_fields = ",".join(foreign_key['reference']['fields'])
            data.append([fields, reference_resource, reference_fields, None])
        super().reset_model(data)


class TableModel(QAbstractItemModel):
    """Used by custom_qtableview.FrozenTableView"""

    def __init__(self, headers=None, data=None):
        super(TableModel, self).__init__()
        if headers is None:
            headers = list()
        if data is None:
            data = list()
        self._data = data
        self._headers = headers

    def parent(self, child=None):
        return QModelIndex()

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column, parent)

    def set_data(self, data, headers):
        if data and len(data[0]) != len(headers):
            raise ValueError("'data[0]' must be same length as 'headers'")
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]

    def row(self, index):
        if index.isValid():
            return self._data[index.row()]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
