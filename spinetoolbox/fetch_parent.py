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

"""The FetchParent and FlexibleFetchParent classes."""
from PySide6.QtCore import QTimer, Signal, QObject, Qt
from .helpers import busy_effect


class FetchParent(QObject):

    _changes_pending = Signal()

    def __init__(self, index=None, owner=None, chunk_size=1000):
        """
        Args:
            index (FetchIndex, optional): an index to speedup looking up fetched items
            owner (object, optional): somebody who owns this FetchParent.
                If it's a QObject instance, then this FetchParent becomes obsolete whenever the owner is destroyed
            chunk_size (int, optional): the number of items this parent should be happy with fetching at a time.
                If None, then no limit is imposed and the parent should fetch the entire contents of the DB.
        """
        super().__init__()
        self._version = 0
        self._restore_item_callbacks = {}
        self._update_item_callbacks = {}
        self._remove_item_callbacks = {}
        self._changes_by_db_map = {}
        self._obsolete = False
        self._fetched = False
        self._busy = False
        self._position = {}
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._apply_pending_changes)
        self._changes_pending.connect(self._timer.start)
        self._index = index
        self._owner = owner
        if isinstance(self._owner, QObject):
            self._owner.destroyed.connect(lambda obj=None: self.set_obsolete(True))
            self.setParent(self._owner)
        self.chunk_size = chunk_size

    def apply_changes_immediately(self):
        # For tests
        self._changes_pending.connect(self._apply_pending_changes, Qt.UniqueConnection)

    @property
    def index(self):
        return self._index

    def reset(self):
        """Resets fetch parent as if nothing was ever fetched."""
        if self.is_obsolete:
            return
        self._version += 1
        self._restore_item_callbacks.clear()
        self._update_item_callbacks.clear()
        self._remove_item_callbacks.clear()
        self._timer.stop()
        self._changes_by_db_map.clear()
        self._fetched = False
        self._busy = False
        self._position.clear()
        if self.index is not None:
            self.index.reset()

    def position(self, db_map):
        return self._position.setdefault(db_map, 0)

    def increment_position(self, db_map):
        self._position[db_map] += 1

    @busy_effect
    def _apply_pending_changes(self):
        if self.is_obsolete:
            return
        for db_map in list(self._changes_by_db_map):
            changes = self._changes_by_db_map.pop(db_map)
            last_handler = None
            items = []
            for handler, item in changes:
                if handler == last_handler:
                    items.append(item)
                    continue
                if items:
                    last_handler({db_map: items})  # pylint: disable=not-callable
                items = [item]
                last_handler = handler
            last_handler({db_map: items})
        QTimer.singleShot(0, lambda: self.set_busy(False))

    def bind_item(self, item, db_map):
        # NOTE: If `item` is in the process of calling callbacks in another thread,
        # the ones added below won't be called.
        # So, it is important to call this function before self.add_item()
        item.add_restore_callback(self._make_restore_item_callback(db_map))
        item.add_update_callback(self._make_update_item_callback(db_map))
        item.add_remove_callback(self._make_remove_item_callback(db_map))

    def _make_restore_item_callback(self, db_map):
        if db_map not in self._restore_item_callbacks:
            self._restore_item_callbacks[db_map] = _ItemCallback(self.add_item, db_map, self._version)
        return self._restore_item_callbacks[db_map]

    def _make_update_item_callback(self, db_map):
        if db_map not in self._update_item_callbacks:
            self._update_item_callbacks[db_map] = _ItemCallback(self.update_item, db_map, self._version)
        return self._update_item_callbacks[db_map]

    def _make_remove_item_callback(self, db_map):
        if db_map not in self._remove_item_callbacks:
            self._remove_item_callbacks[db_map] = _ItemCallback(self.remove_item, db_map, self._version)
        return self._remove_item_callbacks[db_map]

    def _is_valid(self, version):
        return (version is None or version == self._version) and not self.is_obsolete

    def _change_item(self, handler, item, db_map, version):
        if not self._is_valid(version):
            return False
        self._changes_by_db_map.setdefault(db_map, []).append((handler, item))
        self._changes_pending.emit()
        return True

    def add_item(self, item, db_map, version=None):
        return self._change_item(self.handle_items_added, item, db_map, version)

    def update_item(self, item, db_map, version=None):
        return self._change_item(self.handle_items_updated, item, db_map, version)

    def remove_item(self, item, db_map, version=None):
        return self._change_item(self.handle_items_removed, item, db_map, version)

    @property
    def fetch_item_type(self):
        """Returns the DB item type to fetch, e.g., "entity_class".

        Returns:
            str
        """
        raise NotImplementedError()

    def key_for_index(self, db_map):
        """Returns the key for this parent in the index.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            any
        """
        return None

    # pylint: disable=no-self-use
    def accepts_item(self, item, db_map):
        """Called by the associated SpineDBWorker whenever items are fetched and also added/updated/removed.
        Returns whether this parent accepts that item as a children.

        In case of modifications, the SpineDBWorker will call one or more of ``handle_items_added()``,
        ``handle_items_updated()``, or ``handle_items_removed()`` with all the items that pass this test.

        Args:
            item (dict): The item
            db_map (DiffDatabaseMapping)

        Returns:
            bool
        """
        return True

    # pylint: disable=no-self-use
    def shows_item(self, item, db_map):
        """Called by the associated SpineDBWorker whenever items are fetched and accepted.
        Returns whether this parent will show this item to the user.

        Args:
            item (dict): The item
            db_map (DiffDatabaseMapping)

        Returns:
            bool
        """
        return True

    @property
    def is_obsolete(self):
        return self._obsolete

    def set_obsolete(self, obsolete):
        """Sets the obsolete status.

        Args:
            obsolete (bool): whether parent has become obsolete
        """
        if obsolete:
            self.set_busy(False)
        self._obsolete = obsolete

    @property
    def is_fetched(self):
        return self._fetched

    def set_fetched(self, fetched):
        """Sets the fetched status.

        Args:
            fetched (bool): whether parent has been fetched completely
        """
        if fetched:
            self.set_busy(False)
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
    def __init__(self, fetch_item_type, index=None, owner=None, chunk_size=1000):
        super().__init__(index=index, owner=owner, chunk_size=chunk_size)
        self._fetch_item_type = fetch_item_type

    @property
    def fetch_item_type(self):
        return self._fetch_item_type

    @fetch_item_type.setter
    def fetch_item_type(self, fetch_item_type):
        self._fetch_item_type = fetch_item_type

    def handle_items_added(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_removed(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_updated(self, db_map_data):
        raise NotImplementedError(self.fetch_item_type)

    def __str__(self):
        return f"{super().__str__()} fetching {self.fetch_item_type} items owned by {self._owner}"


class FlexibleFetchParent(ItemTypeFetchParent):
    def __init__(
        self,
        fetch_item_type,
        handle_items_added=None,
        handle_items_removed=None,
        handle_items_updated=None,
        accepts_item=None,
        shows_item=None,
        key_for_index=None,
        index=None,
        owner=None,
        chunk_size=1000,
    ):
        super().__init__(fetch_item_type, index=index, owner=owner, chunk_size=chunk_size)
        self._handle_items_added = handle_items_added
        self._handle_items_removed = handle_items_removed
        self._handle_items_updated = handle_items_updated
        self._accepts_item = accepts_item
        self._shows_item = shows_item
        self._key_for_index = key_for_index

    def key_for_index(self, db_map):
        if self._key_for_index is None:
            return None
        return self._key_for_index(db_map)

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

    def shows_item(self, item, db_map):
        if self._shows_item is None:
            return super().shows_item(item, db_map)
        return self._shows_item(item, db_map)


class FetchIndex(dict):
    def __init__(self):
        super().__init__()
        self._position = {}

    def reset(self):
        self._position.clear()
        self.clear()

    def process_item(self, item, db_map):
        raise NotImplementedError()

    def position(self, db_map):
        return self._position.setdefault(db_map, 0)

    def increment_position(self, db_map):
        self._position[db_map] += 1

    def get_items(self, key, db_map):
        return self.get(db_map, {}).get(key, [])


class _ItemCallback:
    def __init__(self, fn, *args):
        self._fn = fn
        self._args = args

    def __call__(self, item):
        return self._fn(item, *self._args)

    def __str__(self):
        return str(self._fn) + " with " + str(self._args)
