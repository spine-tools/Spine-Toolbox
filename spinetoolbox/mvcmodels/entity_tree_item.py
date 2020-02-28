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
Classes to represent entities in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QBrush, QIcon
from .minimal_tree_model import TreeItem


class MultiDBTreeItem(TreeItem):
    """A tree item that may belong in multiple databases."""

    item_type = None
    """Item type identifier string. Should be set to a meaningful value by subclasses."""
    visual_key = ["name"]

    def __init__(self, model=None, db_map_id=None):
        """Init class.

        Args:
            db_mngr (SpineDBManager): a database manager
            db_map_data (dict): maps instances of DiffDatabaseMapping to the id of the item in that db
        """
        super().__init__(model)
        if db_map_id is None:
            db_map_id = {}
        self._db_map_id = db_map_id
        self._child_map = dict()  # Maps db_map to id to row number

    @property
    def db_mngr(self):
        return self.model.db_mngr

    @property
    def child_item_type(self):
        """Returns the type of child items. Reimplement in subclasses to return something more meaningful."""
        return MultiDBTreeItem

    @property
    def display_id(self):
        """"Returns an id for display based on the display key. This id must be the same across all db_maps.
        If it's not, this property becomes None and measures need to be taken (see update_children_by_id).
        """
        ids = [tuple(self.db_map_data_field(db_map, field) for field in self.visual_key) for db_map in self.db_maps]
        if len(set(ids)) != 1:
            return None
        return ids[0]

    @property
    def display_name(self):
        """"Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "name")

    @property
    def display_database(self):
        """"Returns the database for display."""
        return ",".join([db_map.codename for db_map in self.db_maps])

    @property
    def display_icon(self):
        """Returns an icon to display next to the name.
        Reimplement in subclasses to return something nice."""
        return None

    @property
    def first_db_map(self):
        """Returns the first associated db_map."""
        return list(self._db_map_id.keys())[0]

    @property
    def last_db_map(self):
        """Returns the last associated db_map."""
        return list(self._db_map_id.keys())[-1]

    @property
    def db_maps(self):
        """Returns a list of all associated db_maps."""
        return list(self._db_map_id.keys())

    def add_db_map_id(self, db_map, id_):
        """Adds id for this item in the given db_map."""
        self._db_map_id[db_map] = id_
        index = self.index()
        sibling = index.sibling(index.row(), 1)
        self.model.dataChanged.emit(sibling, sibling)

    def take_db_map(self, db_map):
        """Removes the mapping for given db_map and returns it."""
        id_ = self._db_map_id.pop(db_map, None)
        if self._db_map_id:
            index = self.index()
            sibling = index.sibling(index.row(), 1)
            self.model.dataChanged.emit(sibling, sibling)
        else:
            self.parent_item.remove_children(self.child_number(), 1)
        return id_

    def deep_remove_db_map(self, db_map):
        """Removes given db_map from this item and all its descendants."""
        for child in reversed(self.children):
            child.deep_remove_db_map(db_map)
        _ = self.take_db_map(db_map)

    def deep_take_db_map(self, db_map):
        """Takes given db_map from this item and all its descendants.
        Returns a new item from taken data or None if db_map is not present in the first place.
        """
        id_ = self.take_db_map(db_map)
        if not id_:
            return None
        other = type(self)({db_map: id_})
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
            raise ValueError(f"Can't merge an instance of {type(other)} into a MultiDBTreeItem.")
        for db_map in other.db_maps:
            self.add_db_map_id(db_map, other.db_map_id(db_map))
        self._merge_children(other.children)

    def db_map_id(self, db_map):
        """Returns the id for this item in given db_map or None if not present."""
        return self._db_map_id.get(db_map)

    def db_map_data(self, db_map):
        """Returns data for this item in given db_map or None if not present."""
        id_ = self.db_map_id(db_map)
        return self.db_mngr.get_item(db_map, self.item_type, id_)

    def db_map_data_field(self, db_map, field, default=None):
        """Returns field from data for this item in given db_map or None if not found."""
        return self.db_map_data(db_map).get(field, default)

    def _create_new_children(self, db_map, children_ids):
        """
        Creates new items from ids associated to a db map.

        Args:
            db_map (DiffDatabaseMapping): create children for this db_map
            children_data (iter): create childs from these dictionaries
        """
        new_children = []
        for id_ in children_ids:
            new_children.append(self.child_item_type(self.model, {db_map: id_}))
        return new_children

    def _merge_children(self, new_children):
        """Merges new children into this item. Ensures that each children has a valid display id afterwards.
        """
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
        self.append_children(*unmerged)

    def has_children(self):
        """Returns whether or not this item has or could have children."""
        if self.can_fetch_more():
            return any(self._get_children_ids(db_map) for db_map in self.db_maps)
        return bool(self.child_count())

    def fetch_more(self):
        """Fetches children from all associated databases."""
        super().fetch_more()
        db_map_ids = {db_map: list(self._get_children_ids(db_map)) for db_map in self.db_maps}
        self.append_children_by_id(db_map_ids)

    def _get_children_ids(self, db_map):
        """Returns a list of children ids.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def append_children_by_id(self, db_map_ids):
        """
        Appends children by id.

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        if self.can_fetch_more():
            self.model.layoutChanged.emit()
            return
        new_children = []
        for db_map, ids in db_map_ids.items():
            new_children += self._create_new_children(db_map, ids)
        self._merge_children(new_children)

    def remove_children_by_id(self, db_map_ids):
        """
        Removes children by id.

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        if self.can_fetch_more():
            self.model.layoutChanged.emit()
            return
        for db_map, ids in db_map_ids.items():
            for child in self.find_children_by_id(db_map, *ids, reverse=True):
                child.deep_remove_db_map(db_map)

    def update_children_by_id(self, db_map_ids):
        """
        Updates children by id. Essentially makes sure all children have a valid display id
        after updating the underlying data. These may require 'splitting' a child
        into several for different dbs or merging two or more children from different dbs.

        Examples of problems:

        - The user renames an object class in one db but not in the others --> we need to split
        - The user renames an object class and the new name is already 'taken' by another object class in
          another db_map --> we need to merge

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
        if self.can_fetch_more():
            return
        # Find updated rows
        updated_rows = []
        for db_map, ids in db_map_ids.items():
            updated_rows += list(self.find_rows_by_id(db_map, *ids))
        updated_rows = set(updated_rows)
        # Check display ids
        display_ids = [child.display_id for child in self.children if child.display_id]
        new_children = []  # List of new children to be inserted for solving display id problems
        for row in sorted(updated_rows, reverse=True):
            child = self.child(row)
            if not child:
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
        self._merge_children(new_children)

    def insert_children(self, position, *children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            children (iter): insert items from this iterable
        """
        bad_types = [type(child) for child in children if not isinstance(child, MultiDBTreeItem)]
        if bad_types:
            raise TypeError(f"Cand't insert children of type {bad_types} to an item of type {type(self)}")
        if super().insert_children(position, *children):
            self._refresh_child_map()
            return True
        return False

    def remove_children(self, position, count):
        """Removes count children starting from the given position."""
        if super().remove_children(position, count):
            self._refresh_child_map()
            return True
        return False

    def clear_children(self):
        """Clear children list."""
        super().clear_children()
        self._child_map.clear()

    def _refresh_child_map(self):
        """Recomputes the child map."""
        self._child_map.clear()
        for row, child in enumerate(self.children):
            for db_map in child.db_maps:
                id_ = child.db_map_id(db_map)
                self._child_map.setdefault(db_map, dict())[id_] = row

    def find_children_by_id(self, db_map, *ids, reverse=True):
        """Generates children with the given ids in the given db_map.
        If the first id is True, then generates *all* children with the given db_map."""
        for row in self.find_rows_by_id(db_map, *ids, reverse=reverse):
            yield self._children[row]

    def find_rows_by_id(self, db_map, *ids, reverse=True):
        yield from sorted(self._find_unsorted_rows_by_id(db_map, *ids), reverse=reverse)

    def _find_unsorted_rows_by_id(self, db_map, *ids):
        """Generates rows corresponding to children with the given ids in the given db_map.
        If the first id is True, then generates rows corresponding to *all* children with the given db_map."""
        if next(iter(ids), False) is True:
            # Yield all children with the db_map regardless of the id
            d = self._child_map.get(db_map)
            if d:
                yield from d.values()
        else:
            # Yield all children with the db_map *and* the id
            for id_ in ids:
                row = self._child_map.get(db_map, {}).get(id_, None)
                if row is not None:
                    yield row

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.DisplayRole:
            return (self.display_name, self.display_database)[column]

    def default_parameter_data(self):
        """Returns data to set as default in a parameter table when this item is selected."""
        return {"database": self.first_db_map.codename}


class TreeRootItem(MultiDBTreeItem):

    item_type = "root"

    @property
    def display_id(self):
        """"See super class."""
        return "root"

    @property
    def display_name(self):
        """"See super class."""
        return "root"


class ObjectTreeRootItem(TreeRootItem):
    """An object tree root item."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_menu_actions = [{"Add object classes": QIcon(":/icons/menu_icons/cube_plus.svg")}]

    def _get_children_ids(self, db_map):
        """Returns a list of object class ids."""
        return [x["id"] for x in self.db_mngr.get_object_classes(db_map)]

    @property
    def child_item_type(self):
        """Returns an ObjectClassItem."""
        return ObjectClassItem


class RelationshipTreeRootItem(TreeRootItem):
    """A relationship tree root item."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_menu_actions = [{"Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg")}]

    def _get_children_ids(self, db_map):
        """Returns a list of relationship class ids."""
        return [x["id"] for x in self.db_mngr.get_relationship_classes(db_map)]

    @property
    def child_item_type(self):
        """Returns a RelationshipClassItem."""
        return RelationshipClassItem


class EntityClassItem(MultiDBTreeItem):
    """An entity class item."""

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        if role == Qt.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        if role == Qt.ForegroundRole and column == 0:
            if not self.has_children():
                return QBrush(Qt.gray)
        return super().data(column, role)


class ObjectClassItem(EntityClassItem):
    """An object class item."""

    item_type = "object class"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_menu_actions = [
            {
                "Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg"),
                "Add objects": QIcon(":/icons/menu_icons/cube_plus.svg"),
            },
            {"Edit object classes": QIcon(":/icons/menu_icons/cube_pen.svg")},
            {"Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg")},
        ]

    @property
    def display_icon(self):
        """Returns the object class icon."""
        return self.db_mngr.entity_class_icon(self.first_db_map, "object class", self.db_map_id(self.first_db_map))

    def _get_children_ids(self, db_map):
        """Returns a list of object ids in this class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "object") if x["class_id"] == self.db_map_id(db_map)]

    @property
    def child_item_type(self):
        """Returns an ObjectItem."""
        return ObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(object_class_name=self.display_name, database=self.first_db_map.codename)


class RelationshipClassItem(EntityClassItem):
    """A relationship class item."""

    visual_key = ["name", "object_class_name_list"]
    item_type = "relationship class"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_menu_actions = [
            {"Add relationships": QIcon(":/icons/menu_icons/cubes_plus.svg")},
            {"Edit relationship classes": QIcon(":/icons/menu_icons/cubes_pen.svg")},
            {"Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg")},
        ]

    @property
    def display_icon(self):
        """Returns relationship class icon."""
        return self.db_mngr.entity_class_icon(
            self.first_db_map, "relationship class", self.db_map_id(self.first_db_map)
        )

    def _get_children_ids(self, db_map):
        """Returns a list of relationship ids in this class.
        If the parent is an ObjectItem, then only returns ids of relationships involving that object.
        """
        if not isinstance(self.parent_item, ObjectItem):
            return [
                x["id"]
                for x in self.db_mngr.get_items(db_map, "relationship")
                if x["class_id"] == self.db_map_id(db_map)
            ]
        object_id = self.parent_item.db_map_id(db_map)
        return [
            x["id"]
            for items in self.db_mngr.find_cascading_relationships({db_map: {object_id}}).values()
            for x in items
            if x["class_id"] == self.db_map_id(db_map)
        ]

    @property
    def child_item_type(self):
        """Returns a RelationshipItem."""
        return RelationshipItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(relationship_class_name=self.display_name, database=self.first_db_map.codename)


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        return super().data(column, role)


class ObjectItem(EntityItem):
    """An object item."""

    item_type = "object"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_menu_actions = [
            {"Edit objects": QIcon(":/icons/menu_icons/cube_pen.svg")},
            {"Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg")},
        ]

    def _get_children_ids(self, db_map):
        """Returns a list of relationship class ids involving this item's class.
        """
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        return [
            x["id"]
            for items in self.db_mngr.find_cascading_relationship_classes({db_map: {object_class_id}}).values()
            for x in items
        ]

    @property
    def child_item_type(self):
        """Returns a RelationshipClassItem."""
        return RelationshipClassItem

    @property
    def display_icon(self):
        """Returns the object class icon."""
        return self.parent_item.display_icon

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            object_class_name=self.parent_item.display_name,
            object_name=self.display_name,
            database=self.first_db_map.codename,
        )


class RelationshipItem(EntityItem):
    """An object item."""

    visual_key = ["name", "object_name_list"]
    item_type = "relationship"

    def __init__(self, *args, **kwargs):
        """Overridden method to parse some data for convenience later.
        Also make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True
        self.context_menu_actions = [
            {"Edit relationships": QIcon(":/icons/menu_icons/cubes_pen.svg")},
            {"Find next": QIcon(":/icons/menu_icons/ellipsis-h.png")},
            {"Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg")},
        ]

    @property
    def object_name_list(self):
        return self.db_map_data_field(self.first_db_map, "object_name_list", default="")

    @property
    def display_name(self):
        """"Returns the name for display."""
        return (
            self.object_name_list.replace(self.parent_item.parent_item.display_name + ",", "")
            .replace("," + self.parent_item.parent_item.display_name, "")
            .replace(",", self.db_mngr._GROUP_SEP)
        )

    @property
    def display_icon(self):
        """Returns relationship class icon."""
        return self.parent_item.display_icon

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            relationship_class_name=self.parent_item.display_name,
            object_name_list=self.db_map_data_field(self.first_db_map, "object_name_list"),
            database=self.first_db_map.codename,
        )

    def _get_children_ids(self, db_map):
        """See base class."""
        raise NotImplementedError()
