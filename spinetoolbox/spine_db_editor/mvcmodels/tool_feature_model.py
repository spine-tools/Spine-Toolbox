######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from PySide2.QtCore import QMimeData, Qt, QModelIndex
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel
from .tree_item_utility import NonLazyDBItem, NonLazyTreeItem
from .tool_feature_item import FeatureRootItem, ToolRootItem, FeatureLeafItem, ToolLeafItem, ToolFeatureLeafItem


class ToolFeatureModel(MinimalTreeModel):
    """A model to display tools and features in a tree view.


    Args:
        parent (SpineDBEditor)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._db_map_feature_data = {}
        self._db_map_feature_methods = {}

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "description")[section]
        return None

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = NonLazyTreeItem(self)
        self.endResetModel()
        for db_map in self.db_maps:
            db_item = NonLazyDBItem(db_map)
            self._invisible_root_item.append_children(db_item)
            feature_root_item = FeatureRootItem()
            tool_root_item = ToolRootItem()
            db_item.append_children(
                feature_root_item, tool_root_item,
            )

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

    def _add_tools_or_features(self, db_map_data, item_type):
        root_number, leaf_maker, name_maker = {
            "feature": (
                0,
                FeatureLeafItem,
                lambda x: self.make_feature_name(x["entity_class_name"], x["parameter_definition_name"]),
            ),
            "tool": (1, ToolLeafItem, lambda x: x["name"]),
        }[item_type]
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            # First realize the ones added locally
            ids = {name_maker(x): x["id"] for x in items}
            for leaf_item in root_item.children[:-1]:
                id_ = ids.pop(leaf_item.name, None)
                if not id_:
                    continue
                leaf_item.handle_added_to_db(identifier=id_)
            # Now append the ones added externally
            children = [leaf_maker(id_) for id_ in ids.values()]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def _update_tools_or_features(self, db_map_data, item_type):
        root_number = {"feature": 0, "tool": 1}[item_type]
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            ids = {x["id"] for x in items}
            leaf_items = {leaf_item.id: leaf_item for leaf_item in root_item.children[:-1]}
            for id_ in ids.intersection(leaf_items):
                leaf_items[id_].handle_updated_in_db()
        self.layoutChanged.emit()

    def _remove_tools_or_features(self, db_map_data, item_type):
        root_number = {"feature": 0, "tool": 1}[item_type]
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            ids = {x["id"] for x in items}
            removed_rows = []
            for row, leaf_item in enumerate(root_item.children[:-1]):
                if leaf_item.id in ids:
                    removed_rows.append(row)
            for row in sorted(removed_rows, reverse=True):
                root_item.remove_children(row, 1)
        self.layoutChanged.emit()

    def add_features(self, db_map_data):
        self._add_tools_or_features(db_map_data, "feature")

    def add_tools(self, db_map_data):
        self._add_tools_or_features(db_map_data, "tool")

    def update_features(self, db_map_data):
        self._update_tools_or_features(db_map_data, "feature")

    def update_tools(self, db_map_data):
        self._update_tools_or_features(db_map_data, "tool")

    def remove_features(self, db_map_data):
        self._remove_tools_or_features(db_map_data, "feature")

    def remove_tools(self, db_map_data):
        self._remove_tools_or_features(db_map_data, "tool")

    def _tool_feature_ids_per_root_item(self, db_map_data):
        d = {}
        db_map_ids_per_tool_id = {}
        for db_map, data in db_map_data.items():
            for item in data:
                tool_id = item["tool_id"]
                db_map_ids_per_tool_id.setdefault(db_map, {}).setdefault(tool_id, []).append(item["id"])
        for db_item in self._invisible_root_item.children:
            ids_per_tool_id = db_map_ids_per_tool_id.get(db_item.db_map)
            if not ids_per_tool_id:
                continue
            tool_root_item = db_item.child(1)
            for tool_id, ids in ids_per_tool_id.items():
                tool_leaf_item = next(iter(child for child in tool_root_item.children if child.id == tool_id), None)
                if tool_leaf_item is None:
                    continue
                tool_feat_root_item = tool_leaf_item.child(0)
                d[tool_feat_root_item] = ids
        return d

    def add_tool_features(self, db_map_data):
        for tool_feat_root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            children = [ToolFeatureLeafItem(id_) for id_ in ids]
            tool_feat_root_item.append_children(*children)

    def update_tool_features(self, db_map_data):
        for tool_feat_root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            for tool_feat_leaf_item in tool_feat_root_item.children:
                if tool_feat_leaf_item.id in ids:
                    top_left = self.index_from_item(tool_feat_leaf_item.child(0))
                    bottom_right = self.index_from_item(tool_feat_leaf_item.child(-1))
                    self.dataChanged.emit(top_left, bottom_right)

    def remove_tool_features(self, db_map_data):
        for tool_feat_root_item, ids in self._tool_feature_ids_per_root_item(db_map_data).items():
            for row, tool_feat_leaf_item in reversed(list(enumerate(tool_feat_root_item.children))):
                if tool_feat_leaf_item.id in ids:
                    tool_feat_root_item.remove_children(row, 1)

    @staticmethod
    def db_item(item):
        while item.item_type != "db":
            item = item.parent_item
        return item

    def db_row(self, item):
        return self.db_item(item).child_number()

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
