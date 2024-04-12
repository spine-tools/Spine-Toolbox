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

"""Tree items for parameter_value lists."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from spinetoolbox.mvcmodels.shared import PARSED_ROLE
from .tree_item_utility import (
    EmptyChildMixin,
    GrayIfLastMixin,
    BoldTextMixin,
    EditableMixin,
    StandardDBItem,
    FetchMoreMixin,
    SortChildrenMixin,
    LeafItem,
)
from ...helpers import CharIconEngine


class DBItem(EmptyChildMixin, FetchMoreMixin, StandardDBItem):
    """An item representing a db."""

    @property
    def item_type(self):
        return "db"

    @property
    def fetch_item_type(self):
        return "parameter_value_list"

    def empty_child(self):
        return ListItem(self._model)

    def _make_child(self, id_):
        return ListItem(self._model, id_)


class ListItem(
    GrayIfLastMixin, EditableMixin, EmptyChildMixin, SortChildrenMixin, BoldTextMixin, FetchMoreMixin, LeafItem
):
    """A list item."""

    @property
    def item_type(self):
        return "parameter_value_list"

    @property
    def fetch_item_type(self):
        return "list_value"

    def _make_item_data(self):
        return {"name": "Type new list name here..."}

    def _do_set_up(self):
        if not self.id:
            return
        super()._do_set_up()

    # pylint: disable=no-self-use
    def empty_child(self):
        return ValueItem(self._model)

    def _make_child(self, id_):
        return ValueItem(self._model, id_)

    def accepts_item(self, item, db_map):
        return item["parameter_value_list_id"] == self.id

    def _children_sort_key(self, child):
        return self.db_mngr.get_item(self.db_map, "list_value", child.id)["index"]

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DecorationRole:
            engine = CharIconEngine("\uf022", 0)
            return QIcon(engine.pixmap())
        return super().data(column, role)

    def _make_item_to_add(self, value):
        return dict(name=value)

    def add_item_to_db(self, db_item):
        self.db_mngr.add_parameter_value_lists({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_parameter_value_lists({self.db_map: [db_item]})


class ValueItem(GrayIfLastMixin, EditableMixin, LeafItem):
    @property
    def item_type(self):
        return "list_value"

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and not self.id:
            return "Enter new list value here..."
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole, PARSED_ROLE):
            return self.db_mngr.get_value(self.db_map, self.item_type, self.id, role=role)
        return super().data(column, role)

    def list_index(self):
        return self.db_mngr.get_item(self.db_map, self.item_type, self.id)["index"]

    def _make_item_to_add(self, value):
        db_value, db_type = value
        index = 0 if self.child_number() == 0 else self.parent_item.child(self.child_number() - 1).list_index() + 1
        return dict(value=db_value, type=db_type, parameter_value_list_id=self.parent_item.id, index=index)

    def _make_item_to_update(self, _column, value):
        db_value, db_type = value
        return dict(id=self.id, value=db_value, type=db_type)

    def add_item_to_db(self, db_item):
        self.db_mngr.add_list_values({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_list_values({self.db_map: [db_item]})
