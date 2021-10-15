######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
A tree model for parameter_value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

import json
from PySide2.QtCore import Qt, QModelIndex, QTimer
from PySide2.QtGui import QIcon
from spinedb_api import to_database
from spinetoolbox.mvcmodels.shared import PARSED_ROLE
from .tree_model_base import TreeModelBase
from .tree_item_utility import (
    EmptyChildMixin,
    GrayIfLastMixin,
    BoldTextMixin,
    EditableMixin,
    StandardDBItem,
    FetchMoreMixin,
    LeafItem,
)
from ...helpers import CharIconEngine, rows_to_row_count_tuples


class DBItem(EmptyChildMixin, FetchMoreMixin, StandardDBItem):
    """An item representing a db."""

    @property
    def item_type(self):
        return "db"

    @property
    def fetch_item_type(self):
        return "parameter_value_list"

    def empty_child(self):
        return ListItem()

    def remove_wip_items(self, names):
        removed_rows = [
            row for row, list_item in enumerate(self.children[:-1]) if list_item.id is None and list_item.name in names
        ]
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.remove_children(row, count)


class ListItem(GrayIfLastMixin, EditableMixin, EmptyChildMixin, BoldTextMixin, LeafItem):
    """A list item."""

    def __init__(self, identifier=None, name=None):
        super().__init__(identifier=identifier)
        self._name = name

    @property
    def item_type(self):
        return "parameter_value_list"

    def _make_item_data(self):
        return {"name": "Type new list name here..." if self._name is None else self._name}

    @property
    def value_list(self):
        if not self.id:
            return []
        return self.db_mngr.get_parameter_value_list(self.db_map, self.id, role=Qt.EditRole)

    def _do_finalize(self):
        super()._do_finalize()
        children = [ValueItem(self.id) for _ in self.value_list]
        self.append_children(children)

    # pylint: disable=no-self-use
    def empty_child(self):
        return ValueItem(self.id)

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            engine = CharIconEngine("\uf022", 0)
            return QIcon(engine.pixmap())
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.EditRole):
        if role != Qt.EditRole or value == self.data(column, role):
            return False
        if self.id:
            db_item = self._make_item_to_update(column, value)
            self.update_item_in_db(db_item)
            return True
        # Don't add item to db. Items are only added when the first list value is set.
        # Instead, insert a wip list item with a just name, and no values yet
        self.parent_item.insert_children(self.child_number(), [ListItem(name=value)])
        return True

    def update_item_in_db(self, db_item):
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})

    def handle_updated_in_db(self):
        value_count = len(self.value_list)
        curr_value_count = self.child_count() - 1
        if value_count > curr_value_count:
            added_count = value_count - curr_value_count
            children = [ValueItem(self.id) for _ in range(added_count)]
            self.insert_children(curr_value_count, children)
        elif curr_value_count > value_count:
            removed_count = curr_value_count - value_count
            self.remove_children(value_count, removed_count)


class ValueItem(GrayIfLastMixin, EditableMixin, LeafItem):
    @property
    def item_type(self):
        return "list_value"

    @property
    def value(self):
        return self.db_mngr.get_value_list_item(self.db_map, self.id, self.child_number(), Qt.EditRole)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole, PARSED_ROLE):
            value = self.db_mngr.get_value_list_item(self.db_map, self.id, self.child_number(), role)
            if value is not None:
                return value
            return "Enter new list value here..." if role != PARSED_ROLE else None
        return super().data(column, role)

    def _make_item_to_add(self, value):
        db_value = to_database(value)[0]
        return self.make_item_to_add(db_value)

    def make_item_to_add(self, db_value):
        value_list = self.parent_item.value_list.copy()
        try:
            value_list[self.child_number()] = db_value
        except IndexError:
            value_list.append(db_value)
        return [(self.parent_item.name, json.loads(value)) for value in value_list]

    def _make_item_to_update(self, _column, value):
        return self._make_item_to_add(value)

    def add_item_to_db(self, db_item):
        QTimer.singleShot(0, lambda: self._do_add_item_to_db(db_item))

    def _do_add_item_to_db(self, db_item):
        self.db_mngr.import_data({self.db_map: {"parameter_value_lists": db_item}})

    def update_item_in_db(self, db_item):
        self.add_item_to_db(db_item)


class ParameterValueListModel(TreeModelBase):
    """A model to display parameter_value_list data in a tree view."""

    def add_parameter_value_lists(self, db_map_data):
        for db_item, items in self._items_per_db_item(db_map_data).items():
            db_item.remove_wip_items({x["name"] for x in items})
            children = [ListItem(x["id"]) for x in items]
            db_item.insert_children_sorted(children)

    def update_parameter_value_lists(self, db_map_data):
        for root_item, items in self._items_per_db_item(db_map_data).items():
            self._update_leaf_items(root_item, {x["id"] for x in items})

    def remove_parameter_value_lists(self, db_map_data):
        for root_item, items in self._items_per_db_item(db_map_data).items():
            self._remove_leaf_items(root_item, {x["id"] for x in items})

    @staticmethod
    def _make_db_item(db_map):
        return DBItem(db_map)

    @staticmethod
    def _top_children():
        return []

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1."""
        return 1

    def index_name(self, index):
        return self.data(index.parent(), role=Qt.DisplayRole)

    def get_set_data_delayed(self, index):
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.

        Args:
            index (QModelIndex)

        Returns:
            Callable
        """
        item = self.item_from_index(index)
        return lambda value, item=item: item.add_item_to_db(item.make_item_to_add(value[0]))
