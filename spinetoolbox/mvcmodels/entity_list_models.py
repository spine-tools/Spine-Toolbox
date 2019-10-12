######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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


class ObjectClassListModel(QStandardItemModel):
    """A model for listing object classes in the GraphViewForm."""

    def __init__(self, graph_view_form):
        """Initialize class"""
        super().__init__(graph_view_form)
        self._graph_view_form = graph_view_form
        self.db_map = graph_view_form.db_map

    def populate_list(self):
        """Populate model."""
        self.clear()
        object_class_list = [x for x in self.db_map.object_class_list()]
        for object_class in object_class_list:
            object_class_item = QStandardItem(object_class.name)
            data = {"type": "object_class"}
            data.update(object_class._asdict())
            object_class_item.setData(data, Qt.UserRole + 1)
            object_class_item.setData(object_class.name, Qt.ToolTipRole)
            self.appendRow(object_class_item)
        add_more_item = QStandardItem("Add more...")
        add_more_item.setSelectable(False)
        add_more_item.setData(QBrush(QColor("#e6e6e6")), Qt.BackgroundRole)
        icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        add_more_item.setIcon(icon)
        add_more_item.setToolTip("Add custom object class")
        add_more_item.setData("Add More", Qt.UserRole + 2)
        self.appendRow(add_more_item)

    def add_object_class(self, object_class):
        """Add object class item to model."""
        object_class_item = QStandardItem(object_class.name)
        data = {"type": "object_class", **object_class._asdict()}
        object_class_item.setData(data, Qt.UserRole + 1)
        object_class_item.setData(object_class.name, Qt.ToolTipRole)
        for i in range(self.rowCount()):
            visited_index = self.index(i, 0)
            visited_display_order = visited_index.data(Qt.UserRole + 1)['display_order']
            if visited_display_order >= object_class.display_order:
                self.insertRow(i, object_class_item)
                return
        self.insertRow(self.rowCount() - 1, object_class_item)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.DecorationRole and index.data(Qt.UserRole + 1):
            return self._graph_view_form.icon_mngr.object_icon(index.data(Qt.UserRole + 1)["name"])
        return super().data(index, role)


class RelationshipClassListModel(QStandardItemModel):
    """A model for listing relationship classes in the GraphViewForm."""

    def __init__(self, graph_view_form):
        """Initialize class"""
        super().__init__(graph_view_form)
        self._graph_view_form = graph_view_form
        self.db_map = graph_view_form.db_map

    def populate_list(self):
        """Populate model."""
        self.clear()
        relationship_class_list = [x for x in self.db_map.wide_relationship_class_list()]
        for relationship_class in relationship_class_list:
            relationship_class_item = QStandardItem(relationship_class.name)
            data = {"type": "relationship_class"}
            data.update(relationship_class._asdict())
            relationship_class_item.setData(data, Qt.UserRole + 1)
            relationship_class_item.setData(relationship_class.name, Qt.ToolTipRole)
            self.appendRow(relationship_class_item)
        add_more_item = QStandardItem("Add more...")
        add_more_item.setSelectable(False)
        add_more_item.setData(QBrush(QColor("#e6e6e6")), Qt.BackgroundRole)
        icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        add_more_item.setIcon(icon)
        add_more_item.setToolTip("Add custom relationship class")
        add_more_item.setData("Add More", Qt.UserRole + 2)
        self.appendRow(add_more_item)

    def add_relationship_class(self, relationship_class):
        """Add relationship class."""
        relationship_class_item = QStandardItem(relationship_class.name)
        data = {"type": "relationship_class", **relationship_class._asdict()}
        relationship_class_item.setData(data, Qt.UserRole + 1)
        relationship_class_item.setData(relationship_class.name, Qt.ToolTipRole)
        self.insertRow(self.rowCount() - 1, relationship_class_item)

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if role == Qt.DecorationRole and index.data(Qt.UserRole + 1):
            return self._graph_view_form.icon_mngr.relationship_icon(
                index.data(Qt.UserRole + 1)["object_class_name_list"]
            )
        return super().data(index, role)
