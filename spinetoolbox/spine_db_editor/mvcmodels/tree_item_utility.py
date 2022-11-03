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
A tree model for parameter_value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinetoolbox.mvcmodels.minimal_tree_model import TreeItem
from spinetoolbox.helpers import CharIconEngine, FetchParent, ItemTypeFetchParent, bisect_chunks


class StandardTreeItem(TreeItem):
    """A tree item that fetches their children as they are inserted."""

    @property
    def item_type(self):
        return None

    @property
    def db_mngr(self):
        return self.model.db_mngr

    @property
    def display_data(self):
        return None

    @property
    def icon_code(self):
        return None

    @property
    def tool_tip(self):
        return None

    @property
    def display_icon(self):
        if self.icon_code is None:
            return None
        engine = CharIconEngine(self.icon_code, 0)
        return QIcon(engine.pixmap())

    def data(self, column, role=Qt.DisplayRole):
        if column != 0:
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.display_data
        if role == Qt.DecorationRole:
            return self.display_icon
        if role == Qt.ToolTipRole:
            return self.tool_tip
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.DisplayRole):
        return False

    @property
    def non_empty_children(self):
        return self.children

    @property
    def children_ids(self):
        for child in self.non_empty_children:
            try:
                yield child.id
            except AttributeError:
                pass


class EditableMixin:
    def flags(self, column):
        """Makes items editable."""
        return Qt.ItemIsEditable | super().flags(column)


class GrayIfLastMixin:
    """Paints the item gray if it's the last."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and self.child_number() == self.parent_item.child_count() - 1:
            gray_color = QGuiApplication.palette().text().color()
            gray_color.setAlpha(128)
            gray_brush = QBrush(gray_color)
            return gray_brush
        return super().data(column, role)


class BoldTextMixin:
    """Bolds text."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(column, role)


class EmptyChildMixin:
    """Guarantees there's always an empty child."""

    @property
    def non_empty_children(self):
        return self.children[:-1]

    def empty_child(self):
        raise NotImplementedError()

    def _do_finalize(self):
        super()._do_finalize()
        empty_child = self.empty_child()
        self.append_children([empty_child])


class SortChildrenMixin:
    def _children_sort_key(self, child):
        return child.data(0)

    def insert_children_sorted(self, children):
        for child in children:
            child.parent_item = self
        for chunk, pos in bisect_chunks(self.non_empty_children, children, key=self._children_sort_key):
            if not super().insert_children(pos, chunk):
                return False
        return True


class CallbackFetchParent(ItemTypeFetchParent):
    def __init__(
        self,
        fetch_item_type,
        handle_items_added=None,
        handle_items_removed=None,
        handle_items_updated=None,
        filter_query=None,
        accepts_item=None,
    ):
        super().__init__(fetch_item_type)
        self._filter_query = filter_query if filter_query is not None else lambda qry, *args: qry
        self._accepts_item = accepts_item if accepts_item is not None else lambda *args: True
        self._handle_items_added = handle_items_added if handle_items_added is not None else lambda db_map_data: None
        self._handle_items_removed = (
            handle_items_removed if handle_items_removed is not None else lambda db_map_data: None
        )
        self._handle_items_updated = (
            handle_items_updated if handle_items_updated is not None else lambda db_map_data: None
        )

    def handle_items_added(self, db_map_data):
        self._handle_items_added(db_map_data)

    def handle_items_removed(self, db_map_data):
        self._handle_items_removed(db_map_data)

    def handle_items_updated(self, db_map_data):
        self._handle_items_updated(db_map_data)

    def filter_query(self, query, subquery, db_map):
        return self._filter_query(query, subquery, db_map)

    def accepts_item(self, item, db_map):
        return self._accepts_item(item, db_map)


class FetchMoreMixin:
    # FIXME: Use parent for calls to fetch_more can_fetch_more
    # and also insert items from db map cache in case they were already fetched

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._natural_fetch_parent = CallbackFetchParent(
            self.fetch_item_type,
            handle_items_added=self.handle_items_added,
            handle_items_removed=self.handle_items_removed,
            handle_items_updated=self.handle_items_updated,
            filter_query=self.filter_query,
        )

    @property
    def fetch_item_type(self):
        return self.item_type

    def _fetch_parents(self):
        yield self._natural_fetch_parent

    def can_fetch_more(self):
        return any(self.db_mngr.can_fetch_more(self.db_map, parent) for parent in self._fetch_parents())

    def fetch_more(self):
        for parent in self._fetch_parents():
            self.db_mngr.fetch_more(self.db_map, parent)

    def _make_child(self, id_):
        raise NotImplementedError()

    # pylint: disable=no-self-use
    def filter_query(self, query, subquery, db_map):
        return query

    def accepts_item(self, item, db_map):
        return True

    def handle_items_added(self, db_map_data):
        """Inserts items at right positions. Items with commit_id are kept sorted.
        Items without a commit_id are put at the end.

        Args:
            db_map_data (dict): mapping db_map to list of dict corresponding to db items
        """
        db_items = db_map_data.get(self.db_map, [])
        ids_committed = []
        ids_uncommitted = []
        for item in db_items:
            if item["id"] in self.children_ids:
                continue
            ids = ids_committed if item.get("commit_id") is not None else ids_uncommitted
            ids.append(item["id"])
        children_committed = [self._make_child(id_) for id_ in ids_committed]
        children_uncommitted = [self._make_child(id_) for id_ in ids_uncommitted]
        self.insert_children_sorted(children_committed)
        self.insert_children(len(self.non_empty_children), children_uncommitted)

    def handle_items_removed(self, db_map_data):
        ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        removed_rows = []
        for row, leaf_item in enumerate(self.children):
            if leaf_item.id and leaf_item.id in ids:
                removed_rows.append(row)
        for row in sorted(removed_rows, reverse=True):
            self.remove_children(row, 1)

    def handle_items_updated(self, db_map_data):
        leaf_items = {leaf_item.id: leaf_item for leaf_item in self.children if leaf_item.id}
        ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for id_ in set(ids).intersection(leaf_items):
            leaf_item = leaf_items[id_]
            leaf_item.handle_updated_in_db()
            index = self.model.index_from_item(leaf_item)
            self.model.dataChanged.emit(index, index)
            if leaf_item.children:
                top_left = self.model.index_from_item(leaf_item.child(0))
                bottom_right = self.model.index_from_item(leaf_item.child(-1))
                self.model.dataChanged.emit(top_left, bottom_right)


class StandardDBItem(SortChildrenMixin, StandardTreeItem):
    """An item representing a db."""

    def __init__(self, db_map):
        """Init class.

        Args
            db_mngr (SpineDBManager)
            db_map (DiffDatabaseMapping)
        """
        super().__init__()
        self.db_map = db_map

    @property
    def item_type(self):
        return "db"

    def data(self, column, role=Qt.DisplayRole):
        """Shows Spine icon for fun."""
        if column != 0:
            return None
        if role == Qt.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.db_map.codename


class RootItem(SortChildrenMixin, BoldTextMixin, FetchMoreMixin, StandardTreeItem):
    """A root item."""

    @property
    def item_type(self):
        raise NotImplementedError

    @property
    def db_map(self):
        return self.parent_item.db_map


class EmptyChildRootItem(EmptyChildMixin, RootItem):
    def empty_child(self):
        raise NotImplementedError


class LeafItem(StandardTreeItem):
    def __init__(self, identifier=None):
        super().__init__()
        self._id = identifier

    def _make_item_data(self):
        return {"name": f"Type new {self.item_type} name here...", "description": ""}

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def id(self):
        return self._id

    @property
    def item_data(self):
        if not self.id:
            return self._make_item_data()
        return self.db_mngr.get_item(self.db_map, self.item_type, self.id)

    @property
    def name(self):
        return self.item_data["name"]

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()

    def header_data(self, column):
        return self.model.headerData(column, Qt.Horizontal)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            data = self.item_data.get(self.header_data(column))
            if data is None:
                data = ""
            return data
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.EditRole):
        if role != Qt.EditRole or value == self.data(column, role):
            return False
        if self.id:
            db_item = self._make_item_to_update(column, value)
            self.update_item_in_db(db_item)
            return True
        if column == 0:
            db_item = self._make_item_to_add(value)
            self.add_item_to_db(db_item)
        return True

    def _make_item_to_add(self, value):
        return dict(name=value, description=self.item_data["description"])

    def _make_item_to_update(self, column, value):
        field = self.header_data(column)
        return {"id": self.id, field: value}

    def handle_updated_in_db(self):
        index = self.index()
        sibling = self.index().sibling(self.index().row(), 1)
        self.model.dataChanged.emit(index, sibling)

    def can_fetch_more(self):
        return False
