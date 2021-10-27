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

from PySide2.QtCore import Qt, QModelIndex
from .tree_model_base import TreeModelBase
from .parameter_value_list_item import DBItem, ListItem


class ParameterValueListModel(TreeModelBase):
    """A model to display parameter_value_list data in a tree view."""

    def add_parameter_value_lists(self, db_map_data):
        for db_item, items in self._items_per_db_item(db_map_data).items():
            db_item.remove_wip_items({x["name"] for x in items})
            self._insert_items(db_item, items, ListItem)

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
