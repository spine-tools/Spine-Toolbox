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

"""Contains the model for generic items, specifications, and plugins."""
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QBrush, QColor
from PySide6.QtCore import Qt, Slot, QAbstractItemModel, QModelIndex

from spinetoolbox.mvcmodels.minimal_tree_model import TreeItem

class CategoryItem:
    """A class for a Category Item."""
    def __init__(self, model, text):
        """
        Args:
            model (QAbstractItemModel): The model of this item
        """
        super().__init__()
        self._children = []
        self._model = model
        self._parent_item = None
        self._text = text

    def has_children(self):
        """Returns whether this item has children."""
        return bool(self.child_count())

    @property
    def model(self):
        return self._model

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        for child in children:
            child.parent_item = self
        self._children = children

    @property
    def parent_item(self):
        return self._parent_item

    @parent_item.setter
    def parent_item(self, parent_item):
        self._parent_item = parent_item

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
        """Returns the number of rows."""
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
        if position < 0 or position > self.child_count():
            return False
        self._polish_children(children)
        self.model.beginInsertRows(self.index(), position, position + len(children) - 1)
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
        return True

    # pylint: disable=no-self-use
    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # pylint: disable=no-self-use
    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        return self._text

    @property
    def display_data(self):
        return "unnamed"

    @property
    def edit_data(self):
        return self.display_data

    def set_data(self, column, value, role):
        """Sets data for this item.

        Args:
            column (int): column index
            value (object): a new value
            role (int): role of the new value

        Returns:
            bool: True if data was set successfully, False otherwise
        """
        raise NotImplementedError()

class ItemsModel(QAbstractItemModel):
    """Model for all items in project."""

    def __init__(self, parent):
        """
        Args:
            parent (ToolboxUI)
        """
        super().__init__(parent)
        self._parent = parent
        self._root_item = TreeItem(self)

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


class MinimalTreeModel(QAbstractItemModel):

    def item_from_index(self, index):
        """Return the item corresponding to the given index.

        Args:
            index (QModelIndex): model index

        Returns:
            TreeItem: item at index
        """
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


    def hasChildren(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.has_children()

    def canFetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.can_fetch_more()

    def fetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        parent_item.fetch_more()


class GenericItemsModel(QStandardItemModel):
    def __init__(self, toolbox):
        super().__init__()
        self.toolbox = toolbox
        self.add_project_items()
        self.add_specs_title()
        self._spec_model = self.toolbox.specification_model
        self._spec_model.rowsInserted.connect(self._insert_specs)

    def add_project_items(self):
        title = QStandardItem(QIcon(":/icons/share.svg"), "Generic Items")
        title.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # title.setFlags(~Qt.ItemFlag.ItemIsEditable)
        self.insertRow(0, title)
        for item_type, factory in self.toolbox.item_factories.items():
            if factory.is_deprecated():
                continue
            icon = QIcon(factory.icon())
            item = QStandardItem(icon, item_type)
            title.appendRow(item)

    def add_specs_title(self):
        spec_title = QStandardItem(QIcon(":/icons/share.svg"), "Specifications")
        spec_title.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.insertRow(1, spec_title)

    @Slot(QModelIndex, int, int)
    def _insert_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._add_spec(row)

    def _add_spec(self, row):
        spec = self._spec_model.specification(row)
        if spec.plugin:
            return
        next_row = row + 1
        while True:
            next_spec = self._spec_model.specification(next_row)
            if next_spec is None or not next_spec.plugin:
                break
            next_row += 1
        factory = self.toolbox.item_factories[spec.item_type]
        icon = QIcon(factory.icon())
        # icon = self._icon_from_factory(factory)
        print(f"spec name:{spec.name}")
        for row in range(self.rowCount()):
            item = self.itemFromIndex(self.index(row, 0, QModelIndex()))
            item_name = item.data(Qt.ItemDataRole.DisplayRole)
            print(f"item:{item.data(Qt.ItemDataRole.DisplayRole)}")
            if item_name == "Specifications":
                spec_item = QStandardItem(icon, spec.name)
                item.appendRow(spec_item)

    @Slot(QModelIndex)
    def collapse_or_expand_children(self, index):
        if not index.isValid():
            return
        item = self.itemFromIndex(index)
        if item.hasChildren():
            if self.toolbox.ui.treeView_items.isExpanded(index):
                self.toolbox.ui.treeView_items.setExpanded(index, False)
            else:
                self.toolbox.ui.treeView_items.setExpanded(index, True)


def make_icon_background(color):
    color0 = color.name()
    color1 = color.lighter(140).name()
    return f"qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 {color0}, stop: 1 {color1});"


def make_treeview_item_ss(color):
    icon_background = make_icon_background(color)
    return f"QTreeView::item{{background: {icon_background}}}"

def make_treeview_ss(color):
    treeview_item_ss = make_treeview_item_ss(color)
    return "QTreeView::item:has-children {padding:5px; background-color: yellow; color: black; border: 1px solid gray; border-radius: 2px;}" + treeview_item_ss
