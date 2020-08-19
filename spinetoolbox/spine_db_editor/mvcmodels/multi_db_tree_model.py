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
A base model class to represent items from multiple databases in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:    17.6.2020
"""
from PySide2.QtCore import QModelIndex, Qt
from ...mvcmodels.minimal_tree_model import MinimalTreeModel, TreeItem


class MultiDBTreeModel(MinimalTreeModel):
    """Base class for all data store view tree models."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager): A manager for the given db_maps
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._root_item = None
        self.active_member_indexes = dict()

    @property
    def root_item_type(self):
        """Implement in subclasses to create a model specific to any entity type."""
        raise NotImplementedError()

    @property
    def root_item(self):
        return self._root_item

    @property
    def root_index(self):
        return self.index_from_item(self._root_item)

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = TreeItem(self)
        self.endResetModel()
        self._root_item = self.root_item_type(self, dict.fromkeys(self.db_maps))
        self._invisible_root_item.append_children(self._root_item)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        item = self.item_from_index(index)
        if index.column() == 0:
            if role == Qt.DecorationRole:
                return item.display_icon
            if role == Qt.DisplayRole:
                return item.display_data
            if role == Qt.EditRole:
                return item.edit_data
        return item.data(index.column(), role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "database")[section]
        return None

    def find_items(self, db_map, path_prefix, parent_items=(), fetch=False):
        """Returns items at given path prefix.
        """
        if not parent_items:
            # Start from the root node
            parent_items = [self.root_item]
        for id_ in path_prefix:
            parent_items = [
                child for parent_item in parent_items for child in parent_item.find_children_by_id(db_map, id_)
            ]
            if fetch:
                for parent_item in parent_items:
                    parent = self.index_from_item(parent_item)
                    if self.canFetchMore(parent):
                        self.fetchMore(parent)
        return parent_items

    def is_active_member_index(self, index):
        return index in self.active_member_indexes.get(index.parent(), set())

    def set_active_member_indexes(self, indexes):
        self.active_member_indexes.clear()
        for ind in indexes:
            self.active_member_indexes.setdefault(ind.parent(), set()).add(ind)
        self.emit_data_changed_for_column(0, self.active_member_indexes)

    def emit_data_changed_for_column(self, column, parents):
        for parent in parents:
            top_left = self.index(0, column, parent)
            bottom_right = self.index(self.rowCount(parent), column, parent)
            self.dataChanged.emit(top_left, bottom_right)
