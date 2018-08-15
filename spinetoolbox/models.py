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


:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   23.1.2018
"""

import logging
import os
from PySide2.QtCore import Qt, Signal, QModelIndex, QAbstractListModel, QAbstractTableModel,\
    QSortFilterProxyModel
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QFont, QIcon, QPixmap
from PySide2.QtWidgets import QMessageBox
from config import INVALID_CHARS, TOOL_OUTPUT_DIR


class ProjectItemModel(QStandardItemModel):
    """Class to store project items, e.g. Data Stores, Data Connections, Tools, Views."""
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent

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
            QMessageBox.information(self._parent, "Invalid characters", msg)
            return False
        # Check if project item with the same name already exists
        taken_names = self.return_item_names()
        if value in taken_names:
            msg = "Project item <b>{0}</b> already exists".format(value)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._parent, "Invalid name", msg)
            return False
        # Check that no existing project item short name matches the new item's short name.
        # This is to prevent two project items from using the same folder.
        new_short_name = value.lower().replace(' ', '_')
        for taken_name in taken_names:
            taken_short_name = taken_name.lower().replace(' ', '_')
            if new_short_name == taken_short_name:
                msg = "Project item using directory <b>{0}</b> already exists".format(taken_short_name)
                # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                QMessageBox.information(self._parent, "Invalid name", msg)
                return False
        # Get old data dir which will be renamed
        try:
            old_data_dir = item.data_dir  # Full path
        except AttributeError:
            logging.error("Item does not have a data_dir. Make sure that class {0} creates one.".format(item.item_type))
            return False
        # Get project path from the old data dir path
        project_path = os.path.split(old_data_dir)[0]
        # Make path for new data dir
        new_data_dir = os.path.join(project_path, new_short_name)
        # Rename item project directory
        try:
            os.rename(old_data_dir, new_data_dir)
        except FileExistsError:
            msg = "Directory<br/><b>{0}</b><br/>already exists".format(new_data_dir)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._parent, "Renaming directory failed", msg)
            return False
        except PermissionError:
            msg = "Access to directory <br/><b>{0}</b><br/>denied." \
                  "<br/><br/>Possible reasons:" \
                  "<br/>1. Windows Explorer is open in the directory" \
                  "<br/>2. Permission error" \
                  "<br/><br/>Check these and try again.".format(old_data_dir)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._parent, "Renaming directory failed", msg)
            return False
        except OSError:
            msg = "Renaming input directory failed. OSError in" \
                  "<br/><b>{0}</b><br/>Possibly because Windows " \
                  "Explorer is open in the directory".format(old_data_dir)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._parent, "Renaming directory failed", msg)
            return False
        # Find item from project refs list
        project_refs = self._parent.project_refs
        item_ref = None
        for ref in project_refs:
            if ref.name == old_name:
                ref_index = project_refs.index(ref)
                item_ref = project_refs.pop(ref_index)
                break
        # Change name for item in project ref list
        item_ref.set_name(value)
        self._parent.project_refs.append(item_ref)
        # Update DisplayRole of the QStardardItem in Project QTreeView
        q_item = self.find_item(old_name, Qt.MatchExactly | Qt.MatchRecursive)
        q_item.setData(value, Qt.DisplayRole)
        # Rename project item contained in the QStandardItem
        item.set_name(value)
        # Update project item directory variable
        item.data_dir = new_data_dir
        # If item is a Tool, also output_dir must be updated
        if item.item_type == "Tool":
            item.output_dir = os.path.join(item.data_dir, TOOL_OUTPUT_DIR)
        # Update name in the subwindow widget
        item.get_widget().set_name_label(value)
        # Update name item of the QGraphicsItem
        item.get_icon().update_name_item(value)
        # Change old item names in connection model headers to the new name
        header_index = self._parent.connection_model.find_index_in_header(old_name)
        self._parent.connection_model.setHeaderData(header_index, Qt.Horizontal, value)
        self._parent.connection_model.setHeaderData(header_index, Qt.Vertical, value)
        # Force save project
        self._parent.save_project()
        self._parent.msg_success.emit("Project item <b>{0}</b> renamed to <b>{1}</b>".format(old_name, value))
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
            match_flags (QFlags): Or combination of Qt.MatchFlag types

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
    def __init__(self, parent=None):
        super().__init__()
        self._tools = list()
        self._tools.append('No Tool template')  # TODO: Try to get rid of this
        self._parent = parent

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

    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent  # QMainWindow
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
        """Removes count rows starting with the given row under parent parent from the model.

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
        """Removes count columns starting with the given column under parent parent from the model.

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

    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__()
        self._parent = parent  # QMainWindow
        self._data = list()
        self.header = list()

    def flags(self, index):
        """Returns flags for table items."""
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """Number of rows in the model."""
        return len(self._data)

    def columnCount(self, *args, **kwargs):
        """Number of columns in the model."""
        return len(self.header)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Get headers."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                h = self.header[section]
            except IndexError:
                return None
            return h
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Sets the data for the given role and section in the header
        with the specified orientation to the value supplied.
        """
        if orientation == Qt.Horizontal and role == Qt.EditRole:
            try:
                self.header[section] = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except IndexError:
                return False
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
        try:
            return self._data[index.row()][index.column()][role]
        except KeyError:
            return None

    def rowData(self, row, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the given row.

        Args:
            row (int): Item row
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not 0 <= row < self.rowCount():
            return None
        return [self.data(self.index(row, column), role) for column in range(self.columnCount())]

    def columnData(self, column, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the given column.

        Args:
            column (int): Item column
            role (int): Data role

        Returns:
            Item data for given role.
        """
        if not 0 <= column < self.columnCount():
            return None
        return [self.data(self.index(row, column), role) for row in range(self.rowCount())]

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        self._data[index.row()][index.column()][role] = value
        if role == Qt.EditRole:
            self._data[index.row()][index.column()][Qt.DisplayRole] = value
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
        self.beginInsertRows(parent, row, row)
        if self.columnCount() == 0:
            new_row = [{}]
        else:
            new_row = [{} for i in range(self.columnCount())]
        # Notice if insert index > rowCount(), new object is inserted to end
        self._data.insert(row, new_row)
        self.endInsertRows()
        return True

    def insert_row_with_data(self, row, row_data, parent=QModelIndex(), role=Qt.EditRole):
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
        if not count == 1:
            logging.error("Insert 1 column at a time")
            return False
        self.beginInsertColumns(parent, column, column)
        for j in range(self.rowCount()):
            # Notice if insert index > rowCount(), new object is inserted to end
            self._data[j].insert(column, {})
        self.endInsertColumns()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent parent from the model.

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
        self.endRemoveRows()
        return True

    def reset_model(self, new_data):
        """Reset model."""
        self.beginResetModel()
        if new_data:
            for row, row_data in enumerate(new_data):
                self.insert_row_with_data(row, row_data)
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(top_left, bottom_right)
        self.endResetModel()


class ObjectTreeModel(QStandardItemModel):
    """A class to hold Spine data structure in a treeview."""

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self.mapping = parent.mapping
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.ForegroundRole:
            item_type = index.data(Qt.UserRole)
            if not item_type:
                return super().data(index, role)
            if item_type.endswith('class') and not self.hasChildren(index):
                return QBrush(Qt.gray)
        if role == Qt.FontRole:
            item_type = index.data(Qt.UserRole)
            if not item_type:
                return super().data(index, role)
            if item_type.endswith('class'):
                return self.bold_font
        if role == Qt.DecorationRole:
            item_type = index.data(Qt.UserRole)
            if not item_type:
                return super().data(index, role)
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
        # get relationship classes involving the present class
        proto_relationship_class_as_parent_list = self.mapping.proto_relationship_class_list(
            parent_object_class_id=object_class['id'])
        proto_relationship_class_as_child_list = self.mapping.proto_relationship_class_list(
            child_object_class_id=object_class['id'])
        for object_ in object_list:
            object_item = self.new_object_item(object_._asdict(), proto_relationship_class_as_parent_list,
                proto_relationship_class_as_child_list)
            object_class_item.appendRow(object_item)
        return object_class_item

    def new_object_item(self, object_, proto_relationship_class_as_parent_list,
            proto_relationship_class_as_child_list):
        """Returns new object item.

        Args:
            object_ (dict)
            relationship_class_as_parent_list (result)
            relationship_class_as_child_list (result)
        """
        object_item = QStandardItem(object_['name'])
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_, Qt.UserRole+1)
        # create and append proto relationship class items
        for proto_relationship_class in proto_relationship_class_as_parent_list:
            proto_relationship_class_item = self.new_proto_relationship_class_item(
                proto_relationship_class._asdict(),
                parent_object=object_)
            object_item.appendRow(proto_relationship_class_item)
        for proto_relationship_class in proto_relationship_class_as_child_list:
            if proto_relationship_class in proto_relationship_class_as_parent_list:
                continue
            proto_relationship_class_item = self.new_proto_relationship_class_item(
                proto_relationship_class._asdict(),
                child_object=object_)
            object_item.appendRow(proto_relationship_class_item)
        return object_item

    def new_proto_relationship_class_item(self, proto_relationship_class, parent_object=None, child_object=None):
        """Returns new proto relationship class item. Proto means that the relationship class
        only involves object classes, and not another relationship class.

        Args:
            proto_relationship_class (dict): proto relationship class
            parent_object (dict): object of the parent class which is the parent item in the tree
            child_object (dict): object of the child class which is the parent item in the tree
        """
        proto_relationship_class_item = QStandardItem(proto_relationship_class['name'])
        proto_relationship_class_item.setData(proto_relationship_class, Qt.UserRole+1)
        proto_relationship_class_item.setData('proto_relationship_class', Qt.UserRole)
        meta_relationship_class_list = self.mapping.meta_relationship_class_list(
            parent_relationship_class_id=proto_relationship_class['id'])
        if parent_object:
            related_object_list = self.mapping.child_related_object_list(
                relationship_class_id=proto_relationship_class['id'],
                parent_object_id=parent_object['id'])
        elif child_object:
            related_object_list = self.mapping.parent_related_object_list(
                relationship_class_id=proto_relationship_class['id'],
                child_object_id=child_object['id'])
        else:
            related_object_list = self.mapping.empty_list()
        for related_object in related_object_list:
            related_object_item = self.new_related_object_item(
                related_object._asdict(),
                meta_relationship_class_list)
            proto_relationship_class_item.appendRow(related_object_item)
        return proto_relationship_class_item

    def new_related_object_item(self, related_object, meta_relationship_class_list):
        """Returns new related object item.

        Args:
            related_object (dict)
            meta_relationship_class_list (result)
        """
        related_object_item = QStandardItem(related_object['name'])
        related_object_item.setData('related_object', Qt.UserRole)
        related_object_item.setData(related_object, Qt.UserRole+1)
        for meta_relationship_class in meta_relationship_class_list:
            meta_relationship_class_item = self.new_meta_relationship_class_item(
                meta_relationship_class._asdict(),
                related_object
            )
            related_object_item.appendRow(meta_relationship_class_item)
        return related_object_item

    def new_meta_relationship_class_item(self, meta_relationship_class, related_object=None):
        """Returns new meta-relationship class item. Meta means that the relationship class
        only involves another relationship class as parent.

        Args:
            meta_relationship_class (dict): relationship class
            related_object (dict): parent object
        """
        meta_relationship_class_item = QStandardItem(meta_relationship_class['name'])
        meta_relationship_class_item.setData(meta_relationship_class, Qt.UserRole+1)
        meta_relationship_class_item.setData('meta_relationship_class', Qt.UserRole)
        new_meta_relationship_class_list = self.mapping.meta_relationship_class_list(
            parent_relationship_class_id=meta_relationship_class['id'])
        # get new related objects in new relationship class
        if related_object:
            meta_related_object_list = self.mapping.meta_related_object_list(
                relationship_class_id=meta_relationship_class['id'],
                parent_relationship_id=related_object['relationship_id'])
        else:
            meta_related_object_list = self.mapping.empty_list()
        # recursively populate branches
        for meta_related_object in meta_related_object_list:
            # create related object item
            meta_related_object_item = self.new_related_object_item(meta_related_object._asdict(),
                new_meta_relationship_class_list)
            meta_relationship_class_item.appendRow(meta_related_object_item)
        return meta_relationship_class_item

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
        # get proto relationship classes involving the present class
        proto_relationship_class_as_parent_list = self.mapping.proto_relationship_class_list(
            parent_object_class_id=object_['class_id'])
        proto_relationship_class_as_child_list = self.mapping.proto_relationship_class_list(
            child_object_class_id=object_['class_id'])
        object_item = self.new_object_item(object_, proto_relationship_class_as_parent_list,
            proto_relationship_class_as_child_list)
        object_class_item.appendRow(object_item)

    def add_relationship_class(self, relationship_class):
        """Add relationship class item to model.

        Args:
            relationship_class (dict): the relationship class to add
        """
        if 'parent_object_class_id' in relationship_class:
            self.add_proto_relationship_class(relationship_class)
        elif 'parent_relationship_class_id' in relationship_class:
            self.add_meta_relationship_class(relationship_class)

    def add_proto_relationship_class(self, proto_relationship_class):
        """Add proto relationship class."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            # Skip root item
            if not visited_type:
                continue
            if not visited_type == 'object':
                continue
            visited_object_class = visited_item.parent().data(Qt.UserRole+1)
            if proto_relationship_class['parent_object_class_id'] == visited_object_class['id']:
                relationship_class_item = self.new_proto_relationship_class_item(proto_relationship_class)
                visited_item.appendRow(relationship_class_item)
            # Don't add duplicate relationship class if parent and child are the same
            if proto_relationship_class['parent_object_class_id'] == proto_relationship_class['child_object_class_id']:
                continue
            # Add mirror proto relationship class
            if proto_relationship_class['child_object_class_id'] == visited_object_class['id']:
                relationship_class_item = self.new_proto_relationship_class_item(proto_relationship_class)
                visited_item.appendRow(relationship_class_item)

    def add_meta_relationship_class(self, meta_relationship_class):
        """Add meta relationship class."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            # Skip root item
            if not visited_type:
                continue
            # FIXME: this test below seems too soft. The visited item being a related object does not
            # guarantee that the parent is a meta_relationship_class. Could be a proto relationship class too.
            if not visited_type == 'related_object':
                continue
            visited_relationship_class = visited_item.parent().data(Qt.UserRole+1)
            if meta_relationship_class['parent_relationship_class_id'] == visited_relationship_class['id']:
                relationship_class_item = self.new_meta_relationship_class_item(meta_relationship_class)
                visited_item.appendRow(relationship_class_item)

    def add_relationship(self, relationship):
        """Add relationship item to model.

        Args:
            relationship (dict): the relationship to add
        """
        meta_relationship_class_list = self.mapping.meta_relationship_class_list(
            parent_relationship_class_id=relationship['class_id'])
        if 'parent_object_id' in relationship:
            self.add_proto_relationship(relationship, meta_relationship_class_list)
        elif 'parent_relationship_id' in relationship:
            self.add_meta_relationship(relationship, meta_relationship_class_list)

    def add_proto_relationship(self, proto_relationship, meta_relationship_class_list):
        """Add proto relationship."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if not visited_type: # root item
                continue
            if not visited_type == 'proto_relationship_class':
                continue
            visited_proto_relationship_class = visited_item.data(Qt.UserRole+1)
            if not visited_proto_relationship_class['id'] == proto_relationship['class_id']:
                continue
            visited_object = visited_item.parent().data(Qt.UserRole+1)
            if visited_object['id'] == proto_relationship['parent_object_id']:
                child_object = self.mapping.single_object(id=proto_relationship['child_object_id'])
                if child_object:
                    child_object_dict = child_object._asdict()
                    child_object_dict['relationship_id'] = proto_relationship['id']
                    child_object_item = self.new_related_object_item(child_object_dict,
                        meta_relationship_class_list)
                    visited_item.appendRow(child_object_item)
            if visited_object['id'] == proto_relationship['child_object_id']:
                parent_object = self.mapping.single_object(id=proto_relationship['parent_object_id'])
                if parent_object:
                    parent_object_dict = parent_object._asdict()
                    parent_object_dict['relationship_id'] = proto_relationship['id']
                    parent_object_item = self.new_related_object_item(parent_object_dict,
                        meta_relationship_class_list)
                    visited_item.appendRow(parent_object_item)

    def add_meta_relationship(self, meta_relationship, meta_relationship_class_list):
        """Add meta relationship."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if not visited_type: # root item
                continue
            if not visited_type == 'meta_relationship_class':
                continue
            visited_meta_relationship_class = visited_item.data(Qt.UserRole+1)
            if not visited_meta_relationship_class['id'] == meta_relationship['class_id']:
                continue
            visited_related_object = visited_item.parent().data(Qt.UserRole+1)
            if visited_related_object['relationship_id'] == meta_relationship['parent_relationship_id']:
                child_object = self.mapping.single_object(id=meta_relationship['child_object_id'])
                if child_object:
                    child_object_dict = child_object._asdict()
                    child_object_dict['relationship_id'] = meta_relationship['id']
                    child_object_item = self.new_related_object_item(child_object_dict, meta_relationship_class_list)
                    visited_item.appendRow(child_object_item)

    def rename_item(self, new_name, curr_name, renamed_type, renamed_id):
        """Rename all matched items."""
        items = self.findItems(curr_name, Qt.MatchExactly | Qt.MatchRecursive, column=0)
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            visited = visited_item.data(Qt.UserRole+1)
            # Skip root
            if not visited_type:
                continue
            visited_id = visited['id']
            if visited_type == renamed_type and visited_id == renamed_id:
                visited['name'] = new_name
                visited_item.setData(visited, Qt.UserRole+1)
                visited_item.setText(new_name)
            if renamed_type == 'object' and visited_type == 'related_object':
                if visited_id == renamed_id:
                    visited['name'] = new_name
                    visited_item.setData(visited, Qt.UserRole+1)
                    visited_item.setText(new_name)
            if renamed_type == 'related_object' and visited_type == 'object':
                if visited_id == renamed_id:
                    visited['name'] = new_name
                    visited_item.setData(visited, Qt.UserRole+1)
                    visited_item.setText(new_name)

    def remove_item(self, removed_type, removed_id):
        """Remove all matched items and their orphans."""
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        for visited_item in reversed(items):
            visited_type = visited_item.data(Qt.UserRole)
            visited = visited_item.data(Qt.UserRole+1)
            # Skip root
            if not visited_type:
                continue
            # Get visited id
            if visited_type == 'related_object':
                visited_id = visited['relationship_id']
            else:
                visited_id = visited['id']
            if visited_type == removed_type and visited_id == removed_id:
                visited_index = self.indexFromItem(visited_item)
                self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object class, also remove relationship classes that involve it
            if removed_type == 'object_class' and visited_type.endswith('relationship_class'):
                child_object_class_id = visited['child_object_class_id']
                if 'parent_object_class_id' in visited:
                    parent_object_class_id = visited['parent_object_class_id']
                else:
                    parent_object_class_id = None
                if removed_id in [child_object_class_id, parent_object_class_id]:
                    visited_index = self.indexFromItem(visited_item)
                    self.removeRows(visited_index.row(), 1, visited_index.parent())
            # When removing an object, also remove relationships that involve it
            if removed_type == 'object' and visited_type == 'related_object':
                if removed_id == visited['id']:
                    visited_index = self.indexFromItem(visited_item)
                    self.removeRows(visited_index.row(), 1, visited_index.parent())


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """A custom sort filter proxy model."""
    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self.condition_list = list()
        self.hidden_column = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.setDynamicSortFilter(False)
        self.gray_background = self._parent.palette().button() if self._parent else QBrush(Qt.lightGray)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.BackgroundRole:
            if not index.flags() & Qt.ItemIsEditable: # Item is not editable
                return self.gray_background
        return super().data(index, role)

    def reset(self):
        self.condition_list = list()
        self.hidden_column = None

    def apply(self):
        self.setFilterRegExp("")

    def hide_column(self, name):
        h = self.sourceModel().header
        self.hidden_column = h.index(name)

    def add_condition(self, **kwargs):
        """Add a condition to the list by taking the kwargs as statements.
        The condition will be considered True if ANY of the statements is True.
        """
        h = self.sourceModel().header
        condition = {}
        for key, value in kwargs.items():
            column = h.index(key)
            condition[column] = value
        self.condition_list.append(condition)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        All the conditions in the list need to be satisfied, however each condition
        is satisfied as soon as ANY of its statements is satisfied.
        Also set bold font for matched items in each row.
        """
        for column in range(self.sourceModel().columnCount()):
            source_index = self.sourceModel().index(source_row, column, source_parent)
            self.sourceModel().setData(source_index, None, Qt.FontRole)
        if not self.condition_list:
            return False
        result = True
        for condition in self.condition_list:
            partial_result = False
            for column, value in condition.items():
                source_index = self.sourceModel().index(source_row, column, source_parent)
                #index = self.mapFromSource(source_index)
                if self.sourceModel().data(source_index, self.filterRole()) == value:
                    partial_result = True
                    self.sourceModel().setData(source_index, self.bold_font, Qt.FontRole)
            result = result and partial_result
        return result

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if self.hidden_column is None:
            return True
        return source_column != self.hidden_column


class ObjectParameterProxy(CustomSortFilterProxyModel):
    """A class to filter the object parameter table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)

    def flags(self, index):
        """Returns the item flags for the given index."""
        source_index = self.mapToSource(index)
        column_name = self.sourceModel().header[source_index.column()]
        if column_name == 'object_class_name':
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class ObjectParameterValueProxy(CustomSortFilterProxyModel):
    """A class to filter the object parameter value table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)

    def flags(self, index):
        """Returns the item flags for the given index."""
        source_index = self.mapToSource(index)
        column_name = self.sourceModel().header[source_index.column()]
        if column_name in ('object_class_name', 'object_name', 'parameter_name'):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class RelationshipParameterProxy(CustomSortFilterProxyModel):
    """A class to filter the relationship parameter table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def flags(self, index):
        """Returns the item flags for the given index."""
        column_name = self.sourceModel().header[index.column()]
        if column_name == 'relationship_class_name':
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class RelationshipParameterValueProxy(CustomSortFilterProxyModel):
    """A class to filter the relationship parameter value table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)

    def flags(self, index):
        """Returns the item flags for the given index."""
        source_index = self.mapToSource(index)
        column_name = self.sourceModel().header[source_index.column()]
        if column_name in [
                    'relationship_class_name',
                    'parent_object_name',
                    'parent_relationship_name',
                    'child_object_name',
                    'parameter_name'
                ]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class DatapackageDescriptorModel(QStandardItemModel):
    """A class to hold a datapackage descriptor in a treeview."""

    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__(parent)
        self.header = list()

    def find_item(self, key_chain):
        """Find item under a chain of keys.

        Returns:
            key: the last key explored from key_chain
            item: the last item visited
        """
        key_iterator = iter(key_chain)
        item = self.invisibleRootItem()
        while item.hasChildren():
            try:
                key = next(key_iterator)
            except StopIteration:
                break
            for i in range(item.rowCount()):
                child = item.child(i)
                if child.data(Qt.UserRole) == key:
                    item = child
                    break
        return key, item

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns the data for the given role and section in the header
        with the specified orientation.
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                h = self.header[section]
            except IndexError:
                return None
            return h
        else:
            return None
