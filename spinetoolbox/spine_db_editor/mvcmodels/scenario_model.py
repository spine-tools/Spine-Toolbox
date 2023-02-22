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
"""Contains scenario tree model."""
import pickle

from PySide6.QtCore import QMimeData, Qt
from .tree_model_base import TreeModelBase
from .scenario_item import DBItem, ScenarioItem
from .utils import two_column_as_csv
from . import mime_types


class ScenarioModel(TreeModelBase):
    """A model to display scenarios in a tree view."""

    @staticmethod
    def _make_db_item(db_map):
        return DBItem(db_map)

    @staticmethod
    def _top_children():
        return []

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeData(self, indexes):
        """Stores selected indexes into MIME data.

        The MIME data structure contains two distinct data:

        - Text representation of the selection
        - A pickled dict mapping db identifier to list of alternative ids

        Args:
            indexes (Sequence of QModelIndex): selected indexes

        Returns:
            QMimeData: MIME data
        """
        # We have two columns and consequently usually twice the same item per row.
        # Make items unique without losing order using a dictionary trick.
        items = list(dict.fromkeys(self.item_from_index(ind) for ind in indexes))
        d = {}
        for item in items:
            db_item = item.parent_item.parent_item
            db_key = self.db_mngr.db_map_key(db_item.db_map)
            d.setdefault(db_key, []).append(item.alternative_id)
        data = pickle.dumps(d)
        mime = QMimeData()
        mime.setData(mime_types.ALTERNATIVE_DATA, data)
        mime.setText(two_column_as_csv(indexes))
        return mime

    def canDropMimeData(self, data, drop_action, row, column, parent):
        if drop_action & self.supportedDropActions() == 0:
            return False
        if not data.hasFormat(mime_types.ALTERNATIVE_DATA):
            return False
        try:
            payload = pickle.loads(data.data(mime_types.ALTERNATIVE_DATA))
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
        if data.hasFormat("application/vnd.spinetoolbox.scenario-alternative"):
            # Check that reordering only happens within the same scenario
            return False
        return True

    def dropMimeData(self, data, drop_action, row, column, parent):
        scenario_item = self.item_from_index(parent)
        if not isinstance(scenario_item, ScenarioItem):
            # In some rare cases, it is possible that the drop was accepted
            # on a wrong tree item (bug in Qt or canDropMimeData()?).
            # In those cases the type of scen_item is StandardTreeItem or ScenarioRootItem.
            return False
        old_alternative_id_list = list(scenario_item.alternative_id_list)
        if row == -1:
            row = len(old_alternative_id_list)
        db_map_key, alternative_ids = pickle.loads(data.data(mime_types.ALTERNATIVE_DATA)).popitem()
        alternative_id_list = [id_ for id_ in old_alternative_id_list[:row] if id_ not in alternative_ids]
        alternative_id_list += alternative_ids
        alternative_id_list += [id_ for id_ in old_alternative_id_list[row:] if id_ not in alternative_ids]
        db_item = {"id": scenario_item.id, "alternative_id_list": alternative_id_list}
        self.db_mngr.set_scenario_alternatives({scenario_item.db_map: [db_item]})
        return True
