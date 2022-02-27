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

import threading
import queue
import itertools
from enum import auto, Enum, unique
from PySide2.QtCore import QObject, Signal, QEvent, QCoreApplication
from spinedb_api import DiffDatabaseMapping, SpineDBAPIError, SpineDBVersionError
from spinetoolbox.helpers import busy_effect

_FETCH = QEvent.Type(QEvent.registerEventType())
_FETCH_COMPLETE = QEvent.Type(QEvent.registerEventType())
_ADD_OR_UPDATE_ITEMS = QEvent.Type(QEvent.registerEventType())
_READD_ITEMS = QEvent.Type(QEvent.registerEventType())
_REMOVE_ITEMS = QEvent.Type(QEvent.registerEventType())
_COMMIT_SESSION = QEvent.Type(QEvent.registerEventType())
_ROLLBACK_SESSION = QEvent.Type(QEvent.registerEventType())


class _FetchEvent(QEvent):
    def __init__(self, parent, chunk):
        super().__init__(_FETCH)
        self.parent = parent
        self.chunk = chunk


class _FetchCompleteEvent(QEvent):
    def __init__(self, parent):
        super().__init__(_FETCH_COMPLETE)
        self.parent = parent


class _AddOrUpdateItemsEvent(QEvent):
    def __init__(self, item_type, items, errors, signal_name):
        super().__init__(_ADD_OR_UPDATE_ITEMS)
        self.item_type = item_type
        self.items = items
        self.errors = errors
        self.signal_name = signal_name


class _ReaddItemsEvent(QEvent):
    def __init__(self, item_type, items, signal_name):
        super().__init__(_READD_ITEMS)
        self.item_type = item_type
        self.items = items
        self.signal_name = signal_name


class _RemoveItemsEvent(QEvent):
    def __init__(self, ids_per_type, errors):
        super().__init__(_REMOVE_ITEMS)
        self.ids_per_type = ids_per_type
        self.errors = errors


class _CommitSessionEvent(QEvent):
    def __init__(self, errors, undo_stack, cookie):
        super().__init__(_COMMIT_SESSION)
        self.errors = errors
        self.undo_stack = undo_stack
        self.cookie = cookie


class _RollbackSessionEvent(QEvent):
    def __init__(self, errors, undo_stack):
        super().__init__(_ROLLBACK_SESSION)
        self.errors = errors
        self.undo_stack = undo_stack


class _Signal:
    def __init__(self, request, queue_):
        self._request = request
        self._queue = queue_

    def emit(self, *args, **kwargs):
        self._queue.put((self._request, args, kwargs))


class SpineDBWorker(QObject):
    """Does all the DB communication for SpineDBManager, in the non-GUI thread."""

    session_rolled_back = Signal(set)

    @unique
    class _Request(Enum):
        GET_DB_MAP = auto()
        INIT_QUERY = auto()
        FETCH_MORE = auto()
        FETCH_ALL = auto()
        CLOSE_DB_MAP = auto()
        ADD_OR_UPDATE_ITEMS = auto()
        READD_ITEMS = auto()
        REMOVE_ITEMS = auto()
        COMMIT_SESSION = auto()
        ROLLBACK_SESSION = auto()
        GET_METADATA_PER_ENTITY = auto()
        GET_METADATA_PER_PARAMETER_VALUE = auto()
        QUIT = auto()

    def __init__(self, db_mngr, db_url):
        super().__init__()
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._parents = {}
        self._queries = {}
        self._query_has_elements_by_key = {}
        self._query_keys = {}
        self._iterators = {}
        self._busy_parents = set()
        self._fetched_parents = set()
        self._fetched_item_types = set()
        self.commit_cache = {}
        self._queue = queue.Queue()
        self._get_db_map_called = _Signal(self._Request.GET_DB_MAP, self._queue)
        self._init_query_requested = _Signal(self._Request.INIT_QUERY, self._queue)
        self._fetch_more_requested = _Signal(self._Request.FETCH_MORE, self._queue)
        self._fetch_all_requested = _Signal(self._Request.FETCH_ALL, self._queue)
        self._close_db_map_called = _Signal(self._Request.CLOSE_DB_MAP, self._queue)
        self._add_or_update_items_called = _Signal(self._Request.ADD_OR_UPDATE_ITEMS, self._queue)
        self._readd_items_called = _Signal(self._Request.READD_ITEMS, self._queue)
        self._remove_items_called = _Signal(self._Request.REMOVE_ITEMS, self._queue)
        self._commit_session_called = _Signal(self._Request.COMMIT_SESSION, self._queue)
        self._rollback_session_called = _Signal(self._Request.ROLLBACK_SESSION, self._queue)
        self._get_metadata_per_entity_called = _Signal(self._Request.GET_METADATA_PER_ENTITY, self._queue)
        self._get_metadata_per_parameter_value_called = _Signal(
            self._Request.GET_METADATA_PER_PARAMETER_VALUE, self._queue
        )
        self._finished = _Signal(self._Request.QUIT, self._queue)
        self._thread = threading.Thread(target=self._target)
        self._thread.start()

    def deleteLater(self):
        super().deleteLater()
        self._finished.emit()
        self._thread.join()

    def _target(self):
        while True:
            request, args, kwargs = self._queue.get()
            if request == self._Request.QUIT:
                break
            {
                self._Request.GET_DB_MAP: self._get_db_map,
                self._Request.INIT_QUERY: self._init_query,
                self._Request.FETCH_MORE: self._fetch_more,
                self._Request.FETCH_ALL: self._fetch_all,
                self._Request.CLOSE_DB_MAP: self._close_db_map,
                self._Request.ADD_OR_UPDATE_ITEMS: self._add_or_update_items,
                self._Request.READD_ITEMS: self._readd_items,
                self._Request.REMOVE_ITEMS: self._remove_items,
                self._Request.COMMIT_SESSION: self._commit_session,
                self._Request.ROLLBACK_SESSION: self._rollback_session,
                self._Request.GET_METADATA_PER_ENTITY: self._get_metadata_per_entity,
                self._Request.GET_METADATA_PER_PARAMETER_VALUE: self._get_metadata_per_parameter_value,
            }[request](*args, **kwargs)

    def event(self, ev):
        if ev.type() == _FETCH:
            self._receive_fetch(ev)
            return True
        if ev.type() == _FETCH_COMPLETE:
            ev.parent.restart_fetching()
            return True
        if ev.type() == _ADD_OR_UPDATE_ITEMS:
            self._receive_add_or_update_items(ev)
            return True
        if ev.type() == _READD_ITEMS:
            self._receive_readd_items(ev)
            return True
        if ev.type() == _REMOVE_ITEMS:
            self._receive_remove_items(ev)
            return True
        if ev.type() == _COMMIT_SESSION:
            self._receive_commit_session(ev)
            return True
        if ev.type() == _ROLLBACK_SESSION:
            self._receive_rollback_session(ev)
            return True
        return super().event(ev)

    def get_db_map(self, *args, **kwargs):
        out_queue = queue.Queue()
        self._get_db_map_called.emit(out_queue, *args, **kwargs)
        err = out_queue.get()
        return self._db_map, err

    def _get_db_map(self, out_queue, *args, **kwargs):
        try:
            self._db_map = DiffDatabaseMapping(self._db_url, *args, **kwargs)
            out_queue.put(None)
        except (SpineDBVersionError, SpineDBAPIError) as err:
            out_queue.put(err)

    def reset_queries(self, item_type):
        affected_parents = [parent for parent in self._queries if parent.fetch_item_type == item_type]
        for parent in affected_parents:
            self._iterators.pop(parent, None)
            query = self._queries.pop(parent)
            key = self._query_keys.pop(query)
            self._query_has_elements_by_key.pop(key, None)
            parent.restart_fetching()

    def can_fetch_more(self, parent):
        if parent in self._fetched_parents | self._busy_parents:
            return False
        query = self._queries.get(parent)
        if query is None:
            # Query not made yet. Init query and return True
            self._init_query_requested.emit(parent)
            return True
        return self._query_has_elements(query)

    @busy_effect
    def _init_query(self, parent):
        """Initializes query for parent."""
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            return
        try:
            query = self._get_query(parent)
            if not self._query_has_elements(query):
                self._fetched_parents.add(parent)
                QCoreApplication.postEvent(self, _FetchCompleteEvent(parent))
        finally:
            lock.unlock()

    def _get_query(self, parent):
        """Creates a query for parent. Stores both the query and whether or not it has elements."""
        if parent not in self._queries:
            query = self._make_query_for_parent(parent)
            key = self._make_query_key(query)
            if key not in self._query_has_elements_by_key:
                self._query_has_elements_by_key[key] = bool(query.first())
            self._queries[parent] = query
        return self._queries[parent]

    def _query_has_elements(self, query):
        return self._query_has_elements_by_key[self._make_query_key(query)]

    def _make_query_key(self, query):
        if query not in self._query_keys:
            self._query_keys[query] = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        return self._query_keys[query]

    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (object)
        """
        self._busy_parents.add(parent)
        self._fetch_more_requested.emit(parent)

    @busy_effect
    def _fetch_more(self, parent):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            return
        try:
            query = self._get_query(parent)
            iterator = self._get_iterator(parent, query)
            chunk = next(iterator, [])
            QCoreApplication.postEvent(self, _FetchEvent(parent, chunk))
        finally:
            lock.unlock()

    def _receive_fetch(self, ev):
        if ev.chunk:
            signal = self._db_mngr.added_signals[ev.parent.fetch_item_type]
            signal.emit({self._db_map: ev.chunk})
        else:
            self._fetched_parents.add(ev.parent)
        self._busy_parents.discard(ev.parent)
        # TODO: Do we need this? QTimer.singleShot(0, lambda parent=parent: self._busy_parents.discard(parent))

    def fetch_all(self, item_types=None, only_descendants=False, include_ancestors=False):
        if item_types is None:
            item_types = set(self._db_mngr.added_signals)
        if only_descendants:
            item_types = {
                descendant
                for item_type in item_types
                for descendant in self._db_map.descendant_tablenames.get(item_type, ())
            }
        if include_ancestors:
            item_types |= {
                ancestor for item_type in item_types for ancestor in self._db_map.ancestor_tablenames.get(item_type, ())
            }
        item_types -= self._fetched_item_types
        if not item_types:
            # FIXME: Needed? QCoreApplication.processEvents()
            return
        ev = threading.Event()
        self._fetch_all_requested.emit(ev, item_types)
        while True:
            if ev.wait(timeout=0):
                break
            QCoreApplication.processEvents()

    @busy_effect
    def _fetch_all(self, ev, item_types):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            ev.set()
            return
        try:
            for item_type in item_types:
                query, _ = self._make_query_for_item_type(item_type)
                for chunk in _make_iterator(query):
                    self._populate_commit_cache(item_type, chunk)
                    self._db_mngr.cache_items(item_type, {self._db_map: chunk})
                self._fetched_item_types.add(item_type)
            ev.set()
        finally:
            lock.unlock()

    def _make_query_for_parent(self, parent):
        """Makes a database query for given item type.

        Args:
            parent (object): the object that requests the fetching

        Returns:
            Query: database query
        """
        query, subquery = self._make_query_for_item_type(parent.fetch_item_type)
        return parent.filter_query(query, subquery, self._db_map)

    def _make_query_for_item_type(self, item_type):
        subquery_name = self._db_map.cache_sqs[item_type]
        subquery = getattr(self._db_map, subquery_name)
        query = self._db_map.query(subquery)
        return query, subquery

    def _get_iterator(self, parent, query):
        if parent not in self._iterators:
            self._iterators[parent] = _make_iterator(query)
        return self._iterators[parent]

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        if item_type == "entity_group":  # FIXME
            return
        for item in items:
            self.commit_cache.setdefault(item["commit_id"], {}).setdefault(item_type, list()).append(item["id"])

    def close_db_map(self):
        self._close_db_map_called.emit()

    def _close_db_map(self):
        if not self._db_map.connection.closed:
            self._db_map.connection.close()

    def get_metadata_per_entity(self, entity_ids):
        out_queue = queue.Queue()
        self._get_metadata_per_entity_called.emit(out_queue, entity_ids)
        return out_queue.get()

    def _get_metadata_per_entity(self, out_queue, entity_ids):
        d = {}
        sq = self._db_map.ext_entity_metadata_sq
        for x in self._db_map.query(sq).filter(self._db_map.in_(sq.c.entity_id, entity_ids)):
            d.setdefault(x.entity_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)
        out_queue.put(d)

    def get_metadata_per_parameter_value(self, parameter_value_ids):
        out_queue = queue.Queue()
        self._get_metadata_per_parameter_value_called.emit(out_queue, parameter_value_ids)
        return out_queue.get()

    def _get_metadata_per_parameter_value(self, out_queue, parameter_value_ids):
        d = {}
        sq = self._db_map.ext_parameter_value_metadata_sq
        for x in self._db_map.query(sq).filter(self._db_map.in_(sq.c.parameter_value_id, parameter_value_ids)):
            param_val_name = (x.entity_name, x.parameter_name, x.alternative_name)
            d.setdefault(param_val_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)
        out_queue.put(d)

    def add_or_update_items(self, items, method_name, item_type, signal_name, check, cache):
        """Adds or updates items in db.

        Args:
            items (dict): lists of items to add or update
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            item_type (str): item type
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
            check (bool): Whether or not to check integrity
            cache (dict): Cache
        """
        self._add_or_update_items_called.emit(items, method_name, item_type, signal_name, check, cache)

    @busy_effect
    def _add_or_update_items(self, items, method_name, item_type, signal_name, check, cache):
        items, errors = getattr(self._db_map, method_name)(*items, check=check, return_items=True, cache=cache)
        QCoreApplication.postEvent(self, _AddOrUpdateItemsEvent(item_type, items, errors, signal_name))

    def _receive_add_or_update_items(self, ev):
        signal = getattr(self._db_mngr, ev.signal_name)
        items = [self._db_mngr.db_to_cache(self._db_map, ev.item_type, item) for item in ev.items]
        signal.emit({self._db_map: items})
        if ev.errors:
            self._db_mngr.error_msg.emit({self._db_map: ev.errors})

    def readd_items(self, items, method_name, item_type, signal_name):
        """Adds or updates items in db.

        Args:
            items (dict): lists of items to add or update
            method_name (str): attribute of DiffDatabaseMapping to call for performing the operation
            item_type (str): item type
            signal_name (str) : signal attribute of SpineDBManager to emit if successful
        """
        self._readd_items_called.emit(items, method_name, item_type, signal_name)

    @busy_effect
    def _readd_items(self, items, method_name, item_type, signal_name):
        getattr(self._db_map, method_name)(*items, readd=True)
        QCoreApplication.postEvent(self, _ReaddItemsEvent(item_type, items, signal_name))

    def _receive_readd_items(self, ev):
        items = [self._db_mngr.db_to_cache(self._db_map, ev.item_type, item) for item in ev.items]
        signal = getattr(self._db_mngr, ev.signal_name)
        signal.emit({self._db_map: items})

    def remove_items(self, ids_per_type):
        """Removes items from database.

        Args:
            ids_per_type (dict): lists of items to remove keyed by item type (str)
        """
        self._remove_items_called.emit(ids_per_type)

    @busy_effect
    def _remove_items(self, ids_per_type):
        try:
            self._db_map.remove_items(**ids_per_type)
            errors = []
        except SpineDBAPIError as err:
            errors = [err]
        QCoreApplication.postEvent(self, _RemoveItemsEvent(ids_per_type, errors))

    def _receive_remove_items(self, ev):
        if ev.errors:
            self._db_mngr.error_msg.emit({self._db_map: ev.errors})
        self._db_mngr.items_removed.emit({self._db_map: ev.ids_per_type})

    def commit_session(self, commit_msg, cookie=None):
        """Initiates commit session.

        Args:
            commit_msg (str): commit message
            cookie (Any): a cookie to include in session_committed signal
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._commit_session_called.emit(commit_msg, undo_stack, cookie)

    def _commit_session(self, commit_msg, undo_stack, cookie=None):
        """Commits session for given database maps.

        Args:
            commit_msg (str): commit message
            undo_stack (AgedUndoStack): undo stack that outlive the DB manager
            cookie (Any): a cookie to include in session_committed signal
        """
        try:
            self._db_map.commit_session(commit_msg)
            errors = []
        except SpineDBAPIError as e:
            errors = [e.msg]
        QCoreApplication.postEvent(self, _CommitSessionEvent(errors, undo_stack, cookie))

    def _receive_commit_session(self, ev):
        ev.undo_stack.setClean()
        if ev.errors:
            self._db_mngr.error_msg.emit({self._db_map: ev.errors})
        else:
            self._db_mngr.session_committed.emit({self._db_map}, ev.cookie)

    def rollback_session(self):
        """Initiates rollback session action for given database maps in the worker thread.

        Args:
            dirty_db_maps (Iterable of DiffDatabaseMapping): database mapping to roll back
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._rollback_session_called.emit(undo_stack)

    def _rollback_session(self, undo_stack):
        """Rolls back session for given database maps.

        Args:
            undo_stack (AgedUndoStack): undo stack that outlive the DB manager
        """
        try:
            self._db_map.rollback_session()
            errors = []
        except SpineDBAPIError as e:
            errors = [e.msg]
        QCoreApplication.postEvent(self, _RollbackSessionEvent(errors, undo_stack))

    def _receive_rollback_session(self, ev):
        ev.undo_stack.setClean()
        if ev.errors:
            self._db_mngr.error_msg.emit({self._db_map: ev.errors})
        else:
            self._db_mngr.session_rolled_back.emit({self._db_map})


def _make_iterator(query, query_chunk_size=1000, iter_chunk_size=1000):
    """Runs the given query and yields results by chunks of given size.

    Args:
        query (Query): the query

    Yields:
        list: chunk of items
    """
    it = (x._asdict() for x in query.yield_per(query_chunk_size).enable_eagerloads(False))
    while True:
        chunk = list(itertools.islice(it, iter_chunk_size))
        yield chunk
        if not chunk:
            break
