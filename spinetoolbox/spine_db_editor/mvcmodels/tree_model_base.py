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
Models to represent things in a tree.

:authors: M. Marin (KTH)
:date:    1.0.2020
"""
from PySide2.QtCore import Qt, QModelIndex
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel
from .tree_item_utility import NonLazyTreeItem


class TreeModelBase(MinimalTreeModel):
    """A base model to display items in a tree view.


    Args:
        parent (SpineDBEditor)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "description")[section]
        return None

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = NonLazyTreeItem(self)
        self.endResetModel()
        for db_map in self.db_maps:
            db_item = self._make_db_item(db_map)
            self._invisible_root_item.append_children(db_item)
            db_item.append_children(*self._top_children())

    @staticmethod
    def _make_db_item(db_map):
        raise NotImplementedError()

    @staticmethod
    def _top_children():
        raise NotImplementedError()

    def _items_per_db_item(self, db_map_data):
        d = {}
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            d[db_item] = items
        return d

    def _ids_per_root_item(self, db_map_data, root_number=0):
        d = {}
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            d[root_item] = [x["id"] for x in items]
        return d

    @staticmethod
    def _db_map_data_per_id(db_map_data, id_key):
        d = {}
        for db_map, data in db_map_data.items():
            for item in data:
                id_ = item[id_key]
                d.setdefault(db_map, {}).setdefault(id_, []).append(item)
        return d

    def _update_leaf_items(self, root_item, ids):
        leaf_items = {leaf_item.id: leaf_item for leaf_item in root_item.children if leaf_item.id}
        for id_ in set(ids).intersection(leaf_items):
            leaf_item = leaf_items[id_]
            leaf_item.handle_updated_in_db()
            index = self.index_from_item(leaf_item)
            self.dataChanged.emit(index, index)
            if leaf_item.children:
                top_left = self.index_from_item(leaf_item.child(0))
                bottom_right = self.index_from_item(leaf_item.child(-1))
                self.dataChanged.emit(top_left, bottom_right)

    @staticmethod
    def _remove_leaf_items(root_item, ids):
        removed_rows = []
        for row, leaf_item in enumerate(root_item.children[:-1]):
            if leaf_item.id and leaf_item.id in ids:
                removed_rows.append(row)
        for row in sorted(removed_rows, reverse=True):
            root_item.remove_children(row, 1)

    @staticmethod
    def db_item(item):
        while item.item_type != "db":
            item = item.parent_item
        return item

    def db_row(self, item):
        return self.db_item(item).child_number()
