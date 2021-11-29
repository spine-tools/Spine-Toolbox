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
SpineDBFetcher class.

:authors: M. Marin (KTH)
:date:   13.3.2020
"""
import itertools
from PySide2.QtCore import Signal, Slot, QObject, QTimer
from spinetoolbox.helpers import busy_effect, signal_waiter


class SpineDBFetcher(QObject):
    """Fetches content from a Spine database."""

    _fetch_more_requested = Signal(object)
    _chunk_available = Signal(object, list)
    _init_query_requested = Signal(object)
    _can_fetch_more_finished = Signal()
    _fetch_all_requested = Signal(set)
    _fetch_all_finished = Signal()

    def __init__(self, db_mngr, db_map):
        """Initializes the fetcher object.

        Args:
            db_mngr (SpineDBManager): used for fetching
            db_map (DiffDatabaseMapping): The db to fetch
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._db_map = db_map
        self._parents = {}
        self._queries = {}
        self._query_has_elements_by_key = {}
        self._query_keys = {}
        self._iterators = {}
        self._busy_parents = set()
        self._fetched_parents = set()
        self._fetched_item_types = set()
        self._forwarder = _ChunkForwarder(self)
        self.commit_cache = {}
        self.moveToThread(db_mngr.worker_thread)
        self._fetch_more_requested.connect(self._fetch_more)
        self._init_query_requested.connect(self._init_query)
        self._fetch_all_requested.connect(self._fetch_all)
        self._chunk_available.connect(self._forwarder.forward_chunk)

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

    @Slot(object)
    def _init_query(self, parent):
        """Initializes query for parent."""
        self._do_init_query(parent)

    @busy_effect
    def _do_init_query(self, parent):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            return
        try:
            query = self._get_query(parent)
            if not self._query_has_elements(query):
                self._fetched_parents.add(parent)
                parent.restart_fetching()
        finally:
            lock.unlock()

    def _get_query(self, parent):
        """Creates a query for parent. Stores both the query and the count."""
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

    @Slot(object)
    def _fetch_more(self, parent):
        self._do_fetch_more(parent)

    @busy_effect
    def _do_fetch_more(self, parent):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            return
        try:
            query = self._get_query(parent)
            iterator = self._get_iterator(parent, query)
            chunk = next(iterator, [])
            self._chunk_available.emit(parent, chunk)
        finally:
            lock.unlock()

    def receive_chunk(self, parent, chunk):
        if chunk:
            signal = self._db_mngr.added_signals[parent.fetch_item_type]
            signal.emit({self._db_map: chunk})
        else:
            self._fetched_parents.add(parent)
        QTimer.singleShot(0, lambda parent=parent: self._busy_parents.discard(parent))

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
            qApp.processEvents()  # pylint: disable=undefined-variable
            return
        with signal_waiter(self._fetch_all_finished) as waiter:
            self._fetch_all_requested.emit(item_types)
            waiter.wait()

    @Slot(set)
    def _fetch_all(self, item_types):
        self._do_fetch_all(item_types)

    @busy_effect
    def _do_fetch_all(self, item_types):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            self._fetch_all_finished.emit()
            return
        try:
            for item_type in item_types:
                query, _ = self._make_query_for_item_type(item_type)
                for chunk in _make_iterator(query):
                    self._populate_commit_cache(item_type, chunk)
                    self._db_mngr.cache_items(item_type, {self._db_map: chunk})
                self._fetched_item_types.add(item_type)
            self._fetch_all_finished.emit()
        finally:
            lock.unlock()

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        if item_type == "entity_group":  # FIXME
            return
        for item in items:
            self.commit_cache.setdefault(item["commit_id"], {}).setdefault(item_type, list()).append(item["id"])


class _ChunkForwarder(QObject):
    """Forwards query results from DB thread to GUI thread. This prevents an infinite fetching loop."""

    def __init__(self, fetcher):
        super().__init__()
        self._fetcher = fetcher

    def forward_chunk(self, parent, chunk):
        self._fetcher.receive_chunk(parent, chunk)


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
