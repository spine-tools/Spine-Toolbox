######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
from PySide2.QtCore import Qt, QObject, Signal, QModelIndex
from sqlalchemy import or_
from PySide2.QtGui import QFont, QBrush, QIcon


class TreeItem(QObject):
    """A tree item that can fetch its children."""

    children_about_to_be_inserted = Signal("QVariant", "int", "int", name="children_about_to_be_inserted")
    children_about_to_be_removed = Signal("QVariant", "int", "int", name="children_about_to_be_removed")
    children_inserted = Signal("QVariant", name="children_inserted")
    children_removed = Signal("QVariant", name="children_removed")

    def __init__(self, parent=None):
        """Init class.

        Args:
            parent (TreeItem, NoneType): the parent item or None
        """
        super().__init__(parent)
        self._children = []
        self._parent = None
        self._fetched = False
        self.parent = parent
        self.children = []

    @property
    def child_item_type(self):
        """Returns the type of child items. Reimplement in subclasses to return something more meaningfull."""
        return TreeItem

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        bad_types = [type(child) for child in children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Cand't set children of type {bad_types} for an item of type {type(self)}")
        for child in children:
            child.parent = self
        self._children = children

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if not isinstance(parent, TreeItem) and parent is not None:
            raise ValueError("Parent must be instance of TreeItem or None")
        self._parent = parent

    def child(self, row):
        """Returns the child at given row or None if out of bounds."""
        try:
            return self._children[row]
        except IndexError:
            return None

    def last_child(self):
        """Returns the last child."""
        return self.child(-1)

    def child_count(self):
        """Returns the number of children."""
        return len(self._children)

    def child_number(self):
        """Returns the rank of this item as a children, or 0 if it doesn't have a parent."""
        if self.parent is not None:
            return self.parent.children.index(self)
        return 0

    def find_children(self, cond=lambda child: True):
        """Returns children that meet condition expressed as a lambda function."""
        for child in self.children:
            if cond(child):
                yield child

    def find_child(self, cond=lambda child: True):
        """Returns first child that meet condition expressed as a lambda function or None."""
        return next(self.find_children(cond), None)

    def next_sibling(self):
        """Returns the next sibling or None if it's the last or if doesn't have a parent."""
        if self.parent is None:
            return None
        return self.parent.child(self.child_number() + 1)

    def previous_sibling(self):
        """Returns the previous sibling or None if it's first or if doesn't have a parent."""
        if self.child_number() == 0:
            return None
        return self.parent.child(self.child_number() - 1)

    def column_count(self):
        """Returns 0."""
        return 0

    def insert_children(self, position, new_children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            new_children (list): insert items from this list
        """
        bad_types = [type(child) for child in new_children if not isinstance(child, TreeItem)]
        if bad_types:
            raise TypeError(f"Cand't insert children of type {bad_types} to an item of type {type(self)}")
        if position < 0 or position > self.child_count() + 1:
            return False
        self.children_about_to_be_inserted.emit(self, position, len(new_children))
        for child in new_children:
            child.parent = self
        self._children[position:position] = new_children
        self.children_inserted.emit(new_children)
        return True

    def append_children(self, new_children):
        """Append children at the end."""
        return self.insert_children(self.child_count(), new_children)

    def remove_children(self, position, count):
        """Removes count children starting from the given position."""
        if position > self.child_count() or position < 0:
            return False
        if position + count > self.child_count():
            count = self.child_count() - position
        self.children_about_to_be_removed.emit(self, position, count)
        items = self._children[position : position + count]
        del self._children[position : position + count]
        self.children_removed.emit(items)
        return True

    def clear_children(self):
        """Clear children list."""
        self.children.clear()

    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        return None

    def has_children(self):
        """Returns whether or not this item has or could have children."""
        if self.child_count() or self.can_fetch_more():
            return True
        return False

    def can_fetch_more(self):
        """Returns whether or not this item can fetch more."""
        return not self._fetched

    def fetch_more(self):
        """Fetches more children."""
        self._fetched = True


class MultiDBTreeItem(TreeItem):
    """A tree item that may belong in multiple databases."""

    visual_key = ["name"]

    def __init__(self, db_mngr, db_map_id=None, parent=None):
        """Init class.

        Args:
            db_mngr (SpineDBManager)
            db_map_data (dict): maps instances of DiffDatabaseMapping to the id of the item in that db
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self._db_map_id = db_map_id
        self._child_map = dict()  # Maps db_map to id to row number

    def insert_children(self, position, new_children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            new_children (list): insert items from this list
        """
        bad_types = [type(child) for child in new_children if not isinstance(child, MultiDBTreeItem)]
        if bad_types:
            raise TypeError(f"Cand't insert children of type {bad_types} to an item of type {type(self)}")
        if super().insert_children(position, new_children):
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
        super.clear_children()
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
        if next(iter(ids)) is True:
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

    def take_db_map(self, db_map):
        """Removes the mapping for given db_map and returns it."""
        id_ = self._db_map_id.pop(db_map, None)
        if not self._db_map_id:
            self.parent.remove_children(self.child_number(), 1)
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
        other = type(self)(self.db_mngr, {db_map: id_})
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
        """Returns data for this item in given db_map or None if not present."""
        return self._db_map_id.get(db_map)

    def db_map_data(self, db_map):
        """Returns data for this item in given db_map or None if not present."""
        id_ = self.db_map_id(db_map)
        return self.db_mngr.get_data(db_map, self.item_type, id_)

    def db_map_data_field(self, db_map, field, default=None):
        """Returns field from data for this item in given db_map or None if not found."""
        return self.db_map_data(db_map).get(field, default)

    def _get_children_ids(self, db_map):
        """Returns a query that selects all children from given db_map.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def _create_new_children(self, db_map, children_ids):
        """
        Creates new items from ids associated to a db map.

        Args:
            db_map (DiffDatabaseMapping): create children for this db_map
            children_data (iter): create childs from these dictionaries
        """
        new_children = []
        for id_ in children_ids:
            new_children.append(self.child_item_type(self.db_mngr, {db_map: id_}))
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
        self.append_children(unmerged)

    def fetch_more(self):
        """Fetches children from all associated databases."""
        db_map_ids = {db_map: list(self._get_children_ids(db_map)) for db_map in self.db_maps}
        self.append_children_by_id(db_map_ids)
        self._fetched = True

    def append_children_by_id(self, db_map_ids):
        """
        Appends children by id.

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
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
        for db_map, ids in db_map_ids.items():
            for child in self.find_children_by_id(db_map, *ids, reverse=True):
                child.deep_remove_db_map(db_map)

    def update_children_by_id(self, db_map_ids):
        """
        Updates children by id. Essentially makes sure all children have a valid display id
        after an update in the underlying data. These may require 'splitting' a child
        into several for different dbs or merging two or more children from different dbs.

        Examples of problems:
        - The user renames an object class in one db but not in the others --> we need to split
        - The user renames an object class and the new name is already 'taken' by another object class in
          another db_map --> we need to merge

        Args:
            db_map_ids (dict): maps DiffDatabaseMapping instances to list of ids
        """
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

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.DisplayRole:
            return (self.display_name, self.display_database)[column]

    @property
    def display_icon(self):
        """Returns an icon to display next to the name.
        Reimplement in subclasses to return something nice."""
        return None

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

    context_menu_actions = {"Add object classes": QIcon(":/icons/menu_icons/cube_plus.svg")}

    def _get_children_ids(self, db_map):
        """Returns a query that selects all object classes from given db_map."""
        return {x["id"] for x in self.db_mngr.get_object_classes(db_map)}

    @property
    def child_item_type(self):
        """Returns an ObjectClassItem."""
        return ObjectClassItem


class RelationshipTreeRootItem(TreeRootItem):
    """A relationship tree root item."""

    context_menu_actions = {"Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg")}

    def _get_children_ids(self, db_map):
        """Returns a query that selects all relationship classes from given db_map."""
        return {x["id"] for x in self.db_mngr.get_relationship_classes(db_map)}

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
    context_menu_actions = {
        "Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg"),
        "Add objects": QIcon(":/icons/menu_icons/cube_plus.svg"),
        "": None,
        "Edit object classes": QIcon(":/icons/menu_icons/cube_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg"),
    }

    def _get_children_ids(self, db_map):
        """Returns a query that selects all objects of this class from given db_map."""
        return {x["id"] for x in self.db_mngr.get_objects(db_map, class_id=self.db_map_id(db_map))}

    @property
    def child_item_type(self):
        """Returns an ObjectItem."""
        return ObjectItem

    @property
    def display_icon(self):
        """Returns the object class icon."""
        return self.db_mngr.icon_mngr.object_icon(self.display_name)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(object_class_name=self.display_name, database=self.first_db_map.codename)


class RelationshipClassItem(EntityClassItem):
    """A relationship class item."""

    visual_key = ["name", "object_class_name_list"]
    item_type = "relationship class"
    context_menu_actions = {
        "Add relationships": QIcon(":/icons/menu_icons/cubes_plus.svg"),
        "": None,
        "Edit relationship classes": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    @property
    def display_icon(self):
        """Returns relationship class icon."""
        object_class_name_list = self.db_map_data_field(self.first_db_map, "object_class_name_list")
        return self.db_mngr.icon_mngr.relationship_icon(object_class_name_list)

    def _get_children_ids(self, db_map):
        """Returns a query that selects all relationships of this class from the db.
        If the parent is an ObjectItem, then only selects relationships involving that object.
        """
        kwargs = dict(class_id=self.db_map_id(db_map))
        if isinstance(self.parent, ObjectItem):
            kwargs = dict(**kwargs, object_id=self.parent.db_map_id(db_map))
        return {x["id"] for x in self.db_mngr.get_relationships(db_map, **kwargs)}

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
    context_menu_actions = {
        "Edit objects": QIcon(":/icons/menu_icons/cube_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg"),
    }

    def _get_children_ids(self, db_map):
        """Returns a query that selects all relationship classes involving the parent class
        from the given db_map.
        """
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        return {x["id"] for x in self.db_mngr.get_relationship_classes(db_map, object_class_id=object_class_id)}

    @property
    def child_item_type(self):
        """Returns a RelationshipClassItem."""
        return RelationshipClassItem

    @property
    def display_icon(self):
        """Returns the object class icon."""
        return self.parent.display_icon

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            object_class_name=self.parent.display_name,
            object_name=self.display_name,
            database=self.first_db_map.codename,
        )


class RelationshipItem(EntityItem):
    """An object item."""

    visual_key = ["name", "object_name_list"]

    item_type = "relationship"
    context_menu_actions = {
        "Edit relationships": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Find next": QIcon(":/icons/menu_icons/ellipsis-h.png"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    def __init__(self, *args, **kwargs):
        """Overriden method to parse some data for convenience later.
        Also make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True

    @property
    def display_name(self):
        """"Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "object_name_list")

    @property
    def display_icon(self):
        """Returns relationship class icon."""
        return self.parent.display_icon

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def new_children_from_data(self, db_map, children_data):
        """Pass, this item never has children."""
        pass

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            relationship_class_name=self.parent.display_name,
            object_name_list=self.display_name,
            database=self.first_db_map.codename,
        )
