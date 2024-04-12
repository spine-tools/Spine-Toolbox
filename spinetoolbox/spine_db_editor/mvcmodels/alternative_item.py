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

"""Classes to represent items in an alternative tree."""
from PySide6.QtCore import Qt
from .tree_item_utility import EmptyChildMixin, FetchMoreMixin, GrayIfLastMixin, EditableMixin, LeafItem, StandardDBItem

_ALTERNATIVE_ICON = "\uf277"  # map-signs


class DBItem(EmptyChildMixin, FetchMoreMixin, StandardDBItem):
    """A root item representing a db."""

    @property
    def item_type(self):
        return "db"

    @property
    def fetch_item_type(self):
        return "alternative"

    def empty_child(self):
        return AlternativeItem(self._model)

    def _make_child(self, id_):
        return AlternativeItem(self._model, id_)


class AlternativeItem(GrayIfLastMixin, EditableMixin, LeafItem):
    """An alternative leaf item."""

    @property
    def item_type(self):
        return "alternative"

    @property
    def icon_code(self):
        return _ALTERNATIVE_ICON

    def tool_tip(self, column):
        if column == 0 and self.id:
            return "<p>Drag this item on a <b>scenario</b> item in Scenario tree to add it to that scenario.</p>"
        return super().tool_tip(column)

    def add_item_to_db(self, db_item):
        self.db_mngr.add_alternatives({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_alternatives({self.db_map: [db_item]})

    def flags(self, column):
        flags = super().flags(column)
        if self.id is None:
            return flags
        return flags | Qt.ItemFlag.ItemIsDragEnabled
