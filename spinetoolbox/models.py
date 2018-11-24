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
from PySide2.QtCore import Qt, Signal, Slot, QModelIndex, QAbstractListModel, QAbstractTableModel, \
    QSortFilterProxyModel, QAbstractItemModel
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QFont, QFontMetrics, QIcon, QPixmap, \
    QPainter, QGuiApplication
from PySide2.QtWidgets import QMessageBox
from config import INVALID_CHARS, TOOL_OUTPUT_DIR
from helpers import rename_dir, fix_name_ambiguity, busy_effect
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError


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
        # logging.debug("Inserting item on row:{0} under parent:{1}".format(row, parent_item.name))
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
        # TODO: If the item is a Data Store the reference sqlite path must be updated.

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
        elif item.item_type == "Tool":
            item.output_dir = os.path.join(item.data_dir, TOOL_OUTPUT_DIR)
        # If item is a Data Store and an SQLite path is set, give the user a notice that this must be updated manually
        elif item.item_type == "Data Store":
            if not self._toolbox.ui.lineEdit_SQLite_file.text().strip() == "":
                self._toolbox.msg_warning.emit("Note: Path to SQLite file may need updating.")
        # Update name label in tab
        item.update_name_label()
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
            ToolTemplate from tool template list or None if given row is zero
        """
        if row == 0:
            return None
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
        """Returns the row on which the given template is located or -1 if it is not found."""
        for i in range(len(self._tools)):
            if isinstance(self._tools[i], str):
                continue
            else:
                if name == self._tools[i].name:
                    return i
        return -1

    def tool_template_index(self, name):
        """Returns the QModelIndex on which a tool template with
        the given name is located or None if it is not found."""
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
        # logging.debug("Appending item {0} on row and column: {1}".format(name, index))
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
    """Table model for outlining simple tabular data.

    Attributes:
        parent (QMainWindow): the parent widget, usually an instance of TreeViewForm
        can_grow (bool): if True, the model grows automatically when setting data beyond its limits
        has_empty_row (bool): if True, the model always has an empty row at the bottom
    """
    def __init__(self, parent=None, can_grow=False, has_empty_row=False):
        """Initialize class"""
        super().__init__()
        self._parent = parent
        self._main_data = list()  # DisplayRole and EditRole
        self._aux_data = list()  # All the other roles, each entry in the matrix is a dict
        self._flags = list()
        self.default_flags = Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self.header = list()
        self.can_grow = can_grow
        self.has_empty_row = has_empty_row
        self.default_row = []  # A row of default values to put in any newly inserted row
        self._force_default = False  # Whether or not default values are editable
        self.dataChanged.connect(self.receive_data_changed)
        self.rowsAboutToBeRemoved.connect(self.receive_rows_about_to_be_removed)
        self.rowsInserted.connect(self.receive_rows_inserted)
        self.columnsInserted.connect(self.receive_columns_inserted)

    def set_default_row(self, data):
        """Set default row.

        Args:
            data (list)
        """
        if not data:
            return
        self.default_row = data

    @Slot("QModelIndex", "QModelIndex", "QVector", name="receive_data_changed")
    def receive_data_changed(self, top_left, bottom_right, roles):
        """In models with a last empty row, insert a new last empty row in case
        the previous one has been filled with any data other than the defaults."""
        if not self.has_empty_row:
            return
        last_row = self.rowCount() - 1
        for column in range(self.columnCount()):
            try:
                data = self._main_data[last_row][column]
            except KeyError:
                # No data in this column, just continue
                continue
            try:
                default = self.default_row[column]
            except IndexError:
                # No default for this column, check if any data
                if not data:
                    continue
                self.insertRows(self.rowCount(), 1)
                break
            # Both data and default found, check if they differ
            if data != default:
                self.insertRows(self.rowCount(), 1)
                break

    @Slot("QModelIndex", "int", "int", name="receive_rows_about_to_be_removed")
    def receive_rows_about_to_be_removed(self, parent, first, last):
        """In models with a last empty row, insert a new empty row
        in case the current one is being deleted."""
        if not self.has_empty_row:
            return
        last_row = self.rowCount() - 1
        if last_row in range(first, last + 1):
            self.insertRows(self.rowCount(), 1)

    @Slot("QModelIndex", "int", "int", name="receive_rows_inserted")
    def receive_rows_inserted(self, parent, first, last):
        """In models with row defaults, set default data in newly inserted rows."""
        last_column = 0
        for column in range(self.columnCount()):
            last_column = column
            try:
                default = self.default_row[column]
            except IndexError:
                break
            for row in range(first, last + 1):
                self._main_data[row][column] = default
                if self._force_default:
                    self._flags[row][column] &= ~Qt.ItemIsEditable
        if last_column == 0:
            return
        top_left = self.index(first, 0)
        bottom_right = self.index(last, last_column)
        self.dataChanged.emit(top_left, bottom_right, [Qt.EditRole, Qt.DisplayRole])

    @Slot("QModelIndex", "int", "int", name="receive_columns_inserted")
    def receive_columns_inserted(self, parent, first, last):
        """In models with row defaults, set default data in newly inserted columns."""
        last_column = 0
        for column in range(first, last + 1):
            last_column = column
            try:
                default = self.default_row[column]
            except IndexError:
                break
            for row in range(self.rowCount()):
                self._main_data[row][column] = default
                if self._force_default:
                    self._flags[row][column] &= ~Qt.ItemIsEditable
        if last_column == first:
            return
        top_left = self.index(0, first)
        bottom_right = self.index(self.rowCount() - 1, last_column)
        self.dataChanged.emit(top_left, bottom_right, [Qt.EditRole, Qt.DisplayRole])

    def clear(self):
        """Clear all data in model."""
        self.beginResetModel()
        self._main_data = list()
        self._aux_data = list()
        self.endResetModel()
        if self.has_empty_row:
            self.insertRows(self.rowCount(), 1)

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
        return len(self._main_data)

    def columnCount(self, *args, **kwargs):
        """Number of columns in the model."""
        try:
            return len(self._main_data[0])
        except IndexError:
            return len(self.header)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Get headers."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            try:
                return self.header[section]
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
        self.header = labels
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(labels) - 1)

    def insert_horizontal_header_labels(self, section, labels):
        """Insert horizontal header labels at the given section."""
        if not labels:
            return
        for j, value in enumerate(labels):
            if section + j >= self.columnCount():
                self.header.append(value)
            else:
                self.header.insert(section + j, value)
        self.headerDataChanged.emit(Qt.Horizontal, section, section + len(labels))

    def horizontal_header_labels(self):
        return self.header

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if role != Qt.EditRole:
            return False
        if orientation == Qt.Horizontal:
            try:
                self.header[section] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except IndexError:
                return False
        return False

    def index(self, row, column, parent=QModelIndex()):
        if row < 0 or column < 0 or column >= self.columnCount(parent):
            return QModelIndex()
        if self.can_grow:
            index = super().index(row, column, parent)
            while not index.isValid():
                self.insertRows(self.rowCount(parent), 1, parent)
                index = super().index(row, column, parent)
            return index
        if row >= self.rowCount(parent):
            return QModelIndex()
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
            if role in (Qt.DisplayRole, Qt.EditRole):
                return self._main_data[index.row()][index.column()]
            else:
                return self._aux_data[index.row()][index.column()][role]
        except IndexError:
            logging.error(index)
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
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._main_data[row]
        return [self._aux_data[row][column][role] for column in range(self.columnCount())]

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
        if role in (Qt.DisplayRole, Qt.EditRole):
            return [self._main_data[row][column] for row in range(self.rowCount())]
        return [self._aux_data[row][column][role] for row in range(self.rowCount())]

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
            self._aux_data[index.row()][index.column()][role] = value
            self.dataChanged.emit(index, index, [role])
            return True
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
                new_aux_row = [{}]
                new_flags_row = [self.default_flags]
            else:
                new_main_row = [None for j in range(self.columnCount())]
                new_aux_row = [{} for j in range(self.columnCount())]
                new_flags_row = [self.default_flags for j in range(self.columnCount())]
            # Notice if insert index > rowCount(), new object is inserted to end
            self._main_data.insert(row + i, new_main_row)
            self._aux_data.insert(row + i, new_aux_row)
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
        if count < 1:
            return False
        self.beginInsertColumns(parent, column, column + count - 1)
        for j in range(count):
            for i in range(self.rowCount()):
                self._main_data[i].insert(column + j, None)
                self._aux_data[i].insert(column + j, {})
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
        removed_main_data_row = self._main_data.pop(row)
        removed_aux_data_row = self._aux_data.pop(row)
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
        removing_last_column = False
        if self.columnCount() == 1:
            removing_last_column = True
        for r in self._main_data:
            r.pop(column)
        for r in self._aux_data:
            r.pop(column)
        for r in self._flags:
            r.pop(column)
        if removing_last_column:
            self._main_data = []
            self._aux_data = []
            self._flags = []
        # logging.debug("{0} removed from column:{1}".format(removed_column, column))
        self.endRemoveColumns()
        return True

    def remove_row_set(self, row_set, parent=QModelIndex()):
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
        for row in reversed(sorted(row_set)):
            self._main_data.pop(row)
            self._aux_data.pop(row)
            self._flags.pop(row)
        self.endRemoveRows()
        return True

    def reset_model(self, main_data=[], aux_data=None):
        """Reset model."""
        self.beginResetModel()
        self._main_data = main_data
        if aux_data:
            self._aux_data = aux_data
        else:
            self._aux_data = [[{} for j in range(len(row))] for row in main_data]
        self._flags = [[self.default_flags for j in range(len(row))] for row in main_data]
        #for line in main_data:
        #    aux_data_row = list()
        #    flags_row = list()
        #    for item in line:
        #        aux_data_row.append(dict())
        #        flags_row.append(self.default_flags)
        #    self._aux_data.append(aux_data_row)
        #    self._flags.append(flags_row)
        self.endResetModel()
        if self.has_empty_row:
            self.insertRows(self.rowCount(), 1)


class ObjectClassListModel(QStandardItemModel):
    """A class to list object classes in the GraphViewForm."""
    def __init__(self, graph_view_form):
        """Initialize class"""
        super().__init__(graph_view_form)
        self.db_map = graph_view_form.db_map
        self.object_icon_dict = graph_view_form.object_icon_dict
        self.add_more_index = None

    def populate_list(self):
        """Populate model."""
        self.clear()
        object_class_list = [x for x in self.db_map.object_class_list()]
        for object_class in object_class_list:
            icon = self.object_icon_dict[object_class.id]
            object_class_item = QStandardItem(object_class.name)
            data = {"type": "object_class", **object_class._asdict()}
            object_class_item.setData(data, Qt.UserRole + 1)
            object_class_item.setData(icon, Qt.DecorationRole)
            object_class_item.setData(object_class.name, Qt.ToolTipRole)
            self.appendRow(object_class_item)
        add_more_item = QStandardItem()
        add_more_item.setData("Add more...", Qt.DisplayRole)
        self.appendRow(add_more_item)
        self.add_more_index = self.indexFromItem(add_more_item)

    def add_object_class(self, object_class):
        """Add object class item to model."""
        icon = self.object_icon_dict[object_class.id]
        object_class_item = QStandardItem(object_class.name)
        data = {"type": "object_class", **object_class._asdict()}
        object_class_item.setData(data, Qt.UserRole + 1)
        object_class_item.setData(icon, Qt.DecorationRole)
        object_class_item.setData(object_class.name, Qt.ToolTipRole)
        for i in range(self.rowCount()):
            visited_index = self.index(i, 0)
            visited_display_order = visited_index.data(Qt.UserRole + 1)['display_order']
            if visited_display_order >= object_class.display_order:
                self.insertRow(i, object_class_item)
                return
        self.insertRow(self.rowCount() - 1, object_class_item)


class RelationshipClassListModel(QStandardItemModel):
    """A class to list relationship classes in the GraphViewForm."""
    def __init__(self, graph_view_form):
        """Initialize class"""
        super().__init__(graph_view_form)
        self.relationship_icon_dict = graph_view_form.relationship_icon_dict
        self.db_map = graph_view_form.db_map
        self.add_more_index = None

    def populate_list(self):
        """Populate model."""
        self.clear()
        relationship_class_list = [x for x in self.db_map.wide_relationship_class_list()]
        for relationship_class in relationship_class_list:
            icon = self.relationship_icon_dict[relationship_class.id]
            relationship_class_item = QStandardItem(relationship_class.name)
            data = {"type": "relationship_class", **relationship_class._asdict()}
            relationship_class_item.setData(data, Qt.UserRole + 1)
            relationship_class_item.setData(icon, Qt.DecorationRole)
            relationship_class_item.setData(relationship_class.name, Qt.ToolTipRole)
            self.appendRow(relationship_class_item)
        add_more_item = QStandardItem()
        add_more_item.setData("Add more...", Qt.DisplayRole)
        self.appendRow(add_more_item)
        self.add_more_index = self.indexFromItem(add_more_item)

    def add_relationship_class(self, relationship_class):
        """Add relationship class."""
        icon = self.relationship_icon_dict[relationship_class.id]
        relationship_class_item = QStandardItem(relationship_class.name)
        data = {"type": "relationship_class", **relationship_class._asdict()}
        relationship_class_item.setData(data, Qt.UserRole + 1)
        relationship_class_item.setData(icon, Qt.DecorationRole)
        relationship_class_item.setData(relationship_class.name, Qt.ToolTipRole)
        self.insertRow(self.rowCount() - 1, relationship_class_item)


class ObjectTreeModel(QStandardItemModel):
    """A class to hold Spine data structure in a treeview."""

    def __init__(self, tree_view_form):
        """Initialize class"""
        super().__init__(tree_view_form)
        self.db_map = tree_view_form.db_map
        self.root_item = QModelIndex()
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.object_icon_dict = tree_view_form.object_icon_dict
        self.relationship_icon_dict = tree_view_form.relationship_icon_dict

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.ForegroundRole:
            item_type = index.data(Qt.UserRole)
            if item_type.endswith('class') and not self.hasChildren(index):
                return QBrush(Qt.gray)
        return super().data(index, role)

    def backward_sweep(self, index, call=None):
        """Sweep the tree from the given index towards the root, and apply `call` on each."""
        current = index
        while True:
            if call:
                call(current)
            # Try and visit parent
            next_ = current.parent()
            if not next_.isValid():
                break
            current = next_
            continue

    def forward_sweep(self, index, call=None):
        """Sweep the tree from the given index towards the leaves, and apply `call` on each."""
        if call:
            call(index)
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

    def build_flat_tree(self, db_name):
        """Build flat tree, only with object classes and objects."""
        self.clear()
        object_class_list = [x for x in self.db_map.object_class_list()]
        object_list = [x for x in self.db_map.object_list()]
        wide_relationship_class_list = [x for x in self.db_map.wide_relationship_class_list()]
        wide_relationship_list = [x for x in self.db_map.wide_relationship_list()]
        self.root_item = QStandardItem(db_name)
        self.root_item.setData('root', Qt.UserRole)
        icon = QIcon(":/icons/Spine_db_icon.png")
        self.root_item.setData(icon, Qt.DecorationRole)
        object_class_item_list = list()
        for object_class in object_class_list:
            icon = self.object_icon_dict[object_class.id]
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setData('object_class', Qt.UserRole)
            object_class_item.setData(object_class._asdict(), Qt.UserRole + 1)
            object_class_item.setData(object_class.description, Qt.ToolTipRole)
            object_class_item.setData(icon, Qt.DecorationRole)
            object_class_item.setData(self.bold_font, Qt.FontRole)
            object_item_list = list()
            for object_ in object_list:
                if object_.class_id != object_class.id:
                    continue
                object_item = QStandardItem(object_.name)
                object_item.setData('object', Qt.UserRole)
                object_item.setData(object_._asdict(), Qt.UserRole + 1)
                object_item.setData(object_.description, Qt.ToolTipRole)
                object_item.setData(icon, Qt.DecorationRole)
                object_item_list.append(object_item)
            object_class_item.appendRows(object_item_list)
            object_class_item_list.append(object_class_item)
        self.root_item.appendRows(object_class_item_list)
        self.appendRow(self.root_item)

    def build_tree(self, db_name):
        """Build tree."""
        self.clear()
        object_class_list = [x for x in self.db_map.object_class_list()]
        object_list = [x for x in self.db_map.object_list()]
        wide_relationship_class_list = [x for x in self.db_map.wide_relationship_class_list()]
        wide_relationship_list = [x for x in self.db_map.wide_relationship_list()]
        self.root_item = QStandardItem(db_name)
        self.root_item.setData('root', Qt.UserRole)
        icon = QIcon(":/icons/Spine_db_icon.png")
        self.root_item.setData(icon, Qt.DecorationRole)
        object_class_item_list = list()
        for object_class in object_class_list:
            object_icon = self.object_icon_dict[object_class.id]
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setData('object_class', Qt.UserRole)
            object_class_item.setData(object_class._asdict(), Qt.UserRole + 1)
            object_class_item.setData(object_class.description, Qt.ToolTipRole)
            object_class_item.setData(object_icon, Qt.DecorationRole)
            object_class_item.setData(self.bold_font, Qt.FontRole)
            object_item_list = list()
            for object_ in object_list:
                if object_.class_id != object_class.id:
                    continue
                object_item = QStandardItem(object_.name)
                object_item.setData('object', Qt.UserRole)
                object_item.setData(object_._asdict(), Qt.UserRole + 1)
                object_item.setData(object_.description, Qt.ToolTipRole)
                object_item.setData(object_icon, Qt.DecorationRole)
                relationship_class_item_list = list()
                for wide_relationship_class in wide_relationship_class_list:
                    object_class_id_list = [int(x) for x in wide_relationship_class.object_class_id_list.split(",")]
                    if object_.class_id not in object_class_id_list:
                        continue
                    relationship_class_item = QStandardItem(wide_relationship_class.name)
                    relationship_class_item.setData('relationship_class', Qt.UserRole)
                    relationship_class_item.setData(wide_relationship_class._asdict(), Qt.UserRole + 1)
                    relationship_class_item.setData(wide_relationship_class.object_class_name_list, Qt.ToolTipRole)
                    relationship_icon = self.relationship_icon_dict[wide_relationship_class.id]
                    relationship_class_item.setData(relationship_icon, Qt.DecorationRole)
                    relationship_class_item.setData(self.bold_font, Qt.FontRole)
                    relationship_item_list = list()
                    for wide_relationship in wide_relationship_list:
                        if wide_relationship.class_id != wide_relationship_class.id:
                            continue
                        if object_.id not in [int(x) for x in wide_relationship.object_id_list.split(",")]:
                            continue
                        relationship_item = QStandardItem(wide_relationship.object_name_list)
                        relationship_item.setData('relationship', Qt.UserRole)
                        relationship_item.setData(wide_relationship._asdict(), Qt.UserRole + 1)
                        relationship_item.setData(relationship_icon, Qt.DecorationRole)
                        relationship_item_list.append(relationship_item)
                    relationship_class_item.appendRows(relationship_item_list)
                    relationship_class_item_list.append(relationship_class_item)
                object_item.appendRows(relationship_class_item_list)
                object_item_list.append(object_item)
            object_class_item.appendRows(object_item_list)
            object_class_item_list.append(object_class_item)
        self.root_item.appendRows(object_class_item_list)
        self.appendRow(self.root_item)

    def new_object_class_item(self, object_class):
        """Returns new object class item."""
        object_class_item = QStandardItem(object_class.name)
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData(object_class._asdict(), Qt.UserRole + 1)
        object_class_item.setData(object_class.description, Qt.ToolTipRole)
        object_class_item.setData(self.bold_font, Qt.FontRole)
        return object_class_item

    def new_object_item(self, object_, flat=False):
        """Returns new object item."""
        object_item = QStandardItem(object_.name)
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_._asdict(), Qt.UserRole + 1)
        object_item.setData(object_.description, Qt.ToolTipRole)
        if flat:
            return object_item
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
        relationship_class_item.setData(self.bold_font, Qt.FontRole)
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
        for i in range(self.root_item.rowCount()):
            visited_object_class_item = self.root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole + 1)
            if visited_object_class['display_order'] >= object_class.display_order:
                self.root_item.insertRow(i, QStandardItem())
                self.root_item.setChild(i, 0, object_class_item)
                return
        row = self.root_item.rowCount()
        self.root_item.insertRow(row, QStandardItem())
        self.root_item.setChild(row, 0, object_class_item)
        icon = self.object_icon_dict[object_class.id]
        object_class_item.setData(icon, Qt.DecorationRole)

    def add_object(self, object_, flat=False):
        """Add object item to the model."""
        # find object class item among the children of the root
        object_class_item = None
        for i in range(self.root_item.rowCount()):
            visited_object_class_item = self.root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole + 1)
            if visited_object_class['id'] == object_.class_id:
                object_class_item = visited_object_class_item
                break
        if not object_class_item:
            logging.error("Object class item not found in model. This is probably a bug.")
            return
        object_item = self.new_object_item(object_, flat=flat)
        object_class_item.appendRow(object_item)
        object_class_name = object_class_item.data(Qt.DisplayRole)
        icon = object_class_item.data(Qt.DecorationRole)
        object_item.setData(icon, Qt.DecorationRole)

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
            icon = self.relationship_icon_dict[wide_relationship_class.id]
            relationship_class_item.setData(icon, Qt.DecorationRole)
            visited_item.appendRow(relationship_class_item)

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
            icon = visited_item.data(Qt.DecorationRole)
            relationship_item.setData(icon, Qt.DecorationRole)

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
        ids_to_add = set()
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
                    ids_to_add.add(visited_id)
                else:
                    visited_item.setText(updated_item.object_name_list)
                    visited_item.setData(updated_item._asdict(), Qt.UserRole + 1)
            except KeyError:
                continue
        for id in ids_to_add:
            self.add_relationship(updated_items_dict[id])

    def remove_items(self, removed_type, *removed_ids):
        """Remove all matched items and their orphans."""
        # TODO: try and remove all rows at once, if possible
        removed_name_dict = dict()
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
                removed_name_dict.setdefault(visited_type, set()).add(visited["name"])
            # When removing an object class, also remove relationship classes that involve it
            if removed_type == 'object_class' and visited_type == 'relationship_class':
                object_class_id_list = visited['object_class_id_list']
                if any([id in [int(x) for x in object_class_id_list.split(',')] for id in removed_ids]):
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
                    removed_name_dict.setdefault(visited_type, set()).add(visited["name"])
            # When removing an object, also remove relationships that involve it
            if removed_type == 'object' and visited_type == 'relationship':
                object_id_list = visited['object_id_list']
                if any([id in [int(x) for x in object_id_list.split(',')] for id in removed_ids]):
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
                    removed_name_dict.setdefault(visited_type, set()).add(visited["name"])
        return removed_name_dict

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


class WIPTableModel(MinimalTableModel):
    """An editable table model. It has two types of row, normal and wip (work in progess) row.
    For the former, only a subset of columns are editable. For the latter, all of them are editable.
    Wip rows can become normal rows after succesfully setting data for some key fields.
    """
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, can_grow=True, has_empty_row=has_empty_row)
        self._tree_view_form = tree_view_form
        self.fixed_columns = list()
        if self._tree_view_form:
            self.gray_brush = self._tree_view_form.palette().button()
        else:
            self.gray_brush = QGuiApplication.palette().button()

    def setData(self, index, value, role=Qt.EditRole):
        """Set data in model."""
        if role != Qt.EditRole:
            return super().setData(index, value, role)
        return self.batch_set_data([index], [value])

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes."""
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
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
        wip_data_set = self.batch_set_wip_data(wip_indexes, wip_data)
        non_wip_data_set = self.batch_set_non_wip_data(non_wip_indexes, non_wip_data)
        if not wip_data_set and not non_wip_data_set:
            return False
        # Find square envelope of indexes to emit dataChanged
        set_indexes = list()
        if wip_data_set:
            set_indexes.extend(wip_indexes)
        if non_wip_data_set:
            set_indexes.extend(non_wip_indexes)
        top = min(ind.row() for ind in set_indexes)
        bottom = max(ind.row() for ind in set_indexes)
        left = min(ind.column() for ind in set_indexes)
        right = max(ind.column() for ind in set_indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right), [Qt.EditRole, Qt.DisplayRole])
        return True

    def batch_set_wip_data(self, indexes, data):
        """Batch set work in progress data. Update model first, then see if the database
        needs to be updated as well. Extend indexes in case ids are set."""
        if not indexes:
            return False
        for k, index in enumerate(indexes):
            self._main_data[index.row()][index.column()] = data[k]
        items_to_add = self.items_to_add(indexes)
        if self.add_items_to_db(items_to_add):
            id_column = self.horizontal_header_labels().index('id')
            indexes.extend([self.index(row, id_column) for row in items_to_add])
        return True

    def batch_set_non_wip_data(self, indexes, data):
        """Batch set non work in progess data. Try and set data in database first, and if
        successful set data model.
        """
        if not indexes:
            return False
        if not self.update_items_in_db(self.items_to_update(indexes, data)):
            return False
        for k, index in enumerate(indexes):
            self._main_data[index.row()][index.column()] = data[k]
        return True

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        try:
            column = self.fixed_columns[0]
        except IndexError:
            return True
        return self._flags[row][column] & Qt.ItemIsEditable

    def make_data_fixed(self, rows=[], column_names=[]):
        """Make data non-editable and set background."""
        if not rows:
            data_row_count = self.rowCount() - 1 if self.has_empty_row else self.rowCount()
            rows = range(0, data_row_count)
        elif self.has_empty_row:
            empty_row = self.rowCount()  # FIXME: is this correct? or should it be self.rowCount() - 1???
            try:
                rows.remove(empty_row)
            except ValueError:
                pass
        h = self.horizontal_header_labels().index
        columns = []
        for x in column_names:
            try:
                columns.append(h(x))
            except ValueError:
                pass
        if not columns:
            columns = self.fixed_columns
        for column in columns:
            for row in rows:
                self._aux_data[row][column][Qt.BackgroundRole] = self.gray_brush
                self._flags[row][column] = ~Qt.ItemIsEditable
        new_columns = [x for x in columns if x not in self.fixed_columns]
        self.fixed_columns.extend(new_columns)
        try:
            top_left = self.index(min(rows, default=-1), min(columns, default=-1))
            bottom_right = self.index(max(rows, default=-1), max(columns, default=-1))
            self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        except IndexError:
            pass


class ParameterDefinitionModel(WIPTableModel):
    """A model of parameter definition data, used by TreeViewForm.
    It implements methods that are common to both object and relationship parameter definitions,
    so the more specific `ObjectParameterDefinitionModel` and `RelationshipParameterDefinitionModel`
    can inherit from this.
    """
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)
        self.db_map = self._tree_view_form.db_map
        self.object_icon_dict = self._tree_view_form.object_icon_dict
        self.relationship_icon_dict = self._tree_view_form.relationship_icon_dict

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
            if values[k] == index.data(Qt.EditRole):
                continue
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

    @busy_effect
    def add_items_to_db(self, items_to_add):
        """Add items to database and make columns fixed if successful."""
        if not items_to_add:
            return False
        try:
            # TODO: Make it flexible rather than all or nothing? Anyways this would require updating database_api
            items = list(items_to_add.values())
            rows = list(items_to_add.keys())
            parameters = self.db_map.add_parameters(*items)
            id_column = self.horizontal_header_labels().index('id')
            for i, parameter in enumerate(parameters):
                self._main_data[rows[i]][id_column] = parameter.id
            self.make_data_fixed(rows=rows)
            self._tree_view_form.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new parameters."
            self._tree_view_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False

    @busy_effect
    def update_items_in_db(self, items_to_update):
        """Try and update parameters in database."""
        if not items_to_update:
            return False
        try:
            self.db_map.update_parameters(*items_to_update)
            self._tree_view_form.set_commit_rollback_actions_enabled(True)
            msg = "Parameters successfully updated."
            self._tree_view_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False


class ParameterValueModel(WIPTableModel):
    """A model of parameter value data, used by TreeViewForm.
    It implements methods that are common to both object and relationship parameter values,
    so the more specific `ObjectParameterValueModel` and `RelationshipParameterValueModel`
    can inherit from this."""
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)
        self.db_map = self._tree_view_form.db_map
        self.object_icon_dict = self._tree_view_form.object_icon_dict
        self.relationship_icon_dict = self._tree_view_form.relationship_icon_dict
        self.font_metric = QFontMetrics(QFont(""))  # For elided json text

    def data(self, index, role=Qt.DisplayRole):
        """Limit the output of json array data to 8 positions."""
        data = super().data(index, role)
        if role != Qt.DisplayRole:
            return data
        if self.header[index.column()] == 'json':
            return self.font_metric.elidedText(data, Qt.ElideMiddle, 100)
        return data

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
            if values[k] == index.data(Qt.EditRole):
                continue
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

    @busy_effect
    def add_items_to_db(self, items_to_add):
        """Add parameter values to database and make columns fixed if successful."""
        if not items_to_add:
            return False
        try:
            items = list(items_to_add.values())
            rows = list(items_to_add.keys())
            parameter_values = self.db_map.add_parameter_values(*items)
            id_column = self.horizontal_header_labels().index('id')
            for i, parameter_value in enumerate(parameter_values):
                self._main_data[rows[i]][id_column] = parameter_value.id
            self.make_data_fixed(rows=rows)
            self._tree_view_form.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new parameter values."
            self._tree_view_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False

    @busy_effect
    def update_items_in_db(self, items_to_update):
        """Try and update parameter values in database."""
        if not items_to_update:
            return False
        try:
            self.db_map.update_parameter_values(*items_to_update)
            self._tree_view_form.set_commit_rollback_actions_enabled(True)
            msg = "Parameter values successfully updated."
            self._tree_view_form.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)
            return False


class ObjectParameterModel(QAbstractTableModel):
    """A model of object parameter data, used by TreeViewForm.
    It implements methods that are common to both object parameter definitions and values,
    so the more specific `ObjectParameterDefinitionModel` and `ObjectParameterValueModel`
    can inherit from this."""
    def __init__(self):
        super().__init__()
        self.dataChanged.connect(self.handle_data_changed)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="handle_data_changed")
    def handle_data_changed(self, top_left, bottom_right, roles=[]):
        """Fill in decoration role data when object class name changes."""
        if Qt.EditRole not in roles:
            return
        if Qt.DecorationRole in roles:
            return
        header = self.horizontal_header_labels()
        left = top_left.column()
        right = bottom_right.column()
        object_class_name_column = header.index('object_class_name')
        if object_class_name_column < left or object_class_name_column > right:
            return
        top = top_left.row()
        bottom = bottom_right.row()
        object_class_dict = {x.name: x.id for x in self.db_map.object_class_list()}
        for row in range(top, bottom + 1):
            object_class_name = self._main_data[row][object_class_name_column]
            try:
                object_class_id = object_class_dict[object_class_name]
                icon = self.object_icon_dict[object_class_id]
                self._aux_data[row][object_class_name_column][Qt.DecorationRole] = icon
            except KeyError:
                continue
        new_top_left = self.index(top, object_class_name_column)
        new_bottom_right = self.index(bottom, object_class_name_column)
        self.dataChanged.emit(new_top_left, new_bottom_right, [Qt.DecorationRole])

    def decoration_role_data(self, model_data):
        """Return decoration role data based on model_data."""
        header = self.horizontal_header_labels()
        aux_data = []
        aux_data_append = aux_data.append
        row_range = range(len(model_data[0]))
        object_class_id_column = header.index('object_class_id')
        object_class_name_column = header.index('object_class_name')
        for model_row in model_data:
            aux_row = [{} for i in row_range]
            object_class_id = model_row[object_class_id_column]
            icon = self.object_icon_dict[object_class_id]
            aux_row[object_class_name_column][Qt.DecorationRole] = icon
            aux_data_append(aux_row)
        return aux_data


class RelationshipParameterModel(QAbstractTableModel):
    """A model of relationship parameter data, used by TreeViewForm.
    It implements methods that are common to both relationship parameter definitions and values,
    so the more specific `RelationshipParameterDefinitionModel` and `RelationshipParameterValueModel`
    can inherit from this."""
    def __init__(self):
        super().__init__()
        self.dataChanged.connect(self.handle_data_changed)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="handle_data_changed")
    def handle_data_changed(self, top_left, bottom_right, roles=[]):
        """Fill in decoration role data when relationship class or object names change."""
        if Qt.EditRole not in roles:
            return
        if Qt.DecorationRole in roles:
            return
        header = self.horizontal_header_labels()
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        self.set_relationship_class_icon(top, left, bottom, right, header)
        self.set_object_icons(top, left, bottom, right, header)

    def set_relationship_class_icon(self, top, left, bottom, right, header):
        """Set relationship class icons."""
        relationship_class_name_column = header.index('relationship_class_name')
        if relationship_class_name_column < left or relationship_class_name_column > right:
            return
        relationship_class_dict = {x.name: x.id for x in self.db_map.wide_relationship_class_list()}
        for row in range(top, bottom + 1):
            relationship_class_name = self._main_data[row][relationship_class_name_column]
            try:
                relationship_class_id = relationship_class_dict[relationship_class_name]
                icon = self.relationship_icon_dict[relationship_class_id]
                self._aux_data[row][relationship_class_name_column][Qt.DecorationRole] = icon
            except KeyError:
                continue
        new_top_left = self.index(top, relationship_class_name_column)
        new_bottom_right = self.index(bottom, relationship_class_name_column)
        self.dataChanged.emit(new_top_left, new_bottom_right, [Qt.DecorationRole])

    def set_object_icons(self, top, left, bottom, right, header):
        """See reimplementation in RelationshipParameterValueModel"""
        pass


class ObjectParameterDefinitionModel(ParameterDefinitionModel, ObjectParameterModel):
    """A model of object parameter data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)

    def init_model(self, skip_fields=[]):
        """Initialize model from source database."""
        data = self.db_map.object_parameter_list()
        fields = self.db_map.object_parameter_fields()
        header = [x for x in fields if x not in skip_fields]
        self.set_horizontal_header_labels(header)
        model_data = [[v for k, v in r._asdict().items() if k not in skip_fields] for r in data]
        aux_data = self.decoration_role_data(model_data)
        self.reset_model(model_data, aux_data=aux_data)
        column_names = ['id', 'object_class_name']
        self.make_data_fixed(column_names=column_names)

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type != "object_class":
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        column = header_index("object_class_name")
        for row in row_range:
            try:
                curr_name = self._main_data[row][column][Qt.DisplayRole]
                new_name = names_dict[curr_name]
                self._main_data[row][column] = new_name
            except KeyError:
                continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type != "object_class":
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        header_index = self.horizontal_header_labels().index
        column = header_index("object_class_name")
        for row in reversed(row_range):
            try:
                name = self._main_data[row][column]
            except KeyError:
                continue
            if name in removed_names:
                super().removeRows(row, 1)

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        object_class_id_column = header.index('object_class_id')
        object_class_name_column = header.index('object_class_name')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        object_class_dict = {x.name: x.id for x in self.db_map.object_class_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            try:
                object_class_id = object_class_dict[object_class_name]
            except KeyError:
                continue
            # Autoset the object_class_id
            self._main_data[row][object_class_id_column] = object_class_id
            if not parameter_name:
                continue
            item = {
                "object_class_id": object_class_id,
                "name": parameter_name
            }
            for column in range(parameter_name_column + 1, self.columnCount()):
                item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
            items_to_add[row] = item
        return items_to_add


class RelationshipParameterDefinitionModel(ParameterDefinitionModel, RelationshipParameterModel):
    """A model of relationship parameter data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)

    def init_model(self, skip_fields=[]):
        """Initialize model from source database."""
        data = self.db_map.relationship_parameter_list()
        fields = self.db_map.relationship_parameter_fields()
        header = [x for x in fields if x not in skip_fields]
        self.set_horizontal_header_labels(header)
        model_data = [[v for k, v in r._asdict().items() if k not in skip_fields] for r in data]
        # Prepare decoration role data
        aux_data = []
        aux_data_append = aux_data.append
        row_range = range(len(model_data[0]))
        relationship_class_id_column = header.index('relationship_class_id')
        relationship_class_name_column = header.index('relationship_class_name')
        object_class_name_list_column = header.index('object_class_name_list')
        for model_row in model_data:
            aux_row = [{} for i in row_range]
            relationship_class_id = model_row[relationship_class_id_column]
            icon = self.relationship_icon_dict[relationship_class_id]
            aux_row[relationship_class_name_column][Qt.DecorationRole] = icon
            aux_data_append(aux_row)
        self.reset_model(model_data, aux_data=aux_data)
        column_names = ['id', 'relationship_class_name', 'object_class_name_list']
        self.make_data_fixed(column_names=column_names)

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("relationship_class", "object_class"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        if renamed_type == "relationship_class":
            column = header_index("relationship_class_name")
            for row in row_range:
                try:
                    curr_name = self._main_data[row][column]
                    new_name = names_dict[curr_name]
                    self._main_data[row][column] = new_name
                except KeyError:
                    continue
        elif renamed_type == "object_class":
            column = header_index("object_class_name_list")
            for row in row_range:
                object_class_name_list = self.index(row, column).data(Qt.DisplayRole).split(",")
                for i, object_class_name in enumerate(object_class_name_list):
                    try:
                        object_class_name_list[i] = names_dict[object_class_name]
                    except KeyError:
                        continue
                self._main_data[row][column] = ",".join(object_class_name_list)

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("relationship_class", "object_class"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        header_index = self.horizontal_header_labels().index
        if removed_type == "relationship_class":
            column = header_index("relationship_class_name")
            for row in reversed(row_range):
                try:
                    name = self._main_data[row][column]
                except KeyError:
                    continue
                if name in removed_names:
                    super().removeRows(row, 1)
        elif removed_type == "object_class":
            column = header_index("object_class_name_list")
            for row in reversed(row_range):
                try:
                    object_class_name_list = self._main_data[row][column].split(",")
                except KeyError:
                    continue
                for object_class_name in object_class_name_list:
                    if object_class_name in removed_names:
                        super().removeRows(row, 1)
                        break

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db.
        Also extend the given list of indexes if some are autoset."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        relationship_class_id_column = header.index('relationship_class_id')
        relationship_class_name_column = header.index('relationship_class_name')
        object_class_id_list_column = header.index('object_class_id_list')
        object_class_name_list_column = header.index('object_class_name_list')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        relationship_class_dict = {
            x.name: {
                'id': x.id,
                'object_class_id_list': x.object_class_id_list,
                'object_class_name_list': x.object_class_name_list
            } for x in self.db_map.wide_relationship_class_list()}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            if not self.is_work_in_progress(row):
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            object_class_name_list = self.index(row, object_class_name_list_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            try:
                relationship_class = relationship_class_dict[relationship_class_name]
            except KeyError:
                continue
            new_object_class_name_list = relationship_class['object_class_name_list']
            relationship_class_id = relationship_class['id']
            self._main_data[row][relationship_class_id_column] = relationship_class_id
            self._main_data[row][object_class_id_list_column] = relationship_class['object_class_id_list']
            self._main_data[row][object_class_name_list_column] = new_object_class_name_list
            if new_object_class_name_list != object_class_name_list:
                indexes.append(self.index(row, object_class_name_list_column))
            if not parameter_name:
                continue
            item = {
                "relationship_class_id": relationship_class_id,
                "name": parameter_name
            }
            for column in range(parameter_name_column + 1, self.columnCount()):
                item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
            items_to_add[row] = item
        return items_to_add


class ObjectParameterValueModel(ParameterValueModel, ObjectParameterModel):
    """A model of object parameter value data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)

    def init_model(self, skip_fields=['parameter_id']):
        """Initialize model from source database."""
        data = self.db_map.object_parameter_value_list()
        fields = self.db_map.object_parameter_value_fields()
        header = [x for x in fields if x not in skip_fields]
        self.set_horizontal_header_labels(header)
        model_data = [[v for k, v in r._asdict().items() if k not in skip_fields] for r in data]
        aux_data = self.decoration_role_data(model_data)
        self.reset_model(model_data, aux_data=aux_data)
        column_names = ['id', 'object_class_name', 'object_name', 'parameter_name']
        self.make_data_fixed(column_names=column_names)

    def init_model_from_data(self, model_data, header):
        """Initialize model from source database."""
        self.set_horizontal_header_labels(header)
        aux_data = self.decoration_role_data(model_data)
        self.reset_model(model_data, aux_data=aux_data)
        column_names = ['id', 'object_class_name', 'object_name', 'parameter_name']
        self.make_data_fixed(column_names=column_names)

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("object_class", "object", "parameter"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        names_dict = dict(zip(curr_names, new_names))
        header_index = self.horizontal_header_labels().index
        if renamed_type == "object_class":
            column = header_index("object_class_name")
        elif renamed_type == "object":
            column = header_index("object_name")
        elif renamed_type == "parameter":
            column = header_index("parameter_name")
        for row in row_range:
            try:
                curr_name = self._main_data[row][column]
                new_name = names_dict[curr_name]
                self._main_data[row][column] = new_name
            except KeyError:
                continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("object_class", "object", "parameter"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        header_index = self.horizontal_header_labels().index
        if removed_type == "object_class":
            column = header_index("object_class_name")
        elif removed_type == "object":
            column = header_index("object_name")
        elif removed_type == "parameter":
            column = header_index("parameter_name")
        for row in reversed(row_range):
            try:
                name = self._main_data[row][column]
            except KeyError:
                continue
            if name in removed_names:
                super().removeRows(row, 1)

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db.
        Also extend the given list of indexes if some are autoset."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        object_class_id_column = header.index('object_class_id')
        object_class_name_column = header.index('object_class_name')
        object_id_column = header.index('object_id')
        object_name_column = header.index('object_name')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        object_class_id_name_dict = {x.id: x.name for x in self.db_map.object_class_list()}
        object_class_name_id_dict = {x.name: x.id for x in self.db_map.object_class_list()}
        object_dict = {x.name: {'id': x.id, 'class_id': x.class_id} for x in self.db_map.object_list()}
        parameter_dict = {x.name: {'id': x.id, 'object_class_id': x.object_class_id}
                          for x in self.db_map.parameter_list()}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            if not self.is_work_in_progress(row):
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            object_name = self.index(row, object_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            # Find object class id
            object_class_ids = list()
            try:
                object_class_id = object_class_name_id_dict[object_class_name]
                object_class_ids.append(object_class_id)
            except KeyError:
                pass
            object_ = object_dict.get(object_name)
            parameter = parameter_dict.get(parameter_name)
            if object_:
                object_class_ids.append(object_['class_id'])
            if parameter:
                object_class_ids.append(parameter['object_class_id'])
            if object_class_ids and object_class_ids.count(object_class_ids[0]) != len(object_class_ids):
                # Not all of them are equal
                continue
            object_class_id = object_class_ids[0]
            try:
                correct_object_class_name = object_class_id_name_dict[object_class_id]
            except KeyError:
                continue
            self._main_data[row][object_class_id_column] = object_class_id
            self._main_data[row][object_class_name_column] = correct_object_class_name
            if correct_object_class_name != object_class_name:
                indexes.append(self.index(row, object_class_name_column))
            if object_ is None:
                continue
            object_id = object_['id']
            self._main_data[row][object_id_column] = object_id
            if parameter is None:
                continue
            parameter_id = parameter['id']
            item = {
                "object_id": object_id,
                "parameter_id": parameter_id
            }
            for column in range(parameter_name_column + 1, self.columnCount()):
                item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
            items_to_add[row] = item
        return items_to_add


class RelationshipParameterValueModel(ParameterValueModel, RelationshipParameterModel):
    """A model of relationship parameter value data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None, has_empty_row=True):
        """Initialize class."""
        super().__init__(tree_view_form, has_empty_row=has_empty_row)
        self.object_name_range = None  # Range of column indices that are part of the object name list

    def set_object_icons(self, top, left, bottom, right, header):
        """Set object icons."""
        object_name_columns = [x for x in range(left, right + 1) if x in self.object_name_range]
        if not object_name_columns:
            return
        object_dict = {x.name: x.class_id for x in self.db_map.object_list()}
        for row in range(top, bottom + 1):
            for column in object_name_columns:
                object_name = self._main_data[row][column]
                try:
                    object_class_id = object_dict[object_name]
                    icon = self.object_icon_dict[object_class_id]
                    self._aux_data[row][column][Qt.DecorationRole] = icon
                except KeyError:
                    continue
        new_top_left = self.index(top, object_name_columns[0])
        new_bottom_right = self.index(bottom, object_name_columns[-1])
        self.dataChanged.emit(new_top_left, new_bottom_right, [Qt.DecorationRole])

    def init_model(self, skip_fields=['parameter_id']):
        """Initialize model from source database."""
        data = self.db_map.relationship_parameter_value_list()
        fields = self.db_map.relationship_parameter_value_fields()
        header = [x for x in fields if x not in skip_fields]
        # Split single 'object_name_list' column into several 'object_name' columns
        relationship_class_list = self.db_map.wide_relationship_class_list()
        object_class_id_list_index = header.index("object_class_id_list")
        object_name_list_index = header.index("object_name_list")
        max_object_name_list_length = max(
            [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=1)
        self.object_name_range = range(object_name_list_index, object_name_list_index + max_object_name_list_length)
        header.pop(object_name_list_index)
        object_name_header = ["object_name" for k in range(max_object_name_list_length)]
        fix_name_ambiguity(object_name_header)
        for k, i in enumerate(self.object_name_range):
            header.insert(i, object_name_header[k])
        self.set_horizontal_header_labels(header)
        # Compute model and aux data: split single 'object_name_list' value into several 'object_name' values
        model_data = list()
        model_data_append = model_data.append
        aux_data = []
        aux_data_append = aux_data.append
        relationship_class_id_column = header.index('relationship_class_id')
        relationship_class_name_column = header.index('relationship_class_name')
        for row in data:
            model_row = [v for k, v in row._asdict().items() if k not in skip_fields]
            object_name_list = model_row.pop(object_name_list_index).split(',')
            for i in range(max_object_name_list_length):
                try:
                    object_name = object_name_list[i]
                    model_row.insert(object_name_list_index + i, object_name)
                except IndexError:
                    model_row.insert(object_name_list_index + i, None)
            model_data_append(model_row)
            aux_row = [{} for i in model_row]
            object_class_id_list = [int(x) for x in model_row[object_class_id_list_index].split(',')]
            for i in range(max_object_name_list_length):
                try:
                    object_class_id = object_class_id_list[i]
                    object_icon = self.object_icon_dict[object_class_id]
                    aux_row[object_name_list_index + i][Qt.DecorationRole] = object_icon
                except IndexError:
                    pass
            relationship_class_id = model_row[relationship_class_id_column]
            relationship_icon = self.relationship_icon_dict[relationship_class_id]
            aux_row[relationship_class_name_column][Qt.DecorationRole] = relationship_icon
            aux_data_append(aux_row)
        self.reset_model(model_data, aux_data=aux_data)
        object_name_header = [header[x] for x in self.object_name_range]
        column_names = ['id', 'relationship_class_name', *object_name_header, 'parameter_name']
        self.make_data_fixed(column_names=column_names)

    def init_model_from_data(self, model_data, header, object_name_range):
        """Initialize model from source database."""
        self.set_horizontal_header_labels(header)
        self.object_name_range = object_name_range
        self.reset_model(model_data)
        object_name_header = [header[x] for x in self.object_name_range]
        column_names = ['id', 'relationship_class_name', *object_name_header, 'parameter_name']
        self.make_data_fixed(column_names=column_names)

    def rename_items(self, renamed_type, new_names, curr_names):
        if renamed_type not in ("relationship_class", "object", "parameter"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        names_dict = dict(zip(curr_names, new_names))
        if renamed_type == "object":
            for row in row_range:
                for column in self.object_name_range:
                    try:
                        curr_name = self._main_data[row][column]
                        new_name = names_dict[curr_name]
                        self._main_data[row][column] = new_name
                    except KeyError:
                        continue
        elif renamed_type in ("relationship_class", "parameter"):
            header_index = self.horizontal_header_labels().index
            if renamed_type in "relationship_class":
                column = header_index("relationship_class_name")
            elif renamed_type in "parameter":
                column = header_index("parameter_name")
            for row in row_range:
                try:
                    curr_name = self._main_data[row][column]
                    new_name = names_dict[curr_name]
                    self._main_data[row][column] = new_name
                except KeyError:
                    continue

    def remove_items(self, removed_type, *removed_names):
        if removed_type not in ("relationship_class", "object", "parameter"):
            return
        row_range = range(self.rowCount() - 1) if self.has_empty_row else range(self.rowCount())
        if removed_type == "object":
            for row in reversed(row_range):
                for column in self.object_name_range:
                    try:
                        name = self._main_data[row][column]
                    except KeyError:
                        continue
                    if name in removed_names:
                        super().removeRows(row, 1)
                        break
        elif removed_type in ("relationship_class", "parameter"):
            header_index = self.horizontal_header_labels().index
            if removed_type in "relationship_class":
                column = header_index("relationship_class_name")
            elif removed_type in "parameter":
                column = header_index("parameter_name")
            for row in reversed(row_range):
                try:
                    name = self._main_data[row][column]
                except KeyError:
                    continue
                if name in removed_names:
                    super().removeRows(row, 1)

    def extend_object_name_range(self, length):
        """Extend object name range to fit given length."""
        curr_length = len(self.object_name_range)
        diff = length - curr_length
        if diff <= 0:
            return
        self.insertColumns(self.object_name_range.stop, diff)
        object_name_header_ext = ["object_name [{}]".format(str(i + 1)) for i in range(curr_length, length)]
        object_name_header_ext = ["object_name" for i in range(diff)]
        fix_name_ambiguity(object_name_header_ext, offset=curr_length)
        self.insert_horizontal_header_labels(self.object_name_range.stop, object_name_header_ext)
        self.object_name_range = range(self.object_name_range.start, self.object_name_range.stop + diff)
        self.make_data_fixed(column_names=object_name_header_ext)

    def batch_set_wip_data(self, indexes, data):
        """Batch set work in progress data. Update model first, then see if the database
        needs to be updated as well."""
        if not indexes:
            return False
        for k, index in enumerate(indexes):
            self._main_data[index.row()][index.column()] = data[k]
        relationships_on_the_fly = self.relationships_on_the_fly(indexes)
        self.add_items_to_db(self.items_to_add(indexes, relationships_on_the_fly))
        return True

    def relationships_on_the_fly(self, indexes):
        """Return a dict of row (int) to relationship item (KeyedTuple),
        either retrieved or added on the fly.
        Also extend `indexes` with the ones that are 'autoset'.
        """
        relationships_on_the_fly = dict()
        relationships_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        relationship_class_name_column = header.index('relationship_class_name')
        object_id_list_column = header.index('object_id_list')
        object_name1_column = self.object_name_range.start
        # Query db and build ad-hoc dicts
        relationship_class_dict = {
            x.name: {
                'id': x.id,
                'object_class_count': len(x.object_class_id_list.split(','))
            } for x in self.db_map.wide_relationship_class_list()}
        relationship_dict = {
            x.id: (x.class_id, [int(y) for y in x.object_id_list.split(",")])
            for x in self.db_map.wide_relationship_list()}
        relationship_dict = {(x.class_id, x.object_id_list): x.id for x in self.db_map.wide_relationship_list()}
        object_dict = {x.name: x.id for x in self.db_map.object_list()}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            if not self.is_work_in_progress(row):
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            try:
                relationship_class = relationship_class_dict[relationship_class_name]
            except KeyError:
                continue
            object_id_list = list()
            object_name_list = list()
            object_class_count = relationship_class['object_class_count']
            for j in range(object_name1_column, object_name1_column + object_class_count):
                object_name = self.index(row, j).data(Qt.DisplayRole)
                try:
                    object_id = object_dict[object_name]
                    object_id_list.append(object_id)
                    object_name_list.append(object_name)
                except KeyError:
                    break
            if len(object_id_list) < object_class_count or len(object_name_list) < object_class_count:
                continue
            join_object_id_list = ",".join([str(x) for x in object_id_list])
            try:
                relationship_id = relationship_dict[relationship_class['id'], join_object_id_list]
                relationships_on_the_fly[row] = relationship_id
            except KeyError:
                relationship_name = relationship_class_name + "_" + "__".join(object_name_list)
                relationship = {
                    "name": relationship_name,
                    "object_id_list": object_id_list,
                    "class_id": relationship_class['id']
                }
                relationships_to_add[row] = relationship
            self._main_data[row][object_id_list_column] = join_object_id_list
        relationships = self.new_relationships(relationships_to_add)
        if relationships:
            relationships_on_the_fly.update(relationships)
        return relationships_on_the_fly

    def new_relationships(self, relationships_to_add):
        """Add relationships to database on the fly."""
        if not relationships_to_add:
            return {}
        try:
            items = list(relationships_to_add.values())
            rows = list(relationships_to_add.keys())
            relationships = self.db_map.add_wide_relationships(*items)
            for relationship in relationships:
                self._tree_view_form.object_tree_model.add_relationship(relationship)
            msg = "Successfully added new relationships on the fly."
            self._tree_view_form.msg.emit(msg)
            return dict(zip(rows, [x.id for x in relationships]))
        except SpineIntegrityError as e:
            self._tree_view_form.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)

    def items_to_add(self, indexes, relationships_on_the_fly):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header = self.horizontal_header_labels()
        relationship_class_id_column = header.index('relationship_class_id')
        relationship_class_name_column = header.index('relationship_class_name')
        object_class_id_list_column = header.index('object_class_id_list')
        parameter_name_column = header.index('parameter_name')
        # Query db and build ad-hoc dicts
        relationship_class_name_id_dict = {
            x.name: x.id for x in self.db_map.wide_relationship_class_list()}
        relationship_class_dict = {
            x.id: {
                "name": x.name,
                "object_class_id_list": x.object_class_id_list
            } for x in self.db_map.wide_relationship_class_list()}
        parameter_dict = {
            x.name: {
                'id': x.id,
                'relationship_class_id': x.relationship_class_id
            } for x in self.db_map.parameter_list()}
        for row in {ind.row() for ind in indexes}:
            if not self.is_work_in_progress(row):
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            parameter = parameter_dict.get(parameter_name)
            # Find relationship_class_id
            relationship_class_ids = list()
            try:
                relationship_class_id = relationship_class_name_id_dict[relationship_class_name]
                relationship_class_ids.append(relationship_class_id)
            except KeyError:
                pass
            if parameter:
                relationship_class_ids.append(parameter['relationship_class_id'])
            if relationship_class_ids \
                    and relationship_class_ids.count(relationship_class_ids[0]) != len(relationship_class_ids):
                # Not all of them are equal
                continue
            relationship_class_id = relationship_class_ids[0]
            try:
                correct_relationship_class_name = relationship_class_dict[relationship_class_id]['name']
                object_class_id_list = relationship_class_dict[relationship_class_id]['object_class_id_list']
            except KeyError:
                continue
            self._main_data[row][relationship_class_id_column] = relationship_class_id
            self._main_data[row][relationship_class_name_column] = correct_relationship_class_name
            self._main_data[row][object_class_id_list_column] = object_class_id_list
            if correct_relationship_class_name != relationship_class_name:
                indexes.append(self.index(row, relationship_class_name_column))
            if parameter is None:
                continue
            try:
                relationship_id = relationships_on_the_fly[row]
            except KeyError:
                continue
            parameter_id = parameter['id']
            item = {
                "relationship_id": relationship_id,
                "parameter_id": parameter_id
            }
            for column in range(parameter_name_column + 1, self.columnCount()):
                item[header[column]] = self.index(row, column).data(Qt.DisplayRole)
            items_to_add[row] = item
        return items_to_add


class AutoFilterProxy(QSortFilterProxyModel):
    """A custom sort filter proxy model which implementes a two-level filter."""
    def __init__(self, tree_view_form=None):
        """Initialize class."""
        super().__init__(tree_view_form)
        self.header_index = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.italic_font = QFont()
        self.italic_font.setItalic(True)
        self.rule_dict = dict()
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.filter_is_valid = True  # Set it to False when filter needs to be applied

    def index(self, row, column, parent=QModelIndex()):
        if row < 0 or column < 0 or column >= self.columnCount(parent):
            return QModelIndex()
        if self.sourceModel().can_grow:
            index = super().index(row, column, parent)
            source_parent = self.mapToSource(parent)
            while not index.isValid():
                self.sourceModel().insertRows(
                    self.sourceModel().rowCount(source_parent), 1, source_parent)
                index = super().index(row, column, parent)
            return index
        if row >= self.rowCount(parent):
            return QModelIndex()
        return super().index(row, column, parent)

    def setSourceModel(self, source_model):
        super().setSourceModel(source_model)
        source_model.headerDataChanged.connect(self.receive_header_data_changed)
        self.receive_header_data_changed()

    def horizontal_header_labels(self):
        return [self.headerData(i, Qt.Horizontal) for i in range(self.columnCount())]

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        if orientation == Qt.Horizontal:
            self.header_index = self.sourceModel().horizontal_header_labels().index

    def batch_set_data(self, proxy_indexes, values):
        source_indexes = [self.mapToSource(ind) for ind in proxy_indexes]
        return self.sourceModel().batch_set_data(source_indexes, values)

    def is_work_in_progress(self, row):
        """Return whether or not row is a work in progress."""
        return self.sourceModel().is_work_in_progress(self.map_row_to_source(row))

    def map_row_to_source(self, row):
        return self.mapToSource(self.index(row, 0)).row()

    def autofilter_values(self, column):
        """Return values for the autofilter menu of `column`."""
        values = set()
        source_model = self.sourceModel()
        for source_row in range(source_model.rowCount()):
            # Skip values rejected by filter if row is not wip
            if not source_model.is_work_in_progress(source_row) \
                    and not self.filter_accepts_row(source_row, QModelIndex()):
                continue
            # Skip values rejected by autofilters from *other* columns
            if not self.autofilter_accepts_row(source_row, QModelIndex(), skip_source_column=[column]):
                continue
            try:
                value = source_model._main_data[source_row][column]
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
                data = self.sourceModel()._main_data[source_row][source_column]
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


class ObjectParameterDefinitionProxy(AutoFilterProxy):
    """A model to filter object parameter data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None):
        """Initialize class."""
        super().__init__(tree_view_form)
        self.object_class_id_set = set()
        self.object_class_id_column = None
        self.object_class_name_column = None

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_class_id_column = self.header_index("object_class_id")
            self.object_class_name_column = self.header_index("object_class_name")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept rows."""
        source_model = self.sourceModel()
        if self.object_class_id_set:
            object_class_id = source_model._main_data[source_row][self.object_class_id_column]
            if object_class_id not in self.object_class_id_set:
                return False
            source_model._aux_data[source_row][self.object_class_name_column][Qt.FontRole] = self.bold_font
        return True

    def clear_object_class_id_set(self):
        if not self.object_class_id_set:
            return
        self.object_class_id_set.clear()
        self.invalidate_filter()

    def update_object_class_id_set(self, ids):
        if self.object_class_id_set.issuperset(ids):
            return
        self.object_class_id_set.update(ids)
        self.invalidate_filter()

    def diff_update_object_class_id_set(self, ids):
        if self.object_class_id_set.isdisjoint(ids):
            return
        self.object_class_id_set.difference_update(ids)
        self.invalidate_filter()

    def invalidate_filter(self):
        self.filter_is_valid = False
        self.clear_autofilter()
        for row_data in self.sourceModel()._aux_data:
            row_data[self.object_class_name_column][Qt.FontRole] = None
        row_count = self.sourceModel().rowCount()
        top_left = self.sourceModel().index(0, self.object_class_name_column)
        bottom_right = self.sourceModel().index(row_count - 1, self.object_class_name_column)
        self.sourceModel().dataChanged.emit(top_left, bottom_right, [Qt.FontRole])


class ObjectParameterValueProxy(ObjectParameterDefinitionProxy):
    """A model to filter object parameter value data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None):
        """Initialize class."""
        super().__init__(tree_view_form)
        self.object_id_set = set()
        self.object_id_column = None
        self.object_name_column = None

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_id_column = self.header_index("object_id")
            self.object_name_column = self.header_index("object_name")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept rows."""
        if not super().filter_accepts_row(source_row, source_parent):
            return False
        source_model = self.sourceModel()
        if self.object_id_set:
            object_id = source_model._main_data[source_row][self.object_id_column]
            if object_id not in self.object_id_set:
                return False
            source_model._aux_data[source_row][self.object_name_column][Qt.FontRole] = self.bold_font
        return True

    def clear_object_id_set(self):
        if not self.object_id_set:
            return
        self.object_id_set.clear()
        self.invalidate_filter()

    def update_object_id_set(self, ids):
        if self.object_id_set.issuperset(ids):
            return
        self.object_id_set.update(ids)
        self.invalidate_filter()

    def diff_update_object_id_set(self, ids):
        if self.object_id_set.isdisjoint(ids):
            return
        self.object_id_set.difference_update(ids)
        self.invalidate_filter()

    def invalidate_filter(self):
        super().invalidate_filter()
        for row_data in self.sourceModel()._aux_data:
            row_data[self.object_name_column][Qt.FontRole] = None
        row_count = self.sourceModel().rowCount()
        top_left = self.sourceModel().index(0, self.object_name_column)
        bottom_right = self.sourceModel().index(row_count - 1, self.object_name_column)
        self.sourceModel().dataChanged.emit(top_left, bottom_right, [Qt.FontRole])


class RelationshipParameterDefinitionProxy(AutoFilterProxy):
    """A model to filter relationship parameter data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None):
        """Initialize class."""
        super().__init__(tree_view_form)
        self.relationship_class_id_set = set()
        self.object_class_id_set = set()
        self.relationship_class_id_column = None
        self.relationship_class_name_column = None
        self.object_class_id_list_column = None

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.relationship_class_id_column = self.header_index("relationship_class_id")
            self.relationship_class_name_column = self.header_index("relationship_class_name")
            self.object_class_id_list_column = self.header_index("object_class_id_list")

    def filter_accepts_row(self, source_row, source_parent):
        """Accept row."""
        source_model = self.sourceModel()
        if self.relationship_class_id_set:
            relationship_class_id = source_model._main_data[source_row][self.relationship_class_id_column]
            if relationship_class_id not in self.relationship_class_id_set:
                return False
            source_model._aux_data[source_row][self.relationship_class_name_column][Qt.FontRole] = self.bold_font
        if self.object_class_id_set:
            object_class_id_list = source_model._main_data[source_row][self.object_class_id_list_column]
            if not object_class_id_list:
                return False  # FIXME: This shouldn't happen
            if self.object_class_id_set.isdisjoint([int(x) for x in object_class_id_list.split(",")]):
                return False
            source_model._aux_data[source_row][self.relationship_class_name_column][Qt.FontRole] = self.bold_font
        return True

    def clear_relationship_class_id_set(self):
        if not self.relationship_class_id_set:
            return
        self.relationship_class_id_set.clear()
        self.invalidate_filter()

    def update_relationship_class_id_set(self, ids):
        if self.relationship_class_id_set.issuperset(ids):
            return
        self.relationship_class_id_set.update(ids)
        self.invalidate_filter()

    def diff_update_relationship_class_id_set(self, ids):
        if self.relationship_class_id_set.isdisjoint(ids):
            return
        self.relationship_class_id_set.difference_update(ids)
        self.invalidate_filter()

    def clear_object_class_id_set(self):
        if not self.object_class_id_set:
            return
        self.object_class_id_set.clear()
        self.invalidate_filter()

    def update_object_class_id_set(self, ids):
        if self.object_class_id_set.issuperset(ids):
            return
        self.object_class_id_set.update(ids)
        self.invalidate_filter()

    def diff_update_object_class_id_set(self, ids):
        if self.object_class_id_set.isdisjoint(ids):
            return
        self.object_class_id_set.difference_update(ids)
        self.invalidate_filter()

    def invalidate_filter(self):
        self.filter_is_valid = False
        self.clear_autofilter()
        for row_data in self.sourceModel()._aux_data:
            row_data[self.relationship_class_name_column][Qt.FontRole] = None
        row_count = self.sourceModel().rowCount()
        top_left = self.sourceModel().index(0, self.relationship_class_name_column)
        bottom_right = self.sourceModel().index(row_count - 1, self.relationship_class_name_column)
        self.sourceModel().dataChanged.emit(top_left, bottom_right, [Qt.FontRole])


class RelationshipParameterValueProxy(RelationshipParameterDefinitionProxy):
    """A model to filter relationship parameter value data, used by TreeViewForm."""
    def __init__(self, tree_view_form=None):
        """Initialize class."""
        super().__init__(tree_view_form)
        self.object_id_set = set()
        self.object_id_list_set = set()  # Set of string
        self.object_id_list_column = None
        self.object_name_range = None
        self.object_count = 0

    @Slot("Qt.Orientation", "int", "int", name="receive_header_data_changed")
    def receive_header_data_changed(self, orientation=Qt.Horizontal, first=0, last=0):
        super().receive_header_data_changed(orientation, first, last)
        if self.header_index:
            self.object_id_list_column = self.header_index("object_id_list")
        self.object_name_range = self.sourceModel().object_name_range

    def filter_accepts_row(self, source_row, source_parent):
        """Accept row."""
        if not super().filter_accepts_row(source_row, source_parent):
            return False
        source_model = self.sourceModel()
        object_id_list = source_model._main_data[source_row][self.object_id_list_column]
        split_object_id_list = [int(x) for x in object_id_list.split(",")]
        if self.object_id_list_set:
            if object_id_list not in self.object_id_list_set:
                return False
            for j in range(len(split_object_id_list)):
                source_model._aux_data[source_row][self.object_name_range.start + j][Qt.FontRole] = self.bold_font
        if self.object_id_set:
            found = False
            for j, object_id in enumerate(split_object_id_list):
                if object_id in self.object_id_set:
                    source_model._aux_data[source_row][self.object_name_range.start + j][Qt.FontRole] = self.bold_font
                    found = True
            if not found:
                return False
        # If this row passes, update the object count
        self.object_count = max(self.object_count, len(split_object_id_list))
        return True

    def clear_object_id_set(self):
        self.object_count = 0
        if not self.object_id_set:
            return
        self.object_id_set.clear()
        self.invalidate_filter()

    def update_object_id_set(self, ids):
        self.object_count = 0
        if self.object_id_set.issuperset(ids):
            return
        self.object_id_set.update(ids)
        self.invalidate_filter()

    def diff_update_object_id_set(self, ids):
        self.object_count = 0
        if self.object_id_set.isdisjoint(ids):
            return
        self.object_id_set.difference_update(ids)
        self.invalidate_filter()

    def clear_object_id_list_set(self):
        self.object_count = 0
        if not self.object_id_list_set:
            return
        self.object_id_list_set.clear()
        self.invalidate_filter()

    def update_object_id_list_set(self, id_lists):
        self.object_count = 0
        if self.object_id_list_set.issuperset(id_lists):
            return
        self.object_id_list_set.update(id_lists)
        self.invalidate_filter()

    def diff_update_object_id_list_set(self, id_lists):
        self.object_count = 0
        if self.object_id_list_set.isdisjoint(id_lists):
            return
        self.object_id_list_set.difference_update(id_lists)
        self.invalidate_filter()

    def invalidate_filter(self):
        super().invalidate_filter()
        self.object_count = 0
        for row_data in self.sourceModel()._aux_data:
            for j in self.object_name_range:
                row_data[j][Qt.FontRole] = None
        row_count = self.sourceModel().rowCount()
        top_left = self.sourceModel().index(0, self.object_name_range.start)
        bottom_right = self.sourceModel().index(row_count - 1, self.object_name_range.stop - 1)
        self.sourceModel().dataChanged.emit(top_left, bottom_right, [Qt.FontRole])


class JSONModel(MinimalTableModel):
    """A model of JSON array data, used by TreeViewForm.
    TODO: Handle the JSON object data type.

    Attributes:
        parent (JSONEditor): the parent widget
        stride (int): The number of elements to fetch
    """
    def __init__(self, parent, stride=256):
        """Initialize class"""
        super().__init__(parent, can_grow=True)
        self._json = list()
        self.set_horizontal_header_labels(["json"])
        self._stride = stride

    def reset_model(self, json, flags=None, has_empty_row=True):
        """Store JSON array into a list.
        Initialize `stride` rows.
        """
        if json:
            self._json = [x.strip() for x in json[1:-1].split(",")]
        if flags:
            self.default_flags = flags
        self.has_empty_row = has_empty_row
        data = list()
        for i in range(self._stride):
            try:
                data.append([self._json.pop(0)])
            except IndexError:
                break
        super().reset_model(data)

    def canFetchMore(self, parent):
        return len(self._json) > 0

    def fetchMore(self, parent):
        """Pop data from the _json attribute and add it to the model."""
        data = list()
        count = 0
        for i in range(self._stride):
            try:
                data.append(self._json.pop(0))
                count += 1
            except IndexError:
                break
        last_data_row = self.rowCount() - 1 if self.has_empty_row else self.rowCount()
        self.insertRows(last_data_row, count)
        indexes = [self.index(last_data_row + i, 0) for i in range(count)]
        self.batch_set_data(indexes, data)

    def json(self):
        """Return data into JSON array."""
        last_data_row = self.rowCount() - 1 if self.has_empty_row else self.rowCount()
        new_json = [self.index(i, 0).data() for i in range(last_data_row)]
        new_json.extend(self._json)  # Whatever remains unfetched
        if not new_json:
            return None
        return "[" + ", ".join(new_json) + "]"


class DatapackageResourcesModel(QStandardItemModel):
    """A model of datapackage resource data, used by SpineDatapackageWidget."""
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
    """A model of datapackage field data, used by SpineDatapackageWidget."""
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
    """A model of datapackage foreign key data, used by SpineDatapackageWidget."""
    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__(parent, has_empty_row=True)
        # TODO: Change parent (attribute name) to something else
        self.schema = None
        self.set_horizontal_header_labels(["fields", "reference resource", "reference fields"])
        self.clear()

    def reset_model(self, schema):
        self.schema = schema
        data = list()
        for foreign_key in schema.foreign_keys:
            fields = foreign_key['fields']
            reference_resource = foreign_key['reference']['resource']
            reference_fields = foreign_key['reference']['fields']
            data.append([fields, reference_resource, reference_fields])
        super().reset_model(data)
