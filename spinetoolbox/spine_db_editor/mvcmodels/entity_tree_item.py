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

"""
Classes to represent entities in a tree.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QBrush, QIcon

from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.fetch_parent import FlexibleFetchParent
from .multi_db_tree_item import MultiDBTreeItem


class EntityTreeRootItem(MultiDBTreeItem):
    item_type = "root"

    @property
    def display_id(self):
        """See super class."""
        return "root"

    @property
    def display_icon(self):
        return QIcon(":/symbols/Spine_symbol.png")

    @property
    def display_data(self):
        """See super class."""
        return "root"

    def set_data(self, column, value, role):
        """See base class."""
        return False

    @property
    def child_item_class(self):
        """Returns ObjectClassItem."""
        return EntityClassItem


class _FetchEntityGroupMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_group_fetch_parent = FlexibleFetchParent(
            "entity_group",
            accepts_item=self._accepts_entity_group_item,
            handle_items_added=self._handle_entity_group_items_added,
            handle_items_updated=self._handle_entity_group_items_updated,
            handle_items_removed=self._handle_entity_group_items_removed,
            owner=self,
        )

    def _accepts_entity_group_item(self, item, db_map):
        raise NotImplementedError()

    def _handle_entity_group_items_added(self, db_map_data):
        raise NotImplementedError()

    def _handle_entity_group_items_updated(self, db_map_data):
        raise NotImplementedError()

    def _handle_entity_group_items_removed(self, db_map_data):
        raise NotImplementedError()

    def _can_fetch_more_entity_groups(self):
        result = False
        for db_map in self.db_maps:
            result |= self.db_mngr.can_fetch_more(db_map, self._entity_group_fetch_parent)
        return result

    def can_fetch_more(self):
        result = self._can_fetch_more_entity_groups()
        result |= super().can_fetch_more()
        return result

    def _fetch_more_entity_groups(self):
        for db_map in self.db_maps:
            self.db_mngr.fetch_more(db_map, self._entity_group_fetch_parent)

    def fetch_more(self):
        self._fetch_more_entity_groups()
        super().fetch_more()

    def tear_down(self):
        super().tear_down()
        self._entity_group_fetch_parent.set_obsolete(True)


class EntityClassItem(_FetchEntityGroupMixin, MultiDBTreeItem):
    """An entity_class item."""

    visual_key = ["name", "dimension_name_list"]
    item_type = "entity_class"

    @property
    def display_icon(self):
        """Returns class icon."""
        return self.db_mngr.entity_class_icon(self.first_db_map, self.db_map_id(self.first_db_map))

    @property
    def child_item_class(self):
        return EntityItem

    def is_hidden(self):
        return self.model.hide_empty_classes and not self.can_fetch_more() and not self.child_count()

    @property
    def _children_sort_key(self):
        """Reimplemented so groups are above non-groups."""
        return lambda item: (not item.is_group, item.display_id)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(entity_class_name=self.display_data, database=self.first_db_map.codename)

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        if role == Qt.ItemDataRole.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        if role == Qt.ForegroundRole and column == 0:
            if not self.has_children():
                return QBrush(Qt.gray)
        return super().data(column, role)

    def accepts_item(self, item, db_map):
        return item["class_id"] == self.db_map_id(db_map)

    def set_data(self, column, value, role):
        """See base class."""
        return False

    def _accepts_entity_group_item(self, item, db_map):
        return item["class_id"] == self.db_map_id(db_map)

    def _handle_entity_group_items_added(self, db_map_data):
        self._fetch_more_entity_groups()
        db_map_ids = {db_map: [x["group_id"] for x in data] for db_map, data in db_map_data.items()}
        self.update_children_by_id(db_map_ids, is_group=True)

    def _handle_entity_group_items_updated(self, db_map_data):
        pass

    def _handle_entity_group_items_removed(self, db_map_data):
        pass


class EntityItem(_FetchEntityGroupMixin, MultiDBTreeItem):
    """An entity item."""

    visual_key = ["class_name", "byname"]
    item_type = "entity"

    def __init__(self, *args, is_group=False, is_member=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_group = is_group
        self.is_member = is_member

    @property
    def child_item_class(self):
        """Child class is always :class:`EntityItem`."""
        return EntityItem

    @property
    def display_icon(self):
        """Returns corresponding class icon."""
        return self.db_mngr.entity_class_icon(
            self.first_db_map, self.db_map_data_field(self.first_db_map, "class_id"), for_group=self.is_group
        )

    @property
    def element_name_list(self):
        return self.db_map_data_field(self.first_db_map, "element_name_list", default="")

    @property
    def entity_class_key(self):
        return tuple(
            self.db_map_data_field(self.first_db_map, field) for field in ("class_name", "dimension_name_list")
        )

    @property
    def display_data(self):
        byname = self.db_map_data_field(self.first_db_map, "byname", default="")
        if self.is_member:
            return "member: " + DB_ITEM_SEPARATOR.join(byname)
        if self.parent_item.item_type == "entity":
            class_name = self.db_map_data_field(self.first_db_map, "class_name", default="")
            byname = [x if x != self.parent_item.display_data else "\u2022" for x in byname]
            return class_name + "[ " + DB_ITEM_SEPARATOR.join(byname) + " ]"
        return DB_ITEM_SEPARATOR.join(byname)

    @property
    def edit_data(self):
        return DB_ITEM_SEPARATOR.join(self.element_name_list)

    def update(self, is_group=False, is_member=False):
        self.is_group = is_group
        self.is_member = is_member

    def will_always_be_merged(self):
        return self.is_group

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        return super().data(column, role)

    def set_data(self, column, value, role):
        """See base class."""
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            entity_class_name=self.db_map_data_field(self.first_db_map, "class_name"),
            entity_byname=DB_ITEM_SEPARATOR.join(self.db_map_data_field(self.first_db_map, "byname")),
            database=self.first_db_map.codename,
        )

    def is_valid(self):
        """Checks that the parent entity (if any) is still an element in this entity."""
        if self.parent_item.item_type == "entity_class":
            return True
        return self.parent_item.display_data in self.element_name_list

    def accepts_item(self, item, db_map):
        return self.db_map_id(db_map) in item["element_id_list"]

    def _accepts_entity_group_item(self, item, db_map):
        return item["group_id"] == self.db_map_id(db_map)

    def _handle_entity_group_items_added(self, db_map_data):
        db_map_ids = {db_map: [x["member_id"] for x in data] for db_map, data in db_map_data.items()}
        self.append_children_by_id(db_map_ids, is_member=True)

    def _handle_entity_group_items_updated(self, db_map_data):
        pass

    def _handle_entity_group_items_removed(self, db_map_data):
        db_map_ids = {db_map: [x["member_id"] for x in data] for db_map, data in db_map_data.items()}
        self.remove_children_by_id(db_map_ids)
