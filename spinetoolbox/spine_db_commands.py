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
QUndoCommand subclasses for modifying the db.

:authors: M. Marin (KTH)
:date:   31.1.2020
"""

import time
from copy import deepcopy
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QUndoCommand, QUndoStack


def _cache_to_db_relationship_class(item):
    item = deepcopy(item)
    item["object_class_id_list"] = [int(id_) for id_ in item["object_class_id_list"].split(",")]
    del item["object_class_name_list"]
    return item


def _cache_to_db_relationship(item):
    item = deepcopy(item)
    item["object_id_list"] = [int(id_) for id_ in item["object_id_list"].split(",")]
    del item["object_name_list"]
    return item


def _cache_to_db_parameter_definition(item):
    item = {k: v for k, v in item.items() if not any(k.startswith(x) for x in ("formatted_", "expanded_"))}
    item = deepcopy(item)
    if "parameter_name" in item:
        item["name"] = item.pop("parameter_name")
    if "value_list_id" in item:
        item["parameter_value_list_id"] = item.pop("value_list_id")
    return item


def _cache_to_db_parameter_value(item):
    item = {k: v for k, v in item.items() if not any(k.startswith(x) for x in ("formatted_", "expanded_"))}
    item = deepcopy(item)
    if "parameter_id" in item:
        item["parameter_definition_id"] = item.pop("parameter_id")
    return item


def _cache_to_db_parameter_value_list(item):
    item = deepcopy(item)
    item["value_list"] = item["value_list"].split(";")
    return item


def _cache_to_db_item(item_type, item):
    return {
        "relationship_class": _cache_to_db_relationship_class,
        "relationship": _cache_to_db_relationship,
        "parameter_definition": _cache_to_db_parameter_definition,
        "parameter_value": _cache_to_db_parameter_value,
        "parameter_value_list": _cache_to_db_parameter_value_list,
    }.get(item_type, lambda x: x)(item)


def _format_item(item_type, item):
    return {
        "parameter_value": lambda x: "<"
        + ", ".join([x.get("object_name") or x.get("object_name_list"), x["parameter_name"]])
        + ">",
        "parameter_definition": lambda x: x.get("parameter_name") or x.get("name"),
        "parameter_tag": lambda x: x["tag"],
    }.get(item_type, lambda x: x["name"])(item)


class AgedUndoStack(QUndoStack):
    @property
    def redo_age(self):
        if self.canRedo():
            return self.command(self.index()).age
        return None

    @property
    def undo_age(self):
        if self.canUndo():
            return self.command(self.index() - 1).age
        return None

    def commands(self):
        return [self.command(idx) for idx in range(self.index())]


class AgedUndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        """
        Args:
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self._age = time.time()

    @property
    def age(self):
        return self._age


class SpineDBCommand(AgedUndoCommand):
    _add_command_name = {
        "object_class": "add object classes",
        "object": "add objects",
        "relationship_class": "add relationship classes",
        "relationship": "add relationships",
        "entity_group": "add entity groups",
        "parameter_definition": "add parameter definitions",
        "parameter_value": "add parameter values",
        "parameter_value_list": "add parameter value lists",
        "parameter_tag": "add parameter tags",
        "alternative": "add alternative",
        "scenario": "add scenario",
        "feature": "add feature",
        "tool": "add tool",
        "tool_feature": "add tool features",
    }
    _update_command_name = {
        "object_class": "update object classes",
        "object": "update objects",
        "relationship_class": "update relationship classes",
        "relationship": "update relationships",
        "parameter_definition": "update parameter definitions",
        "parameter_value": "update parameter values",
        "parameter_value_list": "update parameter value lists",
        "parameter_tag": "update parameter tags",
        "alternative": "update alternative",
        "scenario": "update scenario",
        "feature": "update feature",
        "tool": "update tool",
        "tool_feature": "update tool features",
    }
    _add_method_name = {
        "object_class": "add_object_classes",
        "object": "add_objects",
        "relationship_class": "add_wide_relationship_classes",
        "relationship": "add_wide_relationships",
        "entity_group": "add_entity_groups",
        "parameter_definition": "add_parameter_definitions",
        "parameter_definition_tag": "add_parameter_definition_tags",
        "parameter_value": "add_parameter_values",
        "parameter_value_list": "add_wide_parameter_value_lists",
        "parameter_tag": "add_parameter_tags",
        "alternative": "add_alternatives",
        "scenario": "add_scenarios",
        "scenario_alternative": "add_scenario_alternatives",
        "feature": "add_features",
        "tool": "add_tools",
        "tool_feature": "add_tool_features",
    }
    _readd_method_name = {
        "object_class": "readd_object_classes",
        "object": "readd_objects",
        "relationship_class": "readd_wide_relationship_classes",
        "relationship": "readd_wide_relationships",
        "entity_group": "readd_entity_groups",
        "parameter_definition": "readd_parameter_definitions",
        "parameter_definition_tag": "readd_parameter_definition_tags",
        "parameter_value": "readd_parameter_values",
        "parameter_value_list": "readd_wide_parameter_value_lists",
        "parameter_tag": "readd_parameter_tags",
        "alternative": "readd_alternatives",
        "scenario": "readd_scenarios",
        "scenario_alternative": "readd_scenario_alternatives",
        "feature": "readd_features",
        "tool": "readd_tools",
        "tool_feature": "readd_tool_features",
    }
    _update_method_name = {
        "object_class": "update_object_classes",
        "object": "update_objects",
        "relationship_class": "update_wide_relationship_classes",
        "relationship": "update_wide_relationships",
        "parameter_definition": "update_parameter_definitions",
        "parameter_value": "update_parameter_values",
        "parameter_value_list": "update_wide_parameter_value_lists",
        "parameter_tag": "update_parameter_tags",
        "alternative": "update_alternatives",
        "scenario": "update_scenarios",
        "scenario_alternative": "_update_scenario_alternatives",
        "feature": "update_features",
        "tool": "update_tools",
        "tool_feature": "update_tool_features",
    }
    _get_method_name = {
        "object_class": "get_object_classes",
        "object": "get_objects",
        "relationship_class": "get_relationship_classes",
        "relationship": "get_relationships",
        "entity_group": "get_entity_groups",
        "parameter_definition": "get_parameter_definitions",
        "parameter_definition_tag": "get_parameter_definition_tags",
        "parameter_value": "get_parameter_values",
        "parameter_value_list": "get_parameter_value_lists",
        "parameter_tag": "get_parameter_tags",
        "alternative": "get_alternatives",
        "scenario": "get_scenarios",
        "scenario_alternative": "get_scenario_alternatives",
        "feature": "get_features",
        "tool": "get_tools",
        "tool_feature": "get_tool_features",
    }
    _added_signal_name = {
        "object_class": "object_classes_added",
        "object": "objects_added",
        "relationship_class": "relationship_classes_added",
        "relationship": "relationships_added",
        "entity_group": "entity_groups_added",
        "parameter_definition": "parameter_definitions_added",
        "parameter_definition_tag": "_parameter_definition_tags_added",
        "parameter_value": "parameter_values_added",
        "parameter_value_list": "parameter_value_lists_added",
        "parameter_tag": "parameter_tags_added",
        "alternative": "alternatives_added",
        "scenario": "scenarios_added",
        "scenario_alternative": "_scenario_alternatives_added",
        "feature": "features_added",
        "tool": "tools_added",
        "tool_feature": "tool_features_added",
    }
    _updated_signal_name = {
        "object_class": "object_classes_updated",
        "object": "objects_updated",
        "relationship_class": "relationship_classes_updated",
        "relationship": "relationships_updated",
        "parameter_definition": "parameter_definitions_updated",
        "parameter_value": "parameter_values_updated",
        "parameter_value_list": "parameter_value_lists_updated",
        "parameter_tag": "parameter_tags_updated",
        "alternative": "alternatives_updated",
        "scenario": "scenarios_updated",
        "scenario_alternative": "_scenario_alternatives_updated",
        "feature": "features_updated",
        "tool": "tools_updated",
        "tool_feature": "tool_features_updated",
    }

    def __init__(self, db_mngr, db_map, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self.db_mngr = db_mngr
        self.db_map = db_map
        self.completed_signal = None
        self._completed = False

    def silence_listener(self, func):
        """Calls given function while silencing the listener Spine db editors.
        This is so undo() and subsequent redo() calls don't trigger the same notifications over and over.
        """
        listeners = self.db_mngr.signaller.db_map_listeners(self.db_map)
        for listener in listeners:
            listener.silenced = True
        func(self)
        for listener in listeners:
            listener.silenced = False

    @staticmethod
    def redomethod(func):
        """Returns a new redo method that determines if the command was completed.
        The command is completed if calling the function triggers the ``completed_signal``.
        Once the command is completed, we don't listen to the signal anymore
        and we also silence the affected Spine db editors.
        If the signal is not received, then the command is declared obsolete.
        """

        def redo(self):
            if self._completed:
                self.silence_listener(func)
                return
            self.completed_signal.connect(self.receive_items_changed)
            func(self)
            self.completed_signal.disconnect(self.receive_items_changed)
            if not self._completed:
                self.setObsolete(True)

        return redo

    @staticmethod
    def undomethod(func):
        """Returns a new undo method that silences the affected Spine db editors.
        """

        def undo(self):
            self.silence_listener(func)

        return undo

    @Slot(object)
    def receive_items_changed(self, _db_map_data):
        """Marks the command as completed."""
        self._completed = True

    def data(self):
        """Returns data to present this command in a DBHistoryDialog."""
        raise NotImplementedError()


class AddItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, data, item_type, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to add
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        self.redo_db_map_data = {db_map: data}
        self.item_type = item_type
        self.method_name = self._add_method_name[item_type]
        self.get_method_name = self._get_method_name[item_type]
        self.completed_signal_name = self._added_signal_name[item_type]
        self.completed_signal = getattr(db_mngr, self.completed_signal_name)
        self.setText(self._add_command_name.get(item_type, "add item") + f" to '{db_map.codename}'")
        self.undo_db_map_typed_ids = None

    @SpineDBCommand.redomethod
    def redo(self):
        self.db_mngr.add_or_update_items(
            self.redo_db_map_data, self.method_name, self.get_method_name, self.completed_signal_name
        )

    @SpineDBCommand.undomethod
    def undo(self):
        self.db_mngr.do_cascade_remove_items(self.undo_db_map_typed_ids)

    @Slot(object)
    def receive_items_changed(self, db_map_data):
        super().receive_items_changed(db_map_data)
        self.redo_db_map_data = {
            db_map: [_cache_to_db_item(self.item_type, item) for item in data] for db_map, data in db_map_data.items()
        }
        self.method_name = self._readd_method_name[self.item_type]
        self.undo_db_map_typed_ids = {
            db_map: {self.item_type: {x["id"] for x in data}} for db_map, data in db_map_data.items()
        }

    def data(self):
        return {_format_item(self.item_type, item): [] for item in self.redo_db_map_data[self.db_map]}


class AddCheckedParameterValuesCommand(AddItemsCommand):
    def __init__(self, db_mngr, db_map, data, parent=None):
        super().__init__(db_mngr, db_map, data, "parameter_value", parent=parent)
        self.method_name = "add_checked_parameter_values"


class UpdateItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, data, item_type, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to update
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        self.item_type = item_type
        self.redo_db_map_data = {db_map: data}
        self.undo_db_map_data = {db_map: [self._undo_item(db_map, item) for item in data]}
        self.method_name = self._update_method_name[item_type]
        self.get_method_name = self._get_method_name[self.item_type]
        self.completed_signal_name = self._updated_signal_name[item_type]
        self.completed_signal = getattr(db_mngr, self.completed_signal_name)
        self.setText(self._update_command_name.get(item_type, "update item") + f" in '{db_map.codename}'")

    def _undo_item(self, db_map, redo_item):
        undo_item = self.db_mngr.get_item(db_map, self.item_type, redo_item["id"])
        return _cache_to_db_item(self.item_type, undo_item)

    @SpineDBCommand.redomethod
    def redo(self):
        self.db_mngr.add_or_update_items(
            self.redo_db_map_data, self.method_name, self.get_method_name, self.completed_signal_name
        )

    @SpineDBCommand.undomethod
    def undo(self):
        self.db_mngr.add_or_update_items(
            self.undo_db_map_data, self.method_name, self.get_method_name, self.completed_signal_name
        )

    def data(self):
        return {_format_item(self.item_type, item): [] for item in self.undo_db_map_data[self.db_map]}


class UpdateCheckedParameterValuesCommand(UpdateItemsCommand):
    def __init__(self, db_mngr, db_map, data, parent=None):
        super().__init__(db_mngr, db_map, data, "parameter_value", parent=parent)
        self.method_name = "update_checked_parameter_values"


class RemoveItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, typed_data, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            typed_data (dict): lists of dict-items to remove keyed by string type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        self.redo_db_map_typed_data = {db_map: typed_data}
        self.undo_typed_db_map_data = {}
        self.setText(f"remove items from '{db_map.codename}'")
        self.completed_signal = self.db_mngr.items_removed_from_cache

    @SpineDBCommand.redomethod
    def redo(self):
        self.db_mngr.do_remove_items(self.redo_db_map_typed_data)

    @SpineDBCommand.undomethod
    def undo(self):
        for item_type in reversed(list(self.undo_typed_db_map_data.keys())):
            db_map_data = self.undo_typed_db_map_data[item_type]
            method_name = self._readd_method_name[item_type]
            get_method_name = self._get_method_name[item_type]
            emit_signal_name = self._added_signal_name[item_type]
            self.db_mngr.add_or_update_items(db_map_data, method_name, get_method_name, emit_signal_name)

    @Slot(object)
    def receive_items_changed(self, typed_db_map_data):  # pylint: disable=arguments-differ
        super().receive_items_changed(typed_db_map_data)
        self.undo_typed_db_map_data = {
            item_type: {self.db_map: [_cache_to_db_item(item_type, item) for item in db_map_data.get(self.db_map, [])]}
            for item_type, db_map_data in typed_db_map_data.items()
        }

    def data(self):
        return {
            item_type: [_format_item(item_type, item) for item in self.undo_typed_db_map_data[item_type][self.db_map]]
            for item_type in reversed(list(self.undo_typed_db_map_data.keys()))
        }
