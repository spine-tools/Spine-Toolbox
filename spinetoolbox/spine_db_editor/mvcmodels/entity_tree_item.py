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

    def _get_children_ids(self, db_map):
        """See super class."""
        raise NotImplementedError()


class ObjectTreeRootItem(EntityRootItem):
    """An object tree root item."""

    item_type = "root"

    @property
    def child_item_type(self):
        """Returns ObjectClassItem."""
        return ObjectClassItem

    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """See super class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "object_class")]


class RelationshipTreeRootItem(EntityRootItem):
    """A relationship tree root item."""

    item_type = "root"

    @property
    def child_item_type(self):
        """Returns RelationshipClassItem."""
        return RelationshipClassItem

    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """See super class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "relationship_class")]


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

    def _get_children_ids(self, db_map):
        """See super class"""
        raise NotImplementedError()

    def fetch_more(self):
        """Fetches children from all associated databases and raises group children.
        """
        super().fetch_more()
        rows = [row for row, child in enumerate(self.children) if child.is_group()]
        self._raise_group_children_by_row(rows)

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
        self.insert_children(self._group_child_count, *group_children)
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


class ObjectClassItem(EntityClassItem):
    """An object_class item."""

    item_type = "object_class"

    @property
    def child_item_type(self):
        """Returns ObjectItem."""
        return ObjectItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(object_class_name=self.display_data, database=self.first_db_map.codename)

    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """see super class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "object") if x["class_id"] == self.db_map_id(db_map)]


class RelationshipClassItemBase(EntityClassItem):
    """A relationship_class item."""

    visual_key = ["name", "object_class_name_list"]
    item_type = "relationship_class"

    @property
    def child_item_type(self):
        """Returns RelationshipItem."""
        return RelationshipItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(relationship_class_name=self.display_data, database=self.first_db_map.codename)

    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()


class RelationshipClassItem(RelationshipClassItemBase):
    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """see super class."""
        return [
            x["id"] for x in self.db_mngr.get_items(db_map, "relationship") if x["class_id"] == self.db_map_id(db_map)
        ]


class ObjectRelationshipClassItem(RelationshipClassItemBase):
    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """see super class."""
        object_id = self.parent_item.db_map_id(db_map)
        return [
            x["id"]
            for items in self.db_mngr.find_cascading_relationships({db_map: {object_id}}).values()
            for x in items
            if x["class_id"] == self.db_map_id(db_map)
        ]


class EntityItem(MultiDBTreeItem):
    """An entity item."""

    @property
    def display_icon(self):
        """Returns corresponding class icon."""
        return self.parent_item._display_icon(for_group=self.is_group())

    def db_map_member_ids(self, db_map):
        return set(x["member_id"] for x in self.db_map_entity_groups(db_map))

    def db_map_entity_groups(self, db_map):
        return self.db_mngr.get_items_by_field(db_map, "entity_group", "entity_id", self.db_map_id(db_map))

    @property
    def member_ids(self):
        return {db_map: self.db_map_member_ids(db_map) for db_map in self.db_maps}

    @property
    def member_rows(self):
        return set(
            row
            for db_map in self.db_maps
            for row in self.parent_item.find_rows_by_id(db_map, *self.db_map_member_ids(db_map))
        )

    def is_group(self):
        return any(self.member_ids.values())

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            return self.db_map_data_field(self.first_db_map, "description")
        if role == Qt.BackgroundRole and column == 0 and self.model.is_active_member_index(self.index()):
            color = qApp.palette().highlight().color()  # pylint: disable=undefined-variable
            color.setAlphaF(0.2)
            return color
        return super().data(column, role)

    def _get_children_ids(self, db_map):
        """See base class."""
        raise NotImplementedError()


class ObjectItem(EntityItem):
    """An object item."""

    item_type = "object"

    @property
    def child_item_type(self):
        """Returns RelationshipClassItem."""
        return ObjectRelationshipClassItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            object_class_name=self.parent_item.display_data,
            object_name=self.display_data,
            database=self.first_db_map.codename,
        )

    def set_data(self, column, value, role):
        """See base class."""
        raise NotImplementedError()

    def _get_children_ids(self, db_map):
        """See base class"""
        object_class_id = self.db_map_data_field(db_map, 'class_id')
        return [
            x["id"]
            for items in self.db_mngr.find_cascading_relationship_classes({db_map: {object_class_id}}).values()
            for x in items
        ]


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
        return self.db_mngr._GROUP_SEP.join(
            [x for x in self.object_name_list.split(",") if x != self.parent_item.parent_item.display_data]
        )

    @property
    def edit_data(self):
        return self.object_name_list

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(
            relationship_class_name=self.parent_item.display_data,
            object_name_list=self.db_map_data_field(self.first_db_map, "object_name_list"),
            database=self.first_db_map.codename,
        )

    def can_fetch_more(self):
        return False

    def _get_children_ids(self, db_map):
        """See base class"""
        raise NotImplementedError()

    def is_valid(self):
        """Checks that the grand parent object is still in the relationship."""
        grand_parent = self.parent_item.parent_item
        if grand_parent.item_type == "root":
            return True
        return grand_parent.display_data in self.object_name_list.split(",")
