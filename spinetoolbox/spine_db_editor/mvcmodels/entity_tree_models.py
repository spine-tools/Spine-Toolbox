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

"""Models to represent entities in a tree."""

from PySide6.QtCore import QObject, QSettings
from spinedb_api import DatabaseMapping
from ...helpers import DB_ITEM_SEPARATOR
from ...spine_db_manager import SpineDBManager
from .entity_tree_item import EntityTreeRootItem
from .level_filter import LevelFilterMixin
from .multi_db_tree_model import MultiDBTreeModel


class EntityTreeModel(LevelFilterMixin, MultiDBTreeModel):
    LEVEL_ITEM_TYPES = ("entity_class", "entity")

    def __init__(self, parent: QObject, app_settings: QSettings, db_mngr: SpineDBManager, *db_maps: DatabaseMapping):
        super().__init__(parent, db_mngr, *db_maps)
        self._app_settings = app_settings
        self._hide_empty_classes = app_settings.value("appSettings/hideEmptyClasses", defaultValue="false") == "true"

    @property
    def root_item_type(self):
        return EntityTreeRootItem

    def build_tree(self):
        """Builds tree, dropping any stale level-filter state so a reload starts unfiltered."""
        self.reset_level_filter_state()
        super().build_tree()

    def filter_text(self, item) -> str:
        """Returns the real, unmangled name of an entity-tree item to match against a level filter.

        For classes this is ``EntityClassItem.name``: the plain class name, without the "(superclass)"
        suffix that ``display_data`` appends. For entities it is the entity byname joined with the DB item
        separator; ``display_data`` mangles a repeated parent element into a placeholder glyph, so it is
        unsuitable for matching. Falls back to the entity's ``name`` when there is no byname.

        Args:
            item: an entity-tree item
        """
        if item.item_type == "entity":
            byname = item.byname
            if byname:
                return DB_ITEM_SEPARATOR.join(byname)
            return item.name
        return item.name

    def item_is_visible(self, item) -> bool:
        """Returns whether a tree item passes the active level filters.

        Only classes get the hide-empty-parent behaviour, and only over LOADED rows: when the entity filter
        is active a class is visible if any already-fetched entity matches, or - optimistically - if it still
        has unfetched entities (``can_fetch_more``, no fetch is forced); it is hidden only when it is fully
        loaded and nothing matches. So a collapsed/unfetched class stays visible until expanded, then refines
        (the insert/remove hooks restart the debounced re-apply once its children are fetched). Entities are
        filtered purely by their own level's regex. Because the entity regex applies at every entity depth
        top-down, a deep element only shows when it and all of its ancestor entities match (caveat N1).

        Args:
            item: an entity-tree item
        """
        if item.item_type == "entity_class":
            if not self.item_passes_own_filter(item):
                return False
            if self.level_filter_active("entity"):
                if any(self.item_passes_own_filter(c) for c in item.children if c.item_type == "entity"):
                    return True
                return item.can_fetch_more()
            return True
        if item.item_type == "entity":
            return self.item_passes_own_filter(item)
        return True

    def _apply_level_filters(self) -> None:
        """Rebuilds all child maps so the current level filters take effect.

        This is the cheap recompute that only re-filters the already-loaded rows; the force-fetch that
        makes a lower-level filter accurate across collapsed classes runs separately (see
        :meth:`LevelFilterMixin._run_force_fetch`).
        """
        self._rebuild_all_child_maps()

    def _level_filter_root(self):
        """See base class. The entity tree walks from its visible root item down through the classes."""
        return self.root_item

    def _rebuild_all_child_maps(self) -> None:
        """Recursively rebuilds every item's child map, emitting a single layout change for the whole tree.

        Unlike calling ``refresh_child_map`` per node (which emits a layout-change pair each time), this emits
        exactly one ``layoutAboutToBeChanged``/``layoutChanged`` around a non-emitting rebuild of each item.
        """
        root = self.root_item
        if root is None:
            return
        self.layoutAboutToBeChanged.emit()
        stack = [root]
        while stack:
            item = stack.pop()
            item.rebuild_child_map()
            stack.extend(item.children)
        self.layoutChanged.emit()

    def find_next_entity_index(self, index):
        """Find and return next occurrence of relationship item."""
        if not index.isValid():
            return None
        ent_item = self.item_from_index(index)
        if not (ent_item.item_type == "entity" and ent_item.element_name_list):
            return None
        # Get all ancestors
        el_item = ent_item.parent_item
        if el_item.item_type != "entity":
            return None
        for db_map in ent_item.db_maps:
            # Get data from ancestors
            ent_data = ent_item.db_map_data(db_map)
            el_data = el_item.db_map_data(db_map)
            # Get specific data for our searches
            el_id = el_data["id"]
            element_ids = list(reversed(ent_data["element_id_list"]))
            dimension_ids = list(reversed(ent_data["dimension_id_list"]))
            # Find position in the entity of the (grand parent) element,
            # then use it to determine dimension and element id to look for
            pos = element_ids.index(el_id) - 1
            element_id = element_ids[pos]
            dimension_id = dimension_ids[pos]
            # Return first node that passes all cascade filters
            for parent_item in self.find_items(db_map, (dimension_id, element_id), fetch=True):
                for item in parent_item.find_children(lambda child: child.display_id == ent_item.display_id):
                    return self.index_from_item(item)
        return None

    def save_hide_empty_classes(self):
        hide_empty_classes = "true" if self.hide_empty_classes else "false"
        self._app_settings.setValue("appSettings/hideEmptyClasses", hide_empty_classes)

    @property
    def hide_empty_classes(self):
        return self._hide_empty_classes

    @hide_empty_classes.setter
    def hide_empty_classes(self, hide_empty_classes):
        if self._hide_empty_classes is hide_empty_classes:
            return
        self._hide_empty_classes = hide_empty_classes
        self.root_item.refresh_child_map()


def group_items_by_db_map(indexes):
    """Groups items from given tree indexes by db map.

    Args:
        indexes (Iterable of QModelIndex): index to entity tree model

    Returns:
        dict: lists of dictionary items keyed by DatabaseMapping
    """
    d = {}
    for index in indexes:
        model = index.model()
        if model is None:
            continue
        item = model.item_from_index(index)
        if item.item_type == "root":
            continue
        for db_map in item.db_maps:
            d.setdefault(db_map, []).append(item.db_map_data(db_map))
    return d
