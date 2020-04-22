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
Models to represent items in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
from PySide2.QtCore import Qt, QAbstractItemModel, QModelIndex


class TreeItem:
    """A tree item that can fetch its children."""

    def __init__(self, model=None):
        """Initializes item.

        Args:
            model (MinimalTreeModel, NoneType): The model where the item belongs.
        """
        if model is None:
            model = MinimalTreeModel()
        self._model = model
        self._children = None
        self._parent_item = None
        self._fetched = False
        self.children = []

    @property
    def model(self):
        return self._model

    @property
    def child_item_type(self):
        """Returns the type of child items. Reimplement in subclasses to return something more meaningfull."""
        return TreeItem

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        bad_types = [type(child) for child in children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Cand't set children of type {bad_types} for an item of type {type(self)}")
        for child in children:
            child.parent_item = self
        self._children = children

    @property
    def parent_item(self):
        return self._parent_item

    @parent_item.setter
    def parent_item(self, parent_item):
        if not isinstance(parent_item, TreeItem) and parent_item is not None:
            raise ValueError("Parent must be instance of TreeItem or None")
        self._parent_item = parent_item
        self._model = parent_item.model

    def child(self, row):
        """Returns the child at given row or None if out of bounds."""
        try:
            return self._children[row]
        except IndexError:
            return None

    def last_child(self):
        """Returns the last child."""
        return self.child(-1)

    def child_count(self):
        """Returns the number of children."""
        return len(self._children)

    def child_number(self):
        """Returns the rank of this item within its parent or 0 if it's an orphan."""
        if self.parent_item:
            return self.parent_item.children.index(self)
        return 0

    def find_children(self, cond=lambda child: True):
        """Returns children that meet condition expressed as a lambda function."""
        for child in self.children:
            if cond(child):
                yield child

    def find_child(self, cond=lambda child: True):
        """Returns first child that meet condition expressed as a lambda function or None."""
        return next(self.find_children(cond), None)

    def next_sibling(self):
        """Returns the next sibling or None if it's the last."""
        return self.parent_item.child(self.child_number() + 1)

    def previous_sibling(self):
        """Returns the previous sibling or None if it's the first."""
        if self.child_number() == 0:
            return None
        return self.parent_item.child(self.child_number() - 1)

    def index(self):
        return self.model.index_from_item(self)

    def insert_children(self, position, *children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            children (iter): insert items from this iterable
        """
        bad_types = [type(child) for child in children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Cand't insert children of type {bad_types} to an item of type {type(self)}")
        if position < 0 or position > self.child_count() + 1:
            return False
        children = list(children)
        for child in children:
            child.parent_item = self
        self.model.beginInsertRows(self.index(), position, position + len(children) - 1)
        self._children[position:position] = children
        self.model.endInsertRows()
        return True

    def append_children(self, *children):
        """Append children at the end."""
        return self.insert_children(self.child_count(), *children)

    def remove_children(self, position, count):
        """Removes count children starting from the given position."""
        if position > self.child_count() or position < 0:
            return False
        if position + count > self.child_count():
            count = self.child_count() - position
        self.model.beginRemoveRows(self.index(), position, position + count - 1)
        del self._children[position : position + count]
        self.model.endRemoveRows()
        return True

    def clear_children(self):
        """Clear children list."""
        self.children.clear()

    # pylint: disable=no-self-use
    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # pylint: disable=no-self-use
    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        return None

    def has_children(self):
        """Returns whether or not this item has or could have children."""
        if self.child_count() or self.can_fetch_more():
            return True
        return False

    def can_fetch_more(self):
        """Returns whether or not this item can fetch more."""
        return not self._fetched

    def fetch_more(self):
        """Fetches more children."""
        self._fetched = True

    @property
    def display_name(self):
        return "unnamed"


class MinimalTreeModel(QAbstractItemModel):
    """Base class for all tree models."""

    def __init__(self, parent=None):
        """Init class.

        Args:
            parent (DataStoreForm)
        """
        super().__init__(parent)
        self._invisible_root_item = TreeItem(self)

    def visit_all(self, index=QModelIndex()):
        """Iterates all items in the model including and below the given index.
        Iterative implementation so we don't need to worry about Python recursion limits.
        """
        if index.isValid():
            ancient_one = self.item_from_index(index)
        else:
            ancient_one = self._invisible_root_item
        yield ancient_one
        child = ancient_one.last_child()
        if not child:
            return
        current = child
        visit_children = True
        while True:
            if visit_children:
                yield current
                child = current.last_child()
                if child:
                    current = child
                    continue
            sibling = current.previous_sibling()
            if sibling:
                visit_children = True
                current = sibling
                continue
            parent_item = current.parent_item
            if parent_item == ancient_one:
                break
            visit_children = False  # To make sure we don't visit children again
            current = parent_item

    def item_from_index(self, index):
        """Return the item corresponding to the given index."""
        if index.isValid():
            return index.internalPointer()
        return self._invisible_root_item

    def index_from_item(self, item):
        """Return a model index corresponding to the given item."""
        return self.createIndex(item.child_number(), 0, item)

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the item in the model specified by the given row, column and parent index."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_item = self.item_from_index(parent)
        item = parent_item.child(row)
        return self.createIndex(row, column, item)

    def parent(self, index):
        """Returns the parent of the model item with the given index."""
        if not index.isValid():
            return QModelIndex()
        item = self.item_from_index(index)
        parent_item = item.parent_item
        if parent_item is None or parent_item == self._invisible_root_item:
            return QModelIndex()
        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        parent_item = self.item_from_index(parent)
        return parent_item.child_count()

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the index."""
        if not index.isValid():
            return None
        item = self.item_from_index(index)
        return item.data(index.column(), role)

    def setData(self, index, value, role=Qt.EditRole):
        """Sets data for given index and role.
        Returns True if successful; otherwise returns False.
        """
        if not index.isValid():
            return False
        item = self.item_from_index(index)
        if role == Qt.EditRole:
            return item.set_data(index.column(), value)
        return False

    def flags(self, index):
        """Returns the item flags for the given index.
        """
        item = self.item_from_index(index)
        return item.flags(index.column())

    def hasChildren(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.has_children()

    def canFetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.can_fetch_more()

    def fetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        parent_item.fetch_more()
