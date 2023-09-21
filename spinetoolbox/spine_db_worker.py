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
The SpineDBWorker class
"""
from PySide6.QtCore import QObject, Signal, Slot
from spinedb_api import DatabaseMapping, SpineDBAPIError
from .qthread_pool_executor import QtBasedThreadPoolExecutor, SynchronousExecutor
from .helpers import busy_effect


_CHUNK_SIZE = 1000


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _more_available = Signal(object)

    def __init__(self, db_mngr, db_url, synchronous=False):
        super().__init__()
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._executor = (SynchronousExecutor if synchronous else QtBasedThreadPoolExecutor)()
        self._parents_by_type = {}
        self.commit_cache = {}
        self._parents_fetching = {}
        self._more_available.connect(self.fetch_more)

    def _get_parents(self, item_type):
        parents = self._parents_by_type.get(item_type, set())
        for parent in list(parents):
            if parent.is_obsolete:
                parents.remove(parent)
        return parents

    def clean_up(self):
        self._executor.shutdown()
        self.deleteLater()

    def get_db_map(self, *args, **kwargs):
        self._db_map = DatabaseMapping(self._db_url, *args, sqlite_timeout=2, chunk_size=_CHUNK_SIZE, **kwargs)
        return self._db_map

    def register_fetch_parent(self, parent):
        """Registers the given parent.

        Args:
            parent (FetchParent): parent to add
        """
        parents = self._parents_by_type.setdefault(parent.fetch_item_type, set())
        parents.add(parent)

    @busy_effect
    def _iterate_cache(self, parent):
        """Iterates the cache for given parent while updating its ``position`` property.
        Iterated items are added to the parent if it accepts them.

        Args:
            parent (FetchParent): the parent.

        Returns:
            bool: Whether the parent can stop fetching from now
        """
        item_type = parent.fetch_item_type
        index = parent.index
        parent_pos = parent.position(self._db_map)
        ids = list(self._db_map.cache.get(item_type, {}))
        if index is not None:
            # Build index from where we left and get items from it
            index_pos = index.position(self._db_map)
            for id_ in ids[index_pos:]:
                item = self._db_mngr.get_item(self._db_map, item_type, id_)
                index.increment_position(self._db_map)
                if not item:
                    continue
                index.process_item(item, self._db_map)
            parent_key = parent.key_for_index(self._db_map)
            items = index.get_items(parent_key, self._db_map)[parent_pos:]
        else:
            # Get items directly from cache, from where we left
            items = [self._db_mngr.get_item(self._db_map, item_type, id_) for id_ in ids[parent_pos:]]
        added_count = 0
        for item in items:
            parent.increment_position(self._db_map)
            if not item:
                continue
            if index is not None or parent.accepts_item(item, self._db_map):
                parent.bind_item(item, self._db_map)
                if item.is_valid():
                    parent.add_item(item, self._db_map)
                    if parent.shows_item(item, self._db_map):
                        added_count += 1
                if added_count == parent.chunk_size:
                    break
        if parent.chunk_size is None:
            return False
        return added_count > 0

    def can_fetch_more(self, parent):
        """Returns whether more data can be fetched for parent.
        Also, registers the parent to notify it of any relevant DB modifications later on.

        Args:
            parent (FetchParent): fetch parent

        Returns:
            bool: True if more data is available, False otherwise
        """
        self.register_fetch_parent(parent)
        return not parent.is_fetched and not parent.is_busy

    @Slot(object)
    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (FetchParent): fetch parent
        """
        self.register_fetch_parent(parent)
        if self._iterate_cache(parent):
            # Something in cache
            return
        item_type = parent.fetch_item_type
        parent.set_fetched(item_type in self._db_map.cache.fetched_item_types)
        if parent.is_fetched:
            # Nothing left in the DB
            return
        # Query the DB
        if item_type in self._parents_fetching:
            self._parents_fetching[item_type].add(parent)
            return
        self._parents_fetching[item_type] = {parent}
        callback = lambda future: self._handle_query_advanced(item_type, future.result())
        self._executor.submit(self._busy_advance_cache_query, item_type).add_done_callback(callback)
        parent.set_busy(True)

    @busy_effect
    def _busy_advance_cache_query(self, item_type):
        return self._db_map.advance_cache_query(item_type)

    def _handle_query_advanced(self, item_type, chunk):
        self._populate_commit_cache(item_type, chunk)
        self._db_mngr.update_icons(self._db_map, item_type, chunk)
        for parent in self._parents_fetching.pop(item_type, ()):
            self._update_parent(parent)

    def _is_fetch_complete(self, parent):
        """Whether fetch is complete for given parent."""
        items = self._db_map.cache.get(parent.fetch_item_type, ())
        index = parent.index
        if index is not None:
            if index.position(self._db_map) < len(items):
                return False
            parent_key = parent.key_for_index(self._db_map)
            index_items = index.get_items(parent_key, self._db_map)
            return parent.position(self._db_map) >= len(index_items)
        return parent.position(self._db_map) >= len(items)

    def _update_parent(self, parent):
        """Check if fetch is complete and react accordingly."""
        if self._is_fetch_complete(parent):
            parent.set_fetched(True)
            parent.set_busy(False)
        else:
            self._more_available.emit(parent)

    def fetch_all(self, fetch_item_types=None):
        self._db_map.fetch_all(fetch_item_types)

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        for item in items:
            commit_id = item.get("commit_id")
            if commit_id is not None:
                self.commit_cache.setdefault(commit_id, {}).setdefault(item_type, []).append(item["id"])

    def close_db_map(self):
        self._db_map.close()

    @busy_effect
    def add_items(self, item_type, orig_items, check):
        """Adds items to db.

        Args:
            item_type (str): item type
            orig_items (list): dict-items to add
            check (bool): Whether to check integrity
        """
        items, errors = self._db_map.add_items(item_type, *orig_items, check=check)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        self._db_mngr.update_icons(self._db_map, item_type, items)
        self._wake_up_parents(item_type, items)
        self._db_mngr.items_added.emit(item_type, {self._db_map: items})
        return items

    @busy_effect
    def update_items(self, item_type, orig_items, check):
        """Updates items in db.

        Args:
            item_type (str): item type
            orig_items (list): dict-items to update
            check (bool): Whether or not to check integrity
        """
        items, errors = self._db_map.update_items(item_type, *orig_items, check=check)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        self._db_mngr.update_icons(self._db_map, item_type, items)
        self._db_mngr.items_updated.emit(item_type, {self._db_map: [dict(x) for x in items]})
        return items

    @busy_effect
    def remove_items(self, item_type, ids):
        """Removes items from database.

        Args:
            item_type (str): item type
            ids (set): ids of items to remove
        """
        items = self._db_map.remove_items(item_type, *ids)
        self._db_mngr.items_removed.emit(item_type, {self._db_map: items})
        return items

    @busy_effect
    def restore_items(self, item_type, ids):
        """Readds items to database.

        Args:
            item_type (str): item type
            ids (set): ids of items to restore
        """
        items = self._db_map.restore_items(item_type, *ids)
        self._db_mngr.update_icons(self._db_map, item_type, items)
        self._wake_up_parents(item_type, items)
        self._db_mngr.items_added.emit(item_type, {self._db_map: items})
        return items

    def _wake_up_parents(self, item_type, items):
        for parent in list(self._get_parents(item_type)):
            for item in items:
                if parent.accepts_item(item, self._db_map):
                    self.fetch_more(parent)
                    break

    def commit_session(self, commit_msg, cookie=None):
        """Commits session.

        Args:
            commit_msg (str): commit message
            cookie (Any): a cookie to include in receive_session_committed call
        """
        try:
            self._db_map.commit_session(commit_msg)
            self._db_mngr.undo_stack[self._db_map].setClean()
            self._db_mngr.receive_session_committed({self._db_map}, cookie)
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})

    def rollback_session(self):
        """Rollbacks session."""
        try:
            self._db_map.rollback_session()
            self._db_mngr.undo_stack[self._db_map].setClean()
            self._db_mngr.receive_session_rolled_back({self._db_map})
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})

    def refresh_session(self):
        """Refreshes session."""
        for parents in self._parents_by_type.values():
            for parent in parents:
                parent.reset()
        self._db_map.refresh_session()
        self._parents_fetching.clear()
        self._db_mngr.receive_session_refreshed({self._db_map})
