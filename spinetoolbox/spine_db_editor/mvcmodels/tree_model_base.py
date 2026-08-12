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

"""Models to represent things in a tree."""

from PySide6.QtCore import QModelIndex, QObject, Qt
from spinedb_api import DatabaseMapping
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel
from ...spine_db_manager import SpineDBManager
from .level_filter import LevelFilterMixin
from .tree_item_utility import StandardTreeItem


class TreeModelBase(LevelFilterMixin, MinimalTreeModel):
    """A base model to display items in a tree view.

    Mixes in :class:`LevelFilterMixin` so every subclass gets per-level regex filtering. A subclass only
    needs to set :attr:`LEVEL_ITEM_TYPES` (the filterable levels, top to bottom); the display name, the
    visibility predicate and the batched refresh are all provided here.
    """

    def __init__(self, parent: QObject, db_mngr: SpineDBManager, *db_maps: DatabaseMapping):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.destroyed.connect(lambda _: self._invisible_root_item.tear_down_recursively())

    def filter_text(self, item) -> str:
        """Returns the item's display name to match against its level filter.

        Args:
            item: a tree item

        Returns:
            the item's displayed text (for a list value this is the rendered value)
        """
        return str(item.data(0, Qt.ItemDataRole.DisplayRole))

    def item_is_visible(self, item) -> bool:
        """Returns whether a tree item passes the active level filters.

        The phantom add-row is always visible. An item on a filtered level must match its own regex. When a
        lower level has an active filter, a parent is kept only if a LOADED descendant matches, or -
        optimistically - if it can still fetch more (no fetch is forced); it is hidden only once it is fully
        loaded and nothing matches. Items on unfiltered levels (e.g. the db root) always pass.

        Args:
            item: a tree item

        Returns:
            whether the item is visible under the current filters
        """
        item_type = item.item_type
        if item_type not in self.LEVEL_ITEM_TYPES:
            return True
        if item.is_empty_row():
            return True
        if not self.item_passes_own_filter(item):
            return False
        lower_types = self.LEVEL_ITEM_TYPES[self.LEVEL_ITEM_TYPES.index(item_type) + 1 :]
        if any(self.level_filter_active(lower) for lower in lower_types):
            if any(self.item_is_visible(child) for child in item.non_empty_children):
                return True
            return item.can_fetch_more()
        return True

    def _apply_level_filters(self) -> None:
        """Refreshes the whole tree so the current level filters take effect, guarded against re-entrancy.

        These trees keep no child-position map, so a single ``layoutAboutToBeChanged``/``layoutChanged`` pair
        is enough for the view to re-query the visible rows.
        """
        if self._applying_level_filters:
            return
        self._applying_level_filters = True
        try:
            self.layoutAboutToBeChanged.emit()
            self._bump_filter_generation()
            self.layoutChanged.emit()
        finally:
            self._applying_level_filters = False

    def _level_filter_root(self):
        """See base class. The standard trees walk from the invisible root down through the db items."""
        return self._invisible_root_item

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 2.

        Returns:
            int: column count
        """
        return 2

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ("name", "description")[section]
        return None

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item.tear_down_recursively()
        self._invisible_root_item = StandardTreeItem(self)
        self.endResetModel()
        for db_map in self.db_maps:
            db_item = self._make_db_item(db_map)
            self._invisible_root_item.append_children([db_item])

    def _make_db_item(self, db_map):
        raise NotImplementedError()

    @staticmethod
    def db_item(item):
        while item.item_type != "db":
            item = item.parent_item
        return item

    def db_row(self, item):
        return self.db_item(item).child_number()
