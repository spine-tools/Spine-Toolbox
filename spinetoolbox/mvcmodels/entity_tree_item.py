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
from PySide2.QtCore import Qt, Signal, QModelIndex
from sqlalchemy import or_
from PySide2.QtGui import QFont, QBrush, QIcon
from ..helpers import all_ids


class TreeItem:
    """A tree item that can fetch its children."""

    def __init__(self, parent=None):
        """Init class.

        Args:
            parent (TreeItem, NoneType): the parent item or None
        """
        self._children = []
        self._parent = None
        self._fetched = False
        self.parent = parent
        self.children = []

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        if not all(isinstance(child, TreeItem) for child in children):
            raise ValueError("all items in children must be instance of TreeItem")
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
        return self.child(-1)

    def child_count(self):
        """Returns the number of children."""
        return len(self._children)

    def child_number(self):
        """Returns the row of this item as a children, or 0 if it doesn't have a parent."""
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
        """Returns the next sibling or None if last or if doesn't have a parent."""
        if self.parent is None:
            return None
        return self.parent.child(self.child_number() + 1)

    def previous_sibling(self):
        """Returns the previous sibling or None if first or if doesn't have a parent."""
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
        self._children[position:position] = new_children
        return True

    def remove_children(self, position, count):
        """Removes count children starting from the given position."""
        if position > self.child_count() or position < 0:
            return False
        if position + count > self.child_count():
            count = self.child_count() - position
        del self._children[position : position + count]
        return True

    def clear_children(self):
        """Clear all children, used when resetting the model."""
        self.children.clear()

    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, column, role=Qt.DisplayRole):
        """Returns data from this item."""
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
        """Fetches more children and returns them in a list.
        The base class implementation returns an empty list.
        """
        self._fetched = True
        return []


class MultiDBTreeItem(TreeItem):
    """A tree item that may belong in multiple databases."""

    primary_key = ["name"]

    def __init__(self, db_map_data, parent=None):
        """Init class.

        Args:
            db_map_data (dict): maps instances of DiffDatabaseMapping to the data of the item in that db

        """
        super().__init__(parent)
        self._db_map_data = db_map_data
        self._child_map = dict()

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
        """Clear all children, used when resetting the model."""
        super.clear_children()
        self._child_map.clear()

    def _refresh_child_map(self):
        """Recomputes the child map."""
        self._child_map.clear()
        for row, child in enumerate(self.children):
            for db_map in child.db_maps:
                self._child_map[(db_map, child.db_map_data_field(db_map, "id"))] = row

    def find_children_by_id(self, db_map, *ids):
        """Yields children with the given ids in the given db_map or all of them if ids is the all_ids constant."""
        if ids == all_ids:
            yield from self._children
        else:
            for id_ in ids:
                if (db_map, id_) in self._child_map:
                    row = self._child_map[db_map, id_]
                    yield self._children[row]

    @property
    def unique_identifier(self):
        """"Returns the value of the primary key for this item or None if non unique across all dbs."""
        pks = [tuple(self.db_map_data_field(db_map, field) for field in self.primary_key) for db_map in self.db_maps]
        if len(set(pks)) != 1:
            return None
        return pks[0]

    @property
    def display_name(self):
        """"Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "name")

    @property
    def display_database(self):
        """"Returns the database for display."""
        return ",".join([self.db_map_data_field(db_map, "database") for db_map in self.db_maps])

    @property
    def first_db_map(self):
        """Returns the first db_map where this item belongs."""
        return list(self._db_map_data.keys())[0]

    @property
    def last_db_map(self):
        """Returns the last db_map where this item belongs."""
        return list(self._db_map_data.keys())[-1]

    @property
    def db_maps(self):
        """Returns a list of all db_maps where this item belongs."""
        return list(self._db_map_data.keys())

    def add_db_map_data(self, db_map, new_data):
        """Adds new data from db_map for this item."""
        self._db_map_data[db_map] = new_data

    def pop_db_map(self, db_map):
        """Removes the mapping for given db_map and returns it."""
        return self._db_map_data.pop(db_map, None)

    def has_one_db_map(self, db_map):
        """Returns true if the given db map is the only one."""
        return len(self._db_map_data) == 1 and db_map in self._db_map_data

    def db_map_data(self, db_map):
        """Returns the data of this item in given db_map or None if not found."""
        return self._db_map_data.get(db_map)

    def db_map_data_field(self, db_map, field, default=None):
        """Returns the data of this item for given filed in given db_map or None if not found."""
        return self._db_map_data.get(db_map, {}).get(field, default)

    def add_db_map_data_field(self, db_map, field, value):
        """Adds a new field to the data of this item in given db_map."""
        db_map_data = self.db_map_data(db_map)
        if db_map_data:
            db_map_data[field] = value

    def _get_children_data(self, db_map):
        """Generates child data by running the children query on the given db_map."""
        for child in self._children_query(db_map):
            yield child._asdict()

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def _create_child_item(self, db_map_data):
        """Returns a child item from given db_map data.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def fetch_more(self):
        """Returns a list of new children to add to the model."""
        filtered = list()
        for db_map in self.db_maps:
            children_data = self._get_children_data(db_map)
            new_children = self._create_new_children(db_map, children_data)
            filtered += self._filter_and_merge(new_children, filtered)
        self._fetched = True
        return filtered

    def add_children_from_data(self, db_map, children_data):
        """
        Returns new children from given data.
        Data is *not* checked for integrity (dups, etc.).

        Args:
            db_map (DiffDatabaseMapping)
            children_data (list): collection of dicts
        """
        new_children = self._create_new_children(db_map, children_data)
        return self._filter_and_merge(new_children, self.children)

    def _filter_and_merge(self, new_children, existing_children):
        """Checks for collision between new children and existing ones.
        Merges children that collide into the existent, returns the others."""
        ref = {child.unique_identifier: child for child in existing_children}
        filtered = []
        for new_child in new_children:
            existing_child = ref.get(new_child.unique_identifier)
            if existing_child:
                # Collision, update existing and get rid of new one
                for db_map in new_child.db_maps:
                    existing_child.add_db_map_data(db_map, new_child.db_map_data(db_map))
                del new_child
            else:
                # No collision, add the new item
                filtered.append(new_child)
        return filtered

    def _create_new_children(self, db_map, children_data):
        """
        Creates and returns new items.
        Data is *not* checked for integrity (dups, etc.).

        Args:
            db_map (DiffDatabaseMapping)
            children_data (iter): dicts with data from each child
        """
        new_children = []
        database = self.db_map_data_field(db_map, "database")
        for child_data in children_data:
            child_data["database"] = database
            new_children.append(self._create_child_item({db_map: child_data}))
        return new_children

    def update_children_from_data(self, db_map, children_data):
        """

        Args:
            db_map (DiffDatabaseMapping)
            children_data (list): collection of dicts
        """
        updated_rows = []
        database = self.db_map_data_field(db_map, "database")
        for child_data in children_data:
            child_data["database"] = database
            row = self._child_map.get((db_map, child_data["id"]))
            if row is None:
                continue
            child = self._children[row]
            child.add_db_map_data(db_map, child_data)
            updated_rows.append(row)
        return updated_rows

    def split_ambiguous(self, rows):
        """
        Check if the children at rows are ambiguous (which may result from an update operation).
        """
        new_children = {}
        for row in rows:
            child = self.child(row)
            if not child:
                continue
            while not child.unique_identifier:
                db_map = child.first_db_map
                child_data = child.pop_db_map(db_map)
                new_child = self._create_child_item({db_map: child_data})
                new_children.append(new_child)
                existing_child = new_children.get(new_child.unique_identifier)
                if existing_child:
                    # Collision, update existing and get rid of new one
                    existing_child.add_db_map_data(db_map, child_data)
                    del new_child
                else:
                    # No collision, add the new item
                    new_children[new_child.unique_identifier] = new_child
        return self._filter_and_merge(new_children.values(), self.children)

    def data(self, column, role):
        """Returns data from this item."""
        if role == Qt.DisplayRole:
            return (self.display_name, self.display_database)[column]
        if role == Qt.DecorationRole and column == 0:
            return self.display_icon()

    def display_icon(self):
        """Returns an icon to display next to the name.
        Reimplement in subclasses to return something nice."""
        return None

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return {"database": self.db_map_data_field(self.first_db_map, "database")}


class TreeRootItem(MultiDBTreeItem):
    @property
    def unique_identifier(self):
        """"Returns a unique identifier for this item across all dbs."""
        return "root"

    @property
    def display_name(self):
        """"Returns a unique identifier for this item across all dbs."""
        return "root"


class ObjectTreeRootItem(TreeRootItem):
    """An object tree root item."""

    context_menu_actions = {"Add object classes": QIcon(":/icons/menu_icons/cube_plus.svg")}

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map."""
        return db_map.query(db_map.object_class_sq)

    def _create_child_item(self, db_map_data):
        return ObjectClassItem(db_map_data, parent=self)


class RelationshipTreeRootItem(TreeRootItem):
    """A relationship tree root item."""

    context_menu_actions = {"Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg")}

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map."""
        return db_map.query(db_map.wide_relationship_class_sq)

    def _create_child_item(self, db_map_data):
        return RelationshipClassItem(db_map_data, parent=self)


class EntityClassItem(MultiDBTreeItem):
    """An entity class item."""

    def data(self, column, role=Qt.DisplayRole):
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

    type_name = "object class"
    context_menu_actions = {
        "Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg"),
        "Add objects": QIcon(":/icons/menu_icons/cube_plus.svg"),
        "": None,
        "Edit object classes": QIcon(":/icons/menu_icons/cube_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg"),
    }

    def _children_query(self, db_map):
        """Returns a query to the given db map that returns children of this item."""
        return db_map.query(db_map.object_sq).filter_by(class_id=self.db_map_data_field(db_map, 'id'))

    def _create_child_item(self, db_map_data):
        return ObjectItem(db_map_data, parent=self)

    def display_icon(self):
        """Returns the object class icon."""
        name = self.db_map_data_field(self.first_db_map, "name")
        # TODO return self._spinedb_manager.icon_manager.object_icon(name)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(object_class_name=data['name'], database=data['database'])


class RelationshipClassItem(EntityClassItem):
    """A relationship class item."""

    primary_key = ["name", "object_class_name_list"]
    type_name = "relationship class"
    context_menu_actions = {
        "Add relationships": QIcon(":/icons/menu_icons/cubes_plus.svg"),
        "": None,
        "Edit relationship classes": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    def __init__(self, *args, **kwargs):
        """Overriden method to parse some data for convenience later."""
        super().__init__(*args, **kwargs)
        for db_map in self.db_maps:
            object_class_id_list = self.db_map_data_field(db_map, "object_class_id_list")
            if object_class_id_list:
                parsed_object_class_id_list = [int(id_) for id_ in object_class_id_list.split(",")]
                self.add_db_map_data_field(db_map, "parsed_object_class_id_list", parsed_object_class_id_list)
            object_class_name_list = self.db_map_data_field(db_map, "object_class_name_list")
            if object_class_name_list:
                parsed_object_class_name_list = object_class_name_list.split(",")
                self.add_db_map_data_field(db_map, "parsed_object_class_name_list", parsed_object_class_name_list)

    def display_icon(self):
        """Returns relationship class icon."""
        object_class_name_list = self.db_map_data_field(self.first_db_map, "object_class_name_list")
        # TODO return self._spinedb_manager.icon_manager.relationship_icon(object_class_name_list)

    def _children_query(self, db_map):
        """Returns a query to the given db map that returns children of this item."""
        sq = db_map.wide_relationship_sq
        qry = db_map.query(sq).filter_by(class_id=self.db_map_data_field(db_map, 'id'))
        if isinstance(self.parent, ObjectItem):
            object_id = self.parent.db_map_data_field(db_map, 'id')
            qry = qry.filter(
                or_(
                    sq.c.object_id_list.like(f"%,{object_id},%"),
                    sq.c.object_id_list.like(f"{object_id},%"),
                    sq.c.object_id_list.like(f"%,{object_id}"),
                    sq.c.object_id_list == object_id,
                )
            )
        return qry

    def _create_child_item(self, db_map_data):
        return RelationshipItem(db_map_data, parent=self)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(relationship_class_name=data['name'], database=data['database'])


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        return super().data(column, role)


class ObjectItem(EntityItem):
    """An object item."""

    type_name = "object"
    context_menu_actions = {
        "Edit objects": QIcon(":/icons/menu_icons/cube_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg"),
    }

    def _children_query(self, db_map):
        """Returns a query to the given db map that returns children of this item."""
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        sq = db_map.wide_relationship_class_sq
        return db_map.query(sq).filter(
            or_(
                sq.c.object_class_id_list.like(f"%,{object_class_id},%"),
                sq.c.object_class_id_list.like(f"{object_class_id},%"),
                sq.c.object_class_id_list.like(f"%,{object_class_id}"),
                sq.c.object_class_id_list == object_class_id,
            )
        )

    def _create_child_item(self, db_map_data):
        return RelationshipClassItem(db_map_data, parent=self)

    def display_icon(self):
        """Returns the object class icon."""
        name = self.parent.db_map_data_field(self.first_db_map, "name")
        # TODO return self._spinedb_manager.icon_manager.object_icon(name)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        parent_data = self.parent.db_map_data(self.first_db_map)
        return dict(object_class_name=parent_data['name'], object_name=data['name'], database=data['database'])


class RelationshipItem(EntityItem):
    """An object item."""

    primary_key = ["name", "object_name_list"]

    type_name = "relationship"
    context_menu_actions = {
        "Edit relationships": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Find next": QIcon(":/icons/menu_icons/ellipsis-h.png"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    def __init__(self, *args, **kwargs):
        """Overriden method to parse some data for convenience later.
        Also make sure we never try and fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True
        for db_map in self.db_maps:
            object_id_list = self.db_map_data_field(db_map, "object_id_list")
            if object_id_list:
                parsed_object_id_list = [int(id_) for id_ in object_id_list.split(",")]
                self.add_db_map_data_field(db_map, "parsed_object_id_list", parsed_object_id_list)
            object_name_list = self.db_map_data_field(db_map, "object_name_list")
            if object_name_list:
                parsed_object_name_list = object_name_list.split(",")
                self.add_db_map_data_field(db_map, "parsed_object_name_list", parsed_object_name_list)

    @property
    def display_name(self):
        """"Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "object_name_list")

    def display_icon(self):
        """Returns relationship class icon."""
        object_class_name_list = self.parent.db_map_data_field(self.first_db_map, "object_class_name_list")
        # TODO return self._spinedb_manager.icon_manager.relationship_icon(object_class_name_list)

    def has_children(self):
        return False

    def new_children_from_data(self, db_map, children_data):
        pass

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        parent_data = self.parent.db_map_data(self.first_db_map)
        return dict(
            relationship_class_name=parent_data['name'],
            object_name_list=data['object_name_list'],
            database=data['database'],
        )
