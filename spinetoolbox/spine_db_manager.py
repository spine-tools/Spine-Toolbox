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
from PySide2.QtCore import QObject, Signal, Slot
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

    parameter_definitions_updated = Signal("QVariant", name="parameter_definitions_updated")
    parameter_values_updated = Signal("QVariant", name="parameter_values_updated")
    parameter_definition_tags_set = Signal("QVariant", name="parameter_definition_tags_set")

    def __init__(self, *db_maps):
        """Init class."""
        super().__init__()
        self._db_maps = db_maps
        self._cache = {}
        self.icon_mngr = IconManager()
        self.connect_signals()

    @property
    def db_maps(self):
        return self._db_maps

    def connect_signals(self):
        """Connect signals."""
        # On cascade remove
        self.object_classes_removed.connect(self.cascade_remove_relationship_classes)
        self.objects_removed.connect(self.cascade_remove_relationships)
        # On cascade update
        self.object_classes_updated.connect(self.cascade_refresh_relationship_classes)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.object_classes_updated.connect(self.cascade_refresh_parameter_values_entity_class)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_definitions)
        self.relationship_classes_updated.connect(self.cascade_refresh_parameter_values_entity_class)
        self.objects_updated.connect(self.cascade_refresh_relationships)
        self.objects_updated.connect(self.cascade_refresh_parameter_values_entity)
        # Auto update
        self.parameter_definitions_updated.connect(self.auto_refresh_parameter_definitions)
        self.parameter_values_updated.connect(self.auto_refresh_parameter_values)
        # Cache
        self.object_classes_added.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_added.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_added.connect(lambda db_map_data: self.cache_items("relationship class", db_map_data))
        self.relationships_added.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        # Discard
        self.object_classes_removed.connect(lambda db_map_data: self.uncache_items("object class", db_map_data))
        self.objects_removed.connect(lambda db_map_data: self.uncache_items("object", db_map_data))
        self.relationship_classes_removed.connect(
            lambda db_map_data: self.uncache_items("relationship class", db_map_data)
        )
        self.relationships_removed.connect(lambda db_map_data: self.uncache_items("relationship", db_map_data))
        # Update cache
        self.object_classes_updated.connect(lambda db_map_data: self.cache_items("object class", db_map_data))
        self.objects_updated.connect(lambda db_map_data: self.cache_items("object", db_map_data))
        self.relationship_classes_updated.connect(
            lambda db_map_data: self.cache_items("relationship class", db_map_data)
        )
        self.relationships_updated.connect(lambda db_map_data: self.cache_items("relationship", db_map_data))
        self.parameter_definition_tags_set.connect(self.cache_parameter_definition_tags)  # TODO: this...
        # Icons
        self.object_classes_added.connect(self.update_icons)
        self.object_classes_updated.connect(self.update_icons)

    def cache_items(self, item_type, db_map_data):
        """Put items in cache.
        It works for both insert and update operations.

        Args:
            item_type (str)
            db_map_data (dict): maps DiffDatabaseMapping instances to lists of items to track
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._cache.setdefault(db_map, {}).setdefault(item_type, {}).setdefault(item["id"], {}).update(item)

    def uncache_items(self, item_type, db_map_data):
        """Remove items from cache.

        Args:
            item_type (str)
            db_map_data (dict): maps DiffDatabaseMapping instances to lists of items to untrack
        """
        for db_map, items in db_map_data.items():
            for item in items:
                self._cache.setdefault(db_map, {}).setdefault(item_type, {}).pop(item["id"])

    def update_icons(self, db_map_data):
        object_classes = [item for db_map, data in db_map_data.items() for item in data]
        self.icon_mngr.setup_object_pixmaps(object_classes)

    def get_item(self, db_map, item_type, id_):
        """Get item from internal dictionaries.

        Args:
            db_map (DiffDatabaseMapping)
            item_type (str)
            id_ (int)
        """
        item = self._cache.get(db_map, {}).get(item_type, {}).get(id_, {})
        if item:
            return item
        return self._get_item_from_db(db_map, item_type, id_)

    def _get_item_from_db(self, db_map, item_type, id_):
        """Get item from database. Called by get_item when it doesn't find the requested item in the cache.
        """
        method_name_dict = {
            "object class": "get_object_classes",
            "object": "get_objects",
            "relationship class": "get_relationship_classes",
            "relationship ": "get_relationship",
            "parameter definition": "get_parameter_definitions",
            "parameter value": "get_parameter_values",
            "parameter value list": "get_parameter_value_lists",
        }
        # TODO: parameter definition and values, use two methods??
        method_name = method_name_dict.get(item_type)
        if not method_name:
            return {}
        _ = getattr(self, method_name)(db_map)
        return self._cache.get(db_map, {}).get(item_type, {}).get(id_, {})

    def get_items(self, db_map, item_type):
        return self._cache.get(db_map, {}).get(item_type, {}).values()

    def get_item_by_field(self, db_map, item_type, field, value):
        return next(iter(x for x in self.get_items(db_map, item_type) if x[field] == value), None)

    def get_object_classes(self, db_map):
        """Get object classes from database.

        Args:
            db_map (DiffDatabaseMapping)
        """
        qry = db_map.query(db_map.object_class_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("object class", {db_map: items})
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
        self.cache_items("object", {db_map: items})
        return items

    def get_relationship_classes(self, db_map, ids=None, object_class_id=None):
        """Get relationship classes from database.

        Args:
            db_map (DiffDatabaseMapping)
            object_class_id (int)
        """
        if ids is None:
            ids = set()
        if object_class_id:
            ids |= {x.id for x in db_map.query(db_map.relationship_class_sq).filter_by(object_class_id=object_class_id)}
        qry = db_map.query(db_map.wide_relationship_class_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_class_sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("relationship class", {db_map: items})
        return items

    def get_relationships(self, db_map, ids=None, class_id=None, object_id=None):
        """Get relationships from database.

        Args:
            db_map (DiffDatabaseMapping)
            class_id (int)
            object_id (int)
        """
        if ids is None:
            ids = set()
        if object_id:
            ids |= {x.id for x in db_map.query(db_map.relationship_sq).filter_by(object_id=object_id)}
        qry = db_map.query(db_map.wide_relationship_sq)
        if ids:
            qry = qry.filter(db_map.wide_relationship_sq.c.id.in_(ids))
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        items = [x._asdict() for x in qry]
        self.cache_items("relationship", {db_map: items})
        return items

    def add_or_update_items(self, db_map_data, method_name, signal_name):
        """Adds or update items.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items to add or update
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
        self.add_or_update_items(db_map_data, "add_object_classes", "object_classes_added")

    def add_objects(self, db_map_data):
        self.add_or_update_items(db_map_data, "add_objects", "objects_added")

    def add_relationship_classes(self, db_map_data):
        self.add_or_update_items(db_map_data, "add_wide_relationship_classes", "relationship_classes_added")

    def add_relationships(self, db_map_data):
        self.add_or_update_items(db_map_data, "add_wide_relationships", "relationships_added")

    def update_object_classes(self, db_map_data):
        self.add_or_update_items(db_map_data, "update_object_classes", "object_classes_updated")

    def update_objects(self, db_map_data):
        self.add_or_update_items(db_map_data, "update_objects", "objects_updated")

    def update_relationship_classes(self, db_map_data):
        self.add_or_update_items(db_map_data, "update_wide_relationship_classes", "relationship_classes_updated")

    def update_relationships(self, db_map_data):
        self.add_or_update_items(db_map_data, "update_wide_relationships", "relationships_updated")

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

    @Slot("QVariant", name="cascade_refresh_relationship_classes")
    def cascade_refresh_relationship_classes(self, db_map_data):
        """Runs when updating object classes. Cascade refresh cached relationship classes."""
        db_map_cascading_data = self.find_cascading_relationship_classes(db_map_data)
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_relationship_classes(db_map, ids=ids)

    @Slot("QVariant", name="cascade_refresh_relationships")
    def cascade_refresh_relationships(self, db_map_data):
        """Runs when updating objects. Cascade refresh cached relationships."""
        db_map_cascading_data = self.find_cascading_relationships(db_map_data)
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_relationships(db_map, ids=ids)

    @Slot("QVariant", name="cascade_remove_relationship_classes")
    def cascade_remove_relationship_classes(self, db_map_data):
        """Runs when removing object classes. Removes relationship classes in cascade."""
        db_map_cascading_data = self.find_cascading_relationship_classes(db_map_data)
        self.relationship_classes_removed.emit(db_map_cascading_data)

    @Slot("QVariant", name="cascade_remove_relationships")
    def cascade_remove_relationships(self, db_map_data):
        """Runs when removing objects. Removes relationships in cascade."""
        db_map_cascading_data = self.find_cascading_relationships(db_map_data)
        self.relationships_removed.emit(db_map_cascading_data)

    def find_cascading_relationship_classes(self, db_map_data):
        """Returns cascading relationship classes given new data for object classes."""
        db_map_cascading_data = dict()
        for db_map, data in db_map_data.items():
            object_class_ids = {str(x["id"]) for x in data}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship class")
                if object_class_ids.intersection(item["object_class_id_list"].split(","))
            ]
        return db_map_cascading_data

    def find_cascading_relationships(self, db_map_data):
        """Returns cascading relationships given new data for objects."""
        db_map_cascading_data = dict()
        for db_map, data in db_map_data.items():
            object_ids = {str(x["id"]) for x in data}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "relationship")
                if object_ids.intersection(item["object_id_list"].split(","))
            ]
        return db_map_cascading_data

    def get_object_parameter_definitions(self, db_map, ids=None, object_class_id=None):
        """Get object parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            object_class_id (int)
        """
        sq = db_map.object_parameter_definition_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter definition", {db_map: items})
        return items

    def get_relationship_parameter_definitions(self, db_map, ids=None, relationship_class_id=None):
        """Get relationship parameter definitions from database.

        Args:
            db_map (DiffDatabaseMapping)
            relationship_class_id (int)
        """
        sq = db_map.relationship_parameter_definition_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter definition", {db_map: items})
        return items

    def get_object_parameter_values(self, db_map, ids=None, object_class_id=None):
        """Get object parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            object_class_id (int)
        """
        sq = db_map.object_parameter_value_sq
        qry = db_map.query(sq)
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value", {db_map: items})
        return items

    def get_relationship_parameter_values(self, db_map, ids=None, relationship_class_id=None):
        """Get relationship parameter values from database.

        Args:
            db_map (DiffDatabaseMapping)
            relationship_class_id (int)
        """
        sq = db_map.relationship_parameter_value_sq
        qry = db_map.query(sq)
        if relationship_class_id:
            qry = qry.filter_by(relationship_class_id=relationship_class_id)
        if ids:
            qry = qry.filter(sq.c.id.in_(ids))
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value", {db_map: items})
        return items

    def get_parameter_definitions(self, db_map, ids=None, entity_class_id=None):
        return self.get_object_parameter_definitions(
            db_map, ids=ids, object_class_id=entity_class_id
        ) + self.get_relationship_parameter_definitions(db_map, ids=ids, relationship_class_id=entity_class_id)

    def get_parameter_values(self, db_map, ids=None, entity_class_id=None):
        return self.get_object_parameter_values(
            db_map, ids=ids, object_class_id=entity_class_id
        ) + self.get_relationship_parameter_values(db_map, ids=ids, relationship_class_id=entity_class_id)

    def get_parameter_value_lists(self, db_map):
        """Get parameter value lists from database.

        Args:
            db_map (DiffDatabaseMapping)
        """
        qry = db_map.query(db_map.wide_parameter_value_list_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("parameter value list", {db_map: items})
        return items

    def get_parameter_tags(self, db_map):
        """Get parameter tags from database.

        Args:
            db_map (DiffDatabaseMapping)
        """
        qry = db_map.query(db_map.parameter_tag_sq)
        items = [x._asdict() for x in qry]
        self.cache_items("parameter tag", {db_map: items})
        return items

    def update_parameter_definitions(self, db_map_data):
        """Update parameter definitions. Take db_map_data that comes in the 'extended' form,
        convert it to the 'regular' form, and insert it into the db.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to parameter definition items
        """
        db_map_tag_data = dict()  # This goes in another table
        for db_map, items in db_map_data.items():
            for item in items:
                name = item.pop("parameter_name", None)
                if name:
                    item["name"] = name
                value_list_name = item.pop("value_list_name", None)
                if value_list_name:
                    value_list = self.get_item_by_field(db_map, "parameter value list", "name", value_list_name)
                    if value_list:
                        item["parameter_value_list_id"] = value_list["id"]
                parameter_tag_list = item.pop("parameter_tag_list", None)
                if parameter_tag_list:
                    try:
                        parameter_tag_list = parameter_tag_list.split(",")
                    except AttributeError:
                        # Can't split
                        continue
                    parameter_tag_id_list = [
                        self.get_item_by_field(db_map, "parameter tag", "tag", tag) for tag in parameter_tag_list
                    ]
                    if None not in parameter_tag_id_list:
                        tag_item = {
                            "parameter_definition_id": item["id"],
                            "parameter_tag_id_list": ",".join([str(x["id"]) for x in parameter_tag_id_list]),
                        }
                        db_map_tag_data.setdefault(db_map, []).append(tag_item)
        self.add_or_update_items(db_map_tag_data, "set_parameter_definition_tags", "parameter_definition_tags_set")
        self.add_or_update_items(db_map_data, "update_parameter_definitions", "parameter_definitions_updated")

    def update_parameter_values(self, db_map_data):
        """Update parameter values. Take db_map_data that comes in the 'extended' form,
        convert it to the 'regular' form, and insert it into the db.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to parameter value items
        """
        self.add_or_update_items(db_map_data, "update_parameter_values", "parameter_values_updated")

    @Slot("QVariant", name="refresh_parameter_definitions")
    def auto_refresh_parameter_definitions(self, db_map_data):
        """Runs when updating parameter definitions. Refreshes parameter definitions
        which are cached in the 'extended' form (i.e. including information about the entity, tags, value lists)

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to parameter definition items
        """
        for db_map, items in db_map_data.items():
            self.get_parameter_definitions(db_map, ids={x["id"] for x in items})

    @Slot("QVariant", name="auto_refresh_parameter_values")
    def auto_refresh_parameter_values(self, db_map_data):
        """Runs when updating parameter values. Refreshes parameter values
        which are cached in the 'extended' form (i.e. including information about the entity, etc.)

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to parameter definition items
        """
        for db_map, items in db_map_data.items():
            self.get_parameter_values(db_map, ids={x["id"] for x in items})

    @Slot("QVariant", name="cascade_refresh_parameter_definitions")
    def cascade_refresh_parameter_definitions(self, db_map_data):
        """Runs when updating entity classes. Cascade refresh cached parameter definitions."""
        db_map_cascading_data = self.find_cascading_parameter_data(db_map_data, "parameter definition")
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_definitions(db_map, ids=ids)

    @Slot("QVariant", name="cascade_refresh_parameter_values_entity_class")
    def cascade_refresh_parameter_values_entity_class(self, db_map_data):
        """Runs when updating entity classes. Cascade refresh cached parameter values."""
        db_map_cascading_data = self.find_cascading_parameter_data(db_map_data, "parameter value")
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_values(db_map, ids=ids)

    def find_cascading_parameter_data(self, db_map_data, item_type):
        """Returns data for cascading parameter definitions or values given data for entity classes."""
        db_map_cascading_data = dict()
        for db_map, data in db_map_data.items():
            entity_class_ids = {str(x["id"]) for x in data}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, item_type)
                if entity_class_ids.intersection(
                    [
                        str(item.get("object_class_id")),
                        str(item.get("relationship_class_id")),
                        *item.get("object_class_id_list", "").split(","),
                    ]
                )
            ]
        return db_map_cascading_data

    @Slot("QVariant", name="cascade_refresh_parameter_values_entity")
    def cascade_refresh_parameter_values_entity(self, db_map_data):
        """Runs when updating entities. Cascade refresh cached parameter values."""
        db_map_cascading_data = self.find_cascading_parameter_values(db_map_data)
        for db_map, data in db_map_cascading_data.items():
            ids = {x["id"] for x in data}
            self.get_parameter_values(db_map, ids=ids)

    def find_cascading_parameter_values(self, db_map_data):
        """Returns data for cascading parameter values given data for entities."""
        db_map_cascading_data = dict()
        for db_map, data in db_map_data.items():
            entity_ids = {str(x["id"]) for x in data}
            db_map_cascading_data[db_map] = [
                item
                for item in self.get_items(db_map, "parameter value")
                if entity_ids.intersection(
                    [
                        str(item.get("object_id")),
                        str(item.get("relationship_id")),
                        *item.get("object_id_list", "").split(","),
                    ]
                )
            ]
        return db_map_cascading_data

    # TODO: this one feels out of place?
    @Slot("QVariant", name="cache_parameter_definition_tags")
    def cache_parameter_definition_tags(self, db_map_data):
        """Cache parameter definition tags.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to parameter definition tag items
        """
        for db_map, items in db_map_data.items():
            for item in items:
                item["id"] = item.pop("parameter_definition_id")
        self.cache_items("parameter definition", db_map_data)
