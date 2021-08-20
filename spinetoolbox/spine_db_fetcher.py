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
from PySide2.QtCore import Signal, Slot, QObject
from spinetoolbox.helpers import busy_effect, signal_waiter, CacheItem

# FIXME: We need to invalidate cache here as user makes changes (update, remove)


class SpineDBFetcher(QObject):
    """Fetches content from a Spine database."""

    _fetch_more_requested = Signal(str, object)
    _fetch_all_requested = Signal()
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
        self._getters = {
            "object_class": self._db_mngr.get_object_classes,
            "relationship_class": self._db_mngr.get_relationship_classes,
            "parameter_definition": self._db_mngr.get_parameter_definitions,
            "object": self._db_mngr.get_objects,
            "relationship": self._db_mngr.get_relationships,
            "entity_group": self._db_mngr.get_entity_groups,
            "parameter_value": self._db_mngr.get_parameter_values,
            "parameter_value_list": self._db_mngr.get_parameter_value_lists,
            "alternative": self._db_mngr.get_alternatives,
            "scenario": self._db_mngr.get_scenarios,
            "scenario_alternative": self._db_mngr.get_scenario_alternatives,
            "feature": self._db_mngr.get_features,
            "tool": self._db_mngr.get_tools,
            "tool_feature": self._db_mngr.get_tool_features,
            "tool_feature_method": self._db_mngr.get_tool_feature_methods,
        }
        self._iterators = {item_type: getter(self._db_map) for item_type, getter in self._getters.items()}
        self._fetched = {item_type: False for item_type in self._getters}
        self.cache = {}
        self._can_fetch_more_cache = {}
        self.moveToThread(db_mngr.worker_thread)
        self._fetch_more_requested.connect(self._fetch_more)
        self._fetch_all_requested.connect(self._fetch_all)

    def cache_items(self, item_type, items):
        self.cache.setdefault(item_type, {}).update({x["id"]: CacheItem(**x) for x in items})

    def get_item(self, item_type, id_):
        return self.cache.get(item_type, {}).get(id_, {})

    def can_fetch_more(self, item_type, success_cond=None):
        if success_cond is None:
            success_cond = lambda _: True
        if not self._fetched[item_type]:
            return True
        items = self.cache.get(item_type, {})
        key = (next(reversed(items), None), len(items))
        cache_key, cache_result = self._can_fetch_more_cache.get((item_type, success_cond), (None, None))
        if key == cache_key:
            return cache_result
        result = any(success_cond(x) for x in items.values())
        self._can_fetch_more_cache[item_type, success_cond] = (key, result)
        return result

    @busy_effect
    def fetch_more(self, item_type, success_cond=None, iter_chunk_size=1000):
        """Fetches items from the database.

        Args:
            item_type (str): the type of items to fetch, e.g. "object_class"
        """
        if not self.can_fetch_more(item_type):
            return
        if success_cond is None:
            success_cond = lambda _: True
        items = self.cache.get(item_type, {})
        args = [iter(items)] * iter_chunk_size
        for keys in itertools.zip_longest(*args):
            keys = set(keys) - {None}  # Remove fillvalues
            chunk = [items[k] for k in keys]
            if any(success_cond(x) for x in chunk):
                for k in keys:
                    del items[k]
                signal = self._db_mngr.added_signals.get(item_type)
                signal.emit({self._db_map: chunk})
                return
        self._fetch_more_requested.emit(item_type, success_cond)

    @Slot(str, object)
    def _fetch_more(self, item_type, success_cond):
        self._do_fetch_more(item_type, success_cond)

    @busy_effect
    def _do_fetch_more(self, item_type, success_cond):
        iterator = self._iterators.get(item_type)
        if iterator is None:
            return
        while True:
            chunk = next(iterator, [])
            if not chunk:
                self._fetched[item_type] = True
                break
            if any(success_cond(x) for x in chunk):
                signal = self._db_mngr.added_signals.get(item_type)
                signal.emit({self._db_map: chunk})
                break
            self.cache_items(item_type, chunk)

    def fetch_all(self):
        if not any(self.can_fetch_more(item_type) for item_type in self._fetched):
            return
        with signal_waiter(self._fetch_all_finished) as waiter:
            self._fetch_all_requested.emit()
            waiter.wait()

    @Slot()
    def _fetch_all(self):
        self._do_fetch_all()

    @busy_effect
    def _do_fetch_all(self):
        for item_type in self._getters:
            self._do_fetch_more(item_type, lambda _: False)
        self._fetch_all_finished.emit()
