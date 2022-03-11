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
QUndoCommand subclasses for modifying the db.

:authors: M. Marin (KTH)
:date:   31.1.2020
"""

import time
from PySide2.QtWidgets import QUndoCommand, QUndoStack
from spinetoolbox.helpers import signal_waiter


class AgedUndoStack(QUndoStack):
    @property
    def redo_age(self):
        if self.canRedo():
            return self.command(self.index()).age
        return -1

    @property
    def undo_age(self):
        if self.canUndo():
            return self.command(self.index() - 1).age
        return -1

    def commands(self):
        return [self.command(idx) for idx in range(self.index())]


class AgedUndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        """
        Args:
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self._age = -1

    def redo(self):
        super().redo()
        self._age = time.time()

    def undo(self):
        super().undo()
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
        "list_value": "add parameter value list values",
        "alternative": "add alternative",
        "scenario": "add scenario",
        "feature": "add feature",
        "tool": "add tool",
        "tool_feature": "add tool features",
        "tool_feature_method": "add tool feature methods",
    }
    _update_command_name = {
        "object_class": "update object classes",
        "object": "update objects",
        "relationship_class": "update relationship classes",
        "relationship": "update relationships",
        "parameter_definition": "update parameter definitions",
        "parameter_value": "update parameter values",
        "parameter_value_list": "update parameter value lists",
        "list_value": "update parameter value list values",
        "alternative": "update alternatives",
        "scenario": "update scenarios",
        "feature": "update features",
        "tool": "update tools",
        "tool_feature": "update tool features",
        "tool_feature_method": "update tool feature methods",
    }
    _add_method_name = {
        "object_class": "add_object_classes",
        "object": "add_objects",
        "relationship_class": "add_wide_relationship_classes",
        "relationship": "add_wide_relationships",
        "entity_group": "add_entity_groups",
        "parameter_definition": "add_parameter_definitions",
        "parameter_value": "add_parameter_values",
        "parameter_value_list": "add_parameter_value_lists",
        "list_value": "add_list_values",
        "alternative": "add_alternatives",
        "scenario": "add_scenarios",
        "scenario_alternative": "add_scenario_alternatives",
        "feature": "add_features",
        "tool": "add_tools",
        "tool_feature": "add_tool_features",
        "tool_feature_method": "add_tool_feature_methods",
    }
    _update_method_name = {
        "object_class": "update_object_classes",
        "object": "update_objects",
        "relationship_class": "update_wide_relationship_classes",
        "relationship": "update_wide_relationships",
        "parameter_definition": "update_parameter_definitions",
        "parameter_value": "update_parameter_values",
        "parameter_value_list": "update_parameter_value_lists",
        "list_value": "update_list_values",
        "alternative": "update_alternatives",
        "scenario": "update_scenarios",
        "scenario_alternative": "update_scenario_alternatives",
        "feature": "update_features",
        "tool": "update_tools",
        "tool_feature": "update_tool_features",
        "tool_feature_method": "update_tool_feature_methods",
    }
    _added_signal_name = {
        "object_class": "object_classes_added",
        "object": "objects_added",
        "relationship_class": "relationship_classes_added",
        "relationship": "relationships_added",
        "entity_group": "entity_groups_added",
        "parameter_definition": "parameter_definitions_added",
        "parameter_value": "parameter_values_added",
        "parameter_value_list": "parameter_value_lists_added",
        "list_value": "list_values_added",
        "alternative": "alternatives_added",
        "scenario": "scenarios_added",
        "scenario_alternative": "scenario_alternatives_added",
        "feature": "features_added",
        "tool": "tools_added",
        "tool_feature": "tool_features_added",
        "tool_feature_method": "tool_feature_methods_added",
    }
    _updated_signal_name = {
        "object_class": "object_classes_updated",
        "object": "objects_updated",
        "relationship_class": "relationship_classes_updated",
        "relationship": "relationships_updated",
        "parameter_definition": "parameter_definitions_updated",
        "parameter_value": "parameter_values_updated",
        "parameter_value_list": "parameter_value_lists_updated",
        "list_value": "list_values_updated",
        "alternative": "alternatives_updated",
        "scenario": "scenarios_updated",
        "scenario_alternative": "scenario_alternatives_updated",
        "feature": "features_updated",
        "tool": "tools_updated",
        "tool_feature": "tool_features_updated",
        "tool_feature_method": "tool_feature_methods_updated",
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
        self._done_once = False

    @staticmethod
    def redomethod(func):
        """Returns a new redo method that determines if the command was completed.
        The command is completed if calling the function triggers the ``completed_signal``.
        Once the command is completed, we don't listen to the signal anymore
        and we also silence the affected Spine db editors.
        If the signal is not received, then the command is declared obsolete.
        """

        def redo(self):
            super().redo()
            with signal_waiter(self.completed_signal) as waiter:
                func(self)
                waiter.wait()
                if not self._done_once:
                    self.receive_items_changed(*waiter.args)
                    self._done_once = True

        return redo

    @staticmethod
    def undomethod(func):
        """Returns a new undo method that silences the affected Spine db editors."""

        def undo(self):
            super().undo()
            func(self)

        return undo

    def receive_items_changed(self, _):
        raise NotImplementedError()


class AddItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, data, item_type, parent=None, check=True):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to add
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        self.redo_db_map_data = {db_map: data}
        self.item_type = item_type
        self.method_name = self._add_method_name[item_type]
        self.completed_signal_name = self._added_signal_name[item_type]
        self.completed_signal = getattr(db_mngr, self.completed_signal_name)
        self.undo_db_map_typed_ids = None
        self._readd = False
        self._check = check
        self.setText(self._add_command_name.get(item_type, "add item") + f" to '{db_map.codename}'")

    @SpineDBCommand.redomethod
    def redo(self):
        self.db_mngr.add_or_update_items(
            self.redo_db_map_data,
            self.method_name,
            self.item_type,
            self.completed_signal_name,
            readd=self._readd,
            check=self._check,
        )

    @SpineDBCommand.undomethod
    def undo(self):
        self.db_mngr.do_remove_items(self.undo_db_map_typed_ids)
        self._readd = True

    def receive_items_changed(self, db_map_data):
        if not db_map_data.get(self.db_map):
            self.setObsolete(True)
            return
        self.redo_db_map_data = {
            db_map: [db_map.cache_to_db(self.item_type, item) for item in data] for db_map, data in db_map_data.items()
        }
        self.undo_db_map_typed_ids = {
            db_map: db_map.cascading_ids(
                cache=self.db_mngr.get_db_map_cache(db_map, {self.item_type}, only_descendants=True),
                **{self.item_type: {x["id"] for x in data}},
            )
            for db_map, data in db_map_data.items()
        }


class UpdateItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, data, item_type, parent=None, check=True):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to update
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        undo_data = [self._undo_item(db_map, item["id"]) for item in data]
        redo_data = [{**undo_item, **item} for undo_item, item in zip(undo_data, data)]
        if undo_data == redo_data:
            self.setObsolete(True)
        self.redo_db_map_data = {db_map: redo_data}
        self.undo_db_map_data = {db_map: undo_data}
        self.method_name = self._update_method_name[item_type]
        self.completed_signal_name = self._updated_signal_name[item_type]
        self.completed_signal = getattr(db_mngr, self.completed_signal_name)
        self._check = check
        self.setText(self._update_command_name.get(item_type, "update item") + f" in '{db_map.codename}'")

    def _undo_item(self, db_map, id_):
        undo_item = self.db_mngr.get_item(db_map, self.item_type, id_)
        return db_map.cache_to_db(self.item_type, undo_item)

    @SpineDBCommand.redomethod
    def redo(self):
        self.db_mngr.add_or_update_items(
            self.redo_db_map_data, self.method_name, self.item_type, self.completed_signal_name, check=self._check
        )

    @SpineDBCommand.undomethod
    def undo(self):
        self.db_mngr.add_or_update_items(
            self.undo_db_map_data, self.method_name, self.item_type, self.completed_signal_name, check=False
        )

    def receive_items_changed(self, db_map_data):
        if not db_map_data.get(self.db_map):
            self.setObsolete(True)
            return
        self.redo_db_map_data = {
            db_map: [db_map.cache_to_db(self.item_type, item) for item in data] for db_map, data in db_map_data.items()
        }
        self._check = False


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
        if not any(typed_data.values()):
            self.setObsolete(True)
        typed_data = db_map.cascading_ids(
            cache=self.db_mngr.get_db_map_cache(db_map, set(typed_data), only_descendants=True), **typed_data
        )
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
            method_name = self._add_method_name[item_type]
            emit_signal_name = self._added_signal_name[item_type]
            with signal_waiter(getattr(self.db_mngr, emit_signal_name)) as waiter:
                self.db_mngr.add_or_update_items(db_map_data, method_name, item_type, emit_signal_name, readd=True)
                waiter.wait()

    def receive_items_changed(self, typed_db_map_data):
        if not any(db_map_data.get(self.db_map) for db_map_data in typed_db_map_data.values()):
            self.setObsolete(True)
            return
        self.undo_typed_db_map_data = {
            item_type: {
                self.db_map: [self.db_map.cache_to_db(item_type, item) for item in db_map_data.get(self.db_map, [])]
            }
            for item_type, db_map_data in typed_db_map_data.items()
        }
