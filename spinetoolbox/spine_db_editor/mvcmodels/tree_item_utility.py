######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from spinetoolbox.helpers import CharIconEngine


class NonLazyTreeItem(TreeItem):
    """A tree item that fetches their children as they are inserted."""

    @property
    def item_type(self):
        return "unknown"

    @property
    def db_mngr(self):
        return self.model.db_mngr

    def can_fetch_more(self):
        """Disables lazy loading by returning False."""
        return False

    def insert_children(self, position, *children):
        """Fetches the children as they become parented."""
        if not super().insert_children(position, *children):
            return False
        for child in children:
            child.fetch_more()
        return True


class EditableMixin:
    def flags(self, column):
        """Makes items editable."""
        return Qt.ItemIsEditable | super().flags(column)


class LastGrayMixin:
    """Paints the last item gray."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and self.child_number() == self.parent_item.child_count() - 1:
            gray_color = QGuiApplication.palette().text().color()
            gray_color.setAlpha(128)
            gray_brush = QBrush(gray_color)
            return gray_brush
        return super().data(column, role)


class AllBoldMixin:
    """Bolds text."""

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            bold_font = QFont()
            bold_font.setBold(True)
            return bold_font
        return super().data(column, role)


class EmptyChildMixin:
    """Guarantess there's always an empty child."""

    def empty_child(self):
        raise NotImplementedError()

    def fetch_more(self):
        empty_child = self.empty_child()
        self.append_children(empty_child)
        self._fetched = True

    def append_empty_child(self, row):
        """Appends empty child if the row is the last one."""
        if row == self.child_count() - 1:
            empty_child = self.empty_child()
            self.append_children(empty_child)


class NonLazyDBItem(NonLazyTreeItem):
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

    def set_data(self, column, value, role):
        """See base class."""
        return False


class RootItem(EmptyChildMixin, AllBoldMixin, NonLazyTreeItem):
    """A root item."""

    @property
    def item_type(self):
        raise NotImplementedError

    @property
    def display_data(self):
        raise NotImplementedError

    @property
    def icon_code(self):
        raise NotImplementedError

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def display_icon(self):
        engine = CharIconEngine(self.icon_code, 0)
        return QIcon(engine.pixmap())

    def data(self, column, role=Qt.DisplayRole):
        if column != 0:
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.display_data
        if role == Qt.DecorationRole:
            return self.display_icon
        return super().data(column, role)

    def set_data(self, column, value, role):
        return False

    def empty_child(self):
        raise NotImplementedError


class LeafItem(NonLazyTreeItem):
    def __init__(self, identifier=None):
        super().__init__()
        self._id = identifier
        self._item_data = self._make_item_data()

    def _make_item_data(self):
        return {"name": f"Type new {self.item_type} name here...", "description": ""}

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def tool_tip(self):
        return None

    @property
    def db_map(self):
        return self.parent_item.db_map

    @property
    def id(self):
        return self._id

    @property
    def item_data(self):
        if not self.id:
            return self._item_data
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
        if role == Qt.ToolTipRole:
            return self.tool_tip
        return super().data(column, role)

    def set_data(self, column, value, role):
        if role != Qt.EditRole or value == self.data(column, role):
            return False
        if self.id:
            field = self.header_data(column)
            db_item = {"id": self.id, field: value}
            self.update_item_in_db(db_item)
            return True
        if column == 0:
            db_item = self._make_item_to_add(value)
            self.add_item_to_db(db_item)
        return True

    def _make_item_to_add(self, name):
        return dict(name=name, description=self._item_data["description"])

    def handle_updated_in_db(self):
        index = self.index()
        sibling = self.index().sibling(self.index().row(), 1)
        self.model.dataChanged.emit(index, sibling)
