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
from PySide2.QtCore import Qt, QModelIndex, QAbstractListModel, QAbstractTableModel,\
    QSortFilterProxyModel
from PySide2.QtGui import QStandardItemModel, QBrush, QFont, QIcon, QPixmap


class ProjectItemModel(QStandardItemModel):
    """Class to store project items, e.g. Data Stores, Data Connections, Tools, Views."""
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent

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
        self._tools.append('No tool template')  # TODO: Try to get rid of this
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
        """Set headers."""
        if role == Qt.DisplayRole:
            try:
                h = self.header[section]
            except IndexError:
                return None
            return h
        else:
            return None

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

    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__()
        self._parent = parent  # QMainWindow
        self._data = list()
        self._user_role_data = list()
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
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.UserRole:
            return self._user_role_data[index.row()][index.column()]
        else:
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
        if role == Qt.DisplayRole:
            return self._data[row]
        return None

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
        if role == Qt.DisplayRole:
            return [self._data[row][column] for row in range(self.rowCount())]
        return None

    def modelData(self, role=Qt.DisplayRole):
        """Returns all the model data.

        Args:
            role (int): Data role

        Returns:
            Model data for given role.
        """
        if role == Qt.DisplayRole:
            return self._data
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            return True
        if role == Qt.UserRole:
            self._user_role_data[index.row()][index.column()] = value
            return True
        return False

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
            new_row = [None]
        else:
            # noinspection PyUnusedLocal
            new_row = [None for i in range(self.columnCount())]
        # Notice if insert index > rowCount(), new object is inserted to end
        self._data.insert(row, new_row)
        self._user_role_data.insert(row, new_row)
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
        self.beginInsertColumns(parent, column, column)
        for j in range(self.rowCount()):
            # Notice if insert index > rowCount(), new object is inserted to end
            self._data[j].insert(column, None)
            self._user_role_data[j].insert(column, None)
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
        removed_row = self._data.pop(row)
        # logging.debug("{0} removed from row:{1}".format(removed_row, row))
        self.endRemoveRows()
        return True

    def reset_model(self, new_data):
        """Reset model."""
        self.beginResetModel()
        self._data = new_data
        if new_data:
            self._user_role_data = [[None for j in new_data[i]] for i in range(len(new_data))]
        self.endResetModel()

    def set_tool_tip(self, tool_tip):
        """Set tool tip."""
        # TODO: This probably does not work. Tooltip should be returned by data() method when role == Qt.ToolTipRole.
        self._tool_tip = tool_tip


class ObjectTreeModel(QStandardItemModel):
    """A class to hold Spine data structure in a treeview."""

    def __init__(self, parent=None):
        """Initialize class"""
        super().__init__(parent)
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


class ObjectParameterProxy(QSortFilterProxyModel):
    """A class to filter the object parameter table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self.object_class_id_filter = None

    def clear_filter(self):
        self.object_class_id_filter = None

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.BackgroundRole:
            if not index.flags() & Qt.ItemIsEditable:
                if self._parent:
                    return self._parent.palette().button()
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """
        # logging.debug("accept rows")
        h = self.sourceModel().header

        def source_data(column_name):
            return self.sourceModel().index(source_row, h.index(column_name), source_parent).data()
        object_class_id = source_data("object_class_id")
        if self.object_class_id_filter:
            return object_class_id == self.object_class_id_filter
        return False

    def flags(self, index):
        """Returns the item flags for the given index."""
        column_name = self.sourceModel().header[index.column()]
        if column_name == 'object_class_name':
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class ObjectParameterValueProxy(QSortFilterProxyModel):
    """A class to filter the object parameter value table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self.object_class_id_filter = None
        self.object_id_filter = None
        self.gray_background = self._parent.palette().button() if self._parent else QBrush(Qt.lightGray)

    def clear_filter(self):
        self.object_class_id_filter = None
        self.object_id_filter = None

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.BackgroundRole:
            if not index.flags() & Qt.ItemIsEditable: # Item is not editable
                return self.gray_background
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """
        # logging.debug("accept rows")
        h = self.sourceModel().header

        def source_data(column_name):
            return self.sourceModel().index(source_row, h.index(column_name), source_parent).data()
        object_class_id = source_data("object_class_id")
        object_id = source_data("object_id")
        if self.object_id_filter:
            return object_id == self.object_id_filter
        if self.object_class_id_filter:
            return object_class_id == self.object_class_id_filter
        return False

    def flags(self, index):
        """Returns the item flags for the given index."""
        source_index = self.mapToSource(index)
        column_name = self.sourceModel().header[source_index.column()]
        if column_name in ('object_class_name', 'object_name', 'parameter_name'):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class RelationshipParameterProxy(QSortFilterProxyModel):
    """A class to filter the relationship parameter table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self.object_class_id_filter = None
        self.relationship_class_id_filter = None
        # self.hide_column = None

    def clear_filter(self):
        self.object_class_id_filter = None
        self.relationship_class_id_filter = None
        # self.hide_column = None

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.BackgroundRole:
            if not index.flags() & Qt.ItemIsEditable:
                if self._parent:
                    return self._parent.palette().button()
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """
        # logging.debug("accept rows")
        h = self.sourceModel().header

        def source_data(column_name):
            return self.sourceModel().index(source_row, h.index(column_name), source_parent).data()
        if self.object_class_id_filter:
            parent_object_class_id = source_data("parent_object_class_id")
            child_object_class_id = source_data("child_object_class_id")
            return self.object_class_id_filter in (parent_object_class_id, child_object_class_id)
        if self.relationship_class_id_filter:
            relationship_class_id = source_data("relationship_class_id")
            return self.relationship_class_id_filter == relationship_class_id
        return False

    def flags(self, index):
        """Returns the item flags for the given index."""
        column_name = self.sourceModel().header[index.column()]
        if column_name == 'relationship_class_name':
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    # def filterAcceptsColumn(self, source_column, source_parent):
    #     """Returns true if the item in the column indicated by the given source_column
    #     and source_parent should be included in the model; otherwise returns false
    #     """

    #     h = self.sourceModel().header
    #     #if self.hide_all_columns:
    #     #    return False
    #     if self.hide_column is not None:
    #         return source_column != self.hide_column
    #     return True


class RelationshipParameterValueProxy(QSortFilterProxyModel):
    """A class to filter the relationship parameter value table in Data Store."""

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self.relationship_class_id_filter = None
        self.relationship_id_filter = None
        self.object_id_filter = None
        self.parent_relationship_id_filter = None
        self.hide_column = None
        self.bold_name = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)

    def clear_filter(self):
        self.relationship_class_id_filter = None
        self.relationship_id_filter = None
        self.object_id_filter = None
        self.parent_relationship_id_filter = None
        self.hide_column = None
        self.bold_name = None

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.FontRole:
            if index.data(Qt.DisplayRole) == self.bold_name:
                return self.bold_font
        if role == Qt.BackgroundRole:
            if not index.flags() & Qt.ItemIsEditable:
                if self._parent:
                    return self._parent.palette().button()
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """
        # logging.debug("accept rows")
        h = self.sourceModel().header

        def source_data(column_name):
            return self.sourceModel().index(source_row, h.index(column_name), source_parent).data()
        if self.relationship_id_filter:
            # related object
            relationship_id = source_data("relationship_id")
            return relationship_id == self.relationship_id_filter
        if self.parent_relationship_id_filter and self.relationship_class_id_filter:
            # meta_relationship_class
            parent_relationship_id = source_data("parent_relationship_id")
            relationship_class_id = source_data("relationship_class_id")
            return parent_relationship_id == self.parent_relationship_id_filter\
                and relationship_class_id == self.relationship_class_id_filter
        if self.object_id_filter and self.relationship_class_id_filter:
            # relationship_class
            parent_object_id = source_data("parent_object_id")
            child_object_id = source_data("child_object_id")
            relationship_class_id = source_data("relationship_class_id")
            return self.object_id_filter in (parent_object_id, child_object_id)\
                and relationship_class_id == self.relationship_class_id_filter
        if self.object_id_filter:
            # object
            parent_object_id = source_data("parent_object_id")
            child_object_id = source_data("child_object_id")
            return child_object_id is not None and parent_object_id is not None\
                and self.object_id_filter in (parent_object_id, child_object_id)
        return False

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        h = self.sourceModel().header
        if self.hide_column is not None:
            return source_column != self.hide_column
        return True

    def flags(self, index):
        """Returns the item flags for the given index."""
        column_name = self.sourceModel().header[index.column()]
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
