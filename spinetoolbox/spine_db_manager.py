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
The SpineDBManager class

:authors: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""

from PySide2.QtCore import Qt, QObject, Signal, Slot, QSettings
from PySide2.QtWidgets import QMessageBox, QDialog, QCheckBox
from PySide2.QtGui import QKeySequence, QIcon, QFontMetrics, QFont
from spinedb_api import (
    SpineDBAPIError,
    SpineDBVersionError,
    DiffDatabaseMapping,
    from_database,
    relativedelta_to_duration,
    ParameterValueFormatError,
    DateTime,
    Duration,
    Map,
    TimePattern,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    is_empty,
    create_new_spine_database,
)
from .helpers import IconManager, busy_effect, format_string_list
from .spine_db_signaller import SpineDBSignaller
from .spine_db_commands import (
    AgedUndoStack,
    AddItemsCommand,
    AddCheckedParameterValuesCommand,
    UpdateItemsCommand,
    UpdateCheckedParameterValuesCommand,
    SetParameterDefinitionTagsCommand,
    RemoveItemsCommand,
)
from .widgets.manage_db_items_dialog import CommitDialog


@busy_effect
def do_create_new_spine_database(url, for_spine_model):
    """Creates a new spine database at the given url."""
    create_new_spine_database(url, for_spine_model=for_spine_model)


class SpineDBManager(QObject):
    """Class to manage DBs within a project.

    TODO: Expand description, how it works, the cache, the signals, etc.
    """

    msg_error = Signal(object)
    session_refreshed = Signal(set)
    session_committed = Signal(set)
    session_rolled_back = Signal(set)
    # Added
    object_classes_added = Signal(object)
    objects_added = Signal(object)
    relationship_classes_added = Signal(object)
    relationships_added = Signal(object)
    parameter_definitions_added = Signal(object)
    _parameter_definitions_added = Signal(object)
    parameter_values_added = Signal(object)
    _parameter_values_added = Signal(object)
    parameter_value_lists_added = Signal(object)
    parameter_tags_added = Signal(object)
    # Removed
    object_classes_removed = Signal(object)
    objects_removed = Signal(object)
    relationship_classes_removed = Signal(object)
    relationships_removed = Signal(object)
    parameter_definitions_removed = Signal(object)
    parameter_values_removed = Signal(object)
    parameter_value_lists_removed = Signal(object)
    parameter_tags_removed = Signal(object)
    # Updated
    object_classes_updated = Signal(object)
    objects_updated = Signal(object)
    relationship_classes_updated = Signal(object)
    relationships_updated = Signal(object)
    parameter_definitions_updated = Signal(object)
    _parameter_definitions_updated = Signal(object)
    parameter_values_updated = Signal(object)
    _parameter_values_updated = Signal(object)
    parameter_value_lists_updated = Signal(object)
    parameter_tags_updated = Signal(object)
    parameter_definition_tags_set = Signal(object)
    # Uncached
    items_removed_from_cache = Signal(object)

    _GROUP_SEP = " \u01C0 "

    def __init__(self, logger, project):
        """Initializes the instance.

        Args:
            logger (LoggingInterface)
            project (SpineToolboxProject)
        """
        super().__init__(project)
        self._logger = logger
        self._db_maps = {}
        self._cache = {}
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.signaller = SpineDBSignaller(self)
        self.undo_stack = {}
        self.undo_action = {}
        self.redo_action = {}
        self.icon_mngr = IconManager()
        self.connect_signals()

    @property
    def db_maps(self):
        return set(self._db_maps.values())

    def create_new_spine_database(self, url, for_spine_model=False):
        if url in self._db_maps:
            message = f"The url <b>{url}</b> is being viewed. Please close all windows viewing this url and try again."
            QMessageBox.critical(self.parent()._toolbox, "Error", message)
            return
        try:
            if not is_empty(url):
                msg = QMessageBox(self.parent()._toolbox)
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText("The database at <b>'{0}'</b> is not empty.".format(url))
                msg.setInformativeText("Do you want to overwrite it?")
                msg.addButton("Overwrite", QMessageBox.AcceptRole)
                msg.addButton("Cancel", QMessageBox.RejectRole)
                ret = msg.exec_()  # Show message box
                if ret != QMessageBox.AcceptRole:
                    return
            do_create_new_spine_database(url, for_spine_model)
            self.parent()._toolbox.msg_success.emit("New Spine db successfully created at '{0}'.".format(url))
        except SpineDBAPIError as e:
            self.parent()._toolbox.msg_error.emit("Unable to create new Spine db at '{0}': {1}.".format(url, e))

    def close_session(self, url):
        """Pops any db map on the given url and closes its connection.

        Args:
            url (str)
        """
        db_map = self._db_maps.pop(url, None)
        if db_map is None:
            return
        db_map.connection.close()

    def close_all_sessions(self):
        """Closes connections to all database mappings."""
        for db_map in self._db_maps.values():
            if not db_map.connection.closed:
                db_map.connection.close()

    def get_db_map(self, url, upgrade=False, codename=None):
        """Returns a DiffDatabaseMapping instance from url if possible, None otherwise.
        If needed, asks the user to upgrade to the latest db version.

        Args:
            url (str, URL)
            upgrade (bool, optional)
            codename (str, NoneType, optional)

        Returns:
            DiffDatabaseMapping, NoneType
        """
        try:
            return self.do_get_db_map(url, upgrade, codename)
        except SpineDBVersionError:
            msg = QMessageBox(self.parent()._toolbox)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Incompatible database version")
            msg.setText(
                "The database at <b>{}</b> is from an older version of Spine "
                "and needs to be upgraded in order to be used with the current version.".format(url)
            )
            msg.setInformativeText(
                "Do you want to upgrade it now?"
                "<p><b>WARNING</b>: After the upgrade, "
                "the database may no longer be used "
                "with previous versions of Spine."
            )
            msg.addButton(QMessageBox.Cancel)
            msg.addButton("Upgrade", QMessageBox.YesRole)
            ret = msg.exec_()  # Show message box
            if ret == QMessageBox.Cancel:
                return None
            return self.get_db_map(url, upgrade=True, codename=codename)

    @busy_effect
    def do_get_db_map(self, url, upgrade, codename):
        """Returns a memorized DiffDatabaseMapping instance from url.
        Called by `get_db_map`.

        Args:
            url (str, URL)
            upgrade (bool, optional)
            codename (str, NoneType, optional)

        Returns:
            DiffDatabaseMapping
        """
        if url not in self._db_maps:
            self._db_maps[url] = DiffDatabaseMapping(url, upgrade=upgrade, codename=codename)
        return self._db_maps[url]

    def get_db_map_for_listener(self, listener, url, upgrade=False, codename=None):
        db_map = self.get_db_map(url, upgrade=upgrade, codename=codename)
        self.signaller.add_db_map_listener(db_map, listener)
        stack = self.undo_stack[db_map] = AgedUndoStack(self)
        undo_action = self.undo_action[db_map] = stack.createUndoAction(self)
        redo_action = self.redo_action[db_map] = stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        stack.indexChanged.connect(listener.update_undo_redo_actions)
        stack.cleanChanged.connect(listener.update_commit_enabled)
        return db_map

    def remove_db_map_listener(self, db_map, listener):
        listeners = self.signaller.db_map_listeners(db_map) - {listener}
        if not listeners:
            if not self.ok_to_close(db_map):
                return False
            self.close_session(db_map.db_url)
        self.signaller.remove_db_map_listener(db_map, listener)
        self.undo_stack[db_map].indexChanged.disconnect(listener.update_undo_redo_actions)
        self.undo_stack[db_map].cleanChanged.disconnect(listener.update_commit_enabled)
        if not self.signaller.db_map_listeners(db_map):
            del self.undo_stack[db_map]
            del self.undo_action[db_map]
            del self.redo_action[db_map]
        return True

    def refresh_session(self, *db_maps):
        refreshed_db_maps = set()
        for db_map in db_maps:
            if self._cache.pop(db_map, None) is not None:
                refreshed_db_maps.add(db_map)
        if refreshed_db_maps:
            self.session_refreshed.emit(refreshed_db_maps)

    def commit_session(self, *db_maps):
        error_log = {}
        committed_db_maps = set()
        for db_map in db_maps:
            if not db_map.has_pending_changes():
                continue
            commit_msg = self._get_commit_msg(db_map)
            if not commit_msg:
                continue
            try:
                db_map.commit_session(commit_msg)
                committed_db_maps.add(db_map)
                self.undo_stack[db_map].setClean()
            except SpineDBAPIError as e:
                error_log[db_map] = e.msg
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if committed_db_maps:
            self.session_committed.emit(committed_db_maps)

    @staticmethod
    def _get_commit_msg(db_map):
        dialog = CommitDialog(qApp.activeWindow(), db_map.codename)  # pylint: disable=undefined-variable
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            return dialog.commit_msg

    def rollback_session(self, *db_maps):
        error_log = {}
        rolled_db_maps = set()
        for db_map in db_maps:
            if not db_map.has_pending_changes():
                continue
            try:
                db_map.rollback_session()
                rolled_db_maps.add(db_map)
                self.undo_stack[db_map].clear()
                del self._cache[db_map]
            except SpineDBAPIError as e:
                error_log[db_map] = e.msg
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if rolled_db_maps:
            self.session_rolled_back.emit(rolled_db_maps)

    def _commit_db_map_session(self, db_map):
        commit_msg = self._get_commit_msg(db_map)
        if not commit_msg:
            return False
        try:
            db_map.commit_session(commit_msg)
            return True
        except SpineDBAPIError as e:
            self.msg_error.emit({db_map: e.msg})
            return False

    def _rollback_db_map_session(self, db_map):
        try:
            db_map.rollback_session()
            return True
        except SpineDBAPIError as e:
            self.msg_error.emit({db_map: e.msg})
            return False

    def ok_to_close(self, db_map):
        """Prompts the user to commit or rollback changes to given database map.

        Returns:
            bool: True if successfully committed or rolled back, False otherwise
        """
        if not db_map.has_pending_changes():
            return True
        commit_at_exit = int(self.qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return self._rollback_db_map_session(db_map)
        if commit_at_exit == 1:  # Default
            # Show message box
            msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit Pending Changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.button(QMessageBox.Save).setText("Commit And Close ")
            msg.button(QMessageBox.Discard).setText("Discard Changes And Close")
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            if answer == QMessageBox.Cancel:
                return False
            chk = chkbox.checkState()
            if chk == 2:
                # Save preference
                preference = "2" if answer == QMessageBox.Save else "0"
                self.qsettings.setValue("appSettings/commitAtExit", preference)
            if answer == QMessageBox.Save:
                return self._commit_db_map_session(db_map)
            return self._rollback_db_map_session(db_map)
        if commit_at_exit == 2:
            # Commit session and don't show message box
            return self._commit_db_map_session(db_map)
        self.qsettings.setValue("appSettings/commitAtExit", "1")
        return True

    def connect_signals(self):
        """Connects signals."""
        # Error
        self.msg_error.connect(self.receive_error_msg)
        # Add to cache
        self.object_classes_added.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_added.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_added.connect(lambda db_map_data: self.cache_items("relationship class", db_map_data))
        self.relationships_added.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        self.parameter_definitions_added.connect(
            lambda db_map_data: self.cache_items("parameter definition", db_map_data)
        )
        self.parameter_values_added.connect(lambda db_map_data: self.cache_items("parameter value", db_map_data))
        self.parameter_value_lists_added.connect(
            lambda db_map_data: self.cache_items("parameter value list", db_map_data)
        )
        self.parameter_tags_added.connect(lambda db_map_data: self.cache_items("parameter tag", db_map_data))
        # Update in cache
        self.object_classes_updated.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_updated.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_updated.connect(
            lambda db_map_data: self.cache_items("relationship class", db_map_data)
        )
        self.relationships_updated.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        self.parameter_definitions_updated.connect(
            lambda db_map_data: self.cache_items("parameter definition", db_map_data)
        )
        self.parameter_values_updated.connect(lambda db_map_data: self.cache_items("parameter value", db_map_data))
        self.parameter_value_lists_updated.connect(
            lambda db_map_data: self.cache_items("parameter value list", db_map_data)
        )
        self.parameter_tags_updated.connect(lambda db_map_data: self.cache_items("parameter tag", db_map_data))
        self.parameter_definition_tags_set.connect(self.cache_parameter_definition_tags)
        # Go from compact to extend format
        self._parameter_definitions_added.connect(self.do_add_parameter_definitions)
        self._parameter_definitions_updated.connect(self.do_update_parameter_definitions)
        self._parameter_values_added.connect(self.do_add_parameter_values)
        self._parameter_values_updated.connect(self.do_update_parameter_values)
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)
        # On cascade remove
        self.object_classes_removed.connect(self.cascade_remove_objects)
        self.object_classes_removed.connect(self.cascade_remove_relationship_classes)
        self.object_classes_removed.connect(self.cascade_remove_parameter_definitions)
        self.object_classes_removed.connect(self.cascade_remove_parameter_values_by_entity_class)
        self.relationship_classes_removed.connect(self.cascade_remove_relationships_by_class)
        self.relationship_classes_removed.connect(self.cascade_remove_parameter_definitions)
        self.relationship_classes_removed.connect(self.cascade_remove_parameter_values_by_entity_class)
        self.objects_removed.connect(self.cascade_remove_relationships_by_object)
        self.objects_removed.connect(self.cascade_remove_parameter_values_by_entity)
        self.relationships_removed.connect(self.cascade_remove_parameter_values_by_entity)
        self.parameter_definitions_removed.connect(self.cascade_remove_parameter_values_by_definition)
        # On cascade refresh
        self.object_classes_updated.connect(self.cascade_refresh_relationship_classes)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.objects_updated.connect(self.cascade_refresh_relationships_by_object)
        self.objects_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.relationships_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.parameter_definitions_updated.connect(self.cascade_refresh_parameter_values_by_definition)
        self.parameter_value_lists_updated.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_value_lists_removed.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_tags_updated.connect(self.cascade_refresh_parameter_definitions_by_tag)
        self.parameter_tags_removed.connect(self.cascade_refresh_parameter_definitions_by_tag)
        # Remove from cache (last, because of how cascade removal works at the moment)
        self.object_classes_removed.connect(lambda db_map_data: self.uncache_items("object class", db_map_data))
        self.objects_removed.connect(lambda db_map_data: self.uncache_items("object", db_map_data))
        self.relationship_classes_removed.connect(
            lambda db_map_data: self.uncache_items("relationship class", db_map_data)
        )
        self.relationships_removed.connect(lambda db_map_data: self.uncache_items("relationship", db_map_data))
        self.parameter_definitions_removed.connect(
            lambda db_map_data: self.uncache_items("parameter definition", db_map_data)
        )
        self.parameter_values_removed.connect(lambda db_map_data: self.uncache_items("parameter value", db_map_data))
        self.parameter_value_lists_removed.connect(
            lambda db_map_data: self.uncache_items("parameter value list", db_map_data)
        )
        self.parameter_tags_removed.connect(lambda db_map_data: self.uncache_items("parameter tag", db_map_data))
        # Do this last, so cache is ready when listeners receive signals
        self.signaller.connect_signals()

    @Slot(object)
    def receive_error_msg(self, db_map_error_log):
        msg = ""
        for db_map, error_log in db_map_error_log.items():
            database = "From " + db_map.codename + ":"
            formatted_log = format_string_list(error_log)
            msg += format_string_list([database, formatted_log])
        self._logger.error_box.emit("Error", msg)

    def cache_items(self, item_type, db_map_data):
        """Caches data for a given type.
        It works for both insert and update operations.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._cache.setdefault(db_map, {}).setdefault(item_type, {})[item["id"]] = item

    @Slot(object)
    def cache_parameter_definition_tags(self, db_map_data):
        """Caches parameter definition tags in the parameter definition dictionary.

        Args:
            db_map_data (dict): lists of parameter definition items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            for item in items:
                cache_item = self._cache[db_map]["parameter definition"][item.pop("parameter_definition_id")]
                cache_item.update(item)

    def uncache_items(self, item_type, db_map_data):
        """Removes data from cache.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        db_map_typed_data = {}
        for db_map, items in db_map_data.items():
            for item in items:
                if db_map not in self._cache:
                    continue
                cached_map = self._cache[db_map]
                if item_type not in cached_map:
                    continue
                cached_items = cached_map[item_type]
                item_id = item["id"]
                if item_id in cached_items:
                    item = cached_items.pop(item_id)
                    db_map_typed_data.setdefault(db_map, {}).setdefault(item_type, []).append(item)
        self.items_removed_from_cache.emit(db_map_typed_data)

    def update_icons(self, db_map_data):
        """Runs when object classes are added or updated. Setups icons for those classes.
        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        object_classes = [item for db_map, data in db_map_data.items() for item in data]
        self.icon_mngr.setup_object_pixmaps(object_classes)

    def entity_class_icon(self, db_map, entity_type, entity_class_id):
        """Returns an appropriate icon for a given entity class.

        Args:
            db_map (DiffDatabaseMapping)
            entity_type (str): either 'object class' or 'relationship class'
            entity_class_id (int)

        Returns:
            QIcon
        """
        entity_class = self.get_item(db_map, entity_type, entity_class_id)
        if not entity_class:
            return None
        if entity_type == "object class":
            return self.icon_mngr.object_icon(entity_class["name"])
        if entity_type == "relationship class":
            return self.icon_mngr.relationship_icon(entity_class["object_class_name_list"])

    def get_item(self, db_map, item_type, id_):
        """Returns the item of the given type in the given db map that has the given id,
        or an empty dict if not found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            id_ (int)

        Returns:
            dict
        """
        item = self._cache.get(db_map, {}).get(item_type, {}).get(id_)
        if item:
            return item
        _ = self._get_items_from_db(db_map, item_type)
        return self._cache.get(db_map, {}).get(item_type, {}).get(id_, {})

    def get_item_by_field(self, db_map, item_type, field, value):
        """Returns the first item of the given type in the given db map
        that has the given value for the given field
        Returns an empty dictionary if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            field (str)
            value

        Returns:
            dict
        """
        return next(iter(self.get_items_by_field(db_map, item_type, field, value)), {})

    def get_items_by_field(self, db_map, item_type, field, value):
        """Returns all items of the given type in the given db map that have the given value
        for the given field. Returns an empty list if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            field (str)
            value

        Returns:
            list
        """
        items = [x for x in self.get_items(db_map, item_type) if x.get(field) == value]
        if items:
            return items
        return [x for x in self._get_items_from_db(db_map, item_type) if x.get(field) == value]

    def get_items(self, db_map, item_type):
        """Returns all the items of the given type in the given db map,
        or an empty list if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)

        Returns:
            list
        """
        items = self._cache.get(db_map, {}).get(item_type, {})
        if items:
            return items.values()
        return self._get_items_from_db(db_map, item_type)

    def _get_items_from_db(self, db_map, item_type):
        """Returns all items of the given type in the given db map.
        Called by the above methods whenever they don't find what they're looking for in cache.
        """
        method_name_dict = {
            "object class": "get_object_classes",
            "object": "get_objects",
            "relationship class": "get_relationship_classes",
            "relationship": "get_relationships",
            "parameter definition": "get_parameter_definitions",
            "parameter value": "get_parameter_values",
            "parameter value list": "get_parameter_value_lists",
            "parameter tag": "get_parameter_tags",
        }
        method_name = method_name_dict.get(item_type)
        if not method_name:
            return []
        return getattr(self, method_name)(db_map)

    def get_field(self, db_map, item_type, id_, field):
        return self.get_item(db_map, item_type, id_).get(field)

    def get_value(self, db_map, item_type, id_, field, role=Qt.DisplayRole):
        """Returns the value or default value of a parameter.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter definition" or "parameter value"
            id_ (int)
            field (str): either "value" or "default_value"
            role (int, optional)
        """
        item = self.get_item(db_map, item_type, id_)
        if not item:
            return None
        key = "formatted_" + field
        if key not in item:
            try:
                parsed_value = from_database(item[field])
            except ParameterValueFormatError as error:
                display_data = "Error"
                tool_tip_data = str(error)
            else:
                display_data = self._display_data(parsed_value)
                tool_tip_data = self._tool_tip_data(parsed_value)
            fm = QFontMetrics(QFont("", 0))
            if isinstance(display_data, str):
                display_data = fm.elidedText(display_data, Qt.ElideRight, 500)
            if isinstance(tool_tip_data, str):
                tool_tip_data = fm.elidedText(tool_tip_data, Qt.ElideRight, 800)
            item[key] = {Qt.DisplayRole: display_data, Qt.ToolTipRole: tool_tip_data, Qt.EditRole: str(item[field])}
        return item[key].get(role)

    @staticmethod
    def _display_data(parsed_value):
        """Returns the value's database representation formatted for Qt.DisplayRole."""
        if isinstance(parsed_value, TimeSeries):
            return "Time series"
        if isinstance(parsed_value, Map):
            return "Map"
        if isinstance(parsed_value, DateTime):
            return str(parsed_value.value)
        if isinstance(parsed_value, Duration):
            return ", ".join(relativedelta_to_duration(delta) for delta in parsed_value.value)
        if isinstance(parsed_value, TimePattern):
            return "Time pattern"
        if isinstance(parsed_value, list):
            return str(parsed_value)
        return parsed_value

    @staticmethod
    def _tool_tip_data(parsed_value):
        """Returns the value's database representation formatted for Qt.ToolTipRole."""
        if isinstance(parsed_value, TimeSeriesFixedResolution):
            resolution = [relativedelta_to_duration(r) for r in parsed_value.resolution]
            resolution = ', '.join(resolution)
            return "Start: {}, resolution: [{}], length: {}".format(parsed_value.start, resolution, len(parsed_value))
        if isinstance(parsed_value, TimeSeriesVariableResolution):
            return "Start: {}, resolution: variable, length: {}".format(parsed_value.indexes[0], len(parsed_value))
        return None

    def get_object_classes(self, db_map, cache=True):
        """Returns object classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.object_class_sq)
        sort_key = lambda x: x["name"]
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("object class", {db_map: items})
        self.update_icons({db_map: items})
        return items

    def get_objects(self, db_map, class_id=None, cache=True):
        """Returns objects from database.

        Args:
            db_map (DiffDatabaseMapping)
            class_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.object_sq)
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        sort_key = lambda x: (x["class_id"], x["name"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("object", {db_map: items})
        return items

    def get_relationship_classes(self, db_map, ids=None, object_class_id=None, cache=True):
        """Returns relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            object_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_relationship_class_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        if object_class_id:
            ids = {x.id for x in db_map.query(db_map.relationship_class_sq).filter_by(object_class_id=object_class_id)}
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        sort_key = lambda x: x["name"]
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("relationship class", {db_map: items})
        return items

    def get_relationships(self, db_map, ids=None, class_id=None, object_id=None, cache=True):
        """Returns relationships from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            class_id (int, optional)
            object_id (int, optional)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_relationship_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        if object_id:
            ids = {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        sort_key = lambda x: (x["class_id"], x["object_name_list"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("relationship", {db_map: items})
        return items

    def get_object_parameter_definitions(self, db_map, ids=None, object_class_id=None, cache=True):
        """Returns object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            object_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        sq = db_map.object_parameter_definition_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        sort_key = lambda x: (x["object_class_name"], x["parameter_name"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("parameter definition", {db_map: items})
        return items

    def get_relationship_parameter_definitions(self, db_map, ids=None, relationship_class_id=None, cache=True):
        """Returns relationship parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            relationship_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        sq = db_map.relationship_parameter_definition_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        sort_key = lambda x: (x["relationship_class_name"], x["parameter_name"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("parameter definition", {db_map: items})
        return items

    def get_object_parameter_values(self, db_map, ids=None, object_class_id=None, cache=True):
        """Returns object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set)
            object_class_id (int)

        Returns:
            list: dictionary items
        """
        sq = db_map.object_parameter_value_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        sort_key = lambda x: (x["object_class_name"], x["object_name"], x["parameter_name"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("parameter value", {db_map: items})
        return items

    def get_relationship_parameter_values(self, db_map, ids=None, relationship_class_id=None, cache=True):
        """Returns relationship parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set)
            relationship_class_id (int)

        Returns:
            list: dictionary items
        """
        sq = db_map.relationship_parameter_value_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        sort_key = lambda x: (x["relationship_class_name"], x["object_class_name_list"], x["parameter_name"])
        items = sorted((x._asdict() for x in qry), key=sort_key)
        _ = cache and self.cache_items("parameter value", {db_map: items})
        return items

    def get_parameter_definitions(self, db_map, ids=None, entity_class_id=None, cache=True):
        """Returns both object and relationship parameter definitions.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            entity_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_definitions(
            db_map, ids=ids, object_class_id=entity_class_id, cache=cache
        ) + self.get_relationship_parameter_definitions(
            db_map, ids=ids, relationship_class_id=entity_class_id, cache=cache
        )

    def get_parameter_values(self, db_map, ids=None, entity_class_id=None, cache=True):
        """Returns both object and relationship parameter values.

        Args:
            db_map (DiffDatabaseMapping)
            ids (set, optional)
            entity_class_id (int, optional)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_values(
            db_map, ids=ids, object_class_id=entity_class_id, cache=cache
        ) + self.get_relationship_parameter_values(db_map, ids=ids, relationship_class_id=entity_class_id, cache=cache)

    def get_parameter_value_lists(self, db_map, cache=True):
        """Returns parameter value lists from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.wide_parameter_value_list_sq)
        items = [x._asdict() for x in qry]
        _ = cache and self.cache_items("parameter value list", {db_map: items})
        return items

    def get_parameter_tags(self, db_map, cache=True):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        qry = db_map.query(db_map.parameter_tag_sq)
        items = [x._asdict() for x in qry]
        _ = cache and self.cache_items("parameter tag", {db_map: items})
        return items

    @busy_effect
    def add_or_update_items(self, db_map_data, method_name, signal_name):
        """Adds or updates items in db.

        Args:
            db_map_data (dict): lists of items to add or update keyed by DiffDatabaseMapping
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
        """
        db_map_data_out = dict()
        error_log = dict()
        for db_map, items in db_map_data.items():
            items, error_log[db_map] = getattr(db_map, method_name)(*items)
            if not items.count():
                continue
            db_map_data_out[db_map] = [x._asdict() for x in items]
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_data_out.values()):
            getattr(self, signal_name).emit(db_map_data_out)

    def add_object_classes(self, db_map_data):
        """Adds object classes to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "object class"))

    def add_objects(self, db_map_data):
        """Adds objects to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "object"))

    def add_relationship_classes(self, db_map_data):
        """Adds relationship classes to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "relationship class"))

    def add_relationships(self, db_map_data):
        """Adds relationships to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "relationship"))

    def add_parameter_definitions(self, db_map_data):
        """Adds parameter definitions to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter definition"))

    def add_parameter_values(self, db_map_data):
        """Adds parameter values to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter value"))

    def add_checked_parameter_values(self, db_map_data):
        """Adds parameter values in db without checking integrity.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddCheckedParameterValuesCommand(self, db_map, data))

    def add_parameter_value_lists(self, db_map_data):
        """Adds parameter value lists to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter value list"))

    def add_parameter_tags(self, db_map_data):
        """Adds parameter tags to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter tag"))

    def update_object_classes(self, db_map_data):
        """Updates object classes in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "object class"))

    def update_objects(self, db_map_data):
        """Updates objects in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "object"))

    def update_relationship_classes(self, db_map_data):
        """Updates relationship classes in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "relationship class"))

    def update_relationships(self, db_map_data):
        """Updates relationships in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "relationship"))

    def update_parameter_definitions(self, db_map_data):
        """Updates parameter definitions in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter definition"))

    def update_parameter_values(self, db_map_data):
        """Updates parameter values in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter value"))

    def update_checked_parameter_values(self, db_map_data):
        """Updates parameter values in db without checking integrity.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateCheckedParameterValuesCommand(self, db_map, data))

    def update_parameter_value_lists(self, db_map_data):
        """Updates parameter value lists in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter value list"))

    def update_parameter_tags(self, db_map_data):
        """Updates parameter tags in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter tag"))

    def set_parameter_definition_tags(self, db_map_data):
        """Sets parameter definition tags in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(SetParameterDefinitionTagsCommand(self, db_map, data))

    def remove_items(self, db_map_typed_data):
        for db_map, typed_data in db_map_typed_data.items():
            self.undo_stack[db_map].push(RemoveItemsCommand(self, db_map, typed_data))

    @busy_effect
    def do_remove_items(self, db_map_typed_data):
        """Removes items from database.

        Args:
            db_map_typed_data (dict): lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
        """
        # Removing works this way in spinedb_api, all at once, probably because of cascading?
        db_map_object_classes = dict()
        db_map_objects = dict()
        db_map_relationship_classes = dict()
        db_map_relationships = dict()
        db_map_parameter_definitions = dict()
        db_map_parameter_values = dict()
        db_map_parameter_value_lists = dict()
        db_map_parameter_tags = dict()
        error_log = dict()
        for db_map, items_per_type in db_map_typed_data.items():
            object_classes = items_per_type.get("object class", ())
            objects = items_per_type.get("object", ())
            relationship_classes = items_per_type.get("relationship class", ())
            relationships = items_per_type.get("relationship", ())
            parameter_definitions = items_per_type.get("parameter definition", ())
            parameter_values = items_per_type.get("parameter value", ())
            parameter_value_lists = items_per_type.get("parameter value list", ())
            parameter_tags = items_per_type.get("parameter tag", ())
            try:
                db_map.remove_items(
                    object_class_ids={x['id'] for x in object_classes},
                    object_ids={x['id'] for x in objects},
                    relationship_class_ids={x['id'] for x in relationship_classes},
                    relationship_ids={x['id'] for x in relationships},
                    parameter_definition_ids={x['id'] for x in parameter_definitions},
                    parameter_value_ids={x['id'] for x in parameter_values},
                    parameter_value_list_ids={x['id'] for x in parameter_value_lists},
                    parameter_tag_ids={x['id'] for x in parameter_tags},
                )
            except SpineDBAPIError as err:
                error_log[db_map] = err
                continue
            db_map_object_classes[db_map] = object_classes
            db_map_objects[db_map] = objects
            db_map_relationship_classes[db_map] = relationship_classes
            db_map_relationships[db_map] = relationships
            db_map_parameter_definitions[db_map] = parameter_definitions
            db_map_parameter_values[db_map] = parameter_values
            db_map_parameter_value_lists[db_map] = parameter_value_lists
            db_map_parameter_tags[db_map] = parameter_tags
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_object_classes.values()):
            self.object_classes_removed.emit(db_map_object_classes)
        if any(db_map_objects.values()):
            self.objects_removed.emit(db_map_objects)
        if any(db_map_relationship_classes.values()):
            self.relationship_classes_removed.emit(db_map_relationship_classes)
        if any(db_map_relationships.values()):
            self.relationships_removed.emit(db_map_relationships)
        if any(db_map_parameter_definitions.values()):
            self.parameter_definitions_removed.emit(db_map_parameter_definitions)
        if any(db_map_parameter_values.values()):
            self.parameter_values_removed.emit(db_map_parameter_values)
        if any(db_map_parameter_value_lists.values()):
            self.parameter_value_lists_removed.emit(db_map_parameter_value_lists)
        if any(db_map_parameter_tags.values()):
            self.parameter_tags_removed.emit(db_map_parameter_tags)

    @staticmethod
    def _to_ids(db_map_data):
        return {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}

    @Slot(object)
    def cascade_remove_objects(self, db_map_data):
        """Removes objects in cascade when removing object classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_entities(self._to_ids(db_map_data), "object")
        if any(db_map_cascading_data.values()):
            self.objects_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_relationship_classes(self, db_map_data):
        """Removes relationship classes in cascade when removing object classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationship_classes(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.relationship_classes_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_relationships_by_class(self, db_map_data):
        """Removes relationships in cascade when removing objects.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_entities(self._to_ids(db_map_data), "relationship")
        if any(db_map_cascading_data.values()):
            self.relationships_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_relationships_by_object(self, db_map_data):
        """Removes relationships in cascade when removing relationship classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationships(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.relationships_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_parameter_definitions(self, db_map_data):
        """Removes parameter definitions in cascade when removing entity classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter definition")
        if any(db_map_cascading_data.values()):
            self.parameter_definitions_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_parameter_values_by_entity_class(self, db_map_data):
        """Removes parameter values in cascade when removing entity classes.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter value")
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_parameter_values_by_entity(self, db_map_data):
        """Removes parameter values in cascade when removing entity classes when removing entities.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_entity(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_remove_parameter_values_by_definition(self, db_map_data):
        """Removes parameter values in cascade when when removing parameter definitions.

        Args:
            db_map_data (dict): lists of removed items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_definition(self._to_ids(db_map_data))
        if any(db_map_cascading_data.values()):
            self.parameter_values_removed.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_relationship_classes(self, db_map_data):
        """Refreshes cached relationship classes when updating object classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationship_classes(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_relationship_classes(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self.relationship_classes_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_relationships_by_object(self, db_map_data):
        """Refreshed cached relationships in cascade when updating objects.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationships(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_relationships(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self.relationships_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_definitions(self, db_map_data):
        """Refreshes cached parameter definitions in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter definition")
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_definitions_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_definitions_by_value_list(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_value_list(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_definitions_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_tag(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_definitions_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_values_by_entity_class(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entity classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_data(self._to_ids(db_map_data), "parameter value")
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_values_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_values_by_entity(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating entities.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_entity(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_values_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_values_by_definition(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating parameter definitions.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_definition(self._to_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data}, cache=False)
            for db_map, data in db_map_cascading_data.items()
        }
        self._parameter_values_updated.emit(db_map_cascading_data)

    def find_cascading_relationship_classes(self, db_map_ids):
        """Finds and returns cascading relationship classes for the given object class ids."""
        db_map_cascading_data = dict()
        for db_map, object_class_ids in db_map_ids.items():
            object_class_ids = {str(id_) for id_ in object_class_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship class")
                if object_class_ids.intersection(item["object_class_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_entities(self, db_map_ids, item_type):
        """Finds and returns cascading entities for the given entity class ids."""
        db_map_cascading_data = dict()
        for db_map, class_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, item_type) if item["class_id"] in class_ids
            ]
        return db_map_cascading_data

    def find_cascading_relationships(self, db_map_ids):
        """Finds and returns cascading relationships for the given object ids."""
        db_map_cascading_data = dict()
        for db_map, object_ids in db_map_ids.items():
            object_ids = {str(id_) for id_ in object_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship")
                if object_ids.intersection(item["object_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_parameter_data(self, db_map_ids, item_type):
        """Finds and returns cascading parameter definitions or values for the given entity class ids."""
        db_map_cascading_data = dict()
        for db_map, entity_class_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, item_type)
                if entity_class_ids.intersection([item.get("object_class_id"), item.get("relationship_class_id")])
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_value_list(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter value list ids."""
        db_map_cascading_data = dict()
        for db_map, value_list_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter definition")
                if item["value_list_id"] in value_list_ids
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_tag(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter tag ids."""
        db_map_cascading_data = dict()
        for db_map, tag_ids in db_map_ids.items():
            tag_ids = {str(id_) for id_ in tag_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter definition")
                if tag_ids.intersection((item["parameter_tag_id_list"] or "0").split(","))
            ]  # NOTE: 0 is 'untagged'
        return db_map_cascading_data

    def find_cascading_parameter_values_by_entity(self, db_map_ids):
        """Finds and returns cascading parameter values for the given entity ids."""
        db_map_cascading_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter value")
                if entity_ids.intersection([item.get("object_id"), item.get("relationship_id")])
            ]
        return db_map_cascading_data

    def find_cascading_parameter_values_by_definition(self, db_map_ids):
        """Finds and returns cascading parameter values for the given parameter definition ids."""
        db_map_cascading_data = dict()
        for db_map, definition_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "parameter value") if item["parameter_id"] in definition_ids
            ]
        return db_map_cascading_data

    @Slot(object)
    def do_add_parameter_definitions(self, db_map_data):
        """Adds parameter definitions in extended format given data in compact format.

        Args:
            db_map_data (dict): lists of parameter definition items keyed by DiffDatabaseMapping
        """
        d = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in items})
            for db_map, items in db_map_data.items()
        }
        self.parameter_definitions_added.emit(d)

    @Slot(object)
    def do_add_parameter_values(self, db_map_data):
        """Adds parameter values in extended format given data in compact format.

        Args:
            db_map_data (dict): lists of parameter value items keyed by DiffDatabaseMapping
        """
        d = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in items})
            for db_map, items in db_map_data.items()
        }
        self.parameter_values_added.emit(d)

    @Slot(object)
    def do_update_parameter_definitions(self, db_map_data):
        """Updates parameter definitions in extended format given data in compact format.

        Args:
            db_map_data (dict): lists of parameter definition items keyed by DiffDatabaseMapping
        """
        d = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in items})
            for db_map, items in db_map_data.items()
        }
        self.parameter_definitions_updated.emit(d)

    @Slot(object)
    def do_update_parameter_values(self, db_map_data):
        """Updates parameter values in extended format given data in compact format.

        Args:
            db_map_data (dict): lists of parameter value items keyed by DiffDatabaseMapping
        """
        d = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in items})
            for db_map, items in db_map_data.items()
        }
        self.parameter_values_updated.emit(d)
