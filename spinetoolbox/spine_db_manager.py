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
import pprint
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
    object_classes_updated = Signal("QVariant", name="object_classes_updated")
    objects_updated = Signal("QVariant", name="objects_updated")
    relationship_classes_updated = Signal("QVariant", name="relationship_classes_updated")
    relationships_updated = Signal("QVariant", name="relationships_updated")

    def __init__(self, keyed_db_maps: Dict[str, DiffDatabaseMapping]):
        """Init class."""
        super().__init__()
        self._keyed_db_maps = keyed_db_maps
        self._db_maps = list(keyed_db_maps.values())
        self._db_names = {db_map: db_name for db_name, db_map in keyed_db_maps.items()}
        self._data = {}
        self.icon_mngr = IconManager()
        self.connect_signals()

    @property
    def db_maps(self):
        return self._db_maps

    def display_database(self, db_map):
        return self._db_names.get(db_map)

    def connect_signals(self):
        """Connect signals."""
        # On cascade remove
        self.object_classes_removed.connect(self.cascade_remove_relationship_classes)
        self.objects_removed.connect(self.cascade_remove_relationships)
        # On cascade update
        self.object_classes_updated.connect(self.cascade_update_relationship_classes)
        self.objects_updated.connect(self.cascade_update_relationships)
        # Track added
        self.object_classes_added.connect(lambda db_map_data: self.track_items("object class", db_map_data))
        self.objects_added.connect(lambda db_map_data: self.track_items("object", db_map_data))
        self.relationship_classes_added.connect(lambda db_map_data: self.track_items("relationship class", db_map_data))
        self.relationships_added.connect(lambda db_map_data: self.track_items("relationship", db_map_data))
        # Untrack removed
        self.object_classes_removed.connect(lambda db_map_data: self.stop_tracking_items("object class", db_map_data))
        self.objects_removed.connect(lambda db_map_data: self.stop_tracking_items("object", db_map_data))
        self.relationship_classes_removed.connect(
            lambda db_map_data: self.stop_tracking_items("relationship class", db_map_data)
        )
        self.relationships_removed.connect(lambda db_map_data: self.stop_tracking_items("relationship", db_map_data))
        # Update tracking information
        self.object_classes_updated.connect(lambda db_map_data: self.track_items("object class", db_map_data))
        self.objects_updated.connect(lambda db_map_data: self.track_items("object", db_map_data))
        self.relationship_classes_updated.connect(
            lambda db_map_data: self.track_items("relationship class", db_map_data)
        )
        self.relationships_updated.connect(lambda db_map_data: self.track_items("relationship", db_map_data))
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)

    def track_items(self, item_type, db_map_data):
        """Track items. Updates the internal dictionaries that hold the items data.
        It works for both insert and update operations.

        Args:
            item_type (str)
            db_map_data (dict): maps DiffDatabaseMapping instances to lists of items to track
        """
        for db_map, items in db_map_data.items():
            self._data.setdefault(db_map, {}).setdefault(item_type, {}).update({x["id"]: x for x in items})

    def stop_tracking_items(self, item_type, db_map_data):
        """Untrack items. Pop entries from the internal dicts that hold the items data.

        Args:
            item_type (str)
            db_map_data (dict): maps DiffDatabaseMapping instances to lists of items to untrack
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._data.setdefault(db_map, {}).setdefault(item_type, {}).pop(item["id"])

    def update_icons(self, db_map_data):
        object_classes = [item for db_map, data in db_map_data.items() for item in data]
        self.icon_mngr.setup_object_pixmaps(object_classes)

    def get_data(self, db_map, item_type, id_):
        """Get data from internal dictionaries.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            id_ (int)
        """
        return self._data.get(db_map, {}).get(item_type, {}).get(id_, {})

    def get_object_classes(self, db_map):
        """Get object classes from database.

        Args:
            db_map (DiffDatabaseMapping)
        """
        qry = db_map.query(db_map.object_class_sq)
        items = [x._asdict() for x in qry]
        self.track_items("object class", {db_map: items})
        self.update_icons({db_map: items})
        return items

    def get_objects(self, db_map, class_id=None):
        """Get objects from database.

        Args:
            db_map (DiffDatabaseMapping)
            class_id (int)
        """
        qry = db_map.query(db_map.object_sq)
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        items = [x._asdict() for x in qry]
        self.track_items("object", {db_map: items})
        return items

    def get_relationship_classes(self, db_map, object_class_id=None):
        """Get relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)
            object_class_id (int)
        """
        qry = db_map.query(db_map.wide_relationship_class_sq)
        if object_class_id:
            ids = {x.id for x in db_map.query(db_map.relationship_class_sq).filter_by(object_class_id=object_class_id)}
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.track_items("relationship class", {db_map: items})
        return items

    def get_relationships(self, db_map, class_id, object_id=None):
        """Get relationships from database.

        Args:
            db_map (DiffDatabaseMapping)
            class_id (int)
            object_id (int)
        """
        qry = db_map.query(db_map.wide_relationship_sq).filter_by(class_id=class_id)
        if object_id:
            ids = {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.track_items("relationship", {db_map: items})
        return items

    def add_or_update_items(self, db_map_data, item_type, method_name, signal_name):
        """Adds or update items.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items to add or update
            item_type (str): the type of item to add or update
            method_name (str): DiffDatabaseMapping method attribute to perform the operation
            signal_name (str) : SpineDBManager signal attribute to emit with added or updated data
        """
        db_map_data_out = dict()
        error_log = dict()
        for db_map, items in db_map_data.items():
            items, error_log[db_map] = getattr(db_map, method_name)(*items)
            if not items.count():
                continue
            db_map_data_out[db_map] = [x._asdict() for x in items]
        if any(error_log.values()):
            self.msg_error.emit(error_log)
        if any(db_map_data_out.values()):
            getattr(self, signal_name).emit(db_map_data_out)

    def add_object_classes(self, db_map_data):
        self.add_or_update_items(db_map_data, "object class", "add_object_classes", "object_classes_added")

    def add_objects(self, db_map_data):
        self.add_or_update_items(db_map_data, "object", "add_objects", "objects_added")

    def add_relationship_classes(self, db_map_data):
        self.add_or_update_items(
            db_map_data, "relationship class", "add_wide_relationship_classes", "relationship_classes_added"
        )

    def add_relationships(self, db_map_data):
        self.add_or_update_items(db_map_data, "relationship", "add_wide_relationships", "relationships_added")

    def update_object_classes(self, db_map_data):
        self.add_or_update_items(db_map_data, "object class", "update_object_classes", "object_classes_updated")

    def update_objects(self, db_map_data):
        self.add_or_update_items(db_map_data, "object", "update_objects", "objects_updated")

    def update_relationship_classes(self, db_map_data):
        self.add_or_update_items(
            db_map_data, "relationship class", "update_wide_relationship_classes", "relationship_classes_updated"
        )

    def update_relationships(self, db_map_data):
        self.add_or_update_items(db_map_data, "relationship", "update_wide_relationships", "relationships_updated")

    def remove_items(self, db_map_typed_data):
        """Remove items.

        db_map_typed_data (dict): maps DiffDatabaseMapping instances to str item type, to list of items to remove.
        """
        db_map_object_classes = dict()
        db_map_objects = dict()
        db_map_relationship_classes = dict()
        db_map_relationships = dict()
        error_log = dict()
        for db_map, items_per_type in db_map_typed_data.items():
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

    def cascade_update_relationship_classes(self, db_map_data):
        """Runs when updating object classes. Updates relationship classes in cascade."""
        db_map_data = self.find_cascading_relationship_classes(db_map_data)
        self.relationship_classes_updated.emit(db_map_data)

    def cascade_update_relationships(self, db_map_data):
        """Runs when updating objects. Updates relationships in cascade."""
        db_map_data = self.find_cascading_relationships(db_map_data)
        self.relationships_updated.emit(db_map_data)

    def cascade_remove_relationship_classes(self, db_map_data):
        """Runs when removing object classes. Removes relationship classes in cascade."""
        db_map_data = self.find_cascading_relationship_classes(db_map_data, update_names=False)
        self.relationship_classes_removed.emit(db_map_data)

    def cascade_remove_relationships(self, db_map_data):
        """Runs when removing objects. Removes relationships in cascade."""
        db_map_data = self.find_cascading_relationships(db_map_data, update_names=False)
        self.relationships_removed.emit(db_map_data)

    def find_cascading_relationship_classes(self, db_map_data, update_names=True):
        """Gets data for object classes and returns data for cascading relationship classes."""
        db_map_data_out = dict()
        for db_map, data in db_map_data.items():
            d = {x["id"]: x["name"] for x in data}
            for item in self._data.get(db_map, {}).get("relationship class", {}).values():
                object_class_id_list = [int(id_) for id_ in item["object_class_id_list"].split(",")]
                if set(d).intersection(object_class_id_list):
                    update_names and self.update_object_class_name_in_relationship_class(item, object_class_id_list, d)
                    db_map_data_out.setdefault(db_map, []).append(item)
        return db_map_data_out

    def find_cascading_relationships(self, db_map_data, update_names=True):
        """Gets data for objects and returns data for cascading relationships."""
        db_map_data_out = dict()
        for db_map, data in db_map_data.items():
            d = {x["id"]: x["name"] for x in data}
            for item in self._data.get(db_map, {}).get("relationship", {}).values():
                object_id_list = [int(id_) for id_ in item["object_id_list"].split(",")]
                if set(d).intersection(object_id_list):
                    update_names and self.update_object_name_in_relationship(item, object_id_list, d)
                    db_map_data_out.setdefault(db_map, []).append(item)
        return db_map_data_out

    @staticmethod
    def update_object_class_name_in_relationship_class(item, object_class_id_list, d):
        object_name_list = item["object_name_list"].split(",")
        object_name_list = [d.get(id_, name) for id_, name in zip(object_id_list, object_name_list)]
        item["object_name_list"] = ",".join(object_name_list)

    @staticmethod
    def update_object_name_in_relationship(item, object_id_list, d):
        object_name_list = item["object_name_list"].split(",")
        object_name_list = [d.get(id_, name) for id_, name in zip(object_id_list, object_name_list)]
        item["object_name_list"] = ",".join(object_name_list)
