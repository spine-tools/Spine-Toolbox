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
The SpineDBManager class

:author: P. Vennström (VTT) and M. Marin (KTH)
:date:   2.10.2019
"""

from typing import Dict
from PySide2.QtCore import QObject, Signal
from spinedb_api import DiffDatabaseMapping, SpineDBAPIError
from .helpers import IconManager


class SpineDBManager(QObject):
    """Class to manage spine DBs in a unified way.
    The idea is to share an object of this class across many mvc models and related classes
    that need to interact with a set of DBs.
    """

    msg_error = Signal("QVariant", name="msg_error")
    object_classes_added = Signal("QVariant", name="object_classes_added")
    objects_added = Signal("QVariant", name="objects_added")
    relationship_classes_added = Signal("QVariant", name="relationship_classes_added")
    relationships_added = Signal("QVariant", name="relationships_added")
    object_classes_removed = Signal("QVariant", name="object_classes_removed")
    objects_removed = Signal("QVariant", name="objects_removed")
    relationship_classes_removed = Signal("QVariant", name="relationship_classes_removed")
    relationships_removed = Signal("QVariant", name="relationships_removed")

    def __init__(self, keyed_db_maps: Dict[str, DiffDatabaseMapping]):
        """Init class."""
        super().__init__()
        self._keyed_db_maps = keyed_db_maps
        self._db_maps = list(keyed_db_maps.values())
        self._db_names = {db_map: db_name for db_name, db_map in keyed_db_maps.items()}
        self._data = {}
        self.icon_mngr = IconManager()
        self.connect_signals()

    def connect_signals(self):
        self.object_classes_added.connect(self.update_icons)

    def update_icons(self, db_map_data):
        object_classes = [item for db_map, data in db_map_data.items() for item in data]
        self.icon_mngr.setup_object_pixmaps(object_classes)

    @property
    def db_maps(self):
        return self._db_maps

    def display_database(self, db_map):
        return self._db_names.get(db_map)

    def get_data(self, db_map, item_type, id_):
        return self._data.get(db_map, {}).get(item_type, {}).get(id_, {})

    def get_object_class_ids(self, db_map):
        d = self._data.setdefault(db_map, {}).setdefault("object class", {})
        qry = db_map.query(db_map.object_class_sq)
        items = {x.id: x._asdict() for x in qry}
        d.update(items)
        self.icon_mngr.setup_object_pixmaps(items.values())
        return items.keys()

    def get_object_ids(self, db_map, class_id=None):
        d = self._data.setdefault(db_map, {}).setdefault("object", {})
        qry = db_map.query(db_map.object_sq)
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        items = {x.id: x._asdict() for x in qry}
        d.update(items)
        return items.keys()

    def get_relationship_class_ids(self, db_map, object_class_id=None):
        d = self._data.setdefault(db_map, {}).setdefault("relationship class", {})
        qry = db_map.query(db_map.wide_relationship_class_sq)
        if object_class_id:
            ids = {x.id for x in db_map.query(db_map.relationship_class_sq).filter_by(object_class_id=object_class_id)}
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        items = {x.id: x._asdict() for x in qry}
        d.update(items)
        return items.keys()

    def get_relationship_ids(self, db_map, class_id, object_id=None):
        d = self._data.setdefault(db_map, {}).setdefault("relationship", {})
        qry = db_map.query(db_map.wide_relationship_sq).filter_by(class_id=class_id)
        if object_id:
            ids = {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        items = {x.id: x._asdict() for x in qry}
        d.update(items)
        return items.keys()

    def add_items(self, input_data, item_type, method_name, signal_name):
        db_map_data = dict()
        error_log = dict()
        for db_map, items in input_data.items():
            added, error_log[db_map] = getattr(db_map, method_name)(*items)
            if not added.count():
                continue
            d = self._data.setdefault(db_map, {}).setdefault(item_type, {})
            added = {x.id: x._asdict() for x in added}
            d.update(added)
            db_map_data[db_map] = list(added.values())
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_data.values()):
            getattr(self, signal_name).emit(db_map_data)

    def add_object_classes(self, db_map_data):
        self.add_items(db_map_data, "object class", "add_object_classes", "objects_classes_added")

    def add_objects(self, db_map_data):
        self.add_items(db_map_data, "object", "add_objects", "objects_added")

    def add_relationship_classes(self, db_map_data):
        self.add_items(db_map_data, "relationship class", "add_wide_relationship_classes", "relationship_classes_added")

    def add_relationships(self, db_map_data):
        self.add_items(db_map_data, "relationship", "add_wide_relationships", "relationships_added")

    def remove_items(self, input_data):
        db_map_object_classes = dict()
        db_map_objects = dict()
        db_map_relationship_classes = dict()
        db_map_relationships = dict()
        error_log = dict()
        for db_map, items_per_type in input_data.items():
            object_classes = items_per_type.get("object class", ())
            objects = items_per_type.get("object", ())
            relationship_classes = items_per_type.get("relationship class", ())
            relationships = items_per_type.get("relationship", ())
            try:
                db_map.remove_items(
                    object_class_ids={x['id'] for x in object_classes},
                    object_ids={x['id'] for x in objects},
                    relationship_class_ids={x['id'] for x in relationship_classes},
                    relationship_ids={x['id'] for x in relationships},
                )
            except SpineDBAPIError as err:
                error_log[db_map] = err
                continue
            db_map_object_classes[db_map] = object_classes
            db_map_objects[db_map] = objects
            db_map_relationship_classes[db_map] = relationship_classes
            db_map_relationships[db_map] = relationships
            # TODO: remove ids from _data
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_object_classes.values()):
            self.object_classes_removed.emit(db_map_object_classes)
        if any(db_map_objects.values()):
            self.objects_removed.emit(db_map_objects)
        if any(db_map_relationship_classes.values()):
            self.relationship_classes_removed.emit(db_map_relationship_classes)
        if any(db_map_relationships.values()):
            self.relationships_removed.emit(db_map_relationships)
