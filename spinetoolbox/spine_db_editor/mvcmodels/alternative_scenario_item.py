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
Classes to represent alternative and scenario items in a tree.

:authors: P. Vennström (VTT)
:date:    17.6.2020
"""
from PySide2.QtCore import Qt
from .tree_item_utility import GrayIfLastMixin, EditableMixin, EmptyChildRootItem, LeafItem, StandardTreeItem

_ALTERNATIVE_ICON = "\uf277"  # map-signs
_SCENARIO_ICON = "\uf008"  # film


class AlternativeRootItem(EmptyChildRootItem):
    """An alternative root item."""

    @property
    def item_type(self):
        return "alternative"

    @property
    def display_data(self):
        return "alternative"

    @property
    def icon_code(self):
        return _ALTERNATIVE_ICON

    def empty_child(self):
        return AlternativeLeafItem()


class ScenarioRootItem(EmptyChildRootItem):
    """A scenario root item."""

    @property
    def item_type(self):
        return "scenario"

    @property
    def display_data(self):
        return "scenario"

    @property
    def icon_code(self):
        return _SCENARIO_ICON

    def empty_child(self):
        return ScenarioLeafItem()


class AlternativeLeafItem(GrayIfLastMixin, EditableMixin, LeafItem):
    """An alternative leaf item."""

    @property
    def item_type(self):
        return "alternative"

    @property
    def tool_tip(self):
        return (
            "<p>Drag this item and drop it onto a <b>scenario_alternative</b> item below to create a scenario"
            " alternative</p>"
        )

    def add_item_to_db(self, db_item):
        self.db_mngr.add_alternatives({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_alternatives({self.db_map: [db_item]})

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled


class ScenarioLeafItem(GrayIfLastMixin, EditableMixin, LeafItem):
    """A scenario leaf item."""

    @property
    def item_type(self):
        return "scenario"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_scenarios({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_scenarios({self.db_map: [db_item]})

    @property
    def scenario_alternative_root_item(self):
        return self.child(1)

    def _do_finalize(self):
        if not self.id:
            return
        super()._do_finalize()
        self.append_children([ScenarioActiveItem(), ScenarioAlternativeRootItem()])

    def handle_updated_in_db(self):
        super().handle_updated_in_db()
        self.scenario_alternative_root_item.update_alternative_id_list()


class ScenarioActiveItem(StandardTreeItem):
    @property
    def item_type(self):
        return "scenario active"

    def flags(self, column):
        flags = super().flags(column)
        if column == 0:
            flags |= Qt.ItemIsEditable
        return flags

    def data(self, column, role=Qt.DisplayRole):
        if column == 0 and role in (Qt.DisplayRole, Qt.EditRole):
            active = "yes" if self.parent_item.item_data["active"] else "no"
            return "active: " + active
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.EditRole):
        if role == Qt.EditRole and column == 0:
            active = {"yes": True, "no": False}.get(value)
            if active is None:
                return False
            db_item = {"id": self.parent_item.id, "active": active}
            self.parent_item.update_item_in_db(db_item)
            return True
        return False


class ScenarioAlternativeRootItem(EmptyChildRootItem):
    """A scenario alternative root item."""

    def empty_child(self):
        return ScenarioAlternativeLeafItem()

    @property
    def item_type(self):
        return "scenario_alternative"

    @property
    def display_data(self):
        return "scenario_alternative"

    @property
    def tool_tip(self):
        return "<p>Drag an <b>alternative</b> item from above and drop it here to create a scenario alternative</p>"

    @property
    def icon_code(self):
        return _ALTERNATIVE_ICON

    @property
    def alternative_id_list(self):
        return self.db_mngr.get_scenario_alternative_id_list(self.db_map, self.parent_item.id)

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDropEnabled

    def update_alternative_id_list(self):
        alt_count = len(self.alternative_id_list)
        curr_alt_count = len(self.non_empty_children)
        if alt_count > curr_alt_count:
            added_count = alt_count - curr_alt_count
            children = [ScenarioAlternativeLeafItem() for _ in range(added_count)]
            self.insert_children(curr_alt_count, children)
        elif curr_alt_count > alt_count:
            removed_count = curr_alt_count - alt_count
            self.remove_children(alt_count, removed_count)


class ScenarioAlternativeLeafItem(GrayIfLastMixin, LeafItem):
    """A scenario alternative leaf item."""

    @property
    def item_type(self):
        return "scenario_alternative"

    @property
    def tool_tip(self):
        return "<p>Drag and drop this item to reorder scenario alternatives</p>"

    def _make_item_data(self):
        return {"name": "Type scenario alternative name here...", "description": ""}

    @property
    def item_data(self):
        if not self.alternative_id:
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
        flags = super().flags(column)
        if self.alternative_id:
            flags |= Qt.ItemIsDragEnabled
        else:
            flags |= Qt.ItemIsEditable
        return flags

    def set_data(self, column, value, role=Qt.EditRole):
        if role != Qt.EditRole or value == self.data(column, role):
            return False
        if self.alternative_id:
            return False
        if column == 0:
            alternative_id_list = self.parent_item.alternative_id_list
            alternative_id_list.append(value)
            db_item = {
                "id": self.parent_item.parent_item.id,
                "alternative_id_list": ",".join([str(id_) for id_ in alternative_id_list]),
            }
            self.db_mngr.set_scenario_alternatives({self.db_map: [db_item]})
        return True
