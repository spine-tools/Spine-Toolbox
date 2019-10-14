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
from ..helpers import all_ids


class TreeItem(QObject):
    """A tree item that can fetch its children."""

    rows_about_to_be_inserted = Signal("QVariant", "int", "int", name="rows_about_to_be_inserted")
    rows_about_to_be_removed = Signal("QVariant", "int", "int", name="rows_about_to_be_removed")
    rows_inserted = Signal("QVariant", name="rows_inserted")
    rows_removed = Signal("QVariant", name="rows_removed")

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
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        if not all(isinstance(child, TreeItem) for child in children):
            raise ValueError("all items in children must be instance of TreeItem")
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
        self.rows_about_to_be_inserted.emit(self, position, len(new_children))
        for child in new_children:
            child.parent = self
        self._children[position:position] = new_children
        self.rows_inserted.emit(new_children)
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
        self.rows_about_to_be_removed.emit(self, position, count)
        items = self._children[position : position + count]
        del self._children[position : position + count]
        self.rows_removed.emit(items)
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
        """Fetches more children.
        """
        self._fetched = True


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
        db_map = self._db_map_data.pop(db_map, None)
        if not self._db_map_data:
            self.parent.remove_children(self.child_number(), 1)
        # Update child map, but maybe not dramatic if we don't
        self._child_map = {key: value for key, value in self._child_map.items() if key[0] != db_map}
        return db_map

    def deep_remove_db_map(self, db_map):
        for child in reversed(self.children):
            child.deep_remove_db_map(db_map)
        _ = self.pop_db_map(db_map)

    def deep_take_db_map(self, db_map):
        """Takes data and children from given db_map into a new item."""
        db_map_data = self.pop_db_map(db_map)
        if not db_map_data:
            return None
        other = type(self)({db_map: db_map_data})
        other_children = []
        for child in self.children:
            other_child = child.deep_take_db_map(db_map)
            if other_child:
                other_children.append(other_child)
        other.children = other_children
        return other

    def deep_merge(self, other):
        if not isinstance(other, type(self)):
            raise ValueError(f"Can't merge an instance of {type(other)} into a MultiDBTreeItem.")
        for db_map in other.db_maps:
            self.add_db_map_data(db_map, other.db_map_data(db_map))
        self._merge_children(other.children)

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

    def _create_new_children(self, db_map, children_data):
        """
        Creates new items for a db map given data..
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

    def _merge_children(self, new_children):
        """Merges source into target children by unique_identifier. Returns unmerged."""
        existing_children = {child.unique_identifier: child for child in self.children}
        unmerged = []
        for new_child in new_children:
            existing = existing_children.get(new_child.unique_identifier)
            if existing:
                # Found match, merge and get rid of src just in case
                existing.deep_merge(new_child)
                del new_child
            else:
                # No match
                unmerged.append(new_child)
        self.append_children(unmerged)

    def fetch_more(self):
        """Creates children by querying all databases.
        Merges the children across databases.
        Returns the list of newly created children.
        """
        all_children = list()
        for db_map in self.db_maps:
            children_data = self._get_children_data(db_map)
            new_children = self._create_new_children(db_map, children_data)
            self._merge_children(new_children)
        self._fetched = True

    def append_children_from_data(self, db_map, children_data):
        """
        Creates children from given data and merges them to the existing.
        Data is *not* checked for integrity (dups, etc.)
        Appends the list of unmerged children.

        Args:
            db_map (DiffDatabaseMapping)
            children_data (list): collection of dicts
        """
        new_children = self._create_new_children(db_map, children_data)
        self._merge_children(new_children)

    def update_children_with_data(self, db_map, children_data):
        """
        Updates children with given data. Note that this may cause two type of problems with the unique id:
        - the unique id of an individual item is no longer unique
        - two or more children have the same unique id
        Call fix_children after you're done updating all your db_maps to fix that situation.
        Returns updated rows so the model knows which children may need a fix.

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

    def fix_children(self, rows):
        """Fixes children thay may have problems with their unique id after calling update_children_with_data."""
        unique_ids = [child.unique_identifier for child in self.children if child.unique_identifier]
        new_children = []
        for row in reversed(sorted(rows)):
            child = self.child(row)
            if not child:
                continue
            # Deep take db maps until the unique id becomes unique
            while not child.unique_identifier:
                db_map = child.first_db_map
                new_child = child.deep_take_db_map(db_map)
                new_children.append(new_child)
            if child.unique_identifier in unique_ids[:row] + unique_ids[row + 1 :]:
                new_children.append(child)
                self.remove_children(row, 1)
        self._merge_children(new_children)

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
        return ObjectClassItem(db_map_data)


class RelationshipTreeRootItem(TreeRootItem):
    """A relationship tree root item."""

    context_menu_actions = {"Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg")}

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map."""
        return db_map.query(db_map.wide_relationship_class_sq)

    def _create_child_item(self, db_map_data):
        return RelationshipClassItem(db_map_data)


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
        return ObjectItem(db_map_data)

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
        return RelationshipItem(db_map_data)

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
        return RelationshipClassItem(db_map_data)

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
