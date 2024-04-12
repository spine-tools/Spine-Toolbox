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

"""The SpineDBWorker class."""
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtCore import QTimer
from spinedb_api import Asterisk, DatabaseMapping
from .qthread_pool_executor import QtBasedThreadPoolExecutor, SynchronousExecutor
from .helpers import busy_effect


_CHUNK_SIZE = 10000


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _query_advanced = Signal(object)

    def __init__(self, db_mngr, db_url, synchronous=False):
        super().__init__()
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._executor = (SynchronousExecutor if synchronous else QtBasedThreadPoolExecutor)()
        self._parents_by_type = {}
        self.commit_cache = {}
        self._parents_fetching = {}
        self._offsets = {}
        self._fetched_item_types = set()
        self._query_advanced.connect(self._fetch_more_later)

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
        self._db_map = DatabaseMapping(self._db_url, *args, sqlite_timeout=2, **kwargs)
        return self._db_map

    def register_fetch_parent(self, parent):
        """Registers the given parent.

        Args:
            parent (FetchParent): parent to add
        """
        parents = self._parents_by_type.setdefault(parent.fetch_item_type, set())
        parents.add(parent)

    @busy_effect
    def _iterate_mapping(self, parent):
        """Iterates the in-memory mapping for given parent while updating its ``position`` property.
        Iterated items are added to the parent if it accepts them.

        Args:
            parent (FetchParent): the parent.

        Returns:
            bool: Whether the parent can stop fetching from now
        """
        item_type = parent.fetch_item_type
        index = parent.index
        parent_pos = parent.position(self._db_map)
        items = self._db_map.get_items(item_type, fetch=False, skip_removed=False)
        if index is not None:
            # Build index from where we left and get items from it
            index_pos = index.position(self._db_map)
            for item in items[index_pos:]:
                index.increment_position(self._db_map)
                if not item:
                    continue
                item.validate()
                index.process_item(item, self._db_map)
            parent_key = parent.key_for_index(self._db_map)
            items = index.get_items(parent_key, self._db_map)[parent_pos:]
        else:
            # Get items directly from mapping, from where we left
            items = items[parent_pos:]
        added_count = 0
        for item in items:
            parent.increment_position(self._db_map)
            if not item:
                continue
            item.validate()
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
        return not parent.is_fetched

    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (FetchParent): fetch parent
        """
        self.register_fetch_parent(parent)
        if not parent.is_busy:
            parent.set_busy(True)
            self._do_fetch_more(parent)

    def _do_fetch_more(self, parent):
        item_type = parent.fetch_item_type
        fully_fetched = item_type in self._fetched_item_types
        # Only trust mapping if no external commits or fully fetched
        if not self._db_map.has_external_commits() or fully_fetched:
            if self._iterate_mapping(parent):
                # Something fetched from mapping
                return
        if fully_fetched:
            # Nothing left in the DB
            parent.set_fetched(True)
            return
        # Query the DB
        if item_type in self._parents_fetching:
            self._parents_fetching[item_type].add(parent)
            return
        self._parents_fetching[item_type] = {parent}
        callback = lambda future: self._handle_query_advanced(item_type, future.result())
        self._executor.submit(self._busy_db_map_fetch_more, item_type).add_done_callback(callback)

    @Slot(object)
    def _fetch_more_later(self, parents):
        for parent in parents:
            QTimer.singleShot(0, lambda parent=parent: self._do_fetch_more(parent))

    @busy_effect
    def _busy_db_map_fetch_more(self, item_type):
        offset = self._offsets.setdefault(item_type, 0)
        chunk = self._db_map.fetch_more(item_type, limit=_CHUNK_SIZE, offset=offset)
        if len(chunk) < _CHUNK_SIZE:
            self._fetched_item_types.add(item_type)
        self._offsets[item_type] += len(chunk)
        return chunk

    def _handle_query_advanced(self, item_type, chunk):
        self._populate_commit_cache(item_type, chunk)
        self._db_mngr.update_icons(self._db_map, item_type, chunk)
        parents = self._parents_fetching.pop(item_type, ())
        if parents and not self._db_map.closed:
            self._query_advanced.emit(parents)

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        for item in items:
            commit_id = item.get("commit_id")
            if commit_id is not None:
                self.commit_cache.setdefault(commit_id, {}).setdefault(item_type, []).append(item["id"])

    def fetch_all(self):
        self._db_map.fetch_all()

    def close_db_map(self):
        # FIXME: maybe check if self._db_map.closed is True in self._do_fetch_more instead?
        self._do_fetch_more = lambda worker, *args, **kwargs: None
        for parents in self._parents_by_type.values():
            for parent in parents:
                if not parent.is_obsolete:
                    parent.set_obsolete(True)
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

    def _wake_up_parents(self, item_type, items):
        for parent in list(self._get_parents(item_type)):
            for item in items:
                if parent.accepts_item(item, self._db_map):
                    self._do_fetch_more(parent)
                    break

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
        self._db_mngr.items_updated.emit(item_type, {self._db_map: items})
        return items

    @busy_effect
    def add_update_items(self, item_type, orig_items, check):
        """Add-updates items in db.

        Args:
            item_type (str): item type
            orig_items (list): dict-items to update
            check (bool): Whether or not to check integrity
        """
        added, updated, errors = self._db_map.add_update_items(item_type, *orig_items, check=check)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        self._db_mngr.update_icons(self._db_map, item_type, added + updated)
        self._wake_up_parents(item_type, added)
        self._db_mngr.items_added.emit(item_type, {self._db_map: added})
        self._db_mngr.items_updated.emit(item_type, {self._db_map: updated})
        return added, updated

    @busy_effect
    def remove_items(self, item_type, ids, check):
        """Removes items from database.

        Args:
            item_type (str): item type
            ids (set): ids of items to remove
        """
        items, errors = self._db_map.remove_items(item_type, *ids, check=check)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
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
        if Asterisk in ids:
            items = self._db_map.get_items(item_type)
        self._db_mngr.update_icons(self._db_map, item_type, items)
        self._db_mngr.items_added.emit(item_type, {self._db_map: items})
        return items

    def refresh_session(self):
        """Refreshes session."""
        self._db_map.refresh_session()
        for parent_type in self._parents_by_type:
            for parent in self._get_parents(parent_type):
                parent.reset()
        self._offsets.clear()
        self._fetched_item_types.clear()
        self._parents_fetching.clear()

    def reset_session(self):
        """Resets session."""
        self._db_map.reset()
        self.refresh_session()
