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
Models to represent alternatives, scenarios and scenario alternatives in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:    17.6.2020
"""
import json
from PySide2.QtCore import QMimeData, Qt
from .tree_model_base import TreeModelBase
from .tree_item_utility import NonLazyDBItem
from .alternative_scenario_item import AlternativeRootItem, ScenarioRootItem, AlternativeLeafItem, ScenarioLeafItem


class AlternativeScenarioModel(TreeModelBase):

    """A model to display alternatives and scenarios in a tree view.


    Args:
        parent (SpineDBEditor)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    @staticmethod
    def _make_db_item(db_map):
        return NonLazyDBItem(db_map)

    @staticmethod
    def _top_children():
        return [AlternativeRootItem(), ScenarioRootItem()]

    def _alternative_or_scenario_ids_per_root_item(self, db_map_data, alternative_or_scenario):
        root_number = {"alternative": 0, "scenario": 1}[alternative_or_scenario]
        d = {}
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            d[root_item] = [x["id"] for x in items]
        return d

    def _scenario_ids_per_root_item(self, db_map_data):
        return self._ids_per_root_item(db_map_data, root_number=1)

    def _alternative_ids_per_root_item(self, db_map_data):
        return self._ids_per_root_item(db_map_data, root_number=0)

    def add_alternatives(self, db_map_data):
        for root_item, ids in self._alternative_ids_per_root_item(db_map_data).items():
            children = [AlternativeLeafItem(id_) for id_ in ids]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def add_scenarios(self, db_map_data):
        for root_item, ids in self._scenario_ids_per_root_item(db_map_data).items():
            children = [ScenarioLeafItem(id_) for id_ in ids]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def update_alternatives(self, db_map_data):
        for root_item, ids in self._alternative_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def update_scenarios(self, db_map_data):
        for root_item, ids in self._scenario_ids_per_root_item(db_map_data).items():
            self._update_leaf_items(root_item, ids)

    def remove_alternatives(self, db_map_data):
        for root_item, ids in self._alternative_ids_per_root_item(db_map_data).items():
            self._remove_leaf_items(root_item, ids)

    def remove_scenarios(self, db_map_data):
        for root_item, ids in self._scenario_ids_per_root_item(db_map_data).items():
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
            scen_row = parent_item.parent_item.child_number() if parent_type == "scenario_alternative root" else None
            master_key = ";;".join([str(db_row), parent_type, str(scen_row)])
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
        db_row, parent_type, scen_row = master_key.split(";;")
        db_row = int(db_row)
        if parent_type not in ("alternative root", "scenario_alternative root"):
            return False
        # Check that target is in the same db as source
        scen_alt_root_item = self.item_from_index(parent)
        if db_row != self.db_row(scen_alt_root_item):
            return False
        if parent_type == "scenario_alternative root":
            # Check that reordering only happens within the same scenario
            scen_row = int(scen_row)
            if scen_row != scen_alt_root_item.parent_item.child_number():
                return False
        return True

    def dropMimeData(self, data, drop_action, row, column, parent):
        scen_alt_root_item = self.item_from_index(parent)
        alternative_id_list = scen_alt_root_item.alternative_id_list
        if row == -1:
            row = len(alternative_id_list)
        master_key, alternative_rows = json.loads(data.text()).popitem()
        db_row, parent_type, _parent_row = master_key.split(";;")
        db_row = int(db_row)
        if parent_type == "alternative root":
            alt_root_item = self._invisible_root_item.child(db_row).child(0)
            alternative_ids = [alt_root_item.child(row).id for row in alternative_rows]
            alternative_ids = [id_ for id_ in alternative_ids if id_ not in set(alternative_id_list) | {None}]
        elif parent_type == "scenario_alternative root":
            alternative_ids = [scen_alt_root_item.child(row).id for row in alternative_rows]
            alternative_id_list = [id_ for id_ in alternative_id_list if id_ not in alternative_ids]
        alternative_id_list[row:row] = alternative_ids
        db_item = {
            "id": scen_alt_root_item.parent_item.id,
            "alternative_id_list": ",".join([str(id_) for id_ in alternative_id_list]),
        }
        self.db_mngr.set_scenario_alternatives({scen_alt_root_item.db_map: [db_item]})
        return True
