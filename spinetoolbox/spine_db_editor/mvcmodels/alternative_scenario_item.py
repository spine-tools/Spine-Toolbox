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
Classes to represent alternative and scenario items in a tree.

:authors: P. Vennström (VTT)
:date:    17.6.2020
"""
from PySide2.QtCore import Qt
from .tree_item_utility import LastGrayMixin, EditableMixin, RootItem, EmptyChildRootItem, LeafItem, NonLazyTreeItem

_ALTERNATIVE_ICON = "\uf277"  # map-signs
_SCENARIO_ICON = "\uf008"  # film


class AlternativeRootItem(EmptyChildRootItem):
    """An alternative root item."""

    @property
    def item_type(self):
        return "alternative root"

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
        return "scenario root"

    @property
    def display_data(self):
        return "scenario"

    @property
    def icon_code(self):
        return _SCENARIO_ICON

    def empty_child(self):
        return ScenarioLeafItem()


class AlternativeLeafItem(LastGrayMixin, EditableMixin, LeafItem):
    """An alternative leaf item."""

    @property
    def item_type(self):
        return "alternative"

    @property
    def tool_tip(self):
        return "<p>Drag this item and drop it onto a <b>scenario_alternative</b> item below to create a scenario alternative</p>"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_alternatives({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_alternatives({self.db_map: [db_item]})

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled


class ScenarioLeafItem(LastGrayMixin, EditableMixin, LeafItem):
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

    def fetch_more(self):
        if not self.id:
            return
        self.append_children(ScenarioActiveItem(), ScenarioAlternativeRootItem())
        self._fetched = True

    def handle_updated_in_db(self):
        super().handle_updated_in_db()
        self.scenario_alternative_root_item.update_alternative_id_list()


class ScenarioActiveItem(NonLazyTreeItem):
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

    def set_data(self, column, value, role):
        if role == Qt.EditRole and column == 0:
            active = {"yes": True, "no": False}.get(value)
            if active is None:
                return False
            db_item = {"id": self.parent_item.id, "active": active}
            self.parent_item.update_item_in_db(db_item)
            return True
        return False


class ScenarioAlternativeRootItem(RootItem):
    """A scenario alternative root item."""

    @property
    def item_type(self):
        return "scenario_alternative root"

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
        alternative_id_list = self.parent_item.item_data.get("alternative_id_list")
        if not alternative_id_list:
            return []
        return [int(id_) for id_ in alternative_id_list.split(",")]

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDropEnabled

    def fetch_more(self):
        children = [ScenarioAlternativeLeafItem() for _ in self.alternative_id_list]
        self.append_children(*children)
        self._fetched = True

    def update_alternative_id_list(self):
        alt_count = len(self.alternative_id_list)
        curr_alt_count = self.child_count()
        if alt_count > curr_alt_count:
            added_count = alt_count - curr_alt_count
            children = [ScenarioAlternativeLeafItem() for _ in range(added_count)]
            self.insert_children(curr_alt_count, *children)
        elif curr_alt_count > alt_count:
            removed_count = curr_alt_count - alt_count
            self.remove_children(alt_count, removed_count)


class ScenarioAlternativeLeafItem(LeafItem):
    """A scenario alternative leaf item."""

    @property
    def item_type(self):
        return "alternative"

    @property
    def tool_tip(self):
        return "<p>Drag and drop this item to reorder scenario alternatives</p>"

    @property
    def id(self):
        return self.parent_item.alternative_id_list[self.child_number()]

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled
