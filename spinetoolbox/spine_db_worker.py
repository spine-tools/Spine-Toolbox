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

:authors: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""
from functools import wraps
import itertools
from enum import Enum, unique, auto
from PySide2.QtCore import QObject, Signal, Slot
from spinedb_api import DiffDatabaseMapping, SpineDBAPIError
from .helpers import busy_effect, separate_metadata_and_item_metadata
from .qthread_pool_executor import QtBasedThreadPoolExecutor


@unique
class _Event(Enum):
    MORE_AVAILABLE = auto()
    WILL_HAVE_CHILDREN_CHANGE = auto()
    ADD_ITEMS = auto()
    UPDATE_ITEMS = auto()
    REMOVE_ITEMS = auto()
    COMMIT_SESSION = auto()
    ROLLBACK_SESSION = auto()


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


def _by_chunks(it):
    """
    Iterate given iterator by chunks.

    Args:
        it (Iterable)
    Yields:
        list: chunk of items
    """
    while True:
        chunk = list(itertools.islice(it, _CHUNK_SIZE))
        yield chunk
        if not chunk:
            break


class _CacheIterator:
    def __init__(self, worker, parent):
        """An iterable that yields items from given worker to given parent.

        Args:
            worker (SpineDBWorker): the worker that provides the items.
            parent (FetchParent): the parent that requests the items.
        """
        self._worker = worker
        self._parent = parent
        self._iter_position = 0

    def _set_iter_position(self, position):
        self._iter_position = position

    def _next_chunk(self):
        """Produces the next chunk of items by iterating the worker's cache.
        If nothing found, then schedules a progression of the worker's query so more items can be found in the future.

        Yields:
            dict
        """
        k = 0
        for item in self._worker.iterate_cache(self._parent, self._iter_position, self._set_iter_position):
            yield item
            k += 1
            if k == _CHUNK_SIZE:
                return
        if not self._parent.is_fetched and k == 0:
            self._worker.advance_query_iterator(self._parent)

    def __next__(self):
        return list(self._next_chunk())

    def __iter__(self):
        return self


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _something_happened = Signal(object, tuple)

    def __init__(self, db_mngr, db_url):
        super().__init__()
        self._parents_by_type = {}
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._query_iterators = {}
        self._fetched_ids = {}
        self._current_fetch_token = 0
        self._removed_ids = {}
        self._fetched_item_types = set()
        self.commit_cache = {}
        self._executor = QtBasedThreadPoolExecutor(max_workers=1)
        self._something_happened.connect(self._handle_something_happened)

    def clean_up(self):
        self._executor.shutdown()
        self.deleteLater()

    @Slot(object, tuple)
    def _handle_something_happened(self, event, args):
        {
            _Event.MORE_AVAILABLE: self._more_available_event,
            _Event.WILL_HAVE_CHILDREN_CHANGE: self._will_have_children_change_event,
            _Event.ADD_ITEMS: self._add_items_event,
            _Event.UPDATE_ITEMS: self._update_items_event,
            _Event.REMOVE_ITEMS: self._remove_items_event,
            _Event.COMMIT_SESSION: self._commit_session_event,
            _Event.ROLLBACK_SESSION: self._rollback_session_event,
        }[event](*args)

    def query(self, sq_name):
        """For tests."""
        return self._executor.submit(self._query, sq_name).result()

    def _query(self, sq_name):
        return self._db_map.query(getattr(self._db_map, sq_name)).all()

    def get_db_map(self, *args, **kwargs):
        return self._executor.submit(self._get_db_map, *args, **kwargs).result()

    def _get_db_map(self, *args, **kwargs):
        self._db_map = DiffDatabaseMapping(self._db_url, *args, **kwargs)
        return self._db_map

    def reset_queries(self):
        """Resets queries and clears caches."""
        self._current_fetch_token += 1
        self._fetched_ids.clear()
        self._fetched_item_types.clear()
        self._query_iterators.clear()
        self._removed_ids.clear()

    def _reset_fetching_if_required(self, parent):
        """Sets fetch parent's token or resets the parent if fetch tokens don't match.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent.fetch_token is None:
            parent.fetch_token = self._current_fetch_token
        elif parent.fetch_token != self._current_fetch_token:
            parent.reset_fetching(self._current_fetch_token)

    def advance_query_iterator(self, parent):
        """Schedules a progression of the DB query that fetches items for given parent.
        Called whenever the parent has fetched everything from the cache already, so more items are needed.

        Args:
            parent (FetchParent)
        """
        self._executor.submit(self._advance_query_iterator, parent)

    def _advance_query_iterator(self, parent):
        """Advances the DB query that fetches items for given parent.
        If the query yields new items, then notifies the main thread to fetch the parent again so the new items
        can be processed.
        Otherwise sets the parent as fully fetched.

        Args:
            parent (FetchParent)
        """
        if self._do_advance_query_iterator(parent.fetch_item_type):
            self._something_happened.emit(_Event.MORE_AVAILABLE, (parent,))
        else:
            parent.set_fetched(True)
            parent.set_busy(False)

    @busy_effect
    @_db_map_lock
    def _do_advance_query_iterator(self, item_type):
        """Advances the DB query that fetches items of given type and caches the results.

        Args:
            item_type (str)

        Returns:
            bool: True if new items were fetched from the DB, False otherwise.
        """
        if item_type not in self._query_iterators:
            try:
                sq_name = self._db_map.cache_sqs[item_type]
            except KeyError:
                return False
            query = self._db_map.query(getattr(self._db_map, sq_name))
            self._query_iterators[item_type] = _by_chunks(
                x._asdict() for x in query.yield_per(_CHUNK_SIZE).enable_eagerloads(False)
            )
        iterator = self._query_iterators[item_type]
        chunk = next(iterator, None)
        if chunk is None:
            self._fetched_item_types.add(item_type)
            return False
        self._fetched_ids.setdefault(item_type, []).extend([x["id"] for x in chunk])
        self._db_mngr.cache_items(item_type, {self._db_map: chunk})
        self._populate_commit_cache(item_type, chunk)
        return True

    def _register_fetch_parent(self, parent):
        """Registers the given parent and starts checking whether it will have children if fetched.

        Args:
            parent (FetchParent)
        """
        self._parents_by_type.setdefault(parent.fetch_item_type, set()).add(parent)
        self._update_parents_will_have_children(parent.fetch_item_type)

    def _update_parents_will_have_children(self, item_type):
        """Schedules a restart of the process that checks whether parents associated to given type will have children.

        Args:
            item_type (str)
        """
        self._executor.submit(self._do_update_parents_will_have_children, item_type)

    def _do_update_parents_will_have_children(self, item_type):
        """Updates the will_have_children property for all parents associated to given type.

        The algorithm is as follows:
        - Iterate the cache and check whether the relevant parents accept the item.
        - If yes, then set will_have_children to True for all of them and forget about them.
        - If the cache is finished, then advance the query and repeat until either
          there are no more parents left to check, or the query is completed.
        - In the latter case set will_have_children to False for all remaining parents.
        - If at any moment the set of parents associated to given type is mutated, quit so we can start over.

        Args:
            item_type (str)
        """
        parents = self._parents_by_type.get(item_type, ())
        position = 0
        while True:
            parents_to_check = {parent for parent in parents if parent.will_have_children is None}
            if not parents_to_check:
                break
            removed_ids = self._removed_ids.get(item_type, ())
            for id_ in self._fetched_ids.get(item_type, [])[position:]:
                if self._parents_by_type.get(item_type, ()) != parents:
                    # New parents registered - we need to start over
                    return
                position += 1
                if id_ in removed_ids:
                    continue
                item = self._db_mngr.get_item(self._db_map, item_type, id_)
                for parent in parents_to_check.copy():
                    if parent.accepts_item(item, self._db_map):
                        parent.will_have_children = True
                        parents_to_check.remove(parent)
                if not parents_to_check:
                    return
            if not parents_to_check:
                break
            if not self._do_advance_query_iterator(item_type):
                for parent in parents_to_check:
                    parent.will_have_children = False
                    self._something_happened.emit(_Event.WILL_HAVE_CHILDREN_CHANGE, (parent,))
                break

    def _get_cache_iterator(self, parent):
        """Initializes and returns the cache iterator for given parent.

        Args:
            parent (FetchParent)

        Returns:
            _CacheIterator
        """
        if parent.iterator is None:
            parent.iterator = _CacheIterator(self, parent)
        return parent.iterator

    def iterate_cache(self, parent, position, set_position):
        """Iterates the cache for given parent starting at given position.

        Args:
            parent (FetchParent): the parent that requests the items.
            position (int): initial position.
            set_position (function): a function to call with the new position every time we iterate.
                This is so the caller (_CacheIterator) knows where to start the next time it needs items.

        Yields:
            dict: The next item from cache that passes the parent's filter.
        """
        item_type = parent.fetch_item_type
        removed_ids = self._removed_ids.get(item_type, ())
        for id_ in self._fetched_ids.get(item_type, [])[position:]:
            position += 1
            set_position(position)
            if id_ in removed_ids:
                continue
            item = self._db_mngr.get_item(self._db_map, item_type, id_)
            if parent.accepts_item(item, self._db_map):
                yield item

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

    @staticmethod
    def _will_have_children_change_event(parent):
        parent.will_have_children_change()

    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent not in self._parents_by_type.get(parent.fetch_item_type, ()):
            raise RuntimeError(
                f"attempting to fetch unregistered parent {parent} - did you forget to call ``can_fetch_more()``"
            )
        self._reset_fetching_if_required(parent)
        parent.set_busy(True)
        iterator = self._get_cache_iterator(parent)
        chunk = next(iterator, None)
        if chunk:
            parent.handle_items_added({self._db_map: chunk})
            parent.set_busy(False)

    def _more_available_event(self, parent):
        self.fetch_more(parent)

    def fetch_all(self, fetch_item_types=None, only_descendants=False, include_ancestors=False):
        if fetch_item_types is None:
            fetch_item_types = set(self._db_map.ITEM_TYPES)
        if only_descendants:
            fetch_item_types = {
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

    @busy_effect
    def _fetch_all(self, item_types):
        for item_type in item_types:
            while self._do_advance_query_iterator(item_type):
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

    def remove_parents(self, parents):
        """Remove given parents. Removed parents don't get updated whenever items are added/updated/removed.

        Args:
            parents (Iterable)
        """
        for parent in parents:
            self._parents_by_type.get(parent.fetch_item_type).remove(parent)

    def _call_in_parents(self, method_name, item_type, items):
        # TODO: Probably we want to handle RunTimeError set changed size during iteration
        # which may happen when removing parents above?
        for parent in self._parents_by_type.get(item_type, ()):
            children = [x for x in items if parent.accepts_item(x, self._db_map)]
            if not children:
                continue
            method = getattr(parent, method_name)
            method({self._db_map: children})

    def _update_special_refs(self, item_type, ids):
        cascading_ids_by_type = self._db_mngr.special_cascading_ids(self._db_map, item_type, ids)
        self._do_update_special_refs(cascading_ids_by_type)

    def _do_update_special_refs(self, cascading_ids_by_type, fill_missing=True):
        for cascading_item_type, cascading_ids in cascading_ids_by_type.items():
            cascading_items = self._db_mngr.make_items_from_ids(
                self._db_map, cascading_item_type, cascading_ids, fill_missing=fill_missing
            )
            self._call_in_parents("handle_items_updated", cascading_item_type, cascading_items)

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

    def _discard_removed_ids(self, item_type, items):
        """Discards added item ids from removed ids cache.

        Args:
            item_type (str): item type
            list of dict: added cache items
        """
        for item in items:
            try:
                removed_ids = self._removed_ids[item_type]
            except KeyError:
                continue
            removed_ids.discard(item["id"])

    def add_items(self, items, item_type, readd, check, cache, callback):
        """Adds items to db.

        Args:
            items (dict): lists of items to add or update
            item_type (str): item type
            readd (bool) : Whether to re-add items that were previously removed
            check (bool): Whether to check integrity
            cache (dict): Cache
            callback (None or function): something to call with the result
        """
        self._executor.submit(self._add_items, items, item_type, readd, check, cache, callback)

    @busy_effect
    def _add_items(self, orig_items, item_type, readd, check, cache, callback):
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
        items, errors = getattr(self._db_map, method_name)(
            *orig_items, check=check, readd=readd, return_items=True, cache=cache
        )
        self._discard_removed_ids(item_type, items)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            actual_items = self._db_mngr.make_items_from_db_items(self._db_map, actual_item_type, actual_items)
            self._something_happened.emit(
                _Event.ADD_ITEMS, (actual_item_type, actual_items, callback if item_type == actual_item_type else None)
            )

    def _add_items_event(self, item_type, items, callback):
        self._call_in_parents("handle_items_added", item_type, items)
        self._update_special_refs(item_type, {x["id"] for x in items})
        db_map_data = {self._db_map: items}
        if callback is not None:
            callback(db_map_data)
        self._db_mngr.items_added.emit(item_type, db_map_data)

    def update_items(self, items, item_type, check, cache, callback):
        """Updates items in db.

        Args:
            items (dict): lists of items to add or update
            item_type (str): item type
            check (bool): Whether or not to check integrity
            cache (dict): Cache
            callback (None or function): something to call with the result
        """
        self._executor.submit(self._update_items, items, item_type, check, cache, callback)

    @busy_effect
    def _update_items(self, orig_items, item_type, check, cache, callback):
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
        items, errors = getattr(self._db_map, method_name)(*orig_items, check=check, return_items=True, cache=cache)
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        for actual_item_type, actual_items in self._split_items_by_type(item_type, items):
            cascading_ids_by_type = self._db_map.cascading_ids(
                cache=cache, **{actual_item_type: {x["id"] for x in actual_items}}
            )
            del cascading_ids_by_type[actual_item_type]
            cascading_items_by_type = {
                actual_item_type: self._db_mngr.make_items_from_db_items(self._db_map, actual_item_type, actual_items)
            }
            for cascading_item_type, cascading_ids in cascading_ids_by_type.items():
                cascading_items = self._db_mngr.make_items_from_ids(self._db_map, cascading_item_type, cascading_ids)
                if cascading_items:
                    cascading_items_by_type[cascading_item_type] = cascading_items
            self._something_happened.emit(
                _Event.UPDATE_ITEMS,
                (cascading_items_by_type, actual_item_type, callback if item_type == actual_item_type else None),
            )

    def _update_items_event(self, cascading_items_by_type, item_type, callback):
        for cascading_item_type, cascading_items in cascading_items_by_type.items():
            self._call_in_parents("handle_items_updated", cascading_item_type, cascading_items)
        self._update_special_refs(item_type, {x["id"] for x in cascading_items_by_type[item_type]})
        db_map_data = {self._db_map: cascading_items_by_type[item_type]}
        if callback is not None:
            callback(db_map_data)
        self._db_mngr.items_updated.emit(item_type, db_map_data)

    def remove_items(self, ids_per_type, callback):
        """Removes items from database.

        Args:
            ids_per_type (dict): lists of items to remove keyed by item type (str)
        """
        self._executor.submit(self._remove_items, ids_per_type, callback)

    @busy_effect
    def _remove_items(self, ids_per_type, callback):
        try:
            self._db_map.remove_items(**ids_per_type)
            errors = []
        except SpineDBAPIError as err:
            errors = [err]
        if not errors:
            for item_type, ids in ids_per_type.items():
                removed_ids = self._removed_ids.setdefault(item_type, set())
                removed_ids |= ids
        else:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        self._something_happened.emit(_Event.REMOVE_ITEMS, (ids_per_type, errors, callback))

    def _remove_items_event(self, ids_per_type, errors, callback):
        items_per_type = {}
        for item_type, ids in ids_per_type.items():
            if not ids:
                continue
            items = items_per_type[item_type] = [
                x for x in (self._db_mngr.get_item(self._db_map, item_type, id_) for id_ in ids) if x
            ]
            cascading_ids_by_type = self._db_mngr.special_cascading_ids(self._db_map, item_type, ids)
            self._db_mngr.uncache_removed_items({self._db_map: {item_type: ids}})
            self._call_in_parents("handle_items_removed", item_type, items)
            self._do_update_special_refs(cascading_ids_by_type, fill_missing=False)
        db_map_typed_data = {self._db_map: items_per_type}
        if callback is not None:
            callback(db_map_typed_data)
        self._db_mngr.items_removed.emit(db_map_typed_data)

    def commit_session(self, commit_msg, cookie=None):
        """Initiates commit session.

        Args:
            commit_msg (str): commit message
            cookie (Any): a cookie to include in session_committed signal
        """
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._executor.submit(self._commit_session, commit_msg, undo_stack, cookie)

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
        self._something_happened.emit(_Event.COMMIT_SESSION, (errors, undo_stack, cookie))

    def _commit_session_event(self, errors, undo_stack, cookie):
        undo_stack.setClean()
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        else:
            self._db_mngr.session_committed.emit({self._db_map}, cookie)

    def rollback_session(self):
        """Initiates rollback session action for given database maps in the worker thread."""
        # Make sure that the worker thread has a reference to undo stacks even if they get deleted
        # in the GUI thread.
        undo_stack = self._db_mngr.undo_stack[self._db_map]
        self._executor.submit(self._rollback_session, undo_stack)

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
        if not errors:
            self._removed_ids.clear()
        self._something_happened.emit(_Event.ROLLBACK_SESSION, (errors, undo_stack))

    def _rollback_session_event(self, errors, undo_stack):
        undo_stack.setClean()
        if errors:
            self._db_mngr.error_msg.emit({self._db_map: errors})
        else:
            self._db_mngr.session_rolled_back.emit({self._db_map})
