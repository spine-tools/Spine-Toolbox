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
Classes to represent entities in a tree.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   11.3.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QBrush, QIcon
from .multi_db_tree_item import MultiDBTreeItem


class EntityRootItem(MultiDBTreeItem):

    item_type = "root"

    @property
    def display_id(self):
        """"See super class."""
        return "root"

    @property
    def display_icon(self):
        return QIcon(":/symbols/Spine_symbol.png")

    @property
    def display_data(self):
        """"See super class."""
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

    def __init__(self, *args, **kwargs):
        """Overridden method to declare group_child_count attribute."""
        super().__init__(*args, **kwargs)
        self._group_child_count = 0

    @property
    def display_icon(self):
        """Returns class icon."""
        return self._display_icon()

    def _display_icon(self, for_group=False):
        return self.db_mngr.entity_class_icon(
            self.first_db_map, self.item_type, self.db_map_id(self.first_db_map), for_group=for_group
        )

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        if role == Qt.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        if role == Qt.ForegroundRole and column == 0:
            if not self.has_children():
                return QBrush(Qt.gray)
        return super().data(column, role)

    def raise_group_children_by_id(self, db_map_ids):
        """
        Moves group children to the top of the list.

        Args:
            db_map_ids (dict): set of ids corresponding to newly inserted group children,
                keyed by DiffDatabaseMapping
        """
        rows = set(row for db_map, ids in db_map_ids.items() for row in self.find_rows_by_id(db_map, *ids))
        self._raise_group_children_by_row(rows)

    def _raise_group_children_by_row(self, rows):
        """
        Moves group children to the top of the list.

        Args:
            rows (set, list): collection of rows corresponding to newly inserted group children
        """
        rows = [row for row in rows if row >= self._group_child_count]
        if not rows:
            return
        self.model.layoutAboutToBeChanged.emit()
        group_children = list(reversed([self.children.pop(row) for row in sorted(rows, reverse=True)]))
        self.insert_children(self._group_child_count, group_children)
        self.model.layoutChanged.emit()
        self._group_child_count += len(group_children)
        self._refresh_child_map()

    def remove_children(self, position, count):
        """
        Overriden method to keep the group child count up to date.
        """
        if not super().remove_children(position, count):
            return False
        first_group_child = position
        last_group_child = min(self._group_child_count - 1, position + count - 1)
        removed_child_count = last_group_child - first_group_child + 1
        if removed_child_count > 0:
            self._group_child_count -= removed_child_count
        return True

    def fetch_successful(self, db_map, item):
        return item["class_id"] == self.db_map_id(db_map)

    def set_data(self, column, value, role):
        """See base class."""
        return False


class ObjectClassItem(EntityClassItem):
    """An object_class item."""

    item_type = "object_class"

    @property
    def child_item_class(self):
        """Returns ObjectItem."""
        return ObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(object_class_name=self.display_data, database=self.first_db_map.codename)


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

    def fetch_successful(self, db_map, item):
        object_id = self.parent_item.db_map_id(db_map)
        return super().fetch_successful(db_map, item) and object_id in {
            int(id_) for id_ in item["object_id_list"].split(",")
        }


class MemberObjectClassItem(ObjectClassItem):
    """A member object class item."""

    item_type = "members"

    @property
    def display_id(self):
        # Return an empty tuple so we never insert anything before this item (see _insert_children_sorted)
        return ()

    @property
    def display_data(self):
        return "members"

    def db_map_data(self, db_map):
        """Returns data for this item as if it was indeed an object class."""
        id_ = self.db_map_id(db_map)
        return self.db_mngr.get_item(db_map, super().item_type, id_)

    def _display_icon(self, for_group=False):
        """Returns icon for this item as if it was indeed an object class."""
        return self.db_mngr.entity_class_icon(
            self.first_db_map, super().item_type, self.db_map_id(self.first_db_map), for_group=False
        )

    def fetch_successful(self, db_map, item):
        return item["class_id"] == self.db_map_id(db_map) and item["group_id"] == self.parent_item.db_map_id(db_map)

    @property
    def child_item_class(self):
        """Returns MemberObjectItem."""
        return MemberObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict()

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.FontRole and column == 0:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(column, role)


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    _has_members_item = False

    @property
    def members_item(self):
        if not self._has_members_item:
            # Insert members item. Note that we pass the db_map_ids of the parent object class item
            self.insert_children(0, [MemberObjectClassItem(self.model, self.parent_item.db_map_ids.copy())])
            self._has_members_item = True
        return self.child(0)

    @property
    def display_icon(self):
        """Returns corresponding class icon."""
        return self.parent_item._display_icon(for_group=self.is_group())

    def db_map_member_ids(self, db_map):
        return [x["member_id"] for x in self.db_map_entity_groups(db_map)]

    def db_map_entity_groups(self, db_map):
        # FIXME: We might need to fetch here
        return self.db_mngr.get_items_by_field(db_map, "entity_group", "group_id", self.db_map_id(db_map))

    def is_group(self):
        return self.members_item.has_children()

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        return super().data(column, role)

    def set_data(self, column, value, role):
        """See base class."""
        return False


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

    def fetch_successful(self, db_map, item):
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        return object_class_id in {int(id_) for id_ in item["object_class_id_list"].split(",")}


class MemberObjectItem(ObjectItem):
    """A member object item."""

    item_type = "entity_group"
    visual_key = ["member_name"]

    @property
    def display_icon(self):
        return self.parent_item.display_icon

    @property
    def display_data(self):
        """"Returns the name for display."""
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
        """"Returns the name for display."""
        return self.db_mngr.GROUP_SEP.join(
            [x for x in self.object_name_list.split(",") if x != self.parent_item.parent_item.display_data]
        )

    @property
    def edit_data(self):
        return self.object_name_list

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            relationship_class_name=self.parent_item.display_data,
            object_name_list=self.db_map_data_field(self.first_db_map, "object_name_list"),
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
        return grand_parent.display_data in self.object_name_list.split(",")
