######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from .entity_tree_item import ObjectTreeRootItem, RelationshipTreeRootItem
from .multi_db_tree_model import MultiDBTreeModel


class ObjectTreeModel(MultiDBTreeModel):
    """An 'object-oriented' tree model."""

    @property
    def root_item_type(self):
        return ObjectTreeRootItem

    def _parent_object_data(self, db_map_data):
        """Takes given object data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            # Group items by class id
            d = dict()
            for item in items:
                d.setdefault(item["class_id"], dict())[item["id"]] = None
            for class_id, ids in d.items():
                # Find the parents corresponding to this class id and put them in the result
                for parent_item in self.find_items(db_map, (class_id,)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def _parent_relationship_class_data(self, db_map_data):
        """Takes given relationship_class data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                for object_class_id in item["object_class_id_list"].split(","):
                    d.setdefault(int(object_class_id), dict())[item["id"]] = None
            for object_class_id, ids in d.items():
                for parent_item in self.find_items(db_map, (object_class_id, None)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def _parent_relationship_data(self, db_map_data):
        """Takes given relationship data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                object_class_id_list = tuple(int(obj_id) for obj_id in item["object_class_id_list"].split(","))
                object_id_list = tuple(int(obj_id) for obj_id in item["object_id_list"].split(","))
                key = (item["class_id"], object_class_id_list, object_id_list)
                d.setdefault(key, dict())[item["id"]] = None
            for (class_id, object_class_id_list, object_id_list), ids in d.items():
                for object_class_id, object_id in zip(object_class_id_list, object_id_list):
                    for parent_item in self.find_items(db_map, (object_class_id, object_id, class_id)):
                        result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def _parent_entity_group_data(self, db_map_data):
        """Takes given entity group data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                d.setdefault(item["class_id"], dict())[item["group_id"]] = None
            for class_id, ids in d.items():
                for parent_item in self.find_items(db_map, (class_id,)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def _parent_entity_member_data(self, db_map_data):
        """Takes given entity member data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                d.setdefault((item["class_id"], item["group_id"]), dict())[item["member_id"]] = None
            for (class_id, group_id), ids in d.items():
                for parent_item in self.find_items(db_map, (class_id, group_id)):
                    member_class_item = parent_item.child(0)
                    result.setdefault(member_class_item, {})[db_map] = list(ids.keys())
        return result

    def add_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_objects(self, db_map_data):
        for parent_item, db_map_ids in self._parent_object_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def add_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_class_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def add_entity_groups(self, db_map_data):
        for parent_item, db_map_ids in self._parent_entity_group_data(db_map_data).items():
            parent_item.raise_group_children_by_id(db_map_ids)
        for parent_item, db_map_ids in self._parent_entity_member_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def remove_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_objects(self, db_map_data):
        for parent_item, db_map_ids in self._parent_object_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_class_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def remove_entity_groups(self, db_map_data):
        for parent_item, db_map_ids in self._parent_entity_member_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def update_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_objects(self, db_map_data):
        for parent_item, db_map_ids in self._parent_object_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_class_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def find_next_relationship_index(self, index):
        """Find and return next occurrence of relationship item."""
        if not index.isValid():
            return
        rel_item = self.item_from_index(index)
        if not rel_item.item_type == "relationship":
            return
        # Get all ancestors
        rel_cls_item = rel_item.parent_item
        obj_item = rel_cls_item.parent_item
        # Get data from ancestors
        # TODO: Is it enough to just use the first db_map?
        db_map = rel_item.first_db_map
        rel_data = rel_item.db_map_data(db_map)
        rel_cls_data = rel_cls_item.db_map_data(db_map)
        obj_data = obj_item.db_map_data(db_map)
        # Get specific data for our searches
        rel_cls_id = rel_cls_data['id']
        obj_id = obj_data['id']
        object_ids = list(reversed([int(id_) for id_ in rel_data['object_id_list'].split(",")]))
        object_class_ids = list(reversed([int(id_) for id_ in rel_cls_data['object_class_id_list'].split(",")]))
        # Find position in the relationship of the (grand parent) object,
        # then use it to determine object_class and object id to look for
        pos = object_ids.index(obj_id) - 1
        object_id = object_ids[pos]
        object_class_id = object_class_ids[pos]
        # Return first node that passes all cascade filters
        for parent_item in self.find_items(db_map, (object_class_id, object_id, rel_cls_id), fetch=True):
            for item in parent_item.find_children(lambda child: child.display_id == rel_item.display_id):
                return self.index_from_item(item)
        return None


class RelationshipTreeModel(MultiDBTreeModel):
    """A relationship-oriented tree model."""

    @property
    def root_item_type(self):
        return RelationshipTreeRootItem

    def _parent_relationship_data(self, db_map_data):
        """Takes given relationship data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            dict: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            d = dict()
            for item in items:
                d.setdefault(item["class_id"], dict())[item["id"]] = None
            for class_id, ids in d.items():
                for parent_item in self.find_items(db_map, (class_id,)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def add_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._parent_relationship_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)
