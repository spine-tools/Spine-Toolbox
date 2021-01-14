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
Models to represent tools and features in a tree.

:authors: M. Marin (KTH)
:date:    1.0.2020
"""
import json
from PySide2.QtCore import QMimeData, Qt
from .tree_model_base import TreeModelBase
from .tree_item_utility import NonLazyDBItem
from .tool_feature_item import (
    FeatureRootItem,
    ToolRootItem,
    FeatureLeafItem,
    ToolLeafItem,
    ToolFeatureLeafItem,
    ToolFeatureMethodLeafItem,
)


class ToolFeatureModel(TreeModelBase):
    """A model to display tools and features in a tree view.


    Args:
        parent (SpineDBEditor)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent, db_mngr, *db_maps)
        self._db_map_feature_data = {}
        self._db_map_feature_methods = {}

    @staticmethod
    def _make_db_item(db_map):
        return NonLazyDBItem(db_map)

    @staticmethod
    def _top_children():
        return [FeatureRootItem(), ToolRootItem()]

    @staticmethod
    def make_feature_name(entity_class_name, parameter_definition_name):
        return entity_class_name + "/" + parameter_definition_name

    def _begin_set_features(self, db_map):
        parameter_definitions = self.db_mngr.get_items(db_map, "parameter_definition")
        key = lambda x: self.make_feature_name(
            x.get("object_class_name") or x.get("relationship_class_name"), x["parameter_name"]
        )
        self._db_map_feature_data[db_map] = {
            key(x): (x["id"], x["value_list_id"]) for x in parameter_definitions if x["value_list_id"]
        }

    def get_all_feature_names(self, db_map):
        self._begin_set_features(db_map)
        return list(self._db_map_feature_data.get(db_map, {}).keys())

    def get_feature_data(self, db_map, feature_name):
        return self._db_map_feature_data.get(db_map, {}).get(feature_name)

    def _begin_set_feature_method(self, db_map, parameter_value_list_id):
        parameter_value_list = self.db_mngr.get_item(db_map, "parameter_value_list", parameter_value_list_id)
        value_index_list = [int(ind) for ind in parameter_value_list["value_index_list"].split(";")]
        display_value_list = self.db_mngr.get_parameter_value_list(db_map, parameter_value_list_id, Qt.DisplayRole)
        self._db_map_feature_methods.setdefault(db_map, {})[parameter_value_list_id] = dict(
            zip(display_value_list, value_index_list)
        )

    def get_all_feature_methods(self, db_map, parameter_value_list_id):
        self._begin_set_feature_method(db_map, parameter_value_list_id)
        return list(self._db_map_feature_methods.get(db_map, {}).get(parameter_value_list_id, {}).keys())

    def get_method_index(self, db_map, parameter_value_list_id, method):
        return self._db_map_feature_methods.get(db_map, {}).get(parameter_value_list_id, {}).get(method)

    def _tool_ids_per_root_item(self, db_map_data):
        return self._ids_per_root_item(db_map_data, root_number=1)

    def _feature_ids_per_root_item(self, db_map_data):
        return self._ids_per_root_item(db_map_data, root_number=0)

    def _tool_feature_ids_per_root_item(self, db_map_data):
        db_map_data_per_tool_id = self._db_map_data_per_id(db_map_data, "tool_id")
        d = {}
        for db_item in self._invisible_root_item.children:
            items_per_tool_id = db_map_data_per_tool_id.get(db_item.db_map)
            if not items_per_tool_id:
                continue
            tool_root_item = db_item.child(1)
            for tool_id, items in items_per_tool_id.items():
                tool_leaf_item = next(iter(child for child in tool_root_item.children if child.id == tool_id), None)
                if tool_leaf_item is None:
                    continue
                tool_feat_root_item = tool_leaf_item.child(0)
                d[tool_feat_root_item] = [x["id"] for x in items]
        return d

    def _tool_feature_method_ids_per_root_item(self, db_map_data):
        db_map_data_per_tool_feat_id = self._db_map_data_per_id(db_map_data, "tool_feature_id")
        d = {}
        for db_item in self._invisible_root_item.children:
            items_per_tool_feat_id = db_map_data_per_tool_feat_id.get(db_item.db_map)
            if not items_per_tool_feat_id:
                continue
            tool_root_item = db_item.child(1)
            for tool_feat_id, items in items_per_tool_feat_id.items():
                tool_feat_leaf_item = next(
                    iter(
                        child
                        for tool_leaf_item in tool_root_item.children
                        for child in tool_leaf_item.child(0).children
                        if child.id == tool_feat_id
                    ),
                    None,
                )
                if tool_feat_leaf_item is None:
                    continue
                tool_feat_meth_root_item = tool_feat_leaf_item.child(1)
                d[tool_feat_meth_root_item] = [x["id"] for x in items]
        return d

    def add_features(self, db_map_data):
        for root_item, ids in self._feature_ids_per_root_item(db_map_data).items():
            children = [FeatureLeafItem(id_) for id_ in ids]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def add_tools(self, db_map_data):
        for root_item, ids in self._tool_ids_per_root_item(db_map_data).items():
            children = [ToolLeafItem(id_) for id_ in ids]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def add_tool_features(self, db_map_data):
        for root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            children = [ToolFeatureLeafItem(id_) for id_ in ids]
            root_item.append_children(*children)

    def add_tool_feature_methods(self, db_map_data):
        for root_item, ids in self._tool_feature_method_ids_per_root_item(db_map_data).items():
            children = [ToolFeatureMethodLeafItem(id_) for id_ in ids]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def update_features(self, db_map_data):
        for root_item, ids in self._feature_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def update_tools(self, db_map_data):
        for root_item, ids in self._tool_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def update_tool_features(self, db_map_data):
        for root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def update_tool_feature_methods(self, db_map_data):
        for root_item, ids in self._tool_feature_method_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def remove_features(self, db_map_data):
        for root_item, ids in self._feature_ids_per_root_item(db_map_data).items():
            self._remove_leaf_items(root_item, ids)

    def remove_tools(self, db_map_data):
        for root_item, ids in self._tool_ids_per_root_item(db_map_data).items():
            self._remove_leaf_items(root_item, ids)

    def remove_tool_features(self, db_map_data):
        for root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            self._remove_leaf_items(root_item, ids)

    def remove_tool_feature_methods(self, db_map_data):
        for root_item, ids in self._tool_feature_method_ids_per_root_item(db_map_data).items():
            self._remove_leaf_items(root_item, ids)

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeData(self, indexes):
        """
        Builds a dict mapping db name to item type to a list of ids.

        Returns:
            QMimeData
        """
        items = {self.item_from_index(ind): None for ind in indexes}  # NOTE: this avoids dupes and keeps order
        d = {}
        for item in items:
            parent_item = item.parent_item
            db_row = self.db_row(parent_item)
            parent_type = parent_item.item_type
            master_key = ";;".join([str(db_row), parent_type])
            d.setdefault(master_key, []).append(item.child_number())
        data = json.dumps(d)
        mime = QMimeData()
        mime.setText(data)
        return mime

    def canDropMimeData(self, data, drop_action, row, column, parent):
        if not parent.isValid():
            return False
        if not data.hasText():
            return False
        try:
            data = json.loads(data.text())
        except ValueError:
            return False
        if not isinstance(data, dict):
            return False
        # Check that all source data comes from the same db and parent
        if len(data) != 1:
            return False
        master_key = next(iter(data))
        db_row, parent_type = master_key.split(";;")
        db_row = int(db_row)
        if parent_type != "feature root":
            return False
        # Check that target is in the same db as source
        tool_item = self.item_from_index(parent)
        if db_row != self.db_row(tool_item):
            return False
        return True

    def dropMimeData(self, data, drop_action, row, column, parent):
        tool_feat_root_item = self.item_from_index(parent)
        master_key, feature_rows = json.loads(data.text()).popitem()
        db_row, _parent_type = master_key.split(";;")
        db_row = int(db_row)
        feat_root_item = self._invisible_root_item.child(db_row).child(0)
        db_items = []
        for feat_row in feature_rows:
            item = feat_root_item.child(feat_row)
            feature_id = item.id
            if feature_id in tool_feat_root_item.feature_id_list:
                continue
            parameter_value_list_id = item.item_data.get("parameter_value_list_id")
            db_item = {
                "tool_id": tool_feat_root_item.parent_item.id,
                "feature_id": feature_id,
                "parameter_value_list_id": parameter_value_list_id,
            }
            db_items.append(db_item)
        self.db_mngr.add_tool_features({tool_feat_root_item.db_map: db_items})
        return True
