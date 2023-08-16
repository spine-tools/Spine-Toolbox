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
"""

from PySide6.QtCore import QTimer, Signal, QObject
from .helpers import busy_effect


class FetchParent(QObject):
    """
    Attrs:
        fetch_token (int or None)
        will_have_children (bool or None): Whether this parent will have children if fetched.
        None means we don't know yet. Set to a boolean value whenever we find out.
    """

    _changes_pending = Signal()

    def __init__(self, owner=None, chunk_size=1000):
        """
        Args:
            owner (object): somebody who owns this FetchParent. If it's a QObject instance, then this FetchParent
            becomes obsolete whenever the owner is destroyed
            chunk_size (int or None): the number of items this parent should be happy with fetching at a time.
            If None, then no limit is imposed and the parent should fetch the entire contents of the DB.
        """
        super().__init__()
        self._timer = QTimer()
        self._items_to_add = {}
        self._items_to_update = {}
        self._items_to_remove = {}
        self._obsolete = False
        self._fetched = False
        self._busy = False
        self._position = {}
        self.fetch_token = None
        self.will_have_children = None
        self._timer.setSingleShot(True)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._apply_pending_changes)
        self._changes_pending.connect(self._timer.start)
        self._owner = owner
        if isinstance(self._owner, QObject):
            self._owner.destroyed.connect(lambda obj=None: self.set_obsolete(True))
        self.chunk_size = chunk_size

    def reset_fetching(self, fetch_token):
        """Resets fetch parent as if nothing was ever fetched.

        Args:
            fetch_token (object): current fetch token
        """
        if self.is_obsolete:
            return
        self._timer.stop()
        self._items_to_add.clear()
        self._items_to_update.clear()
        self._items_to_remove.clear()
        self._fetched = False
        self._busy = False
        self._position.clear()
        self.fetch_token = fetch_token
        self.will_have_children = None
        self.will_have_children_change()

    def position(self, db_map):
        return self._position.setdefault(db_map, 0)

    def increment_position(self, db_map):
        self._position[db_map] += 1

    @busy_effect
    def _apply_pending_changes(self):
        if self.is_obsolete:
            return
        for db_map in list(self._items_to_add):
            data = self._items_to_add.pop(db_map)
            self.handle_items_added({db_map: data})
        for db_map in list(self._items_to_update):
            data = self._items_to_update.pop(db_map)
            self.handle_items_updated({db_map: data})
        for db_map in list(self._items_to_remove):
            data = self._items_to_remove.pop(db_map)
            self.handle_items_removed({db_map: data})
        QTimer.singleShot(0, lambda: self.set_busy(False))

    def add_item(self, item, db_map):
        self._items_to_add.setdefault(db_map, []).append(item)
        self._changes_pending.emit()

    def update_item(self, item, db_map):
        self._items_to_update.setdefault(db_map, []).append(item)
        self._changes_pending.emit()

    def remove_item(self, item, db_map):
        self._items_to_remove.setdefault(db_map, []).append(item)
        self._changes_pending.emit()

    @property
    def fetch_item_type(self):
        """Returns the type of item to fetch, e.g., "object_class".

        Returns:
            str
        """
        raise NotImplementedError()

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

    def will_have_children_change(self):
        """Called when the will_have_children property changes."""

    @property
    def is_obsolete(self):
        return self._obsolete

    def set_obsolete(self, obsolete):
        """Sets the obsolete status.

        Args:
            obsolete (bool): whether parent has become obsolete
        """
        self._obsolete = obsolete

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
    def __init__(self, fetch_item_type, owner=None, chunk_size=1000):
        super().__init__(owner=owner, chunk_size=chunk_size)
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
        will_have_children_change=None,
        owner=None,
        chunk_size=1000,
    ):
        super().__init__(fetch_item_type, owner=owner, chunk_size=chunk_size)
        self._accepts_item = accepts_item
        self._shows_item = shows_item
        self._handle_items_added = handle_items_added
        self._handle_items_removed = handle_items_removed
        self._handle_items_updated = handle_items_updated
        self._will_have_children_change = will_have_children_change

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

    def will_have_children_change(self):
        if self._will_have_children_change is None:
            super().will_have_children_change()
        else:
            self._will_have_children_change()
