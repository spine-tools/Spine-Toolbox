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

    def __init__(self, db_map_data, parent=None):
        """Init class.

        Args:
            db_map_data (dict): maps instances of DiffDatabaseMapping to the data for the item in that db

        """
        super().__init__(parent)
        self._db_map_data = db_map_data
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
                id_ = child.db_map_data_field(db_map, "id")
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
        """"Returns the display id of this item or None if non unique across all dbs."""
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
        return ",".join([self.db_map_data_field(db_map, "database") for db_map in self.db_maps])

    @property
    def first_db_map(self):
        """Returns the first associated db_map."""
        return list(self._db_map_data.keys())[0]

    @property
    def last_db_map(self):
        """Returns the last associated db_map."""
        return list(self._db_map_data.keys())[-1]

    @property
    def db_maps(self):
        """Returns a list of all associated db_maps."""
        return list(self._db_map_data.keys())

    def add_db_map_data(self, db_map, new_data):
        """Adds new data for this item in the given db_map."""
        self._db_map_data[db_map] = new_data

    def take_db_map(self, db_map):
        """Removes the mapping for given db_map and returns it."""
        db_map = self._db_map_data.pop(db_map, None)
        if not self._db_map_data:
            self.parent.remove_children(self.child_number(), 1)
        self._child_map.pop(db_map, None)
        return db_map

    def deep_remove_db_map(self, db_map):
        """Removes given db_map from this item and all its descendants."""
        for child in reversed(self.children):
            child.deep_remove_db_map(db_map)
        _ = self.take_db_map(db_map)

    def deep_take_db_map(self, db_map):
        """Takes given db_map from this item and all its descendants.
        Returns a new item from taken data or None if db_map is not present in the first place.
        """
        db_map_data = self.take_db_map(db_map)
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
        """Merges another item and all its descendants into this one."""
        if not isinstance(other, type(self)):
            raise ValueError(f"Can't merge an instance of {type(other)} into a MultiDBTreeItem.")
        for db_map in other.db_maps:
            self.add_db_map_data(db_map, other.db_map_data(db_map))
        self._merge_children(other.children)

    def db_map_data(self, db_map):
        """Returns data for this item in given db_map or None if not present."""
        return self._db_map_data.get(db_map)

    def db_map_data_field(self, db_map, field, default=None):
        """Returns field from data for this item in given db_map or None if not found."""
        return self._db_map_data.get(db_map, {}).get(field, default)

    def set_db_map_data_field(self, db_map, field, value):
        """Sets field in data for this item in given db_map."""
        db_map_data = self.db_map_data(db_map)
        if db_map_data:
            db_map_data[field] = value

    def _get_children_data(self, db_map):
        """Generates children data for the given db_map.
        Runs _children_query.
        """
        for child in self._children_query(db_map):
            yield child._asdict()

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def _create_child_item(self, db_map_data):
        """Returns a child item for given db_map data.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def _create_new_children(self, db_map, children_data):
        """
        Creates new items from data associated to a db map.
        Data is *not* checked for integrity (dups, etc.).

        Args:
            db_map (DiffDatabaseMapping): create children for this db_map
            children_data (iter): create childs from these dictionaries
        """
        new_children = []
        database = self.db_map_data_field(db_map, "database")
        for child_data in children_data:
            child_data["database"] = database
            new_children.append(self._create_child_item({db_map: child_data}))
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
        db_map_data = {db_map: self._get_children_data(db_map) for db_map in self.db_maps}
        self.append_children_from_data(db_map_data)
        self._fetched = True

    def append_children_from_data(self, db_map_data):
        """
        Appends children from data. Data is *not* checked for integrity (dups, etc.)

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of dict-items
        """
        new_children = []
        for db_map, data in db_map_data.items():
            new_children += self._create_new_children(db_map, data)
        self._merge_children(new_children)

    def remove_children_by_data(self, db_map_data):
        """
        Removes children by data.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict
        """
        for db_map, data in db_map_data.items():
            ids = {x["id"] for x in data}
            for child in self.find_children_by_id(db_map, *ids, reverse=True):
                child.deep_remove_db_map(db_map)

    def update_children_with_data(self, db_map_data):
        """
        Updates children with data. Data is *not* checked for integrity (dups, etc.)

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of dict-items
        """
        updated_rows = []
        for db_map, data in db_map_data.items():
            updated_rows += self._update_db_map_children_with_data(db_map, data)
        updated_rows = set(updated_rows)
        self._fix_children(updated_rows)

    def _update_db_map_children_with_data(self, db_map, children_data):
        """
        Updates children from given db_map using data without checking anything. Returns updated rows.
        Note that after this, there may be two type of problems concerning display ids.
        - the display id of an individual child is no longer consistent across db_maps
        - two or more children now have the same display id
        _fix_children must be called with the returned rows to fix these problems.

        Args:
            db_map (DiffDatabaseMapping)
            children_data (list): list of dict-items
        """
        updated_rows = []
        database = self.db_map_data_field(db_map, "database")
        for child_data in children_data:
            child_data["database"] = database
            row = self._child_map.get(db_map, {}).get(child_data["id"])
            if row is None:
                continue
            child = self._children[row]
            child.add_db_map_data(db_map, child_data)
            updated_rows.append(row)
        return updated_rows

    def _fix_children(self, rows):
        """Fixes children thay may have problems with their display id after calls to
        _update_db_map_children_with_data."""
        display_ids = [child.display_id for child in self.children if child.display_id]
        new_children = []
        for row in sorted(rows, reverse=True):
            child = self.child(row)
            if not child:
                continue
            # Solve first problem: Deep take db maps until the display id becomes consistent
            while not child.display_id:
                db_map = child.first_db_map
                new_child = child.deep_take_db_map(db_map)
                new_children.append(new_child)
            # Solve second problem: take the child and put it in the list to be inserted again
            if child.display_id in display_ids[:row] + display_ids[row + 1 :]:
                new_children.append(child)
                self.remove_children(row, 1)
        self._merge_children(new_children)

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.DisplayRole:
            return (self.display_name, self.display_database)[column]

    def display_icon(self, icon_manager):
        """Returns an icon to display next to the name.
        Reimplement in subclasses to return something nice."""
        return None

    def default_parameter_data(self):
        """Returns data to set as default in a parameter table when this item is selected."""
        return {"database": self.db_map_data_field(self.first_db_map, "database")}


class TreeRootItem(MultiDBTreeItem):
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

    def _children_query(self, db_map):
        """Returns a query that selects all object classes from given db_map."""
        return db_map.query(db_map.object_class_sq)

    def _create_child_item(self, db_map_data):
        """Returns an ObjectClassItem."""
        return ObjectClassItem(db_map_data)


class RelationshipTreeRootItem(TreeRootItem):
    """A relationship tree root item."""

    context_menu_actions = {"Add relationship classes": QIcon(":/icons/menu_icons/cubes_plus.svg")}

    def _children_query(self, db_map):
        """Returns a query that selects all relationship classes from given db_map."""
        return db_map.query(db_map.wide_relationship_class_sq)

    def _create_child_item(self, db_map_data):
        """Returns a RelationshipClassItem."""
        return RelationshipClassItem(db_map_data)


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
        """Returns a query that selects all objects of this class from given db_map."""
        return db_map.query(db_map.object_sq).filter_by(class_id=self.db_map_data_field(db_map, 'id'))

    def _create_child_item(self, db_map_data):
        """Returns an ObjectItem."""
        return ObjectItem(db_map_data)

    def display_icon(self, icon_manager):
        """Returns the object class icon."""
        name = self.db_map_data_field(self.first_db_map, "name")
        return icon_manager.object_icon(name)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(object_class_name=data['name'], database=data['database'])


class RelationshipClassItem(EntityClassItem):
    """A relationship class item."""

    visual_key = ["name", "object_class_name_list"]
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
                self.set_db_map_data_field(db_map, "parsed_object_class_id_list", parsed_object_class_id_list)
            object_class_name_list = self.db_map_data_field(db_map, "object_class_name_list")
            if object_class_name_list:
                parsed_object_class_name_list = object_class_name_list.split(",")
                self.set_db_map_data_field(db_map, "parsed_object_class_name_list", parsed_object_class_name_list)

    def display_icon(self, icon_manager):
        """Returns relationship class icon."""
        object_class_name_list = self.db_map_data_field(self.first_db_map, "object_class_name_list")
        return icon_manager.relationship_icon(object_class_name_list)

    def _children_query(self, db_map):
        """Returns a query that selects all relationships of this class from the db.
        If the parent is an ObjectItem, then only selects relationships involving that object.
        """
        sq = db_map.wide_relationship_sq
        qry = db_map.query(sq).filter_by(class_id=self.db_map_data_field(db_map, 'id'))
        if isinstance(self.parent, ObjectItem):
            object_id = self.parent.db_map_data_field(db_map, 'id')
            ids = {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
            qry = qry.filter(sq.c.id.in_(ids))
        return qry

    def _create_child_item(self, db_map_data):
        """Returns a RelationshipItem."""
        return RelationshipItem(db_map_data)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(relationship_class_name=data['name'], database=data['database'])


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
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
        """Returns a query that selects all relationship classes involving the parent class
        from the given db_map.
        """
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        sq = db_map.relationship_class_sq
        ids = {x.id for x in db_map.query(sq).filter_by(object_class_id=object_class_id)}
        sq = db_map.wide_relationship_class_sq
        return db_map.query(sq).filter(sq.c.id.in_(ids))

    def _create_child_item(self, db_map_data):
        """Returns a RelationshipClassItem."""
        return RelationshipClassItem(db_map_data)

    def display_icon(self, icon_manager):
        """Returns the object class icon."""
        name = self.parent.db_map_data_field(self.first_db_map, "name")
        return icon_manager.object_icon(name)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        parent_data = self.parent.db_map_data(self.first_db_map)
        return dict(object_class_name=parent_data['name'], object_name=data['name'], database=data['database'])


class RelationshipItem(EntityItem):
    """An object item."""

    visual_key = ["name", "object_name_list"]

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
        Also make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True
        for db_map in self.db_maps:
            object_id_list = self.db_map_data_field(db_map, "object_id_list")
            if object_id_list:
                parsed_object_id_list = [int(id_) for id_ in object_id_list.split(",")]
                self.set_db_map_data_field(db_map, "parsed_object_id_list", parsed_object_id_list)
            object_name_list = self.db_map_data_field(db_map, "object_name_list")
            if object_name_list:
                parsed_object_name_list = object_name_list.split(",")
                self.set_db_map_data_field(db_map, "parsed_object_name_list", parsed_object_name_list)

    @property
    def display_name(self):
        """"Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "object_name_list")

    def display_icon(self, icon_manager):
        """Returns relationship class icon."""
        object_class_name_list = self.parent.db_map_data_field(self.first_db_map, "object_class_name_list")
        return icon_manager.relationship_icon(object_class_name_list)

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def new_children_from_data(self, db_map, children_data):
        """Pass, this item never has children."""
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
