######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains scenario tree model."""
import pickle
from PySide6.QtCore import QMimeData, Qt, QByteArray
from spinetoolbox.helpers import unique_name
from .tree_model_base import TreeModelBase
from .scenario_item import ScenarioDBItem, ScenarioAlternativeItem, ScenarioItem
from .utils import two_column_as_csv
from . import mime_types


class ScenarioModel(TreeModelBase):
    """A model to display scenarios in a tree view."""

    def _make_db_item(self, db_map):
        return ScenarioDBItem(self, db_map)

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeData(self, indexes):
        """Stores selected indexes into MIME data.

        If indexes contains scenario indexes, only those indexes will be kept.
        Otherwise, only scenario alternative indexes are kept.

        The MIME data contains distinct data:
        - Text representation of the selection
        - A pickled dict mapping db identifier to list of alternative ids
        - A pickled dict mapping db identifier to list of scenario ids

        Args:
            indexes (Sequence of QModelIndex): selected indexes

        Returns:
            QMimeData: MIME data or None if selection was bad
        """
        mime = QMimeData()
        scenario_indexes = []
        scenario_items = {}
        for index in indexes:
            item = self.item_from_index(index)
            if isinstance(item, ScenarioItem) and item.id is not None:
                scenario_indexes.append(index)
                # We have two columns and consequently usually twice the same item per row.
                # Make items unique without losing order using a dictionary trick.
                scenario_items[item] = None
        if scenario_items:
            scenario_data = {}
            for item in scenario_items:
                db_item = item.parent_item
                db_key = self.db_mngr.db_map_key(db_item.db_map)
                scenario_data.setdefault(db_key, []).append(item.id)
            mime.setData(mime_types.SCENARIO_DATA, QByteArray(pickle.dumps(scenario_data)))
            mime.setText(two_column_as_csv(scenario_indexes))
            return mime
        alternative_indexes = []
        alternative_items = {}
        for index in indexes:
            item = self.item_from_index(index)
            if isinstance(item, ScenarioAlternativeItem) and item.alternative_id is not None:
                alternative_indexes.append(index)
                # We have two columns and consequently usually twice the same item per row.
                # Make items unique without losing order using a dictionary trick.
                alternative_items[item] = None
        if alternative_items:
            alternative_data = {}
            for item in alternative_items:
                db_item = item.parent_item.parent_item
                db_key = self.db_mngr.db_map_key(db_item.db_map)
                alternative_data.setdefault(db_key, []).append(item.alternative_id)
            mime.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(alternative_data)))
            mime.setText(two_column_as_csv(alternative_indexes))
            return mime
        return None

    def canDropMimeData(self, mime_data, drop_action, row, column, parent):
        if drop_action & self.supportedDropActions() == 0:
            return False
        if not mime_data.hasFormat(mime_types.ALTERNATIVE_DATA):
            return False
        try:
            payload = pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data())
        except pickle.UnpicklingError:
            return False
        if not isinstance(payload, dict):
            return False
        # Check that all source data comes from the same db and parent
        if len(payload) != 1:
            return False
        db_map_key = next(iter(payload))
        try:
            db_map = self.db_mngr.db_map_from_key(db_map_key)
        except KeyError:
            return False
        if not parent.isValid():
            return True
        parent_item = self.item_from_index(parent)
        # Check that target is in the same db as source
        db_item = self.db_item(parent_item)
        if db_map != db_item.db_map:
            return False
        if mime_data.hasFormat("application/vnd.spinetoolbox.scenario-alternative"):
            # Check that reordering only happens within the same scenario
            return False
        return True

    def dropMimeData(self, mime_data, drop_action, row, column, parent):
        # This function expects that data has be verified by canDropMimeData() already.
        scenario_item = self.item_from_index(parent)
        if not isinstance(scenario_item, ScenarioItem):
            # In some rare cases, it is possible that the drop was accepted
            # on a wrong tree item (bug in Qt or canDropMimeData()?).
            # In those cases the type of scen_item is StandardTreeItem or ScenarioRootItem.
            return False
        self.paste_alternative_mime_data(mime_data, row, scenario_item)
        return True

    def paste_alternative_mime_data(self, mime_data, row, scenario_item):
        """Adds alternatives from MIME data to the model.

        Args:
            mime_data (QMimeData): mime data that must contain ALTERNATIVE_DATA format
            row (int): where to paste within scenario item, -1 lets the model choose
            scenario_item (ScenarioItem): parent item
        """
        old_alternative_id_list = list(scenario_item.alternative_id_list)
        if row == -1:
            row = len(old_alternative_id_list)
        new_alternative_ids = []
        for db_map_key, alternative_names in pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data()).items():
            target_db_map = self.db_mngr.db_map_from_key(db_map_key)
            if target_db_map != scenario_item.db_map:
                continue
            for name in alternative_names:
                if isinstance(name, str):
                    new_alternative_ids.append(scenario_item.db_map.get_alternative_item(name=name)["id"])
                else:  # When rearranging alternatives in a scenario, the id is given straight
                    new_alternative_ids.append(name)
        alternative_id_list = [id_ for id_ in old_alternative_id_list[:row] if id_ not in new_alternative_ids]
        alternative_id_list += new_alternative_ids
        alternative_id_list += [id_ for id_ in old_alternative_id_list[row:] if id_ not in new_alternative_ids]
        db_item = {"id": scenario_item.id, "alternative_id_list": alternative_id_list}
        self.db_mngr.set_scenario_alternatives({scenario_item.db_map: [db_item]})

    def paste_scenario_mime_data(self, mime_data, db_item):
        """Adds scenarios and their alternatives from MIME data to the model.

        Args:
            mime_data (QMimeData): mime data that must contain ALTERNATIVE_DATA format
            db_item (ScenarioDBItem): parent item
        """
        scenarios_to_add = []
        alternatives_to_add = []
        alternative_names_by_scenario = {}
        existing_scenarios = {i["name"] for i in self.db_mngr.get_items(db_item.db_map, "scenario")}
        existing_alternatives = {i["name"] for i in self.db_mngr.get_items(db_item.db_map, "alternative")}
        for db_map_key, scenario_names in pickle.loads(mime_data.data(mime_types.SCENARIO_DATA).data()).items():
            db_map = self.db_mngr.db_map_from_key(db_map_key)
            if db_map is db_item.db_map:
                continue
            for name in scenario_names:
                scenario_data = db_map.get_scenario_item(name=name)
                if scenario_data["name"] in existing_scenarios:
                    continue
                alternative_id_list = self.db_mngr.get_scenario_alternative_id_list(db_map, scenario_data["id"])
                for alternative_id in alternative_id_list:
                    alternative_db_item = self.db_mngr.get_item(db_map, "alternative", alternative_id)
                    alternative_names_by_scenario.setdefault(scenario_data["name"], []).append(
                        alternative_db_item["name"]
                    )
                    if alternative_db_item["name"] in existing_alternatives:
                        continue
                    alternatives_to_add.append(
                        {"name": alternative_db_item["name"], "description": alternative_db_item["description"]}
                    )
                scenarios_to_add.append({"name": scenario_data["name"], "description": scenario_data["description"]})
        if scenarios_to_add:
            if alternatives_to_add:
                self.db_mngr.add_alternatives({db_item.db_map: alternatives_to_add})
            self.db_mngr.add_scenarios({db_item.db_map: scenarios_to_add})
            alternatives = self.db_mngr.get_items(db_item.db_map, "alternative")
            alternative_id_by_name = {i["name"]: i["id"] for i in alternatives}
            scenarios = self.db_mngr.get_items(db_item.db_map, "scenario")
            scenario_id_by_name = {i["name"]: i["id"] for i in scenarios}
            scenario_alternative_id_lists = []
            for scenario_name, alternative_name_list in alternative_names_by_scenario.items():
                alternative_id_list = [alternative_id_by_name[name] for name in alternative_name_list]
                scenario_alternative_id_lists.append(
                    {"id": scenario_id_by_name[scenario_name], "alternative_id_list": alternative_id_list}
                )
            self.db_mngr.set_scenario_alternatives({db_item.db_map: scenario_alternative_id_lists})

    def duplicate_scenario(self, scenario_item):
        """Duplicates scenario within database.

        Args:
            scenario_item (ScenarioItem): scenario item to duplicate
        """
        db_map = scenario_item.db_map
        existing_names = {i["name"] for i in self.db_mngr.get_items(db_map, "scenario")}
        name = unique_name(scenario_item.item_data["name"], existing_names)
        self.db_mngr.add_scenarios({db_map: [{"name": name, "description": scenario_item.item_data["description"]}]})
        alternative_id_list = self.db_mngr.get_scenario_alternative_id_list(db_map, scenario_item.id)
        for item in self.db_mngr.get_items(db_map, "scenario"):
            if item["name"] == name:
                self.db_mngr.set_scenario_alternatives(
                    {db_map: [{"id": item["id"], "alternative_id_list": alternative_id_list}]}
                )
                break
