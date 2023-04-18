######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

from .entity_tree_item import ObjectTreeRootItem, RelationshipTreeRootItem
from .multi_db_tree_model import MultiDBTreeModel


class ObjectTreeModel(MultiDBTreeModel):
    """An 'object-oriented' tree model."""

    @property
    def root_item_type(self):
        return ObjectTreeRootItem

    def find_next_relationship_index(self, index):
        """Find and return next occurrence of relationship item."""
        if not index.isValid():
            return None
        rel_item = self.item_from_index(index)
        if not rel_item.item_type == "relationship":
            return None
        # Get all ancestors
        rel_cls_item = rel_item.parent_item
        obj_item = rel_cls_item.parent_item
        for db_map in rel_item.db_maps:
            # Get data from ancestors
            rel_data = rel_item.db_map_data(db_map)
            rel_cls_data = rel_cls_item.db_map_data(db_map)
            obj_data = obj_item.db_map_data(db_map)
            # Get specific data for our searches
            rel_cls_id = rel_cls_data['id']
            obj_id = obj_data['id']
            object_ids = list(reversed(rel_data['object_id_list']))
            object_class_ids = list(reversed(rel_cls_data['object_class_id_list']))
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
