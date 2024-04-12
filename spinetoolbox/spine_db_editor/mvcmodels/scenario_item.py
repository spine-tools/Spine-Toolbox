######################################################################################################################
# Copyright (C) 2017-2023 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes to represent items in scenario tree."""
from PySide6.QtCore import Qt
from .tree_item_utility import (
    BoldTextMixin,
    EditableMixin,
    EmptyChildMixin,
    FetchMoreMixin,
    GrayIfLastMixin,
    LeafItem,
    StandardDBItem,
)

_SCENARIO_ICON = "\uf008"  # film


class ScenarioDBItem(EmptyChildMixin, FetchMoreMixin, StandardDBItem):
    """A root item representing a db."""

    @property
    def item_type(self):
        return "db"

    @property
    def fetch_item_type(self):
        return "scenario"

    def empty_child(self):
        return ScenarioItem(self._model)

    def _make_child(self, id_):
        return ScenarioItem(self._model, id_)


class ScenarioItem(GrayIfLastMixin, EditableMixin, EmptyChildMixin, FetchMoreMixin, BoldTextMixin, LeafItem):
    """A scenario leaf item."""

    @property
    def item_type(self):
        return "scenario"

    @property
    def fetch_item_type(self):
        return "scenario_alternative"

    @property
    def icon_code(self):
        return _SCENARIO_ICON

    def tool_tip(self, column):
        if column == 0 and not self.id:
            return "<p><b>Note</b>: Scenario names longer than 20 characters might appear shortened in generated files.</p>"
        return super().tool_tip(column)

    def _do_set_up(self):
        """Doesn't add children to the last row."""
        if not self.id:
            return
        super()._do_set_up()

    def add_item_to_db(self, db_item):
        self.db_mngr.add_scenarios({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_scenarios({self.db_map: [db_item]})

    def handle_updated_in_db(self):
        super().handle_updated_in_db()
        self.update_alternative_id_list()

    def flags(self, column):
        if self.id is not None:
            return super().flags(column) | Qt.ItemFlag.ItemIsDropEnabled
        return super().flags(column) | Qt.ItemFlag.ItemNeverHasChildren

    @property
    def alternative_id_list(self):
        return self.db_mngr.get_scenario_alternative_id_list(self.db_map, self.id)

    def update_alternative_id_list(self):
        alt_count = len(self.alternative_id_list)
        curr_alt_count = len(self.non_empty_children)
        if alt_count > curr_alt_count:
            added_count = alt_count - curr_alt_count
            children = [ScenarioAlternativeItem(self._model) for _ in range(added_count)]
            self.insert_children(curr_alt_count, children)
        elif curr_alt_count > alt_count:
            removed_count = curr_alt_count - alt_count
            self.remove_children(alt_count, removed_count)
        else:
            self.model.dataChanged.emit(
                self.model.index(0, 0, self.index()), self.model.index(self.row_count() - 1, 0, self.index())
            )

    def accepts_item(self, item, db_map):
        return db_map == self.db_map and item["scenario_id"] == self.id

    def handle_items_added(self, _db_map_data):
        self.update_alternative_id_list()

    def handle_items_removed(self, _db_map_data):
        self.update_alternative_id_list()

    def handle_items_updated(self, _db_map_data):
        self.update_alternative_id_list()

    def empty_child(self):
        """See base class."""
        return ScenarioAlternativeItem(self._model)

    def _make_child(self, id_):
        """Not needed - we don't quite add children here, but rather update them in update_alternative_id_list."""


class ScenarioAlternativeItem(GrayIfLastMixin, EditableMixin, LeafItem):
    """A scenario alternative leaf item."""

    @property
    def item_type(self):
        return "scenario_alternative"

    def tool_tip(self, column):
        if column == 0:
            return "<p>Drag and drop this item to reorder scenario alternatives</p>"
        return super().tool_tip(column)

    def _make_item_data(self):
        return {"name": "Type scenario alternative name here...", "description": ""}

    @property
    def item_data(self):
        if self.alternative_id is None:
            return self._make_item_data()
        return self.db_mngr.get_item(self.db_map, "alternative", self.alternative_id)

    @property
    def alternative_id(self):
        try:
            return self.parent_item.alternative_id_list[self.child_number()]
        except IndexError:
            return None

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()

    def flags(self, column):
        flags = super().flags(column) | Qt.ItemFlag.ItemNeverHasChildren
        if self.alternative_id is not None:
            flags |= Qt.ItemIsDragEnabled
        else:
            flags |= Qt.ItemIsEditable
        return flags

    def set_data(self, column, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or value == self.data(column, role):
            return False
        if self.alternative_id is not None:
            return False
        if column == 0:
            alternative_id_list = list(self.parent_item.alternative_id_list)
            alternative_id_list.append(value)
            db_item = {"id": self.parent_item.id, "alternative_id_list": alternative_id_list}
            self.db_mngr.set_scenario_alternatives({self.db_map: [db_item]})
        return True
