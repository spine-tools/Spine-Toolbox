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
Models to represent entities in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
from PySide2.QtCore import Qt, Signal, QAbstractItemModel, QModelIndex
from PySide2.QtGui import QIcon
from .entity_tree_item import (
    TreeItem,
    ObjectTreeRootItem,
    ObjectClassItem,
    ObjectItem,
    RelationshipTreeRootItem,
    RelationshipClassItem,
    RelationshipItem,
)
from ..helpers import all_ids


class EntityTreeModel(QAbstractItemModel):
    """Base class for all entity tree models."""

    remove_selection_requested = Signal(name="remove_selection_requested")

    def __init__(self, parent, db_maps):
        """Init class.

        Args:
            parent (DataStoreForm)
            db_maps (dict): maps db names to DiffDatabaseMapping instances
        """
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
        self.endResetModel()
        self._root = self._create_root_item(self._db_map_data, parent=self._invisible_root)
        self._invisible_root.insert_children(0, [self._root])

    @property
    def root_item(self):
        return self._root

    @property
    def root_index(self):
        return self.createIndex(0, 0, self._root)

    def _create_root_item(self):
        raise NotImplementedError()

    def visit_all(self, index=QModelIndex()):
        """Iterates all items in the model including and below the given index.
        Iterative implementation to comply with Python recursion limits.
        """
        if index.isValid():
            ancient_one = self.item_from_index(index)
        else:
            ancient_one = self._invisible_root
        yield ancient_one
        child = ancient_one.last_child()
        if not child:
            return
        current = child
        visit_children = True
        while True:
            yield current
            if visit_children:
                child = current.last_child()
                if child:
                    current = child
                    continue
            sibling = current.previous_sibling()
            if sibling:
                visit_children = True
                current = sibling
                continue
            parent = current._parent
            if parent == ancient_one:
                break
            visit_children = False  # Make sure we don't visit children again
            current = parent

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
        item = self.item_from_index(index)
        parent_item = item.parent
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
        item = self.item_from_index(index)
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
        item = parent_item.child(row)
        if item:
            return self.createIndex(row, column, item)
        return QModelIndex()

    def columnCount(self, parent=QModelIndex()):
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
        self.insert_rows(0, items, parent)

    def removeRows(self, row, count, parent=QModelIndex()):
        parent_item = self.item_from_index(parent)
        self.beginRemoveRows(parent, row, row + count - 1)
        success = parent_item.remove_children(row, count)
        self.endRemoveRows()
        return success

    def insert_rows(self, row, items, parent=QModelIndex()):
        parent_item = self.item_from_index(parent)
        self.beginInsertRows(parent, row, row + len(items) - 1)
        success = parent_item.insert_children(position, items)
        self.endInsertRows()
        return success

    def append_rows(self, items, parent=QModelIndex()):
        return self.insert_rows(self.rowCount(parent), items, parent)

    def deselect_index(self, index):
        """Removes the index from the dict."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(self.item_from_index(index))
        self.selected_indexes[item_type].pop(index)

    def select_index(self, index):
        """Adds the index to the dict."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(self.item_from_index(index))
        self.selected_indexes.setdefault(item_type, {})[index] = None

    def cascade_filter_nodes(self, *conds, fetch=False, fetched_only=True):
        """Filter nodes in cascade by applying the given conditions as follows:
        Root --(first cond on children)--> First level nodes --(second cond on children)--> Second level nodes, etc.
        Returns the nodes at the lowest level attained.
        Optionally fetch the nodes as it goes.
        """
        parents = [self.root_item]
        for cond in conds:
            parents = [child for parent in parents for child in parent.find_children(cond)]
            if fetch:
                for parent in parents:
                    index = self.index_from_item(parent)
                    self.canFetchMore(index) and self.fetchMore(index)
        if fetched_only:
            return [parent for parent in parents if not self.canFetchMore(self.index_from_item(parent))]
        return parents

    def cascade_filter_nodes_by_id(self, db_map, *ids_set, fetch=False, fetched_only=True):
        """Filter nodes by ids in cascade as follows:
        Root --> First level nodes with ids in first set of ids --> Second level nodes with ids in second set of ids...
        """
        parents = [self.root_item]
        for ids in ids_set:
            parents = [child for parent in parents for child in parent.find_children_by_id(db_map, *ids)]
            if fetch:
                for parent in parents:
                    index = self.index_from_item(parent)
                    self.canFetchMore(index) and self.fetchMore(index)
        if fetched_only:
            return [parent for parent in parents if not self.canFetchMore(self.index_from_item(parent))]
        return parents

    def append_children(self, db_map, data, parent):
        """Convenience method to append children to an item and then
        the corresponding rows to the model."""
        new_items = parent.add_children_from_data(db_map, data)
        self.append_rows(new_items, self.index_from_item(parent))

    def remove_node(self, db_map, item):
        """Convenience method to remove a db_map from an item and then
        remove it from the model if empty."""
        if not item.has_one_db_map(db_map):
            item.pop_db_map(db_map)
            return None
        row = item.child_number()
        parent = self.parent(self.createIndex(0, 0, item))
        self.removeRow(row, parent)
        return row

    def append_split_children(self, rows, parent):
        """Convenience method to split children from an item and add
        the corresponding rows to the model."""
        new_items = parent.split_ambiguous(rows)
        self.append_rows(new_items, self.index_from_item(parent))


class ObjectTreeModel(EntityTreeModel):
    """An 'object-oriented' tree model."""

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

    def add_object_classes(self, db_map_data):
        selected_items = [self.item_from_index(ind) for ind in self.selected_object_class_indexes]
        for db_map, data in db_map_data.items():
            self.append_children(db_map, data, self.root_item)
        self.selected_indexes[ObjectClassItem] = {self.index_from_item(item): None for item in selected_items}

    def remove_object_classes(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_object_classes(db_map, removed_items)

    def _remove_db_map_object_classes(self, db_map, removed_items):
        removed_ids = {x['id'] for x in removed_items}
        for item in reversed(self.cascade_filter_nodes_by_id(db_map, removed_ids, fetched_only=False)):
            self.remove_node(db_map, item)

    def update_object_classes(self, db_map_data):
        updated_rows = set()
        for db_map, data in db_map_data.items():
            updated_rows.update(self.root_item.update_children_from_data(db_map, data))
        self.append_split_children(updated_rows, self.root_item)

    def add_objects(self, db_map_data):
        for db_map, new_items in db_map_data.items():
            self._add_db_map_objects(db_map, new_items)

    def _add_db_map_objects(self, db_map, new_items):
        d = dict()
        for item in new_items:
            d.setdefault(item["class_id"], []).append(item)
        for class_id, data in d.items():
            for parent in self.cascade_filter_nodes_by_id(db_map, (class_id,)):
                self.append_children(db_map, data, parent)

    def remove_objects(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_objects(db_map, removed_items)

    def _remove_db_map_objects(self, db_map, removed_items):
        d = dict()
        for item in removed_items:
            d.setdefault(item["class_id"], []).append(item['id'])
        for class_id, removed_ids in d.items():
            for item in reversed(self.cascade_filter_nodes_by_id(db_map, (class_id,), removed_ids, fetched_only=False)):
                self.remove_node(db_map, item)

    def add_relationship_classes(self, db_map_data):
        for db_map, new_items in db_map_data.items():
            self._add_db_map_relationship_classes(db_map, new_items)

    def _add_db_map_relationship_classes(self, db_map, new_items):
        d = dict()
        for item in new_items:
            for object_class_id in item["object_class_id_list"].split(","):
                d.setdefault(int(object_class_id), []).append(item)
        for object_class_id, data in d.items():
            for parent in self.cascade_filter_nodes_by_id(db_map, (object_class_id,), all_ids):
                self.append_children(db_map, data, parent)

    def remove_relationship_classes(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_relationship_classes(db_map, removed_items)

    def _remove_db_map_relationship_classes(self, db_map, removed_items):
        d = dict()
        for item in removed_items:
            for object_class_id in item["object_class_id_list"].split(","):
                d.setdefault(int(object_class_id), []).append(item['id'])
        for object_class_id, removed_ids in d.items():
            for item in reversed(
                self.cascade_filter_nodes_by_id(db_map, (object_class_id,), all_ids, removed_ids, fetched_only=False)
            ):
                self.remove_node(db_map, item)

    def add_relationships(self, db_map_data):
        for db_map, new_items in db_map_data.items():
            self._add_db_map_relationships(db_map, new_items)

    def _add_db_map_relationships(self, db_map, new_items):
        d = dict()
        for item in new_items:
            for object_id in item["object_id_list"].split(","):
                d.setdefault((item["class_id"], int(object_id)), []).append(item)
        for (class_id, object_id), data in d.items():
            for parent in self.cascade_filter_nodes_by_id(db_map, all_ids, (object_id,), (class_id,)):
                self.append_children(db_map, data, parent)

    def remove_relationships(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_relationships(db_map, removed_items)

    def _remove_db_map_relationships(self, db_map, removed_items):
        d = dict()
        for item in removed_items:
            for object_id in item["object_id_list"].split(","):
                d.setdefault((item["class_id"], int(object_id)), []).append(item['id'])
        for (class_id, object_id), removed_ids in d.items():
            for item in self.cascade_filter_nodes_by_id(
                db_map, all_ids, (object_id,), (class_id,), removed_ids, fetched_only=False
            ):
                self.remove_node(db_map, item)

    def find_next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        if not index.isValid():
            return
        rel_item = self.item_from_index(index)
        if not isinstance(rel_item, RelationshipItem):
            return
        # Get all ancestors
        rel_cls_item = rel_item._parent
        obj_item = rel_cls_item._parent
        obj_cls_item = obj_item._parent
        # Get data from ancestors
        # TODO: Is it enough to just use the first db_map?
        db_map = rel_item.first_db_map
        rel_data = rel_item.db_map_data(db_map)
        rel_cls_data = rel_cls_item.db_map_data(db_map)
        obj_data = obj_item.db_map_data(db_map)
        obj_cls_data = obj_cls_item.db_map_data(db_map)
        # Get specific data for our searches
        rel_cls_id = rel_cls_data['id']
        obj_id = obj_data['id']
        obj_cls_id = obj_cls_data['id']
        object_ids = list(reversed([int(id_) for id_ in rel_data['object_id_list'].split(",")]))
        object_class_ids = list(reversed([int(id_) for id_ in rel_cls_data['object_class_id_list'].split(",")]))
        # Find position in the relationship of the (grand parent) object,
        # then use it to determine object class and object id to look for
        pos = object_ids.index(obj_id) - 1
        object_id = object_ids[pos]
        object_class_id = object_class_ids[pos]
        # Return first node that passes all cascade fiters
        for parent in self.cascade_filter_nodes_by_id(
            db_map, (object_class_id,), (object_id,), (rel_cls_id,), fetch=True
        ):
            for item in parent.find_children(lambda child: child.unique_identifier == rel_item.unique_identifier):
                return self.index_from_item(item)
        return None


class RelationshipTreeModel(EntityTreeModel):
    """A relationship-oriented tree model."""

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

    def add_relationship_classes(self, db_map_data):
        for db_map, data in db_map_data.items():
            self.append_children(db_map, data, self.root_item)

    def remove_relationship_classes(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_relationship_classes(db_map, removed_items)

    def _remove_db_map_relationship_classes(self, db_map, removed_items):
        removed_ids = {x['id'] for x in removed_items}
        for item in reversed(self.cascade_filter_nodes_by_id(db_map, removed_ids, fetched_only=False)):
            self.remove_node(db_map, item)

    def add_relationships(self, db_map_data):
        for db_map, new_items in db_map_data.items():
            self.__add_db_map_relationships(db_map, new_items)

    def _add_db_map_relationships(self, db_map, new_items):
        d = dict()
        for item in new_items:
            d.setdefault(item["class_id"], []).append(item)
        for class_id, data in d.items():
            for parent in self.cascade_filter_nodes_by_id(db_map, (class_id,)):
                self.append_children(db_map, data, parent)

    def remove_relationships(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_relationships(db_map, removed_items)

    def _remove_db_map_relationships(self, db_map, removed_items):
        d = dict()
        for item in removed_items:
            d.setdefault(item["class_id"], []).append(item['id'])
        for class_id, removed_ids in d.items():
            for item in reversed(self.cascade_filter_nodes_by_id(db_map, (class_id,), removed_ids, fetched_only=False)):
                self.remove_node(db_map, item)

    def remove_object_classes(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_object_classes(db_map, removed_items)

    def _remove_db_map_object_classes(self, db_map, removed_items):
        removed_ids = {x['id'] for x in removed_items}
        for item in reversed(
            self.cascade_filter_nodes(
                lambda rel_cls: set(rel_cls.db_map_data_field(db_map, "parsed_object_class_id_list", [])).intersection(
                    removed_ids
                ),
                fetched_only=False,
            )
        ):
            self.remove_node(db_map, item)

    def remove_objects(self, db_map_data):
        for db_map, removed_items in db_map_data.items():
            self._remove_db_map_objects(db_map, removed_items)

    def _remove_db_map_objects(self, db_map, removed_items):
        d = dict()
        for item in removed_items:
            d.setdefault(item["class_id"], []).append(item['id'])
        for class_id, object_ids in d.items():
            for item in reversed(
                self.cascade_filter_nodes(
                    lambda rel_cls: set(
                        rel_cls.db_map_data_field(db_map, "parsed_object_class_id_list", [])
                    ).intersection((class_id,)),
                    lambda rel: set(rel.db_map_data_field(db_map, "parsed_object_id_list", [])).intersection(
                        object_ids
                    ),
                    fetched_only=False,
                )
            ):
                self.remove_node(db_map, item)
