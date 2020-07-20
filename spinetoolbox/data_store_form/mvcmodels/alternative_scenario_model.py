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
from PySide2.QtCore import QMimeData, Qt, QModelIndex
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel
from .tree_item_utility import NonLazyDBItem
from .alternative_scenario_item import (
    NonLazyTreeItem,
    AlternativeRootItem,
    ScenarioRootItem,
    AlternativeLeafItem,
    ScenarioLeafItem,
)


class AlternativeScenarioModel(MinimalTreeModel):

    """A model to display parameter_value_list data in a tree view.


    Args:
        parent (DataStoreForm)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("name", "description")[section]
        return None

    def alternative_root_indexes(self, db_maps):
        items = [child for child in self._invisible_root_item.children if child.db_map in db_maps]
        items += [item.child(0) for item in items]
        return [self.index_from_item(item) for item in items]

    def scenario_root_indexes(self, db_maps):
        items = [child for child in self._invisible_root_item.children if child.db_map in db_maps]
        items += [item.child(1) for item in items]
        return [self.index_from_item(item) for item in items]

    def build_tree(self):
        """Builds tree."""
        self.beginResetModel()
        self._invisible_root_item = NonLazyTreeItem(self)
        self.endResetModel()
        for db_map in self.db_maps:
            db_item = NonLazyDBItem(db_map)
            self._invisible_root_item.append_children(db_item)
            alt_root_item = AlternativeRootItem()
            scen_root_item = ScenarioRootItem()
            db_item.append_children(alt_root_item, scen_root_item)

    def _add_leaves(self, db_map_data, leaf_type):
        root_number, leaf_maker = {"alternative": (0, AlternativeLeafItem), "scenario": (1, ScenarioLeafItem)}[
            leaf_type
        ]
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            root_item = db_item.child(root_number)
            # First realize the ones added locally
            ids = {x["name"]: x["id"] for x in items}
            for leaf_item in root_item.children[:-1]:
                id_ = ids.pop(leaf_item.name, None)
                if not id_:
                    continue
                leaf_item.handle_added_to_db(identifier=id_)
            # Now append the ones added externally
            children = [leaf_maker(id_) for id_ in ids.values()]
            root_item.insert_children(root_item.child_count() - 1, *children)

    def _update_leaves(self, db_map_data, leaf_type):
        root_number = {"alternative": 0, "scenario": 1}[leaf_type]
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

    def _remove_leaves(self, db_map_data, leaf_type):
        root_number = {"alternative": 0, "scenario": 1}[leaf_type]
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

    def add_alternatives(self, db_map_data):
        self._add_leaves(db_map_data, "alternative")

    def add_scenarios(self, db_map_data):
        self._add_leaves(db_map_data, "scenario")

    def update_alternatives(self, db_map_data):
        self._update_leaves(db_map_data, "alternative")

    def update_scenarios(self, db_map_data):
        self._update_leaves(db_map_data, "scenario")

    def remove_alternatives(self, db_map_data):
        self._remove_leaves(db_map_data, "alternative")

    def remove_scenarios(self, db_map_data):
        self._remove_leaves(db_map_data, "scenario")

    @staticmethod
    def db_row(item):
        while item.item_type != "db":
            item = item.parent_item
        return item.child_number()

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeData(self, indexes):
        """
        Builds a dict mapping db name to item type to a list of ids.

        Returns:
            QMimeData
        """
        items = [self.item_from_index(i) for i in indexes]
        d = {}
        for item in items:
            parent_item = item.parent_item
            db_row = self.db_row(parent_item)
            parent_type = parent_item.item_type
            master_key = ";;".join([str(db_row), parent_type])
            d.setdefault(master_key, {}).setdefault(parent_item.child_number(), []).append(item.child_number())
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
        if len(data) != 1:
            return False
        master_key = next(iter(data))
        if len(data[master_key]) != 1:
            return False
        db_row, parent_type = master_key.split(";;")
        db_row = int(db_row)
        if parent_type not in ("alternative root", "scenario"):
            return False
        scenario_item = self.item_from_index(parent)
        if db_row != self.db_row(scenario_item):
            return False
        if parent_type == "scenario":
            scenario_row = next(iter(data[master_key]))
            if int(scenario_row) != scenario_item.child_number():
                return False
        return True

    def dropMimeData(self, data, drop_action, row, column, parent):
        scenario_item = self.item_from_index(parent)
        alternative_id_list = scenario_item.alternative_id_list
        if row == -1:
            row = len(alternative_id_list)
        master_key, rows = json.loads(data.text()).popitem()
        db_row, parent_type = master_key.split(";;")
        db_row = int(db_row)
        if parent_type == "alternative root":
            alt_root_item = self._invisible_root_item.child(db_row).child(0)
            _, alternative_rows = rows.popitem()
            alternative_ids = [alt_root_item.child(row).id for row in alternative_rows]
            alternative_ids = [id_ for id_ in alternative_ids if id_ not in set(alternative_id_list) | {None}]
        elif parent_type == "scenario":
            _, alternative_rows = rows.popitem()
            alternative_ids = [scenario_item.child(row).id for row in alternative_rows]
            alternative_id_list = [id_ for id_ in alternative_id_list if id_ not in alternative_ids]
        alternative_id_list[row:row] = alternative_ids
        db_item = {
            "scenario_id": scenario_item.id,
            "alternative_id_list": ",".join([str(id_) for id_ in alternative_id_list]),
        }
        self.db_mngr.set_scenario_alternatives({scenario_item.db_map: [db_item]})
        return True
