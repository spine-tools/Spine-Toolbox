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
        self._iterators = {}
        self.commit_cache = {}
        self._fetched = {}
        self._can_fetch_more_cache = {}
        self.moveToThread(db_mngr.worker_thread)
        self._fetch_more_requested.connect(self._fetch_more)
        self._fetch_all_requested.connect(self._fetch_all)
        self._parents = {}

    def can_fetch_more(self, item_type, parent=None):
        return not self._fetched.get((item_type, parent), False)

    @busy_effect
    def fetch_more(self, item_type, parent=None):
        """Fetches items from the database.

        Args:
            item_type (str): the type of items to fetch, e.g. "object_class"
        """
        self._fetch_more_requested.emit(item_type, parent)

    @Slot(str, object)
    def _fetch_more(self, item_type, parent):
        self._do_fetch_more(item_type, parent)

    def _get_iterator(self, item_type, parent):
        if (item_type, parent) not in self._iterators:
            self._iterators[item_type, parent] = self._get_db_items(item_type, parent)
        return self._iterators[item_type, parent]

    @busy_effect
    def _do_fetch_more(self, item_type, parent):
        iterator = self._get_iterator(item_type, parent)
        if iterator is None:
            return
        chunk = next(iterator, [])
        print(item_type, parent, len(chunk))
        self._populate_commit_cache(item_type, chunk)
        if not chunk:
            self._fetched[item_type, parent] = True
            return
        signal = self._db_mngr.added_signals[item_type]
        signal.emit({self._db_map: chunk})

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
            qApp.processEvents()
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

    def _get_db_items(self, item_type, parent, order_by=("id",), query_chunk_size=1000, iter_chunk_size=1000):
        """Runs the given query and yields results by chunks of given size.

        Args:
            item_type (str): item type

        Yields:
            list: chunk of items
        """
        query = self._make_query(item_type, parent, order_by=order_by)
        it = (x._asdict() for x in query.yield_per(query_chunk_size).enable_eagerloads(False))
        while True:
            chunk = list(itertools.islice(it, iter_chunk_size))
            yield chunk
            if not chunk:
                break

    def _make_query(self, item_type, parent, order_by=("id",)):
        """Makes a database query for given item type.

        Args:
            item_type (str): item type
            order_by (Iterable): key for order by

        Returns:
            Query: database query
        """
        sq_name = self._db_map.cache_sqs[item_type]
        sq = getattr(self._db_map, sq_name)
        qry = self._db_map.query(sq).order_by(*[getattr(sq.c, k) for k in order_by])
        if parent is not None:
            qry = parent.filter_query(qry, self._db_map)
        return qry

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        if item_type == "entity_group":  # FIXME
            return
        for item in items:
            self.commit_cache.setdefault(item["commit_id"], {}).setdefault(item_type, list()).append(item["id"])
