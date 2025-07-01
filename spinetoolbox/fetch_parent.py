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
from __future__ import annotations
from collections.abc import Callable, Hashable
from contextlib import suppress
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from spinedb_api import DatabaseMapping
from spinedb_api.db_mapping_base import MappedItemBase, PublicItem
from spinedb_api.temp_id import TempId
from .helpers import busy_effect

if TYPE_CHECKING:
    from .spine_db_manager import SpineDBManager


DBMapMixedItems = dict[DatabaseMapping, list[MappedItemBase | PublicItem]]


class FetchParent(QObject):

    _changes_pending = Signal()

    def __init__(self, index: Optional[FetchIndex] = None, owner: Optional[object] = None, chunk_size: int = 1000):
        """
        Args:
            index: an index to speedup looking up fetched items
            owner  somebody who owns this FetchParent.
                If it's a QObject instance, then this FetchParent becomes obsolete whenever the owner is destroyed
            chunk_size: the number of items this parent should be happy with fetching at a time.
                If None, then no limit is imposed and the parent should fetch the entire contents of the DB.
        """
        super().__init__()
        self._version = 0
        self._restore_item_callbacks: dict[DatabaseMapping, _ItemCallback] = {}
        self._update_item_callbacks: dict[DatabaseMapping, _ItemCallback] = {}
        self._remove_item_callbacks: dict[DatabaseMapping, _ItemCallback] = {}
        self._changes_by_db_map: dict[
            DatabaseMapping, list[tuple[Callable[[DBMapMixedItems], None], MappedItemBase | PublicItem]]
        ] = {}
        self._obsolete = False
        self._fetched = False
        self._busy = False
        self._position: dict[DatabaseMapping, int] = {}
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

    def apply_changes_immediately(self) -> None:
        # For tests
        self._changes_pending.connect(self._apply_pending_changes, Qt.ConnectionType.UniqueConnection)

    @property
    def index(self) -> Optional[FetchIndex]:
        return self._index

    def reset(self) -> None:
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

    def position(self, db_map: DatabaseMapping) -> int:
        return self._position.setdefault(db_map, 0)

    def increment_position(self, db_map: DatabaseMapping) -> None:
        self._position[db_map] += 1

    @busy_effect
    def _apply_pending_changes(self) -> None:
        if self.is_obsolete:
            return
        while self._changes_by_db_map:
            db_map, changes = self._changes_by_db_map.popitem()
            last_handler = None
            items = []
            for handler, item in changes:
                if handler is last_handler:
                    items.append(item)
                    continue
                if items:
                    last_handler({db_map: items})  # pylint: disable=not-callable
                items = [item]
                last_handler = handler
            last_handler({db_map: items})
        QTimer.singleShot(0, lambda: self.set_busy(False))

    def bind_item(self, item: PublicItem, db_map: DatabaseMapping) -> None:
        # NOTE: If `item` is in the process of calling callbacks in another thread,
        # the ones added below won't be called.
        # So, it is important to call this function before self.add_item()
        item.add_restore_callback(self._make_restore_item_callback(db_map))
        item.add_update_callback(self._make_update_item_callback(db_map))
        item.add_remove_callback(self._make_remove_item_callback(db_map))

    def _make_restore_item_callback(self, db_map: DatabaseMapping) -> _ItemCallback:
        if db_map not in self._restore_item_callbacks:
            self._restore_item_callbacks[db_map] = _ItemCallback(self.add_item, db_map, self._version)
        return self._restore_item_callbacks[db_map]

    def _make_update_item_callback(self, db_map: DatabaseMapping) -> _ItemCallback:
        if db_map not in self._update_item_callbacks:
            self._update_item_callbacks[db_map] = _ItemCallback(self.update_item, db_map, self._version)
        return self._update_item_callbacks[db_map]

    def _make_remove_item_callback(self, db_map: DatabaseMapping) -> _ItemCallback:
        if db_map not in self._remove_item_callbacks:
            self._remove_item_callbacks[db_map] = _ItemCallback(self.remove_item, db_map, self._version)
        return self._remove_item_callbacks[db_map]

    def _is_valid(self, version: Optional[int]) -> bool:
        return (version is None or version == self._version) and not self.is_obsolete

    def _change_item(
        self,
        handler: Callable[[DBMapMixedItems], None],
        item: MappedItemBase | PublicItem,
        db_map: DatabaseMapping,
        version: Optional[int],
    ) -> bool:
        if not self._is_valid(version):
            return False
        self._changes_by_db_map.setdefault(db_map, []).append((handler, item))
        self._changes_pending.emit()
        return True

    def add_item(self, item: MappedItemBase, db_map: DatabaseMapping, version: Optional[int] = None) -> bool:
        return self._change_item(self.handle_items_added, item, db_map, version)

    def update_item(self, item: MappedItemBase, db_map: DatabaseMapping, version=None) -> bool:
        return self._change_item(self.handle_items_updated, item, db_map, version)

    def remove_item(self, item: MappedItemBase, db_map: DatabaseMapping, version=None) -> bool:
        return self._change_item(self.handle_items_removed, item, db_map, version)

    @property
    def fetch_item_type(self) -> str:
        """Returns the DB item type to fetch, e.g., "entity_class"."""
        raise NotImplementedError()

    def key_for_index(self, db_map: DatabaseMapping) -> Optional[TempId]:
        """Returns the key for this parent in the index."""
        return None

    def accepts_item(self, item: MappedItemBase | PublicItem, db_map: DatabaseMapping) -> bool:
        """Called by the associated SpineDBWorker whenever items are fetched and also added/updated/removed.
        Returns whether this parent accepts that item as a children.

        In case of modifications, the SpineDBWorker will call one or more of ``handle_items_added()``,
        ``handle_items_updated()``, or ``handle_items_removed()`` with all the items that pass this test.
        """
        return True

    def shows_item(self, item: MappedItemBase | PublicItem, db_map: DatabaseMapping) -> bool:
        """Called by the associated SpineDBWorker whenever items are fetched and accepted.
        Returns whether this parent will show this item to the user.
        """
        return True

    @property
    def is_obsolete(self) -> bool:
        return self._obsolete

    def set_obsolete(self, obsolete: bool) -> None:
        """Sets the obsolete status.

        Args:
            obsolete: whether parent has become obsolete
        """
        if obsolete:
            self.set_busy(False)
        self._obsolete = obsolete

    @property
    def is_fetched(self) -> bool:
        return self._fetched

    def set_fetched(self, fetched: bool) -> None:
        """Sets the fetched status.

        Args:
            fetched: whether parent has been fetched completely
        """
        if fetched:
            self.set_busy(False)
        self._fetched = fetched

    @property
    def is_busy(self) -> bool:
        return self._busy

    def set_busy(self, busy: bool) -> None:
        """Sets the busy status.

        Args:
            busy: whether parent is busy fetching
        """
        self._busy = busy

    def handle_items_added(self, db_map_data: DBMapMixedItems) -> None:
        """
        Called by SpineDBWorker when items are added to the DB.

        Args:
            db_map_data: Mapping DatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_removed(self, db_map_data: DBMapMixedItems) -> None:
        """
        Called by SpineDBWorker when items are removed from the DB.

        Args:
            db_map_data: Mapping DatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_updated(self, db_map_data: DBMapMixedItems) -> None:
        """
        Called by SpineDBWorker when items are updated in the DB.

        Args:
            db_map_data: Mapping DatabaseMapping instances to list of dict-items for which
                ``accepts_item()`` returns True.
        """
        raise NotImplementedError(self.fetch_item_type)


class ItemTypeFetchParent(FetchParent):
    def __init__(
        self,
        fetch_item_type: str,
        index: Optional[FetchIndex] = None,
        owner: Optional[object] = None,
        chunk_size: int = 1000,
    ):
        super().__init__(index=index, owner=owner, chunk_size=chunk_size)
        self._fetch_item_type = fetch_item_type

    @property
    def fetch_item_type(self) -> str:
        return self._fetch_item_type

    @fetch_item_type.setter
    def fetch_item_type(self, fetch_item_type: str) -> None:
        self._fetch_item_type = fetch_item_type

    def handle_items_added(self, db_map_data: DBMapMixedItems) -> None:
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_removed(self, db_map_data: DBMapMixedItems) -> None:
        raise NotImplementedError(self.fetch_item_type)

    def handle_items_updated(self, db_map_data: DBMapMixedItems) -> None:
        raise NotImplementedError(self.fetch_item_type)

    def __str__(self):
        return f"{super().__str__()} fetching {self.fetch_item_type} items owned by {self._owner}"


class FlexibleFetchParent(ItemTypeFetchParent):
    def __init__(
        self,
        fetch_item_type: str,
        handle_items_added: Optional[Callable[[DBMapMixedItems], None]] = None,
        handle_items_removed: Optional[Callable[[DBMapMixedItems], None]] = None,
        handle_items_updated: Optional[Callable[[DBMapMixedItems], None]] = None,
        accepts_item: Optional[Callable[[MappedItemBase | PublicItem, DatabaseMapping], bool]] = None,
        shows_item: Optional[Callable[[MappedItemBase | PublicItem, DatabaseMapping], bool]] = None,
        key_for_index: Optional[Callable[[DatabaseMapping], TempId]] = None,
        index: Optional[FetchIndex] = None,
        owner: Optional[object] = None,
        chunk_size: int = 1000,
    ):
        super().__init__(fetch_item_type, index=index, owner=owner, chunk_size=chunk_size)
        self._handle_items_added = handle_items_added
        self._handle_items_removed = handle_items_removed
        self._handle_items_updated = handle_items_updated
        self._accepts_item = accepts_item
        self._shows_item = shows_item
        self._key_for_index = key_for_index

    def key_for_index(self, db_map: DatabaseMapping) -> Optional[TempId]:
        if self._key_for_index is None:
            return None
        return self._key_for_index(db_map)

    def handle_items_added(self, db_map_data: DBMapMixedItems) -> None:
        if self._handle_items_added is None:
            return
        self._handle_items_added(db_map_data)

    def handle_items_removed(self, db_map_data: DBMapMixedItems) -> None:
        if self._handle_items_removed is None:
            return
        self._handle_items_removed(db_map_data)

    def handle_items_updated(self, db_map_data: DBMapMixedItems) -> None:
        if self._handle_items_updated is None:
            return
        self._handle_items_updated(db_map_data)

    def accepts_item(self, item: MappedItemBase | PublicItem, db_map: DatabaseMapping) -> bool:
        if self._accepts_item is None:
            return super().accepts_item(item, db_map)
        return self._accepts_item(item, db_map)

    def shows_item(self, item: MappedItemBase | PublicItem, db_map: DatabaseMapping) -> bool:
        if self._shows_item is None:
            return super().shows_item(item, db_map)
        return self._shows_item(item, db_map)


class FetchIndex(dict[DatabaseMapping, dict[Hashable, list[MappedItemBase | PublicItem]]]):
    def __init__(self):
        super().__init__()
        self._position: dict[DatabaseMapping, int] = {}
        self._connected_to_db_mngr = False

    def connect(self, db_mngr: SpineDBManager) -> None:
        if self._connected_to_db_mngr:
            return
        db_mngr.database_reset.connect(self.reset)
        self._connected_to_db_mngr = True

    @Slot(object)
    def reset(self, db_map: DatabaseMapping) -> None:
        with suppress(KeyError):
            del self._position[db_map]
        with suppress(KeyError):
            del self[db_map]

    def process_item(self, item: MappedItemBase | PublicItem, db_map: DatabaseMapping) -> None:
        raise NotImplementedError()

    def position(self, db_map: DatabaseMapping) -> int:
        return self._position.setdefault(db_map, 0)

    def increment_position(self, db_map: DatabaseMapping) -> None:
        self._position[db_map] += 1

    def get_items(self, key: Hashable, db_map: DatabaseMapping) -> list[MappedItemBase | PublicItem]:
        return self.get(db_map, {}).get(key, [])


class _ItemCallback:
    def __init__(self, fn: Callable[[MappedItemBase, ...], bool], *args):
        self._fn = fn
        self._args = args

    def __call__(self, item: MappedItemBase) -> bool:
        return self._fn(item, *self._args)

    def __str__(self):
        return str(self._fn) + " with " + str(self._args)
