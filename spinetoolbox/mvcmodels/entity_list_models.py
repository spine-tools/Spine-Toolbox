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
List models for object and relationship classes.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QIcon, QColor


class EntityListModel(QStandardItemModel):
    """A model for listing entity classes in the GraphViewForm."""

    def __init__(self, graph_view_form, db_mngr, db_map):
        """Initialize class"""
        super().__init__(graph_view_form)
        self.db_mngr = db_mngr
        self.db_map = db_map
        self.new_index = None

    @property
    def add_more_icon(self):
        raise NotImplementedError()

    @property
    def entity_type(self):
        raise NotImplementedError()

    def _get_entity_class_ids(self):
        raise NotImplementedError()

    def populate_list(self):
        """Populate model."""
        self.clear()
        new_item = QStandardItem("New...")
        new_item.setSelectable(False)
        new_item.setData(QBrush(QColor("#e6e6e6")), Qt.BackgroundRole)
        new_item.setIcon(self.add_more_icon)
        new_item.setToolTip("Add new class.")
        self.appendRow(new_item)
        self.new_index = self.indexFromItem(new_item)
        for entity_class_id in self._get_entity_class_ids():
            self.add_entity_class(entity_class_id)

    def add_entity_class(self, entity_class_id):
        """Add entity class item to model."""
        entity_class_item = QStandardItem()
        entity_class_item.setData(entity_class_id, Qt.UserRole + 1)
        self.appendRow(entity_class_item)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if index != self.new_index:
            if role == Qt.DisplayRole:
                return self._data(index)
            if role == Qt.DecorationRole:
                return self.db_mngr.entity_class_icon(self.db_map, self.entity_type, index.data(Qt.UserRole + 1))
            if role == Qt.ToolTipRole:
                return f"<html>Drag-and-drop this icon onto the Entity graph to create a new <b>{self._data(index)}</b></html>"
        return super().data(index, role)

    def _data(self, index):
        return self.db_mngr.get_item(self.db_map, self.entity_type, index.data(Qt.UserRole + 1)).get("name")

    def receive_entity_classes_added(self, db_map_data):
        """Runs when entity classes are added."""
        for entity_class in db_map_data.get(self.db_map, []):
            self.add_entity_class(entity_class["id"])

    def receive_entity_classes_updated(self, db_map_data):
        """Runs when entity classes are update."""
        ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for item in self.findItems("*", Qt.MatchWildcard):
            if item.data(Qt.UserRole + 1) in ids:
                self.dataChanged.emit(item.index(), item.index())

    def receive_entity_classes_removed(self, db_map_data):
        """Runs when entity classes are removed."""
        ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for item in self.findItems("*", Qt.MatchWildcard):
            if item.data(Qt.UserRole + 1) in ids:
                self.removeRow(item.index().row())

    def flags(self, index):
        return super().flags(index) & ~Qt.ItemIsSelectable


class ObjectClassListModel(EntityListModel):
    """A model for listing object classes in the GraphViewForm."""

    @property
    def add_more_icon(self):
        return QIcon(":/icons/menu_icons/cube_plus.svg")

    @property
    def entity_type(self):
        return "object class"

    def _get_entity_class_ids(self):
        return [x["id"] for x in self.db_mngr.get_object_classes(self.db_map)]


class RelationshipClassListModel(EntityListModel):
    """A model for listing relationship classes in the GraphViewForm."""

    @property
    def add_more_icon(self):
        return QIcon(":/icons/menu_icons/cubes_plus.svg")

    @property
    def entity_type(self):
        return "relationship class"

    def _get_entity_class_ids(self):
        return [x["id"] for x in self.db_mngr.get_relationship_classes(self.db_map)]
