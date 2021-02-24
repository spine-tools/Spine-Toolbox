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
The SpineDBManager class

:authors: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""

import itertools
from PySide2.QtCore import Qt, QObject, Signal, QThread
from PySide2.QtWidgets import QMessageBox, QDialog, QCheckBox, QWidget
from PySide2.QtGui import QFontMetrics, QFont
from spinedb_api import (
    is_empty,
    create_new_spine_database,
    SpineDBVersionError,
    SpineDBAPIError,
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
from .helpers import IconManager, busy_effect
from .spine_db_signaller import SpineDBSignaller
from .spine_db_fetcher import SpineDBFetcher
from .spine_db_worker import SpineDBWorker
from .spine_db_commands import (
    AgedUndoStack,
    AddItemsCommand,
    CheckAddParameterValuesCommand,
    UpdateItemsCommand,
    CheckUpdateParameterValuesCommand,
    RemoveItemsCommand,
)
from .widgets.commit_dialog import CommitDialog
from .mvcmodels.shared import PARSED_ROLE
from .spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
from .spine_db_editor.widgets.spine_db_editor import SpineDBEditor


@busy_effect
def do_create_new_spine_database(url):
    """Creates a new spine database at the given url."""
    create_new_spine_database(url)


def _grouper(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


class SpineDBManager(QObject):
    """Class to manage DBs within a project.

    TODO: Expand description, how it works, the cache, the signals, etc.
    """

    error_msg = Signal(object)
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
    scenario_alternatives_added = Signal(object)
    scenario_alternatives_updated = Signal(object)
    scenario_alternatives_removed = Signal(object)
    parameter_definition_tags_added = Signal(object)
    parameter_definition_tags_removed = Signal(object)
    # For tests
    data_imported = Signal()

    _GROUP_SEP = " \u01C0 "

    def __init__(self, settings, parent):
        """Initializes the instance.

        Args:
            settings (QSettings): Toolbox settings
            parent (QObject, optional): parent object
        """
        super().__init__(parent)
        self._db_maps = {}
        self._cache = {}
        self.qsettings = settings
        self.undo_stack = {}
        self.undo_action = {}
        self.redo_action = {}
        self.icon_mngr = {}
        self.signaller = SpineDBSignaller(self)
        self._thread = QThread()
        self._worker = SpineDBWorker(self)
        self._fetchers = []
        self.connect_signals()

    @property
    def thread(self):
        self._thread.start()
        return self._thread

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
        url = str(url)
        return self._db_maps.get(url)

    def is_url_available(self, url, logger):
        if str(url) in self._db_maps:
            message = f"The URL <b>{url}</b> is in use. Please close all applications using it and try again."
            logger.msg_error.emit(message)
            return False
        return True

    def create_new_spine_database(self, url, logger):
        try:
            if not is_empty(url):
                msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText(f"The URL <b>{url}</b> points to an existing database.")
                msg.setInformativeText("Do you want to overwrite it?")
                msg.addButton("Overwrite", QMessageBox.AcceptRole)
                msg.addButton("Cancel", QMessageBox.RejectRole)
                ret = msg.exec_()  # Show message box
                if ret != QMessageBox.AcceptRole:
                    return
            do_create_new_spine_database(url)
            logger.msg_success.emit(f"New Spine db successfully created at '{url}'.")
            db_map = self.db_map(url)
            self.refresh_session(db_map)
        except SpineDBAPIError as e:
            logger.msg_error.emit(f"Unable to create new Spine db at '{url}': {e}.")

    def close_session(self, url):
        """Pops any db map on the given url and closes its connection.

        Args:
            url (str)
        """
        db_map = self._db_maps.pop(url, None)
        if db_map is None:
            return
        self._close_db_map(db_map)

    def close_all_sessions(self):
        """Closes connections to all database mappings."""
        for db_map in self._db_maps.values():
            self._close_db_map(db_map)

    def _close_db_map(self, db_map):
        self._worker.close_db_map(db_map)

    def get_db_map(self, url, logger, codename=None, upgrade=False, create=False):
        """Returns a DiffDatabaseMapping instance from url if possible, None otherwise.
        If needed, asks the user to upgrade to the latest db version.

        Args:
            url (str, URL)
            logger (LoggerInterface)
            codename (str, NoneType, optional)
            upgrade (bool, optional)
            create (bool, optional)

        Returns:
            DiffDatabaseMapping, NoneType
        """
        try:
            return self._do_get_db_map(url, codename, upgrade, create)
        except SpineDBVersionError as v_err:
            if v_err.upgrade_available:
                msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Incompatible database version")
                msg.setText(
                    f"The database at <b>{url}</b> is at revision <b>{v_err.current}</b> and needs to be "
                    f"upgraded to revision <b>{v_err.expected}</b> in order to be used with the current "
                    f"version of Spine Toolbox."
                )
                msg.setInformativeText(
                    "Do you want to upgrade the database now?"
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
            QMessageBox.information(
                qApp.activeWindow(),  # pylint: disable=undefined-variable
                "Unsupported database version",
                f"Database at <b>{url}</b> is newer than this version of Spine Toolbox "
                f"can handle.<br><br>"
                f"The db is at revision <b>{v_err.current}</b> while this version "
                f"of Spine Toolbox supports revisions up to <b>{v_err.expected}</b>. "
                f"<br><br>Please upgrade Spine Toolbox to open this database.",
            )
            return None
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
        db_map, err = self._worker.get_db_map(url, codename=codename, upgrade=upgrade, create=create)
        if err is not None:
            raise err
        self._db_maps[url] = db_map
        stack = self.undo_stack[db_map] = AgedUndoStack(self)
        self.undo_action[db_map] = stack.createUndoAction(self)
        self.redo_action[db_map] = stack.createRedoAction(self)
        return db_map

    def register_listener(self, listener, *db_maps):
        """Register given listener for all given db_map's signals.

        Args:
            listener (object)
            db_maps (DiffDatabaseMapping)
        """
        for db_map in db_maps:
            self.signaller.add_db_map_listener(db_map, listener)
            stack = self.undo_stack[db_map]
            try:
                stack.indexChanged.connect(listener.update_undo_redo_actions)
                stack.cleanChanged.connect(listener.update_commit_enabled)
            except AttributeError:
                pass

    def unregister_listener(self, listener, *db_maps):
        """Unregisters given listener from given db_map signals.
        If any of the db_maps becomes an orphan and is dirty, prompts user to commit or rollback.

        Args:
            listener (object)
            db_maps (DiffDatabaseMapping)
        """
        is_dirty = lambda db_map: not self.undo_stack[db_map].isClean() or db_map.has_pending_changes()
        is_orphan = lambda db_map: not any(
            isinstance(x, SpineDBEditor) for x in self.signaller.db_map_listeners(db_map) - {listener}
        )
        dirty_orphan_db_maps = [db_map for db_map in db_maps if is_orphan(db_map) and is_dirty(db_map)]
        if dirty_orphan_db_maps:
            answer = self._prompt_to_commit_changes()
            if answer == QMessageBox.Cancel:
                return False
            db_names = ", ".join([db_map.codename for db_map in dirty_orphan_db_maps])
            if answer == QMessageBox.Save:
                commit_msg = self._get_commit_msg(db_names)
                if not commit_msg:
                    return False
        for db_map in db_maps:
            self.signaller.remove_db_map_listener(db_map, listener)
            try:
                self.undo_stack[db_map].indexChanged.disconnect(listener.update_undo_redo_actions)
                self.undo_stack[db_map].cleanChanged.disconnect(listener.update_commit_enabled)
            except AttributeError:
                pass
        if dirty_orphan_db_maps:
            if answer == QMessageBox.Save:
                self._worker.commit_session(dirty_orphan_db_maps, commit_msg)
            else:
                self._worker.rollback_session(dirty_orphan_db_maps)
        for db_map in db_maps:
            if not self.signaller.db_map_listeners(db_map):
                self.close_session(db_map.db_url)
                del self.undo_stack[db_map]
                del self.undo_action[db_map]
                del self.redo_action[db_map]
        return True

    def _prompt_to_commit_changes(self):
        """Prompts the user to commit or rollback changes to 'dirty' db maps.

        Returns:
            bool: True to commit, False to rollback, None to do nothing
        """
        commit_at_exit = int(self.qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return QMessageBox.Discard
        if commit_at_exit == 1:  # Default
            # Show message box
            parent = qApp.activeWindow()  # pylint: disable=undefined-variable
            msg = QMessageBox(parent)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle(parent.windowTitle())
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.button(QMessageBox.Save).setText("Commit and close ")
            msg.button(QMessageBox.Discard).setText("Discard changes and close")
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            if answer != QMessageBox.Cancel and chkbox.checkState() == 2:
                # Save preference
                preference = "2" if answer == QMessageBox.Save else "0"
                self.qsettings.setValue("appSettings/commitAtExit", preference)
            return answer
        if commit_at_exit == 2:
            # Commit session and don't show message box
            return QMessageBox.Save

    def get_fetcher(self, listener):
        """Fetches given db_map for given listener.

        Args:
            listener (SpineDBEditor)
        """
        fetcher = SpineDBFetcher(self, listener)
        # NOTE: The below connection style prevents segfaults when connecting to a slot that's being executed
        fetcher.finished.connect(lambda fetcher=fetcher: self._clean_up_fetcher(fetcher))
        self._fetchers.append(fetcher)
        return fetcher

    def _clean_up_fetcher(self, fetcher):
        """
        Cleans up things after fetcher has finished working.

        Args:
            fetcher (SpineDBFetcher): the fetcher to clean up
        """
        self._fetchers.remove(fetcher)
        fetcher.close()

    def clean_up(self):
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()

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
        dirty_db_maps = [
            db_map for db_map in db_maps if not self.undo_stack[db_map].isClean() or db_map.has_pending_changes()
        ]
        if not dirty_db_maps:
            return
        db_names = ", ".join([db_map.codename for db_map in dirty_db_maps])
        commit_msg = self._get_commit_msg(db_names)
        if not commit_msg:
            return
        self._worker.commit_session(dirty_db_maps, commit_msg, cookie)

    @staticmethod
    def _get_commit_msg(db_names):
        dialog = CommitDialog(qApp.activeWindow(), db_names)  # pylint: disable=undefined-variable
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            return dialog.commit_msg

    def rollback_session(self, *db_maps):
        dirty_db_maps = [
            db_map for db_map in db_maps if not self.undo_stack[db_map].isClean() or db_map.has_pending_changes()
        ]
        if not dirty_db_maps:
            return
        db_names = ", ".join([db_map.codename for db_map in dirty_db_maps])
        if not self._get_rollback_confirmation(db_names):
            return
        self._worker.rollback_session(dirty_db_maps)

    @staticmethod
    def _get_rollback_confirmation(db_names):
        message_box = QMessageBox(
            QMessageBox.Question,
            f"Rollback changes in {db_names}",
            "Are you sure? All your changes since the last commit will be reverted and removed from the undo/redo stack.",
            QMessageBox.Ok | QMessageBox.Cancel,
            parent=qApp.activeWindow(),  # pylint: disable=undefined-variable
        )
        message_box.button(QMessageBox.Ok).setText("Rollback")
        answer = message_box.exec_()
        return answer == QMessageBox.Ok

    def connect_signals(self):
        """Connects signals."""
        # Cache
        ordered_signals = {
            "object_class": (self.object_classes_added, self.object_classes_updated),
            "relationship_class": (self.relationship_classes_added, self.relationship_classes_updated),
            "parameter_tag": (self.parameter_tags_added, self.parameter_tags_updated),
            "parameter_value_list": (self.parameter_value_lists_added, self.parameter_value_lists_updated),
            "parameter_definition": (self.parameter_definitions_added, self.parameter_definitions_updated),
            "parameter_definition_tag": (self.parameter_definition_tags_added,),
            "alternative": (self.alternatives_added, self.alternatives_updated),
            "scenario": (self.scenarios_added, self.scenarios_updated),
            "scenario_alternative": (self.scenario_alternatives_added, self.scenario_alternatives_updated),
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
        self._worker.connect_signals()
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)
        qApp.aboutToQuit.connect(self.clean_up)  # pylint: disable=undefined-variable

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

    def get_icon_mngr(self, db_map):
        """Returns an icon manager for given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            IconManager
        """
        if db_map not in self.icon_mngr:
            self.icon_mngr[db_map] = IconManager()
        return self.icon_mngr[db_map]

    def update_icons(self, db_map_data):
        """Runs when object classes are added or updated. Setups icons for those classes.

        Args:
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, object_classes in db_map_data.items():
            self.get_icon_mngr(db_map).setup_object_pixmaps(object_classes)

    def entity_class_icon(self, db_map, entity_type, entity_class_id, for_group=False):
        """Returns an appropriate icon for a given entity class.

        Args:
            db_map (DiffDatabaseMapping)
            entity_type (str): either 'object_class' or 'relationship_class'
            entity_class_id (int): entity class' id
            for_group (bool): if True, return the group object icon instead

        Returns:
            QIcon: requested icon
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

    def get_scenario_alternative_id_list(self, db_map, scen_id):
        alternative_id_list = self.get_item(db_map, "scenario", scen_id).get("alternative_id_list")
        if alternative_id_list is None:
            return []
        return [int(id_) for id_ in alternative_id_list.split(",")]

    @staticmethod
    def get_db_items(query, chunk_size=1000):
        """Runs the given query and yield results by chunks of given size.

        Returns:
            generator(list)
        """
        it = (x._asdict() for x in query.yield_per(chunk_size).enable_eagerloads(False))
        while True:
            chunk = list(itertools.islice(it, chunk_size))
            if not chunk:
                return
            yield chunk

    @staticmethod
    def _make_query(db_map, sq_name, ids=(), key=("id",)):
        """Makes a database query

        Args:
            db_map (DatabaseMappingBase): database map
            sq_name (str): name of the subquery
            ids (Iterable of int): ids by which the query should be filtered

        Returns:
            Alias: database subquery
        """
        sq = getattr(db_map, sq_name)
        query = db_map.query(sq)
        if ids:
            query = query.filter(db_map.in_(sq.c.id, ids)).order_by(*[getattr(sq.c, k) for k in key])
        return query

    def get_alternatives(self, db_map, ids=()):
        """Returns alternatives from database.

        Args:
            db_map (DatabaseMappingBase): database map
            ids (Iterable of int): ids by which the alternatives should be filtered

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "alternative_sq", ids=ids, key=["name"]))

    def get_scenarios(self, db_map, ids=()):
        """Returns scenarios from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "wide_scenario_sq", ids=ids, key=["name"]))

    def get_scenario_alternatives(self, db_map, ids=()):
        """Returns scenario alternatives from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "scenario_alternative_sq", ids=ids))

    def get_object_classes(self, db_map, ids=()):
        """Returns object classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "object_class_sq", ids=ids, key=["name"]))

    def get_objects(self, db_map, ids=()):
        """Returns objects from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "ext_object_sq", ids=ids, key=["class_id", "name"]))

    def get_relationship_classes(self, db_map, ids=()):
        """Returns relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "wide_relationship_class_sq", ids=ids, key=["name"]))

    def get_relationships(self, db_map, ids=()):
        """Returns relationships from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(db_map, "wide_relationship_sq", ids=ids, key=["class_id", "object_name_list"])
        )

    def get_entity_groups(self, db_map, ids=()):
        """Returns entity groups from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "entity_group_sq", ids=ids))

    def get_object_parameter_definitions(self, db_map, ids=()):
        """Returns object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(
                db_map, "object_parameter_definition_sq", ids=ids, key=["object_class_name", "parameter_name"]
            )
        )

    def get_relationship_parameter_definitions(self, db_map, ids=()):
        """Returns relationship parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(
                db_map,
                "relationship_parameter_definition_sq",
                ids=ids,
                key=["relationship_class_name", "parameter_name"],
            )
        )

    def get_parameter_definitions(self, db_map, ids=()):
        """Returns both object and relationship parameter definitions.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_object_parameter_definitions(db_map, ids=ids)
        yield from self.get_relationship_parameter_definitions(db_map, ids=ids)

    def get_parameter_definition_tags(self, db_map, ids=()):
        """Returns parameter definition tags.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "parameter_definition_tag_sq", ids=ids))

    def get_object_parameter_values(self, db_map, ids=()):
        """Returns object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(
                db_map, "object_parameter_value_sq", ids=ids, key=["object_class_name", "object_name", "parameter_name"]
            )
        )

    def get_relationship_parameter_values(self, db_map, ids=()):
        """Returns relationship parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(
                db_map,
                "relationship_parameter_value_sq",
                ids=ids,
                key=["relationship_class_name", "object_name_list", "parameter_name"],
            )
        )

    def get_parameter_values(self, db_map, ids=()):
        """Returns both object and relationship parameter values.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_object_parameter_values(db_map, ids=ids)
        yield from self.get_relationship_parameter_values(db_map, ids=ids)

    def get_parameter_value_lists(self, db_map, ids=()):
        """Returns parameter_value lists from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "wide_parameter_value_list_sq", ids=ids, key=["name"]))

    def get_parameter_tags(self, db_map, ids=()):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "parameter_tag_sq", ids=ids, key=["tag"]))

    def get_features(self, db_map, ids=()):
        """Returns features from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(
            self._make_query(db_map, "ext_feature_sq", ids=ids, key=["entity_class_name", "parameter_definition_name"])
        )

    def get_tools(self, db_map, ids=()):
        """Get tools from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "tool_sq", ids=ids, key=["name"]))

    def get_tool_features(self, db_map, ids=()):
        """Returns tool features from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "tool_feature_sq", ids=ids))

    def get_tool_feature_methods(self, db_map, ids=()):
        """Returns tool feature methods from database.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list: dictionary items
        """
        yield from self.get_db_items(self._make_query(db_map, "tool_feature_method_sq", ids=ids))

    def import_data(self, db_map_data, command_text="Import data"):
        """Imports the given data into given db maps using the dedicated import functions from spinedb_api.
        Condenses all in a single command for undo/redo.

        Args:
            db_map_data (dict(DiffDatabaseMapping, dict())): Maps dbs to data to be passed as keyword arguments
                to `get_data_for_import`
            command_text (str, optional): What to call the command that condenses the operation.
        """
        self._worker.import_data(db_map_data, command_text)

    def add_or_update_items(self, db_map_data, method_name, get_method_name, signal_name):
        self._worker.add_or_update_items(db_map_data, method_name, get_method_name, signal_name)

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
        self._worker.set_scenario_alternatives(db_map_data)

    def set_parameter_definition_tags(self, db_map_data):
        """Sets parameter_definition tags in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        self._worker.set_parameter_definition_tags(db_map_data)

    def remove_items(self, db_map_typed_ids):
        for db_map, ids_per_type in db_map_typed_ids.items():
            self.undo_stack[db_map].push(RemoveItemsCommand(self, db_map, ids_per_type))

    @busy_effect
    def do_remove_items(self, db_map_typed_ids):
        """Removes items from database.

        Args:
            db_map_typed_ids (dict): lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
        """
        self._worker.remove_items(db_map_typed_ids)

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
            "scenario_alternative": self.scenario_alternatives_removed,
            "scenario": self.scenarios_removed,
            "alternative": self.alternatives_removed,
            "parameter_definition_tag": self.parameter_definition_tags_removed,
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

    @staticmethod
    def get_all_multi_spine_db_editors():
        """Yields all instances of MultiSpineDBEditor currently open.

        Returns:
            Generator
        """
        for window in qApp.topLevelWindows():  # pylint: disable=undefined-variable
            widget = QWidget.find(window.winId())
            if isinstance(widget, MultiSpineDBEditor):
                yield widget

    @staticmethod
    def get_all_spine_db_editors():
        """Yields all instances of SpineDBEditor currently open.

        Returns:
            Generator
        """
        for w in SpineDBManager.get_all_multi_spine_db_editors():
            for k in range(w.tab_widget.count()):
                yield w.tab_widget.widget(k)

    def export_data(self, caller, db_map_item_ids, file_path, file_filter):
        self._worker.export_data(caller, db_map_item_ids, file_path, file_filter)
