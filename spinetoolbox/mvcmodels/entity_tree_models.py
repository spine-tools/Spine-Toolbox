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
from PySide2.QtCore import Qt, Signal, Slot, QAbstractItemModel, QModelIndex
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
from .minimal_tree_model import MinimalTreeModel


class EntityTreeModel(MinimalTreeModel):
    """Base class for all entity tree models."""

    remove_selection_requested = Signal(name="remove_selection_requested")

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm)
            db_mngr (SpineDBManager): A manager for the given db_maps
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._root_item = None
        self.selected_indexes = dict()  # Maps item type to selected indexes
        self._selection_buffer = list()  # To restablish selected indexes after adding/removing rows
        self.connect_db_mngr_signals()

    def connect_db_mngr_signals(self):
        """Connect signals to slots."""

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item.deleteLater()
        self._invisible_root_item = TreeItem()
        self.endResetModel()
        self.selected_indexes.clear()
        self.track_item(self._invisible_root_item)
        self._root_item = self.root_item_type(self.db_mngr, dict.fromkeys(self.db_maps))
        self._root_item.index = self.createIndex(0, 0, self._root_item)
        self._invisible_root_item.insert_children(0, self._root_item)

    def _fill_selection_buffer(self, index, last):
        """Pops indexes out of selection dictionary and add items into buffer."""
        item = self.item_from_index(index)
        selected = self.selected_indexes.get(item.child_item_type)
        if not selected:
            return
        self._selection_buffer.clear()
        for child in item.children[last:]:
            if selected.pop(self.index_from_item(child), None) is not None:
                self._selection_buffer.append(child)

    def _empty_selection_buffer(self):
        """Selects all indexes corresponding to items in the selection buffer."""
        for item in self._selection_buffer:
            self.select_index(self.index_from_item(item))
        self._selection_buffer.clear()

    @Slot("QModelIndex", "int", "int", name="receive_children_about_to_be_inserted")
    def receive_children_about_to_be_inserted(self, index, row, count):
        """Begin an operation to insert rows."""
        super().receive_children_about_to_be_inserted(index, row, count)
        self._fill_selection_buffer(index, row + count)

    @Slot(name="receive_children_inserted")
    def receive_children_inserted(self):
        """End an operation to insert rows."""
        super().receive_children_inserted()
        self._empty_selection_buffer()

    @Slot("QModelIndex", "int", "int", name="receive_children_about_to_be_removed")
    def receive_children_about_to_be_removed(self, index, row, count):
        """Begin an operation to remove rows."""
        super().receive_children_about_to_be_removed(index, row, count)
        self._fill_selection_buffer(index, row + count)

    @Slot(name="receive_children_removed")
    def receive_children_removed(self):
        """End an operation to remove rows. Stop tracking all removed items."""
        super().receive_children_removed()
        self._empty_selection_buffer()

    @property
    def root_item(self):
        return self._root_item

    @property
    def root_index(self):
        return self.index_from_item(self._root_item)

    @property
    def root_item_type(self):
        """Implement in subclasses to create a model specific to any entity type."""
        raise NotImplementedError()

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        item = self.item_from_index(index)
        if index.column() == 0:
            if role == Qt.DecorationRole:
                return item.display_icon
            if role == Qt.DisplayRole:
                return item.display_name
        return item.data(index.column(), role)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "database")[section]
        return None

    def hasChildren(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.has_children()

    def canFetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        return parent_item.can_fetch_more()

    def fetchMore(self, parent):
        parent_item = self.item_from_index(parent)
        parent_item.fetch_more()

    def deselect_index(self, index):
        """Marks the index as deselected."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(self.item_from_index(index))
        self.selected_indexes[item_type].pop(index)

    def select_index(self, index):
        """Marks the index as selected."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(self.item_from_index(index))
        self.selected_indexes.setdefault(item_type, {})[index] = None

    def cascade_filter_nodes_by_id(self, db_map, *ids_set, parents=(), fetch=False, return_unfetched=False):
        """Filter nodes by ids in cascade starting from the list of parents.
        Returns the nodes at the lowest level attained.
        Optionally fetches the nodes as it goes.
        """
        if not parents:
            parents = [self.root_item]
        for ids in ids_set:
            parents = [child for parent in parents for child in parent.find_children_by_id(db_map, *ids)]
            if fetch:
                for parent in parents:
                    index = self.index_from_item(parent)
                    self.canFetchMore(index) and self.fetchMore(index)
        if not return_unfetched:
            return [parent for parent in parents if not self.canFetchMore(self.index_from_item(parent))]
        return parents


class ObjectTreeModel(EntityTreeModel):
    """An 'object-oriented' tree model."""

    remove_icon = QIcon(":/icons/menu_icons/cube_minus.svg")

    def connect_db_mngr_signals(self):
        self.db_mngr.object_classes_added.connect(self.add_object_classes)
        self.db_mngr.objects_added.connect(self.add_objects)
        self.db_mngr.relationship_classes_added.connect(self.add_relationship_classes)
        self.db_mngr.relationships_added.connect(self.add_relationships)
        self.db_mngr.object_classes_removed.connect(self.remove_object_classes)
        self.db_mngr.objects_removed.connect(self.remove_objects)
        self.db_mngr.relationship_classes_removed.connect(self.remove_relationship_classes)
        self.db_mngr.relationships_removed.connect(self.remove_relationships)
        self.db_mngr.object_classes_updated.connect(self.update_object_classes)
        self.db_mngr.objects_updated.connect(self.update_objects)
        self.db_mngr.relationship_classes_updated.connect(self.update_relationship_classes)
        self.db_mngr.relationships_updated.connect(self.update_relationships)

    @property
    def root_item_type(self):
        return ObjectTreeRootItem

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

    def _group_object_data(self, db_map_data):
        """Takes given object data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            result (dict): maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            # Group items by class id
            d = dict()
            for item in items:
                d.setdefault(item["class_id"], set()).add(item["id"])
            for class_id, ids in d.items():
                # Find the parents corresponding the this class id and put them in the result
                for parent in self.cascade_filter_nodes_by_id(db_map, (class_id,)):
                    result.setdefault(parent, {})[db_map] = ids
        return result

    def _group_relationship_class_data(self, db_map_data):
        """Takes given relationship class data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            result (dict): maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                for object_class_id in item["object_class_id_list"].split(","):
                    d.setdefault(int(object_class_id), set()).add(item["id"])
            for object_class_id, ids in d.items():
                for parent in self.cascade_filter_nodes_by_id(db_map, (object_class_id,), (True,)):
                    result.setdefault(parent, {})[db_map] = ids
        return result

    def _group_relationship_data(self, db_map_data):
        """Takes given relationship data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            result (dict): maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                for object_id in item["object_id_list"].split(","):
                    key = (int(object_id), item["class_id"])
                    d.setdefault(key, set()).add(item["id"])
            for (object_id, class_id), ids in d.items():
                for parent in self.cascade_filter_nodes_by_id(db_map, (True,), (object_id,), (class_id,)):
                    result.setdefault(parent, {})[db_map] = ids
        return result

    def add_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_objects(self, db_map_data):
        for parent, db_map_ids in self._group_object_data(db_map_data).items():
            parent.append_children_by_id(db_map_ids)

    def add_relationship_classes(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.append_children_by_id(db_map_ids)

    def remove_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_objects(self, db_map_data):
        for parent, db_map_ids in self._group_object_data(db_map_data).items():
            parent.remove_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.remove_children_by_id(db_map_ids)

    def update_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_objects(self, db_map_data):
        for parent, db_map_ids in self._group_object_data(db_map_data).items():
            parent.update_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.update_children_by_id(db_map_ids)

    def find_next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        # Mildly insane? But I can't think of something better now
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
            for item in parent.find_children(lambda child: child.display_id == rel_item.display_id):
                return self.index_from_item(item)
        return None


class RelationshipTreeModel(EntityTreeModel):
    """A relationship-oriented tree model."""

    remove_icon = QIcon(":/icons/menu_icons/cubes_minus.svg")

    def connect_db_mngr_signals(self):
        self.db_mngr.relationship_classes_added.connect(self.add_relationship_classes)
        self.db_mngr.relationships_added.connect(self.add_relationships)
        self.db_mngr.relationship_classes_removed.connect(self.remove_relationship_classes)
        self.db_mngr.relationships_removed.connect(self.remove_relationships)
        self.db_mngr.relationship_classes_updated.connect(self.update_relationship_classes)
        self.db_mngr.relationships_updated.connect(self.update_relationships)

    @property
    def root_item_type(self):
        return RelationshipTreeRootItem

    @property
    def selected_relationship_class_indexes(self):
        return self.selected_indexes.get(RelationshipClassItem, {})

    @property
    def selected_relationship_indexes(self):
        return self.selected_indexes.get(RelationshipItem, {})

    def _group_relationship_data(self, db_map_data):
        """Takes given relationship data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            result (dict): maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                d.setdefault(item["class_id"], set()).add(item["id"])
            for class_id, ids in d.items():
                for parent in self.cascade_filter_nodes_by_id(db_map, (class_id,)):
                    result.setdefault(parent, {})[db_map] = ids
        return result

    def add_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.append_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.remove_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent.update_children_by_id(db_map_ids)
