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
from PySide6.QtCore import QObject
from spinedb_api import DatabaseMapping
from spinetoolbox.fetch_parent import FetchParent
from spinetoolbox.helpers import bisect_chunks, order_key
from spinetoolbox.mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from spinetoolbox.spine_db_manager import SpineDBManager


class LazyFilterCheckboxListModel(SimpleFilterCheckboxListModel):
    """Extends SimpleFilterCheckboxListModel to allow for lazy loading in synch with another model."""

    def __init__(
        self,
        parent: QObject | None,
        db_mngr: SpineDBManager,
        db_maps: list[DatabaseMapping],
        fetch_parent: FetchParent,
        show_empty: bool = True,
    ):
        """
        Args:
            parent: parent object
            db_mngr: database manager
            db_maps: database maps
            fetch_parent: fetch parent
            show_empty: if True, show an empty row at the end of the list
        """
        super().__init__(parent, show_empty=show_empty)
        self._db_mngr = db_mngr
        self._db_maps = db_maps
        self._fetch_parent = fetch_parent

    def canFetchMore(self, _parent):
        result = False
        for db_map in self._db_maps:
            result |= self._db_mngr.can_fetch_more(db_map, self._fetch_parent)
        return result

    def fetchMore(self, _parent):
        for db_map in self._db_maps:
            self._db_mngr.fetch_more(db_map, self._fetch_parent)

    def _do_add_items(self, data):
        """Adds items so the list is always sorted, while assuming that both existing and new items are sorted."""
        for chunk, pos in bisect_chunks(self._data, data, key=lambda x: order_key(str(x))):
            self.beginInsertRows(self.index(0, 0), pos, pos + len(chunk) - 1)
            self._data[pos:pos] = chunk
            self.endInsertRows()
