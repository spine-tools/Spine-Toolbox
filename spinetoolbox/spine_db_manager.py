######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

import json
import os
from PySide6.QtCore import Qt, QObject, Signal, Slot, QRecursiveMutex
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtGui import QFontMetrics, QFont, QWindow
from sqlalchemy.engine.url import URL
from spinedb_api import (
    is_empty,
    create_new_spine_database,
    DatabaseMapping,
    SpineDBVersionError,
    SpineDBAPIError,
    from_database,
    to_database,
    relativedelta_to_duration,
    ParameterValueFormatError,
    IndexedValue,
    Array,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    TimePattern,
    Map,
    get_data_for_import,
    import_data,
    export_data,
)
from spinedb_api.parameter_value import load_db_value
from spinedb_api.parameter_value import join_value_and_type, split_value_and_type
from spinedb_api.spine_io.exporters.excel import export_spine_database_to_xlsx
from .spine_db_icon_manager import SpineDBIconManager
from .spine_db_worker import SpineDBWorker
from .spine_db_commands import SpineDBMacro, AgedUndoStack, AddItemsCommand, UpdateItemsCommand, RemoveItemsCommand
from .mvcmodels.shared import PARSED_ROLE
from .spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
from .helpers import get_upgrade_db_promt_text, busy_effect


@busy_effect
def do_create_new_spine_database(url):
    """Creates a new spine database at the given url."""
    create_new_spine_database(url)


class SpineDBManager(QObject):
    """Class to manage DBs within a project."""

    error_msg = Signal(dict)
    session_refreshed = Signal(set)
    session_committed = Signal(set, object)
    session_rolled_back = Signal(set)
    # Data changed signals
    items_added = Signal(str, dict)
    """Emitted whenever items are added to a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DiffDatabaseMapping to list of added dict-items.
    """
    items_updated = Signal(str, dict)
    """Emitted whenever items are updated in a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DiffDatabaseMapping to list of updated dict-items.
    """
    items_removed = Signal(str, dict)
    """Emitted whenever items are removed from a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DiffDatabaseMapping to list of updated dict-items.
    """
    # Closing
    waiting_for_fetcher = Signal()
    fetcher_waiting_over = Signal()

    def __init__(self, settings, parent):
        """Initializes the instance.

        Args:
            settings (QSettings): Toolbox settings
            parent (QObject, optional): parent object
        """
        super().__init__(parent)
        self.qsettings = settings
        self._db_maps = {}
        self.db_map_locks = {}
        self._workers = {}
        self.listeners = dict()
        self.undo_stack = {}
        self.undo_action = {}
        self.redo_action = {}
        self._icon_mngr = {}
        self._connect_signals()

    def _connect_signals(self):
        self.session_refreshed.connect(self.receive_session_refreshed)
        self.session_committed.connect(self.receive_session_committed)
        self.session_rolled_back.connect(self.receive_session_rolled_back)
        self.error_msg.connect(self.receive_error_msg)
        qApp.aboutToQuit.connect(self.clean_up)  # pylint: disable=undefined-variable

    @Slot(object)
    def receive_error_msg(self, db_map_error_log):
        for db_map, error_log in db_map_error_log.items():
            for listener in self.listeners.get(db_map, ()):
                listener.receive_error_msg({db_map: error_log})

    @Slot(set)
    def receive_session_refreshed(self, db_maps):
        for db_map in db_maps:
            for listener in self.listeners.get(db_map, ()):
                try:
                    listener.receive_session_refreshed([db_map])
                except AttributeError:
                    pass

    @Slot(set, object)
    def receive_session_committed(self, db_maps, cookie):
        for db_map in db_maps:
            for listener in self.listeners.get(db_map, ()):
                try:
                    listener.receive_session_committed([db_map], cookie)
                except AttributeError:
                    pass

    @Slot(set)
    def receive_session_rolled_back(self, db_maps):
        for db_map in db_maps:
            for listener in self.listeners.get(db_map, ()):
                try:
                    listener.receive_session_rolled_back([db_map])
                except AttributeError:
                    pass

    def _get_worker(self, db_map):
        """Returns a worker.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            SpineDBWorker
        """
        return self._workers[db_map]

    def can_fetch_more(self, db_map, parent):
        """Whether or not we can fetch more items of given type from given db.

        Args:
            db_map (DiffDatabaseMapping)
            parent (FetchParent): The object that requests the fetching and that might want to react to further DB
                modifications.

        Returns:
            bool
        """
        if db_map.connection.closed:
            return False
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return False
        return worker.can_fetch_more(parent)

    def fetch_more(self, db_map, parent):
        """Fetches more items of given type from given db.

        Args:
            db_map (DiffDatabaseMapping)
            parent (FetchParent): The object that requests the fetching.
        """
        if db_map.connection.closed:
            return
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return
        worker.fetch_more(parent)

    def add_items_to_cache(self, item_type, db_map_data):
        """Adds items to cache.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping

        Returns:
            dict: mapping db_map to added cache items
        """
        new_db_map_data = {}
        if item_type in ("object_class", "relationship_class"):
            self.update_icons(db_map_data)
        for db_map, items in db_map_data.items():
            table_cache = db_map.cache.table_cache(item_type)
            new_db_map_data[db_map] = [table_cache.add_item(item, keep_existing=True) for item in items]
        return new_db_map_data

    def update_items_in_cache(self, item_type, db_map_data):
        """Updates items in cache.

        Args:
            item_type (str)
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        if item_type in ("object_class", "relationship_class"):
            self.update_icons(db_map_data)
        for db_map, items in db_map_data.items():
            table_cache = db_map.cache.get(item_type)
            if table_cache is None:
                continue
            for item in items:
                table_cache.update_item(item)

    @staticmethod
    def remove_items_in_cache(item_type, db_map_ids):
        """Removes items in cache.

        Args:
            item_type (str)
            db_map_ids (dict): mapping db_map to ids to remove

        Returns:
            dict: mapping db_map to removed cache items
        """
        db_map_data = {}
        for db_map, ids in db_map_ids.items():
            table_cache = db_map.cache.get(item_type)
            if table_cache is None:
                continue
            db_map_data[db_map] = sum((table_cache.remove_item(id_) for id_ in ids), [])
        return db_map_data

    @busy_effect
    def get_db_map_cache(self, db_map, fetch_item_types=None, include_descendants=False, include_ancestors=False):
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return {}
        worker.fetch_all(
            fetch_item_types=fetch_item_types,
            include_descendants=include_descendants,
            include_ancestors=include_ancestors,
        )
        return db_map.cache

    def get_icon_mngr(self, db_map):
        """Returns an icon manager for given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            SpineDBIconManager
        """
        if db_map not in self._icon_mngr:
            self._icon_mngr[db_map] = SpineDBIconManager()
        return self._icon_mngr[db_map]

    def update_icons(self, db_map_data):
        """Runs when object classes are added or updated. Setups icons for those classes.

        Args:
            db_map_data (dict): lists of dictionary items keyed by DiffDatabaseMapping
        """
        for db_map, classes in db_map_data.items():
            self.get_icon_mngr(db_map).update_icon_caches(classes)

    @property
    def db_maps(self):
        return set(self._db_maps.values())

    @staticmethod
    def db_map_key(db_map):
        """Creates an identifier for given db_map.

        Args:
            db_map (DiffDatabaseMapping): database mapping

        Returns:
            int: identification key
        """
        return hash(db_map)

    def db_map_from_key(self, key):
        """Returns database mapping that corresponds to given identification key.

        Args:
            key (int): identification key

        Returns:
            DiffDatabaseMapping: database mapping

        Raises:
            KeyError: raised if database map is not found
        """
        return {self.db_map_key(db_map): db_map for db_map in self._db_maps.values()}[key]

    @property
    def db_urls(self):
        return set(self._db_maps)

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

    def create_new_spine_database(self, url, logger):
        try:
            if not is_empty(url):
                msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText(f"The URL <b>{url}</b> points to an existing database.")
                msg.setInformativeText("Do you want to overwrite it?")
                overwrite_button = msg.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
                msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                msg.exec()
                # We have custom buttons, exec() returns an opaque value.
                # Let's check the clicked button explicitly instead.
                clicked_button = msg.clickedButton()
                if clicked_button is not overwrite_button:
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
        lock = self.db_map_locks.pop(db_map)
        lock_failed_reported = False
        while not lock.tryLock(50):
            if not lock_failed_reported:
                self.waiting_for_fetcher.emit()
                lock_failed_reported = True
            qApp.processEvents()
        try:
            worker = self._workers.pop(db_map, None)
            if worker is not None:
                worker.close_db_map()
                worker.clean_up()
            db_map.cache.clear()
            del self.undo_stack[db_map]
            del self.undo_action[db_map]
            del self.redo_action[db_map]
        finally:
            lock.unlock()
            if lock_failed_reported:
                self.fetcher_waiting_over.emit()

    def close_all_sessions(self):
        """Closes connections to all database mappings."""
        for url in list(self._db_maps):
            self.close_session(url)

    def get_db_map(self, url, logger, codename=None, upgrade=False, create=False, ignore_version_error=False):
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
            if ignore_version_error:
                return None
            if v_err.upgrade_available:
                text, info_text = get_upgrade_db_promt_text(url, v_err.current, v_err.expected)
                msg = QMessageBox(self.parent() or qApp.activeWindow())  # pylint: disable=undefined-variable
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Incompatible database version")
                msg.setText(text)
                msg.setInformativeText(info_text)
                msg.addButton(QMessageBox.StandardButton.Cancel)
                msg.addButton("Upgrade", QMessageBox.ButtonRole.YesRole)
                ret = msg.exec()  # Show message box
                if ret == QMessageBox.StandardButton.Cancel:
                    return None
                return self.get_db_map(url, logger, codename=codename, upgrade=True, create=create)
            QMessageBox.information(
                qApp.activeWindow(),  # pylint: disable=undefined-variable
                "Unsupported database version",
                f"Database at <b>{url}</b> is newer than this version of Spine Toolbox can handle.<br><br>"
                f"The db is at revision <b>{v_err.current}</b> while this version "
                f"of Spine Toolbox supports revisions up to <b>{v_err.expected}</b>.<br><br>"
                "Please upgrade Spine Toolbox to open this database.",
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
        worker = SpineDBWorker(self, url)
        try:
            db_map = worker.get_db_map(codename=codename, upgrade=upgrade, create=create)
        except Exception as error:
            worker.clean_up()
            raise error
        self._workers[db_map] = worker
        self._db_maps[url] = db_map
        self.db_map_locks[db_map] = QRecursiveMutex()  # TODO: Plain QMutex() would be faster here. Can we use it?
        stack = self.undo_stack[db_map] = AgedUndoStack(self)
        self.undo_action[db_map] = stack.createUndoAction(self)
        self.redo_action[db_map] = stack.createRedoAction(self)
        return db_map

    def query(self, db_map, sq_name):
        """For tests."""
        return self._get_worker(db_map).query(sq_name)

    def add_db_map_listener(self, db_map, listener):
        """Adds listener for given db_map."""
        self.listeners.setdefault(db_map, set()).add(listener)

    def remove_db_map_listener(self, db_map, listener):
        """Removes db_map from the maps listener listens to."""
        listeners = self.listeners.get(db_map, set())
        listeners.discard(listener)
        if not listeners:
            self.listeners.pop(db_map)

    def db_map_listeners(self, db_map):
        return self.listeners.get(db_map, set())

    def register_listener(self, listener, *db_maps):
        """Register given listener for all given db_map's signals.

        Args:
            listener (object)
            db_maps (DiffDatabaseMapping)
        """
        for db_map in db_maps:
            self.add_db_map_listener(db_map, listener)
            stack = self.undo_stack[db_map]
            try:
                stack.canRedoChanged.connect(listener.update_undo_redo_actions)
                stack.canUndoChanged.connect(listener.update_undo_redo_actions)
                stack.cleanChanged.connect(listener.update_commit_enabled)
            except AttributeError:
                pass

    def unregister_listener(self, listener, *db_maps, dirty_db_maps=None, commit_dirty=False, commit_msg=""):
        """Unregisters given listener from given db_map signals.
        If any of the db_maps becomes an orphan and is dirty, prompts user to commit or rollback.

        Args:
            listener (object)
            *db_maps (DiffDatabaseMapping)
            commit_dirty (bool): True to commit dirty database mapping, False to roll back
            commit_msg (str): commit message
        """
        for db_map in db_maps:
            self.remove_db_map_listener(db_map, listener)
            try:
                self.undo_stack[db_map].canRedoChanged.disconnect(listener.update_undo_redo_actions)
                self.undo_stack[db_map].canUndoChanged.disconnect(listener.update_undo_redo_actions)
                self.undo_stack[db_map].cleanChanged.disconnect(listener.update_commit_enabled)
            except AttributeError:
                pass
        if dirty_db_maps:
            if commit_dirty:
                self.commit_session(commit_msg, *dirty_db_maps)
            else:
                self.rollback_session(*dirty_db_maps)
        for db_map in db_maps:
            if not self.db_map_listeners(db_map):
                self.close_session(db_map.db_url)

    def is_dirty(self, db_map):
        """Returns True if mapping has pending changes.

        Args:
            db_map (DiffDatabaseMapping): database mapping

        Returns:
            bool: True if db_map has pending changes, False otherwise
        """
        return not self.undo_stack[db_map].isClean()

    def dirty(self, *db_maps):
        """Filters clean mappings from given database maps.

        Args:
            *db_maps: mappings to check

        Return:
            list of DiffDatabaseMapping: dirty  mappings
        """
        return [db_map for db_map in db_maps if self.is_dirty(db_map)]

    def dirty_and_without_editors(self, listener, *db_maps):
        """Checks which of the given database mappings are dirty and have no editors.

        Args:
            listener (Any): a listener object
            *db_maps: mappings to check

        Return:
            list of DiffDatabaseMapping: mappings that are dirty and don't have editors
        """

        def has_editors(db_map):
            return any(
                hasattr(x, "is_db_map_editor") and x.is_db_map_editor()
                for x in self.db_map_listeners(db_map) - {listener}
            )

        return [db_map for db_map in self.dirty(*db_maps) if not has_editors(db_map)]

    def clean_up(self):
        while self._workers:
            _, worker = self._workers.popitem()
            worker.clean_up()
        self.deleteLater()

    def refresh_session(self, *db_maps):
        refreshed_db_maps = set(db_map for db_map in db_maps if db_map in self.db_maps)
        if not refreshed_db_maps:
            return
        for db_map in refreshed_db_maps:
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                continue
            worker.reset_queries()
            db_map.cache.clear()
        self.session_refreshed.emit(refreshed_db_maps)

    def commit_session(self, commit_msg, *dirty_db_maps, cookie=None):
        """
        Commits the current session.

        Args:
            commit_msg (str): commit message for all database maps
            *dirty_db_maps: dirty database maps to commit
            cookie (object, optional): a free form identifier which will be forwarded to ``session_committed`` signal
        """
        for db_map in dirty_db_maps:
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                continue
            worker.commit_session(commit_msg, cookie)

    def notify_session_committed(self, cookie, *db_maps):
        """Notifies manager and listeners when a commit has taken place by a third party.

        Args:
            cookie (Any): commit cookie
            *db_maps: database maps that were committed
        """
        self.refresh_session(*db_maps)
        self.session_committed.emit(set(db_maps), cookie)

    def rollback_session(self, *dirty_db_maps):
        """
        Rolls back the current session.

        Args:
            *dirty_db_maps: dirty database maps to commit
        """
        for db_map in dirty_db_maps:
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                continue
            worker.rollback_session()
            worker.reset_queries()

    def entity_class_renderer(self, db_map, entity_type, entity_class_id, for_group=False):
        """Returns an icon renderer for a given entity class.

        Args:
            db_map (DiffDatabaseMapping): database map
            entity_type (str): either 'object_class' or 'relationship_class'
            entity_class_id (int): entity class' id
            for_group (bool): if True, return the group object icon instead

        Returns:
            QSvgRenderer: requested renderer or None if no entity class was found
        """
        entity_class = self.get_item(db_map, entity_type, entity_class_id)
        if not entity_class:
            return None
        if entity_type == "object_class":
            if for_group:
                return self.get_icon_mngr(db_map).group_renderer(entity_class["name"])
            return self.get_icon_mngr(db_map).class_renderer(entity_class["name"])
        if entity_type == "relationship_class":
            return self.get_icon_mngr(db_map).relationship_class_renderer(
                entity_class["name"], entity_class["object_class_name_list"]
            )

    def entity_class_icon(self, db_map, entity_type, entity_class_id, for_group=False):
        """Returns an appropriate icon for a given entity class.

        Args:
            db_map (DiffDatabaseMapping): database map
            entity_type (str): either 'object_class' or 'relationship_class'
            entity_class_id (int): entity class' id
            for_group (bool): if True, return the group object icon instead

        Returns:
            QIcon: requested icon or None if no entity class was found
        """
        renderer = self.entity_class_renderer(db_map, entity_type, entity_class_id, for_group=for_group)
        return SpineDBIconManager.icon_from_renderer(renderer) if renderer is not None else None

    def get_item(self, db_map, item_type, id_, only_visible=True):
        """Returns the item of the given type in the given db map that has the given id,
        or an empty dict if not found.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            id_ (int)
            only_visible (bool, optional): If True, only looks in items that have already made it into the cache.

        Returns:
            CacheItem: cached item
        """
        item = db_map.cache.get(item_type, {}).get(id_, {})
        if only_visible and item:
            return item
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return {}
        worker.fetch_all(fetch_item_types={item_type})
        return db_map.cache.get(item_type, {}).get(id_, {})

    def get_field(self, db_map, item_type, id_, field, only_visible=True):
        return self.get_item(db_map, item_type, id_, only_visible=only_visible).get(field)

    def get_items(self, db_map, item_type, only_visible=True):
        """Returns a list of the items of the given type in the given db map.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            only_visible (bool, optional): If True, only returns items that have already made it into the cache.

        Returns:
            list
        """
        items = list(db_map.cache.get(item_type, {}).values())
        if only_visible:
            return items
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return []
        worker.fetch_all(fetch_item_types={item_type})
        return list(db_map.cache.get(item_type, {}).values())

    def get_items_by_field(self, db_map, item_type, field, value, only_visible=True):
        """Returns a list of items of the given type in the given db map that have the given value
        for the given field.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            field (str)
            value

        Returns:
            list
        """
        return [x for x in self.get_items(db_map, item_type, only_visible=only_visible) if x.get(field) == value]

    def get_item_by_field(self, db_map, item_type, field, value, only_visible=True):
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
        return next(iter(self.get_items_by_field(db_map, item_type, field, value, only_visible=only_visible)), {})

    @staticmethod
    def display_data_from_parsed(parsed_data):
        """Returns the value's database representation formatted for Qt.ItemDataRole.DisplayRole."""
        if isinstance(parsed_data, TimeSeries):
            display_data = "Time series"
        elif isinstance(parsed_data, Map):
            display_data = "Map"
        elif isinstance(parsed_data, Array):
            display_data = "Array"
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
    def tool_tip_data_from_parsed(parsed_data):
        """Returns the value's database representation formatted for Qt.ItemDataRole.ToolTipRole."""
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

    def _format_list_value(self, db_map, item_type, value, list_value_id):
        list_value = self.get_item(db_map, "list_value", list_value_id)
        if not list_value:
            return value
        index = list_value["index"]
        formatted_value = "[" + str(index) + "] " + value
        if item_type != "list_value":
            value_list_name = self.get_item(db_map, "parameter_value_list", list_value["parameter_value_list_id"])[
                "name"
            ]
            formatted_value = value_list_name + formatted_value
        return formatted_value

    def get_value(self, db_map, item_type, id_, role=Qt.ItemDataRole.DisplayRole):
        """Returns the value or default value of a parameter.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str): either "parameter_definition", "parameter_value", or "list_value"
            id_ (int): The parameter_value or definition id
            role (int, optional)

        Returns:
            any
        """
        item = self.get_item(db_map, item_type, id_)
        if not item:
            return None
        value_field, type_field = {
            "parameter_value": ("value", "type"),
            "list_value": ("value", "type"),
            "parameter_definition": ("default_value", "default_type"),
        }[item_type]
        list_value_id = id_ if item_type == "list_value" else item["list_value_id"]
        complex_types = {"array": "Array", "time_series": "Time series", "time_pattern": "Time pattern", "map": "Map"}
        if role == Qt.ItemDataRole.DisplayRole and item[type_field] in complex_types:
            return self._format_list_value(db_map, item_type, complex_types[item[type_field]], list_value_id)
        if role == Qt.ItemDataRole.EditRole:
            return join_value_and_type(item[value_field], item[type_field])
        key = "parsed_value"
        if key not in item:
            item[key] = self._parse_value(item[value_field], item[type_field])
        return self._format_value(item[key], role=role)

    def get_value_from_data(self, data, role=Qt.ItemDataRole.DisplayRole):
        """Returns the value or default value of a parameter directly from data.
        Used by ``EmptyParameterModel.data()``.

        Args:
            data (str): joined value and type
            role (int, optional)

        Returns:
            any
        """
        if data is None:
            return None
        parsed_value = self._parse_value(*split_value_and_type(data))
        return self._format_value(parsed_value, role=role)

    @staticmethod
    def _parse_value(db_value, value_type=None):
        try:
            return from_database(db_value, value_type=value_type)
        except ParameterValueFormatError as error:
            return error

    def _format_value(self, parsed_value, role=Qt.ItemDataRole.DisplayRole):
        """Formats the given value for the given role.

        Args:
            parsed_value (object): A python object as returned by spinedb_api.from_database
            role (int, optional)
        """
        if role == Qt.ItemDataRole.DisplayRole:
            return self.display_data_from_parsed(parsed_value)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.tool_tip_data_from_parsed(parsed_value)
        if role == Qt.TextAlignmentRole:
            if isinstance(parsed_value, str):
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)
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

    def get_value_index(self, db_map, item_type, id_, index, role=Qt.ItemDataRole.DisplayRole):
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
        if role == Qt.ItemDataRole.EditRole:
            return join_value_and_type(*to_database(parsed_value))
        if role == Qt.ItemDataRole.DisplayRole:
            return self.display_data_from_parsed(parsed_value)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.tool_tip_data_from_parsed(parsed_value)
        if role == PARSED_ROLE:
            return parsed_value
        return None

    def get_value_list_item(self, db_map, id_, index, role=Qt.ItemDataRole.DisplayRole, only_visible=True):
        """Returns one value item of a parameter_value_list.

        Args:
            db_map (DiffDatabaseMapping)
            id_ (int): The parameter_value_list id
            index (int): The value item index
            role (int, optional)
        """
        try:
            return self.get_parameter_value_list(db_map, id_, role=role, only_visible=only_visible)[index]
        except IndexError:
            return None

    def get_parameter_value_list(self, db_map, id_, role=Qt.ItemDataRole.DisplayRole, only_visible=True):
        """Returns a parameter_value_list formatted for the given role.

        Args:
            db_map (DiffDatabaseMapping)
            id_ (int): The parameter_value_list id
            role (int, optional)
        """
        return [
            self.get_value(db_map, "list_value", item["id"], role=role)
            for item in self.get_items_by_field(
                db_map, "list_value", "parameter_value_list_id", id_, only_visible=only_visible
            )
        ]

    def get_scenario_alternative_id_list(self, db_map, scen_id, only_visible=True):
        scenario = self.get_item(db_map, "scenario", scen_id, only_visible=only_visible)
        if not scenario:
            return []
        return scenario["alternative_id_list"]

    def import_data(self, db_map_data, command_text="Import data"):
        """Imports the given data into given db maps using the dedicated import functions from spinedb_api.
        Condenses all in a single command for undo/redo.

        Args:
            db_map_data (dict(DiffDatabaseMapping, dict())): Maps dbs to data to be passed as keyword arguments
                to `get_data_for_import`
            command_text (str, optional): What to call the command that condenses the operation.
        """
        db_map_error_log = dict()
        for db_map, data in db_map_data.items():

            def make_cache(*args, **kwargs):
                return self.get_db_map_cache(db_map)

            try:
                data_for_import = get_data_for_import(db_map, make_cache=make_cache, **data)
            except (TypeError, ValueError) as err:
                msg = f"Failed to import data: {err}. Please check that your data source has the right format."
                db_map_error_log.setdefault(db_map, []).append(msg)
                continue
            cmd_iter = self._import_data_cmds(db_map, data_for_import, db_map_error_log)
            macro = SpineDBMacro(cmd_iter)
            macro.setText(command_text)
            self.undo_stack[db_map].push(macro)
        if any(db_map_error_log.values()):
            self.error_msg.emit(db_map_error_log)

    def import_data_commands(self, db_map, data):
        """Creates undo commands necessary to import given data.

        Args:
            db_map (DatabaseMapping): target database mapping
            data (dict): data to import

        Yields:
            SpineDBCommand: import undo command
        """

        def make_cache(*args, **kwargs):
            return self.get_db_map_cache(db_map)

        db_map_error_log = dict()
        data_for_import = get_data_for_import(db_map, make_cache=make_cache, **data)
        yield from self._import_data_cmds(db_map, data_for_import, db_map_error_log)

    def _import_data_cmds(self, db_map, data_for_import, db_map_error_log):
        for item_type, (to_add, to_update, import_error_log) in data_for_import:
            db_map_error_log.setdefault(db_map, []).extend([str(x) for x in import_error_log])
            if to_update:
                yield UpdateItemsCommand(self, db_map, to_update, item_type, check=False)
            if to_add:
                yield AddItemsCommand(self, db_map, to_add, item_type, check=False)

    def add_items(self, db_map_data, item_type, readd=False, cascade=True, check=True, callback=None):
        for db_map, data in db_map_data.items():
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                # We're closing the kiosk.
                continue
            cache = self.get_db_map_cache(db_map)
            worker.add_items(data, item_type, readd, cascade, check, cache, callback)

    def update_items(self, db_map_data, item_type, check=True, callback=None):
        for db_map, data in db_map_data.items():
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                # We're closing the kiosk.
                continue
            cache = self.get_db_map_cache(db_map)
            worker.update_items(data, item_type, check, cache, callback)

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

    def add_object_metadata(self, db_map_data):
        """Adds object metadata to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "object_metadata"))

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

    def add_parameter_value_lists(self, db_map_data):
        """Adds parameter_value lists to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_value_list"))

    def add_list_values(self, db_map_data):
        """Adds parameter_value list values to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "list_value"))

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

    def add_metadata(self, db_map_data):
        """Adds metadata to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "metadata"))

    def add_entity_metadata(self, db_map_data):
        """Adds entity metadata to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "entity_metadata"))

    def add_parameter_value_metadata(self, db_map_data):
        """Adds parameter value metadata to db.

        Args:
            db_map_data (dict): lists of items to add keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(AddItemsCommand(self, db_map, data, "parameter_value_metadata"))

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

    def update_expanded_parameter_values(self, db_map_data):
        """Updates expanded parameter values in db without checking integrity.

        Args:
            db_map_data (dict): lists of expanded items to update keyed by DiffDatabaseMapping
        """
        for db_map, expanded_data in db_map_data.items():
            packed_data = {}
            for item in expanded_data:
                packed_data.setdefault(item["id"], {})[item["index"]] = (item["value"], item["type"])
            items = []
            for id_, indexed_values in packed_data.items():
                parsed_value = self.get_value(db_map, "parameter_value", id_, role=PARSED_ROLE)
                if isinstance(parsed_value, IndexedValue):
                    for index, (val, typ) in indexed_values.items():
                        parsed_val = from_database(val, typ)
                        parsed_value.set_value(index, parsed_val)
                    value, value_type = to_database(parsed_value)
                else:
                    value, value_type = next(iter(indexed_values.values()))
                item = {"id": id_, "value": value, "type": value_type}
                items.append(item)
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, items, "parameter_value"))

    def update_parameter_value_lists(self, db_map_data):
        """Updates parameter_value lists in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_value_list"))

    def update_list_values(self, db_map_data):
        """Updates parameter_value list values in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "list_value"))

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

    def update_metadata(self, db_map_data):
        """Updates metadata in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "metadata"))

    def update_entity_metadata(self, db_map_data):
        """Updates entity metadata in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "entity_metadata"))

    def update_parameter_value_metadata(self, db_map_data):
        """Updates parameter value metadata in db.

        Args:
            db_map_data (dict): lists of items to update keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, data, "parameter_value_metadata"))

    def set_scenario_alternatives(self, db_map_data):
        """Sets scenario alternatives in db.

        Args:
            db_map_data (dict): lists of items to set keyed by DiffDatabaseMapping
        """
        for db_map, data in db_map_data.items():
            child_cmds = []
            cache = self.get_db_map_cache(db_map)
            items_to_add, ids_to_remove = db_map.get_data_to_set_scenario_alternatives(*data, cache=cache)
            if ids_to_remove:
                rm_cmd = RemoveItemsCommand(self, db_map, ids_to_remove, "scenario_alternative")
                child_cmds.append(rm_cmd)
            if items_to_add:
                add_cmd = AddItemsCommand(self, db_map, items_to_add, "scenario_alternative")
                child_cmds.append(add_cmd)
            if child_cmds:
                macro = SpineDBMacro(iter(child_cmds))
                macro.setText(f"set scenario alternatives in {db_map.codename}")
                self.undo_stack[db_map].push(macro)

    def purge_items(self, db_map_purgable_items):
        """Purges selected items from given database.

        Args:
            db_map_purgable_items (dict): mapping from database map to list of purgable item types
        """
        db_map_typed_data = {
            db_map: {
                item_type: {x["id"] for x in self.get_items(db_map, item_type, only_visible=False)}
                for item_type in item_types
            }
            for db_map, item_types in db_map_purgable_items.items()
        }
        self.remove_items(db_map_typed_data)

    def remove_items(self, db_map_typed_ids):
        """Pushes a command to remove items to undo stack."""
        for db_map, ids_per_type in db_map_typed_ids.items():
            macro = SpineDBMacro(self._remove_items_commands(db_map, ids_per_type))
            self.undo_stack[db_map].push(macro)

    def _remove_items_commands(self, db_map, ids_per_type):
        for item_type, ids_ in ids_per_type.items():
            yield RemoveItemsCommand(self, db_map, ids_, item_type)

    @busy_effect
    def do_remove_items(self, item_type, db_map_ids, callback=None, committing_callback=None):
        """Removes items from database.

        Args:
            item_type (str): database item type
            db_map_ids (dict): mapping DatabaseMapping to removable ids
            callback (Callable, optional): function to call after removal is finished
            committing_callback (Callable, optional): function to call after removal has been committed
        """
        for db_map, ids in db_map_ids.items():
            try:
                worker = self._get_worker(db_map)
            except KeyError:
                continue
            worker.remove_items(item_type, ids, callback, committing_callback)

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

    def find_cascading_relationship_classes(self, db_map_ids, only_visible=True):
        """Finds and returns cascading relationship classes for the given object_class ids."""
        db_map_cascading_data = dict()
        for db_map, object_class_ids in db_map_ids.items():
            for item in self.get_items(db_map, "relationship_class", only_visible=only_visible):
                if set(item["object_class_id_list"]) & set(object_class_ids):
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_cascading_relationships(self, db_map_ids, only_visible=True):
        """Finds and returns cascading relationships for the given object ids."""
        db_map_cascading_data = dict()
        for db_map, object_ids in db_map_ids.items():
            for item in self.get_items(db_map, "relationship", only_visible=only_visible):
                if set(item["object_id_list"]) & set(object_ids):
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_cascading_parameter_data(self, db_map_ids, item_type, only_visible=True):
        """Finds and returns cascading parameter definitions or values for the given entity_class ids."""
        db_map_cascading_data = dict()
        for db_map, entity_class_ids in db_map_ids.items():
            for item in self.get_items(db_map, item_type, only_visible=only_visible):
                if item["entity_class_id"] in entity_class_ids:
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_cascading_parameter_values_by_entity(self, db_map_ids, only_visible=True):
        """Finds and returns cascading parameter values for the given entity ids."""
        db_map_cascading_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            for item in self.get_items(db_map, "parameter_value", only_visible=only_visible):
                if item["entity_id"] in entity_ids:
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_cascading_parameter_values_by_definition(self, db_map_ids, only_visible=True):
        """Finds and returns cascading parameter values for the given parameter_definition ids."""
        db_map_cascading_data = dict()
        for db_map, param_def_ids in db_map_ids.items():
            for item in self.get_items(db_map, "parameter_value", only_visible=only_visible):
                if item["parameter_id"] in param_def_ids:
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_cascading_scenario_alternatives_by_scenario(self, db_map_ids, only_visible=True):
        """Finds and returns cascading scenario alternatives for the given scenario ids."""
        db_map_cascading_data = dict()
        for db_map, ids in db_map_ids.items():
            for item in self.get_items(db_map, "scenario_alternative", only_visible=only_visible):
                if item["scenario_id"] in ids:
                    db_map_cascading_data.setdefault(db_map, []).append(item)
        return db_map_cascading_data

    def find_groups_by_entity(self, db_map_ids, only_visible=True):
        """Finds and returns groups for the given entity ids."""
        db_map_group_data = dict()
        for db_map, entity_ids in db_map_ids.items():
            for item in self.get_items(db_map, "entity_group", only_visible=only_visible):
                if item["entity_id"] in entity_ids:
                    db_map_group_data.setdefault(db_map, []).append(item)
        return db_map_group_data

    def duplicate_scenario(self, scen_data, dup_name, db_map):
        data = self._get_data_for_export(scen_data)
        data = {
            "scenarios": [(dup_name, active, description) for (_, active, description) in data.get("scenarios", [])],
            "alternatives": data.get("alternatives", []),
            "scenario_alternatives": [
                (dup_name, alt_name, before_alt_name)
                for (_, alt_name, before_alt_name) in data.get("scenario_alternatives", [])
            ],
        }
        self.import_data({db_map: data}, command_text="Duplicate scenario")

    def duplicate_object(self, object_data, orig_name, dup_name, db_maps):
        _replace_name = lambda name_list: [name if name != orig_name else dup_name for name in name_list]
        data = self._get_data_for_export(object_data)
        data = {
            "objects": [
                (cls_name, dup_name, description) for (cls_name, obj_name, description) in data.get("objects", [])
            ],
            "relationships": [
                (cls_name, _replace_name(obj_name_lst)) for (cls_name, obj_name_lst) in data.get("relationships", [])
            ],
            "object_parameter_values": [
                (cls_name, dup_name, param_name, val, alt)
                for (cls_name, obj_name, param_name, val, alt) in data.get("object_parameter_values", [])
            ],
            "relationship_parameter_values": [
                (cls_name, _replace_name(obj_name_lst), param_name, val, alt)
                for (cls_name, obj_name_lst, param_name, val, alt) in data.get("relationship_parameter_values", [])
            ],
        }
        self.import_data({db_map: data for db_map in db_maps}, command_text="Duplicate object")

    def _get_data_for_export(self, db_map_item_ids):
        data = {}
        for db_map, item_ids in db_map_item_ids.items():
            make_cache = lambda tablenames, db_map=db_map, **kwargs: self.get_db_map_cache(
                db_map, fetch_item_types=tablenames, **kwargs
            )

            for key, items in export_data(db_map, make_cache=make_cache, parse_value=load_db_value, **item_ids).items():
                data.setdefault(key, []).extend(items)
        return data

    def export_data(self, caller, db_map_item_ids, file_path, file_filter):
        data = self._get_data_for_export(db_map_item_ids)
        if file_filter.startswith("JSON"):
            self.export_to_json(file_path, data, caller)
        elif file_filter.startswith("SQLite"):
            self.export_to_sqlite(file_path, data, caller)
        elif file_filter.startswith("Excel"):
            self.export_to_excel(file_path, data, caller)
        else:
            raise ValueError()

    def _is_url_available(self, url, logger):
        if str(url) in self.db_urls:
            message = f"The URL <b>{url}</b> is in use. Please close all applications using it and try again."
            logger.msg_error.emit(message)
            return False
        return True

    def export_to_sqlite(self, file_path, data_for_export, caller):
        """Exports given data into SQLite file."""
        url = URL("sqlite", database=file_path)
        if not self._is_url_available(url, caller):
            return
        create_new_spine_database(url)
        db_map = DatabaseMapping(url)
        import_data(db_map, **data_for_export)
        try:
            db_map.commit_session("Export data from Spine Toolbox.")
        except SpineDBAPIError as err:
            error_msg = {None: [f"[SpineDBAPIError] Unable to export file <b>{db_map.codename}</b>: {err.msg}"]}
            caller.msg_error.emit(error_msg)
        else:
            caller.sqlite_file_exported.emit(file_path)
        finally:
            db_map.connection.close()

    def export_to_json(self, file_path, data_for_export, caller):  # pylint: disable=no-self-use
        """Exports given data into JSON file."""
        json_data = json.dumps(data_for_export, indent=4)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        caller.file_exported.emit(file_path)

    def export_to_excel(self, file_path, data_for_export, caller):  # pylint: disable=no-self-use
        """Exports given data into Excel file."""
        # NOTE: We import data into an in-memory Spine db and then export that to excel.
        url = URL("sqlite", database="")
        db_map = DatabaseMapping(url, create=True)
        import_data(db_map, **data_for_export)
        file_name = os.path.split(file_path)[1]
        if os.path.exists(file_path):
            os.remove(file_path)
        try:
            export_spine_database_to_xlsx(db_map, file_path)
        except PermissionError:
            error_msg = {
                None: [f"Unable to export file <b>{file_name}</b>.<br/>Close the file in Excel and try again."]
            }
            caller.msg_error.emit(error_msg)
        except OSError:
            error_msg = {None: [f"[OSError] Unable to export file <b>{file_name}</b>."]}
            caller.msg_error.emit(error_msg)
        else:
            caller.file_exported.emit(file_path)
        finally:
            db_map.connection.close()

    def get_items_for_commit(self, db_map, commit_id):
        try:
            worker = self._get_worker(db_map)
        except KeyError:
            return {}
        worker.fetch_all()
        return worker.commit_cache.get(commit_id, {})

    @staticmethod
    def get_all_multi_spine_db_editors():
        """Yields all instances of MultiSpineDBEditor currently open.

        Yields:
            MultiSpineDBEditor
        """
        for window in qApp.topLevelWindows():  # pylint: disable=undefined-variable
            if isinstance(window, QWindow):
                widget = QWidget.find(window.winId())
                if isinstance(widget, MultiSpineDBEditor) and widget.accepting_new_tabs:
                    yield widget

    def get_all_spine_db_editors(self):
        """Yields all instances of SpineDBEditor currently open.

        Yields:
            SpineDBEditor
        """
        for w in self.get_all_multi_spine_db_editors():
            for k in range(w.tab_widget.count()):
                yield w.tab_widget.widget(k)

    def _get_existing_spine_db_editor(self, db_url_codenames):
        db_url_codenames = {str(url): codename for url, codename in db_url_codenames.items()}
        for multi_db_editor in self.get_all_multi_spine_db_editors():
            for k in range(multi_db_editor.tab_widget.count()):
                db_editor = multi_db_editor.tab_widget.widget(k)
                if db_editor.db_url_codenames == db_url_codenames:
                    return multi_db_editor, db_editor
        return None

    def open_db_editor(self, db_url_codenames):
        """Opens a SpineDBEditor with given urls. Uses an existing MultiSpineDBEditor if any.
        Also, if the same urls are open in an existing SpineDBEditor, just raises that one
        instead of creating another.

        Args:
            db_url_codenames (dict): mapping url to codename
        """
        multi_db_editor = next(self.get_all_multi_spine_db_editors(), None)
        if multi_db_editor is None:
            multi_db_editor = MultiSpineDBEditor(self, db_url_codenames)
            multi_db_editor.show()
            return
        existing = self._get_existing_spine_db_editor(db_url_codenames)
        if existing is None:
            multi_db_editor.add_new_tab(db_url_codenames)
        else:
            multi_db_editor, db_editor = existing
            multi_db_editor.set_current_tab(db_editor)
        if multi_db_editor.isMinimized():
            multi_db_editor.showNormal()
        multi_db_editor.activateWindow()
