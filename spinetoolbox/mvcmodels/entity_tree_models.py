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
Models for object and relationship classes.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
from PySide2.QtCore import Qt, Signal, QAbstractItemModel, QModelIndex
from sqlalchemy import or_
from spinedb_api import DiffDatabaseMapping
from PySide2.QtGui import QFont, QBrush, QIcon


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

    def child_count(self):
        """Returns the number of children."""
        return len(self._children)

    def child_number(self):
        """Returns the row of this item as a children, or 0 if it doesn't have a parent."""
        if self._parent is not None:
            return self._parent.children.index(self)
        return 0

    def find_children(self, cond=lambda child: True):
        """Returns children that meet condition expressed as a lambda function."""
        for child in self.children:
            if cond(child):
                yield child

    def find_child(self, cond=lambda child: True):
        """Returns first child that meet condition expressed as a lambda function."""
        return next(self.find_children(cond), None)

    def next_sibling(self):
        """Returns the next sibling or None if last or if doesn't have a parent."""
        if self._parent is None:
            return None
        return self._parent.child(self.child_number() + 1)

    def clear_children(self):
        """Clear all children, used when resetting the model."""
        self.children.clear()

    def column_count(self):
        """Returns 0."""
        return 0

    def insert_children(self, position, new_children):
        """Insert new children at given position. Returns a boolean depending on how it went.

        Args:
            position (int): insert new items here
            new_children (list): insert items from this list
        """
        if not all(isinstance(item, TreeItem) for item in new_children):
            raise TypeError("All rows in new_rows must be of type 'TreeItem'")
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

    def flags(self, column):
        """Enables the item and makes it selectable."""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, column, role=Qt.DisplayRole):
        """Returns data from this item for a QAbstractItemModel."""
        return None

    def set_data(self, column, value):
        """Sets data from this item in a QAbstractItemModel.
        Returns how it went."""
        return False

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

    def __init__(self, db_map_data, parent=None):
        """Init class.

        Args:
            db_map_data (dict): maps instances of DiffDatabaseMapping to the data of the item in that db

        """
        super().__init__(parent)
        self._db_map_data = db_map_data

    @property
    def unique_identifier(self):
        """"Returns a unique identifier for this item across all dbs.
        The base class implementation returns the name.
        """
        return self.db_map_data(self.first_db_map)["name"]

    @property
    def display_data(self):
        """"Returns a short unique identifier for display purposes."""
        return self.unique_identifier

    @property
    def first_db_map(self):
        """Returns the first db_map where this item belongs."""
        db_map = next(iter(self._db_map_data.keys()))
        return db_map

    @property
    def db_maps(self):
        """Returns a list of all db_maps where this item belongs."""
        return list(self._db_map_data.keys())

    def add_db_map_data(self, db_map: DiffDatabaseMapping, new_data: dict):
        """Adds a new mapping from db_map to id for this item."""
        self._db_map_data[db_map] = new_data

    def remove_db_map_data(self, db_map: DiffDatabaseMapping):
        """Removes the mapping from given db_map."""
        return self._db_map_data.pop(db_map, None)

    def db_map_data(self, db_map):
        """Returns the data of this item in given db_map or None if not found."""
        return self._db_map_data.get(db_map)

    def db_map_data_field(self, db_map, field):
        """Returns the data of this item for given filed in given db_map or None if not found."""
        return self._db_map_data.get(db_map, {}).get(field)

    def fetch_more(self):
        new_children = dict()
        for db_map, child_data in self._get_children_data():
            database = self.db_map_data(db_map)["database"]
            child_data["database"] = database
            new_item = self._create_child_item({db_map: child_data})
            unique_identifier = new_item.unique_identifier
            if unique_identifier not in new_children:
                new_children[unique_identifier] = new_item
            else:
                existing_item = new_children[unique_identifier]
                existing_item.add_db_map_data(db_map, child_data)
                del new_item
        self._fetched = True
        new_children = list(new_children.values())
        return new_children

    def _get_children_data(self):
        """Generates tuples of (db_map, child data) from all the dbs."""
        for db_map in self.db_maps:
            for child in self._children_query(db_map):
                yield (db_map, child._asdict())

    def _children_query(self, db_map):
        """Returns a query that selects all children from given db_map."""
        raise NotImplementedError()

    def _create_child_item(self, db_map_data):
        """Returns a child item fromg given db_map_data.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()

    def append_children_from_data(self, db_map, children_data):
        """

        Args:
            db_map (DiffDatabaseMapping)
            children_data (list): collection of dicts
        """
        existing_identifiers = [child.unique_identifier for child in self.children]
        added_rows = []
        updated_inds = []
        database = self.db_map_data(db_map)["database"]
        for child_data in children_data:
            child_data["database"] = database
            try:
                # Check in the existing identifiers if we have a collision
                new_item = self._create_child_item({db_map: child_data})
                ind = existing_identifiers.index(new_item.unique_identifier)
            except ValueError:
                # No collision, let's add the new item
                added_rows.append(new_item)
            else:
                # Collision, update current and get rid of the new one
                self.child(ind).add_db_map_data(db_map, child_data)
                updated_inds.append(ind)
                del new_item
        return added_rows, updated_inds

    def data(self, column, role):
        """Returns data from this item for a QAbstractItemModel."""
        if role == Qt.DisplayRole:
            return (self.display_data, ", ".join([self.db_map_data(db_map)["database"] for db_map in self.db_maps]))[
                column
            ]

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return {}


class TreeRootItem(MultiDBTreeItem):
    @property
    def unique_identifier(self):
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
            data = self.db_map_data(self.first_db_map)
            return data.get("description", "")
        if role == Qt.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        if role == Qt.ForegroundRole and column == 0:
            if not self.has_children():
                return QBrush(Qt.gray)
        return super().data(column, role)

    def flags(self, column):
        super_flags = super().flags(column)
        if column == 0:
            super_flags = super_flags | Qt.ItemIsEditable
        return super_flags

    def set_data(self, column, value):
        if column == 0:
            for db_map, data in self._db_map_data.items():
                updated_item = {"id": data["id"], "name": str(value)}
                db_map.update_object_classes(updated_item)
            return True
        return False


class ObjectClassItem(EntityClassItem):
    """An object class item."""

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
        return db_map.query(db_map.object_sq).filter_by(class_id=self.db_map_data(db_map)['id'])

    def _create_child_item(self, db_map_data):
        return ObjectItem(db_map_data, parent=self)

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DecorationRole and column == 0:
            data = self.db_map_data(self.first_db_map)
            # TODO return self._spinedb_manager.icon_manager.object_icon(data["name"])
        return super().data(column, role)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(object_class_name=data['name'], database=data['database'])


class RelationshipClassItem(EntityClassItem):

    context_menu_actions = {
        "Add relationships": QIcon(":/icons/menu_icons/cubes_plus.svg"),
        "": None,
        "Edit relationship classes": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    @property
    def unique_identifier(self):
        """"The name plus the object class names list."""
        data = self.db_map_data(self.first_db_map)
        return (data["name"], data["object_class_name_list"])

    @property
    def display_data(self):
        """"Returns a short unique identifier for display purposes."""
        data = self.db_map_data(self.first_db_map)
        return data["name"]

    def _children_query(self, db_map):
        """Returns a query to the given db map that returns children of this item."""
        sq = db_map.wide_relationship_sq
        qry = db_map.query(sq).filter_by(class_id=self.db_map_data(db_map)['id'])
        if isinstance(self.parent, ObjectItem):
            object_id = self.parent.db_map_data(db_map)['id']
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

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DecorationRole and column == 0:
            data = self.db_map_data(self.first_db_map)
            # TODO return self._spinedb_manager.icon_manager.relationship_icon(data["object_class_name_list"])
        return super().data(column, role)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        return dict(relationship_class_name=data['name'], database=data['database'])


class EntityItem(MultiDBTreeItem):
    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            data = self.db_map_data(self.first_db_map)
            return data.get("description", "")
        return super().data(column, role)

    def flags(self, column):
        roles = super().flags(column)
        if column == 0:
            roles = roles | Qt.ItemIsEditable
        return roles

    def set_data(self, column, value):
        if column == 0:
            for db_map, data in self._db_map_data.items():
                updated_item = {"id": data["id"], "name": str(value)}
                db_map.update_object_classes(updated_item)
            return True
        return False


class ObjectItem(EntityItem):
    context_menu_actions = {
        "Edit objects": QIcon(":/icons/menu_icons/cube_pen.svg"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cube_minus.svg"),
    }

    def _children_query(self, db_map):
        """Returns a query to the given db map that returns children of this item."""
        object_class_id = self.parent.db_map_data(db_map)['id']
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

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DecorationRole and column == 0:
            data = self.parent.db_map_data(self.first_db_map)
            # TODO return self._spinedb_manager.icon_manager.object_icon(data["name"])
        return super().data(column, role)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        parent_data = self._parent.db_map_data(self.first_db_map)
        return dict(object_class_name=parent_data['name'], object_name=data['name'], database=data['database'])


class RelationshipItem(EntityItem):
    context_menu_actions = {
        "Edit relationships": QIcon(":/icons/menu_icons/cubes_pen.svg"),
        "": None,
        "Find next": QIcon(":/icons/menu_icons/ellipsis-h.png"),
        "": None,
        "Remove selection": QIcon(":/icons/menu_icons/cubes_minus.svg"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fetched = True

    @property
    def unique_identifier(self):
        data = self.db_map_data(self.first_db_map)
        return (data["name"], data["object_name_list"])

    @property
    def display_data(self):
        """"Returns a short unique identifier for display purposes."""
        data = self.db_map_data(self.first_db_map)
        return data["object_name_list"]

    def has_children(self):
        return False

    def append_children_from_data(self, db_map, children_data):
        pass

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        data = self.db_map_data(self.first_db_map)
        parent_data = self._parent.db_map_data(self.first_db_map)
        return dict(
            relationship_class_name=parent_data['name'],
            object_name_list=data['object_name_list'],
            database=data['database'],
        )


class EntityTreeModel(QAbstractItemModel):

    remove_selection_requested = Signal(name="remove_selection_requested")

    def __init__(self, parent, db_maps):
        super().__init__(parent)
        self._parent = parent
        self.db_maps = db_maps
        self._invisible_root = TreeItem()
        self._root = None
        self._db_map_data = {db_map: {"database": database} for database, db_map in db_maps.items()}
        self.selected_indexes = dict()  # Maps item type to selected indexes

    def build_tree(self):
        self.beginResetModel()
        self._invisible_root.clear_children()
        self._root = self._create_root_item(self._db_map_data, parent=self._invisible_root)
        self._invisible_root.insert_children(0, [self._root])
        self.endResetModel()

    @property
    def root_item(self):
        return self._root

    @property
    def root_index(self):
        return self.createIndex(0, 0, self._root)

    def _create_root_item(self):
        raise NotImplementedError()

    def visit_all(self, index=QModelIndex()):
        """Iterates all items in the model including and below the given index."""
        if index.isValid():
            ancient_one = index.internalPointer()
        else:
            ancient_one = self._invisible_root
        yield ancient_one
        child = ancient_one.child(0)
        if not child:
            return
        current = child
        back_to_parent = False
        while True:
            yield current
            if not back_to_parent:
                child = current.child(0)
                if child:
                    current = child
                    continue
            sibling = current.next_sibling()
            if sibling:
                back_to_parent = False
                current = sibling
                continue
            parent = current._parent
            if parent != ancient_one:
                back_to_parent = True
                current = parent
                continue
            break

    def visit_all_recursive(self, index=QModelIndex()):
        """Yields the current index and all its descendants."""
        # NOTE: Kept because it's nice, but not used for fear of recursion limits
        if index.isValid():
            item = index.internalPointer()
        else:
            item = self._invisible_root
        for child in reversed(item.children):
            if child.child_count() > 0:
                yield from self.visit_all_recursive(self.createIndex(0, 0, child))
            else:
                yield child
        yield item

    def remove_node(self, db_map, remove_ids, instance_of):
        for tree_item in self.visit_all():
            if not isinstance(tree_item, instance_of):
                continue
            if db_map in tree_item.db_maps and tree_item.db_map_data(db_map)['id'] in remove_ids:
                _ = tree_item.remove_db_map_data(db_map)
                if not tree_item.db_maps:
                    row = tree_item.child_number()
                    parent = self.parent(self.createIndex(0, 0, tree_item))
                    self.removeRow(row, parent)

    def append_to_node(self, db_map, data, parent_type, condition=lambda item: True):
        for tree_item in self.visit_all():
            if not isinstance(tree_item, parent_type) or not condition(tree_item):
                continue
            tree_index = self.index_from_item(tree_item)
            if self.canFetchMore(tree_index):
                continue
            added_items, _ = tree_item.append_children_from_data(db_map, data)
            self.appendRows(added_items, tree_index)

    def append_entities_to_class_node(self, db_map, new_items, parent_type):
        d = dict()
        for item in new_items:
            item = item._asdict()
            d.setdefault(item["class_id"], []).append(item)
        for class_id, data in d.items():
            self.append_to_node(
                db_map, data, parent_type, condition=lambda item: item.db_map_data_field(db_map, "id") == class_id
            )

    def remove_entity_class(self, db_map, entity_class_ids):
        self.remove_node(db_map, entity_class_ids, EntityClassItem)

    def remove_entity(self, db_map, entity_ids):
        self.remove_node(db_map, entity_ids, EntityItem)

    def item_from_index(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self._invisible_root

    def index_from_item(self, item):
        """Return a model index corresponding to the given item."""
        # TODO: this works, right?
        return self.createIndex(item.child_number(), 0, item)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = self.item_from_index(index)
        parent_item = child_item.parent

        if parent_item == self._invisible_root:
            return QModelIndex()

        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def column_count(self, parent):
        return 2

    def data(self, index, role):
        item = self.item_from_index(index)
        return item.data(index.column(), role)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        item = index.internalPointer()
        if role == Qt.EditRole:
            return item.set_data(index.column(), value)
        return False

    def flags(self, index):
        item = self.item_from_index(index)
        roles = item.flags(index.column())
        return roles

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "database")[section]
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self.item_from_index(parent)
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def columnCount(self, parent=QModelIndex()):
        """"""
        return 2

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        parent_item = self.item_from_index(parent)
        return parent_item.child_count()

    def hasChildren(self, parent):
        """Return True if not fetched, so the user can try and expand it."""
        parent_item = self.item_from_index(parent)
        return parent_item.has_children()

    def canFetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.can_fetch_more()

    def fetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        items = parent_item.fetch_more()
        self.insertRows(0, items, parent)

    def removeRows(self, position, rows, parent=QModelIndex()):
        parent_item = self.item_from_index(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parent_item.remove_children(position, rows)
        self.endRemoveRows()
        return success

    def insertRows(self, position, rows, parent=QModelIndex()):
        parent_item = self.item_from_index(parent)
        self.beginInsertRows(parent, position, position + len(rows) - 1)
        success = parent_item.insert_children(position, rows)
        self.endInsertRows()
        return success

    def appendRows(self, rows, parent=QModelIndex()):
        position = parent.internalPointer().child_count()
        return self.insertRows(position, rows, parent)

    def deselect_index(self, index):
        """Removes the index from the dict."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(index.internalPointer())
        self.selected_indexes[item_type].pop(index)

    def select_index(self, index):
        """Adds the index to the dict."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(index.internalPointer())
        self.selected_indexes.setdefault(item_type, {})[index] = None

    def find_item(self, cond, index=QModelIndex()):
        """Find the first item that satisfies given condition."""
        for visited in self.visit_all(index):
            if cond(visited):
                return visited
        return None


class ObjectTreeModel(EntityTreeModel):
    remove_icon = QIcon(":/icons/menu_icons/cube_minus.svg")

    @staticmethod
    def _create_root_item(db_map_data, parent):
        return ObjectTreeRootItem(db_map_data, parent=parent)

    @property
    def selected_object_class_indexes(self):
        return self.selected_indexes.get(ObjectClassItem, {})

    @property
    def selected_object_indexes(self):
        return self.selected_indexes.get(ObjectItem, {})

    @property
    def selected_relationship_class_indexes(self):
        return self.selected_indexes.get(RelationshipClassItem, {})

    @property
    def selected_relationship_indexes(self):
        return self.selected_indexes.get(RelationshipItem, {})

    def add_object_classes(self, db_map, new_items):
        data = [x._asdict() for x in new_items]
        self.append_to_node(db_map, data, ObjectTreeRootItem)

    def add_objects(self, db_map, new_items):
        self.append_entities_to_class_node(db_map, new_items, ObjectClassItem)

    def add_relationship_classes(self, db_map, new_items):
        d = dict()
        for item in new_items:
            item = item._asdict()
            for id_ in item["object_class_id_list"].split(","):
                d.setdefault(int(id_), []).append(item)
        for object_class_id, data in d.items():
            self.append_to_node(
                db_map,
                data,
                ObjectItem,
                condition=lambda item: item.db_map_data_field(db_map, "class_id") == object_class_id,
            )

    def add_relationships(self, db_map, new_items):
        d = dict()
        for item in new_items:
            item = item._asdict()
            for id_ in item["object_id_list"].split(","):
                d.setdefault((item["class_id"], int(id_)), []).append(item)
        for (class_id, object_id), data in d.items():
            self.append_to_node(
                db_map,
                data,
                RelationshipClassItem,
                condition=lambda item: item.db_map_data_field(db_map, "id") == class_id
                and item._parent.db_map_data_field(db_map, "id") == object_id,
            )

    def find_next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        # Mildly insane, but gets the job done and I can't think of anything better right now
        # Still it just searches in the first db map only...
        if not index.isValid():
            return
        rel_item = index.internalPointer()
        if not isinstance(rel_item, RelationshipItem):
            return
        # Get all ancestors
        rel_cls_item = rel_item._parent
        obj_item = rel_cls_item._parent
        obj_cls_item = obj_item._parent
        # Get data from ancestors
        db_map = rel_item.first_db_map
        rel_data = rel_item.db_map_data(db_map)
        rel_cls_data = rel_cls_item.db_map_data(db_map)
        obj_data = obj_item.db_map_data(db_map)
        obj_cls_data = obj_cls_item.db_map_data(db_map)
        # Get specific data for our searches
        rel_cls_id = rel_cls_data['id']
        obj_id = obj_data['id']
        obj_cls_id = obj_cls_data['id']
        object_ids = [int(id_) for id_ in rel_data['object_id_list'].split(",")]
        object_class_ids = [int(id_) for id_ in rel_cls_data['object_class_id_list'].split(",")]
        # Find position in the relationship of the (grand parent) object
        # then use it to determine object class and object id to look for
        pos = object_ids.index(obj_id) + 1
        if pos == len(object_ids):
            pos = 0
        object_id = object_ids[pos]
        object_class_id = object_class_ids[pos]
        # Find, fetch, and find again until done
        # Find object class
        found_obj_cls_item = self.root_item.find_child(
            lambda child: child.db_map_data_field(db_map, "id") == object_class_id
        )
        if not found_obj_cls_item:
            return None
        found_obj_cls_ind = self.index_from_item(found_obj_cls_item)
        self.canFetchMore(found_obj_cls_ind) and self.fetchMore(found_obj_cls_ind)
        # Find object
        found_obj_item = found_obj_cls_item.find_child(lambda child: child.db_map_data_field(db_map, "id") == object_id)
        if not found_obj_item:
            return None
        found_obj_ind = self.index_from_item(found_obj_item)
        self.canFetchMore(found_obj_ind) and self.fetchMore(found_obj_ind)
        # Find relationship class
        found_rel_cls_item = found_obj_item.find_child(
            lambda child: child.db_map_data_field(db_map, "id") == rel_cls_id
        )
        if not found_rel_cls_item:
            return None
        found_rel_cls_ind = self.index_from_item(found_rel_cls_item)
        self.canFetchMore(found_rel_cls_ind) and self.fetchMore(found_rel_cls_ind)
        # Find relationship
        found_rel_item = found_rel_cls_item.find_child(
            lambda child: child.unique_identifier == rel_item.unique_identifier
        )
        if not found_rel_item:
            return None
        return self.index_from_item(found_rel_item)


class RelationshipTreeModel(EntityTreeModel):
    remove_icon = QIcon(":/icons/menu_icons/cubes_minus.svg")

    @staticmethod
    def _create_root_item(db_map_data, parent):
        return RelationshipTreeRootItem(db_map_data, parent=parent)

    @property
    def selected_relationship_class_indexes(self):
        return self.selected_indexes.get(RelationshipClassItem, {})

    @property
    def selected_relationship_indexes(self):
        return self.selected_indexes.get(RelationshipItem, {})

    def add_relationship_classes(self, db_map, new_items):
        data = [x._asdict() for x in new_items]
        self.append_to_node(db_map, data, RelationshipTreeRootItem)

    def add_relationships(self, db_map, new_items):
        self.append_entities_to_class_node(db_map, new_items, RelationshipClassItem)
