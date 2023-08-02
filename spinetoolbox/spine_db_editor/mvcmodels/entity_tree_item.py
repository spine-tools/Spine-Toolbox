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


class EntityRootItem(MultiDBTreeItem):
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


class ObjectTreeRootItem(EntityRootItem):
    """An object tree root item."""

    item_type = "root"

    @property
    def child_item_class(self):
        """Returns ObjectClassItem."""
        return ObjectClassItem


class RelationshipTreeRootItem(EntityRootItem):
    """A relationship tree root item."""

    item_type = "root"

    @property
    def child_item_class(self):
        """Returns RelationshipClassItem."""
        return RelationshipClassItem


class EntityClassItem(MultiDBTreeItem):
    """An entity_class item."""

    @property
    def display_icon(self):
        """Returns class icon."""
        return self._display_icon()

    def _display_icon(self, for_group=False):
        return self.db_mngr.entity_class_icon(
            self.first_db_map, self.item_type, self.db_map_id(self.first_db_map), for_group=for_group
        )

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


class ObjectClassItem(EntityClassItem):
    """An object_class item."""

    item_type = "object_class"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_group_fetch_parent = FlexibleFetchParent(
            "entity_group",
            accepts_item=self._accepts_entity_group_item,
            handle_items_added=self._handle_entity_group_items_added,
            handle_items_updated=self._handle_entity_group_items_updated,
            owner=self,
        )

    @property
    def child_item_class(self):
        """Returns ObjectItem."""
        return ObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(object_class_name=self.display_data, database=self.first_db_map.codename)

    @property
    def _children_sort_key(self):
        """Reimplemented so groups are above non-groups."""
        return lambda item: (not item.is_group, item.display_id)

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

    def _accepts_entity_group_item(self, item, db_map):
        return item["class_id"] == self.db_map_id(db_map)

    def _handle_entity_group_items_added(self, db_map_data):
        self._fetch_more_entity_groups()
        db_map_ids = {db_map: [x["group_id"] for x in data] for db_map, data in db_map_data.items()}
        self.update_children_by_id(db_map_ids, is_group=True)

    def _handle_entity_group_items_updated(self, db_map_data):
        db_map_ids = {db_map: [x["group_id"] for x in data] for db_map, data in db_map_data.items()}
        self.update_children_by_id(db_map_ids, is_group=True)

    def tear_down(self):
        super().tear_down()
        self._entity_group_fetch_parent.set_obsolete(True)

    def revitalize(self):
        """See base class"""
        super().revitalize()
        self._entity_group_fetch_parent.set_obsolete(False)


class RelationshipClassItem(EntityClassItem):
    """A relationship_class item."""

    visual_key = ["name", "object_class_name_list"]
    item_type = "relationship_class"

    @property
    def child_item_class(self):
        """Returns RelationshipItem."""
        return RelationshipItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(relationship_class_name=self.display_data, database=self.first_db_map.codename)


class ObjectRelationshipClassItem(RelationshipClassItem):
    def set_data(self, column, value, role):
        """See base class."""
        return False

    def accepts_item(self, item, db_map):
        if not super().accepts_item(item, db_map):
            return False
        object_id = self.parent_item.db_map_id(db_map)
        return object_id in item["object_id_list"]


class MembersItem(EntityClassItem):
    """An item to hold members of a group."""

    item_type = "members"

    @property
    def display_id(self):
        # Return an empty tuple so we never insert anything above this item (see _insert_children_sorted)
        return ()

    @property
    def display_data(self):
        return "members"

    def db_map_data(self, db_map):
        """Returns data for this item as if it was indeed an object class."""
        id_ = self.db_map_id(db_map)
        return self.db_mngr.get_item(db_map, "object_class", id_)

    def _display_icon(self, for_group=False):
        """Returns icon for this item as if it was indeed an object class."""
        return self.db_mngr.entity_class_icon(
            self.first_db_map, "object_class", self.db_map_id(self.first_db_map), for_group=False
        )

    def accepts_item(self, item, db_map):
        return item["group_id"] == self.parent_item.db_map_id(db_map)

    @property
    def child_item_class(self):
        """Returns MemberObjectItem."""
        return MemberObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict()

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ItemDataRole.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(column, role)


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    def __init__(self, *args, is_group=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_group = is_group
        self.has_members_item = False

    def update(self, is_group=False):
        self.is_group = is_group

    def should_be_merged(self):
        return self.is_group

    @property
    def display_icon(self):
        """Returns corresponding class icon."""
        return self.parent_item._display_icon(for_group=self.is_group)

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        return super().data(column, role)

    def set_data(self, column, value, role):
        """See base class."""
        return False

    def _can_fetch_members_item(self):
        return self.is_group and not self.has_members_item

    def _fetch_members_item(self):
        if self._can_fetch_members_item():
            self.has_members_item = True
            # Insert members item. Note that we pass the db_map_ids of the parent object class item
            self.insert_children(0, [MembersItem(self.model, self.parent_item.db_map_ids.copy())])

    def can_fetch_more(self):
        return super().can_fetch_more() or self._can_fetch_members_item()

    def fetch_more(self):
        super().fetch_more()
        self._fetch_members_item()


class ObjectItem(EntityItem):
    """An object item."""

    item_type = "object"

    @property
    def child_item_class(self):
        """Child class is always :class:`ObjectRelationshipClassItem`."""
        return ObjectRelationshipClassItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            object_class_name=self.db_map_data_field(self.first_db_map, "class_name"),
            object_name=self.display_data,
            database=self.first_db_map.codename,
        )

    def accepts_item(self, item, db_map):
        if not super().accepts_item(item, db_map):
            return False
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        return object_class_id in item["object_class_id_list"]


class MemberObjectItem(ObjectItem):
    """A member object item."""

    item_type = "entity_group"
    visual_key = ["member_name"]

    @property
    def display_icon(self):
        return self.parent_item.display_icon

    @property
    def display_data(self):
        """ "Returns the name for display."""
        return self.db_map_data_field(self.first_db_map, "member_name")

    def has_children(self):
        return False

    def can_fetch_more(self):
        return False


class RelationshipItem(EntityItem):
    """A relationship item."""

    visual_key = ["name", "object_name_list"]
    item_type = "relationship"

    def __init__(self, *args, **kwargs):
        """Overridden method to make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True

    @property
    def object_name_list(self):
        return self.db_map_data_field(self.first_db_map, "object_name_list", default="")

    @property
    def display_data(self):
        """ "Returns the name for display."""
        return DB_ITEM_SEPARATOR.join(
            [x for x in self.object_name_list if x != self.parent_item.parent_item.display_data]
        )

    @property
    def edit_data(self):
        return DB_ITEM_SEPARATOR.join(self.object_name_list)

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            relationship_class_name=self.parent_item.display_data,
            object_name_list=DB_ITEM_SEPARATOR.join(self.object_name_list),
            database=self.first_db_map.codename,
        )

    def has_children(self):
        return False

    def can_fetch_more(self):
        return False

    def is_valid(self):
        """Checks that the grand parent object is still in the relationship."""
        grand_parent = self.parent_item.parent_item
        if grand_parent.item_type == "root":
            return True
        return grand_parent.display_data in self.object_name_list
