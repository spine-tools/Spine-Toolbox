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
from collections import OrderedDict
from PySide2.QtCore import Signal, Slot, QObject
from spinetoolbox.helpers import busy_effect, signal_waiter, CacheItem


class SpineDBFetcher(QObject):
    """Fetches content from a Spine database."""

    _fetch_more_requested = Signal(str, object)
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
        self._iterators = {
            item_type: self._get_db_items(item_type)
            for item_type in (
                "object_class",
                "relationship_class",
                "parameter_definition",
                "object",
                "relationship",
                "entity_group",
                "parameter_value",
                "parameter_value_list",
                "alternative",
                "scenario",
                "scenario_alternative",
                "feature",
                "tool",
                "tool_feature",
                "tool_feature_method",
            )
        }
        self.cache = {}
        self._fetched = {item_type: False for item_type in self._iterators}
        self._can_fetch_more_cache = {}
        self.moveToThread(db_mngr.worker_thread)
        self._fetch_more_requested.connect(self._fetch_more)
        self._fetch_all_requested.connect(self._fetch_all)
        self._parents = {}

    def cache_items(self, item_type, items):
        # NOTE: OrderedDict is so we can call `reversed()` in Python 3.7
        self.cache.setdefault(item_type, OrderedDict()).update({x["id"]: CacheItem(**x) for x in items})

    def get_item(self, item_type, id_):
        return self.cache.get(item_type, {}).get(id_, {})

    def _make_fetch_successful(self, parent):
        try:
            fetch_successful = parent.fetch_successful
        except AttributeError:
            return lambda _: True
        return lambda item: fetch_successful(self._db_map, item)

    def _can_fetch_more_from_cache(self, item_type, parent=None):
        fetch_successful = self._make_fetch_successful(parent)
        items = self.cache.get(item_type, OrderedDict())
        key = (next(reversed(items), None), len(items))
        try:
            fetch_id = parent.fetch_id()
        except AttributeError:
            fetch_id = parent
        cache_key, cache_result = self._can_fetch_more_cache.get((item_type, fetch_id), (None, None))
        if key == cache_key:
            return cache_result
        try:
            result = any(fetch_successful(x) for x in items.values())
        except RuntimeError:
            # OrderedDict mutated during iteration
            # The DB thread added some stuff to the cache while we were looking at it,
            # which means we need to start over
            return self.can_fetch_more(item_type, parent=parent)
        self._can_fetch_more_cache[item_type, fetch_id] = (key, result)
        return result

    def can_fetch_more(self, item_type, parent=None):
        if self._can_fetch_more_from_cache(item_type, parent=parent):
            return True
        return not self._fetched[item_type]

    def _fetch_more_from_cache(self, item_type, parent=None, iter_chunk_size=1000):
        fetch_successful = self._make_fetch_successful(parent)
        items = self.cache.get(item_type, {})
        args = [iter(items)] * iter_chunk_size
        for keys in itertools.zip_longest(*args):
            keys = set(keys) - {None}  # Remove fillvalues
            chunk = [items[k] for k in keys]
            if any(fetch_successful(x) for x in chunk):
                for k in keys:
                    del items[k]
                signal = self._db_mngr.added_signals[item_type]
                signal.emit({self._db_map: chunk})
                return True
        return False

    @busy_effect
    def fetch_more(self, item_type, parent=None, iter_chunk_size=1000):
        """Fetches items from the database.

        Args:
            item_type (str): the type of items to fetch, e.g. "object_class"
        """
        if self._fetch_more_from_cache(item_type, parent=parent, iter_chunk_size=iter_chunk_size):
            return
        # Nothing found in cache.
        # Add parent to the list of parents to refetch in case something is added to the cache
        self._parents.setdefault(item_type, []).append(parent)
        self._fetch_more_requested.emit(item_type, parent)

    @Slot(str, object)
    def _fetch_more(self, item_type, parent):
        self._do_fetch_more(item_type, parent)

    @busy_effect
    def _do_fetch_more(self, item_type, parent):
        iterator = self._iterators.get(item_type)
        if iterator is None:
            return
        fetch_successful = self._make_fetch_successful(parent)
        while True:
            chunk = next(iterator, [])
            if not chunk:
                self._fetched[item_type] = True
                break
            if any(fetch_successful(x) for x in chunk):
                signal = self._db_mngr.added_signals[item_type]
                signal.emit({self._db_map: chunk})
                return
            self.cache_items(item_type, chunk)
            self._refetch_parents(item_type)
        try:
            parent.fully_fetched.emit()
        except AttributeError:
            pass

    def _refetch_parents(self, item_type):
        """Refetches parents that might have missed some content from the cache.
        Called after adding items to the cache from the DB thread.

        Args:
            item_type (str)
        """
        for parent in self._parents.pop(item_type, []):
            if self._can_fetch_more_from_cache(item_type, parent=parent):
                self._fetch_more_from_cache(item_type, parent=parent)

    def fetch_all(self, item_types=None, only_descendants=False, include_ancestors=False):
        if item_types is None:
            item_types = set(self._iterators)
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
        item_types = {item_type for item_type in item_types if self.can_fetch_more(item_type)}
        if not item_types:
            return
        with signal_waiter(self._fetch_all_finished) as waiter:
            self._fetch_all_requested.emit(item_types)
            waiter.wait()

    @Slot(set)
    def _fetch_all(self, item_types):
        self._do_fetch_all(item_types)

    @busy_effect
    def _do_fetch_all(self, item_types):
        class _Parent:
            def fetch_successful(self, *args):
                return False

        parent = _Parent()
        for item_type in item_types:
            self._do_fetch_more(item_type, parent)
        self._fetch_all_finished.emit()

    def _get_db_items(self, item_type, order_by=("id",), query_chunk_size=1000, iter_chunk_size=1000):
        """Runs the given query and yields results by chunks of given size.

        Args:
            item_type (str): item type

        Yields:
            list: chunk of items
        """
        query = self._make_query(item_type, order_by=order_by)
        it = (x._asdict() for x in query.yield_per(query_chunk_size).enable_eagerloads(False))
        while True:
            chunk = list(itertools.islice(it, iter_chunk_size))
            yield chunk
            if not chunk:
                break

    def _make_query(self, item_type, order_by=("id",)):
        """Makes a database query for given item type.

        Args:
            item_type (str): item type
            order_by (Iterable): key for order by

        Returns:
            Query: database query
        """
        sq_name = self._db_map.cache_sqs[item_type]
        sq = getattr(self._db_map, sq_name)
        return self._db_map.query(sq).order_by(*[getattr(sq.c, k) for k in order_by])
