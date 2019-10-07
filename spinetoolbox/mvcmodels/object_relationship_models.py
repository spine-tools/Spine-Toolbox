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
Models for object and relationship classes.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QFont, QIcon, QColor, QPen
from ..helpers import busy_effect


class ObjectClassListModel(QStandardItemModel):
    """A model for listing object classes in the GraphViewForm."""

    def __init__(self, graph_view_form):
        """Initialize class"""
        super().__init__(graph_view_form)
        self._graph_view_form = graph_view_form
        self.db_map = graph_view_form.db_map
        self.add_more_index = None

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
        add_more_item = QStandardItem()
        add_more_item.setSelectable(False)
        add_more_item.setData("Add more...", Qt.DisplayRole)
        add_more_item.setData(QBrush(QColor("#e6e6e6")), Qt.BackgroundRole)
        # add_more_item.setTextAlignment(Qt.AlignHCenter)
        icon = QIcon(":/icons/menu_icons/cube_plus.svg")
        add_more_item.setIcon(icon)
        add_more_item.setData("Add custom object class", Qt.ToolTipRole)
        self.appendRow(add_more_item)
        self.add_more_index = self.indexFromItem(add_more_item)

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
        self.add_more_index = None

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
        add_more_item = QStandardItem()
        add_more_item.setData("Add more...", Qt.DisplayRole)
        self.appendRow(add_more_item)
        self.add_more_index = self.indexFromItem(add_more_item)

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


class ObjectTreeModel(QStandardItemModel):
    """A model to display objects and relationships in a tree
    with object classes at the outer level.
    """

    def __init__(self, parent, flat=False):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent
        self.db_maps = parent.db_maps
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.flat = flat
        self._fetched = {}
        self.root_item = None

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if index.column() != 0:
            return super().data(index, role)
        if role == Qt.ForegroundRole:
            item_type = index.data(Qt.UserRole)
            if item_type.endswith('class') and not self.hasChildren(index):
                return QBrush(Qt.gray)
        elif role == Qt.DecorationRole:
            item_type = index.data(Qt.UserRole)
            if item_type == 'root':
                return QIcon(":/symbols/Spine_symbol.png")
            if item_type == 'object_class':
                return self._parent.icon_mngr.object_icon(index.data(Qt.DisplayRole))
            if item_type == 'object':
                return self._parent.icon_mngr.object_icon(index.parent().data(Qt.DisplayRole))
            if item_type == 'relationship_class':
                return self._parent.icon_mngr.relationship_icon(index.data(Qt.ToolTipRole))
            if item_type == 'relationship':
                return self._parent.icon_mngr.relationship_icon(index.parent().data(Qt.ToolTipRole))
        return super().data(index, role)

    @staticmethod
    def backward_sweep(index, call=None):
        """Sweep the tree from the given index towards the root, and apply `call` on each."""
        current = index
        while True:
            if call:
                call(current)
            # Try and visit parent
            next_ = current.parent()
            if not next_.isValid():
                break
            current = next_

    def forward_sweep(self, index, call=None):
        """Sweep the tree from the given index towards the leaves, and apply `call` on each."""
        if call:
            call(index)
        if self.canFetchMore(index) or not self.hasChildren(index):
            return
        current = index
        back_to_parent = False  # True if moving back to the parent index
        while True:
            if call:
                call(current)
            if not back_to_parent:
                # Try and visit first child
                next_ = self.index(0, 0, current)
                if next_.isValid():
                    back_to_parent = False
                    current = next_
                    continue
            # Try and visit next sibling
            next_ = current.sibling(current.row() + 1, 0)
            if next_.isValid():
                back_to_parent = False
                current = next_
                continue
            # Go back to parent
            next_ = self.parent(current)
            if next_ != index:
                back_to_parent = True
                current = next_
                continue
            break

    def hasChildren(self, parent):
        """Return True if not fetched, so the user can try and expand it."""
        if not parent.isValid():
            return super().hasChildren(parent)
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return super().hasChildren(parent)
        if parent_type == 'relationship':
            return False
        if self.flat and parent_type in ('object', 'relationship_class'):
            return False
        if not self.canFetchMore(parent):
            return super().hasChildren(parent)
        return True

    def canFetchMore(self, parent):
        """Return True if not fetched."""
        if not parent.isValid():
            return True
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return True
        fetched = self._fetched[parent_type]
        parent_db_map_dict = parent.data(Qt.UserRole + 1)
        if parent_type in ('object_class', 'object'):
            return any((db_map, item['id']) not in fetched for db_map, item in parent_db_map_dict.items())
        if parent_type == 'relationship_class':
            grampa_db_map_dict = parent.parent().data(Qt.UserRole + 1)
            for db_map, rel_cls in parent_db_map_dict.items():
                obj = grampa_db_map_dict[db_map]
                if (db_map, (obj['id'], rel_cls['id'])) not in fetched:
                    return True
            return False
        return False

    @busy_effect
    def fetchMore(self, parent):
        """Build the deeper levels of the tree"""
        if not parent.isValid():
            return False
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return False
        fetched = self._fetched[parent_type]
        parent_db_map_dict = parent.data(Qt.UserRole + 1)
        if parent_type == 'object_class':
            object_class_item = self.itemFromIndex(parent)
            for db_map, object_class in parent_db_map_dict.items():
                self.add_objects_to_class(db_map, db_map.object_list(class_id=object_class['id']), object_class_item)
                fetched.add((db_map, object_class['id']))
        elif parent_type == 'object':
            object_item = self.itemFromIndex(parent)
            for db_map, object_ in parent_db_map_dict.items():
                relationship_classes = db_map.wide_relationship_class_list(object_class_id=object_['class_id'])
                self.add_relationships_classes_to_object(db_map, relationship_classes, object_item)
                fetched.add((db_map, object_['id']))
        elif parent_type == 'relationship_class':
            grampa_db_map_dict = parent.parent().data(Qt.UserRole + 1)
            rel_cls_item = self.itemFromIndex(parent)
            for db_map, relationship_class in parent_db_map_dict.items():
                object_ = grampa_db_map_dict[db_map]
                relationships = db_map.wide_relationship_list(
                    class_id=relationship_class['id'], object_id=object_['id']
                )
                self.add_relationships_to_class(db_map, relationships, rel_cls_item)
                fetched.add((db_map, (object_['id'], relationship_class['id'])))
        self.dataChanged.emit(parent, parent)

    def build_tree(self, flat=False):
        """Build the first level of the tree"""
        self.clear()
        self.setHorizontalHeaderLabels(["item", "databases"])
        self._fetched = {"object_class": set(), "object": set(), "relationship_class": set(), "relationship": set()}
        self.root_item = QStandardItem('root')
        self.root_item.setData('root', Qt.UserRole)
        db_item = QStandardItem(", ".join([self._parent.db_map_to_name[x] for x in self.db_maps]))
        for db_map in self.db_maps:
            self.add_object_classes(db_map, db_map.object_class_list())
        self.appendRow([self.root_item, db_item])

    def new_object_class_row(self, db_map, object_class):
        """Returns new object class item."""
        object_class_item = QStandardItem(object_class.name)
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData({db_map: object_class._asdict()}, Qt.UserRole + 1)
        object_class_item.setData(object_class.description, Qt.ToolTipRole)
        object_class_item.setData(self.bold_font, Qt.FontRole)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [object_class_item, db_item]

    def new_object_row(self, db_map, object_):
        """Returns new object item."""
        object_item = QStandardItem(object_.name)
        object_item.setData('object', Qt.UserRole)
        object_item.setData({db_map: object_._asdict()}, Qt.UserRole + 1)
        object_item.setData(object_.description, Qt.ToolTipRole)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [object_item, db_item]

    def new_relationship_class_row(self, db_map, relationship_class):
        """Returns new relationship class item."""
        relationship_class_item = QStandardItem(relationship_class.name)
        relationship_class_item.setData('relationship_class', Qt.UserRole)
        relationship_class_item.setData({db_map: relationship_class._asdict()}, Qt.UserRole + 1)
        relationship_class_item.setData(relationship_class.object_class_name_list, Qt.ToolTipRole)
        relationship_class_item.setData(self.bold_font, Qt.FontRole)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [relationship_class_item, db_item]

    def new_relationship_row(self, db_map, relationship):
        """Returns new relationship item."""
        relationship_item = QStandardItem(relationship.object_name_list)
        relationship_item.setData('relationship', Qt.UserRole)
        relationship_item.setData({db_map: relationship._asdict()}, Qt.UserRole + 1)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [relationship_item, db_item]

    def add_object_classes(self, db_map, object_classes):
        """Add object class items to given db.
        """
        existing_rows = [
            [self.root_item.child(i, 0), self.root_item.child(i, 1)] for i in range(self.root_item.rowCount())
        ]
        existing_row_d = {row[0].text(): row for row in existing_rows}
        new_rows = []
        for object_class in object_classes:
            if object_class.name in existing_row_d:
                # Already in model, append db_map information
                object_class_item, db_item = existing_row_d[object_class.name]
                db_map_dict = object_class_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = object_class._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
                # Add objects from this db if fetched
                object_class_index = self.indexFromItem(object_class_item)
                if not self.canFetchMore(object_class_index):
                    self.add_objects_to_class(db_map, db_map.object_list(class_id=object_class.id), object_class_item)
            else:
                new_rows.append(self.new_object_class_row(db_map, object_class))
        # Insert rows at right position given display_order
        for row in new_rows:
            object_class_item = row[0]
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            object_class = db_map_dict[db_map]
            for i in range(self.root_item.rowCount()):
                visited_object_class_item = self.root_item.child(i)
                visited_db_map_dict = visited_object_class_item.data(Qt.UserRole + 1)
                if db_map not in visited_db_map_dict:
                    continue
                visited_object_class = visited_db_map_dict[db_map]
                if visited_object_class['display_order'] > object_class['display_order']:
                    self.root_item.insertRow(i, row)
                    break
            else:
                self.root_item.appendRow(row)

    def add_objects(self, db_map, objects):
        """Add object items to the given db."""
        object_dict = {}
        for object_ in objects:
            object_dict.setdefault(object_.class_id, list()).append(object_)
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            object_class_index = self.indexFromItem(object_class_item)
            if self.canFetchMore(object_class_index):
                continue
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                # Can someone be adding objects to a class that doesn't exist in the same db?
                continue
            object_class = db_map_dict[db_map]
            object_class_id = object_class['id']
            if object_class_id not in object_dict:
                continue
            objects = object_dict[object_class_id]
            self.add_objects_to_class(db_map, objects, object_class_item)

    def add_relationship_classes(self, db_map, relationship_classes):
        """Add relationship class items to model."""
        relationship_class_dict = {}
        for relationship_class in relationship_classes:
            for object_class_id in relationship_class.object_class_id_list.split(","):
                relationship_class_dict.setdefault(int(object_class_id), list()).append(relationship_class)
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                # Can someone be adding relationship classes where one of the classes doesn't exist in the same db?
                continue
            object_class = db_map_dict[db_map]
            object_class_id = object_class['id']
            if object_class_id not in relationship_class_dict:
                continue
            relationship_classes = relationship_class_dict[object_class_id]
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                object_index = self.indexFromItem(object_item)
                if self.canFetchMore(object_index):
                    continue
                self.add_relationships_classes_to_object(db_map, relationship_classes, object_item)

    def add_relationships(self, db_map, relationships):
        """Add relationship items to model."""
        relationship_dict = {}
        for relationship in relationships:
            class_id = relationship.class_id
            for object_id in relationship.object_id_list.split(","):
                d = relationship_dict.setdefault(int(object_id), {})
                d.setdefault(class_id, []).append(relationship)
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                db_map_dict = object_item.data(Qt.UserRole + 1)
                if db_map not in db_map_dict:
                    # Can someone be adding relationships where one of the objects doesn't exist in the same db?
                    continue
                object_ = db_map_dict[db_map]
                object_id = object_['id']
                if object_id not in relationship_dict:
                    continue
                class_relationship_dict = relationship_dict[object_id]
                for k in range(object_item.rowCount()):
                    rel_cls_item = object_item.child(k, 0)
                    rel_cls_index = self.indexFromItem(rel_cls_item)
                    if self.canFetchMore(rel_cls_index):
                        continue
                    db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        # Can someone be adding relationships to a class that doesn't exist in the same db?
                        continue
                    rel_cls = db_map_dict[db_map]
                    rel_cls_id = rel_cls['id']
                    if rel_cls_id not in class_relationship_dict:
                        continue
                    relationships = class_relationship_dict[rel_cls_id]
                    self.add_relationships_to_class(db_map, relationships, rel_cls_item)

    def add_objects_to_class(self, db_map, objects, object_class_item):
        existing_rows = [
            [object_class_item.child(j, 0), object_class_item.child(j, 1)] for j in range(object_class_item.rowCount())
        ]
        existing_row_d = {row[0].text(): row for row in existing_rows}
        new_rows = []
        for object_ in objects:
            if object_.name in existing_row_d:
                # Already in model, append db_map information
                object_item, db_item = existing_row_d[object_.name]
                db_map_dict = object_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = object_._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
                # Add relationship classes from this db if fetched
                object_index = self.indexFromItem(object_item)
                if not self.canFetchMore(object_index):
                    relationship_classes = db_map.wide_relationship_class_list(object_class_id=object_.class_id)
                    self.add_relationships_classes_to_object(db_map, relationship_classes, object_item)
            else:
                new_rows.append(self.new_object_row(db_map, object_))
        for row in new_rows:
            object_class_item.appendRow(row)

    def add_relationships_classes_to_object(self, db_map, relationship_classes, object_item):
        existing_rows = [[object_item.child(j, 0), object_item.child(j, 1)] for j in range(object_item.rowCount())]
        existing_row_d = {(row[0].text(), row[0].data(Qt.ToolTipRole)): row for row in existing_rows}
        new_rows = []
        for rel_cls in relationship_classes:
            if (rel_cls.name, rel_cls.object_class_name_list) in existing_row_d:
                # Already in model, append db_map information
                rel_cls_item, db_item = existing_row_d[rel_cls.name, rel_cls.object_class_name_list]
                db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = rel_cls._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
                # Add relationships from this db if fetched
                rel_cls_index = self.indexFromItem(rel_cls_item)
                if not self.canFetchMore(rel_cls_index):
                    object_id = object_item.data(Qt.UserRole + 1)[db_map]['id']
                    relationships = db_map.wide_relationship_list(class_id=rel_cls.id, object_id=object_id)
                    self.add_relationships_to_class(db_map, relationships, rel_cls_item)
            else:
                new_rows.append(self.new_relationship_class_row(db_map, rel_cls))
        for row in new_rows:
            object_item.appendRow(row)

    def add_relationships_to_class(self, db_map, relationships, rel_cls_item):
        existing_rows = [[rel_cls_item.child(j, 0), rel_cls_item.child(j, 1)] for j in range(rel_cls_item.rowCount())]
        existing_row_d = {row[0].text(): row for row in existing_rows}
        new_rows = []
        for relationship in relationships:
            if relationship.object_name_list in existing_row_d:
                # Already in model, append db_map information
                relationship_item, db_item = existing_row_d[relationship.object_name_list]
                db_map_dict = relationship_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = relationship._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
            else:
                new_rows.append(self.new_relationship_row(db_map, relationship))
        for row in new_rows:
            rel_cls_item.appendRow(row)

    def update_object_classes(self, db_map, object_classes):
        """Update object classes in the model.
        This of course means updating the object class name in relationship class items.
        """
        object_class_d = {x.id: x for x in object_classes}
        existing_rows = [
            [self.root_item.child(i, 0), self.root_item.child(i, 1)] for i in range(self.root_item.rowCount())
        ]
        existing_row_d = {row[0].text(): (i, row) for i, row in enumerate(existing_rows)}
        removed_rows = []
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i)
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            object_class = db_map_dict[db_map]
            object_class_id = object_class['id']
            upd_object_class = object_class_d.pop(object_class_id, None)
            if not upd_object_class:
                continue
            existing_i, existing_row = existing_row_d.get(upd_object_class.name, (i, None))
            if i != existing_i:
                # Already another item with that name, in a different position
                removed_rows.append(i)
                object_class_item, db_item = existing_row
                db_map_dict = object_class_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = upd_object_class._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
                # Add objects from this db if fetched
                object_class_index = self.indexFromItem(object_class_item)
                if not self.canFetchMore(object_class_index):
                    self.add_objects_to_class(db_map, db_map.object_list(class_id=object_class_id), object_class_item)
            else:
                db_map_dict[db_map] = upd_object_class._asdict()
                object_class_item.setData(upd_object_class.name, Qt.DisplayRole)
                object_class_item.setData(upd_object_class.description, Qt.ToolTipRole)
            # Update child relationship class items
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                for k in range(object_item.rowCount()):
                    rel_cls_item = object_item.child(k, 0)
                    db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        continue
                    rel_cls = db_map_dict[db_map]
                    obj_cls_name_list = rel_cls['object_class_name_list'].split(',')
                    obj_cls_id_list = [int(x) for x in rel_cls['object_class_id_list'].split(',')]
                    for l, id_ in enumerate(obj_cls_id_list):
                        if id_ == object_class_id:
                            obj_cls_name_list[l] = upd_object_class.name
                    rel_cls['object_class_name_list'] = ",".join(obj_cls_name_list)
                    rel_cls_item.setData(",".join(obj_cls_name_list), Qt.ToolTipRole)
        self.remove_object_class_rows(db_map, removed_rows)

    def update_objects(self, db_map, objects):
        """Update object in the model.
        This of course means updating the object name in relationship items.
        """
        object_d = {}
        for object_ in objects:
            object_d.setdefault(object_.class_id, {}).update({object_.id: object_})
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            object_class = db_map_dict[db_map]
            object_class_id = object_class['id']
            class_object_dict = object_d.pop(object_class_id, None)
            if not class_object_dict:
                continue
            existing_rows = [
                [object_class_item.child(j, 0), object_class_item.child(j, 1)]
                for j in range(object_class_item.rowCount())
            ]
            existing_row_d = {row[0].text(): (j, row) for j, row in enumerate(existing_rows)}
            removed_rows = []
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                db_map_dict = object_item.data(Qt.UserRole + 1)
                if db_map not in db_map_dict:
                    continue
                object_ = db_map_dict[db_map]
                object_id = object_['id']
                upd_object = class_object_dict.pop(object_id, None)
                if not upd_object:
                    continue
                existing_j, existing_row = existing_row_d.get(upd_object.name, (j, None))
                if j != existing_j:
                    # Already another item with that name, in a different position
                    removed_rows.append(j)
                    object_item, db_item = existing_row
                    db_map_dict = object_item.data(Qt.UserRole + 1)
                    db_map_dict[db_map] = upd_object._asdict()
                    databases = db_item.data(Qt.DisplayRole)
                    databases += "," + self._parent.db_map_to_name[db_map]
                    db_item.setData(databases, Qt.DisplayRole)
                    # Add relationship classes from this db if fetched
                    object_index = self.indexFromItem(object_item)
                    if not self.canFetchMore(object_index):
                        relationship_classes = db_map.wide_relationship_class_list(object_class_id=object_class_id)
                        self.add_relationships_classes_to_object(db_map, relationship_classes, object_item)
                else:
                    db_map_dict[db_map] = upd_object._asdict()
                    object_item.setData(upd_object.name, Qt.DisplayRole)
                    object_item.setData(upd_object.description, Qt.ToolTipRole)
                # Update child relationship items
                for k in range(object_item.rowCount()):
                    rel_cls_item = object_item.child(k, 0)
                    for l in range(rel_cls_item.rowCount()):
                        relationship_item = rel_cls_item.child(l, 0)
                        db_map_dict = relationship_item.data(Qt.UserRole + 1)
                        if db_map not in db_map_dict:
                            continue
                        relationship = db_map_dict[db_map]
                        object_name_list = relationship['object_name_list'].split(',')
                        object_id_list = [int(x) for x in relationship['object_id_list'].split(',')]
                        for m, id_ in enumerate(object_id_list):
                            if id_ == object_id:
                                object_name_list[m] = upd_object.name
                        relationship['object_name_list'] = ",".join(object_name_list)
                        relationship_item.setData(",".join(object_name_list), Qt.DisplayRole)
            self.remove_object_rows(db_map, removed_rows, object_class_item)

    def update_relationship_classes(self, db_map, relationship_classes):
        """Update relationship classes in the model."""
        relationship_class_dict = {}
        for rel_cls in relationship_classes:
            for object_class_id in rel_cls.object_class_id_list.split(","):
                relationship_class_dict.setdefault(int(object_class_id), {}).update({rel_cls.id: rel_cls})
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            object_class = db_map_dict[db_map]
            object_class_id = object_class['id']
            class_rel_cls_dict = relationship_class_dict.pop(object_class_id, None)
            if not class_rel_cls_dict:
                continue
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                existing_rows = [
                    [object_item.child(k, 0), object_item.child(k, 1)] for k in range(object_item.rowCount())
                ]
                existing_row_d = {
                    (row[0].text(), row[0].data(Qt.ToolTipRole)): (i, row) for i, row in enumerate(existing_rows)
                }
                removed_rows = []
                for k in range(object_item.rowCount()):
                    rel_cls_item = object_item.child(k, 0)
                    db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        continue
                    rel_cls = db_map_dict[db_map]
                    rel_cls_id = rel_cls['id']
                    if rel_cls_id not in class_rel_cls_dict:
                        continue
                    upd_rel_cls = class_rel_cls_dict[rel_cls_id]
                    upd_rel_cls_key = (upd_rel_cls.name, upd_rel_cls.object_class_name_list)
                    existing_k, existing_row = existing_row_d.get(upd_rel_cls_key, (k, None))
                    if k != existing_k:
                        # Already another item with that name, in a different position
                        removed_rows.append(k)
                        rel_cls_item, db_item = existing_row
                        db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                        db_map_dict[db_map] = upd_rel_cls._asdict()
                        databases = db_item.data(Qt.DisplayRole)
                        databases += "," + self._parent.db_map_to_name[db_map]
                        db_item.setData(databases, Qt.DisplayRole)
                        # Add relationships from this db if fetched
                        rel_cls_index = self.indexFromItem(rel_cls_item)
                        if not self.canFetchMore(rel_cls_index):
                            object_id = object_item.data(Qt.UserRole + 1)[db_map]['id']
                            relationships = db_map.wide_relationship_list(class_id=rel_cls_id, object_id=object_id)
                            self.add_relationships_to_class(db_map, relationships, rel_cls_item)
                    else:
                        db_map_dict[db_map] = upd_rel_cls._asdict()
                        rel_cls_item.setData(upd_rel_cls.name, Qt.DisplayRole)
                self.remove_relationship_class_rows(db_map, removed_rows, object_item)

    def update_relationships(self, db_map, relationships):
        """Update relationships in the model.
        Move rows if the objects in the relationship change."""
        relationship_dict = {}
        for relationship in relationships:
            relationship_dict.setdefault(relationship.class_id, {}).update({relationship.id: relationship})
        relationships_to_add = set()
        for i in range(self.root_item.rowCount()):
            object_class_item = self.root_item.child(i, 0)
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                for k in range(object_item.rowCount()):
                    rel_cls_item = object_item.child(k, 0)
                    db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        continue
                    rel_cls = db_map_dict[db_map]
                    rel_cls_id = rel_cls['id']
                    if rel_cls_id not in relationship_dict:
                        continue
                    class_relationship_dict = relationship_dict[rel_cls_id]
                    existing_rows = [
                        [rel_cls_item.child(k, 0), rel_cls_item.child(k, 1)] for k in range(rel_cls_item.rowCount())
                    ]
                    existing_row_d = {row[0].text(): (i, row) for i, row in enumerate(existing_rows)}
                    removed_rows = []
                    for l in range(rel_cls_item.rowCount()):
                        relationship_item = rel_cls_item.child(l, 0)
                        db_map_dict = relationship_item.data(Qt.UserRole + 1)
                        if db_map not in db_map_dict:
                            continue
                        relationship = db_map_dict[db_map]
                        relationship_id = relationship['id']
                        if relationship_id not in class_relationship_dict:
                            continue
                        upd_relationship = class_relationship_dict[relationship_id]
                        if upd_relationship.object_id_list != relationship['object_id_list']:
                            # Object id list changed, we don't know if the item belongs here anymore
                            removed_rows.append(j)
                            relationships_to_add.add(upd_relationship)
                        else:
                            existing_l, existing_row = existing_row_d.get(upd_relationship.object_name_list, (l, None))
                            if l != existing_l:
                                # Already another item with that name, in a different position
                                removed_rows.append(l)
                                relationship_item, db_item = existing_row
                                db_map_dict = relationship_item.data(Qt.UserRole + 1)
                                db_map_dict[db_map] = upd_relationship._asdict()
                                databases = db_item.data(Qt.DisplayRole)
                                databases += "," + self._parent.db_map_to_name[db_map]
                                db_item.setData(databases, Qt.DisplayRole)
                            else:
                                db_map_dict[db_map] = upd_relationship._asdict()
                    self.remove_relationship_rows(db_map, removed_rows, rel_cls_item)
        self.add_relationships(db_map, relationships_to_add)

    def remove_object_class_rows(self, db_map, removed_rows):
        for row in sorted(removed_rows, reverse=True):
            object_class_item = self.root_item.child(row, 0)
            db_map_dict = object_class_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map, None)
            if not db_map_dict:
                self.root_item.removeRow(row)
            else:
                db_item = self.root_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)
                self.remove_object_rows(db_map, range(object_class_item.rowCount()), object_class_item)

    def remove_object_rows(self, db_map, removed_rows, object_class_item):
        for row in sorted(removed_rows, reverse=True):
            object_item = object_class_item.child(row, 0)
            db_map_dict = object_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map, None)
            if not db_map_dict:
                object_class_item.removeRow(row)
            else:
                db_item = object_class_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)
                self.remove_relationship_class_rows(db_map, range(object_item.rowCount()), object_item)

    def remove_relationship_class_rows(self, db_map, removed_rows, object_item):
        for row in sorted(removed_rows, reverse=True):
            rel_cls_item = object_item.child(row, 0)
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map, None)
            if not db_map_dict:
                object_item.removeRow(row)
            else:
                db_item = object_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)
                self.remove_relationship_rows(db_map, range(rel_cls_item.rowCount()), rel_cls_item)

    def remove_relationship_rows(self, db_map, removed_rows, rel_cls_item):
        for row in sorted(removed_rows, reverse=True):
            relationship_item = rel_cls_item.child(row, 0)
            db_map_dict = relationship_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map)
            if not db_map_dict:
                rel_cls_item.removeRow(row)
            else:
                db_item = rel_cls_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)

    def remove_object_classes(self, db_map, removed_ids):
        """Remove object classes and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_object_class_rows = []
        removed_relationship_class_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type not in ('object_class', 'relationship_class'):
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            if visited_type == 'object_class':
                visited_id = visited['id']
                if visited_id in removed_ids:
                    removed_object_class_rows.append(visited_item.row())
            elif visited_type == 'relationship_class':
                object_class_id_list = visited['object_class_id_list']
                if any(str(id) in object_class_id_list.split(',') for id in removed_ids):
                    visited_index = self.indexFromItem(visited_item.parent())
                    removed_relationship_class_row_d.setdefault(visited_index, []).append(visited_item.row())
        for object_index, rows in removed_relationship_class_row_d.items():
            object_item = self.itemFromIndex(object_index)
            self.remove_relationship_class_rows(db_map, rows, object_item)
        self.remove_object_class_rows(db_map, removed_object_class_rows)

    def remove_objects(self, db_map, removed_ids):
        """Remove objects and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_object_row_d = {}
        removed_relationship_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type not in ('object', 'relationship'):
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            visited_index = self.indexFromItem(visited_item)
            if visited_type == 'object':
                visited_id = visited['id']
                if visited_id in removed_ids:
                    removed_object_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
            elif visited_type == 'relationship':
                object_id_list = visited['object_id_list']
                if any(id in [int(x) for x in object_id_list.split(',')] for id in removed_ids):
                    removed_relationship_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
        for rel_cls_index, rows in removed_relationship_row_d.items():
            rel_cls_item = self.itemFromIndex(rel_cls_index)
            self.remove_relationship_rows(db_map, rows, rel_cls_item)
        for obj_cls_index, rows in removed_object_row_d.items():
            obj_cls_item = self.itemFromIndex(obj_cls_index)
            self.remove_object_rows(db_map, rows, obj_cls_item)

    def remove_relationship_classes(self, db_map, removed_ids):
        """Remove relationship classes and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_class_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship_class':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            if visited['id'] in removed_ids:
                visited_index = self.indexFromItem(visited_item)
                removed_relationship_class_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
        for object_index, rows in removed_relationship_class_row_d.items():
            object_item = self.itemFromIndex(object_index)
            self.remove_relationship_class_rows(db_map, rows, object_item)

    def remove_relationships(self, db_map, removed_ids):
        """Remove relationships."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            if visited['id'] in removed_ids:
                visited_index = self.indexFromItem(visited_item)
                removed_relationship_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
        for rel_cls_index, rows in removed_relationship_row_d.items():
            rel_cls_item = self.itemFromIndex(rel_cls_index)
            self.remove_relationship_rows(db_map, rows, rel_cls_item)

    def next_relationship_index(self, index):
        """Find and return next ocurrence of relationship item."""
        if index.data(Qt.UserRole) != 'relationship':
            return None
        object_name_list = index.data(Qt.DisplayRole)
        class_name = index.parent().data(Qt.DisplayRole)
        object_class_name_list = index.parent().data(Qt.ToolTipRole)
        items = [
            item
            for item in self.findItems(object_name_list, Qt.MatchExactly | Qt.MatchRecursive, column=0)
            if item.parent().data(Qt.DisplayRole) == class_name
            and item.parent().data(Qt.ToolTipRole) == object_class_name_list
        ]
        position = None
        for i, item in enumerate(items):
            if index == self.indexFromItem(item):
                position = i
                break
        if position is None:
            return None
        position = (position + 1) % len(items)
        return self.indexFromItem(items[position])


class RelationshipTreeModel(QStandardItemModel):
    """A model to display relationships in a tree.
    """

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent
        self.db_maps = parent.db_maps
        self.root_item = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self._fetched = set()

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""
        if index.column() != 0:
            return super().data(index, role)
        if role == Qt.ForegroundRole:
            item_type = index.data(Qt.UserRole)
            if item_type.endswith('class') and not self.hasChildren(index):
                return QBrush(Qt.gray)
        if role == Qt.DecorationRole:
            item_type = index.data(Qt.UserRole)
            if item_type == 'root':
                return QIcon(":/symbols/Spine_symbol.png")
            if item_type == 'relationship_class':
                return self._parent.icon_mngr.relationship_icon(index.data(Qt.ToolTipRole))
            if item_type == 'relationship':
                return self._parent.icon_mngr.relationship_icon(index.parent().data(Qt.ToolTipRole))
        return super().data(index, role)

    def hasChildren(self, parent):
        """Return True if not fetched, so the user can try and expand it."""
        if not parent.isValid():
            return super().hasChildren(parent)
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return super().hasChildren(parent)
        if parent_type == 'relationship':
            return False
        if not self.canFetchMore(parent):
            return super().hasChildren(parent)
        return True

    def canFetchMore(self, parent):
        """Return True if not fetched."""
        if not parent.isValid():
            return True
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return True
        db_map_dict = parent.data(Qt.UserRole + 1)
        return any((db_map, item['id']) not in self._fetched for db_map, item in db_map_dict.items())

    @busy_effect
    def fetchMore(self, parent):
        """Build the deeper level of the tree"""
        if not parent.isValid():
            return False
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'root':
            return False
        parent_type = parent.data(Qt.UserRole)
        if parent_type == 'relationship_class':
            parent_db_map_dict = parent.data(Qt.UserRole + 1)
            rel_cls_item = self.itemFromIndex(parent)
            for db_map, relationship_class in parent_db_map_dict.items():
                relationships = db_map.wide_relationship_list(class_id=relationship_class['id'])
                self.add_relationships_to_class(db_map, relationships, rel_cls_item)
                self._fetched.add((db_map, relationship_class['id']))
        self.dataChanged.emit(parent, parent)

    def build_tree(self):
        """Build the first level of the tree"""
        self.clear()
        self.setHorizontalHeaderLabels(["item", "databases"])
        self._fetched = set()
        self.root_item = QStandardItem('root')
        self.root_item.setData('root', Qt.UserRole)
        db_item = QStandardItem(", ".join([self._parent.db_map_to_name[x] for x in self.db_maps]))
        for db_map in self.db_maps:
            self.add_relationship_classes(db_map, db_map.wide_relationship_class_list())
        self.appendRow([self.root_item, db_item])

    def new_relationship_class_row(self, db_map, relationship_class):
        """Returns new relationship class item."""
        relationship_class_item = QStandardItem(relationship_class.name)
        relationship_class_item.setData('relationship_class', Qt.UserRole)
        relationship_class_item.setData({db_map: relationship_class._asdict()}, Qt.UserRole + 1)
        relationship_class_item.setData(relationship_class.object_class_name_list, Qt.ToolTipRole)
        relationship_class_item.setData(self.bold_font, Qt.FontRole)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [relationship_class_item, db_item]

    def new_relationship_row(self, db_map, relationship):
        """Returns new relationship item."""
        relationship_item = QStandardItem(relationship.object_name_list)
        relationship_item.setData('relationship', Qt.UserRole)
        relationship_item.setData({db_map: relationship._asdict()}, Qt.UserRole + 1)
        db_item = QStandardItem(self._parent.db_map_to_name[db_map])
        return [relationship_item, db_item]

    def add_relationship_classes(self, db_map, relationship_classes):
        """Add relationship class items to the model."""
        existing_rows = [
            [self.root_item.child(j, 0), self.root_item.child(j, 1)] for j in range(self.root_item.rowCount())
        ]
        existing_row_d = {(row[0].text(), row[0].data(Qt.ToolTipRole)): row for row in existing_rows}
        new_rows = []
        for rel_cls in relationship_classes:
            if (rel_cls.name, rel_cls.object_class_name_list) in existing_row_d:
                # Already in model, append db_map information
                rel_cls_item, db_item = existing_row_d[rel_cls.name, rel_cls.object_class_name_list]
                db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = rel_cls._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
            else:
                new_rows.append(self.new_relationship_class_row(db_map, rel_cls))
        for row in new_rows:
            self.root_item.appendRow(row)

    def add_relationships(self, db_map, relationships):
        """Add relationship items to model."""
        relationship_dict = {}
        for relationship in relationships:
            relationship_dict.setdefault(relationship.class_id, list()).append(relationship)
        for i in range(self.root_item.rowCount()):
            rel_cls_item = self.root_item.child(i, 0)
            rel_cls_index = self.indexFromItem(rel_cls_item)
            if self.canFetchMore(rel_cls_index):
                continue
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                # Can someone be adding relationships to a class that doesn't exist in the same db?
                continue
            relationship_class = db_map_dict[db_map]
            relationship_class_id = relationship_class['id']
            if relationship_class_id not in relationship_dict:
                continue
            relationships = relationship_dict[relationship_class_id]
            self.add_relationships_to_class(db_map, relationships, rel_cls_item)

    def add_relationships_to_class(self, db_map, relationships, rel_cls_item):
        existing_rows = [[rel_cls_item.child(j, 0), rel_cls_item.child(j, 1)] for j in range(rel_cls_item.rowCount())]
        existing_row_d = {row[0].text(): row for row in existing_rows}
        new_rows = []
        for relationship in relationships:
            if relationship.object_name_list in existing_row_d:
                # Already in model, append db_map information
                relationship_item, db_item = existing_row_d[relationship.object_name_list]
                db_map_dict = relationship_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = relationship._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
            else:
                new_rows.append(self.new_relationship_row(db_map, relationship))
        for row in new_rows:
            rel_cls_item.appendRow(row)

    def update_object_classes(self, db_map, object_classes):
        """Update object classes in the model.
        This just means updating the object class name in relationship class items.
        """
        object_class_d = {x.id: x.name for x in object_classes}
        for i in range(self.root_item.rowCount()):
            rel_cls_item = self.root_item.child(i, 0)
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            rel_cls = db_map_dict[db_map]
            obj_cls_name_list = rel_cls['object_class_name_list'].split(',')
            obj_cls_id_list = [int(x) for x in rel_cls['object_class_id_list'].split(',')]
            for k, id_ in enumerate(obj_cls_id_list):
                if id_ in object_class_d:
                    obj_cls_name_list[k] = object_class_d[id_]
            rel_cls['object_class_name_list'] = ",".join(obj_cls_name_list)
            rel_cls_item.setData(",".join(obj_cls_name_list), Qt.ToolTipRole)

    def update_objects(self, db_map, objects):
        """Update object in the model.
        This just means updating the object name in relationship items.
        """
        object_d = {x.id: x.name for x in objects}
        for i in range(self.root_item.rowCount()):
            relationship_class_item = self.root_item.child(i)
            for j in range(relationship_class_item.rowCount()):
                relationship_item = relationship_class_item.child(j)
                db_map_dict = relationship_item.data(Qt.UserRole + 1)
                if db_map not in db_map_dict:
                    continue
                relationship = db_map_dict[db_map]
                object_id_list = [int(x) for x in relationship['object_id_list'].split(",")]
                object_name_list = relationship['object_name_list'].split(",")
                for k, id_ in enumerate(object_id_list):
                    if id_ in object_d:
                        object_name_list[k] = object_d[id_]
                str_object_name_list = ",".join(object_name_list)
                relationship['object_name_list'] = str_object_name_list
                relationship_item.setData(str_object_name_list, Qt.DisplayRole)

    def update_relationship_classes(self, db_map, relationship_classes):
        """Update relationship classes in the model."""
        rel_cls_d = {x.id: x for x in relationship_classes}
        existing_rows = [
            [self.root_item.child(j, 0), self.root_item.child(j, 1)] for j in range(self.root_item.rowCount())
        ]
        existing_row_d = {(row[0].text(), row[0].data(Qt.ToolTipRole)): (i, row) for i, row in enumerate(existing_rows)}
        removed_rows = []
        for i in range(self.root_item.rowCount()):
            rel_cls_item = self.root_item.child(i)
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            rel_cls = db_map_dict[db_map]
            rel_cls_id = rel_cls['id']
            upd_rel_cls = rel_cls_d.pop(rel_cls_id, None)
            if not upd_rel_cls:
                continue
            rel_cls_key = (upd_rel_cls.name, upd_rel_cls.object_class_name_list)
            existing_i, existing_row = existing_row_d.get(rel_cls_key, (i, None))
            if existing_i != i:
                # Already there
                removed_rows.append(i)
                rel_cls_item, db_item = existing_row
                db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
                db_map_dict[db_map] = upd_rel_cls._asdict()
                databases = db_item.data(Qt.DisplayRole)
                databases += "," + self._parent.db_map_to_name[db_map]
                db_item.setData(databases, Qt.DisplayRole)
                # Add relationships from this db if fetched
                rel_cls_index = self.indexFromItem(rel_cls_item)
                if not self.canFetchMore(rel_cls_index):
                    relationships = db_map.wide_relationship_list(class_id=rel_cls_id)
                    self.add_relationships_to_class(db_map, relationships, rel_cls_item)
            else:
                db_map_dict[db_map] = upd_rel_cls._asdict()
                rel_cls_item.setData(upd_rel_cls.name, Qt.DisplayRole)
                rel_cls_item.setData(upd_rel_cls.object_class_name_list, Qt.ToolTipRole)
        self.remove_relationship_class_rows(db_map, removed_rows)

    def update_relationships(self, db_map, relationships):
        """Update relationships in the model."""
        relationship_d = {}
        for rel in relationships:
            relationship_d.setdefault(rel.class_id, {}).update({rel.id: rel})
        for i in range(self.root_item.rowCount()):
            rel_cls_item = self.root_item.child(i)
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            if db_map not in db_map_dict:
                continue
            rel_cls = db_map_dict[db_map]
            rel_cls_id = rel_cls['id']
            class_relationship_dict = relationship_d.pop(rel_cls_id, None)
            if not class_relationship_dict:
                continue
            existing_rows = [
                [rel_cls_item.child(j, 0), rel_cls_item.child(j, 1)] for j in range(rel_cls_item.rowCount())
            ]
            existing_row_d = {row[0].text(): (i, row) for i, row in enumerate(existing_rows)}
            removed_rows = []
            for j in range(rel_cls_item.rowCount()):
                relationship_item = rel_cls_item.child(j)
                db_map_dict = relationship_item.data(Qt.UserRole + 1)
                if db_map not in db_map_dict:
                    continue
                relationship = db_map_dict[db_map]
                relationship_id = relationship['id']
                upd_relationship = class_relationship_dict.pop(relationship_id, None)
                if not upd_relationship:
                    continue
                existing_j, existing_row = existing_row_d.get(upd_relationship.object_name_list, (j, None))
                if existing_j != j:
                    # Already there
                    removed_rows.append(j)
                    relationship_item, db_item = existing_row
                    db_map_dict = relationship_item.data(Qt.UserRole + 1)
                    db_map_dict[db_map] = upd_relationship._asdict()
                    databases = db_item.data(Qt.DisplayRole)
                    databases += "," + self._parent.db_map_to_name[db_map]
                    db_item.setData(databases, Qt.DisplayRole)
                else:
                    db_map_dict[db_map] = upd_relationship._asdict()
                    relationship_item.setData(upd_relationship.object_name_list, Qt.DisplayRole)
            self.remove_relationship_rows(db_map, removed_rows, rel_cls_item)

    def remove_relationship_class_rows(self, db_map, removed_rows):
        for row in sorted(removed_rows, reverse=True):
            rel_cls_item = self.root_item.child(row, 0)
            db_map_dict = rel_cls_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map, None)
            if not db_map_dict:
                self.root_item.removeRow(row)
            else:
                db_item = self.root_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)
                self.remove_relationship_rows(db_map, range(rel_cls_item.rowCount()), rel_cls_item)

    def remove_relationship_rows(self, db_map, removed_rows, rel_cls_item):
        for row in sorted(removed_rows, reverse=True):
            relationship_item = rel_cls_item.child(row, 0)
            db_map_dict = relationship_item.data(Qt.UserRole + 1)
            db_map_dict.pop(db_map, None)
            if not db_map_dict:
                rel_cls_item.removeRow(row)
            else:
                db_item = rel_cls_item.child(row, 1)
                databases = db_item.data(Qt.DisplayRole).split(",")
                if self._parent.db_map_to_name[db_map] in databases:
                    databases.remove(self._parent.db_map_to_name[db_map])
                    db_item.setData(",".join(databases), Qt.DisplayRole)

    def remove_object_classes(self, db_map, removed_ids):
        """Remove object classes and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_class_rows = []
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship_class':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            object_class_id_list = visited['object_class_id_list']
            if any(str(id) in object_class_id_list.split(',') for id in removed_ids):
                removed_relationship_class_rows.append(visited_item.row())
        self.remove_relationship_class_rows(db_map, removed_relationship_class_rows)

    def remove_objects(self, db_map, removed_ids):
        """Remove objects and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            object_id_list = visited['object_id_list']
            if any(str(id) in object_id_list.split(',') for id in removed_ids):
                visited_index = self.indexFromItem(visited_item)
                removed_relationship_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
        for rel_cls_index, rows in removed_relationship_row_d.items():
            rel_cls_item = self.itemFromIndex(rel_cls_index)
            self.remove_relationship_rows(db_map, rows, rel_cls_item)

    def remove_relationship_classes(self, db_map, removed_ids):
        """Remove relationship classes and their childs."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_class_rows = []
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship_class':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            visited_id = visited['id']
            if visited_id in removed_ids:
                visited_index = self.indexFromItem(visited_item)
                removed_relationship_class_rows.append(visited_index.row())
        self.remove_relationship_class_rows(db_map, removed_relationship_class_rows)

    def remove_relationships(self, db_map, removed_ids):
        """Remove relationships."""
        if not removed_ids:
            return
        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive, column=0)
        removed_relationship_row_d = {}
        for visited_item in items:
            visited_type = visited_item.data(Qt.UserRole)
            if visited_type != 'relationship':
                continue
            # Get visited
            db_map_dict = visited_item.data(Qt.UserRole + 1)
            visited = db_map_dict.get(db_map)
            if not visited:
                continue
            if visited['id'] in removed_ids:
                visited_index = self.indexFromItem(visited_item)
                removed_relationship_row_d.setdefault(visited_index.parent(), []).append(visited_index.row())
        for rel_cls_index, rows in removed_relationship_row_d.items():
            rel_cls_item = self.itemFromIndex(rel_cls_index)
            self.remove_relationship_rows(db_map, rows, rel_cls_item)
