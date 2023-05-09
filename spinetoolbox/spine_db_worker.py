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
from .helpers import busy_effect, separate_metadata_and_item_metadata


_CHUNK_SIZE = 1000


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _more_available = Signal(object)
    _will_have_children_change = Signal(object)

    def __init__(self, db_mngr, db_url):
        super().__init__()
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._parents_by_type = {}
        self._restore_item_callbacks = {}
        self._update_item_callbacks = {}
        self._remove_item_callbacks = {}
        self._current_fetch_token = 0
        self.commit_cache = {}
        self._advance_query_callbacks = {}
        self._more_available.connect(self.fetch_more)
        self._will_have_children_change.connect(self._handle_will_have_children_change)

    def _get_parents(self, item_type):
        parents = self._parents_by_type.get(item_type, set())
        for parent in list(parents):
            if parent.is_obsolete:
                parents.remove(parent)
        return parents

    def clean_up(self):
        self.deleteLater()

    def get_db_map(self, *args, **kwargs):
        self._db_map = DatabaseMapping(
            self._db_url, *args, sqlite_timeout=2, chunk_size=_CHUNK_SIZE, asynchronous=True, **kwargs
        )
        return self._db_map

    def reset_queries(self):
        """Resets queries and clears caches."""
        self._cache.reset_queries()
        self._reset_queries()

    def _reset_queries(self):
        self._current_fetch_token += 1
        self._advance_query_callbacks.clear()

    def _reset_fetching_if_required(self, parent):
        """Sets fetch parent's token or resets the parent if fetch tokens don't match.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent.fetch_token is None:
            parent.fetch_token = self._current_fetch_token
        elif parent.fetch_token != self._current_fetch_token:
            self._restore_item_callbacks.pop(parent, None)
            self._update_item_callbacks.pop(parent, None)
            self._remove_item_callbacks.pop(parent, None)
            parent.reset_fetching(self._current_fetch_token)

    def _register_fetch_parent(self, parent):
        """Registers the given parent and starts checking whether it will have children if fetched.

        Args:
            parent (FetchParent)
        """
        parents = self._parents_by_type.setdefault(parent.fetch_item_type, set())
        if parent not in parents:
            parents.add(parent)
            self._update_parents_will_have_children(parent.fetch_item_type)

    def _fetched_ids(self, item_type, position):
        return list(self._db_map.cache.get(item_type, {}))[position:]

    def _update_parents_will_have_children(self, item_type):
        """Schedules a restart of the process that checks whether parents associated to given type will have children.

        Args:
            item_type (str)
        """
        self._db_map.executor.submit(self._do_update_parents_will_have_children, item_type)

    def _do_update_parents_will_have_children(self, item_type):
        """Updates the ``will_have_children`` property for all parents associated to given type.

        Args:
            item_type (str)
        """
        # 1. Initialize the list of parents to check (those with will_have_children equal to None)
        # 2. Obtain the next item of given type from cache.
        # 3. Check if the unchecked parents accept the item. Set will_have_children to True if any of them does
        #    and remove them from the list to check.
        # 4. If there are no more items in cache, advance the query and if it brings more items, go back to 2.
        # 5. If the query is completed, set will_have_children to False for all remaining parents to check and quit.
        # 6. If at any moment the set of parents associated to given type is mutated, quit so we can start over.
        parents = self._get_parents(item_type)
        position = 0
        while True:
            parents_to_check = {parent for parent in parents if parent.will_have_children is None}
            if not parents_to_check:
                break
            for id_ in self._fetched_ids(item_type, position):
                if self._get_parents(item_type) != parents:
                    # New parents registered - we need to start over
                    return
                position += 1
                item = self._db_mngr.get_item(self._db_map, item_type, id_)
                for parent in parents_to_check.copy():
                    if parent.accepts_item(item, self._db_map):
                        parent.will_have_children = True
                        parents_to_check.remove(parent)
                if not parents_to_check:
                    break
            if not parents_to_check:
                break
            chunk = self._db_map.cache.do_advance_query(item_type)
            self._do_call_advance_query_callbacks(item_type, chunk)
            if position == len(self._db_map.cache.get(item_type, ())):
                for parent in parents_to_check:
                    parent.will_have_children = False
                self._will_have_children_change.emit(parents_to_check)
                break

    @Slot(object)
    @staticmethod
    def _handle_will_have_children_change(parents):
        for parent in parents:
            parent.will_have_children_change()

    def _iterate_cache(self, parent):
        """Iterates the cache for given parent while updating its ``position`` property.
        Iterated items are added to the parent if it accepts them.

        Args:
            parent (FetchParent): the parent.

        Returns:
            bool: Whether the parent can stop fetching from now
        """
        item_type = parent.fetch_item_type
        added_count = 0
        for id_ in self._fetched_ids(item_type, parent.position(self._db_map)):
            parent.increment_position(self._db_map)
            item = self._db_mngr.get_item(self._db_map, item_type, id_)
            if not item:
                # Happens in one unit test???
                continue
            if parent.accepts_item(item, self._db_map):
                self._bind_item(parent, item)
                if item.is_valid():
                    parent.add_item(item, self._db_map)
                    if parent.shows_item(item, self._db_map):
                        added_count += 1
                if added_count == parent.chunk_size:
                    break
        if parent.chunk_size is None:
            return False
        return added_count > 0

    def _bind_item(self, parent, item):
        item.restore_callbacks.add(self._make_restore_item_callback(parent))
        item.update_callbacks.add(self._make_update_item_callback(parent))
        item.remove_callbacks.add(self._make_remove_item_callback(parent))

    def _add_item(self, parent, item):
        if parent.is_obsolete:
            self._restore_item_callbacks.pop(parent, None)
            return False
        parent.add_item(item, self._db_map)
        return True

    def _update_item(self, parent, item):
        if parent.is_obsolete:
            self._update_item_callbacks.pop(parent, None)
            return False
        parent.update_item(item, self._db_map)
        return True

    def _remove_item(self, parent, item):
        if parent.is_obsolete:
            self._remove_item_callbacks.pop(parent, None)
            return False
        parent.remove_item(item, self._db_map)
        return True

    def _make_restore_item_callback(self, parent):
        if parent not in self._restore_item_callbacks:
            self._restore_item_callbacks[parent] = lambda item, parent=parent: self._add_item(parent, item)
        return self._restore_item_callbacks[parent]

    def _make_update_item_callback(self, parent):
        if parent not in self._update_item_callbacks:
            self._update_item_callbacks[parent] = lambda item, parent=parent: self._update_item(parent, item)
        return self._update_item_callbacks[parent]

    def _make_remove_item_callback(self, parent):
        if parent not in self._remove_item_callbacks:
            self._remove_item_callbacks[parent] = lambda item, parent=parent: self._remove_item(parent, item)
        return self._remove_item_callbacks[parent]

    def can_fetch_more(self, parent):
        """Returns whether more data can be fetched for parent.
        Also, registers the parent to notify it of any relevant DB modifications later on.

        Args:
            parent (FetchParent): fetch parent

        Returns:
            bool: True if more data is available, False otherwise
        """
        self._reset_fetching_if_required(parent)
        self._register_fetch_parent(parent)
        return parent.will_have_children is not False and not parent.is_fetched and not parent.is_busy

    @Slot(object)
    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (FetchParent): fetch parent
        """
        self._reset_fetching_if_required(parent)
        self._register_fetch_parent(parent)
        if self._iterate_cache(parent) or parent.is_fetched:  # NOTE: Order of statements is important
            return
        # Nothing in cache, something in DB
        item_type = parent.fetch_item_type
        if item_type in self._db_map.cache.fetched_item_types:
            return
        callback = lambda parent=parent: self._handle_query_advanced(parent)
        if item_type in self._advance_query_callbacks:
            self._advance_query_callbacks[item_type].add(callback)
            return
        self._advance_query_callbacks[item_type] = {callback}
        future = self._db_map.cache.advance_query(item_type)
        future.add_done_callback(
            lambda future, item_type=item_type: self._call_advance_query_callbacks(item_type, future)
        )
        parent.set_busy(True)

    def _handle_query_advanced(self, parent):
        if parent.position(self._db_map) < len(self._db_map.cache.get(parent.fetch_item_type, ())):
            self._more_available.emit(parent)
        else:
            parent.set_fetched(True)
            parent.set_busy(False)

    def _call_advance_query_callbacks(self, item_type, future):
        self._do_call_advance_query_callbacks(item_type, future.result())

    def _do_call_advance_query_callbacks(self, item_type, chunk):
        self._populate_commit_cache(item_type, chunk)
        self._db_mngr.update_icons(self._db_map, item_type, chunk)
        for callback in self._advance_query_callbacks.pop(item_type, ()):
            if callback is not None:
                callback()

    def fetch_all(self, fetch_item_types=None, include_descendants=False, include_ancestors=False):
        if fetch_item_types is None:
            fetch_item_types = set(self._db_map.ITEM_TYPES)
        self._db_map.fetch_all(
            fetch_item_types, include_descendants=include_descendants, include_ancestors=include_ancestors
        )

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        for item in items:
            commit_id = item.get("commit_id")
            if commit_id is not None:
                self.commit_cache.setdefault(commit_id, {}).setdefault(item_type, []).append(item["id"])

    def close_db_map(self):
        self._db_map.close()

    def _split_items_by_type(self, item_type, items):
        if item_type in ("parameter_value_metadata", "entity_metadata"):
            db_map_item_metadata, db_map_metadata = separate_metadata_and_item_metadata({self._db_map: items})
            metadata = db_map_metadata.get(self._db_map)
            item_metadata = db_map_item_metadata.get(self._db_map)
            if metadata:
                yield "metadata", metadata
            if item_metadata:
                yield item_type, item_metadata
        else:
            yield item_type, items

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
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            self._db_mngr.update_icons(self._db_map, actual_item_type, actual_items)
            for parent in self._get_parents(actual_item_type):
                self.fetch_more(parent)
            if item_type == actual_item_type:
                result = actual_items
            self._db_mngr.items_added.emit(actual_item_type, {self._db_map: actual_items})
        return result

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
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            self._db_mngr.update_icons(self._db_map, actual_item_type, actual_items)
            if item_type == actual_item_type:
                result = actual_items
            self._db_mngr.items_updated.emit(actual_item_type, {self._db_map: [{**x} for x in actual_items]})
        return result

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
        self._db_mngr.items_added.emit(item_type, {self._db_map: items})
        return items

    def commit_session(self, commit_msg, cookie=None):
        """Initiates commit session.

        Args:
            commit_msg (str): commit message
            cookie (Any): a cookie to include in session_committed signal
        """
        try:
            self._db_map.commit_session(commit_msg)  # This blocks until session is committed
            self._db_mngr.undo_stack[self._db_map].setClean()
            self._db_mngr.session_committed.emit({self._db_map}, cookie)
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})

    def rollback_session(self):
        """Initiates rollback session in the worker thread."""
        try:
            self._db_map.rollback_session()  # This blocks until session is rolled back
            self._reset_queries()
            self._db_mngr.undo_stack[self._db_map].setClean()
            self._db_mngr.session_rolled_back.emit({self._db_map})
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})
