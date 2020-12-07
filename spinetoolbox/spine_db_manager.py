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
    is_empty,
    create_new_spine_database,
    DiffDatabaseMapping,
    SpineDBVersionError,
    SpineDBAPIError,
    get_data_for_import,
    from_database,
    to_database,
    relativedelta_to_duration,
    ParameterValueFormatError,
    IndexedValue,
    Array,
    DateTime,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    TimePattern,
    Map,
)
from .spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from .helpers import IconManager, busy_effect, format_string_list
from .spine_db_signaller import SpineDBSignaller
from .spine_db_fetcher import SpineDBFetcher
from .spine_db_commands import (
    AgedUndoStack,
    AgedUndoCommand,
    AddItemsCommand,
    CheckAddParameterValuesCommand,
    UpdateItemsCommand,
    CheckUpdateParameterValuesCommand,
    RemoveItemsCommand,
)
from .widgets.commit_dialog import CommitDialog
from .mvcmodels.shared import PARSED_ROLE


@busy_effect
def do_create_new_spine_database(url):
    """Creates a new spine database at the given url."""
    create_new_spine_database(url)


class SpineDBManager(QObject):
    """Class to manage DBs within a project.

    TODO: Expand description, how it works, the cache, the signals, etc.
    """

    database_created = Signal(object)
    session_refreshed = Signal(set)
    session_committed = Signal(set, object)
    session_rolled_back = Signal(set)
    # Added
    scenarios_added = Signal(object)
    alternatives_added = Signal(object)
    object_classes_added = Signal(object)
    objects_added = Signal(object)
    relationship_classes_added = Signal(object)
    relationships_added = Signal(object)
    entity_groups_added = Signal(object)
    parameter_definitions_added = Signal(object)
    parameter_values_added = Signal(object)
    parameter_value_lists_added = Signal(object)
    parameter_tags_added = Signal(object)
    features_added = Signal(object)
    tools_added = Signal(object)
    tool_features_added = Signal(object)
    tool_feature_methods_added = Signal(object)
    # Removed
    scenarios_removed = Signal(object)
    alternatives_removed = Signal(object)
    object_classes_removed = Signal(object)
    objects_removed = Signal(object)
    relationship_classes_removed = Signal(object)
    relationships_removed = Signal(object)
    entity_groups_removed = Signal(object)
    parameter_definitions_removed = Signal(object)
    parameter_values_removed = Signal(object)
    parameter_value_lists_removed = Signal(object)
    parameter_tags_removed = Signal(object)
    features_removed = Signal(object)
    tools_removed = Signal(object)
    tool_features_removed = Signal(object)
    tool_feature_methods_removed = Signal(object)
    # Updated
    scenarios_updated = Signal(object)
    alternatives_updated = Signal(object)
    object_classes_updated = Signal(object)
    objects_updated = Signal(object)
    relationship_classes_updated = Signal(object)
    relationships_updated = Signal(object)
    parameter_definitions_updated = Signal(object)
    parameter_values_updated = Signal(object)
    parameter_value_lists_updated = Signal(object)
    parameter_tags_updated = Signal(object)
    parameter_definition_tags_set = Signal(object)
    features_updated = Signal(object)
    tools_updated = Signal(object)
    tool_features_updated = Signal(object)
    tool_feature_methods_updated = Signal(object)
    # Uncached
    items_removed_from_cache = Signal(object)
    # Internal
    _scenario_alternatives_added = Signal(object)
    _scenario_alternatives_updated = Signal(object)
    _scenario_alternatives_removed = Signal(object)
    _parameter_definition_tags_added = Signal(object)
    _parameter_definition_tags_removed = Signal(object)

    _GROUP_SEP = " \u01C0 "

    def __init__(self, settings, logger, project):
        """Initializes the instance.

        Args:
            settings (QSettings): Toolbox settings
            logger (LoggingInterface): a general, non-database-specific logger
            project (SpineToolboxProject)
        """
        super().__init__(project)
        self._project = project
        self._general_logger = logger
        self._db_specific_loggers = dict()
        self._db_maps = {}
        self._cache = {}
        self._db_editors = {}
        self.qsettings = settings
        self.undo_stack = {}
        self.undo_action = {}
        self.redo_action = {}
        self.icon_mngr = {}
        self.signaller = SpineDBSignaller(self)
        self._fetchers = []
        self.connect_signals()

    @property
    def db_maps(self):
        return set(self._db_maps.values())

    def db_map(self, url):
        """
        Returns a database mapping for given URL.

        Args:
            url (str): a database URL

        Returns:
            DiffDatabaseMapping: a database map or None if not found
        """
        return self._db_maps.get(url)

    @property
    def db_editors(self):
        return set(self._db_editors.values())

    def open_db_maps(self, url):
        for db_editor in self.db_editors:
            for db_url, db_map in zip(db_editor.db_urls, db_editor.db_maps):
                if url == db_url:
                    yield db_map

    def create_new_spine_database(self, url):
        if url in set(url for db_editor in self.db_editors for url in db_editor.db_urls):
            message = (
                f"The db at <b>{url}</b> is open in a Spine db editor. "
                "Please close all Spine db editors using this url and try again."
            )
            self._general_logger.error_box.emit("Error", message)
            return
        try:
            if not is_empty(url):
                msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText(f"The database at <b>'{url}'</b> is not empty.")
                msg.setInformativeText("Do you want to overwrite it?")
                msg.addButton("Overwrite", QMessageBox.AcceptRole)
                msg.addButton("Cancel", QMessageBox.RejectRole)
                ret = msg.exec_()  # Show message box
                if ret != QMessageBox.AcceptRole:
                    return
            do_create_new_spine_database(url)
            self._general_logger.msg_success.emit(f"New Spine db successfully created at '{url}'.")
        except SpineDBAPIError as e:
            self._general_logger.msg_error.emit(f"Unable to create new Spine db at '{url}': {e}.")
        else:
            self.database_created.emit(url)

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

    def show_spine_db_editor(self, db_url_codenames, logger, create=False):
        """Creates a new SpineDBEditor and shows it.

        Args:
            db_url_codenames (dict): Mapping db urls to codenames.
            logger (LoggingInterface): Where to log SpineDBAPIError
        """
        key = tuple(db_url_codenames.keys())
        db_editor = self._db_editors.get(key)
        if db_editor is None:
            db_maps = [
                self.get_db_map(url, logger, codename=codename, create=create)
                for url, codename in db_url_codenames.items()
            ]
            if not all(db_maps):
                return False
            self._db_editors[key] = db_editor = SpineDBEditor(self, *db_maps)
            db_editor.destroyed.connect(lambda: self._db_editors.pop(key))
            db_editor.show()
        else:
            if db_editor.windowState() & Qt.WindowMinimized:
                db_editor.setWindowState(db_editor.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            db_editor.activateWindow()
        return True

    def get_db_map(self, url, logger, codename=None, upgrade=False, create=False):
        """Returns a DiffDatabaseMapping instance from url if possible, None otherwise.
        If needed, asks the user to upgrade to the latest db version.

        Args:
            url (str, URL)
            logger (LoggingInterface): Where to log SpineDBAPIError
            upgrade (bool, optional)
            codename (str, NoneType, optional)

        Returns:
            DiffDatabaseMapping, NoneType
        """
        try:
            return self._do_get_db_map(url, codename, upgrade, create)
        except SpineDBVersionError:
            msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
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
            return self.get_db_map(url, logger, codename=codename, upgrade=True, create=create)
        except SpineDBAPIError as err:
            logger.msg_error.emit(err.msg)
            return None

    @busy_effect
    def _do_get_db_map(self, url, codename, upgrade, create):
        """Returns a memorized DiffDatabaseMapping instance from url.
        Called by `get_db_map`.

        Args:
            url (str, URL)
            codename (str, NoneType)
            upgrade (bool)
            create (bool)

        Returns:
            DiffDatabaseMapping
        """
        url = str(url)
        db_map = self._db_maps.get(url)
        if db_map is not None:
            if codename is not None:
                db_map.codename = codename
            return db_map
        db_map = self._db_maps[url] = DiffDatabaseMapping(url, codename=codename, upgrade=upgrade, create=create)
        stack = self.undo_stack[db_map] = AgedUndoStack(self)
        undo_action = self.undo_action[db_map] = stack.createUndoAction(self)
        redo_action = self.redo_action[db_map] = stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        return db_map

    def register_listener(self, ds_form, *db_maps):
        """Register given ds_form as listener for all given db_map's signals.

        Args:
            ds_form (SpineDBEditor)
            db_maps (DiffDatabaseMapping)
        """
        for db_map in db_maps:
            self.signaller.add_db_map_listener(db_map, ds_form)
            stack = self.undo_stack[db_map]
            stack.indexChanged.connect(ds_form.update_undo_redo_actions)
            stack.cleanChanged.connect(ds_form.update_commit_enabled)

    def unregister_listener(self, ds_form, db_map):
        """Unregisters given ds_form from given db_map signals.

        Args:
            ds_form (SpineDBEditor)
            db_map (DiffDatabaseMapping)
        """
        listeners = self.signaller.db_map_listeners(db_map) - {ds_form}
        if not listeners:
            if not self.ok_to_close(db_map):
                return False
            self.close_session(db_map.db_url)
        self.signaller.remove_db_map_listener(db_map, ds_form)
        self.undo_stack[db_map].indexChanged.disconnect(ds_form.update_undo_redo_actions)
        self.undo_stack[db_map].cleanChanged.disconnect(ds_form.update_commit_enabled)
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
            listener (SpineDBEditor)
            *db_maps: database maps to fetch
        """
        fetcher = SpineDBFetcher(self, listener)
        fetcher.finished.connect(self._clean_up_fetcher)
        self._fetchers.append(fetcher)
        fetcher.fetch(db_maps)

    @Slot(object)
    def _clean_up_fetcher(self, fetcher):
        """
        Cleans up things after fetcher has finished working.

        Args:
            fetcher (SpineDBFetcher): the fetcher to clean up
        """
        fetcher.clean_up()
        fetcher.deleteLater()
        self._fetchers.remove(fetcher)

    @Slot()
    def _stop_fetchers(self):
        """
        Quits all fetchers and deletes them.
        """
        for fetcher in self._fetchers:
            fetcher.quit()
            fetcher.deleteLater()
        self._fetchers.clear()

    def refresh_session(self, *db_maps):
        refreshed_db_maps = set()
        for db_map in db_maps:
            if self._cache.pop(db_map, None) is not None:
                refreshed_db_maps.add(db_map)
        if refreshed_db_maps:
            self.session_refreshed.emit(refreshed_db_maps)

    def commit_session(self, *db_maps, cookie=None):
        """
        Commits the current session.

        Args:
            *db_maps: database maps to commit
            cookie (object, optional): a free form identifier which will be forwarded to ``session_committed`` signal
        """
        error_log = {}
        committed_db_maps = set()
        changed_db_maps = [
            db_map for db_map in db_maps if not self.undo_stack[db_map].isClean() or db_map.has_pending_changes()
        ]
        if not changed_db_maps:
            return
        db_names = ", ".join([db_map.codename for db_map in changed_db_maps])
        commit_msg = self._get_commit_msg(db_names)
        if not commit_msg:
            return
        for db_map in changed_db_maps:
            try:
                db_map.commit_session(commit_msg)
                committed_db_maps.add(db_map)
                self.undo_stack[db_map].setClean()
            except SpineDBAPIError as e:
                error_log[db_map] = e.msg
        if any(error_log.values()):
            self.error_msg(error_log)
        if committed_db_maps:
            self.session_committed.emit(committed_db_maps, cookie)

    @staticmethod
    def _get_commit_msg(db_names):
        dialog = CommitDialog(qApp.activeWindow(), db_names)  # pylint: disable=undefined-variable
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            return dialog.commit_msg

    def rollback_session(self, *db_maps):
        error_log = {}
        rolled_db_maps = set()
        for db_map in db_maps:
            if self.undo_stack[db_map].isClean() and not db_map.has_pending_changes():
                continue
            if not self._get_rollback_confirmation(db_map):
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

    @staticmethod
    def _get_rollback_confirmation(db_map):
        message_box = QMessageBox(
            QMessageBox.Question,
            f"Rollback changes in {db_map.codename}",
            "Are you sure? All your changes since the last commit will be reverted and removed from the undo/redo stack.",
            QMessageBox.Ok | QMessageBox.Cancel,
            parent=qApp.activeWindow(),  # pylint: disable=undefined-variable
        )
        message_box.button(QMessageBox.Ok).setText("Rollback")
        answer = message_box.exec_()
        return answer == QMessageBox.Ok

    def _commit_db_map_session(self, db_map):
        commit_msg = self._get_commit_msg(db_map)
        if not commit_msg:
            return False
        try:
            db_map.commit_session(commit_msg)
            cookie = None
            self.session_committed.emit({db_map}, cookie)
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
        if self.undo_stack[db_map].isClean() and not db_map.has_pending_changes():
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
        # Cache
        ordered_signals = {
            "object_class": (self.object_classes_added, self.object_classes_updated),
            "relationship_class": (self.relationship_classes_added, self.relationship_classes_updated),
            "parameter_tag": (self.parameter_tags_added, self.parameter_tags_updated),
            "parameter_value_list": (self.parameter_value_lists_added, self.parameter_value_lists_updated),
            "parameter_definition": (self.parameter_definitions_added, self.parameter_definitions_updated),
            "parameter_definition_tag": (self._parameter_definition_tags_added,),
            "alternative": (self.alternatives_added, self.alternatives_updated),
            "scenario": (self.scenarios_added, self.scenarios_updated),
            "scenario_alternative": (self._scenario_alternatives_added, self._scenario_alternatives_updated),
            "object": (self.objects_added, self.objects_updated),
            "relationship": (self.relationships_added, self.relationships_updated),
            "entity_group": (self.entity_groups_added,),
            "parameter_value": (self.parameter_values_added, self.parameter_values_updated),
            "feature": (self.features_added, self.features_updated),
            "tool": (self.tools_added, self.tools_updated),
            "tool_feature": (self.tool_features_added, self.tool_features_updated),
            "tool_feature_method": (self.tool_feature_methods_added, self.tool_feature_methods_updated),
        }
        for item_type, signals in ordered_signals.items():
            for signal in signals:
                signal.connect(lambda db_map_data, item_type=item_type: self.cache_items(item_type, db_map_data))
        # Signaller (after caching, so items are there when listeners receive signals)
        self.signaller.connect_signals()
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)
        # On cascade refresh
        self.alternatives_updated.connect(self.cascade_refresh_parameter_values_by_alternative)
        self.object_classes_updated.connect(self.cascade_refresh_relationship_classes)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_values_by_entity_class)
        self.objects_updated.connect(self.cascade_refresh_relationships_by_object)
        self.objects_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.relationships_updated.connect(self.cascade_refresh_parameter_values_by_entity)
        self.parameter_definitions_updated.connect(self.cascade_refresh_parameter_values_by_definition)
        self.parameter_value_lists_added.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_value_lists_updated.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_value_lists_removed.connect(self.cascade_refresh_parameter_definitions_by_value_list)
        self.parameter_tags_updated.connect(self.cascade_refresh_parameter_definitions_by_tag)
        self.parameter_definitions_updated.connect(self.cascade_refresh_features_by_paremeter_definition)
        self.parameter_value_lists_updated.connect(self.cascade_refresh_features_by_paremeter_value_list)
        self.features_updated.connect(self.cascade_refresh_tool_features_by_feature)
        # refresh
        self._scenario_alternatives_added.connect(self._refresh_scenario_alternatives)
        self._scenario_alternatives_updated.connect(self._refresh_scenario_alternatives)
        self._scenario_alternatives_removed.connect(self._refresh_scenario_alternatives)
        self._parameter_definition_tags_added.connect(self._refresh_parameter_definitions_by_tag)
        self._parameter_definition_tags_removed.connect(self._refresh_parameter_definitions_by_tag)
        qApp.aboutToQuit.connect(self._stop_fetchers)  # pylint: disable=undefined-variable

    def error_msg(self, db_map_error_log):
        db_msgs = []
        for db_map, error_log in db_map_error_log.items():
            if isinstance(error_log, str):
                error_log = [error_log]
            db_msg = "From " + db_map.codename + ":" + format_string_list(error_log)
            db_msgs.append(db_msg)
        for db_map in db_map_error_log:
            logger = self._db_specific_loggers.get(db_map.codename)
            if logger is not None:
                msg = format_string_list(db_msgs)
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

    def update_icons(self, db_map_data):
        """Runs when object classes are added or updated. Setups icons for those classes.
        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, object_classes in db_map_data.items():
            self.icon_mngr.setdefault(db_map, IconManager()).setup_object_pixmaps(object_classes)

    def entity_class_icon(self, db_map, entity_type, entity_class_id, for_group=False):
        """Returns an appropriate icon for a given entity_class.

        Args:
            db_map (DiffDatabaseMapping)
            entity_type (str): either 'object_class' or 'relationship_class'
            entity_class_id (int)

        Returns:
            QIcon
        """
        entity_class = self.get_item(db_map, entity_type, entity_class_id)
        if not entity_class:
            return None
        if entity_type == "object_class":
            if for_group:
                return self.icon_mngr[db_map].group_object_icon(entity_class["name"])
            return self.icon_mngr[db_map].object_icon(entity_class["name"])
        if entity_type == "relationship_class":
            return self.icon_mngr[db_map].relationship_icon(entity_class["object_class_name_list"])

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

    def _pop_item(self, db_map, item_type, id_):
        return self._cache.get(db_map, {}).get(item_type, {}).pop(id_, {})

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
        return list(self._cache.get(db_map, {}).get(item_type, {}).values())

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
            item_type (str): either "parameter_definition" or "parameter_value"
            id_ (int): The parameter_value or definition id
            role (int, optional)
        """
        item = self.get_item(db_map, item_type, id_)
        if not item:
            return None
        field = {"parameter_value": "value", "parameter_definition": "default_value"}[item_type]
        if role == Qt.EditRole:
            return item[field]
        key = "parsed_value"
        if key not in item:
            item[key] = self.parse_value(item[field])
        return self.format_value(item[key], role)

    @staticmethod
    def parse_value(db_value):
        try:
            return from_database(db_value)
        except ParameterValueFormatError as error:
            return error

    def format_value(self, parsed_value, role=Qt.DisplayRole):
        """Formats the given value for the given role.

        Args:
            parsed_value (object): A python object as returned by spinedb_api.from_database
            role (int, optional)
        """
        if role == Qt.DisplayRole:
            return self._display_data(parsed_value)
        if role == Qt.ToolTipRole:
            return self._tool_tip_data(parsed_value)
        if role == Qt.TextAlignmentRole:
            if isinstance(parsed_value, str):
                return Qt.AlignLeft
            return Qt.AlignRight
        if role == PARSED_ROLE:
            return parsed_value
        return None

    def get_value_indexes(self, db_map, item_type, id_):
        """Returns the value or default value indexes of a parameter.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter_definition" or "parameter_value"
            id_ (int): The parameter_value or definition id
        """
        parsed_value = self.get_value(db_map, item_type, id_, role=PARSED_ROLE)
        if isinstance(parsed_value, IndexedValue):
            return parsed_value.indexes
        return [""]

    def get_value_index(self, db_map, item_type, id_, index, role=Qt.DisplayRole):
        """Returns the value or default value of a parameter for a given index.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter_definition" or "parameter_value"
            id_ (int): The parameter_value or definition id
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

    def _split_and_parse_value_list(self, item):
        if "split_value_list" not in item:
            item["split_value_list"] = item["value_list"].split(";")
        if "split_parsed_value_list" not in item:
            item["split_parsed_value_list"] = [self.parse_value(value) for value in item["split_value_list"]]

    def get_value_list_item(self, db_map, id_, index, role=Qt.DisplayRole):
        """Returns one value item of a parameter_value_list.

        Args:
            db_map (DiffDatabaseMapping)
            id_ (int): The parameter_value_list id
            index (int): The value item index
            role (int, optional)
        """
        item = self.get_item(db_map, "parameter_value_list", id_)
        if not item:
            return None
        self._split_and_parse_value_list(item)
        if index < 0 or index >= len(item["split_value_list"]):
            return None
        if role == Qt.EditRole:
            return item["split_value_list"][index]
        return self.format_value(item["split_parsed_value_list"][index], role)

    def get_parameter_value_list(self, db_map, id_, role=Qt.DisplayRole):
        """Returns a parameter_value_list formatted for the given role.

        Args:
            db_map (DiffDatabaseMapping)
            id_ (int): The parameter_value_list id
            role (int, optional)
        """
        item = self.get_item(db_map, "parameter_value_list", id_)
        if not item:
            return []
        self._split_and_parse_value_list(item)
        if role == Qt.EditRole:
            return item["split_value_list"]
        return [self.format_value(parsed_value, role) for parsed_value in item["split_parsed_value_list"]]

    @staticmethod
    def get_db_items(query, key=lambda x: x["id"]):
        return sorted((x._asdict() for x in query), key=key)

    @staticmethod
    def _make_query(db_map, sq_name, ids=()):
        sq = getattr(db_map, sq_name)
        query = db_map.query(sq)
        if ids:
            query = query.filter(db_map.in_(sq.c.id, ids))
        return query

    def get_alternatives(self, db_map, ids=()):
        """Returns alternatives from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "alternative_sq", ids=ids), key=lambda x: x["name"])

    def get_scenarios(self, db_map, ids=()):
        """Returns scenarios from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "wide_scenario_sq", ids=ids), key=lambda x: x["name"])

    def get_scenario_alternatives(self, db_map, ids=()):
        """Returns scenario alternatives from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "scenario_alternative_sq", ids=ids))

    def get_object_classes(self, db_map, ids=()):
        """Returns object classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "object_class_sq", ids=ids), key=lambda x: x["name"])

    def get_objects(self, db_map, ids=()):
        """Returns objects from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "ext_object_sq", ids=ids), key=lambda x: (x["class_id"], x["name"])
        )

    def get_relationship_classes(self, db_map, ids=()):
        """Returns relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "wide_relationship_class_sq", ids=ids), key=lambda x: x["name"]
        )

    def get_relationships(self, db_map, ids=()):
        """Returns relationships from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "wide_relationship_sq", ids=ids),
            key=lambda x: (x["class_id"], x["object_name_list"]),
        )

    def get_entity_groups(self, db_map, ids=()):
        """Returns entity groups from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "entity_group_sq", ids=ids))

    def get_object_parameter_definitions(self, db_map, ids=()):
        """Returns object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        items = self.get_db_items(
            self._make_query(db_map, "object_parameter_definition_sq", ids=ids),
            key=lambda x: (x["object_class_name"], x["parameter_name"]),
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
            key=lambda x: (x["relationship_class_name"], x["parameter_name"]),
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

    def get_parameter_definition_tags(self, db_map, ids=()):
        """Returns parameter definition tags.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "parameter_definition_tag_sq", ids=ids))

    def get_object_parameter_values(self, db_map, ids=()):
        """Returns object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "object_parameter_value_sq", ids=ids),
            key=lambda x: (x["object_class_name"], x["object_name"], x["parameter_name"]),
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
            key=lambda x: (x["relationship_class_name"], x["object_name_list"], x["parameter_name"]),
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
        """Returns parameter_value lists from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "wide_parameter_value_list_sq", ids=ids), key=lambda x: x["name"]
        )

    def get_parameter_tags(self, db_map, ids=()):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "parameter_tag_sq", ids=ids), key=lambda x: x["tag"])

    def get_features(self, db_map, ids=()):
        """Returns features from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(
            self._make_query(db_map, "ext_feature_sq", ids=ids),
            key=lambda x: (x["entity_class_name"], x["parameter_definition_name"]),
        )

    def get_tools(self, db_map, ids=()):
        """Get tools from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "tool_sq", ids=ids), key=lambda x: x["name"])

    def get_tool_features(self, db_map, ids=()):
        """Returns tool features from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "tool_feature_sq", ids=ids))

    def get_tool_feature_methods(self, db_map, ids=()):
        """Returns tool feature methods from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        return self.get_db_items(self._make_query(db_map, "tool_feature_method_sq", ids=ids))

    def import_data(self, db_map_data, command_text="Import data"):
        """Imports the given data into given db maps using the dedicated import functions from spinedb_api.
        Condenses all in a single command for undo/redo.

        Args:
            db_map_data (dict(DiffDatabaseMapping, dict())): Maps dbs to data to be passed as keyword arguments
                to `get_data_for_import`
            command_text (str, optional): What to call the command that condenses the operation.
        """
        error_log = dict()
        for db_map, data in db_map_data.items():
            try:
                data_for_import = get_data_for_import(db_map, **data)
            except (TypeError, ValueError) as err:
                msg = f"Failed to import data: {err}. Please check that your data source has the right format."
                error_log.setdefault(db_map, []).append(msg)
                continue
            import_command = AgedUndoCommand()
            import_command.setText(command_text)
            child_cmds = []
            # NOTE: we push the import command before adding the children,
            # because we *need* to call redo() on the children one by one so the data gets in gradually
            self.undo_stack[db_map].push(import_command)
            for item_type, (to_add, to_update, import_error_log) in data_for_import:
                error_log.setdefault(db_map, []).extend([str(x) for x in import_error_log])
                if to_add:
                    add_cmd = AddItemsCommand(self, db_map, to_add, item_type, parent=import_command)
                    add_cmd.redo()
                    child_cmds.append(add_cmd)
                if to_update:
                    upd_cmd = UpdateItemsCommand(self, db_map, to_update, item_type, parent=import_command)
                    upd_cmd.redo()
                    child_cmds.append(upd_cmd)
            if all([cmd.isObsolete() for cmd in child_cmds]):
                # Nothing imported. Set the command obsolete and call undo() on the stack to removed it
                import_command.setObsolete(True)
                self.undo_stack[db_map].undo()
        if any(error_log.values()):
            self.error_msg(error_log)

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
            result = getattr(db_map, method_name)(*items)
            if isinstance(result, tuple):
                ids, errors = result
            else:
                ids, errors = result, ()
            if errors:
                error_log[db_map] = errors
            if not ids:
                continue
            db_map_data_out[db_map] = getattr(self, get_method_name)(db_map, ids=ids)
        if any(error_log.values()):
            self.error_msg(error_log)
        if any(db_map_data_out.values()):
            getattr(self, signal_name).emit(db_map_data_out)

    def add_alternatives(self, db_map_data):
        """Adds alternatives to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "alternative"))

    def add_scenarios(self, db_map_data):
        """Adds scenarios to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "scenario"))

    def add_object_classes(self, db_map_data):
        """Adds object classes to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "object_class"))

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
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "relationship_class"))

    def add_relationships(self, db_map_data):
        """Adds relationships to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "relationship"))

    def add_object_groups(self, db_map_data):
        """Adds object groups to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "object group"))

    def add_entity_groups(self, db_map_data):
        """Adds entity groups to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "entity_group"))

    def add_parameter_definitions(self, db_map_data):
        """Adds parameter definitions to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_definition"))

    def add_parameter_values(self, db_map_data):
        """Adds parameter values to db without checking integrity.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_value"))

    def check_add_parameter_values(self, db_map_data):
        """Adds parameter values in db *with* checking integrity.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(CheckAddParameterValuesCommand(self, db_map, data))

    def add_parameter_value_lists(self, db_map_data):
        """Adds parameter_value lists to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_value_list"))

    def add_parameter_tags(self, db_map_data):
        """Adds parameter tags to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_tag"))

    def add_features(self, db_map_data):
        """Adds features to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "feature"))

    def add_tools(self, db_map_data):
        """Adds tools to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "tool"))

    def add_tool_features(self, db_map_data):
        """Adds tool features to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "tool_feature"))

    def add_tool_feature_methods(self, db_map_data):
        """Adds tool feature methods to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "tool_feature_method"))

    def update_alternatives(self, db_map_data):
        """Updates alternatives in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "alternative"))

    def update_scenarios(self, db_map_data):
        """Updates scenarios in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "scenario"))

    def update_object_classes(self, db_map_data):
        """Updates object classes in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "object_class"))

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
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "relationship_class"))

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
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_definition"))

    def update_parameter_values(self, db_map_data):
        """Updates parameter values in db without checking integrity.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_value"))

    def check_update_parameter_values(self, db_map_data):
        """Updates parameter values in db *with* checking integrity.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(CheckUpdateParameterValuesCommand(self, db_map, data))

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
                parsed_data = self.get_value(db_map, "parameter_value", id_, role=PARSED_ROLE)
                if isinstance(parsed_data, IndexedValue):
                    for index, value in indexed_values.items():
                        parsed_data.set_value(index, value)
                    value = to_database(parsed_data)
                else:
                    value = next(iter(indexed_values.values()))
                item = {"id": id_, "value": value}
                items.append(item)
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, items, "parameter_value"))

    def update_parameter_value_lists(self, db_map_data):
        """Updates parameter_value lists in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_value_list"))

    def update_parameter_tags(self, db_map_data):
        """Updates parameter tags in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_tag"))

    def update_features(self, db_map_data):
        """Updates features in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "feature"))

    def update_tools(self, db_map_data):
        """Updates tools in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "tool"))

    def update_tool_features(self, db_map_data):
        """Updates tools features in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "tool_feature"))

    def update_tool_feature_methods(self, db_map_data):
        """Updates tools feature methods in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "tool_feature_method"))

    def set_scenario_alternatives(self, db_map_data):
        """Sets scenario alternatives in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            macro_command = AgedUndoCommand()
            macro_command.setText(f"set scenario alternatives in {db_map.codename}")
            self.undo_stack[db_map].push(macro_command)
            child_cmds = []
            items_to_add, items_to_update, ids_to_remove = db_map.get_data_to_set_scenario_alternatives(*data)
            if ids_to_remove:
                rm_cmd = RemoveItemsCommand(self, db_map, {"scenario_alternative": ids_to_remove}, parent=macro_command)
                rm_cmd.redo()
                child_cmds.append(rm_cmd)
            if items_to_update:
                upd_cmd = UpdateItemsCommand(
                    self, db_map, items_to_update, "scenario_alternative", parent=macro_command
                )
                upd_cmd.redo()
                child_cmds.append(upd_cmd)
            if items_to_add:
                add_cmd = AddItemsCommand(self, db_map, items_to_add, "scenario_alternative", parent=macro_command)
                add_cmd.redo()
                child_cmds.append(add_cmd)
            if all([cmd.isObsolete() for cmd in child_cmds]):
                macro_command.setObsolete(True)
                self.undo_stack[db_map].undo()

    def set_parameter_definition_tags(self, db_map_data):
        """Sets parameter_definition tags in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            macro_command = AgedUndoCommand()
            macro_command.setText(f"set parameter definition tags in {db_map.codename}")
            self.undo_stack[db_map].push(macro_command)
            child_cmds = []
            items_to_add, ids_to_remove = db_map.get_data_to_set_parameter_definition_tags(*data)
            if ids_to_remove:
                rm_cmd = RemoveItemsCommand(
                    self, db_map, {"parameter_definition_tag": ids_to_remove}, parent=macro_command
                )
                rm_cmd.redo()
                child_cmds.append(rm_cmd)
            if items_to_add:
                add_cmd = AddItemsCommand(self, db_map, items_to_add, "parameter_definition_tag", parent=macro_command)
                add_cmd.redo()
                child_cmds.append(add_cmd)
            if all([cmd.isObsolete() for cmd in child_cmds]):
                macro_command.setObsolete(True)
                self.undo_stack[db_map].undo()

    def remove_items(self, db_map_typed_ids):
        for db_map, ids_per_type in db_map_typed_ids.items():
            ids_per_type = db_map.cascading_ids(**ids_per_type)
            self.undo_stack[db_map].push(RemoveItemsCommand(self, db_map, ids_per_type))

    def do_cascade_remove_items(self, db_map_typed_ids):
        db_map_typed_ids = {
            db_map: db_map.cascading_ids(**ids_per_type) for db_map, ids_per_type in db_map_typed_ids.items()
        }
        self.do_remove_items(db_map_typed_ids)

    @busy_effect
    def do_remove_items(self, db_map_typed_ids):
        """Removes items from database.

        Args:
            db_map_typed_ids (dict): lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
        """
        error_log = dict()
        for db_map, ids_per_type in db_map_typed_ids.items():
            try:
                db_map.remove_items(**ids_per_type)
            except SpineDBAPIError as err:
                error_log[db_map] = [err]
                continue
        if any(error_log.values()):
            self.error_msg(error_log)
        self.uncache_items(db_map_typed_ids)

    def _pop_item(self, db_map, item_type, id_):
        return self._cache.get(db_map, {}).get(item_type, {}).pop(id_, {})

    def uncache_items(self, db_map_typed_ids):
        """Removes data from cache.

        Args:
            db_map_typed_ids
        """
        ordered_signals = {
            "parameter_value": self.parameter_values_removed,
            "entity_group": self.entity_groups_removed,
            "relationship": self.relationships_removed,
            "object": self.objects_removed,
            "scenario_alternative": self._scenario_alternatives_removed,
            "scenario": self.scenarios_removed,
            "alternative": self.alternatives_removed,
            "parameter_definition_tag": self._parameter_definition_tags_removed,
            "tool_feature_method": self.tool_feature_methods_removed,
            "tool_feature": self.tool_features_removed,
            "feature": self.features_removed,
            "tool": self.tools_removed,
            "parameter_definition": self.parameter_definitions_removed,
            "parameter_value_list": self.parameter_value_lists_removed,
            "parameter_tag": self.parameter_tags_removed,
            "relationship_class": self.relationship_classes_removed,
            "object_class": self.object_classes_removed,
        }  # NOTE: The rule here is, if table A has a fk that references table B, then A must come *before* B
        typed_db_map_data = {}
        for item_type, signal in ordered_signals.items():
            db_map_ids = {db_map: ids_per_type.get(item_type) for db_map, ids_per_type in db_map_typed_ids.items()}
            db_map_data = {
                db_map: [self._pop_item(db_map, item_type, id_) for id_ in ids]
                for db_map, ids in db_map_ids.items()
                if ids
            }
            if any(db_map_data.values()):
                signal.emit(db_map_data)
                typed_db_map_data[item_type] = db_map_data
        if typed_db_map_data:
            self.items_removed_from_cache.emit(typed_db_map_data)

    @staticmethod
    def db_map_ids(db_map_data):
        return {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}

    @staticmethod
    def db_map_class_ids(db_map_data):
        d = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                d.setdefault((db_map, item["class_id"]), set()).add(item["id"])
        return d

    @Slot(object)
    def _refresh_scenario_alternatives(self, db_map_data):
        """Refreshes cached scenarios when updating scenario alternatives.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_data = {
            db_map: self.get_scenarios(db_map, ids={x["scenario_id"] for x in data})
            for db_map, data in db_map_data.items()
        }
        if not any(db_map_data.values()):
            return
        self.scenarios_updated.emit(db_map_data)

    @Slot(object)
    def _refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["parameter_definition_id"] for x in data})
            for db_map, data in db_map_data.items()
        }
        if not any(db_map_data.values()):
            return
        self.parameter_definitions_updated.emit(db_map_data)

    @Slot(object)
    def cascade_refresh_relationship_classes(self, db_map_data):
        """Refreshes cached relationship classes when updating object classes.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_relationship_classes(self.db_map_ids(db_map_data))
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
        db_map_cascading_data = self.find_cascading_relationships(self.db_map_ids(db_map_data))
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
        db_map_cascading_data = self.find_cascading_parameter_data(self.db_map_ids(db_map_data), "parameter_definition")
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_definitions_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_definitions_by_value_list(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter_value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_value_list(self.db_map_ids(db_map_data))
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
        db_map_cascading_data = self.find_cascading_parameter_data(self.db_map_ids(db_map_data), "parameter_value")
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
        db_map_cascading_data = self.find_cascading_parameter_values_by_entity(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_values_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_values_by_alternative(self, db_map_data):
        """Refreshes cached parameter values in cascade when updating alternatives.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_values_by_alternative(self.db_map_ids(db_map_data))
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
        db_map_cascading_data = self.find_cascading_parameter_values_by_definition(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_values(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_values_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_parameter_definitions_by_tag(self, db_map_data):
        """Refreshes cached parameter definitions when updating parameter tags.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_parameter_definitions_by_tag(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_parameter_definitions(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.parameter_definitions_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_features_by_paremeter_definition(self, db_map_data):
        """Refreshes cached features in cascade when updating parameter definitions.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_features_by_parameter_definition(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_features(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.features_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_features_by_paremeter_value_list(self, db_map_data):
        """Refreshes cached features in cascade when updating parameter value lists.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_features_by_parameter_value_list(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_features(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.features_updated.emit(db_map_cascading_data)

    @Slot(object)
    def cascade_refresh_tool_features_by_feature(self, db_map_data):
        """Refreshes cached tool features in cascade when updating features.

        Args:
            db_map_data (dict): lists of updated items keyed by DiffDatabaseMapping
        """
        db_map_cascading_data = self.find_cascading_tool_features_by_feature(self.db_map_ids(db_map_data))
        if not any(db_map_cascading_data.values()):
            return
        db_map_cascading_data = {
            db_map: self.get_tool_features(db_map, ids={x["id"] for x in data})
            for db_map, data in db_map_cascading_data.items()
        }
        self.tool_features_updated.emit(db_map_cascading_data)

    def find_cascading_relationship_classes(self, db_map_ids):
        """Finds and returns cascading relationship classes for the given object_class ids."""
        db_map_cascading_data = dict()
        for db_map, object_class_ids in db_map_ids.items():
            object_class_ids = {str(id_) for id_ in object_class_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship_class")
                if object_class_ids.intersection(item["object_class_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_entities(self, db_map_ids, item_type):
        """Finds and returns cascading entities for the given entity_class ids."""
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
        """Finds and returns cascading parameter definitions or values for the given entity_class ids."""
        db_map_cascading_data = dict()
        for db_map, entity_class_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, item_type) if item["entity_class_id"] in entity_class_ids
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_value_list(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter_value_list ids."""
        db_map_cascading_data = dict()
        for db_map, value_list_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter_definition")
                if item["value_list_id"] in value_list_ids
            ]
        return db_map_cascading_data

    def find_cascading_parameter_definitions_by_tag(self, db_map_ids):
        """Finds and returns cascading parameter definitions for the given parameter_tag ids."""
        db_map_cascading_data = dict()
        for db_map, tag_ids in db_map_ids.items():
            tag_ids = {str(id_) for id_ in tag_ids}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter_definition")
                if tag_ids.intersection((item["parameter_tag_id_list"] or "0").split(","))
            ]  # NOTE: 0 is 'untagged'
        return db_map_cascading_data

    def find_cascading_parameter_values_by_entity(self, db_map_ids):
        """Finds and returns cascading parameter values for the given entity ids."""
        db_map_cascading_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "parameter_value") if item["entity_id"] in entity_ids
            ]
        return db_map_cascading_data

    def find_cascading_parameter_values_by_definition(self, db_map_ids):
        """Finds and returns cascading parameter values for the given parameter_definition ids."""
        db_map_cascading_data = dict()
        for db_map, definition_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "parameter_value") if item["parameter_id"] in definition_ids
            ]
        return db_map_cascading_data

    def find_groups_by_entity(self, db_map_ids):
        """Finds and returns groups for the given entity ids."""
        db_map_group_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            db_map_group_data[db_map] = [
                item for item in self.get_items(db_map, "entity_group") if item["entity_id"] in entity_ids
            ]
        return db_map_group_data

    def find_groups_by_member(self, db_map_ids):
        """Finds and returns groups for the given entity ids."""
        db_map_group_data = dict()
        for db_map, member_ids in db_map_ids.items():
            db_map_group_data[db_map] = [
                item for item in self.get_items(db_map, "entity_group") if item["member_id"] in member_ids
            ]
        return db_map_group_data

    def find_cascading_parameter_values_by_alternative(self, db_map_ids):
        """Finds and returns cascading parameter values for the given alternative ids."""
        db_map_cascading_data = dict()
        for db_map, alt_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "parameter_value") if item["alternative_id"] in alt_ids
            ]
        return db_map_cascading_data

    def find_cascading_scenario_alternatives_by_alternative(self, db_map_ids):
        """Finds and returns cascading scenario_alternatives for the given alternative ids."""
        db_map_cascading_data = dict()
        for db_map, alt_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "scenario_alternative") if item["alternative_id"] in alt_ids
            ]
        return db_map_cascading_data

    def find_cascading_scenario_alternatives_by_scenario(self, db_map_ids):
        """Finds and returns cascading scenario_alternatives for the given scenario ids."""
        db_map_cascading_data = dict()
        for db_map, scen_ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "scenario_alternative") if item["scenario_id"] in scen_ids
            ]
        return db_map_cascading_data

    def find_cascading_features_by_parameter_definition(self, db_map_ids):
        """Finds and returns cascading features for the given parameter definition ids."""
        db_map_cascading_data = dict()
        for db_map, ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "feature") if item["parameter_definition_id"] in ids
            ]
        return db_map_cascading_data

    def find_cascading_features_by_parameter_value_list(self, db_map_ids):
        """Finds and returns cascading features for the given parameter value list ids."""
        db_map_cascading_data = dict()
        for db_map, ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "feature") if item["parameter_value_list_id"] in ids
            ]
        return db_map_cascading_data

    def find_cascading_tool_features_by_feature(self, db_map_ids):
        """Finds and returns cascading tool features for the given feature ids."""
        db_map_cascading_data = dict()
        for db_map, ids in db_map_ids.items():
            db_map_cascading_data[db_map] = [
                item for item in self.get_items(db_map, "tool_feature") if item["feature_id"] in ids
            ]
        return db_map_cascading_data
