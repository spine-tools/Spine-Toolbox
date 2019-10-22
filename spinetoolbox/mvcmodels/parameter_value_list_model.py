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
A tree model for parameter value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QObject, Signal, Slot, QModelIndex, QAbstractItemModel
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinedb_api import to_database, from_database
from .parameter_value_formatting import format_for_DisplayRole


class EditableMixin:
    def flags(self):
        """Makes items editable."""
        return Qt.ItemIsEditable | super().flags()


class GrayFontMixin:
    """Paints the text gray."""

    def data(self, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and self.row == self.parent.child_count() - 1:
            gray_color = QGuiApplication.palette().text().color()
            gray_color.setAlpha(128)
            gray_brush = QBrush(gray_color)
            return gray_brush
        return super().data(role)


class BoldFontMixin:
    """Bolds text."""

    def data(self, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(role)


class TreeNode(QObject):
    """A tree node item for ParameterValueListModel."""

    children_about_to_be_inserted = Signal("QVariant", "int", "int", name="children_about_to_be_inserted")
    children_about_to_be_removed = Signal("QVariant", "int", "int", name="children_about_to_be_removed")
    children_inserted = Signal("QVariant", name="children_inserted")
    children_removed = Signal("QVariant", name="children_removed")

    def __init__(self, parent):
        """Init class.

        Args
            parent (TreeNode): the parent node
        """
        super().__init__(parent)
        self.parent = parent
        self.children = list()

    @property
    def row(self):
        try:
            return self.parent.children.index(self)
        except AttributeError:
            return 0

    def child_count(self):
        return len(self.children)

    def insert_children(self, first, *children):
        """Inserts children."""
        last = first + len(children) - 1
        self.children_about_to_be_inserted.emit(self, first, last)
        children = list(children)
        self.children[first:first] = list(children)
        self.children_inserted.emit(children)

    def append_children(self, *children):
        """Appends children."""
        self.insert_children(self.child_count(), *children)

    def remove_children(self, first, last):
        """Removes children."""
        if first < 0 or last >= self.child_count() or first > last:
            return
        self.children_about_to_be_removed.emit(self, first, last)
        del self.children[first : last + 1]
        self.children_removed.emit()

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, role=Qt.DisplayRole):
        """Return data for item."""


class InvisibleRootNode(TreeNode):
    def __init__(self, db_mngr, *db_maps):
        super().__init__(None)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def fetch_children(self):
        children = [DBNode(self, self.db_mngr, db_map) for db_map in self.db_maps]
        self.append_children(*children)


class AppendEmptyChildMixin:
    """Provides a method to append an empty child if needed."""

    def append_empty_child(self, row):
        if row == self.child_count() - 1:
            empty_child = self.empty_child()
            self.append_children(empty_child)


class DBNode(AppendEmptyChildMixin, TreeNode):
    """A node representing a db."""

    def __init__(self, parent, db_mngr, db_map):
        """Init class.

        Args
            parent (TreeNode): the parent node
            db_map (DiffDatabaseMapping)
        """
        super().__init__(parent)
        self.db_map = db_map
        self.db_mngr = db_mngr
        children = [
            ListNode(self, db_mngr, db_map, value_list["id"], value_list["name"], value_list["value_list"].split(","))
            for value_list in db_mngr.get_parameter_value_lists(db_map)
        ]
        empty_child = self.empty_child()
        self.append_children(*children, empty_child)

    def empty_child(self):
        return ListNode(self, self.db_mngr, self.db_map)

    def data(self, role=Qt.DisplayRole):
        """Shows Spine icon for fun."""
        if role == Qt.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        elif role == Qt.DisplayRole:
            return f"root ({self.db_map.codename})"


class ListNode(GrayFontMixin, BoldFontMixin, AppendEmptyChildMixin, EditableMixin, TreeNode):
    """A list node."""

    def __init__(self, parent, db_mngr, db_map, identifier=None, name=None, value_list=()):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_map = db_map
        self.id = identifier
        self.name = name or "Type new list name here..."
        children = [ValueNode(self, from_database(value)) for value in value_list]
        empty_child = self.empty_child()
        self.append_children(*children, empty_child)

    def compile_value_list(self):
        return [to_database(child.value) for child in self.children[:-1]]

    def empty_child(self):
        return ValueNode(self, "Type new list value here...")

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.name
        return super().data(role)

    def set_data(self, name):
        if name == self.name:
            return False
        if self.id:
            self.update_name_in_db(name)
            return False
        self.name = name
        self.parent.append_empty_child(self.row)
        self.add_to_db()
        return True

    def set_child_data(self, child, value):
        if value == child.value:
            return False
        if self.id:
            self.update_value_list_in_db(child, value)
            return False
        child.value = value
        self.append_empty_child(child.row)
        self.add_to_db()
        return True

    def update_name_in_db(self, name):
        db_item = dict(id=self.id, name=name)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def update_value_list_in_db(self, child, value):
        value_list = self.compile_value_list()
        try:
            value_list[child.row] = value
        except IndexError:
            value_list.append(value)
        db_item = dict(id=self.id, value_list=value_list)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def add_to_db(self):
        """Add item to db."""
        value_list = self.compile_value_list()
        db_item = dict(name=self.name, value_list=value_list)
        self.db_mngr.add_parameter_value_lists({self.db_map: [db_item]})

    def update_from_db(self, name, value_list):
        self.name = name
        self.reset_value_list(value_list)

    def add_from_database(self, identifier, value_list):
        self.id = identifier
        self.reset_value_list(value_list)

    def reset_value_list(self, value_list):
        if value_list == self.compile_value_list():
            return
        value_count = len(value_list)
        curr_value_count = self.child_count() - 1
        if value_count > curr_value_count:
            added_count = value_count - curr_value_count
            children = [ValueNode(self) for _ in range(added_count)]
            self.insert_children(curr_value_count, *children)
        elif curr_value_count > value_count:
            removed_count = curr_value_count - value_count
            self.remove_children(value_count, removed_count)
        for child, value in zip(self.children, value_list):
            child.value = from_database(value)


class ValueNode(GrayFontMixin, EditableMixin, TreeNode):
    """A value node."""

    def __init__(self, parent, value=None):
        super().__init__(parent)
        self.value = value

    def data(self, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.value
        return super().data(role)

    def set_data(self, value):
        return self.parent.set_child_data(self, value)


class ParameterValueListModel(QAbstractItemModel):
    """A model to display parameter value list data in a tree view.


    Args:
        parent (DataStoreForm)
        db_maps (dict): maps db names to DiffDatabaseMapping instances
    """

    remove_selection_requested = Signal(name="remove_selection_requested")
    remove_icon = QIcon(":/icons/minus.png")

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._invisible_root_node = None
        self.connect_db_mngr_signals()

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_value_lists_added.connect(self.receive_parameter_value_lists_added)
        self.db_mngr.parameter_value_lists_updated.connect(self.receive_parameter_value_lists_updated)

    @Slot("QVariant", name="receive_parameter_value_lists_added")
    def receive_parameter_value_lists_added(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_node in self._invisible_root_node.children:
            items = db_map_data.get(db_node.db_map)
            if not items:
                continue
            items = {x["name"]: x for x in items}
            for list_node in db_node.children[:-1]:
                item = items.pop(list_node.name, None)
                if not item:
                    continue
                list_node.add_from_database(identifier=item["id"], value_list=item["value_list"].split(","))
            # Now append remaining items
            children = [
                ListNode(db_node, self.db_mngr, db_map, item["id"], item["name"], item["value_list"].split(","))
                for item in items.values()
            ]
            db_node.insert_children(db_node.child_count() - 1, *children)
        self.layoutChanged.emit()

    @Slot("QVariant", name="receive_parameter_value_lists_updated")
    def receive_parameter_value_lists_updated(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_node in self._invisible_root_node.children:
            items = db_map_data.get(db_node.db_map)
            if not items:
                continue
            items = {x["id"]: x for x in items}
            for list_node in db_node.children[:-1]:
                item = items.get(list_node.id)
                if not item:
                    continue
                list_node.update_from_db(name=item["name"], value_list=item["value_list"].split(","))
        self.layoutChanged.emit()

    def build_tree(self):
        """Initialize the internal data structure of TreeNode instances."""
        self.beginResetModel()
        self._invisible_root_node = InvisibleRootNode(self.db_mngr, *self.db_maps)
        self.track_item(self._invisible_root_node)
        self._invisible_root_node.fetch_children()
        self.endResetModel()

    def index_from_item(self, item):
        return self.createIndex(item.row, 0, item)

    def track_item(self, item):
        item.children_about_to_be_inserted.connect(self.receive_children_about_to_be_inserted)
        item.children_inserted.connect(self.receive_children_inserted)
        item.children_about_to_be_removed.connect(self.receive_children_about_to_be_removed)
        item.children_removed.connect(self.receive_children_removed)

    def stop_tracking_item(self, item):
        item.children_about_to_be_inserted.disconnect(self.receive_children_about_to_be_inserted)
        item.children_inserted.disconnect(self.receive_children_inserted)
        item.children_about_to_be_removed.disconnect(self.receive_children_about_to_be_removed)
        item.children_removed.disconnect(self.receive_children_removed)

    @Slot("QVariant", "int", "int", name="receive_children_about_to_be_inserted")
    def receive_children_about_to_be_inserted(self, parent_item, first, last):
        parent_index = self.index_from_item(parent_item)
        self.beginInsertRows(parent_index, first, last)

    @Slot("QVariant", name="receive_children_inserted")
    def receive_children_inserted(self, children):
        self.endInsertRows()
        for child in children:
            self.track_item(child)

    @Slot("QVariant", "int", "int", name="receive_children_about_to_be_removed")
    def receive_children_about_to_be_removed(self, parent_item, first, last):
        parent_index = self.index_from_item(parent_item)
        self.beginRemoveRows(parent_index, first, last)

    @Slot("QVariant", name="receive_children_removed")
    def receive_children_removed(self, children):
        self.endRemoveRows()
        for child in children:
            self.stop_tracking_item(child)

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the item in the model specified by the given row, column and parent index."""
        if not parent.isValid():
            parent_node = self._invisible_root_node
        else:
            parent_node = parent.internalPointer()
        node = parent_node.children[row]
        return self.createIndex(row, column, node)

    def parent(self, index):
        """Returns the parent of the model item with the given index."""
        if not index.isValid():
            return QModelIndex()
        parent_node = index.internalPointer().parent
        if parent_node is None:
            return QModelIndex()
        return self.createIndex(0, 0, parent_node)

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows under the given parent.
        Get it from the lenght of the appropriate list.
        """
        if not parent.isValid():
            parent_node = self._invisible_root_node
        else:
            parent_node = parent.internalPointer()
        return parent_node.child_count()

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 1

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the index.
        """
        if not index.isValid():
            return None
        return index.internalPointer().data(role)

    def flags(self, index):
        """Returns the item flags for the given index.
        """
        return index.internalPointer().flags()

    def setData(self, index, value, role=Qt.EditRole):
        """Sets data for given index and role.
        Returns True if successful; otherwise returns False.
        """
        if not index.isValid() or role != Qt.EditRole:
            return False
        node = index.internalPointer()
        if node.set_data(value):
            self.dataChanged.emit(index, index, [role])
            return True
        return False
