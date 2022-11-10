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
from .helpers import busy_effect, separate_metadata_and_item_metadata, FetchParent
from .qthread_pool_executor import QtBasedThreadPoolExecutor


@unique
class _Event(Enum):
    FETCH = auto()
    FETCH_STATUS_CHANGE = auto()
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


class SpineDBWorker(QObject):
    """Does all the communication with a certain DB for SpineDBManager, in a non-GUI thread."""

    _something_happened = Signal(object, tuple)

    def __init__(self, db_mngr, db_url):
        super().__init__()
        self._parents_by_type = {}
        self._db_mngr = db_mngr
        self._db_url = db_url
        self._db_map = None
        self._current_fetch_token = 0
        self._removed_ids = {}
        self._query_has_elements_by_key = {}
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
            _Event.FETCH: self._fetch_event,
            _Event.FETCH_STATUS_CHANGE: self._fetch_status_change_event,
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
        self._fetched_item_types.clear()
        self._query_has_elements_by_key.clear()
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

    def can_fetch_more(self, parent):
        """Returns whether more data can be fetched for parent.
        Also, registers the parent to notify it of any relevant DB modifications later on.

        Args:
            parent (FetchParent): fetch parent

        Returns:
            bool: True if more data is available, False otherwise
        """
        self._parents_by_type.setdefault(parent.fetch_item_type, set()).add(parent)
        self._reset_fetching_if_required(parent)
        if parent.is_fetched or parent.is_busy_fetching:
            return False
        if parent.query_initialized == FetchParent.Init.UNINITIALIZED:
            parent.query_initialized = FetchParent.Init.IN_PROGRESS
            self._executor.submit(self._init_query, parent)
            return True
        if parent.query_initialized == FetchParent.Init.IN_PROGRESS:
            return True
        if parent.query_initialized == FetchParent.Init.FAILED:
            return False
        return self._query_has_elements(parent)

    @busy_effect
    def _init_query(self, parent):
        """Initializes query for parent.

        Args:
            parent (FetchParent): fetch parent
        """
        lock = self._db_mngr.db_map_locks.get(self._db_map)
        if lock is None or not lock.tryLock():
            parent.query_initialized = FetchParent.Init.FAILED
            return
        try:
            self._setdefault_query(parent)
            if not self._query_has_elements(parent):
                parent.set_fetched(True)
                self._something_happened.emit(_Event.FETCH_STATUS_CHANGE, (parent,))
        finally:
            parent.query_initialized = FetchParent.Init.FINISHED
            lock.unlock()

    @staticmethod
    def _fetch_status_change_event(parent):
        parent.fetch_status_change()

    def _setdefault_query(self, parent):
        """Creates a query for parent. Stores both the query and whether it has elements.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent.query is None:
            parent.query = self._make_query_for_parent(parent)
            self._setdefault_query_key(parent)
            if parent.query_key not in self._query_has_elements_by_key:
                self._query_has_elements_by_key[parent.query_key] = bool(parent.query.first())
        return parent.query

    def _query_has_elements(self, parent):
        """Checks whether query has something to return.

        Args:
            parent (FetchParent): fetch parent

        Returns:
            bool: True if query will give records, False otherwise
        """
        return self._query_has_elements_by_key[self._setdefault_query_key(parent)]

    @staticmethod
    def _setdefault_query_key(parent):
        """Returns parent's query key or creates and sets a new one if it doesn't exist.

        Args:
            parent (FetchParent): fetch parent

        Returns:
            str: query key
        """
        if parent.query_key is None:
            parent.query_key = str(parent.query.statement.compile(compile_kwargs={"literal_binds": True}))
        return parent.query_key

    def fetch_more(self, parent):
        """Fetches items from the database.

        Args:
            parent (FetchParent): fetch parent
        """
        if parent not in self._parents_by_type.get(parent.fetch_item_type, set()):
            raise RuntimeError(
                f"attempting to fetch unregistered parent {parent} - did you forget to call ``can_fetch_more()``"
            )
        self._reset_fetching_if_required(parent)
        parent.set_busy_fetching(True)
        self._executor.submit(self._fetch_more, parent)

    @busy_effect
    @_db_map_lock
    def _fetch_more(self, parent):
        iterator = self._get_iterator(parent)
        chunk = next(iterator, [])
        if chunk:
            more_available = True
            removed_ids = self._removed_ids.get(parent.fetch_item_type)
            if removed_ids is not None:
                chunk = [item for item in chunk if item["id"] not in removed_ids]
        else:
            more_available = False
        self._something_happened.emit(_Event.FETCH, (parent, chunk, more_available))

    def _fetch_event(self, parent, chunk, more_available):
        if chunk:
            db_map_data = {self._db_map: chunk}
            self._db_mngr.cache_items(parent.fetch_item_type, db_map_data)
            parent.handle_items_added(db_map_data)
        elif not more_available and parent.query is not None:
            parent.set_fetched(True)
        parent.set_busy_fetching(False)

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
        if not fetch_item_types:
            # FIXME: Needed? QCoreApplication.processEvents()
            return
        _ = self._executor.submit(self._fetch_all, fetch_item_types).result()

    @busy_effect
    @_db_map_lock
    def _fetch_all(self, item_types):
        for item_type in item_types:
            query, _ = self._make_query_for_item_type(item_type)
            if query is None:
                continue
            for chunk in _make_iterator(query):
                self._populate_commit_cache(item_type, chunk)
                self._db_mngr.cache_items(item_type, {self._db_map: chunk})
            self._fetched_item_types.add(item_type)

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
        try:
            subquery_name = self._db_map.cache_sqs[item_type]
        except KeyError:
            return None, None
        subquery = getattr(self._db_map, subquery_name)
        query = self._db_map.query(subquery)
        return query, subquery

    def _get_iterator(self, parent):
        if parent.query_iterator is None:
            # For some reason queries that haven't been iterated before don't
            # keep up with deleted items. Reset the query here as a workaround.
            parent.query = self._make_query_for_parent(parent)
            parent.query_iterator = _make_iterator(self._setdefault_query(parent))
        return parent.query_iterator

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

    def get_entity_metadata(self, entity_id):
        """Queries metadata records for a single entity synchronously.

        Args:
            entity_id (int): entity id

        Returns:
            list of namedtuple: entity metadata records
        """
        return self._executor.submit(self._get_entity_metadata, entity_id).result()

    def _get_entity_metadata(self, entity_id):
        """Queries metadata records for a single entity.

        Args:
            entity_id (int): entity id

        Returns:
            list of namedtuple: entity metadata records
        """
        sq = self._db_map.ext_entity_metadata_sq
        return self._db_map.query(sq).filter(sq.c.entity_id == entity_id).all()

    def get_parameter_value_metadata(self, parameter_value_id):
        """Queries metadata records for a single parameter value synchronously.

        Args:
            parameter_value_id (int): parameter value id

        Returns:
            list of namedtuple: parameter value metadata records
        """
        return self._executor.submit(self._get_parameter_value_metadata, parameter_value_id).result()

    def _get_parameter_value_metadata(self, parameter_value_id):
        """Queries metadata records for a single parameter value.

        Args:
            parameter_value_id (int): parameter value id

        Returns:
            list of namedtuple: parameter value metadata records
        """
        sq = self._db_map.ext_parameter_value_metadata_sq
        return self._db_map.query(sq).filter(sq.c.parameter_value_id == parameter_value_id).all()

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
        to_remove = set()
        for parent in self._parents_by_type.get(item_type, ()):
            children = [x for x in items if parent.accepts_item(x, self._db_map)]
            if not children:
                continue
            method = getattr(parent, method_name)
            method({self._db_map: children})
        for parent in to_remove:
            self._parents_by_type.get(parent.fetch_item_type).remove(parent)

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


def _make_iterator(query):
    """Runs the given query and yields results by chunks of given size.

    Args:
        query (Query): the query

    Yields:
        list: chunk of items
    """
    it = (x._asdict() for x in query.yield_per(_CHUNK_SIZE).enable_eagerloads(False))
    while True:
        chunk = list(itertools.islice(it, _CHUNK_SIZE))
        yield chunk
        if not chunk:
            break
