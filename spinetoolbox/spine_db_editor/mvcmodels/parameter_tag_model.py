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
A tree model for parameter_tags.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QIcon
from spinetoolbox.mvcmodels.minimal_tree_model import MinimalTreeModel
from .tree_item_utility import (
    EmptyChildMixin,
    LastGrayMixin,
    EditableMixin,
    NonLazyTreeItem,
    NonLazyDBItem,
)
from ...helpers import CharIconEngine


class DBItem(EmptyChildMixin, NonLazyDBItem):
    """An item representing a db."""

    def empty_child(self):
        return TagItem()


class TagItem(LastGrayMixin, EditableMixin, NonLazyTreeItem):
    def __init__(self, identifier=None):
        super().__init__()
        self._id = identifier
        self._item_data = {"tag": f"Type new tag here...", "description": ""}

    @property
    def item_type(self):
        return "parameter_tag"

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
    def tag(self):
        return self.item_data["tag"]

    def add_item_to_db(self, db_item):
        self.db_mngr.add_parameter_tags({self.db_map: [db_item]})

    def update_item_in_db(self, db_item):
        self.db_mngr.update_parameter_tags({self.db_map: [db_item]})

    def header_data(self, column):
        return self.model.headerData(column, Qt.Horizontal)

    def data(self, column, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            data = self.item_data.get(self.header_data(column))
            if data is None:
                data = ""
            return data
        if role == Qt.DecorationRole and column == 0:
            engine = CharIconEngine("\uf02b", 0)
            return QIcon(engine.pixmap())
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
            db_item = dict(tag=value, description=self._item_data["description"])
            self.add_item_to_db(db_item)
        return True

    def handle_updated_in_db(self):
        index = self.index()
        sibling = self.index().sibling(self.index().row(), 1)
        self.model.dataChanged.emit(index, sibling)


class ParameterTagModel(MinimalTreeModel):
    """A model to display parameter_tag data in a tree view.


    Args:
        parent (SpineDBEditor)
        db_mngr (SpineDBManager)
        db_maps (iter): DiffDatabaseMapping instances
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def receive_parameter_tags_added(self, db_map_data):
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            # First realize the ones added locally
            ids = {x["tag"]: x["id"] for x in items}
            for tag_item in db_item.children[:-1]:
                id_ = ids.pop(tag_item.tag, None)
                if not id_:
                    continue
                tag_item.handle_added_to_db(identifier=id_)
            # Now append the ones added externally
            children = [TagItem(id_) for id_ in ids.values()]
            db_item.insert_children(db_item.child_count() - 1, *children)

    def receive_parameter_tags_updated(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            ids = {x["id"] for x in items}
            tag_items = {tag_item.id: tag_item for tag_item in db_item.children[:-1]}
            for id_ in ids.intersection(tag_items):
                tag_items[id_].handle_updated_in_db()
        self.layoutChanged.emit()

    def receive_parameter_tags_removed(self, db_map_data):
        self.layoutAboutToBeChanged.emit()
        for db_item in self._invisible_root_item.children:
            items = db_map_data.get(db_item.db_map)
            if not items:
                continue
            ids = {x["id"] for x in items}
            removed_rows = []
            for row, tag_item in enumerate(db_item.children[:-1]):
                if tag_item.id in ids:
                    removed_rows.append(row)
            for row in sorted(removed_rows, reverse=True):
                db_item.remove_children(row, 1)
        self.layoutChanged.emit()

    def build_tree(self):
        """Initialize the internal data structure of the model."""
        self.beginResetModel()
        self._invisible_root_item = NonLazyTreeItem(self)
        self.endResetModel()
        db_items = [DBItem(db_map) for db_map in self.db_maps]
        self._invisible_root_item.append_children(*db_items)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 2.
        """
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("tag", "description")[section]
        return None
