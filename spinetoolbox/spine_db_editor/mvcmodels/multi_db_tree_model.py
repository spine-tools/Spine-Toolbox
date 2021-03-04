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
A base model class to represent items from multiple databases in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:    17.6.2020
"""
from PySide2.QtCore import QModelIndex, Qt
from ...mvcmodels.minimal_tree_model import MinimalTreeModel, TreeItem


class MultiDBTreeModel(MinimalTreeModel):
    """Base class for all tree models in Spine db editor."""

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
