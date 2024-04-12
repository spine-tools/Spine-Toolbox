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

"""Base classes to represent items from multiple databases in a tree."""
from operator import attrgetter
from PySide6.QtCore import Qt
from ...helpers import rows_to_row_count_tuples, bisect_chunks
from ...fetch_parent import FlexibleFetchParent
from ...mvcmodels.minimal_tree_model import TreeItem


class MultiDBTreeItem(TreeItem):
    """A tree item that may belong in multiple databases."""

    item_type = None
    """Item type identifier string. Should be set to a meaningful value by subclasses."""
    visual_key = ["name"]
    _fetch_index = None

    def __init__(self, model, db_map_ids=None):
        """
        Args:
            model (MinimalTreeModel, optional): item's model
            db_map_ids (dict, optional): maps instances of DatabaseMapping to the id of the item in that db
        """
        super().__init__(model)
        if db_map_ids is None:
            db_map_ids = {}
        self._db_map_ids = db_map_ids
        self._child_map = {}  # Maps db_map to id to row number
        self._fetch_parent = FlexibleFetchParent(
            self.fetch_item_type,
            accepts_item=self.accepts_item,
            handle_items_added=self.handle_items_added,
            handle_items_removed=self.handle_items_removed,
            handle_items_updated=self.handle_items_updated,
            index=self._fetch_index,
            key_for_index=self._key_for_index,
            owner=self,
        )

    @property
    def visible_children(self):
        return self.children

    def row_count(self):
        """Overriden to use visible_children."""
        return len(self.visible_children)

    def child(self, row):
        """Overriden to use visible_children."""
        if 0 <= row < self.row_count():
            return self.visible_children[row]
        return None

    def child_number(self):
        """Overriden to use find_row which is a dict-lookup rather than a list.index() call."""
        if not self.parent_item:
            return None
        try:
            db_map, id_ = next(iter(self._db_map_ids.items()))
        except StopIteration:
            return None
        if isinstance(self.parent_item, MultiDBTreeItem):
            return self.parent_item.find_row(db_map, id_)
        return 0

    def refresh_child_map(self):
        """Recomputes the child map."""
        self.model.layoutAboutToBeChanged.emit()
        self._child_map.clear()
        for row, child in enumerate(self.visible_children):
            for db_map in child.db_maps:
                id_ = child.db_map_id(db_map)
                self._child_map.setdefault(db_map, {})[id_] = row
        self.model.layoutChanged.emit()

    def set_data(self, column, value, role):
        raise NotImplementedError()

    @property
    def db_mngr(self):
        return self.model.db_mngr

    @property
    def child_item_class(self):
        """Returns the type of child items."""
        raise NotImplementedError()

    @property
    def display_id(self):
        """Returns an id for display based on the display key. This id must be the same across all db_maps.
        If it's not, this property becomes None and measures need to be taken (see update_children_by_id).
        """
        ids = {tuple(self.db_map_data_field(db_map, field) for field in self.visual_key) for db_map in self.db_maps}
        if len(ids) != 1:
            return None
        return next(iter(ids))

    @property
    def name(self):
        return self.db_map_data_field(self.first_db_map, "name", default="")

    @property
    def display_data(self):
        """Returns the name for display."""
        return self.name

    @property
    def display_database(self):
        """Returns the database for display."""
        return ",".join([db_map.codename for db_map in self.db_maps])

    @property
    def display_icon(self):
        """Returns an icon to display next to the name.
        Reimplement in subclasses to return something nice."""
        return None

    @property
    def first_db_map(self):
        """Returns the first associated db_map."""
        return next(iter(self._db_map_ids))

    @property
    def db_maps(self):
        """Returns a list of all associated db_maps."""
        return list(self._db_map_ids)

    @property
    def db_map_ids(self):
        """Returns dict with db_map as key and id as value"""
        return self._db_map_ids

    def add_db_map_id(self, db_map, id_):
        """Adds id for this item in the given db_map."""
        self._db_map_ids[db_map] = id_
        index = self.index()
        sibling = index.sibling(index.row(), 1)
        self.model.dataChanged.emit(sibling, sibling)

    def take_db_map(self, db_map):
        """Removes the mapping for given db_map and returns it."""
        return self._db_map_ids.pop(db_map, None)

    def deep_refresh_children(self):
        """Refreshes children after taking db_maps from them.
        Called after removing and updating children for this item."""
        removed_rows = []
        for row, child in reversed(list(enumerate(self.children))):
            if not child.db_map_ids:
                removed_rows.append(row)
        for row, count in reversed(rows_to_row_count_tuples(removed_rows)):
            self.remove_children(row, count)
        for row, child in enumerate(self.children):
            child.deep_refresh_children()
        if self.children:
            top_row = 0
            bottom_row = self.row_count() - 1
            top_index = self.children[top_row].index().sibling(top_row, 1)
            bottom_index = self.children[bottom_row].index().sibling(bottom_row, 1)
            self.model.dataChanged.emit(top_index, bottom_index)

    def deep_remove_db_map(self, db_map):
        """Removes given db_map from this item and all its descendants."""
        for child in reversed(self.children):
            child.deep_remove_db_map(db_map)
        _ = self.take_db_map(db_map)

    def deep_take_db_map(self, db_map):
        """Removes given db_map from this item and all its descendants, and
        returns a new item from the db_map's data.

        Returns:
            MultiDBTreeItem, NoneType
        """
        id_ = self.take_db_map(db_map)
        if id_ is None:
            return None
        other = self.parent_item.make_or_restore_child({db_map: id_})
        other_children = []
        for child in self.children:
            other_child = child.deep_take_db_map(db_map)
            if other_child:
                other_children.append(other_child)
        other.children = other_children
        return other

    def deep_merge(self, other):
        """Merges another item and all its descendants into this one."""
        if not isinstance(other, type(self)):
            raise ValueError(f"Can't merge an instance of {type(other).__name__} into a MultiDBTreeItem.")
        for db_map in other.db_maps:
            self.add_db_map_id(db_map, other.db_map_id(db_map))
        self._merge_children(other.children)

    def db_map_id(self, db_map):
        """Returns the id for this item in given db_map or None if not present."""
        return self._db_map_ids.get(db_map)

    def db_map_data(self, db_map):
        """Returns data for this item in given db_map or an empty dict if not present."""
        id_ = self.db_map_id(db_map)
        return self.db_mngr.get_item(db_map, self.item_type, id_)

    def db_map_data_field(self, db_map, field, default=None):
        """Returns field from data for this item in given db_map or None if not found."""
        return self.db_map_data(db_map).get(field, default)

    def _create_new_children(self, db_map, children_ids, **kwargs):
        """
        Creates new items from ids associated to a db map.

        Args:
            db_map (DiffDatabaseMapping): create children for this db_map
            children_ids (iter): create children from these ids

        Returns:
            list of MultiDBTreeItem: new children
        """
        return [self.make_or_restore_child(db_map, id_, **kwargs) for id_ in children_ids]

    def make_or_restore_child(self, db_map, id_, **kwargs):
        """Makes or restores a child if one was ever made using given db_map and id.
        The purpose of restoring is to keep using the same FetchParent,
        which is useful in case the user undoes a series of removal operations
        that would add items in cascade to the tree.

        Args:
            db_map (DatabaseMapping)
            id (int)

        Returns:
            MultiDBTreemItem
        """
        db_map_ids = {db_map: id_}
        key = (db_map, id_)
        child = self._created_children.get(key)
        if child is not None:
            child.restore(db_map_ids, **kwargs)
            return child
        child = self._created_children[key] = self._make_child(db_map_ids, **kwargs)
        return child

    def restore(self, db_map_ids, **kwargs):
        self._db_map_ids.update(db_map_ids)

    def _make_child(self, db_map_ids, **kwargs):
        return self.child_item_class(self.model, db_map_ids, **kwargs)

    def _merge_children(self, new_children):
        """Merges new children into this item. Ensures that each child has a valid display id afterwards."""
        if not new_children:
            return
        if len(self._db_map_ids) == 1:
            self._insert_children_sorted(new_children)
            return
        existing_children = {child.display_id: child for child in self.children}
        unmerged = []
        for new_child in new_children:
            match = existing_children.get(new_child.display_id)
            if match:
                # Found match, merge and get rid of new just in case
                match.deep_merge(new_child)  # NOTE: This calls `_merge_children` on the match
                del new_child
            else:
                # No match
                existing_children[new_child.display_id] = new_child
                unmerged.append(new_child)
        if not unmerged:
            self.refresh_child_map()
            return
        self._insert_children_sorted(unmerged)

    def _insert_children_sorted(self, new_children):
        """Inserts and sorts children."""
        new_children = sorted(new_children, key=self._children_sort_key)
        for chunk, pos in bisect_chunks(self.children, new_children, key=self._children_sort_key):
            self.insert_children(pos, chunk)

    @property
    def _children_sort_key(self):
        return attrgetter("display_id")

    @property
    def fetch_item_type(self):
        return self.child_item_class.item_type

    def can_fetch_more(self):
        if self.fetch_item_type is None:
            return False
        result = False
        for db_map in self.db_maps:
            result |= self.db_mngr.can_fetch_more(db_map, self._fetch_parent)
        return result

    def fetch_more(self):
        """Fetches children from all associated databases."""
        if self.fetch_item_type is None:
            return
        for db_map in self.db_maps:
            self.db_mngr.fetch_more(db_map, self._fetch_parent)

    def fetch_more_if_possible(self):
        if self.can_fetch_more():
            self.fetch_more()

    def _key_for_index(self, db_map):
        return None

    def accepts_item(self, item, db_map):
        return True

    def handle_items_added(self, db_map_data):
        db_map_ids = {db_map: [x["id"] for x in data] for db_map, data in db_map_data.items()}
        self.append_children_by_id(db_map_ids)

    def handle_items_removed(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.remove_children_by_id(db_map_ids)

    def handle_items_updated(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.update_children_by_id(db_map_ids)

    def append_children_by_id(self, db_map_ids, **kwargs):
        """
        Appends children by id.

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        new_children = []
        for db_map, ids in db_map_ids.items():
            new_children += self._create_new_children(db_map, ids, **kwargs)
        self._merge_children(new_children)

    def remove_children_by_id(self, db_map_ids):
        """
        Removes children by id.

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        for db_map, ids in db_map_ids.items():
            for child in self.find_children_by_id(db_map, *ids, reverse=True):
                child.deep_remove_db_map(db_map)
        self.deep_refresh_children()

    def is_valid(self):
        """See base class."""
        return bool(self._db_map_ids)

    def update_children_by_id(self, db_map_ids, **kwargs):
        """
        Updates children by id. Essentially makes sure all children have a valid display id
        after updating the underlying data. These may require 'splitting' a child
        into several for different dbs or merging two or more children from different dbs.

        Examples of problems:

        - The user renames an object_class in one db but not in the others --> we need to split
        - The user renames an object_class and the new name is already 'taken' by another object_class in
          another db_map --> we need to merge

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        # Find rows to update and db_map ids to add
        rows_to_update = set()
        db_map_ids_to_add = dict()
        for db_map, ids in db_map_ids.items():
            for id_ in ids:
                row = self.find_row(db_map, id_)
                if row is not None:
                    rows_to_update.add(row)
                else:
                    db_map_ids_to_add.setdefault(db_map, set()).add(id_)
        new_children = []  # List of new children to be inserted
        for db_map, ids in db_map_ids_to_add.items():
            new_children += self._create_new_children(db_map, ids, **kwargs)
        # Check display ids
        display_ids = [child.display_id for child in self.children if child.display_id is not None]
        for row in sorted(rows_to_update, reverse=True):
            child = self.child(row)
            if not child:
                continue
            if not child.is_valid():
                self.remove_children(row, 1)
                display_ids.pop(row)
                continue
            while not child.display_id:
                # Split child until it recovers a valid display id
                db_map = child.first_db_map
                new_child = child.deep_take_db_map(db_map)
                new_children.append(new_child)
            if child.display_id in display_ids[:row] + display_ids[row + 1 :]:
                # Take the child and put it in the list to be merged
                new_children.append(child)
                self.remove_children(row, 1)
                display_ids.pop(row)
                new_children.append(child)
        self.deep_refresh_children()
        self._merge_children(new_children)
        top_left = self.model.index(0, 0, self.index())
        bottom_right = self.model.index(self.row_count() - 1, 0, self.index())
        self.model.dataChanged.emit(top_left, bottom_right)

    def insert_children(self, position, children):
        """Inserts new children at given position.

        Args:
            position (int): insert new items here
            children (Iterable of MultiDBTreeItem): insert items from this iterable

        Returns:
            bool: True if children were inserted successfully, False otherwise
        """
        bad_types = [type(child) for child in children if not isinstance(child, MultiDBTreeItem)]
        if bad_types:
            raise TypeError(f"Can't insert children of type {bad_types} to an item of type {type(self)}")
        if not super().insert_children(position, children):
            return False
        self.refresh_child_map()
        for child in children:
            child.register_fetch_parent()
        return True

    def remove_children(self, position, count):
        """Removes count children starting from the given position."""
        if super().remove_children(position, count):
            self.refresh_child_map()
            return True
        return False

    def reposition_child(self, row):
        child = self.child(row)
        if not child:
            return
        self.remove_children(row, 1)
        self._insert_children_sorted([child])

    def find_row(self, db_map, id_):
        return self._child_map.get(db_map, {}).get(id_)

    def find_children_by_id(self, db_map, *ids, reverse=True):
        """Generates children with the given ids in the given db_map.
        If the first id is None, then generates *all* children with the given db_map."""
        for row in self.find_rows_by_id(db_map, *ids, reverse=reverse):
            yield self.children[row]

    def find_rows_by_id(self, db_map, *ids, reverse=True):
        yield from sorted(self._find_unsorted_rows_by_id(db_map, *ids), reverse=reverse)

    def _find_unsorted_rows_by_id(self, db_map, *ids):
        """Generates rows corresponding to children with the given ids in the given db_map.
        If the only id given is None, then generates rows corresponding to *all* children with the given db_map."""
        if len(ids) == 1 and ids[0] is None:
            d = self._child_map.get(db_map)
            if d:
                yield from d.values()
        else:
            # Yield all children with the db_map *and* the id
            for id_ in ids:
                row = self.find_row(db_map, id_)
                if row is not None:
                    yield row

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return self.display_data
            if column == 1:
                return self.display_database
        if role == Qt.ItemDataRole.DecorationRole:
            if column == 0:
                return self.display_icon
        if role == Qt.ItemDataRole.EditRole:
            return self.edit_data

    def default_parameter_data(self):
        """Returns data to set as default in a parameter table when this item is selected."""
        return {"database": self.first_db_map.codename}

    def tear_down(self):
        super().tear_down()
        self._fetch_parent.set_obsolete(True)

    def register_fetch_parent(self):
        """Registers item's fetch parent for all model's databases."""
        for db_map in self.model.db_maps:
            self.model.db_mngr.register_fetch_parent(db_map, self._fetch_parent)
