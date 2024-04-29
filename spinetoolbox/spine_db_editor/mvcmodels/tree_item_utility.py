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
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinetoolbox.mvcmodels.minimal_tree_model import TreeItem
from spinetoolbox.helpers import CharIconEngine, bisect_chunks, plain_to_tool_tip
from spinetoolbox.fetch_parent import FlexibleFetchParent


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
        children_committed = [self._do_make_child(id_) for id_ in ids_committed]
        children_uncommitted = [self._do_make_child(id_) for id_ in ids_uncommitted]
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

    def __init__(self, model, db_map):
        """Init class.

        Args:
            model (MinimalTreeModel)
            db_map (DatabaseMapping)
        """
        super().__init__(model)
        self.db_map = db_map

    @property
    def item_type(self):
        return "db"

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        """Shows Spine icon for fun."""
        if column != 0:
            return None
        if role == Qt.ItemDataRole.DecorationRole:
            return QIcon(":/symbols/Spine_symbol.png")
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self.db_map.codename


class LeafItem(StandardTreeItem):
    def __init__(self, model, identifier=None):
        """
        Args:
            model (MinimalTreeModel)
            identifier (int, optional): item's database id
        """
        super().__init__(model)
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

    def tool_tip(self, column):
        if column != 0 and (header_data := self.header_data(column)) == "description":
            return plain_to_tool_tip(self.item_data.get(header_data))
        return super().tool_tip(column)

    def add_item_to_db(self, db_item):
        raise NotImplementedError()

    def update_item_in_db(self, db_item):
        raise NotImplementedError()

    def header_data(self, column):
        return self.model.headerData(column, Qt.Orientation.Horizontal)

    def data(self, column, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            data = self.item_data.get(self.header_data(column))
            if data is None:
                data = ""
            return data
        return super().data(column, role)

    def set_data(self, column, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or value == self.data(column, role):
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
