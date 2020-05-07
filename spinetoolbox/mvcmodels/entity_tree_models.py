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
Models to represent entities in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""
import json

from PySide2.QtCore import Qt, Signal, QModelIndex, QMimeData
from PySide2.QtGui import QIcon
from .entity_tree_item import (
    ScenarioAlternativeItem,
    ScenarioItem,
    ScenarioClassItem,
    AlternativeClassItem,
    AlternativeItem,
    ObjectTreeRootItem,
    ObjectClassItem,
    ObjectItem,
    RelationshipTreeRootItem,
    RelationshipClassItem,
    RelationshipItem,
)
from .minimal_tree_model import MinimalTreeModel, TreeItem


class EntityTreeModel(MinimalTreeModel):
    """Base class for all entity tree models."""

    remove_selection_requested = Signal()

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

    @property
    def root_item_type(self):
        """Implement in subclasses to create a model specific to any entity type."""
        raise NotImplementedError()

    @property
    def root_item(self):
        return self._root_item

    @property
    def root_index(self):
        return self.index_from_item(self._root_item)

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

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = TreeItem(self)
        self.endResetModel()
        self.selected_indexes.clear()
        self._root_item = self.root_item_type(self, dict.fromkeys(self.db_maps))
        self._invisible_root_item.append_children(self._root_item)

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

    def _select_index(self, index):
        """Marks the index as selected."""
        if not index.isValid() or index.column() != 0:
            return
        item_type = type(self.item_from_index(index))
        self.selected_indexes.setdefault(item_type, {})[index] = None

    def select_indexes(self, indexes):
        """Marks given indexes as selected."""
        self.selected_indexes.clear()
        for index in indexes:
            self._select_index(index)

    def find_items(self, db_map, path_prefix, parent_items=(), fetch=False):
        """Returns items at given path prefix.
        """
        if not parent_items:
            # Start from the root node
            parent_items = [self.root_item]
        for id_ in path_prefix:
            parent_items = [
                child for parent_item in parent_items for child in parent_item.find_children_by_id(db_map, id_)
            ]
            if fetch:
                for parent_item in parent_items:
                    parent = self.index_from_item(parent_item)
                    if self.canFetchMore(parent):
                        self.fetchMore(parent)
        return parent_items


class AlternativeTreeModel(EntityTreeModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_icon = QIcon(":/icons/menu_icons/cube_minus.svg")
        self._alternative_root = None
        self._scenario_root = None

    @property
    def root_item_type(self):
        return AlternativeClassItem

    @property
    def selected_alternative_indexes(self):
        return self.selected_indexes.get(AlternativeItem, {})

    @property
    def selected_scenario_indexes(self):
        return self.selected_indexes.get(ScenarioItem, {})

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeData(self, indexes):
        items = [self.item_from_index(i) for i in indexes]
        db_map_id = {}
        for item in items:
            for db_map in item.db_maps:
                db_map_id.setdefault(db_map.codename, {}).setdefault(item.item_type, []).append(
                    item.db_map_data_field(db_map, "id")
                )
        data = json.dumps(db_map_id)
        mime = QMimeData()
        mime.setText(data)
        return mime

    def dropMimeData(self, data, drop_action, row, column, parent):
        db_map_alternative_ids = json.loads(data.text())
        db_codenames = {db.codename: db for db in self.db_mngr.db_maps if db.codename in db_map_alternative_ids}
        db_map_scen_alt_ids = {
            db_codenames[name]: type_ids["scenario_alternative"]
            for name, type_ids in db_map_alternative_ids.items()
            if "scenario_alternative" in type_ids
        }
        db_map_alternative_ids = {
            db_codenames[name]: type_ids["alternative"]
            for name, type_ids in db_map_alternative_ids.items()
            if "alternative" in type_ids
        }
        if db_map_alternative_ids and not db_map_scen_alt_ids:
            parent_item = parent.internalPointer()
            parent_item.insert_alternative(row, db_map_alternative_ids)
            return True
        elif db_map_scen_alt_ids and not db_map_alternative_ids:
            parent_item = parent.internalPointer()
            source_row = None
            count = 0
            for child_row, child in enumerate(parent_item.children):
                if all(id_ in db_map_scen_alt_ids.get(db_map, {}) for db_map, id_ in child.db_map_ids.items()):
                    if source_row is None:
                        source_row = child_row
                    count += 1
                elif source_row is not None:
                    break

            parent_item.move_scenario_alternative(source_row, count, row)
            return True
        return False

    def canDropMimeData(self, data, drop_action, row, column, parent):
        if not data.hasText():
            return False
        try:
            data = json.loads(data.text())
        except ValueError:
            return False
        types = set()
        if not isinstance(data, dict):
            return False
        for _, item_type_dict in data.items():
            if not isinstance(item_type_dict, dict):
                return False
            types.update(item_type_dict.keys())
        if len(types) > 1:
            return False

        return True

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = TreeItem(self)
        self.endResetModel()
        self.selected_indexes.clear()
        self._root_item = self._invisible_root_item
        self._alternative_root = AlternativeClassItem(self, dict.fromkeys(self.db_maps))
        self._scenario_root = ScenarioClassItem(self, dict.fromkeys(self.db_maps))
        self._invisible_root_item.append_children(self._alternative_root)
        self._invisible_root_item.append_children(self._scenario_root)

    def _group_scenario_alternative_data(self, db_map_data):
        """Takes given object data and returns the same data keyed by parent tree-item.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items as dict

        Returns:
            result (dict): maps parent tree-items to DiffDatabaseMapping instances to list of item ids
        """
        result = dict()
        for db_map, items in db_map_data.items():
            # Group items by scenario id
            d = dict()
            for item in items:
                d.setdefault(item["scenario_id"], set()).add(item["id"])
            for scenario_id, ids in d.items():
                # Find the parents corresponding the this class id and put them in the result
                for parent_item in self.find_leaves(db_map, (scenario_id,), parent_items=(self._scenario_root,)):
                    result.setdefault(parent_item, {})[db_map] = ids
        return result

    def add_scenarios(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._scenario_root.append_children_by_id(db_map_ids)

    def add_alternatives(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._alternative_root.append_children_by_id(db_map_ids)

    def add_scenario_alternatives(self, db_map_data):
        for parent_item, db_map_ids in self._group_scenario_alternative_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def update_alternatives(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._alternative_root.update_children_by_id(db_map_ids)

    def update_scenarios(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._scenario_root.update_children_by_id(db_map_ids)

    def update_scenario_alternatives(self, db_map_data):
        for parent_item, db_map_ids in self._group_scenario_alternative_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def remove_alternatives(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._alternative_root.remove_children_by_id(db_map_ids)

    def remove_scenarios(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self._scenario_root.remove_children_by_id(db_map_ids)

    def remove_scenario_alternatives(self, db_map_data):
        for parent_item, db_map_ids in self._group_scenario_alternative_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)


class ObjectTreeModel(EntityTreeModel):
    """An 'object-oriented' tree model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_icon = QIcon(":/icons/menu_icons/cube_minus.svg")

    @property
    def root_item_type(self):
        return ObjectTreeRootItem

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
                d.setdefault(item["class_id"], dict())[item["id"]] = None
            for class_id, ids in d.items():
                # Find the parents corresponding the this class id and put them in the result
                for parent_item in self.find_items(db_map, (class_id,)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
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
                    d.setdefault(int(object_class_id), dict())[item["id"]] = None
            for object_class_id, ids in d.items():
                for parent_item in self.find_items(db_map, (object_class_id, None)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
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
                    d.setdefault(key, dict())[item["id"]] = None
            for (object_id, class_id), ids in d.items():
                for parent_item in self.find_items(db_map, (None, object_id, class_id)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def add_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_objects(self, db_map_data):
        for parent_item, db_map_ids in self._group_object_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def add_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def remove_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_objects(self, db_map_data):
        for parent_item, db_map_ids in self._group_object_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def update_object_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_objects(self, db_map_data):
        for parent_item, db_map_ids in self._group_object_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_class_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)

    def find_next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        # Mildly insane? But I can't think of something better now
        if not index.isValid():
            return
        rel_item = self.item_from_index(index)
        if not isinstance(rel_item, RelationshipItem):
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
        # then use it to determine object class and object id to look for
        pos = object_ids.index(obj_id) - 1
        object_id = object_ids[pos]
        object_class_id = object_class_ids[pos]
        # Return first node that passes all cascade fiters
        for parent_item in self.find_items(db_map, (object_class_id, object_id, rel_cls_id), fetch=True):
            for item in parent_item.find_children(lambda child: child.display_id == rel_item.display_id):
                return self.index_from_item(item)
        return None


class RelationshipTreeModel(EntityTreeModel):
    """A relationship-oriented tree model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_icon = QIcon(":/icons/menu_icons/cubes_minus.svg")

    @property
    def root_item_type(self):
        return RelationshipTreeRootItem

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
                d.setdefault(item["class_id"], dict())[item["id"]] = None
            for class_id, ids in d.items():
                for parent_item in self.find_items(db_map, (class_id,)):
                    result.setdefault(parent_item, {})[db_map] = list(ids.keys())
        return result

    def add_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.append_children_by_id(db_map_ids)

    def add_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.append_children_by_id(db_map_ids)

    def remove_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.remove_children_by_id(db_map_ids)

    def remove_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.remove_children_by_id(db_map_ids)

    def update_relationship_classes(self, db_map_data):
        db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}
        self.root_item.update_children_by_id(db_map_ids)

    def update_relationships(self, db_map_data):
        for parent_item, db_map_ids in self._group_relationship_data(db_map_data).items():
            parent_item.update_children_by_id(db_map_ids)
