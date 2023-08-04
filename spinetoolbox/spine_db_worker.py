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
from functools import wraps
from PySide6.QtCore import QObject, Signal, Slot
from spinedb_api import DatabaseMapping, SpineDBAPIError
from .helpers import busy_effect, separate_metadata_and_item_metadata
from .qthread_pool_executor import QtBasedThreadPoolExecutor


_CHUNK_SIZE = 1000


def _db_map_lock(func):
    """A wrapper for SpineDBWorker that locks the database for the duration of the wrapped method.

    In case the locking fails, the wrapped method will not be invoked.

    Args:
        func (Callable): method to wrap
    """

    @wraps(func)
    def new_function(self, *args, **kwargs):
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            return
        try:
            return func(self, *args, **kwargs)
        finally:
            lock.unlock()

    return new_function


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _more_available = Signal(object)
    _will_have_children_change = Signal(list)

    def __init__(self, db_mngr, db_url):
        super().__init__()
        self._parents_by_type = {}
        self._add_item_callbacks = {}
        self._update_item_callbacks = {}
        self._remove_item_callbacks = {}
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._committing = False
        self._current_fetch_token = 0
        self._offsets = {}
        self._fetched_ids = {}
        self._fetched_item_types = set()
        self.commit_cache = {}
        self._executor = QtBasedThreadPoolExecutor(max_workers=1)
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
        self._executor.shutdown()
        self.deleteLater()

    def query(self, sq_name):
        """For tests."""
        return self._executor.submit(self._query, sq_name).result()

    def _query(self, sq_name):
        return self._db_map.query(getattr(self._db_map, sq_name)).all()

    def get_db_map(self, *args, **kwargs):
        return self._executor.submit(self._get_db_map, *args, **kwargs).result()

    def _get_db_map(self, *args, **kwargs):
        self._db_map = DatabaseMapping(
            self._db_url, *args, advance_cache_query=self.advance_query, sqlite_timeout=2, **kwargs
        )
        return self._db_map

    def reset_queries(self):
        """Resets queries and clears caches."""
        self._current_fetch_token += 1
        self._offsets.clear()
        self._fetched_ids.clear()
        self._fetched_item_types.clear()
        self._advance_query_callbacks.clear()

    def _reset_fetching_if_required(self, parent):
        """Sets fetch parent's token or resets the parent if fetch tokens don't match.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent.fetch_token is None:
            parent.fetch_token = self._current_fetch_token
        elif parent.fetch_token != self._current_fetch_token:
            self._add_item_callbacks.pop(parent, None)
            self._update_item_callbacks.pop(parent, None)
            self._remove_item_callbacks.pop(parent, None)
            parent.reset_fetching(self._current_fetch_token)

    def advance_query(self, item_type):
        """Advances the DB query that fetches items of given type.

        Args:
            item_type (str)

        Returns:
            bool
        """
        if item_type in self._fetched_item_types:
            return False
        return self._executor.submit(self._do_advance_query, item_type).result()

    def _advance_query(self, item_type, callback=None):
        """Schedules a progression of the DB query that fetches items of given type.
        Adds the given callback to the collection of callbacks to call when the query progresses.

        Args:
            item_type (str)
            callback (Function or None)

        Returns:
            bool: True if query is being advanced, False otherwise
        """
        if item_type in self._fetched_item_types:
            return False
        if item_type in self._advance_query_callbacks:
            self._advance_query_callbacks[item_type].add(callback)
            return True
        self._advance_query_callbacks[item_type] = {callback}
        self._executor.submit(self._do_advance_query, item_type)
        return True

    @busy_effect
    @_db_map_lock
    def _do_advance_query(self, item_type):
        """Advances the DB query that fetches items of given type and caches the results.

        Args:
            item_type (str)

        Returns:
            bool: True if new items were fetched from the DB, False otherwise.
        """
        try:
            sq_name = self._db_map.cache_sqs[item_type]
        except KeyError:
            return False
        offset = self._offsets.setdefault(item_type, 0)
        query = self._db_map.query(getattr(self._db_map, sq_name)).limit(_CHUNK_SIZE).offset(offset)
        chunk = [x._asdict() for x in query]
        self._offsets[item_type] += len(chunk)
        if not chunk:
            self._fetched_item_types.add(item_type)
        else:
            self._db_mngr.add_items_to_cache(item_type, {self._db_map: chunk})
            self._fetched_ids.setdefault(item_type, []).extend([x["id"] for x in chunk])
            self._populate_commit_cache(item_type, chunk)
        for callback in self._advance_query_callbacks.pop(item_type, ()):
            if callback is not None:
                callback()
        return bool(chunk)

    def _register_fetch_parent(self, parent):
        """Registers the given parent and starts checking whether it will have children if fetched.

        Args:
            parent (FetchParent)
        """
        parents = self._parents_by_type.setdefault(parent.fetch_item_type, set())
        if parent not in parents:
            parents.add(parent)
            self._update_parents_will_have_children(parent.fetch_item_type)

    def _update_parents_will_have_children(self, item_type):
        """Schedules a restart of the process that checks whether parents associated to given type will have children.

        Args:
            item_type (str)
        """
        self._executor.submit(self._do_update_parents_will_have_children, item_type)

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
            for id_ in self._fetched_ids.get(item_type, [])[position:]:
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
            self._do_advance_query(item_type)
            if position == len(self._fetched_ids.get(item_type, ())):
                for parent in parents_to_check:
                    parent.will_have_children = False
                self._will_have_children_change.emit(parents_to_check)
                break

    @Slot(list)
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
        for id_ in self._fetched_ids.get(item_type, [])[parent.position(self._db_map) :]:
            parent.increment_position(self._db_map)
            item = self._db_mngr.get_item(self._db_map, item_type, id_)
            if not item:
                # Happens in one unit test
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
        item.readd_callbacks.add(self._make_add_item_callback(parent))
        item.update_callbacks.add(self._make_update_item_callback(parent))
        item.remove_callbacks.add(self._make_remove_item_callback(parent))

    def _add_item(self, parent, item):
        if parent.is_obsolete:
            self._add_item_callbacks.pop(parent, None)
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

    def _make_add_item_callback(self, parent):
        if parent not in self._add_item_callbacks:
            self._add_item_callbacks[parent] = lambda item, parent=parent: self._add_item(parent, item)
        return self._add_item_callbacks[parent]

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
        parent.set_busy(True)
        if not self._iterate_cache(parent) and not parent.is_fetched:
            if not self._advance_query(parent.fetch_item_type, callback=lambda: self._handle_query_advanced(parent)):
                parent.set_busy(False)

    def _handle_query_advanced(self, parent):
        if parent.position(self._db_map) < len(self._fetched_ids.get(parent.fetch_item_type, ())):
            self._more_available.emit(parent)
        else:
            parent.set_fetched(True)
            parent.set_busy(False)

    def fetch_all(self, fetch_item_types=None, include_descendants=False, include_ancestors=False):
        if fetch_item_types is None:
            fetch_item_types = set(self._db_map.ITEM_TYPES)
        if include_descendants:
            fetch_item_types |= {
                descendant
                for item_type in fetch_item_types
                for descendant in self._db_map.descendant_tablenames.get(item_type, ())
            }
        if include_ancestors:
            fetch_item_types |= {
                ancestor
                for item_type in fetch_item_types
                for ancestor in self._db_map.ancestor_tablenames.get(item_type, ())
            }
        fetch_item_types -= self._fetched_item_types
        if fetch_item_types:
            _ = self._executor.submit(self._fetch_all, fetch_item_types).result()

    def _fetch_all(self, item_types):
        for item_type in item_types:
            while self._do_advance_query(item_type):
                pass

    def _populate_commit_cache(self, item_type, items):
        if item_type == "commit":
            return
        if item_type == "entity_group":  # FIXME: the entity_group table has no commit_id column :(
            return
        for item in items:
            self.commit_cache.setdefault(item["commit_id"], {}).setdefault(item_type, list()).append(item["id"])

    def close_db_map(self):
        _ = self._executor.submit(self._close_db_map).result()

    def _close_db_map(self):
        if not self._db_map.connection.closed:
            self._db_map.connection.close()

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
    def add_items(self, orig_items, item_type, readd, cascade, check, cache, callback):
        """Adds items to db.

        Args:
            orig_items (dict): lists of items to add or update
            item_type (str): item type
            readd (bool) : Whether to re-add items that were previously removed
            cascade (bool): Whether to add items in cascade or just the root items
            check (bool): Whether to check integrity
            cache (dict): Cache
            callback (None or function): something to call with the result
        """
        method_name = {
            "object_class": "add_object_classes",
            "object": "add_objects",
            "relationship_class": "add_wide_relationship_classes",
            "relationship": "add_wide_relationships",
            "entity_group": "add_entity_groups",
            "parameter_definition": "add_parameter_definitions",
            "parameter_value": "add_parameter_values",
            "parameter_value_list": "add_parameter_value_lists",
            "list_value": "add_list_values",
            "alternative": "add_alternatives",
            "scenario": "add_scenarios",
            "scenario_alternative": "add_scenario_alternatives",
            "feature": "add_features",
            "tool": "add_tools",
            "tool_feature": "add_tool_features",
            "tool_feature_method": "add_tool_feature_methods",
            "metadata": "add_metadata",
            "entity_metadata": "add_ext_entity_metadata",
            "parameter_value_metadata": "add_ext_parameter_value_metadata",
        }[item_type]
        check &= not self._committing
        readd |= self._committing
        with self._db_map.override_committing(self._committing):
            items, errors = getattr(self._db_map, method_name)(
                *orig_items, check=check, readd=readd, return_items=True, cache=cache
            )
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        if self._committing:
            if callback is not None:
                callback({})
            return
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            if not readd:
                actual_items = self._db_mngr.add_items_to_cache(actual_item_type, {self._db_map: actual_items})[
                    self._db_map
                ]
                self._fetched_ids.setdefault(actual_item_type, []).extend([x["id"] for x in actual_items])
                for parent in self._get_parents(actual_item_type):
                    self.fetch_more(parent)
                data = actual_items
            else:
                data = []
                for item in actual_items:
                    # Item may have been replaced in cache during commit.
                    item_type = item.item_type
                    item_in_cache = self._db_mngr.get_item(self._db_map, item_type, item["id"])
                    if not item_in_cache.readd_callbacks:
                        # Item may have been unbound on commit.
                        # We need to rebind it so cascade_readd() notifies fetch parents properly.
                        self._rebind_recursively(item_in_cache)
                    if cascade:
                        item_in_cache.cascade_readd()
                    else:
                        item_in_cache.readd()
                    data.append(item_in_cache)
            db_map_data = {self._db_map: data}
            if item_type == actual_item_type and callback is not None:
                callback(db_map_data)
            self._db_mngr.items_added.emit(actual_item_type, db_map_data)

    def _rebind_recursively(self, item):
        """Rebinds a cache item and its referrers to fetch parents.

        Args:
            item (CacheItem): item to rebind
        """
        if not item.readd_callbacks:
            for parent in self._get_parents(item.item_type):
                if parent.accepts_item(item, self._db_map):
                    self._bind_item(parent, item)
        for referrer in item.referrers.values():
            self._rebind_recursively(referrer)

    @busy_effect
    def update_items(self, orig_items, item_type, check, cache, callback):
        """Updates items in db.

        Args:
            orig_items (dict): lists of items to add or update
            item_type (str): item type
            check (bool): Whether or not to check integrity
            cache (dict): Cache
            callback (None or function): something to call with the result
        """
        method_name = {
            "object_class": "update_object_classes",
            "object": "update_objects",
            "relationship_class": "update_wide_relationship_classes",
            "relationship": "update_wide_relationships",
            "parameter_definition": "update_parameter_definitions",
            "parameter_value": "update_parameter_values",
            "parameter_value_list": "update_parameter_value_lists",
            "list_value": "update_list_values",
            "alternative": "update_alternatives",
            "scenario": "update_scenarios",
            "scenario_alternative": "update_scenario_alternatives",
            "feature": "update_features",
            "tool": "update_tools",
            "tool_feature": "update_tool_features",
            "tool_feature_method": "update_tool_feature_methods",
            "metadata": "update_metadata",
            "entity_metadata": "update_ext_entity_metadata",
            "parameter_value_metadata": "update_ext_parameter_value_metadata",
        }[item_type]
        check &= not self._committing
        with self._db_map.override_committing(self._committing):
            items, errors = getattr(self._db_map, method_name)(*orig_items, check=check, return_items=True, cache=cache)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        if self._committing:
            if callback is not None:
                callback({})
            return
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            self._db_mngr.update_items_in_cache(actual_item_type, {self._db_map: actual_items})
            db_map_data = {self._db_map: [{**x} for x in actual_items]}
            if item_type == actual_item_type and callback is not None:
                callback(db_map_data)
            self._db_mngr.items_updated.emit(actual_item_type, db_map_data)

    @busy_effect
    def remove_items(self, item_type, ids, callback, committing_callback):
        """Removes items from database.

        Args:
            item_type (str): item type
            ids (Iterable of int): removable item ids
            callback (Callable, optional): function to call after items have been removed
            committing_callback (Callable, optional): function to call after remove operation has been committed only
        """
        if self._committing:
            with self._db_map.override_committing(self._committing):
                try:
                    removed_items = self._db_map.cascade_remove_items(**{item_type: ids})
                except SpineDBAPIError as err:
                    self._db_mngr.error_msg.emit({self._db_map: [err]})
                else:
                    if committing_callback is not None:
                        committing_callback({self._db_map: removed_items})
            if callback is not None:
                callback({})
            return
        db_map_data = self._db_mngr.remove_items_in_cache(item_type, {self._db_map: ids})
        if callback is not None:
            callback(db_map_data)
        self._db_mngr.items_removed.emit(item_type, db_map_data)

    def commit_session(self, commit_msg, cookie=None):
        """Initiates commit session.

        Args:
            commit_msg (str): commit message
            cookie (Any): a cookie to include in session_committed signal
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._executor.submit(self._commit_session, commit_msg, undo_stack, cookie).result()

    def _commit_session(self, commit_msg, undo_stack, cookie=None):
        """Commits session for given database maps.

        Args:
            commit_msg (str): commit message
            undo_stack (AgedUndoStack): undo stack that outlive the DB manager
            cookie (Any): a cookie to include in session_committed signal
        """
        self._committing = True
        undo_stack.commit()
        self._committing = False
        try:
            self._db_map.commit_session(commit_msg)
            self._db_mngr.session_committed.emit({self._db_map}, cookie)
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})
        undo_stack.setClean()

    def rollback_session(self):
        """Initiates rollback session in the worker thread."""
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._executor.submit(self._rollback_session, undo_stack)

    def _rollback_session(self, undo_stack):
        """Rolls back session.

        Args:
            undo_stack (AgedUndoStack): undo stack that outlive the DB manager
        """
        try:
            self._db_map.reset_session()
            self._db_mngr.session_rolled_back.emit({self._db_map})
        except SpineDBAPIError as err:
            self._db_mngr.error_msg.emit({self._db_map: [err.msg]})
        undo_stack.setClean()
