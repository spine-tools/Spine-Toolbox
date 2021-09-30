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

from PySide2.QtCore import Qt, QObject, Signal, Slot
from spinedb_api import DiffDatabaseMapping, SpineDBAPIError, SpineDBVersionError
from spinetoolbox.helpers import busy_effect


class SpineDBWorker(QObject):
    """Does all the DB communication for SpineDBManager, in the non-GUI thread."""

    session_rolled_back = Signal(set)
    _get_db_map_called = Signal()
    _get_metadata_per_entity_called = Signal(object, list, dict)
    _get_metadata_per_parameter_value_called = Signal(object, list, dict)
    _close_db_map_called = Signal(object)
    _add_or_update_items_called = Signal(object, str, str, bool, str)
    _readd_items_called = Signal(object, str, str, str)
    _remove_items_called = Signal(object)
    _commit_session_called = Signal(object, str, dict, object)
    _rollback_session_called = Signal(object, dict)

    def __init__(self, db_mngr):
        super().__init__()
        thread = db_mngr.worker_thread
        self.moveToThread(thread)
        thread.finished.connect(self.deleteLater)
        self._db_mngr = db_mngr
        self._db_map = None
        self._db_map_args = None
        self._db_map_kwargs = None
        self._err = None

    def connect_signals(self):
        # pylint: disable=undefined-variable
        connection = Qt.BlockingQueuedConnection if self.thread() is not qApp.thread() else Qt.DirectConnection
        self._get_db_map_called.connect(self._get_db_map, connection)
        self._get_metadata_per_entity_called.connect(self._get_metadata_per_entity, connection)
        self._get_metadata_per_parameter_value_called.connect(self._get_metadata_per_parameter_value, connection)
        self._close_db_map_called.connect(self._close_db_map)
        self._add_or_update_items_called.connect(self._add_or_update_items)
        self._readd_items_called.connect(self._readd_items)
        self._remove_items_called.connect(self._remove_items)
        self._commit_session_called.connect(self._commit_session)
        self._rollback_session_called.connect(self._rollback_session)

    def get_db_map(self, *args, **kwargs):
        self._db_map = None
        self._db_map_args = args
        self._db_map_kwargs = kwargs
        self._err = None
        self._get_db_map_called.emit()
        return self._db_map, self._err

    @Slot()
    def _get_db_map(self):
        try:
            self._db_map = DiffDatabaseMapping(*self._db_map_args, **self._db_map_kwargs)
        except (SpineDBVersionError, SpineDBAPIError) as err:
            self._err = err

    def close_db_map(self, db_map):
        self._close_db_map_called.emit(db_map)

    @Slot(object)
    def _close_db_map(self, db_map):  # pylint: disable=no-self-use
        if not db_map.connection.closed:
            db_map.connection.close()

    def get_metadata_per_entity(self, db_map, entity_ids):
        d = {}
        self._get_metadata_per_entity_called.emit(db_map, entity_ids, d)
        return d

    # pylint: disable=no-self-use
    @Slot(object, list, dict)
    def _get_metadata_per_entity(self, db_map, entity_ids, d):
        sq = db_map.ext_entity_metadata_sq
        for x in db_map.query(sq).filter(db_map.in_(sq.c.entity_id, entity_ids)):
            d.setdefault(x.entity_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)

    def get_metadata_per_parameter_value(self, db_map, parameter_value_ids):
        d = {}
        self._get_metadata_per_parameter_value_called.emit(db_map, parameter_value_ids, d)
        return d

    # pylint: disable=no-self-use
    @Slot(object, list, dict)
    def _get_metadata_per_parameter_value(self, db_map, parameter_value_ids, d):
        sq = db_map.ext_parameter_value_metadata_sq
        for x in db_map.query(sq).filter(db_map.in_(sq.c.parameter_value_id, parameter_value_ids)):
            param_val_name = (x.entity_name, x.parameter_name, x.alternative_name)
            d.setdefault(param_val_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)

    def add_or_update_items(self, db_map_data, method_name, item_type, signal_name, readd=False, check=True):
        """Adds or updates items in db.

        Args:
            db_map_data (dict): lists of items to add or update keyed by DiffDatabaseMapping
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            item_type (str): item type
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
            readd (bool): Whether or not to readd items
            check (bool): Whether or not to check integrity
        """
        if readd:
            self._readd_items_called.emit(db_map_data, method_name, item_type, signal_name)
        else:
            self._add_or_update_items_called.emit(db_map_data, method_name, item_type, check, signal_name)

    @Slot(object, str, str, bool, str)
    def _add_or_update_items(self, db_map_data, method_name, item_type, check, signal_name):
        self._do_add_or_update_items(db_map_data, method_name, item_type, check, signal_name)

    @busy_effect
    def _do_add_or_update_items(self, db_map_data, method_name, item_type, check, signal_name):
        signal = getattr(self._db_mngr, signal_name)
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            cache = self._db_mngr.get_db_map_cache(db_map, {item_type}, include_ancestors=True)
            items, errors = getattr(db_map, method_name)(*items, check=check, return_items=True, cache=cache)
            if errors:
                db_map_error_log[db_map] = errors
            items = [self._db_mngr.db_to_cache(db_map, item_type, item) for item in items]
            signal.emit({db_map: items})
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)

    @Slot(object, str, str, str)
    def _readd_items(self, db_map_data, method_name, item_type, signal_name):
        self._do_readd_items(db_map_data, method_name, item_type, signal_name)

    @busy_effect
    def _do_readd_items(self, db_map_data, method_name, item_type, signal_name):
        signal = getattr(self._db_mngr, signal_name)
        for db_map, items in db_map_data.items():
            getattr(db_map, method_name)(*items, readd=True)
            visible = []
            hidden = []
            for item in items:
                item = self._db_mngr.db_to_cache(db_map, item_type, item)
                if item.pop("visible", True):
                    visible.append(item)
                else:
                    hidden.append(item)
            self._db_mngr.cache_items_for_fetching(db_map, item_type, hidden)
            signal.emit({db_map: visible})

    def remove_items(self, db_map_typed_ids):
        """Removes items from database.

        Args:
            db_map_typed_ids (dict): lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
        """
        self._remove_items_called.emit(db_map_typed_ids)

    @Slot(object)
    def _remove_items(self, db_map_typed_ids):
        self._do_remove_items(db_map_typed_ids)

    @busy_effect
    def _do_remove_items(self, db_map_typed_ids):
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
        """Initiates commit session action for given database maps in the worker thread.

        Args:
            dirty_db_maps (Iterable of DiffDatabaseMapping): database mapping to commit
            commit_msg (str): commit message
            cookie (Any): a cookie to include in session_committed signal
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stacks = {db_map: self._db_mngr.undo_stack[db_map] for db_map in dirty_db_maps}
        self._commit_session_called.emit(dirty_db_maps, commit_msg, undo_stacks, cookie)

    @Slot(object, str, dict, object)
    def _commit_session(self, dirty_db_maps, commit_msg, undo_stacks, cookie=None):
        """Commits session for given database maps.

        Args:
            dirty_db_maps (Iterable of DiffDatabaseMapping): database mapping to commit
            commit_msg (str): commit message
            undo_stacks (dict of AgedUndoStack): undo stacks that outlive the DB manager
            cookie (Any): a cookie to include in session_committed signal
        """
        db_map_error_log = {}
        committed_db_maps = set()
        for db_map in dirty_db_maps:
            try:
                db_map.commit_session(commit_msg)
                committed_db_maps.add(db_map)
                undo_stacks[db_map].setClean()
            except SpineDBAPIError as e:
                db_map_error_log[db_map] = e.msg
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        if committed_db_maps:
            self._db_mngr.session_committed.emit(committed_db_maps, cookie)

    def rollback_session(self, dirty_db_maps):
        """Initiates rollback session action for given database maps in the worker thread.

        Args:
            dirty_db_maps (Iterable of DiffDatabaseMapping): database mapping to roll back
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stacks = {db_map: self._db_mngr.undo_stack[db_map] for db_map in dirty_db_maps}
        self._rollback_session_called.emit(dirty_db_maps, undo_stacks)

    @Slot(object, dict)
    def _rollback_session(self, dirty_db_maps, undo_stacks):
        """Rolls back session for given database maps.

        Args:
            dirty_db_maps (Iterable of DiffDatabaseMapping): database mapping to roll back
            undo_stacks (dict of AgedUndoStack): undo stacks that outlive the DB manager
        """
        db_map_error_log = {}
        rolled_db_maps = set()
        for db_map in dirty_db_maps:
            try:
                db_map.rollback_session()
                rolled_db_maps.add(db_map)
                undo_stacks[db_map].clear()
            except SpineDBAPIError as e:
                db_map_error_log[db_map] = e.msg
        if any(db_map_error_log.values()):
            self._db_mngr.error_msg.emit(db_map_error_log)
        if rolled_db_maps:
            self.session_rolled_back.emit(rolled_db_maps)
