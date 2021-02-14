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
The SpineDBWorker class

:authors: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""

from PySide2.QtCore import QObject, Signal, Slot, QEventLoop
from spinedb_api import DiffDatabaseMapping, get_data_for_import, SpineDBAPIError, SpineDBVersionError
from .spine_db_commands import AgedUndoCommand, AddItemsCommand, UpdateItemsCommand, RemoveItemsCommand


class SpineDBWorker(QObject):
    """Does all the DB communication for SpineDBManager, in the non-GUI thread."""

    _get_db_map_called = Signal()
    _get_db_map_finished = Signal()
    _close_db_map_called = Signal(object)
    _add_or_update_items_called = Signal(object, str, str, str)
    _remove_items_called = Signal(object)
    _commit_session_called = Signal(object, str, object)
    _rollback_session_called = Signal(object)
    _import_data_called = Signal(object, str)
    _set_scenario_alternatives_called = Signal(object)
    _set_parameter_definition_tags_called = Signal(bool)

    def __init__(self, db_mngr):
        super().__init__()
        self.moveToThread(db_mngr.thread)
        self._db_mngr = db_mngr
        self._db_map = None
        self._db_map_args = None
        self._db_map_kwargs = None
        self._err = None

    def connect_signals(self):
        self._get_db_map_called.connect(self._get_db_map)
        self._close_db_map_called.connect(self._close_db_map)
        self._add_or_update_items_called.connect(self._add_or_update_items)
        self._remove_items_called.connect(self._remove_items)
        self._commit_session_called.connect(self._commit_session)
        self._rollback_session_called.connect(self._rollback_session)
        self._import_data_called.connect(self._import_data)
        self._set_scenario_alternatives_called.connect(self._set_scenario_alternatives)
        self._set_parameter_definition_tags_called.connect(self._set_parameter_definition_tags)

    def get_db_map(self, *args, **kwargs):
        loop = QEventLoop()
        self._get_db_map_finished.connect(loop.quit)
        self._db_map = None
        self._db_map_args = args
        self._db_map_kwargs = kwargs
        self._err = None
        self._get_db_map_called.emit()
        if self._db_map is None and self._err is None:
            loop.exec_()
        return self._db_map, self._err

    @Slot()
    def _get_db_map(self):
        # FIXME: What to do in case of errors?
        try:
            self._db_map = DiffDatabaseMapping(*self._db_map_args, **self._db_map_kwargs)
        except (SpineDBVersionError, SpineDBAPIError) as err:
            self._err = err
        self._get_db_map_finished.emit()

    def close_db_map(self, db_map):
        self._close_db_map_called.emit(db_map)

    @Slot(object)
    def _close_db_map(self, db_map):  # pylint: disable=no-self-use
        if not db_map.connection.closed:
            db_map.connection.close()

    def add_or_update_items(self, db_map_data, method_name, getter_name, signal_name):
        self._add_or_update_items_called.emit(db_map_data, method_name, getter_name, signal_name)

    @Slot(object, str, str, str)
    def _add_or_update_items(self, db_map_data, method_name, getter_name, signal_name):
        """Adds or updates items in db.

        Args:
            db_map_data (dict): lists of items to add or update keyed by DiffDatabaseMapping
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            getter_name (str): attribute of SpineDBManager to call for getting affected items
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
        """
        getter = getattr(self._db_mngr, getter_name)
        signal = getattr(self._db_mngr, signal_name)
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            result = getattr(db_map, method_name)(*items)
            if isinstance(result, tuple):
                ids, errors = result
            else:
                ids, errors = result, ()
            if errors:
                db_map_error_log[db_map] = errors
            if not ids:
                continue
            for chunk in getter(db_map, ids=ids):
                signal.emit({db_map: chunk})
                self._refresh(signal_name, {db_map: chunk})
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)

    def remove_items(self, db_map_typed_ids):
        self._remove_items_called.emit(db_map_typed_ids)

    @Slot(object)
    def _remove_items(self, db_map_typed_ids):
        """Removes items from database.

        Args:
            db_map_typed_ids (dict): lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
        """
        db_map_typed_ids = {
            db_map: db_map.cascading_ids(**ids_per_type) for db_map, ids_per_type in db_map_typed_ids.items()
        }
        db_map_error_log = dict()
        for db_map, ids_per_type in db_map_typed_ids.items():
            try:
                db_map.remove_items(**ids_per_type)
            except SpineDBAPIError as err:
                db_map_error_log[db_map] = [err]
                continue
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        self._db_mngr.uncache_items(db_map_typed_ids)

    def commit_session(self, dirty_db_maps, commit_msg, cookie=None):
        self._commit_session_called.emit(dirty_db_maps, commit_msg, cookie)

    @Slot(object, str, object)
    def _commit_session(self, dirty_db_maps, commit_msg, cookie=None):
        db_map_error_log = {}
        committed_db_maps = set()
        for db_map in dirty_db_maps:
            try:
                db_map.commit_session(commit_msg)
                committed_db_maps.add(db_map)
                self._db_mngr.undo_stack[db_map].setClean()
            except SpineDBAPIError as e:
                db_map_error_log[db_map] = e.msg
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        if committed_db_maps:
            self._db_mngr.session_committed.emit(committed_db_maps, cookie)

    def rollback_session(self, dirty_db_maps):
        self._rollback_session_called.emit(dirty_db_maps)

    @Slot(object)
    def _rollback_session(self, dirty_db_maps):
        db_map_error_log = {}
        rolled_db_maps = set()
        for db_map in dirty_db_maps:
            try:
                db_map.rollback_session()
                rolled_db_maps.add(db_map)
                self._db_mngr.undo_stack[db_map].clear()
                del self._db_mngr._cache[db_map]
            except SpineDBAPIError as e:
                db_map_error_log[db_map] = e.msg
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        if rolled_db_maps:
            self._db_mngr.session_rolled_back.emit(rolled_db_maps)

    def import_data(self, db_map_data, command_text="Import data"):
        self._import_data_called.emit(db_map_data, command_text)

    @Slot(object, str)
    def _import_data(self, db_map_data, command_text="Import data"):
        db_map_error_log = dict()
        for db_map, data in db_map_data.items():
            try:
                data_for_import = get_data_for_import(db_map, **data)
            except (TypeError, ValueError) as err:
                msg = f"Failed to import data: {err}. Please check that your data source has the right format."
                db_map_error_log.setdefault(db_map, []).append(msg)
                continue
            command = AgedUndoCommand()
            command.setText(command_text)
            child_cmds = []
            # NOTE: we push the import command before adding the children,
            # because we *need* to call redo() on the children one by one so the data gets in gradually
            self._db_mngr.undo_stack[db_map].push(command)
            for item_type, (to_add, to_update, import_error_log) in data_for_import:
                db_map_error_log.setdefault(db_map, []).extend([str(x) for x in import_error_log])
                if to_add:
                    add_cmd = AddItemsCommand(self._db_mngr, db_map, to_add, item_type, parent=command)
                    add_cmd.redo()
                    child_cmds.append(add_cmd)
                if to_update:
                    upd_cmd = UpdateItemsCommand(self._db_mngr, db_map, to_update, item_type, parent=command)
                    upd_cmd.redo()
                    child_cmds.append(upd_cmd)
            if child_cmds and all([cmd.isObsolete() for cmd in child_cmds]):
                # Nothing imported. Set the command obsolete and call undo() on the stack to removed it
                command.setObsolete(True)
                self._db_mngr.undo_stack[db_map].undo()
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        self._db_mngr.data_imported.emit()

    def set_scenario_alternatives(self, db_map_data):
        self._set_scenario_alternatives_called.emit(db_map_data)

    @Slot(object)
    def _set_scenario_alternatives(self, db_map_data):
        for db_map, data in db_map_data.items():
            command = AgedUndoCommand()
            command.setText(f"set scenario alternatives in {db_map.codename}")
            self._db_mngr.undo_stack[db_map].push(command)
            child_cmds = []
            items_to_add, items_to_update, ids_to_remove = db_map.get_data_to_set_scenario_alternatives(*data)
            if ids_to_remove:
                rm_cmd = RemoveItemsCommand(
                    self._db_mngr, db_map, {"scenario_alternative": ids_to_remove}, parent=command
                )
                rm_cmd.redo()
                child_cmds.append(rm_cmd)
            if items_to_update:
                upd_cmd = UpdateItemsCommand(
                    self._db_mngr, db_map, items_to_update, "scenario_alternative", parent=command
                )
                upd_cmd.redo()
                child_cmds.append(upd_cmd)
            if items_to_add:
                add_cmd = AddItemsCommand(self._db_mngr, db_map, items_to_add, "scenario_alternative", parent=command)
                add_cmd.redo()
                child_cmds.append(add_cmd)
            if child_cmds and all([cmd.isObsolete() for cmd in child_cmds]):
                command.setObsolete(True)
                self._db_mngr.undo_stack[db_map].undo()

    def set_parameter_definition_tags(self, db_map_data):
        self._set_parameter_definition_tags_called.emit(db_map_data)

    @Slot(object)
    def _set_parameter_definition_tags(self, db_map_data):
        for db_map, data in db_map_data.items():
            command = AgedUndoCommand()
            command.setText(f"set parameter definition tags in {db_map.codename}")
            self._db_mngr.undo_stack[db_map].push(command)
            child_cmds = []
            items_to_add, ids_to_remove = db_map.get_data_to_set_parameter_definition_tags(*data)
            if ids_to_remove:
                rm_cmd = RemoveItemsCommand(
                    self._db_mngr, db_map, {"parameter_definition_tag": ids_to_remove}, parent=command
                )
                rm_cmd.redo()
                child_cmds.append(rm_cmd)
            if items_to_add:
                add_cmd = AddItemsCommand(
                    self._db_mngr, db_map, items_to_add, "parameter_definition_tag", parent=command
                )
                add_cmd.redo()
                child_cmds.append(add_cmd)
            if child_cmds and all([cmd.isObsolete() for cmd in child_cmds]):
                command.setObsolete(True)
                self._db_mngr.undo_stack[db_map].undo()

    def _refresh(self, signal_name, db_map_data):
        callbacks = {
            "alternatives_updated": (self._cascade_refresh_parameter_values_by_alternative,),
            "object_classes_updated": (
                self._cascade_refresh_relationship_classes,
                self._cascade_refresh_parameter_definitions,
                self._cascade_refresh_parameter_values_by_entity_class,
            ),
            "relationship_classes_updated": (
                self._cascade_refresh_parameter_definitions,
                self._cascade_refresh_parameter_values_by_entity_class,
            ),
            "objects_updated": (
                self._cascade_refresh_relationships_by_object,
                self._cascade_refresh_parameter_values_by_entity,
            ),
            "relationships_updated": (self._cascade_refresh_parameter_values_by_entity,),
            "parameter_definitions_updated": (
                self._cascade_refresh_parameter_values_by_definition,
                self._cascade_refresh_features_by_paremeter_definition,
            ),
            "parameter_value_lists_added": (self._cascade_refresh_parameter_definitions_by_value_list,),
            "parameter_value_lists_updated": (
                self._cascade_refresh_parameter_definitions_by_value_list,
                self._cascade_refresh_features_by_paremeter_value_list,
            ),
            "parameter_value_lists_removed": (self._cascade_refresh_parameter_definitions_by_value_list,),
            "parameter_tags_updated": (self._cascade_refresh_parameter_definitions_by_tag,),
            "features_updated": (self._cascade_refresh_tool_features_by_feature,),
            "scenario_alternatives_added": (self._refresh_scenario_alternatives,),
            "scenario_alternatives_updated": (self._refresh_scenario_alternatives,),
            "scenario_alternatives_removed": (self._refresh_scenario_alternatives,),
            "parameter_definition_tags_added": (self._refresh_parameter_definitions_by_tag,),
            "parameter_definition_tags_removed": (self._refresh_parameter_definitions_by_tag,),
        }.get(signal_name, ())
        for callback in callbacks:
            callback(db_map_data)

    def _refresh_scenario_alternatives(self, db_map_data):
        """Refreshes cached scenarios when updating scenario alternatives.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            for chunk in self._db_mngr.get_scenarios(db_map, ids={x["scenario_id"] for x in data}):
                self._db_mngr.scenarios_updated.emit({db_map: chunk})

    def _refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            for chunk in self._db_mngr.get_parameter_definitions(
                db_map, ids={x["parameter_definition_id"] for x in data}
            ):
                self._db_mngr.parameter_definitions_updated.emit({db_map: chunk})

    def _cascade_refresh_relationship_classes(self, db_map_data):
        """Refreshes cached relationship classes when updating object classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_relationship_classes(self._db_map_ids(db_map_data))
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_relationship_classes(db_map, ids={x["id"] for x in data}):
                self._db_mngr.relationship_classes_updated.emit({db_map: chunk})

    def _cascade_refresh_relationships_by_object(self, db_map_data):
        """Refreshed cached relationships in cascade when updating objects.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_relationships(self._db_map_ids(db_map_data))
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_relationships(db_map, ids={x["id"] for x in data}):
                self._db_mngr.relationships_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_definitions(self, db_map_data):
        """Refreshes cached parameter definitions in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_data(
            self._db_map_ids(db_map_data), "parameter_definition"
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_definitions(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_definitions_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_definitions_by_value_list(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter_value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_definitions_by_value_list(
            self._db_map_ids(db_map_data)
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_definitions(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_definitions_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_values_by_entity_class(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_data(
            self._db_map_ids(db_map_data), "parameter_value"
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_values(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_values_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_values_by_entity(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entities.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_values_by_entity(self._db_map_ids(db_map_data))
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_values(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_values_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_values_by_alternative(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating alternatives.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_values_by_alternative(
            self._db_map_ids(db_map_data)
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_values(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_values_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_values_by_definition(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating parameter definitions.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_values_by_definition(
            self._db_map_ids(db_map_data)
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_values(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_values_updated.emit({db_map: chunk})

    def _cascade_refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_parameter_definitions_by_tag(self._db_map_ids(db_map_data))
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_parameter_definitions(db_map, ids={x["id"] for x in data}):
                self._db_mngr.parameter_definitions_updated.emit({db_map: chunk})

    def _cascade_refresh_features_by_paremeter_definition(self, db_map_data):
        """Refreshes cached features in cascade when updating parameter definitions.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_features_by_parameter_definition(
            self._db_map_ids(db_map_data)
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_features(db_map, ids={x["id"] for x in data}):
                self._db_mngr.features_updated.emit({db_map: chunk})

    def _cascade_refresh_features_by_paremeter_value_list(self, db_map_data):
        """Refreshes cached features in cascade when updating parameter value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_features_by_parameter_value_list(
            self._db_map_ids(db_map_data)
        )
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_features(db_map, ids={x["id"] for x in data}):
                self._db_mngr.features_updated.emit({db_map: chunk})

    def _cascade_refresh_tool_features_by_feature(self, db_map_data):
        """Refreshes cached tool features in cascade when updating features.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self._db_mngr.find_cascading_tool_features_by_feature(self._db_map_ids(db_map_data))
        for db_map, data in db_map_cascading_data.items():
            for chunk in self._db_mngr.get_tool_features(db_map, ids={x["id"] for x in data}):
                self._db_mngr.tool_features_updated.emit({db_map: chunk})

    def _db_map_ids(self, db_map_data):
        return self._db_mngr.db_map_ids(db_map_data)
