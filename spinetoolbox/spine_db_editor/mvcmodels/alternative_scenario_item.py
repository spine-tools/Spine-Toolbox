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
from PySide2.QtGui import QIcon
from .tree_item_utility import NonLazyTreeItem, LastGrayMixin, AllBoldMixin, EmptyChildMixin, EditableMixin
from ...helpers import CharIconEngine

_ALTERNATIVE_ICON = "\uf277"  # map-signs
_SCENARIO_ICON = "\uf008"  # film


class RootItem(EmptyChildMixin, AllBoldMixin, NonLazyTreeItem):
    """A root item."""

    @property
    def item_type(self):
        raise NotImplementedError

    @property
    def display_data(self):
        raise NotImplementedError

    @property
    def icon_code(self):
        raise NotImplementedError

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def display_icon(self):
        engine = CharIconEngine(self.icon_code, 0)
        return QIcon(engine.pixmap())

    def data(self, column, role=Qt.DisplayRole):
        if column != 0:
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.display_data
        if role == Qt.DecorationRole:
            return self.display_icon
        return super().data(column, role)

    def set_data(self, column, value, role):
        return False

    def empty_child(self):
        raise NotImplementedError


class LeafItem(NonLazyTreeItem):
    def __init__(self, identifier=None):
        super().__init__()
        self._id = identifier
        self._item_data = {"name": f"Type new {self.item_type} name here...", "description": ""}

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def tool_tip(self):
        return None

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def id(self):
        return self._id

    @property
    def item_data(self):
        if not self.id:
            return self._item_data
        return self.db_mngr.get_item(self.db_map, self.item_type, self.id)

    @property
    def name(self):
        return self.item_data["name"]

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()

    def header_data(self, column):
        return self.model.headerData(column, Qt.Horizontal)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            data = self.item_data.get(self.header_data(column))
            if data is None:
                data = ""
            return data
        if role == Qt.ToolTipRole:
            return self.tool_tip
        return super().data(column, role)

    def set_data(self, column, value, role):
        if role != Qt.EditRole or value == self.data(column, role):
            return False
        if self.id:
            field = self.header_data(column)
            db_item = {"id": self.id, field: value}
            self.update_item_in_db(db_item)
            return True
        if column == 0:
            db_item = dict(name=value, description=self._item_data["description"])
            self.add_item_to_db(db_item)
        return True

    def handle_updated_in_db(self):
        index = self.index()
        sibling = self.index().sibling(self.index().row(), 1)
        self.model.dataChanged.emit(index, sibling)


class AlternativeRootItem(RootItem):
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


class ScenarioRootItem(RootItem):
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
        return "<p>Drag this item and drop it onto a <b>scenario</b> item below to create a scenario alternative</p>"

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

    @property
    def tool_tip(self):
        return "<p>Drag an <b>alternative</b> item from above and drop it here to create a scenario alternative</p>"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_scenarios({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_scenarios({self.db_map: [db_item]})

    def flags(self, column):
        flags = super().flags(column)
        if self.id:
            flags |= Qt.ItemIsDropEnabled
        if column == 0:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.CheckStateRole and column == 0 and self.child_number() != self.parent_item.child_count() - 1:
            is_active = self.item_data["active"]
            return Qt.Checked if is_active else Qt.Unchecked
        return super().data(column, role)

    def set_data(self, column, value, role):
        if role == Qt.CheckStateRole and column == 0 and self.child_number() != self.parent_item.child_count() - 1:
            db_item = {"id": self.id, "active": value == Qt.Checked}
            self.update_item_in_db(db_item)
            return True
        return super().set_data(column, value, role)

    @property
    def alternative_id_list(self):
        alternative_id_list = self.item_data.get("alternative_id_list")
        if not alternative_id_list:
            return []
        return [int(id_) for id_ in alternative_id_list.split(",")]

    def fetch_more(self):
        children = [ScenarioAlternativeLeafItem() for _ in self.alternative_id_list]
        self.append_children(*children)
        self._fetched = True

    def handle_updated_in_db(self):
        super().handle_updated_in_db()
        self._update_alternative_id_list()

    def _update_alternative_id_list(self):
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
