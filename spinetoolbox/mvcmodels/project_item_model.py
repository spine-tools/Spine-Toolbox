######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a class for storing project items.

:authors: P. Savolainen (VTT)
:date:   23.1.2018
"""

import logging
from copy import copy
from PySide2.QtCore import Qt, QModelIndex, QAbstractItemModel
from PySide2.QtWidgets import QMessageBox
from ..config import INVALID_CHARS
from ..metaobject import shorten


class ProjectItemModel(QAbstractItemModel):
    def __init__(self, toolbox, root):
        """Class to store project tree items and ultimately project items in a tree structure.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            root (RootProjectTreeItem): Root item for the project item tree
        """
        super().__init__()
        self._toolbox = toolbox
        self._root = root

    def root(self):
        """Returns the root item."""
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
        return parent.internalPointer().child_count()

    def columnCount(self, parent=QModelIndex()):
        """Returns model column count which is always 1."""
        return 1

    def flags(self, index):
        """Returns flags for the item at given index

        Args:
            index (QModelIndex): Flags of item at this index.
        """
        return index.internalPointer().flags()

    def parent(self, index=QModelIndex()):
        """Returns index of the parent of given index.

        Args:
            index (QModelIndex): Index of item whose parent is returned

        Returns:
            QModelIndex: Index of parent item
        """
        item = self.item(index)
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
        parent_item = self.item(parent)
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
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.name
        return None

    def item(self, index):
        """Returns item at given index.

        Args:
            index (QModelIndex): Index of item

        Returns:
            RootProjectTreeItem, CategoryProjectTreeItem or LeafProjectTreeItem: Item at given index or root project
                item if index is not valid
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
        try:
            row = category_names.index(category_name)
        except ValueError:
            logging.error("Category name %s not found in %s", category_name, category_names)
            return None
        return self.index(row, 0, QModelIndex())

    def find_item(self, name):
        """Returns the QModelIndex of the leaf item with the given name

        Args:
            name (str): The searched project item (long) name

        Returns:
            QModelIndex: Index of a project item with the given name or None if not found
        """
        for category in self.root().children():
            category_index = self.find_category(category.name)
            start_index = self.index(0, 0, category_index)
            matching_index = self.match(start_index, Qt.DisplayRole, name, 1, Qt.MatchFixedString | Qt.MatchRecursive)
            if not matching_index:
                pass  # no match in this category
            elif len(matching_index) == 1:
                return matching_index[0]
        return None

    def get_item(self, name):
        """Returns leaf item with given name or None if it doesn't exist.

        Args:
            name (str): Project item name

        Returns:
            LeafProjectTreeItem, NoneType
        """
        ind = self.find_item(name)
        if ind is None:
            return None
        return self.item(ind)

    def category_of_item(self, name):
        """Returns the category item of the category that contains project item with given name

        Args:
            name (str): Project item name

        Returns:
            category item or None if the category was not found
        """
        for category in self.root().children():
            for item in category.children():
                if name == item.name:
                    return category
        return None

    def insert_item(self, item, parent=QModelIndex()):
        """Adds a new item to model. Fails if given parent is not
        a category item nor a leaf item. New item is inserted as
        the last item of its branch.

        Args:
            item (CategoryProjectTreeItem or LeafProjectTreeItem): Project item to add to model
            parent (QModelIndex): Parent project item

        Returns:
            bool: True if successful, False otherwise
        """
        parent_item = self.item(parent)
        row = self.rowCount(parent)  # parent.child_count()
        self.beginInsertRows(parent, row, row)
        retval = parent_item.add_child(item)
        self.endInsertRows()
        return retval

    def remove_item(self, item, parent=QModelIndex()):
        """Removes item from model.

        Args:
            item (BaseProjectTreeItem): Project item to remove
            parent (QModelIndex): Parent of item that is to be removed

        Returns:
            bool: True if item removed successfully, False if item removing failed
        """
        parent_item = self.item(parent)
        row = item.row()
        self.beginRemoveRows(parent, row, row)
        retval = parent_item.remove_child(row)
        self.endRemoveRows()
        return retval

    def setData(self, index, value, role=Qt.EditRole):
        """Changes the name of the leaf item at given index to given value.

        Args:
            index (QModelIndex): Tree item index
            value (str): New project item name
            role (int): Item data role to set

        Returns:
            bool: True or False depending on whether the new name is acceptable and renaming succeeds
        """
        if not role == Qt.EditRole:
            return super().setData(index, value, role)
        item = index.internalPointer()
        if item.parent() is None:
            # The item has been removed from the model
            return False
        old_name = item.name
        if not value.strip() or value == old_name:
            return False
        # Check that new name is legal
        if any(x in INVALID_CHARS for x in value):
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
        new_short_name = shorten(value)
        if self._toolbox.project_item_model.short_name_reserved(new_short_name):
            msg = "Project item using directory <b>{0}</b> already exists".format(new_short_name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid name", msg)
            return False
        if not item.project_item.rename(value):
            return False
        item.set_name(value)
        self._toolbox.project().dag_handler.rename_node(old_name, value)
        self._toolbox.msg_success.emit(f"Project item <b>{old_name}</b> renamed to <b>{value}</b>")
        return True

    def items(self, category_name=None):
        """Returns a list of leaf items in model according to category name. If no category name given,
        returns all leaf items in a list.

        Args:
            category_name (str): Item category. Data Connections, Data Stores, Importers, Exporters, Tools or Views
                permitted.

        Returns:
            :obj:'list' of :obj:'LeafProjectTreeItem': Depending on category_name argument, returns all items or only
            items according to category. An empty list is returned if there are no items in the given category
            or if an unknown category name was given.
        """
        if not category_name:
            items = list()
            for category in self.root().children():
                items += category.children()
            return items
        category_index = self.find_category(category_name)
        if not category_index:
            logging.error("Category item '%s' not found", category_name)
            return list()
        return category_index.internalPointer().children()

    def n_items(self):
        """Returns the number of all items in the model excluding category items and root.

        Returns:
            int: Number of items
        """
        return len(self.items())

    def item_names(self):
        """Returns all leaf item names in a list.

        Returns:
            obj:'list' of obj:'str': Item names
        """
        return [item.name for item in self.items()]

    def items_per_category(self):
        """Returns a dict mapping category indexes to a list of items in that category.

        Returns:
            dict(QModelIndex,list(LeafProjectTreeItem))
        """
        category_inds = [self.index(row, 0) for row in range(self.rowCount())]
        return {ind: copy(ind.internalPointer().children()) for ind in category_inds}

    def short_name_reserved(self, short_name):
        """Checks if the directory name derived from the name of the given item is in use.

        Args:
            short_name (str): Item short name

        Returns:
            bool: True if short name is taken, False if it is available.
        """
        return short_name in set(item.short_name for item in self.items())
