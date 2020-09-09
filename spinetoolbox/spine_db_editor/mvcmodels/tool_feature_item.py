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
Classes to represent tool and feature items in a tree.

:authors: M. Marin (KTH)
:date:    1.9.2020
"""
from PySide2.QtCore import Qt
from .tree_item_utility import LastGrayMixin, EditableMixin, RootItem, LeafItem

_FEATURE_ICON = "\uf5bc"  # splotch
_TOOL_ICON = "\uf6e3"  # hammer


class FeatureRootItem(RootItem):
    """A feature root item."""

    @property
    def item_type(self):
        return "feature root"

    @property
    def display_data(self):
        return "feature"

    @property
    def icon_code(self):
        return _FEATURE_ICON

    def empty_child(self):
        return FeatureLeafItem()


class ToolRootItem(RootItem):
    """A tool root item."""

    @property
    def item_type(self):
        return "tool root"

    @property
    def display_data(self):
        return "tool"

    @property
    def icon_code(self):
        return _TOOL_ICON

    def empty_child(self):
        return ToolLeafItem()


class FeatureLeafItem(LastGrayMixin, EditableMixin, LeafItem):
    """A feature leaf item."""

    @property
    def item_type(self):
        return "feature"

    def _make_item_data(self):
        return {"name": "Enter new feature here...", "description": ""}

    @property
    def item_data(self):
        if not self.id:
            return self._item_data
        item_data = self.db_mngr.get_item(self.db_map, self.item_type, self.id)
        name = self.model.make_feature_name(item_data["entity_class_name"], item_data["parameter_definition_name"])
        return dict(name=name, **item_data)

    @property
    def tool_tip(self):
        return "<p>Drag this item and drop it onto a <b>tool</b> item below to create a tool feature</p>"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_features({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_features({self.db_map: [db_item]})

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled

    def _make_item_to_add(self, value):
        parameter_definition_id, parameter_value_list_id = value
        return dict(
            parameter_definition_id=parameter_definition_id,
            parameter_value_list_id=parameter_value_list_id,
            description=self._item_data["description"],
        )

    def _make_item_to_update(self, column, value):
        if column != 0:
            return super()._make_item_to_update(column, value)
        parameter_definition_id, parameter_value_list_id = value
        return dict(
            id=self.id, parameter_definition_id=parameter_definition_id, parameter_value_list_id=parameter_value_list_id
        )


class ToolLeafItem(LastGrayMixin, EditableMixin, LeafItem):
    """A tool leaf item."""

    @property
    def item_type(self):
        return "tool"

    @property
    def tool_tip(self):
        return "<p>Drag a <b>feature</b> item from above and drop it here to create a tool feature</p>"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_tools({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_tools({self.db_map: [db_item]})

    def flags(self, column):
        flags = super().flags(column)
        if self.id:
            flags |= Qt.ItemIsDropEnabled
        return flags

    @property
    def feature_id_list(self):
        feature_id_list = self.item_data.get("feature_id_list")
        if not feature_id_list:
            return []
        return [int(id_) for id_ in feature_id_list.split(",")]

    def fetch_more(self):
        children = [ToolFeatureLeafItem() for _ in self.feature_id_list]
        self.append_children(*children)
        self._fetched = True

    def handle_updated_in_db(self):
        super().handle_updated_in_db()
        self._update_feature_id_list()

    def _update_feature_id_list(self):
        feat_count = len(self.feature_id_list)
        curr_feat_count = self.child_count()
        if feat_count > curr_feat_count:
            added_count = feat_count - curr_feat_count
            children = [ToolFeatureLeafItem() for _ in range(added_count)]
            self.insert_children(curr_feat_count, *children)
        elif curr_feat_count > feat_count:
            removed_count = curr_feat_count - feat_count
            self.remove_children(feat_count, removed_count)


class ToolFeatureLeafItem(LeafItem):
    """A tool feature leaf item."""

    @property
    def item_type(self):
        return "feature"

    @property
    def id(self):
        return self.parent_item.feature_id_list[self.child_number()]

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()
