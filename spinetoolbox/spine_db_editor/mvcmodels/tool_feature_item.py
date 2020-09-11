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
from .tree_item_utility import LastGrayMixin, EditableMixin, RootItem, EmptyChildRootItem, LeafItem, NonLazyTreeItem

_FEATURE_ICON = "\uf5bc"  # splotch
_TOOL_ICON = "\uf6e3"  # hammer
_METHOD_ICON = "\uf1de"  # sliders-h


class FeatureRootItem(EmptyChildRootItem):
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


class ToolRootItem(EmptyChildRootItem):
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
        return "<p>Drag this item and drop it onto a <b>tool feature</b> item below to create a tool feature</p>"

    def add_item_to_db(self, db_item):
        if db_item is None:
            return
        self.db_mngr.add_features({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        if db_item is None:
            return
        self.db_mngr.update_features({self.db_map: [db_item]})

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled

    def _make_item_to_add(self, value):
        ids = self._get_ids_from_feat_name(value)
        if not ids:
            return None
        parameter_definition_id, parameter_value_list_id = ids
        return dict(
            parameter_definition_id=parameter_definition_id,
            parameter_value_list_id=parameter_value_list_id,
            description=self._item_data["description"],
        )

    def _make_item_to_update(self, column, value):
        if column != 0:
            return super()._make_item_to_update(column, value)
        ids = self._get_ids_from_feat_name(value)
        if not ids:
            return None
        parameter_definition_id, parameter_value_list_id = ids
        return dict(
            id=self.id, parameter_definition_id=parameter_definition_id, parameter_value_list_id=parameter_value_list_id
        )

    def _get_ids_from_feat_name(self, feature_name):
        ids = self.model.get_feature_data(self.db_map, feature_name)
        if ids is None:
            self.model._parent.error_box.emit(
                "Error",
                f"<p>Invalid feature '{feature_name}'. </p>"
                "<p>Please enter a valid combination of entity class/parameter definition.</p>",
            )
            return None
        return ids


class ToolLeafItem(LastGrayMixin, EditableMixin, LeafItem):
    """A tool leaf item."""

    @property
    def item_type(self):
        return "tool"

    def add_item_to_db(self, db_item):
        self.db_mngr.add_tools({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_tools({self.db_map: [db_item]})

    def fetch_more(self):
        if not self.id:
            return
        self.append_children(ToolFeatureRootItem())
        self._fetched = True


class ToolFeatureRootItem(RootItem):
    """A tool_feature root item."""

    @property
    def item_type(self):
        return "tool_feature root"

    @property
    def display_data(self):
        return "tool_feature"

    @property
    def tool_tip(self):
        return "<p>Drag a <b>feature</b> item from above and drop it here to create a tool feature</p>"

    @property
    def icon_code(self):
        return _FEATURE_ICON

    @property
    def feature_id_list(self):
        return [child.id for child in self.children]

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDropEnabled


class ToolFeatureLeafItem(LeafItem):
    """A tool feature leaf item."""

    @property
    def item_type(self):
        return "tool_feature"

    @property
    def item_data(self):
        item_data = self.db_mngr.get_item(self.db_map, self.item_type, self.id)
        feature_data = self.db_mngr.get_item(self.db_map, "feature", item_data["feature_id"])
        name = self.model.make_feature_name(
            feature_data["entity_class_name"], feature_data["parameter_definition_name"]
        )
        return dict(name=name, **item_data)

    def fetch_more(self):
        self.append_children(ToolFeatureRequiredItem(), ToolFeatureMethodRootItem())
        self._fetched = True

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        self.db_mngr.update_tool_features({self.db_map: [db_item]})


class ToolFeatureRequiredItem(NonLazyTreeItem):
    """A tool feature required item."""

    @property
    def item_type(self):
        return "tool_feature required"

    def flags(self, column):
        flags = super().flags(column)
        if column == 0:
            flags |= Qt.ItemIsEditable
        return flags

    def data(self, column, role=Qt.DisplayRole):
        if column == 0 and role in (Qt.DisplayRole, Qt.EditRole):
            required = "yes" if self.parent_item.item_data["required"] else "no"
            return "required: " + required
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.EditRole):
        if role == Qt.EditRole and column == 0:
            required = {"yes": True, "no": False}.get(value)
            if required is None:
                return False
            db_item = {"id": self.parent_item.id, "required": required}
            self.parent_item.update_item_in_db(db_item)
            return True
        return False


class ToolFeatureMethodRootItem(EmptyChildRootItem):
    """A tool_feature_method root item."""

    @property
    def item_type(self):
        return "tool_feature_method root"

    @property
    def display_data(self):
        return "tool_feature_method"

    @property
    def icon_code(self):
        return _METHOD_ICON

    def empty_child(self):
        return ToolFeatureMethodLeafItem()


class ToolFeatureMethodLeafItem(LastGrayMixin, LeafItem):
    """A tool_feature_method leaf item."""

    @property
    def item_type(self):
        return "tool_feature_method"

    @property
    def tool_feature_item(self):
        return self.parent_item.parent_item

    @property
    def item_data(self):
        if not self.id:
            return self._item_data
        item_data = self.db_mngr.get_item(self.db_map, self.item_type, self.id)
        name = self.db_mngr.get_value_list_item(
            self.db_map, item_data["parameter_value_list_id"], item_data["method_index"]
        )
        return dict(name=name, **item_data)

    def _make_item_data(self):
        return {"name": "Enter new method here...", "description": ""}

    def flags(self, column):
        flags = super().flags(column)
        if column == 0:
            flags |= Qt.ItemIsEditable
        return flags

    def _make_item_to_add(self, value):
        tool_feat_item = self.tool_feature_item
        tool_feature_id = tool_feat_item.id
        parameter_value_list_id = tool_feat_item.item_data["parameter_value_list_id"]
        method_index = self._get_method_index(parameter_value_list_id, value)
        if method_index is None:
            return None
        return dict(
            tool_feature_id=tool_feature_id, parameter_value_list_id=parameter_value_list_id, method_index=method_index
        )

    def _get_method_index(self, parameter_value_list_id, method):
        method_index = self.model.get_method_index(self.tool_feature_item.db_map, parameter_value_list_id, method)
        if method_index is None:
            self.model._parent.error_box.emit(
                "Error",
                f"<p>Invalid method '{method}'. </p>"
                f"<p>Please enter a valid method for feature '{self.tool_feature_item.name}'.</p>",
            )
            return None
        return method_index

    def add_item_to_db(self, db_item):
        self.db_mngr.add_tool_feature_methods({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_tool_feature_methods({self.db_map: [db_item]})
