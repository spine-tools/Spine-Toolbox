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
Models to represent alternatives, scenarios and scenario alternatives in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:    17.6.2020
"""
import json
from PySide2.QtCore import QMimeData, Qt
from .alternative_tree_item import AlternativeItem, AlternativeRootItem, ScenarioItem, ScenarioRootItem
from .multi_db_tree_model import MultiDBTreeModel
from ...mvcmodels.minimal_tree_model import TreeItem


class AlternativeTreeModel(MultiDBTreeModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._alternative_root = None
        self._scenario_root = None

    @property
    def alternative_root_index(self):
        """Index of the root of the alternative branch of the tree."""
        return self.index_from_item(self._alternative_root)

    @property
    def scenario_root_index(self):
        """Index of the root of the scenario branch of the tree."""
        return self.index_from_item(self._scenario_root)

    @property
    def root_item_type(self):
        return AlternativeRootItem

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
        if db_map_scen_alt_ids and not db_map_alternative_ids:
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
        self._root_item = self._invisible_root_item
        self._alternative_root = AlternativeRootItem(self, dict.fromkeys(self.db_maps))
        self._scenario_root = ScenarioRootItem(self, dict.fromkeys(self.db_maps))
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
                for parent_item in self.find_items(db_map, (scenario_id,), parent_items=(self._scenario_root,)):
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
