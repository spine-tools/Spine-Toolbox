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

"""Classes to represent entities in a tree."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QBrush, QIcon
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, plain_to_tool_tip
from spinetoolbox.fetch_parent import FlexibleFetchParent, FetchIndex
from .multi_db_tree_item import MultiDBTreeItem


class EntityClassIndex(FetchIndex):
    def process_item(self, item, db_map):
        class_id = item["class_id"]
        self.setdefault(db_map, {}).setdefault(class_id, []).append(item)


class EntityGroupIndex(FetchIndex):
    def process_item(self, item, db_map):
        group_id = item["group_id"]
        self.setdefault(db_map, {}).setdefault(group_id, []).append(item)


class EntityIndex(FetchIndex):
    def process_item(self, item, db_map):
        element_id_list = item["element_id_list"]
        for el_id in element_id_list:
            self.setdefault(db_map, {}).setdefault(el_id, []).append(item)


class EntityTreeRootItem(MultiDBTreeItem):
    item_type = "root"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_children_initially = True

    @property
    def visible_children(self):
        return [x for x in self.children if not x.is_hidden()]

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

    def _polish_children(self, children):
        """See base class."""
        db_map_entity_class_ids = {
            db_map: {x["class_id"] for x in self.db_mngr.get_items(db_map, "entity")} for db_map in self.db_maps
        }
        for child in children:
            child.set_has_children_initially(
                any(child.db_map_id(db_map) in db_map_entity_class_ids.get(db_map, ()) for db_map in child.db_maps)
            )


class EntityClassItem(MultiDBTreeItem):
    """An entity_class item."""

    visual_key = ["name", "dimension_name_list", "superclass_name"]
    item_type = "entity_class"
    _fetch_index = EntityClassIndex()

    @property
    def display_icon(self):
        """Returns class icon."""
        return self.db_mngr.entity_class_icon(self.first_db_map, self.db_map_id(self.first_db_map))

    @property
    def child_item_class(self):
        return EntityItem

    def is_hidden(self):
        return self.model.hide_empty_classes and not self.has_children()

    @property
    def _children_sort_key(self):
        """Reimplemented so groups are above non-groups."""
        return lambda item: (not item.is_group, item.display_id)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(entity_class_name=self.name, database=self.first_db_map.codename)

    @property
    def display_data(self):
        """Returns the name for display."""
        name = self.name
        superclass_name = self.db_map_data_field(self.first_db_map, "superclass_name")
        if superclass_name:
            name += f"({superclass_name})"
        return name

    @property
    def has_dimensions(self):
        return bool(self.db_map_data_field(self.first_db_map, "dimension_id_list"))

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ItemDataRole.ToolTipRole:
            return plain_to_tool_tip(self.db_map_data_field(self.first_db_map, "description"))
        if column == 0:
            if role == Qt.ItemDataRole.FontRole:
                bold_font = QFont()
                bold_font.setBold(True)
                return bold_font
            if role == Qt.ItemDataRole.ForegroundRole:
                if not self.has_children():
                    return QBrush(Qt.gray)
        return super().data(column, role)

    def _key_for_index(self, db_map):
        return self.db_map_id(db_map)

    def accepts_item(self, item, db_map):
        return item["class_id"] == self.db_map_id(db_map)

    def set_data(self, column, value, role):
        """See base class."""
        return False

    def _polish_children(self, children):
        """See base class."""
        db_map_entity_element_ids = {
            db_map: {el_id for ent in self.db_mngr.get_items(db_map, "entity") for el_id in ent["element_id_list"]}
            for db_map in self.db_maps
        }
        for child in children:
            child.set_has_children_initially(
                any(child.db_map_id(db_map) in db_map_entity_element_ids.get(db_map, ()) for db_map in child.db_maps)
            )


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    visual_key = ["entity_class_name", "entity_byname"]
    item_type = "entity"
    _fetch_index = EntityIndex()
    _entity_group_index = EntityGroupIndex()

    def __init__(self, *args, is_member=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_group = False
        self._is_member = is_member
        self._entity_group_fetch_parent = FlexibleFetchParent(
            "entity_group",
            accepts_item=self._accepts_entity_group_item,
            handle_items_added=self._handle_entity_group_items_added,
            handle_items_removed=self._handle_entity_group_items_removed,
            index=self._entity_group_index,
            key_for_index=self._key_for_entity_group_index,
            owner=self,
        )

    @property
    def is_group(self):
        if not self._is_group and self._can_fetch_more_entity_groups():
            self._fetch_more_entity_groups()
        return self._is_group

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
        return self.db_map_data_field(self.first_db_map, "element_name_list", default=())

    @property
    def element_byname_list(self):
        return self.db_map_data_field(self.first_db_map, "element_byname_list", default=())

    @property
    def byname(self):
        return self.db_map_data_field(self.first_db_map, "entity_byname", default=())

    @property
    def entity_class_name(self):
        return self.db_map_data_field(self.first_db_map, "entity_class_name", default="")

    @property
    def entity_class_key(self):
        return tuple(
            self.db_map_data_field(self.first_db_map, field) for field in ("entity_class_name", "dimension_name_list")
        )

    @property
    def display_data(self):
        element_byname_list = self.element_byname_list
        if element_byname_list:
            element_byname_list = [
                x
                if not isinstance(self.parent_item, EntityItem) or x != self.parent_item.byname
                else ["\u066D"] * len(x)
                for x in element_byname_list
            ]
            return DB_ITEM_SEPARATOR.join([DB_ITEM_SEPARATOR.join(x) for x in element_byname_list])
        return self.name

    @property
    def edit_data(self):
        return DB_ITEM_SEPARATOR.join(self.byname)

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ToolTipRole:
            return plain_to_tool_tip(self.db_map_data_field(self.first_db_map, "description"))
        return super().data(column, role)

    def set_data(self, column, value, role):
        """See base class."""
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            entity_class_name=self.db_map_data_field(self.first_db_map, "entity_class_name"),
            entity_byname=DB_ITEM_SEPARATOR.join(self.db_map_data_field(self.first_db_map, "entity_byname")),
            database=self.first_db_map.codename,
        )

    def is_valid(self):
        """See base class.

        Additionally, checks that the parent entity (if any) is still an element in this entity.
        """
        if not super().is_valid():
            return False
        if self.parent_item.item_type == "entity_class":
            return True
        if self._is_member:
            return True
        return self.parent_item.name in self.element_name_list

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

    def _key_for_index(self, db_map):
        return self.db_map_id(db_map)

    def _key_for_entity_group_index(self, db_map):
        return self.db_map_id(db_map)

    def accepts_item(self, item, db_map):
        return self.db_map_id(db_map) in item["element_id_list"]

    def _accepts_entity_group_item(self, item, db_map):
        return item["group_id"] == self.db_map_id(db_map)

    def _handle_entity_group_items_added(self, db_map_data):
        db_map_member_ids = {db_map: [x["member_id"] for x in data] for db_map, data in db_map_data.items()}
        self.append_children_by_id(db_map_member_ids, is_member=True)
        if not self._is_group:
            self._is_group = True
            self.parent_item.reposition_child(self.child_number())

    def _handle_entity_group_items_removed(self, db_map_data):
        db_map_ids = {db_map: [x["member_id"] for x in data] for db_map, data in db_map_data.items()}
        self.remove_children_by_id(db_map_ids)
        if not any(self.db_mngr.get_item(db_map, "entity", self.db_map_id(db_map)) for db_map in self.db_maps):
            # Not an entity anymore
            return
        if self._is_group:
            if any(
                self.db_mngr.get_items_by_field(db_map, "entity_group", "group_id", self.db_map_id(db_map))
                for db_map in self.db_maps
            ):
                # Still a group
                return
            self._is_group = False
            self.parent_item.reposition_child(self.child_number())

    def tear_down(self):
        super().tear_down()
        self._entity_group_fetch_parent.set_obsolete(True)
