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
A tree model for parameter_value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinetoolbox.mvcmodels.minimal_tree_model import TreeItem
from spinetoolbox.helpers import CharIconEngine, bisect_chunks


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
    """Guarantess there's always an empty child."""

    @property
    def non_empty_children(self):
        return self.children[:-1]

    def empty_child(self):
        raise NotImplementedError()

    def _do_finalize(self):
        super()._do_finalize()
        empty_child = self.empty_child()
        self.append_children([empty_child])


class SortsChildrenMixin:
    def insert_children_sorted(self, children):
        for child in children:
            child.parent_item = self
        for chunk, pos in bisect_chunks(self.non_empty_children, children, key=lambda x: x.data(0)):
            if not super().insert_children(pos, chunk):
                return False
        return True


class FetchMoreMixin:
    # FIXME: Use parent for calls to fetch_more can_fetch_more
    # and also insert items from db map cache in case they were already fetched
    @property
    def fetch_item_type(self):
        return self.item_type

    def can_fetch_more(self):
        return self.db_mngr.can_fetch_more(self.db_map, self.fetch_item_type)

    def fetch_more(self):
        self.db_mngr.fetch_more(self.db_map, self.fetch_item_type)


class StandardDBItem(SortsChildrenMixin, StandardTreeItem):
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


class RootItem(SortsChildrenMixin, BoldTextMixin, FetchMoreMixin, StandardTreeItem):
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
