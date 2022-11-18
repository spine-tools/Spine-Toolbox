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
The FetchParent and FlexibleFetchParent classes.

:authors: M. Marin (ER) and A. Soininen (VTT)
:date:   18.11.2022
"""


class FetchParent:
    _CHUNK_SIZE = 1000
    _worker = None
    _fetched = False
    _busy = False
    position = 0
    fetch_token = None
    will_have_children = None
    """Whether this parent will have children if fetched.
    None means we don't know yet. Set to a boolean value whenever we find out.
    """

    @property
    def fetch_item_type(self):
        """Returns the type of item to fetch, e.g., "object_class".
        Used to create an initial query for this item.

        Returns:
            str
        """
        raise NotImplementedError()

    def bind_worker(self, worker):
        self._worker = worker

    def _next_chunk(self):
        """Produces the next chunk of items by iterating the worker's cache.
        If nothing found, then schedules a progression of the worker's query so more items can be found in the future.

        Yields:
            dict
        """
        k = 0
        for item in self._worker.iterate_cache(self):
            yield item
            k += 1
            if k == self._CHUNK_SIZE:
                return
        if not self.is_fetched and k == 0:
            self._worker.advance_query(self)

    def __next__(self):
        return list(self._next_chunk())

    def __iter__(self):
        return self

    # pylint: disable=no-self-use
    def accepts_item(self, item, db_map):
        """Called by the associated SpineDBWorker whenever items are fetched and also added/updated/removed.
        Returns whether this parent should accept that item as a children.

        In case of modifications, the SpineDBWorker will call one or more of ``handle_items_added()``,
        ``handle_items_updated()``, or ``handle_items_removed()`` with all the items that pass this test.

        Args:
            item (dict): The item
            db_map (DiffDatabaseMapping)

        Returns:
            bool
        """
        return True

    def will_have_children_change(self):
        """Called when the will_have_children property changes."""

    @property
    def is_fetched(self):
        return self._fetched

    def set_fetched(self, fetched):
        """Sets the fetched status.

        Args:
            fetched (bool): whether parent has been fetched completely
        """
        self._fetched = fetched

    @property
    def is_busy(self):
        return self._busy

    def set_busy(self, busy):
        """Sets the busy status.

        Args:
            busy (bool): whether parent is busy fetching
        """
        self._busy = busy

    def reset_fetching(self, fetch_token):
        """Resets fetch parent as if nothing was ever fetched.

        Args:
            fetch_token (object): current fetch token
        """
        self._worker = None
        self._fetched = False
        self._busy = False
        self.position = 0
        self.fetch_token = fetch_token
        self.will_have_children = None
        self.will_have_children_change()

    def handle_items_added(self, db_map_data):
        """
        Called by SpineDBWorker when items are added to the DB.

        Args:
            db_map_data (dict): Mapping DiffDatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_removed(self, db_map_data):
        """
        Called by SpineDBWorker when items are removed from the DB.

        Args:
            db_map_data (dict): Mapping DiffDatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_updated(self, db_map_data):
        """
        Called by SpineDBWorker when items are updated in the DB.

        Args:
            db_map_data (dict): Mapping DiffDatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)


class ItemTypeFetchParent(FetchParent):
    def __init__(self, fetch_item_type):
        super().__init__()
        self._fetch_item_type = fetch_item_type

    @property
    def fetch_item_type(self):
        return self._fetch_item_type

    def handle_items_added(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_removed(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_updated(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)


class FlexibleFetchParent(ItemTypeFetchParent):
    def __init__(
        self,
        fetch_item_type,
        handle_items_added=None,
        handle_items_removed=None,
        handle_items_updated=None,
        accepts_item=None,
    ):
        super().__init__(fetch_item_type)
        self._accepts_item = accepts_item
        self._handle_items_added = handle_items_added
        self._handle_items_removed = handle_items_removed
        self._handle_items_updated = handle_items_updated

    def handle_items_added(self, db_map_data):
        if self._handle_items_added is None:
            return
        self._handle_items_added(db_map_data)

    def handle_items_removed(self, db_map_data):
        if self._handle_items_removed is None:
            return
        self._handle_items_removed(db_map_data)

    def handle_items_updated(self, db_map_data):
        if self._handle_items_updated is None:
            return
        self._handle_items_updated(db_map_data)

    def accepts_item(self, item, db_map):
        if self._accepts_item is None:
            return super().accepts_item(item, db_map)
        return self._accepts_item(item, db_map)
