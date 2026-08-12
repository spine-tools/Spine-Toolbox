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

"""A tree model for parameter_value lists."""

from typing import ClassVar
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont, QGuiApplication, QIcon
from spinedb_api.temp_id import TempId
from spinetoolbox.fetch_parent import FlexibleFetchParent
from spinetoolbox.helpers import CharIconEngine, DBMapPublicItems, bisect_chunks, plain_to_tool_tip
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel, TreeItem
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE, ITEM_ID_ROLE


class StandardTreeItem(TreeItem):
    """A tree item that fetches their children as they are inserted."""

    item_type: ClassVar[str] = None
    icon_code: ClassVar[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Memoized filtered view of the children plus a {child: visible_row} position map, both keyed on the
        # model's ``filter_generation`` so they are rebuilt lazily only when the filter or the children change.
        self._visible_children_cache: list | None = None
        self._visible_row_map: dict = {}
        self._visible_cache_generation: int = -1

    @property
    def db_mngr(self):
        return self.model.db_mngr

    @property
    def display_data(self):
        return None

    def tool_tip(self, column):
        return None

    @property
    def display_icon(self):
        if self.icon_code is None:
            return None
        engine = CharIconEngine(self.icon_code, 0)
        return QIcon(engine.pixmap())

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.tool_tip(column)
        if column != 0:
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self.display_data
        if role == Qt.ItemDataRole.DecorationRole:
            return self.display_icon
        return super().data(0, role)

    def set_data(self, column, value, role=Qt.ItemDataRole.DisplayRole):
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

    def is_empty_row(self):
        """Returns whether this item is the phantom trailing "add new" row.

        The empty row is the child that :class:`EmptyChildMixin` appends past ``non_empty_children``; a
        plain parent has no such row. It is detected by identity so it works even for levels (e.g. scenario
        alternatives) whose real items also carry a ``None`` id.

        Returns:
            bool: whether this item is its parent's phantom add-row
        """
        parent = self.parent_item
        if parent is None:
            return False
        return self not in parent.non_empty_children

    def raw_row(self):
        """Returns this item's index among its parent's children, ignoring any level filter.

        Use this wherever the row is a domain ordinal (an index into an id list or a DB order); use
        :meth:`child_number` only for the visible Qt row.

        Returns:
            Optional[int]: the raw sibling index, or None if this item has no parent
        """
        if self.parent_item is None:
            return None
        return self.parent_item.children.index(self)

    @property
    def visible_children(self):
        """Returns the children that pass the active level filters, plus the phantom add-row.

        When no level filter is active this is ``self.children`` unchanged, so the filtered path adds no
        overhead to normal operation. Otherwise the filtered list is memoized and only recomputed when the
        model's :attr:`~.level_filter.LevelFilterMixin.filter_generation` moves, so repeated Qt
        layout/paint/scroll queries are served from the cache rather than rebuilt every time.

        Returns:
            list: the visible children
        """
        if not self.model.has_level_filters():
            return self.children
        self._ensure_visible_cache()
        return self._visible_children_cache

    def _ensure_visible_cache(self) -> None:
        """Rebuilds the filtered child list and position map if the filter generation has moved."""
        generation = self.model.filter_generation
        if self._visible_cache_generation == generation and self._visible_children_cache is not None:
            return
        visible = [child for child in self.children if self.model.item_is_visible(child)]
        self._visible_children_cache = visible
        self._visible_row_map = {child: row for row, child in enumerate(visible)}
        self._visible_cache_generation = generation

    def row_count(self):
        """Overridden to count only visible children."""
        return len(self.visible_children)

    def child(self, row):
        """Overridden to return the visible child at the given row or None if out of bounds."""
        visible = self.visible_children
        if 0 <= row < len(visible):
            return visible[row]
        return None

    def child_number(self):
        """Overridden to return the item's VISIBLE row within its parent, or None if hidden/orphan.

        With no filter active this is the raw sibling index; under a filter it is an O(1) lookup in the
        parent's cached ``{child: visible_row}`` map rather than an O(n) scan of the filtered list.
        """
        parent = self.parent_item
        if parent is None:
            return None
        if not self.model.has_level_filters():
            try:
                return parent.children.index(self)
            except ValueError:
                return None
        parent._ensure_visible_cache()
        return parent._visible_row_map.get(self)

    def insert_children(self, position, children):
        """Inserts children and refines the filter once new rows appear under an active filter."""
        if not super().insert_children(position, children):
            return False
        if self.model.has_level_filters():
            # Newly fetched/inserted children must be filtered; invalidate the cached filtered lists so the
            # new rows are reflected. The debounced re-apply also refines any now-non-empty (or still-empty)
            # parent that a filter should show or hide, and continues any active force-fetch cascade.
            self.model._bump_filter_generation()
            self.model._schedule_level_filter_refresh()
        return True

    def remove_children(self, position, count):
        """Removes children and refines the filter under an active filter."""
        if not super().remove_children(position, count):
            return False
        if self.model.has_level_filters():
            self.model._bump_filter_generation()
            self.model._schedule_level_filter_refresh()
        return True


class EditableMixin:
    def flags(self, column):
        """Makes items editable."""
        return Qt.ItemIsEditable | super().flags(column)


class GrayIfLastMixin:
    """Paints the item gray if it's the last."""

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ForegroundRole and self.child_number() == self.parent_item.row_count() - 1:
            gray_color = QGuiApplication.palette().text().color()
            gray_color.setAlpha(128)
            gray_brush = QBrush(gray_color)
            return gray_brush
        return super().data(column, role)


class BoldTextMixin:
    """Bolds text."""

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.FontRole:
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

    def _do_set_up(self):
        super()._do_set_up()
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


class FetchMoreMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._natural_fetch_parent = FlexibleFetchParent(
            self.fetch_item_type,
            handle_items_added=self.handle_items_added,
            handle_items_removed=self.handle_items_removed,
            handle_items_updated=self.handle_items_updated,
            accepts_item=self.accepts_item,
        )

    def tear_down(self):
        super().tear_down()
        self._natural_fetch_parent.set_obsolete(True)
        self._natural_fetch_parent.deleteLater()

    @property
    def fetch_item_type(self):
        return self.item_type

    def _fetch_parents(self):
        yield self._natural_fetch_parent

    def can_fetch_more(self):
        result = False
        for parent in self._fetch_parents():
            result |= self.db_mngr.can_fetch_more(self.db_map, parent)
        return result

    def fetch_more(self):
        for parent in self._fetch_parents():
            self.db_mngr.fetch_more(self.db_map, parent)

    def _make_child(self, id_):
        raise NotImplementedError()

    def _do_make_child(self, id_):
        child = self._created_children.get(id_)
        if child is None:
            child = self._created_children[id_] = self._make_child(id_)
        return child

    def accepts_item(self, item, db_map):
        return True

    def handle_items_added(self, db_map_data: DBMapPublicItems) -> None:
        """Inserts items at right positions. Items that have been committed are kept sorted.
        Uncommitted items are put at the end.

        Args:
            db_map_data: mapping db_map to list of dict corresponding to db items
        """
        db_items = db_map_data.get(self.db_map, [])
        children_committed = []
        children_uncommitted = []
        existing_ids = set(self.children_ids)
        for item in db_items:
            item_id = item["id"]
            if item_id in existing_ids:
                continue
            child = self._do_make_child(item_id)
            (children_committed if item.is_committed() else children_uncommitted).append(child)
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
                bottom_right = self.model.index_from_item(leaf_item.child(leaf_item.child_count() - 1))
                self.model.dataChanged.emit(top_left, bottom_right)


class StandardDBItem(SortChildrenMixin, StandardTreeItem):
    """An item representing a db."""

    item_type = "db"

    def __init__(self, model, db_map, db_name_registry):
        """
        Args:
            model (MinimalTreeModel): tree model
            db_map (DatabaseMapping): database mapping
            db_name_registry (NameRegistry): database display name registry
        """
        super().__init__(model)
        self.db_map = db_map
        self._db_name_registry = db_name_registry

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Shows Spine icon for fun."""
        if column != 0:
            return None
        if role == Qt.ItemDataRole.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._db_name_registry.display_name(self.db_map.sa_url)
        if role == DB_MAP_ROLE:
            return self.db_map
        return None


class LeafItem(StandardTreeItem):
    def __init__(self, model: MinimalTreeModel, identifier: TempId | None = None):
        """
        Args:
            model: The model the item belongs to.
            identifier: Item's id.
        """
        super().__init__(model)
        self._id = identifier

    def _make_item_data(self):
        return {"name": f"Type new {self.item_type} name here...", "description": ""}

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

    def tool_tip(self, column):
        if column != 0 and (header_data := self.header_data(column)) == "description":
            return plain_to_tool_tip(self.item_data.get(header_data))
        return super().tool_tip(column)

    def header_data(self, column):
        return self.model.headerData(column, Qt.Orientation.Horizontal)

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            data = self.item_data.get(self.header_data(column))
            if data is None:
                data = ""
            return data
        if role == ITEM_ID_ROLE:
            return self._id
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or value == self.data(column, role):
            return False
        if self.id:
            db_item = self._make_item_to_update(column, value)
            self.db_mngr.update_items(self.item_type, {self.db_map: [db_item]})
            return True
        if column == 0:
            db_item = self._make_item_to_add(value)
            self.db_mngr.add_items(self.item_type, {self.db_map: [db_item]})
        return True

    def _make_item_to_add(self, value):
        return {"name": value, "description": self.item_data["description"]}

    def _make_item_to_update(self, column, value):
        field = self.header_data(column)
        return {"id": self.id, field: value}

    def handle_updated_in_db(self):
        index = self.index()
        sibling = self.index().sibling(self.index().row(), 1)
        self.model.dataChanged.emit(index, sibling)

    def can_fetch_more(self):
        return False
