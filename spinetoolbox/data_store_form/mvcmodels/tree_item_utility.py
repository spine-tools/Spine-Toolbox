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
A tree model for parameter value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from spinetoolbox.mvcmodels.minimal_tree_model import TreeItem


class NonLazyTreeItem(TreeItem):
    """A tree item that fetches their children as they are inserted."""

    @property
    def item_type(self):
        raise NotImplementedError()

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
