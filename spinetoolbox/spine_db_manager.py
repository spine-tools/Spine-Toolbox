######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""The SpineDBManager class."""
from collections.abc import Iterable
from contextlib import suppress
import json
import os
from threading import RLock
from typing import Any, Optional, Union
import numpy as np
import numpy.typing as nptyping
from PySide6.QtCore import QObject, QSettings, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy.engine.url import URL
from spinedb_api import (
    Array,
    Asterisk,
    DatabaseMapping,
    IndexedValue,
    Map,
    ParameterValueFormatError,
    SpineDBAPIError,
    TimePattern,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    create_new_spine_database,
    export_data,
    from_database,
    get_data_for_import,
    import_data,
    is_empty,
    relativedelta_to_duration,
    to_database,
)
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.exception import NothingToCommit
from spinedb_api.helpers import remove_credentials_from_url
from spinedb_api.parameter_value import (
    MapIndex,
    Value,
    deep_copy_value,
    dump_db_value,
    join_value_and_type,
    load_db_value,
    split_value_and_type,
)
from spinedb_api.spine_io.exporters.excel import export_spine_database_to_xlsx
from spinedb_api.temp_id import TempId
from spinetoolbox.database_display_names import NameRegistry
from .fetch_parent import FetchParent
from .helpers import DBMapDictItems, DBMapPublicItems, busy_effect, plain_to_tool_tip
from .logger_interface import LoggerInterface
from .mvcmodels.shared import INVALID_TYPE, PARAMETER_TYPE_VALIDATION_ROLE, PARSED_ROLE, TYPE_NOT_VALIDATED, VALID_TYPE
from .parameter_type_validation import ParameterTypeValidator
from .spine_db_commands import (
    AddItemsCommand,
    AddUpdateItemsCommand,
    AgedUndoStack,
    RemoveItemsCommand,
    UpdateItemsCommand,
)
from .spine_db_icon_manager import SpineDBIconManager
from .spine_db_worker import SpineDBWorker
from .widgets.options_dialog import OptionsDialog

ValidatedValueCache = dict[str, dict[int, dict[int, bool]]]


@busy_effect
def do_create_new_spine_database(url: str) -> None:
    """Creates a new spine database at the given url."""
    create_new_spine_database(url)


class SpineDBManager(QObject):
    """Class to manage DBs within a project."""

    error_msg = Signal(object)
    # Data changed signals
    items_added = Signal(str, dict)
    """Emitted whenever items are added to a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DatabaseMapping to list of added dict-items.
    """
    items_updated = Signal(str, dict)
    """Emitted whenever items are updated in a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DatabaseMapping to list of updated dict-items.
    """
    items_removed = Signal(str, dict)
    """Emitted whenever items are removed from a DB.

    Args:
        str: item type, such as "object_class"
        dict: mapping DatabaseMapping to list of updated dict-items.
    """
    database_clean_changed = Signal(object, bool)
    """Emitted whenever database becomes clean or dirty.

    Args:
        object: database mapping
        bool: True if database has become clean, False if it became dirty
    """
    database_reset = Signal(object)
    """Emitted whenever database is reset.

    Args:
        object: database mapping
    """

    def __init__(self, settings: QSettings, parent: Optional[QObject], synchronous: bool = False):
        """
        Args:
            settings: Toolbox settings
            parent : parent object
            synchronous: If True, fetch database synchronously
        """
        super().__init__(parent)
        self.qsettings = settings
        self._db_maps = {}
        self.name_registry = NameRegistry(self)
        self._workers: dict[DatabaseMapping, SpineDBWorker] = {}
        self._lock_lock = RLock()
        self._db_locks: dict[DatabaseMapping, RLock] = {}
        self.listeners: dict[DatabaseMapping, set[object]] = {}
        self.undo_stack: dict[DatabaseMapping, AgedUndoStack] = {}
        self.undo_action: dict[DatabaseMapping, QAction] = {}
        self.redo_action: dict[DatabaseMapping, QAction] = {}
        self._icon_mngr: dict[DatabaseMapping, SpineDBIconManager] = {}
        self._connect_signals()
        self._cmd_id = 0
        self._synchronous = synchronous
        self._validated_values: ValidatedValueCache = {"parameter_definition": {}, "parameter_value": {}}
        self._parameter_type_validator = ParameterTypeValidator(self)
        self._parameter_type_validator.validated.connect(self._parameter_value_validated)
        self._no_prompt_urls: set[str] = set()

    def _connect_signals(self) -> None:
        self.error_msg.connect(self.receive_error_msg)
        qApp.aboutToQuit.connect(self.clean_up)  # pylint: disable=undefined-variable

    @property
    def parameter_type_validator(self) -> ParameterTypeValidator:
        return self._parameter_type_validator

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

    def get_lock(self, db_map: DatabaseMapping) -> RLock:
        return self._db_locks[db_map]

    def register_fetch_parent(self, db_map: DatabaseMapping, parent: FetchParent) -> None:
        """Registers a fetch parent.

        Args:
            db_map: target database mapping
            parent: fetch parent
        """
        if db_map.closed:
            return
        try:
            worker = self._workers[db_map]
        except KeyError:
            return
        worker.register_fetch_parent(parent)

    def can_fetch_more(self, db_map: DatabaseMapping, parent: FetchParent) -> bool:
        """Whether we can fetch more items of given type from given db."""
        if db_map.closed:
            return False
        try:
            worker = self._workers[db_map]
        except KeyError:
            return False
        return worker.can_fetch_more(parent)

    def fetch_more(self, db_map: DatabaseMapping, parent: FetchParent) -> None:
        """Fetches more items for fetch parent from given db."""
        if db_map.closed:
            return
        try:
            worker = self._workers[db_map]
        except KeyError:
            return
        worker.fetch_more(parent)

    def get_icon_mngr(self, db_map: DatabaseMapping) -> SpineDBIconManager:
        """Returns an icon manager for given db_map."""
        if db_map not in self._icon_mngr:
            self._icon_mngr[db_map] = SpineDBIconManager()
        return self._icon_mngr[db_map]

    def update_icons(self, db_map: DatabaseMapping, item_type: str, items: Iterable[PublicItem]) -> None:
        """Runs when items are added or updated. Setups icons."""
        if item_type == "entity_class":
            self.get_icon_mngr(db_map).update_icon_caches(items)

    @property
    def db_maps(self) -> set[DatabaseMapping]:
        return set(self._db_maps.values())

    @staticmethod
    def db_map_key(db_map: DatabaseMapping) -> str:
        """Creates an identifier for given db_map.

        Args:
            db_map: database mapping

        Returns:
            identification key
        """
        return str(hash(db_map))

    def db_map_from_key(self, key: str) -> DatabaseMapping:
        """Returns database mapping that corresponds to given identification key.

        Args:
            key: identification key

        Returns:
            database mapping

        Raises:
            KeyError: raised if database map is not found
        """
        return {self.db_map_key(db_map): db_map for db_map in self._db_maps.values()}[key]

    @property
    def db_urls(self) -> set[str]:
        return set(self._db_maps)

    def db_map(self, url: str) -> DatabaseMapping:
        """
        Returns a database mapping for given URL.

        Args:
            url: a database URL

        Returns:
            a database map or None if not found
        """
        url = str(url)
        return self._db_maps.get(url)

    def create_new_spine_database(self, url: str, logger: LoggerInterface, overwrite: bool = False):
        if not overwrite and not is_empty(url):
            msg = QMessageBox(qApp.activeWindow())  # pylint: disable=undefined-variable
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Database not empty")
            msg.setText(f"The URL <b>{remove_credentials_from_url(url)}</b> points to an existing database.")
            msg.setInformativeText("Do you want to overwrite it?")
            overwrite_button = msg.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            # We have custom buttons, exec() returns an opaque value.
            # Let's check the clicked button explicitly instead.
            clicked_button = msg.clickedButton()
            if clicked_button is not overwrite_button:
                return
        try:
            do_create_new_spine_database(url)
            logger.msg_success.emit(f"New Spine db successfully created at '{url}'.")
            db_map = self.db_map(url)
            self.refresh_session(db_map)
        except SpineDBAPIError as e:
            logger.msg_error.emit(f"Unable to create new Spine db at '{url}': {e}.")

    def close_session(self, url: str) -> None:
        """Pops any db map on the given url and closes its connection."""
        self._no_prompt_urls.discard(url)
        try:
            db_map = self._db_maps.pop(url)
        except KeyError:
            return
        try:
            worker = self._workers.pop(db_map)
        except KeyError:
            pass
        else:
            worker.close_db_map()  # NOTE: This calls ThreadPoolExecutor.shutdown() which waits for Futures to finish
            worker.clean_up()
        with self._lock_lock:
            with suppress(KeyError):
                del self._db_locks[db_map]
        del self._validated_values["parameter_definition"][id(db_map)]
        del self._validated_values["parameter_value"][id(db_map)]
        self.undo_stack[db_map].cleanChanged.disconnect()
        del self.undo_stack[db_map]
        del self.undo_action[db_map]
        del self.redo_action[db_map]

    def close_all_sessions(self) -> None:
        """Closes connections to all database mappings."""
        for url in list(self._db_maps):
            self.close_session(url)

    def get_db_map(
        self, url: str, logger: LoggerInterface, create: bool = False, force_upgrade_prompt: bool = False
    ) -> Optional[DatabaseMapping]:
        """Returns a DatabaseMapping instance from url if possible, None otherwise.
        If needed, asks the user to upgrade to the latest db version.
        """
        url = str(url)
        db_map = self._db_maps.get(url)
        if db_map is not None:
            return db_map
        try:
            prompt_data = DatabaseMapping.get_upgrade_db_prompt_data(url, create=create)
        except SpineDBAPIError as err:
            logger.msg_error.emit(err.msg)
            return None
        if prompt_data is not None:
            if not force_upgrade_prompt and url in self._no_prompt_urls:
                return None
            self._no_prompt_urls.add(url)
            title, text, option_to_kwargs, notes, preferred = prompt_data
            kwargs = OptionsDialog.get_answer(
                self.parent(), title, text, option_to_kwargs, notes=notes, preferred=preferred
            )
            if kwargs is None:
                return None
        else:
            kwargs = {}
        kwargs["create"] = create
        try:
            return self._do_get_db_map(url, **kwargs)
        except SpineDBAPIError as err:
            logger.msg_error.emit(err.msg)
            return None

    @busy_effect
    def _do_get_db_map(self, url: str, **kwargs) -> DatabaseMapping:
        """Returns a memorized DatabaseMapping instance from url.

        Args:
            url: database URL
            **kwargs: arguments passed to worker's get_db_map()

        Returns:
            DatabaseMapping
        """
        worker = SpineDBWorker(self, url, synchronous=self._synchronous)
        try:
            db_map = worker.get_db_map(**kwargs)
        except Exception as error:
            worker.clean_up()
            raise error
        self._workers[db_map] = worker
        with self._lock_lock:
            self._db_locks[db_map] = RLock()
        self._db_maps[url] = db_map
        self._validated_values["parameter_definition"][id(db_map)] = {}
        self._validated_values["parameter_value"][id(db_map)] = {}
        stack = self.undo_stack[db_map] = AgedUndoStack(self)
        stack.cleanChanged.connect(lambda clean: self.database_clean_changed.emit(db_map, clean))
        self.undo_action[db_map] = stack.createUndoAction(self)
        self.redo_action[db_map] = stack.createRedoAction(self)
        return db_map

    def add_db_map_listener(self, db_map: DatabaseMapping, listener: object) -> None:
        """Adds listener for given db_map."""
        self.listeners.setdefault(db_map, set()).add(listener)

    def remove_db_map_listener(self, db_map: DatabaseMapping, listener: object) -> None:
        """Removes db_map from the maps listener listens to."""
        listeners = self.listeners.get(db_map, set())
        listeners.discard(listener)
        if not listeners:
            self.listeners.pop(db_map)

    def db_map_listeners(self, db_map: DatabaseMapping) -> set[object]:
        return self.listeners.get(db_map, set())

    def register_listener(self, listener: object, *db_maps: DatabaseMapping) -> None:
        """Register given listener for all given db_map's signals."""
        for db_map in db_maps:
            self.add_db_map_listener(db_map, listener)

    def unregister_listener(
        self,
        listener: object,
        *db_maps: DatabaseMapping,
        dirty_db_maps: Optional[Iterable[DatabaseMapping]] = None,
        commit_dirty: bool = False,
        commit_msg: str = "",
    ) -> list[DatabaseMapping]:
        """Unregisters given listener from given db_map signals.
        If any of the db_maps becomes an orphan and is dirty, prompts user to commit or rollback.

        Args:
            listener: listener to unregister
            *db_maps: Database mappings from which to unregister
            dirty_db_maps: Database mappings that have uncommitted changes
            commit_dirty: True to commit dirty database mapping, False to roll back
            commit_msg: commit message

        Returns:
            All the db maps that failed to commit
        """
        failed_db_maps = []
        for db_map in db_maps:
            self.remove_db_map_listener(db_map, listener)
        if dirty_db_maps:
            if commit_dirty:
                failed_db_maps += self.commit_session(commit_msg, *dirty_db_maps)
            else:
                self.rollback_session(*dirty_db_maps)
        # If some db maps failed to commit, reinstate their listeners
        for db_map in failed_db_maps:
            self.add_db_map_listener(db_map, listener)
        for db_map in db_maps:
            if not self.db_map_listeners(db_map):
                self.close_session(db_map.db_url)
        return failed_db_maps

    def is_dirty(self, db_map: DatabaseMapping) -> bool:
        """Returns True if mapping has pending changes.

        Args:
            db_map: database mapping

        Returns:
            True if db_map has pending changes, False otherwise
        """
        return not self.undo_stack[db_map].isClean()

    def dirty(self, *db_maps: DatabaseMapping) -> list[DatabaseMapping]:
        """Filters clean mappings from given database maps.

        Args:
            *db_maps: mappings to check

        Return:
            list of DatabaseMapping: dirty  mappings
        """
        return [db_map for db_map in db_maps if self.is_dirty(db_map)]

    def dirty_and_without_editors(self, listener: object, *db_maps: DatabaseMapping) -> list[DatabaseMapping]:
        """Checks which of the given database mappings are dirty and have no editors.

        Args:
            listener: a listener object
            *db_maps: mappings to check

        Return:
            list of DatabaseMapping: mappings that are dirty and don't have editors
        """

        def has_editors(db_map):
            return any(
                hasattr(x, "is_db_map_editor") and x.is_db_map_editor()
                for x in self.db_map_listeners(db_map) - {listener}
            )

        return [db_map for db_map in self.dirty(*db_maps) if not has_editors(db_map)]

    def clean_up(self) -> None:
        while self._workers:
            _, worker = self._workers.popitem()
            worker.clean_up()
        self._parameter_type_validator.tear_down()
        self.deleteLater()

    def refresh_session(self, *db_maps: DatabaseMapping) -> None:
        reset_db_maps = set()
        for db_map in db_maps:
            if not db_map or not db_map.has_external_commits():
                continue
            try:
                worker = self._workers[db_map]
            except KeyError:
                continue
            is_dirty = not self.undo_stack[db_map].isClean()
            worker.refresh_session()
            self.undo_stack[db_map].clear()
            if is_dirty:
                self.undo_stack[db_map].resetClean()
            reset_db_maps.add(db_map)
        if reset_db_maps:
            self.receive_session_refreshed(reset_db_maps)

    def reset_session(self, *db_maps: DatabaseMapping) -> set[DatabaseMapping]:
        reset_db_maps = set()
        for db_map in db_maps:
            try:
                worker = self._workers[db_map]
            except KeyError:
                continue
            worker.reset_session()
            self.undo_stack[db_map].clear()
            reset_db_maps.add(db_map)
            self.database_reset.emit(db_map)
        return reset_db_maps

    def commit_session(
        self, commit_msg: str, *dirty_db_maps: DatabaseMapping, cookie: Optional[Any] = None
    ) -> list[DatabaseMapping]:
        """
        Commits the current session.

        Args:
            commit_msg: commit message for all database maps
            *dirty_db_maps: dirty database maps to commit
            cookie: a free form identifier which will be forwarded to ``SpineDBWorker.commit_session``
        """
        failed_db_maps = []
        for db_map in dirty_db_maps:
            success = self._do_commit_session(db_map, commit_msg, cookie)
            if not success:
                failed_db_maps.append(db_map)
                continue
        return failed_db_maps

    def _do_commit_session(self, db_map: DatabaseMapping, commit_msg: str, cookie: Optional[Any] = None) -> bool:
        """Commits session for given db.

        Args:
            db_map: db map
            commit_msg: commit message
            cookie: a cookie to include in receive_session_committed call

        Returns:
            True if operation was successful, False otherwise.
        """
        try:
            try:
                transformations, info = db_map.commit_session(commit_msg, apply_compatibility_transforms=False)
            except NothingToCommit:
                self.undo_stack[db_map].setClean()
                return True
            self.undo_stack[db_map].setClean()
            if info:
                info = "".join(f"- {x}\n" for x in info)
                QMessageBox.warning(
                    QApplication.activeWindow(),
                    "Your data needs to be refitted",
                    f"Some of the data committed to the DB at '{db_map.db_url}' "
                    "uses an old format and needs to be refitted. "
                    f"The following transformations will be applied:\n\n{info}\n"
                    "Afterwards, you can review the changes "
                    "and either commit or rollback.",
                    buttons=QMessageBox.StandardButton.Apply,
                )
                identifier = self.get_command_identifier()
                for tablename, (items_to_add, items_to_update, ids_to_remove) in transformations:
                    self.remove_items({db_map: {tablename: ids_to_remove}}, identifier=identifier)
                    self.update_items(tablename, {db_map: items_to_update}, identifier=identifier)
                    self.add_items(tablename, {db_map: items_to_add}, identifier=identifier)
            self.receive_session_committed({db_map}, cookie)
            return True
        except SpineDBAPIError as err:
            self.error_msg.emit({db_map: [err.msg]})
            return False

    def notify_session_committed(self, cookie: Optional[Any], *db_maps: DatabaseMapping) -> None:
        """Notifies manager and listeners when a commit has taken place by a third party.

        Args:
            cookie: commit cookie
            *db_maps: database maps that were committed
        """
        reset_db_maps = self.reset_session(*db_maps)
        if reset_db_maps:
            self.receive_session_committed(reset_db_maps, cookie)

    def rollback_session(self, *dirty_db_maps: DatabaseMapping) -> None:
        """Rolls back the current session.

        Args:
            *dirty_db_maps: dirty database maps to commit
        """
        for db_map in dirty_db_maps:
            self._do_rollback_session(db_map)

    def _do_rollback_session(self, db_map: DatabaseMapping) -> None:
        """Rolls back session for given db."""
        try:
            db_map.rollback_session()
        except SpineDBAPIError as err:
            self.error_msg.emit({db_map: [err.msg]})
            return
        self._validated_values["parameter_definition"][id(db_map)].clear()
        self._validated_values["parameter_value"][id(db_map)].clear()
        self.undo_stack[db_map].clear()
        self.receive_session_rolled_back({db_map})

    def entity_class_renderer(
        self, db_map: DatabaseMapping, entity_class_id: TempId, for_group: bool = False, color: Optional[QColor] = None
    ) -> Optional[QSvgRenderer]:
        """Returns an icon renderer for a given entity class.

        Args:
            db_map (DatabaseMapping): database map
            entity_class_id (int): entity class id
            for_group (bool): if True, return the group object icon instead
            color (QColor, optional): icon color

        Returns:
            QSvgRenderer: requested renderer or None if no entity class was found
        """
        entity_class = self.get_item(db_map, "entity_class", entity_class_id)
        if not entity_class:
            return None
        if for_group:
            return self.get_icon_mngr(db_map).group_renderer(entity_class)
        if color is not None:
            color_code = int(color.rgba())
            return self.get_icon_mngr(db_map).color_class_renderer(entity_class, color_code)
        return self.get_icon_mngr(db_map).class_renderer(entity_class)

    def entity_class_icon(
        self, db_map: DatabaseMapping, entity_class_id: TempId, for_group: bool = False
    ) -> Optional[QIcon]:
        """Returns an appropriate icon for a given entity class.

        Args:
            db_map: database map
            entity_class_id: entity class' id
            for_group: if True, return the group object icon instead

        Returns:
            requested icon or None if no entity class was found
        """
        renderer = self.entity_class_renderer(db_map, entity_class_id, for_group=for_group)
        return SpineDBIconManager.icon_from_renderer(renderer) if renderer is not None else None

    @staticmethod
    def get_item(db_map: DatabaseMapping, item_type: str, id_: TempId) -> Optional[PublicItem]:
        """Returns the item of the given type in the given db map that has the given id,
        or an empty dict if not found.
        """
        mapped_table = db_map.mapped_table(item_type)
        try:
            return mapped_table[id_].public_item
        except KeyError:
            return None

    def get_items(self, db_map: DatabaseMapping, item_type: str, **search_criteria) -> list[PublicItem]:
        """Returns a list of the items of the given type in the given db map."""
        with self.get_lock(db_map):
            table = db_map.mapped_table(item_type)
            return db_map.find(table, **search_criteria)

    def get_items_by_field(self, db_map: DatabaseMapping, item_type: str, field: str, value: Any) -> list[PublicItem]:
        """Returns a list of items of the given type in the given db map that have the given value
        for the given field.
        """
        with self.get_lock(db_map):
            mapped_table = db_map.mapped_table(item_type)
            return [x for x in db_map.find(mapped_table) if x.get(field) == value]

    def get_item_by_field(
        self, db_map: DatabaseMapping, item_type: str, field: str, value: Any
    ) -> Union[PublicItem, dict]:
        """Returns the first item of the given type in the given db map
        that has the given value for the given field
        Returns an empty dictionary if none found.
        """
        return next(iter(self.get_items_by_field(db_map, item_type, field, value)), {})

    @staticmethod
    def display_data_from_parsed(parsed_data: Value) -> str:
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
        return display_data

    @staticmethod
    def tool_tip_data_from_parsed(parsed_data: Value) -> Optional[str]:
        """Returns the value's database representation formatted for Qt.ItemDataRole.ToolTipRole."""
        if isinstance(parsed_data, TimeSeriesFixedResolution):
            resolution = [relativedelta_to_duration(r) for r in parsed_data.resolution]
            resolution = ", ".join(resolution)
            tool_tip_data = f"Start: {parsed_data.start}<br>resolution: [{resolution}]<br>length: {len(parsed_data)}"
        elif isinstance(parsed_data, TimeSeriesVariableResolution):
            tool_tip_data = f"Start: {parsed_data.indexes[0]}<br>resolution: variable<br>length: {len(parsed_data)}"
        elif isinstance(parsed_data, ParameterValueFormatError):
            tool_tip_data = str(parsed_data)
        else:
            tool_tip_data = None
        return plain_to_tool_tip(tool_tip_data)

    def _tool_tip_for_invalid_parameter_type(self, item: PublicItem) -> str:
        """Returns tool tip for parameter (default) values that have an invalid type."""
        if item.item_type == "parameter_value":
            definition = self.get_item(item.db_map, "parameter_definition", item["parameter_definition_id"])
        else:
            definition = item
        type_list = definition["parameter_type_list"]
        if len(type_list) == 1:
            return plain_to_tool_tip(f"Expected value's type to be <b>{type_list[0]}</b>.")
        return plain_to_tool_tip(f"Expected value's type to be one of <b>{', '.join(type_list)}</b>.")

    def _format_list_value(self, db_map: DatabaseMapping, item_type: str, value: Value, list_value_id: TempId) -> str:
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

    def get_value(
        self, db_map: DatabaseMapping, item: PublicItem, role: Union[int, Qt.ItemDataRole] = Qt.ItemDataRole.DisplayRole
    ) -> Optional[Union[int, Value]]:
        """Returns the value or default value of a parameter.

        Args:
            db_map: database mapping
            item: parameter value item, parameter definition item, or list value item
            role: data role

        Returns:
            value corresponding to role
        """
        if not item:
            return None
        if role == PARAMETER_TYPE_VALIDATION_ROLE:
            try:
                is_valid = self._validated_values[item.item_type][id(db_map)][item["id"].private_id]
            except KeyError:
                return TYPE_NOT_VALIDATED
            return VALID_TYPE if is_valid else INVALID_TYPE
        if role == Qt.ItemDataRole.ToolTipRole:
            try:
                is_valid = self._validated_values[item.item_type][id(db_map)][item["id"].private_id]
            except KeyError:
                pass
            else:
                if not is_valid:
                    return self._tool_tip_for_invalid_parameter_type(item)
        value_field, type_field = {
            "parameter_value": ("value", "type"),
            "list_value": ("value", "type"),
            "parameter_definition": ("default_value", "default_type"),
        }[item.item_type]
        complex_types = {"array": "Array", "time_series": "Time series", "time_pattern": "Time pattern", "map": "Map"}
        if role == Qt.ItemDataRole.DisplayRole and item[type_field] in complex_types:
            list_value_id = item["id"] if item.item_type == "list_value" else item["list_value_id"]
            return self._format_list_value(db_map, item.item_type, complex_types[item[type_field]], list_value_id)
        if role == Qt.ItemDataRole.EditRole:
            return join_value_and_type(item[value_field], item[type_field])
        return self._format_value(item["parsed_value"], role=role)

    def get_value_from_data(
        self, data: Optional[str], role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    ) -> Optional[Union[str, int]]:
        """Returns the value or default value of a parameter directly from data."""
        if data is None:
            return None
        parsed_value = self._parse_value(*split_value_and_type(data))
        return self._format_value(parsed_value, role=role)

    @staticmethod
    def _parse_value(db_value: bytes, type_: Optional[str] = None) -> Value:
        try:
            return from_database(db_value, type_=type_)
        except ParameterValueFormatError as error:
            return str(error)

    def _format_value(
        self, parsed_value: Value, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    ) -> Optional[Union[str, int]]:
        """Formats the given value for the given role."""
        if role == Qt.ItemDataRole.DisplayRole:
            return self.display_data_from_parsed(parsed_value)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.tool_tip_data_from_parsed(parsed_value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(parsed_value, str):
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if role == PARSED_ROLE:
            return parsed_value
        return None

    def get_value_indexes(self, db_map: DatabaseMapping, item_type: str, id_: TempId) -> nptyping.NDArray:
        """Returns the value or default value indexes of a parameter.

        Args:
            db_map: Database mapping
            item_type: either "parameter_definition" or "parameter_value"
            id_: The parameter_value or definition id
        """
        item = self.get_item(db_map, item_type, id_)
        parsed_value = item["parsed_value"]
        if isinstance(parsed_value, IndexedValue):
            return parsed_value.indexes
        return np.array([""])

    def get_value_index(
        self,
        db_map: DatabaseMapping,
        item_type: str,
        id_: TempId,
        index: MapIndex,
        role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole,
    ) -> Optional[Value]:
        """Returns the value or default value of a parameter for a given index.

        Args:
            db_map: Database mapping.
            item_type: either "parameter_definition" or "parameter_value"
            id_: The parameter_value or definition id
            index: The index to retrieve
            role: Data role.
        """
        item = self.get_item(db_map, item_type, id_)
        parsed_value = item["parsed_value"]
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

    def get_value_list_item(
        self, db_map: DatabaseMapping, id_: TempId, index: int, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    ) -> Optional[list[Optional[Union[int, Value]]]]:
        """Returns one value item of a parameter_value_list.

        Args:
            db_map: Database mapping
            id_: The parameter_value_list id
            index: The value item index
            role: Data role
        """
        try:
            return self.get_parameter_value_list(db_map, id_, role=role)[index]
        except IndexError:
            return None

    def get_parameter_value_list(
        self, db_map: DatabaseMapping, id_: TempId, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    ) -> list[Optional[Union[int, Value]]]:
        """Returns a parameter_value_list formatted for the given role.

        Args:
            db_map: Database mapping
            id_: The parameter_value_list id
            role: Data role.
        """
        with self.get_lock(db_map):
            list_value_table = db_map.mapped_table("list_value")
            return [
                self.get_value(db_map, item, role=role)
                for item in db_map.find(list_value_table, parameter_value_list_id=id_)
            ]

    def get_scenario_alternative_id_list(self, db_map: DatabaseMapping, scen_id: TempId) -> list[TempId]:
        if db_map in self._db_locks:
            with self._db_locks[db_map]:
                scen = self.get_item(db_map, "scenario", scen_id)
                return scen["alternative_id_list"] if scen else []
        return []

    def import_data(self, db_map_data: dict[DatabaseMapping, dict[str, list[tuple]]], command_text: str) -> None:
        """Imports the given data into given db maps using the dedicated import functions from spinedb_api.
        Condenses all in a single command for undo/redo.

        Args:
            db_map_data: Maps dbs to data to be passed as keyword arguments to ``get_data_for_import``
            command_text: What to call the command that condenses the operation.
        """
        db_map_error_log = {}
        for db_map, data in db_map_data.items():
            with db_map:
                errors = []
                try:
                    data_for_import = get_data_for_import(db_map, errors, **data)
                except (TypeError, ValueError) as err:
                    errors.append(str(err))
                    msg = f"Failed to import data: {err}. Please check that your data source has the right format."
                    db_map_error_log.setdefault(db_map, []).append(msg)
                    continue
                db_map_error_log.setdefault(db_map, []).extend(errors)
                identifier = self.get_command_identifier()
                for item_type, items in data_for_import:
                    if isinstance(items, tuple):
                        items, errors = items
                        db_map_error_log.setdefault(db_map, []).extend(errors)
                    self.add_update_items(item_type, {db_map: list(items)}, command_text, identifier=identifier)
        if any(db_map_error_log.values()):
            self.error_msg.emit(db_map_error_log)

    def add_ext_item_metadata(self, item_type: str, db_map_data: DBMapDictItems) -> None:
        for db_map, items in db_map_data.items():
            identifier = self.get_command_identifier()
            metadata_items = db_map.get_metadata_to_add_with_item_metadata_items(*items)
            if metadata_items:
                self.add_items("metadata", {db_map: metadata_items}, identifier=identifier)
            self.add_items(item_type, {db_map: items}, identifier=identifier)

    def update_expanded_parameter_values(self, db_map_data: DBMapDictItems) -> None:
        """Updates expanded parameter values in db.

        Args:
            db_map_data: lists of expanded items to update keyed by DatabaseMapping
        """
        for db_map, expanded_data in db_map_data.items():
            packed_data = {}
            for item in expanded_data:
                packed_data.setdefault(item["id"], {})[item["index"]] = (item["value"], item["type"])
            items = []
            value_table = db_map.mapped_table("parameter_value")
            for id_, indexed_values in packed_data.items():
                item = value_table.find_item_by_id(id_)
                parsed_value = item["parsed_value"]
                if isinstance(parsed_value, IndexedValue):
                    parsed_value = deep_copy_value(parsed_value)
                    for index, (val, typ) in indexed_values.items():
                        parsed_val = from_database(val, typ)
                        parsed_value.set_value(index, parsed_val)
                    value, value_type = to_database(parsed_value)
                else:
                    value, value_type = next(iter(indexed_values.values()))
                item = {"id": id_, "value": value, "type": value_type}
                items.append(item)
            self.undo_stack[db_map].push(UpdateItemsCommand(self, db_map, "parameter_value", items))

    def update_ext_item_metadata(self, item_type: str, db_map_data: DBMapDictItems) -> None:
        for db_map, items in db_map_data.items():
            identifier = self.get_command_identifier()
            metadata_items = db_map.get_metadata_to_add_with_item_metadata_items(*items)
            if metadata_items:
                self.add_items("metadata", {db_map: metadata_items}, identifier=identifier)
            self.update_items(item_type, {db_map: items}, identifier=identifier)

    def set_scenario_alternatives(self, db_map_data: DBMapDictItems) -> None:
        """Sets scenario alternatives in db.

        Args:
            db_map_data: lists of items to set keyed by DatabaseMapping
        """
        db_map_error_log = {}
        for db_map, data in db_map_data.items():
            identifier = self.get_command_identifier()
            items_to_add, ids_to_remove, errors = self.get_data_to_set_scenario_alternatives(db_map, data)
            if ids_to_remove:
                self.remove_items({db_map: {"scenario_alternative": ids_to_remove}}, identifier=identifier)
            if items_to_add:
                self.add_items("scenario_alternative", {db_map: items_to_add}, identifier=identifier)
            if errors:
                db_map_error_log.setdefault(db_map, []).extend([str(x) for x in errors])
        if any(db_map_error_log.values()):
            self.error_msg.emit(db_map_error_log)

    def get_data_to_set_scenario_alternatives(
        self, db_map: DatabaseMapping, scenarios: Iterable[dict]
    ) -> tuple[list[dict], set[TempId], list[str]]:
        """Returns data to add and remove, in order to set wide scenario alternatives.

        Args:
            db_map: the db_map
            scenarios: One or more wide scenario :class:`dict` objects to set.
                Each item must include the following keys:

                - "id": integer scenario id
                - "alternative_id_list": list of alternative ids for that scenario

        Returns
            scenario_alternative :class:`dict` objects to add, integer scenario_alternative ids to remove,
            and list of errors
        """

        def _is_equal(to_add, to_rm):
            return all(to_rm[k] == v for k, v in to_add.items())

        scen_alts_to_add = []
        scen_alt_ids_to_remove = {}
        errors = []
        with self._db_locks[db_map]:
            scenario_table = db_map.mapped_table("scenario")
            for scen in scenarios:
                try:
                    current_scen = scenario_table.find_item_by_id(scen["id"])
                except SpineDBAPIError:
                    error = f"no scenario matching {scen} to set alternatives for"
                    errors.append(error)
                    continue
                scenario_id = current_scen["id"]
                for k, alternative_id in enumerate(scen.get("alternative_id_list", ())):
                    item_to_add = {"scenario_id": scenario_id, "alternative_id": alternative_id, "rank": k + 1}
                    scen_alts_to_add.append(item_to_add)
                for k, alternative_name in enumerate(scen.get("alternative_name_list", ())):
                    item_to_add = {
                        "scenario_id": scenario_id,
                        "alternative_name": alternative_name,
                        "rank": k + 1,
                    }
                    scen_alts_to_add.append(item_to_add)
                scenario_alternative_table = db_map.mapped_table("scenario_alternative")
                scenario_name = current_scen["name"]
                for alternative_name in current_scen["alternative_name_list"]:
                    current_scen_alt = scenario_alternative_table.find_item(
                        {"scenario_name": scenario_name, "alternative_name": alternative_name}
                    )
                    scen_alt_ids_to_remove[current_scen_alt["id"]] = current_scen_alt
        # Remove items that are both to add and to remove
        for id_, to_rm in list(scen_alt_ids_to_remove.items()):
            i = next((i for i, to_add in enumerate(scen_alts_to_add) if _is_equal(to_add, to_rm)), None)
            if i is not None:
                del scen_alts_to_add[i]
                del scen_alt_ids_to_remove[id_]
        return scen_alts_to_add, set(scen_alt_ids_to_remove), errors

    def purge_items(self, db_map_item_types: dict[DatabaseMapping, list[str]], **kwargs) -> None:
        """Purges selected items from given database.

        Args:
            db_map_item_types: mapping from database map to list of purgable item types
            **kwargs: keyword arguments passed to ``remove_items()``
        """
        db_map_typed_data = {
            db_map: {item_type: {Asterisk} for item_type in item_types}
            for db_map, item_types in db_map_item_types.items()
        }
        self.remove_items(db_map_typed_data, **kwargs)

    def add_items(
        self, item_type: str, db_map_data: DBMapDictItems, identifier: Optional[int] = None, **kwargs
    ) -> None:
        """Pushes commands to add items to undo stack."""
        if identifier is None:
            identifier = self.get_command_identifier()
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(
                AddItemsCommand(self, db_map, item_type, data, identifier=identifier, **kwargs)
            )

    def update_items(
        self, item_type: str, db_map_data: DBMapDictItems, identifier: Optional[int] = None, **kwargs
    ) -> None:
        """Pushes commands to update items to undo stack."""
        if identifier is None:
            identifier = self.get_command_identifier()
        if item_type in ("parameter_definition", "parameter_value"):
            self._clear_validated_value_ids(item_type, db_map_data)
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(
                UpdateItemsCommand(self, db_map, item_type, data, identifier=identifier, **kwargs)
            )

    def add_update_items(
        self, item_type: str, db_map_data: DBMapDictItems, command_text: str, identifier=None, **kwargs
    ) -> None:
        """Pushes commands to add_update items to undo stack."""
        if identifier is None:
            identifier = self.get_command_identifier()
        if item_type in ("parameter_definition", "parameter_value"):
            self._clear_validated_value_ids(item_type, db_map_data)
        for db_map, data in db_map_data.items():
            self.undo_stack[db_map].push(
                AddUpdateItemsCommand(self, db_map, item_type, data, command_text, identifier=identifier, **kwargs)
            )

    def remove_items(
        self,
        db_map_typed_ids: dict[DatabaseMapping, dict[str, set[TempId]]],
        identifier: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Pushes commands to remove items to undo stack."""
        if identifier is None:
            identifier = self.get_command_identifier()
        for db_map, ids_per_type in db_map_typed_ids.items():
            for item_type, ids in ids_per_type.items():
                if item_type in ("parameter_definition", "parameter_value"):
                    if Asterisk in ids:
                        self._validated_values[item_type][id(db_map)].clear()
                    else:
                        validated_values = self._validated_values[item_type][id(db_map)]
                        for id_ in ids:
                            with suppress(KeyError):
                                del validated_values[id_.private_id]
                self.undo_stack[db_map].push(
                    RemoveItemsCommand(self, db_map, item_type, ids, identifier=identifier, **kwargs)
                )

    def get_command_identifier(self) -> int:
        id_ = self._cmd_id
        self._cmd_id += 1
        return id_

    @busy_effect
    def do_add_items(
        self, db_map: DatabaseMapping, item_type: str, data: list[dict], check: bool = True
    ) -> list[PublicItem]:
        try:
            worker = self._workers[db_map]
        except KeyError:
            # We're closing the kiosk.
            return []
        return worker.add_items(item_type, data, check)

    @busy_effect
    def do_update_items(
        self, db_map: DatabaseMapping, item_type: str, data: list[dict], check: bool = True
    ) -> list[PublicItem]:
        try:
            worker = self._workers[db_map]
        except KeyError:
            # We're closing the kiosk.
            return []
        return worker.update_items(item_type, data, check)

    @busy_effect
    def do_add_update_items(
        self, db_map: DatabaseMapping, item_type: str, data: list[dict], check: bool = True
    ) -> tuple[list[PublicItem], list[PublicItem]]:
        try:
            worker = self._workers[db_map]
        except KeyError:
            # We're closing the kiosk.
            return [], []
        return worker.add_update_items(item_type, data, check)

    @busy_effect
    def do_remove_items(
        self, db_map: DatabaseMapping, item_type: str, ids: set[TempId], check: bool = True
    ) -> list[PublicItem]:
        """Removes items from database.

        Args:
            db_map: DatabaseMapping instance
            item_type: database item type
            ids: ids to remove
            check: If False, omit integrity checks.
        """
        try:
            worker = self._workers[db_map]
        except KeyError:
            return []
        return worker.remove_items(item_type, ids, check)

    @busy_effect
    def do_restore_items(self, db_map: DatabaseMapping, item_type: str, ids: set[TempId]) -> list[PublicItem]:
        """Restores items in database.

        Args:
            db_map: DatabaseMapping instance
            item_type (str): database item type
            ids (set): ids to restore
        """
        try:
            worker = self._workers[db_map]
        except KeyError:
            return []
        return worker.restore_items(item_type, ids)

    @staticmethod
    def db_map_ids(db_map_data: Union[DBMapDictItems, DBMapPublicItems]) -> dict[DatabaseMapping, set[TempId]]:
        return {db_map: {x["id"] for x in data if x} for db_map, data in db_map_data.items()}

    @staticmethod
    def db_map_class_ids(
        db_map_data: Union[DBMapDictItems, DBMapPublicItems]
    ) -> dict[tuple[DatabaseMapping, TempId], set[TempId]]:
        d = {}
        for db_map, items in db_map_data.items():
            for item in items:
                if item:
                    d.setdefault((db_map, item["class_id"]), set()).add(item["id"])
        return d

    def find_cascading_entity_classes(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns cascading entity classes for the given dimension ids."""
        db_map_cascading_data = {}
        for db_map, dimension_ids in db_map_ids.items():
            dimension_ids = set(dimension_ids)
            with self.get_lock(db_map):
                class_table = db_map.mapped_table("entity_class")
                db_map.do_fetch_all(class_table)
                for item in class_table.values():
                    if item.is_valid() and not dimension_ids.isdisjoint(item["dimension_id_list"]):
                        db_map_cascading_data.setdefault(db_map, []).append(item.public_item)
        return db_map_cascading_data

    def find_cascading_entities(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns cascading entities for the given element ids."""
        db_map_cascading_data = {}
        for db_map, element_ids in db_map_ids.items():
            element_ids = set(element_ids)
            with self.get_lock(db_map):
                entity_table = db_map.mapped_table("entity")
                db_map.do_fetch_all(entity_table)
                for item in entity_table.values():
                    if item.is_valid() and not element_ids.isdisjoint(item["element_id_list"]):
                        db_map_cascading_data.setdefault(db_map, []).append(item.public_item)
        return db_map_cascading_data

    def find_cascading_parameter_definitions(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns cascading parameter definitions or values for the given entity_class ids."""
        db_map_cascading_data = {}
        for db_map, entity_class_ids in db_map_ids.items():
            entity_class_ids = set(entity_class_ids)
            with self.get_lock(db_map):
                definition_table = db_map.mapped_table("parameter_definition")
                db_map.do_fetch_all(definition_table)
                for item in definition_table.values():
                    if item.is_valid() and item["entity_class_id"] in entity_class_ids:
                        db_map_cascading_data.setdefault(db_map, []).append(item.public_item)
        return db_map_cascading_data

    def find_cascading_parameter_values_by_entity(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns cascading parameter values for the given entity ids."""
        db_map_cascading_data = {}
        for db_map, entity_ids in db_map_ids.items():
            entity_ids = set(entity_ids)
            with self.get_lock(db_map):
                parameter_table = db_map.mapped_table("parameter_value")
                db_map.do_fetch_all(parameter_table)
                for item in parameter_table.values():
                    if item.is_valid() and item["entity_id"] in entity_ids:
                        db_map_cascading_data.setdefault(db_map, []).append(item.public_item)
        return db_map_cascading_data

    def find_cascading_scenario_alternatives_by_scenario(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns cascading scenario alternatives for the given scenario ids."""
        db_map_cascading_data = {}
        for db_map, ids in db_map_ids.items():
            ids = set(ids)
            with self.get_lock(db_map):
                scenario_alternative_table = db_map.mapped_table("scenario_alternative")
                db_map.do_fetch_all(scenario_alternative_table)
                for item in scenario_alternative_table.values():
                    if item.is_valid() and item["scenario_id"] in ids:
                        db_map_cascading_data.setdefault(db_map, []).append(item.public_item)
        return db_map_cascading_data

    def find_groups_by_entity(
        self, db_map_ids: dict[DatabaseMapping, Iterable[TempId]]
    ) -> dict[DatabaseMapping, list[PublicItem]]:
        """Finds and returns groups for the given entity ids."""
        db_map_group_data = {}
        for db_map, entity_ids in db_map_ids.items():
            entity_ids = set(entity_ids)
            with self.get_lock(db_map):
                entity_group_table = db_map.mapped_table("entity_group")
                db_map.do_fetch_all(entity_group_table)
                for item in entity_group_table.values():
                    if item.is_valid() and item["entity_id"] in entity_ids:
                        db_map_group_data.setdefault(db_map, []).append(item.public_item)
        return db_map_group_data

    def duplicate_scenario(
        self, scen_data: dict[DatabaseMapping, dict[str, Iterable[TempId]]], dup_name: str, db_map: DatabaseMapping
    ) -> None:
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

    def duplicate_entity(
        self, orig_name: str, dup_name: str, class_name: str, db_maps: Iterable[DatabaseMapping]
    ) -> None:
        """Duplicates entity, its parameter values and related multidimensional entities.

        Args:
            orig_name: original entity's name
            dup_name: duplicate's name
            class_name: entity class name
            db_maps: database mappings where duplication should take place
        """
        dup_import_data = {}
        for db_map in db_maps:
            entity_table = db_map.mapped_table("entity")
            entity = db_map.item(entity_table, entity_class_name=class_name, name=orig_name)
            element_name_list = entity["element_name_list"]
            if element_name_list:
                first_import_entry = (class_name, dup_name, element_name_list, entity["description"])
            else:
                first_import_entry = (class_name, dup_name, entity["description"])
            dup_entity_import_data = [first_import_entry]
            for item in db_map.find(entity_table):
                element_name_list = item["element_name_list"]
                item_class_name = item["entity_class_name"]
                if orig_name in element_name_list and item_class_name != class_name:
                    index = item["dimension_name_list"].index(class_name)
                    name_list = element_name_list
                    dup_name_list = name_list[:index] + (dup_name,) + name_list[index + 1 :]
                    dup_entity_import_data.append((item_class_name, dup_name_list, item["description"]))
            dup_import_data[db_map] = {"entities": dup_entity_import_data}
            dup_value_import_data = []
            for item in db_map.find_parameter_values(entity_class_name=class_name, entity_name=orig_name):
                dup_value_import_data.append(
                    (
                        class_name,
                        dup_name,
                        item["parameter_definition_name"],
                        item["parsed_value"],
                        item["alternative_name"],
                    )
                )
            dup_import_data[db_map].update(parameter_values=dup_value_import_data)
            dup_entity_alternative_import_data = []
            for item in db_map.find_entity_alternatives(entity_class_name=class_name, entity_name=orig_name):
                dup_entity_alternative_import_data.append(
                    (class_name, dup_name, item["alternative_name"], item["active"])
                )
            dup_import_data[db_map]["entity_alternatives"] = dup_entity_alternative_import_data
        self.import_data(dup_import_data, command_text="Duplicate entity")

    @staticmethod
    def _get_data_for_export(
        db_map_item_ids: dict[DatabaseMapping, dict[str, Iterable[TempId]]]
    ) -> dict[str, list[tuple]]:
        data = {}
        for db_map, item_ids in db_map_item_ids.items():
            with db_map:
                for key, items in export_data(db_map, parse_value=load_db_value, **item_ids).items():
                    data.setdefault(key, []).extend(items)
        return data

    def export_data(
        self,
        caller: object,
        db_map_item_ids: dict[DatabaseMapping, dict[str, Iterable[TempId]]],
        file_path: str,
        file_filter: str,
    ) -> None:
        data = self._get_data_for_export(db_map_item_ids)
        if file_filter.startswith("JSON"):
            self.export_to_json(file_path, data, caller)
        elif file_filter.startswith("SQLite"):
            self.export_to_sqlite(file_path, data, caller)
        elif file_filter.startswith("Excel"):
            self.export_to_excel(file_path, data, caller)
        else:
            raise ValueError()

    def _is_url_available(self, url: Union[URL, str], logger: LoggerInterface) -> bool:
        if str(url) in self.db_urls:
            message = f"The URL <b>{url}</b> is in use. Please close all applications using it and try again."
            logger.msg_error.emit(message)
            return False
        return True

    def export_to_sqlite(self, file_path: str, data_for_export: dict[str, list[tuple]], caller: object) -> None:
        """Exports given data into SQLite file."""
        url = URL.create("sqlite", database=file_path)
        if not self._is_url_available(url, caller):
            return
        with DatabaseMapping(url, create=True) as db_map:
            import_data(db_map, **data_for_export)
            try:
                db_map.commit_session("Export data from Spine Toolbox.")
            except SpineDBAPIError as err:
                error_msg = f"[SpineDBAPIError] Unable to export file <b>{file_path}</b>: {err.msg}"
                caller.msg_error.emit(error_msg)
            else:
                caller.file_exported.emit(file_path, 1.0, True)

    @staticmethod
    def export_to_json(file_path: str, data_for_export: dict[str, list[tuple]], caller: object) -> None:
        """Exports given data into JSON file."""
        json_data = json.dumps(data_for_export, indent=4)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        caller.file_exported.emit(file_path, 1.0, False)

    @staticmethod
    def export_to_excel(file_path: str, data_for_export: dict[str, list[tuple]], caller: object) -> None:
        """Exports given data into Excel file."""
        # NOTE: We import data into an in-memory Spine db and then export that to excel.
        url = URL.create("sqlite", database="")
        with DatabaseMapping(url, create=True) as db_map:
            count, errors = import_data(db_map, **data_for_export, unparse_value=dump_db_value)
            file_name = os.path.split(file_path)[1]
            if errors:
                error_msg = (
                    f"Unable to export file <b>{file_name}</b>."
                    f"Failed to copy the data to temporary database: <p>{errors}</p>"
                )
                caller.msg_error.emit(error_msg)
                return
            if count > 0:
                db_map.commit_session("Added data for exporting.")
            if os.path.exists(file_path):
                os.remove(file_path)
            try:
                export_spine_database_to_xlsx(db_map, file_path)
            except PermissionError:
                error_msg = f"Unable to export file <b>{file_name}</b>.<br/>Close the file in Excel and try again."
                caller.msg_error.emit(error_msg)
            except OSError:
                error_msg = f"[OSError] Unable to export file <b>{file_name}</b>."
                caller.msg_error.emit(error_msg)
            else:
                caller.file_exported.emit(file_path, 1.0, False)

    def get_items_for_commit(self, db_map: DatabaseMapping, commit_id: TempId) -> dict[str, list[TempId]]:
        try:
            worker = self._workers[db_map]
        except KeyError:
            return {}
        return worker.commit_cache.get(commit_id.db_id, {})

    @Slot(list, list)
    def _parameter_value_validated(self, keys, is_valid_list):
        for key, is_valid in zip(keys, is_valid_list):
            with suppress(KeyError):
                self._validated_values[key.item_type][key.db_map_id][key.item_private_id] = is_valid

    def _clear_validated_value_ids(self, item_type: str, db_map_data: DBMapPublicItems) -> None:
        db_map_validated_values = self._validated_values[item_type]
        for db_map, data in db_map_data.items():
            validated_values = db_map_validated_values[id(db_map)]
            for item in data:
                with suppress(KeyError):
                    del validated_values[item["id"].private_id]
