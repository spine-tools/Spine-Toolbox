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
A tree model for parameter value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinedb_api import to_database
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel, TreeItem
from spinetoolbox.mvcmodels.shared import PARSED_ROLE
from spinetoolbox.helpers import try_number_from_string


class ValueListTreeItem(TreeItem):
    """A tree item that can fetch its children."""

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def db_mngr(self):
        return self.model.db_mngr

    def can_fetch_more(self):
        """Disables lazy loading by returning False."""
        return False

    def insert_children(self, position, *children):
        """Fetches the children as they become parented."""
        if not super().insert_children(position, *children):
            return False
        for child in children:
            child.fetch_more()
        return True


class EditableMixin:
    def flags(self, column):
        """Makes items editable."""
        return Qt.ItemIsEditable | super().flags(column)


class GrayFontMixin:
    """Paints the text gray."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and self.child_number() == self.parent_item.child_count() - 1:
            gray_color = QGuiApplication.palette().text().color()
            gray_color.setAlpha(128)
            gray_brush = QBrush(gray_color)
            return gray_brush
        return super().data(column, role)


class BoldFontMixin:
    """Bolds text."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(column, role)


class AppendEmptyChildMixin:
    """Provides a method to append an empty child if needed."""

    def append_empty_child(self, row):
        """Append empty child if the row is the last one."""
        if row == self.child_count() - 1:
            empty_child = self.empty_child()
            self.append_children(empty_child)


class DBItem(AppendEmptyChildMixin, ValueListTreeItem):
    """An item representing a db."""

    def __init__(self, db_map):
        """Init class.

        Args
            db_mngr (SpineDBManager)
            db_map (DiffDatabaseMapping)
        """
        super().__init__()
        self.db_map = db_map

    @property
    def item_type(self):
        return "db"

    def fetch_more(self):
        empty_child = self.empty_child()
        self.append_children(empty_child)
        self._fetched = True

    def empty_child(self):
        return ListItem(self.db_map)

    def data(self, column, role=Qt.DisplayRole):
        """Shows Spine icon for fun."""
        if role == Qt.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        if role in (Qt.DisplayRole, Qt.EditRole):
            return f"root ({self.db_map.codename})"


class ListItem(GrayFontMixin, BoldFontMixin, AppendEmptyChildMixin, EditableMixin, ValueListTreeItem):
    """A list item."""

    def __init__(self, db_map, identifier=None):
        super().__init__()
        self.db_map = db_map
        self.id = identifier
        self._name = "Type new list name here..."

    @property
    def item_type(self):
        return "list"

    @property
    def name(self):
        if not self.id:
            return self._name
        return self.db_mngr.get_item(self.db_map, "parameter value list", self.id)["name"]

    @property
    def value_list(self):
        if not self.id:
            return [child.value for child in self.children[:-1]]
        return self.db_mngr.get_item(self.db_map, "parameter value list", self.id)["value_list"].split(";")

    def fetch_more(self):
        children = [ValueItem() for _ in self.value_list]
        if self.id:
            children.append(self.empty_child())
        self.append_children(*children)
        self._fetched = True

    # pylint: disable=no-self-use
    def empty_child(self):
        return ValueItem(is_empty=True)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.name
        return super().data(column, role)

    def set_data(self, column, name, role):
        if role != Qt.EditRole or name == self.name:
            return False
        if self.id:
            self.update_name_in_db(name)
            return False
        self._name = name
        self.parent_item.append_empty_child(self.child_number())
        self.append_children(self.empty_child())
        return True

    def set_child_data(self, child, value):
        if value == child.value:
            return False
        if self.id:
            self.update_value_list_in_db(child, value)
        else:
            self.add_to_db(child, value)
        return True

    def update_name_in_db(self, name):
        db_item = dict(id=self.id, name=name)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def _new_value_list(self, child_number, value):
        value_list = self.value_list.copy()
        try:
            value_list[child_number] = value
        except IndexError:
            value_list.append(value)
        return value_list

    def update_value_list_in_db(self, child, value):
        value_list = self._new_value_list(child.child_number(), value)
        db_item = dict(id=self.id, value_list=value_list)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def add_to_db(self, child, value):
        """Add item to db."""
        value_list = self._new_value_list(child.child_number(), value)
        db_item = dict(name=self.name, value_list=value_list)
        self.db_mngr.add_parameter_value_lists({self.db_map: [db_item]})

    def handle_updated_in_db(self):
        """Runs when an item with this id has been updated in the db."""
        self.update_value_list()

    def handle_added_to_db(self, identifier):
        """Runs when the item with this name has been added to the db."""
        self.id = identifier
        self.update_value_list()

    def update_value_list(self):
        value_count = len(self.value_list)
        curr_value_count = self.child_count() - 1
        if value_count > curr_value_count:
            added_count = value_count - curr_value_count
            children = [ValueItem() for _ in range(added_count)]
            self.insert_children(curr_value_count, *children)
        elif curr_value_count > value_count:
            removed_count = curr_value_count - value_count
            self.remove_children(value_count, removed_count)


class ValueItem(GrayFontMixin, EditableMixin, ValueListTreeItem):
    """A value item."""

    def __init__(self, is_empty=False):
        super().__init__()
        self._is_empty = is_empty
        self._fetched = True

    @property
    def item_type(self):
        return "value"

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def value(self):
        return self.db_mngr.get_value_list_item(self.db_map, self.parent_item.id, self.child_number(), Qt.EditRole)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole, PARSED_ROLE):
            if self._is_empty:
                return {PARSED_ROLE: None}.get(role, "Enter new list value here...")
            return self.db_mngr.get_value_list_item(self.db_map, self.parent_item.id, self.child_number(), role)
        return super().data(column, role)

    def set_data(self, column, value, role):
        if role != Qt.EditRole:
            return False
        value = try_number_from_string(value)
        value = to_database(value)
        return self.set_data_in_db(value)

    def set_data_in_db(self, db_value):
        return self.parent_item.set_child_data(self, db_value)


class ParameterValueListModel(MinimalTreeModel):
    """A model to display parameter value list data in a tree view.


    Args:
        parent (DataStoreForm)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def receive_parameter_value_lists_added(self, db_map_data):
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            # First realize the ones added locally
            ids = {x["name"]: x["id"] for x in items}
            for list_item in db_item.children[:-1]:
                id_ = ids.pop(list_item.name, None)
                if not id_:
                    continue
                list_item.handle_added_to_db(identifier=id_)
            # Now append the ones added externally
            children = [ListItem(db_item.db_map, id_) for id_ in ids.values()]
            db_item.insert_children(db_item.child_count() - 1, *children)

    def receive_parameter_value_lists_updated(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            ids = {x["id"] for x in items}
            list_items = {list_item.id: list_item for list_item in db_item.children[:-1]}
            for id_ in ids.intersection(list_items):
                list_items[id_].handle_updated_in_db()
        self.layoutChanged.emit()

    def receive_parameter_value_lists_removed(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            ids = {x["id"] for x in items}
            removed_rows = []
            for row, list_item in enumerate(db_item.children[:-1]):
                if list_item.id in ids:
                    removed_rows.append(row)
            for row in sorted(removed_rows, reverse=True):
                db_item.remove_children(row, 1)
        self.layoutChanged.emit()

    def build_tree(self):
        """Initialize the internal data structure of the model."""
        self.beginResetModel()
        self._invisible_root_item = ValueListTreeItem(self)
        self.endResetModel()
        db_items = [DBItem(db_map) for db_map in self.db_maps]
        self._invisible_root_item.append_children(*db_items)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 1

    def index_name(self, index):
        return self.data(index.parent(), role=Qt.DisplayRole)

    def get_set_data_delayed(self, index):
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.

        Args:
            index (QModelIndex)

        Returns:
            function
        """
        item = self.item_from_index(index)
        return lambda value, item=item: item.set_data_in_db(value)
