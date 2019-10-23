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
Models to represent items in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
from PySide2.QtCore import QObject, Qt, Signal, Slot, QAbstractItemModel, QModelIndex


class TreeItem(QObject):
    """A tree item that can fetch its children."""

    children_about_to_be_inserted = Signal("QModelIndex", "int", "int", name="children_about_to_be_inserted")
    children_about_to_be_removed = Signal("QModelIndex", "int", "int", name="children_about_to_be_removed")
    children_inserted = Signal(name="children_inserted")
    children_removed = Signal(name="children_removed")

    def __init__(self, parent=None):
        """Init class.

        Args:
            parent (TreeItem, NoneType): the parent item or None
        """
        super().__init__(parent)
        self._children = []
        self._parent = None
        self._fetched = False
        self.parent = parent
        self.children = []
        self._index = QModelIndex()

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
            child.parent = self
        self._children = children

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if not isinstance(parent, TreeItem) and parent is not None:
            raise ValueError("Parent must be instance of TreeItem or None")
        self._parent = parent

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        if not isinstance(index, QModelIndex):
            raise ValueError("Index must be a QModelIndex")
        self._index = index

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

    def row(self):
        """Returns the row of this item in the model."""
        return self.index.row()

    def find_children(self, cond=lambda child: True):
        """Returns children that meet condition expressed as a lambda function."""
        for child in self.children:
            if cond(child):
                yield child

    def find_child(self, cond=lambda child: True):
        """Returns first child that meet condition expressed as a lambda function or None."""
        return next(self.find_children(cond), None)

    def next_sibling(self):
        """Returns the next sibling or None if it's the last or if doesn't have a parent."""
        if self.parent is None:
            return None
        return self.parent.child(self.row() + 1)

    def previous_sibling(self):
        """Returns the previous sibling or None if it's first or if doesn't have a parent."""
        if self.row() == 0:
            return None
        return self.parent.child(self.row() - 1)

    def column_count(self):
        """Returns 0."""
        return 0

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
        self.children_about_to_be_inserted.emit(self.index, position, len(children))
        for child in children:
            child.parent = self
        self._children[position:position] = children
        self.children_inserted.emit()
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
        self.children_about_to_be_removed.emit(self.index, position, count)
        del self._children[position : position + count]
        self.children_removed.emit()
        return True

    def clear_children(self):
        """Clear children list."""
        self.children.clear()

    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

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


class MinimalTreeModel(QAbstractItemModel):
    """Base class for all tree models."""

    def __init__(self, parent):
        """Init class.

        Args:
            parent (DataStoreForm)
        """
        super().__init__(parent)
        self._parent = parent
        self._invisible_root_item = TreeItem()

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item.deleteLater()
        self._invisible_root_item = TreeItem()
        self.endResetModel()

    def createIndex(self, row, column, item):
        """Creates an index and stores it in the item for convenience."""
        index = super().createIndex(row, column, item)
        if not item.index.isValid():
            # This is so we only track items once
            self.track_item(item)
        item.index = index
        return index

    def track_item(self, item):
        """Tracks given TreeItem. This means we insert rows when children are inserted
        and remove rows when children are removed."""
        item.children_about_to_be_inserted.connect(self.receive_children_about_to_be_inserted)
        item.children_inserted.connect(self.receive_children_inserted)
        item.children_about_to_be_removed.connect(self.receive_children_about_to_be_removed)
        item.children_removed.connect(self.receive_children_removed)

    def stop_tracking_item(self, item):
        """Stops tracking given TreeItem."""
        item.children_about_to_be_inserted.disconnect(self.receive_children_about_to_be_inserted)
        item.children_inserted.disconnect(self.receive_children_inserted)
        item.children_about_to_be_removed.disconnect(self.receive_children_about_to_be_removed)
        item.children_removed.disconnect(self.receive_children_removed)

    @Slot("QModelIndex", "int", "int", name="receive_children_about_to_be_inserted")
    def receive_children_about_to_be_inserted(self, index, row, count):
        """Begin an operation to insert rows."""
        print(index)
        self.beginInsertRows(index, row, row + count - 1)

    @Slot(name="receive_children_inserted")
    def receive_children_inserted(self):
        """End an operation to insert rows. Start tracking all inserted items."""
        self.endInsertRows()

    @Slot("QModelIndex", "int", "int", name="receive_children_about_to_be_removed")
    def receive_children_about_to_be_removed(self, index, row, count):
        """Begin an operation to remove rows."""
        self.beginRemoveRows(index, row, row + count - 1)
        for child in self.item_from_index(parent).children[row, row + count]:
            self.stop_tracking_item(child)

    @Slot(name="receive_children_removed")
    def receive_children_removed(self):
        """End an operation to remove rows. Stop tracking all removed items."""
        self.endRemoveRows()

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
            yield current
            if visit_children:
                child = current.last_child()
                if child:
                    current = child
                    continue
            sibling = current.previous_sibling()
            if sibling:
                visit_children = True
                current = sibling
                continue
            parent = current._parent
            if parent == ancient_one:
                break
            visit_children = False  # To make sure we don't visit children again
            current = parent

    def item_from_index(self, index):
        """Return the item corresponding to the given index."""
        if index.isValid():
            return index.internalPointer()
        return self._invisible_root_item

    def index_from_item(self, item):
        """Return a model index corresponding to the given item."""
        return item.index

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
        parent_item = item.parent
        if parent_item == self._invisible_root_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

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
