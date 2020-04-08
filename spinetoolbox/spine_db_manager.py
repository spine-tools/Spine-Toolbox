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

from PySide2.QtCore import Qt, QObject, Signal, Slot
from PySide2.QtWidgets import QMessageBox, QDialog, QCheckBox
from PySide2.QtGui import QKeySequence, QIcon, QFontMetrics, QFont
from spinedb_api import (
    Array,
    create_new_spine_database,
    DateTime,
    DiffDatabaseMapping,
    Duration,
    from_database,
    IndexedValue,
    is_empty,
    Map,
    ParameterValueFormatError,
    relativedelta_to_duration,
    SpineDBAPIError,
    SpineDBVersionError,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    TimePattern,
    to_database,
)
from .helpers import IconManager, busy_effect, format_string_list
from .spine_db_signaller import SpineDBSignaller
from .spine_db_fetcher import SpineDBFetcher
from .spine_db_commands import (
    AgedUndoStack,
    AddItemsCommand,
    AddCheckedParameterValuesCommand,
    UpdateItemsCommand,
    UpdateCheckedParameterValuesCommand,
    SetParameterDefinitionTagsCommand,
    RemoveItemsCommand,
)
from .widgets.data_store_manage_items_dialog import CommitDialog
from .mvcmodels.shared import PARSED_ROLE


@busy_effect
def do_create_new_spine_database(url):
    """Creates a new spine database at the given url."""
    create_new_spine_database(url)


class SpineDBManager(QObject):
    """Class to manage DBs within a project.

    TODO: Expand description, how it works, the cache, the signals, etc.
    """

    session_refreshed = Signal(set)
    session_committed = Signal(set)
    session_rolled_back = Signal(set)
    # Added
    object_classes_added = Signal(object)
    objects_added = Signal(object)
    relationship_classes_added = Signal(object)
    relationships_added = Signal(object)
    parameter_definitions_added = Signal(object)
    parameter_values_added = Signal(object)
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
    parameter_values_updated = Signal(object)
    parameter_value_lists_updated = Signal(object)
    parameter_tags_updated = Signal(object)
    parameter_definition_tags_set = Signal(object)
    # Uncached
    items_removed_from_cache = Signal(object)

    _GROUP_SEP = " \u01C0 "

    def __init__(self, settings, logger, project):
        """Initializes the instance.

        Args:
            settings (QSettings): Toolbox settings
            logger (LoggingInterface): a general, non-database-specific logger
            project (SpineToolboxProject)
        """
        super().__init__(project)
        self._general_logger = logger
        self._db_specific_loggers = dict()
        self._db_maps = {}
        self._cache = {}
        self.qsettings = settings
        self.undo_stack = {}
        self.undo_action = {}
        self.redo_action = {}
        self.icon_mngr = IconManager()
        self.signaller = SpineDBSignaller(self)
        self.fetchers = []
        self.connect_signals()

    @property
    def db_maps(self):
        return set(self._db_maps.values())

    def create_new_spine_database(self, url):
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
            do_create_new_spine_database(url)
            self._general_logger.msg_success.emit("New Spine db successfully created at '{0}'.".format(url))
        except SpineDBAPIError as e:
            self._general_logger.msg_error.emit("Unable to create new Spine db at '{0}': {1}.".format(url, e))

    def close_session(self, url):
        """Pops any db map on the given url and closes its connection.

        Args:
            url (str)
        """
        db_map = self._db_maps.pop(url, None)
        if db_map is None:
            return
        db_map.connection.close()
        if db_map.codename in self._db_specific_loggers:
            del self._db_specific_loggers[db_map.codename]

    def close_all_sessions(self):
        """Closes connections to all database mappings."""
        for db_map in self._db_maps.values():
            if not db_map.connection.closed:
                db_map.connection.close()
        self._db_specific_loggers.clear()

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
        """Returns a db_map for given listener.

        Args:
            listener (DataStoreForm)
            url (DiffDatabaseMapping)
        """
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
        """Removes listener for a given db_map.

        Args:
            db_map (DiffDatabaseMapping)
            listener (DataStoreForm)
        """
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

    def set_logger_for_db_map(self, logger, db_map):
        if db_map.codename is not None:
            self._db_specific_loggers[db_map.codename] = logger

    def unset_logger_for_db_map(self, db_map):
        if db_map.codename in self._db_specific_loggers:
            del self._db_specific_loggers[db_map.codename]

    def fetch_db_maps_for_listener(self, listener, *db_maps):
        """Fetches given db_map for given listener.

        Args:
            db_map (DiffDatabaseMapping)
            listener (DataStoreForm)
        """
        fetcher = SpineDBFetcher(self, listener, *db_maps)
        self.fetchers.append(fetcher)
        fetcher.run()

    def refresh_session(self, *db_maps):
        refreshed_db_maps = set()
        for db_map in db_maps:
            if self._cache.pop(db_map, None) is not None:
                refreshed_db_maps.add(db_map)
        if refreshed_db_maps:
            self.session_refreshed.emit(refreshed_db_maps)

    def commit_session(self, *db_maps, rollback_if_no_msg=False):
        error_log = {}
        committed_db_maps = set()
        rolled_db_maps = set()
        for db_map in db_maps:
            if self.undo_stack[db_map].isClean():
                continue
            commit_msg = self._get_commit_msg(db_map)
            try:
                if commit_msg:
                    db_map.commit_session(commit_msg)
                    committed_db_maps.add(db_map)
                    self.undo_stack[db_map].setClean()
                elif rollback_if_no_msg:
                    db_map.rollback_session()
                    rolled_db_maps.add(db_map)
                    self._cache.pop(db_map, None)
                    self.undo_stack[db_map].setClean()
            except SpineDBAPIError as e:
                error_log[db_map] = e.msg
        if any(error_log.values()):
            self.error_msg(error_log)
        if committed_db_maps:
            self.session_committed.emit(committed_db_maps)
        if rolled_db_maps:
            self.session_rolled_back.emit(rolled_db_maps)

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
            if self.undo_stack[db_map].isClean():
                continue
            try:
                db_map.rollback_session()
                rolled_db_maps.add(db_map)
                self.undo_stack[db_map].clear()
                del self._cache[db_map]
            except SpineDBAPIError as e:
                error_log[db_map] = e.msg
        if any(error_log.values()):
            self.error_msg(error_log)
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
            self.error_msg({db_map: e.msg})
            return False

    def _rollback_db_map_session(self, db_map):
        try:
            db_map.rollback_session()
            return True
        except SpineDBAPIError as e:
            self.error_msg({db_map: e.msg})
            return False

    def ok_to_close(self, db_map):
        """Prompts the user to commit or rollback changes to given database map.

        Returns:
            bool: True if successfully committed or rolled back, False otherwise
        """
        if self.undo_stack[db_map].isClean():
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
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)
        # On cascade remove
        self.object_classes_removed.connect(self.cascade_remove_objects)
        self.object_classes_removed.connect(self.cascade_remove_relationship_classes)
        self.object_classes_removed.connect(self.cascade_remove_parameter_definitions)
        self.relationship_classes_removed.connect(self.cascade_remove_relationships_by_class)
        self.relationship_classes_removed.connect(self.cascade_remove_parameter_definitions)
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
        # Signaller (after caching, so items are there when listeners receive signals)
        self.signaller.connect_signals()
        # Remove from cache (after signaller, so views are able to find items until the very last moment)
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

    def error_msg(self, db_map_error_log):
        msg = ""
        for db_map, error_log in db_map_error_log.items():
            database = "From " + db_map.codename + ":"
            formatted_log = format_string_list(error_log)
            msg += format_string_list([database, formatted_log])
        for db_map in db_map_error_log:
            logger = self._db_specific_loggers.get(db_map.codename)
            if logger is not None:
                logger.error_box.emit("Error", msg)

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
                item = item.copy()
                cache_item = self._cache[db_map]["parameter definition"][item.pop("id")]
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
                db_map_cache_data = self._cache.get(db_map)
                if db_map_cache_data is None:
                    continue
                cache_items = db_map_cache_data.get(item_type)
                if cache_items is None:
                    continue
                removed_item = cache_items.pop(item["id"], None)
                if removed_item:
                    db_map_typed_data.setdefault(db_map, {}).setdefault(item_type, []).append(removed_item)
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
        return [x for x in self.get_items(db_map, item_type) if x.get(field) == value]

    def get_items(self, db_map, item_type):
        """Returns all the items of the given type in the given db map,
        or an empty list if none found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)

        Returns:
            list
        """
        return self._cache.get(db_map, {}).get(item_type, {}).values()

    def get_field(self, db_map, item_type, id_, field):
        return self.get_item(db_map, item_type, id_).get(field)

    @staticmethod
    def _display_data(parsed_data):
        """Returns the value's database representation formatted for Qt.DisplayRole."""
        if isinstance(parsed_data, TimeSeries):
            display_data = "Time series"
        elif isinstance(parsed_data, Map):
            display_data = "Map"
        elif isinstance(parsed_data, Array):
            display_data = "Array"
        elif isinstance(parsed_data, DateTime):
            display_data = str(parsed_data.value)
        elif isinstance(parsed_data, Duration):
            display_data = ", ".join(relativedelta_to_duration(delta) for delta in parsed_data.value)
        elif isinstance(parsed_data, TimePattern):
            display_data = "Time pattern"
        elif isinstance(parsed_data, ParameterValueFormatError):
            display_data = "Error"
        else:
            display_data = str(parsed_data)
        if isinstance(display_data, str):
            fm = QFontMetrics(QFont("", 0))
            display_data = fm.elidedText(display_data, Qt.ElideRight, 500)
        return display_data

    @staticmethod
    def _tool_tip_data(parsed_data):
        """Returns the value's database representation formatted for Qt.ToolTipRole."""
        if isinstance(parsed_data, TimeSeriesFixedResolution):
            resolution = [relativedelta_to_duration(r) for r in parsed_data.resolution]
            resolution = ', '.join(resolution)
            tool_tip_data = "Start: {}, resolution: [{}], length: {}".format(
                parsed_data.start, resolution, len(parsed_data)
            )
        elif isinstance(parsed_data, TimeSeriesVariableResolution):
            tool_tip_data = "Start: {}, resolution: variable, length: {}".format(
                parsed_data.indexes[0], len(parsed_data)
            )
        elif isinstance(parsed_data, ParameterValueFormatError):
            tool_tip_data = str(parsed_data)
        else:
            tool_tip_data = None
        if isinstance(tool_tip_data, str):
            fm = QFontMetrics(QFont("", 0))
            tool_tip_data = fm.elidedText(tool_tip_data, Qt.ElideRight, 800)
        return tool_tip_data

    def get_value(self, db_map, item_type, id_, role=Qt.DisplayRole):
        """Returns the value or default value of a parameter.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter definition" or "parameter value"
            id_ (int): The parameter value or definition id
            role (int, optional)
        """
        item = self.get_item(db_map, item_type, id_)
        if not item:
            return None
        field = {"parameter value": "value", "parameter definition": "default_value"}[item_type]
        if role == Qt.EditRole:
            return item[field]
        key = "formatted_value"
        if key not in item:
            try:
                item[key] = from_database(item[field])
            except ParameterValueFormatError as error:
                item[key] = error
        if role == Qt.DisplayRole:
            return self._display_data(item[key])
        if role == Qt.ToolTipRole:
            return self._tool_tip_data(item[key])
        if role == PARSED_ROLE:
            return item[key]
        return None

    def get_value_indexes(self, db_map, item_type, id_):
        """Returns the value or default value indexes of a parameter.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter definition" or "parameter value"
            id_ (int): The parameter value or definition id
        """
        parsed_value = self.get_value(db_map, item_type, id_, role=PARSED_ROLE)
        if isinstance(parsed_value, IndexedValue):
            return parsed_value.indexes
        return [""]

    def get_value_index(self, db_map, item_type, id_, index, role=Qt.DisplayRole):
        """Returns the value or default value of a parameter for a given index.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter definition" or "parameter value"
            id_ (int): The parameter value or definition id
            index: The index to retrieve
            role (int, optional)
        """
        parsed_value = self.get_value(db_map, item_type, id_, role=PARSED_ROLE)
        if isinstance(parsed_value, IndexedValue):
            parsed_value = parsed_value.get_value(index)
        if role == Qt.EditRole:
            return to_database(parsed_value)
        if role == Qt.DisplayRole:
            return self._display_data(parsed_value)
        if role == Qt.ToolTipRole:
            return self._tool_tip_data(parsed_value)
        if role == PARSED_ROLE:
            return parsed_value
        return None

    def _expand_map(self, map_to_expand, preceding_indexes=None):
        """
        NOTE: Not in use at the moment.
        Expands map iteratively.

        Args:
            map_to_expand (spinedb_api.Map): a map to expand.
            preceding_indexes (list): a list of indexes indexing a nested map

        Return:
            dict: mapping each index string to the corresponding scalar value
        """
        current_indexes = map_to_expand.indexes
        if not current_indexes:
            return []
        if preceding_indexes is None:
            preceding_indexes = list()
        values = dict()
        for index, value in zip(current_indexes, map_to_expand.values):
            index_list = preceding_indexes + [index]
            if isinstance(value, Map):
                nested_values = self._expand_map(value, index_list)
                values.update(nested_values)
            else:
                index_as_string = ", ".join([str(i) for i in index_list])
                values[index_as_string] = value
        return values

    @staticmethod
    def get_db_items(query, order_by_fields):
        return sorted((x._asdict() for x in query), key=lambda x: tuple(x[f] for f in order_by_fields))

    @staticmethod
    def _make_query(db_map, sq_name, ids=()):
        sq = getattr(db_map, sq_name)
        query = db_map.query(sq)
        if ids:
            query = query.filter(sq.c.id.in_(ids))
        return query

    def get_object_classes(self, db_map, ids=()):
        """Returns object classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "object_class_sq", ids=ids), ("name",))

    def get_objects(self, db_map, ids=()):
        """Returns objects from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "object_sq", ids=ids), ("class_id", "name"))

    def get_relationship_classes(self, db_map, ids=()):
        """Returns relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "wide_relationship_class_sq", ids=ids), ("name",))

    def get_relationships(self, db_map, ids=()):
        """Returns relationships from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "wide_relationship_sq", ids=ids), ("class_id", "object_name_list")
        )

    def get_object_parameter_definitions(self, db_map, ids=()):
        """Returns object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        items = self.get_db_items(
            self._make_query(db_map, "object_parameter_definition_sq", ids=ids), ("object_class_name", "parameter_name")
        )
        return items

    def get_relationship_parameter_definitions(self, db_map, ids=()):
        """Returns relationship parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "relationship_parameter_definition_sq", ids=ids),
            ("relationship_class_name", "parameter_name"),
        )

    def get_parameter_definitions(self, db_map, ids=()):
        """Returns both object and relationship parameter definitions.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_definitions(db_map, ids=ids) + self.get_relationship_parameter_definitions(
            db_map, ids=ids
        )

    def get_object_parameter_values(self, db_map, ids=()):
        """Returns object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "object_parameter_value_sq", ids=ids),
            ("object_class_name", "object_name", "parameter_name"),
        )

    def get_relationship_parameter_values(self, db_map, ids=()):
        """Returns relationship parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "relationship_parameter_value_sq", ids=ids),
            ("relationship_class_name", "object_name_list", "parameter_name"),
        )

    def get_parameter_values(self, db_map, ids=()):
        """Returns both object and relationship parameter values.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_object_parameter_values(db_map, ids=ids) + self.get_relationship_parameter_values(
            db_map, ids=ids
        )

    def get_parameter_value_lists(self, db_map, ids=()):
        """Returns parameter value lists from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "wide_parameter_value_list_sq", ids=ids), ("name",))

    def get_parameter_tags(self, db_map, ids=()):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "parameter_tag_sq", ids=ids), ("tag",))

    def get_parameter_definition_tags(self, db_map, ids=()):
        """Returns parameter definition tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "wide_parameter_definition_tag_sq", ids=ids), ("id",))

    @busy_effect
    def add_or_update_items(self, db_map_data, method_name, get_method_name, signal_name):
        """Adds or updates items in db.

        Args:
            db_map_data (dict): lists of items to add or update keyed by DiffDatabaseMapping
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            get_method_name (str): attribute of SpineDBManager to call for getting affected items
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
        """
        db_map_data_out = dict()
        error_log = dict()
        for db_map, items in db_map_data.items():
            ids, error_log[db_map] = getattr(db_map, method_name)(*items)
            if not ids:
                continue
            db_map_data_out[db_map] = getattr(self, get_method_name)(db_map, ids=ids)
        if any(error_log.values()):
            self.error_msg(error_log)
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

    def update_expanded_parameter_values(self, db_map_data):
        """Updates expanded parameter values in db without checking integrity.

        Args:
            db_map_data (dict): lists of expanded items to update keyed by DiffDatabaseMapping
        """
        for db_map, expanded_data in db_map_data.items():
            packed_data = {}
            for item in expanded_data:
                packed_data.setdefault(item["id"], {})[item["index"]] = item["value"]
            items = []
            for id_, indexed_values in packed_data.items():
                parsed_data = self.get_value(db_map, "parameter value", id_, role=PARSED_ROLE)
                if isinstance(parsed_data, IndexedValue):
                    for index, value in indexed_values.items():
                        parsed_data.set_value(index, value)
                    value = to_database(parsed_data)
                else:
                    value = next(iter(indexed_values.values()))
                item = {"id": id_, "value": value}
                items.append(item)
            self.undo_stack[db_map].push(UpdateCheckedParameterValuesCommand(self, db_map, items))

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
            self.error_msg(error_log)
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
            db_map: self.get_relationship_classes(db_map, ids={x["id"] for x in data})
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
            db_map: self.get_relationships(db_map, ids={x["id"] for x in data})
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
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_definitions_updated.emit(db_map_cascading_data)

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
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_definitions_updated.emit(db_map_cascading_data)

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
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_definitions_updated.emit(db_map_cascading_data)

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
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_values_updated.emit(db_map_cascading_data)

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
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_values_updated.emit(db_map_cascading_data)

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
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_values_updated.emit(db_map_cascading_data)

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
                item for item in self.get_items(db_map, item_type) if item["entity_class_id"] in entity_class_ids
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
                item for item in self.get_items(db_map, "parameter value") if item["entity_id"] in entity_ids
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
