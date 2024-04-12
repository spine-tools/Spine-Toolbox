######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Models to represent items in a tree."""
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex


class TreeItem:
    """A tree item that can fetch its children."""

    def __init__(self, model):
        """
        Args:
            model (MinimalTreeModel): The model where the item belongs.
        """
        super().__init__()
        self._children = []
        self._model = model
        self._parent_item = None
        self._fetched = False
        self._set_up_once = False
        self._has_children_initially = False
        self._created_children = {}

    def set_has_children_initially(self, has_children_initially):
        self._has_children_initially = has_children_initially

    def has_children(self):
        """Returns whether this item has or could have children."""
        if self._has_children_initially:
            return True
        return bool(self.child_count())

    @property
    def model(self):
        return self._model

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        bad_types = [type(child) for child in children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Can't set children of type {bad_types} for an item of type {type(self)}")
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

    def is_valid(self):
        """Tests if item is valid.

        Return:
            bool: True if item is valid, False otherwise
        """
        return True

    def child(self, row):
        """Returns the child at given row or None if out of bounds."""
        if 0 <= row < len(self._children):
            return self.children[row]
        return None

    def last_child(self):
        """Returns the last child."""
        return self.child(self.child_count() - 1)

    def child_count(self):
        """Returns the number of children."""
        return len(self.children)

    def row_count(self):
        """Returns the number of rows, which may be different from the number of children.
        This allows subclasses to hide children."""
        return self.child_count()

    def child_number(self):
        """Returns the rank of this item within its parent or -1 if it's an orphan."""
        if self.parent_item:
            return self.parent_item.children.index(self)
        return None

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
        if self.child_number() is None:
            return None
        return self.parent_item.child(self.child_number() - 1)

    def index(self):
        return self.model.index_from_item(self)

    def set_up(self):
        if not self._set_up_once:
            self._set_up_once = True
            self._do_set_up()

    def _do_set_up(self):
        """Do stuff after the item has been inserted."""

    def _polish_children(self, children):
        """Polishes children just before inserting them."""

    def insert_children(self, position, children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            children (list of TreeItem): insert items from this iterable

        Returns:
            bool: True if the children were inserted successfully, False otherwise
        """
        bad_types = [type(child) for child in children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Can't insert children of type {bad_types} to an item of type {type(self).__name__}")
        if position < 0 or position > self.child_count():
            return False
        self._polish_children(children)
        parent_index = self.index()
        self.model.beginInsertRows(parent_index, position, position + len(children) - 1)
        for child in children:
            child.parent_item = self
        self.children[position:position] = children
        self.model.endInsertRows()
        for child in children:
            child.set_up()
        return True

    def append_children(self, children):
        """Append children at the end."""
        return self.insert_children(self.child_count(), children)

    def tear_down(self):
        """Do stuff after the item has been removed."""

    def tear_down_recursively(self):
        for child in self._created_children.values():
            child.tear_down_recursively()
        for child in self._children:
            child.tear_down_recursively()
        self.tear_down()

    def remove_children(self, position, count):
        """Removes count children starting from the given position.

        Args:
            position (int): position of the first child to remove
            count (int): number of children to remove

        Returns:
            bool: True if operation was successful, False otherwise
        """
        first = position
        last = position + count - 1
        if first >= self.child_count() or first < 0:
            return False
        if last >= self.child_count():
            last = self.child_count() - 1
        self.model.beginRemoveRows(self.index(), first, last)
        del self.children[first : last + 1]
        self.model.endRemoveRows()
        self._has_children_initially = False
        return True

    # pylint: disable=no-self-use
    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # pylint: disable=no-self-use
    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        return None

    def can_fetch_more(self):
        """Returns whether this item can fetch more."""
        return not self._fetched

    def fetch_more(self):
        """Fetches more children."""
        self._fetched = True

    @property
    def display_data(self):
        return "unnamed"

    @property
    def edit_data(self):
        return self.display_data

    def set_data(self, column, value, role):
        """
        Sets data for this item.

        Args:
            column (int): column index
            value (object): a new value
            role (int): role of the new value

        Returns:
            bool: True if data was set successfully, False otherwise
        """
        raise NotImplementedError()


class MinimalTreeModel(QAbstractItemModel):
    """Base class for all tree models."""

    def __init__(self, parent):
        """Init class.

        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._parent = parent
        self._invisible_root_item = TreeItem(self)

    def visit_all(self, index=QModelIndex(), view=None):
        """Iterates all items in the model including and below the given index.
        Iterative implementation so we don't need to worry about Python recursion limits.

        Args:
            index (QModelIndex): an index to start. If not given, we start at the root
            view (QTreeView): a tree view. If given, we only yield items that are visible
                to that view. So for example, if a tree item is not expanded then we don't yield
                its children.

        Yields:
            TreeItem
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
                if view is None or view.isExpanded(self.index_from_item(current)):
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
        """Return a model index corresponding to the given item.

        Args:
            item (StandardTreeItem): item

        Returns:
            QModelIndex: item's index
        """
        row = item.child_number()
        if row is None:
            return QModelIndex()
        return self.createIndex(row, 0, item)

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
        if parent_item is None or parent_item is self._invisible_root_item:
            return QModelIndex()
        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        parent_item = self.item_from_index(parent)
        return parent_item.row_count()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns the data stored under the given role for the index."""
        if not index.isValid():
            return None
        item = self.item_from_index(index)
        if not item.is_valid():
            return None
        return item.data(index.column(), role)

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Sets data for given index and role.
        Returns True if successful; otherwise returns False.
        """
        if not index.isValid():
            return False
        item = self.item_from_index(index)
        if not item.set_data(index.column(), value, role):
            return False
        self.dataChanged.emit(index, index, [])
        return True

    def flags(self, index):
        """Returns the item flags for the given index."""
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
