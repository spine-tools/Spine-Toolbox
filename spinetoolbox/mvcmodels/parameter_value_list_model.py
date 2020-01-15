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

from PySide2.QtCore import Qt, Signal, QModelIndex
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinedb_api import to_database, from_database
from .minimal_tree_model import MinimalTreeModel, TreeItem


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


class DBItem(AppendEmptyChildMixin, TreeItem):
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
    def db_mngr(self):
        return self.model.db_mngr

    def fetch_more(self):
        children = [
            ListItem(self.db_map, value_list["id"], value_list["name"], value_list["value_list"].split(","))
            for value_list in self.db_mngr.get_parameter_value_lists(self.db_map)
        ]
        empty_child = self.empty_child()
        self.append_children(*children, empty_child)
        self._fetched = True

    def empty_child(self):
        return ListItem(self.db_map)

    def data(self, column, role=Qt.DisplayRole):
        """Shows Spine icon for fun."""
        if role == Qt.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        if role == Qt.DisplayRole:
            return f"root ({self.db_map.codename})"


class ListItem(GrayFontMixin, BoldFontMixin, AppendEmptyChildMixin, EditableMixin, TreeItem):
    """A list item."""

    def __init__(self, db_map, identifier=None, name=None, value_list=()):
        super().__init__()
        self.db_map = db_map
        self.id = identifier
        self.name = name or "Type new list name here..."
        self.value_list = value_list

    @property
    def db_mngr(self):
        return self.model.db_mngr

    def fetch_more(self):
        children = [ValueItem(from_database(value)) for value in self.value_list]
        empty_child = self.empty_child()
        self.append_children(*children, empty_child)
        self._fetched = True

    def compile_value_list(self):
        return [to_database(child.value) for child in self.children[:-1]]

    # pylint: disable=no-self-use
    def empty_child(self):
        return ValueItem("Type new list value here...")

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.name
        return super().data(column, role)

    def set_data(self, column, name):
        if name == self.name:
            return False
        if self.id:
            self.update_name_in_db(name)
            return False
        self.name = name
        self.parent_item.append_empty_child(self.child_number())
        self.add_to_db()
        return True

    def set_child_data(self, child, value):
        if value == child.value:
            return False
        if self.id:
            self.update_value_list_in_db(child, value)
            return False
        child.value = value
        self.append_empty_child(child.child_number())
        self.add_to_db()
        return True

    def update_name_in_db(self, name):
        db_item = dict(id=self.id, name=name)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def update_value_list_in_db(self, child, value):
        value_list = self.compile_value_list()
        value = to_database(value)
        try:
            value_list[child.child_number()] = value
        except IndexError:
            value_list.append(value)
        db_item = dict(id=self.id, value_list=value_list)
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def add_to_db(self):
        """Add item to db."""
        value_list = self.compile_value_list()
        db_item = dict(name=self.name, value_list=value_list)
        self.db_mngr.add_parameter_value_lists({self.db_map: [db_item]})

    def handle_updated_in_db(self, name, value_list):
        """Runs when an item with this id has been updated in the db."""
        self.name = name
        self.reset_value_list(value_list)

    def handle_added_to_db(self, identifier, value_list):
        """Runs when the item with this name has been added to the db."""
        self.id = identifier
        self.reset_value_list(value_list)

    def reset_value_list(self, value_list):
        curr_value_list = self.compile_value_list()
        if value_list == curr_value_list:
            return
        value_count = len(value_list)
        curr_value_count = len(curr_value_list)
        if value_count > curr_value_count:
            added_count = value_count - curr_value_count
            children = [ValueItem() for _ in range(added_count)]
            self.insert_children(curr_value_count, *children)
        elif curr_value_count > value_count:
            removed_count = curr_value_count - value_count
            self.remove_children(value_count, removed_count)
        for child, value in zip(self.children, value_list):
            child.value = from_database(value)


class ValueItem(GrayFontMixin, EditableMixin, TreeItem):
    """A value item."""

    def __init__(self, value=None):
        super().__init__()
        self.value = value
        self._fetched = True

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.value
        return super().data(column, role)

    def set_data(self, column, value):
        return self.parent_item.set_child_data(self, value)


class ParameterValueListModel(MinimalTreeModel):
    """A model to display parameter value list data in a tree view.


    Args:
        parent (DataStoreForm)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    remove_selection_requested = Signal()
    remove_icon = QIcon(":/icons/minus.png")

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def receive_parameter_value_lists_added(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            items = {x["name"]: x for x in items}
            for list_item in db_item.children[:-1]:
                item = items.pop(list_item.name, None)
                if not item:
                    continue
                list_item.handle_added_to_db(identifier=item["id"], value_list=item["value_list"].split(","))
            # Now append remaining items
            children = [
                ListItem(db_item.db_map, item["id"], item["name"], item["value_list"].split(","))
                for item in items.values()
            ]
            db_item.insert_children(db_item.child_count() - 1, *children)
        self.layoutChanged.emit()

    def receive_parameter_value_lists_updated(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            items = {x["id"]: x for x in items}
            for list_item in db_item.children[:-1]:
                item = items.get(list_item.id)
                if not item:
                    continue
                list_item.handle_updated_in_db(name=item["name"], value_list=item["value_list"].split(","))
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
        self._invisible_root_item = TreeItem(self)
        self.endResetModel()
        db_items = [DBItem(db_map) for db_map in self.db_maps]
        self._invisible_root_item.append_children(*db_items)
        for item in self.visit_all():
            item.fetch_more()

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 1
