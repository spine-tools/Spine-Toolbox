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

from typing import Tuple, Dict, Set
from PySide2.QtCore import QObject, Signal
from spinedb_api import DiffDatabaseMapping
from helpers import IconManager


class SpineDBManager(QObject):
    """Class to manage spine DBs in a unified way.
    The idea is to share an object of this class across many mvc models and related classes
    that need to interact with a set of DBs.
    """

    entities_deleted = Signal(DiffDatabaseMapping, set)
    entity_classes_deleted = Signal(DiffDatabaseMapping, set)
    entities_updated = Signal(DiffDatabaseMapping, set)
    entity_classes_updated = Signal(DiffDatabaseMapping, set)
    entities_added = Signal(DiffDatabaseMapping, set)
    entity_classes_added = Signal(DiffDatabaseMapping, set)

    def __init__(self, db_maps: Dict[str, DiffDatabaseMapping]):
        """Init class."""
        super(SpineDBManager, self).__init__()
        self._db_maps = db_maps
        self.fetched = {"entity_class": set(), "entity": set()}
        self.entity = {db_map: dict() for db_map in self._db_maps.values()}
        self.entity_class = {db_map: dict() for db_map in self._db_maps.values()}
        self.entity_class_relation_membership = {db_map: dict() for db_map in self._db_maps.values()}
        self.db_name_to_map = {db_name: db_map for db_name, db_map in self._db_maps.items()}
        self.db_map_to_name = {db_map: db_name for db_name, db_map in self._db_maps.items()}
        self.icon_manager = IconManager()
        for db_map in self._db_maps.values():
            self.icon_manager.setup_object_pixmaps(db_map.object_class_list())

    @staticmethod
    def _obj_to_dict(obj):
        """Returns a dictionary mapping ids to dictionary-items
        in the given collection of objects."""
        d = {}
        for data in obj:
            data = data._asdict()
            data["entity_type"] = "object"
            d[data["id"]] = data
        return d

    @staticmethod
    def _obj_class_to_dict(obj):
        """Returns a dictionary mapping ids to dictionary-items
        in the given collection of objects classes."""
        d = {}
        for data in obj:
            data = data._asdict()
            data["class_type"] = "object"
            d[data["id"]] = data
        return d

    @staticmethod
    def _rel_to_dict(rel):
        """Returns a dictionary mapping ids to dictionary-items
        in the given collection of relationships."""
        d = {}
        for data in rel:
            data = data._asdict()
            data["object_id_list"] = [int(id_str) for id_str in data["object_id_list"].split(",")]
            data["entity_type"] = "relationship"
            d[data["id"]] = data
        return d

    @staticmethod
    def _rel_class_to_dict(rel):
        """Returns a dictionary mapping ids to dictionary-items
        in the given collection of relationship classes."""
        d = {}
        for data in rel:
            data = data._asdict()
            data["class_type"] = "relationship"
            data["object_class_id_list"] = [int(id_str) for id_str in data["object_class_id_list"].split(",")]
            d[data["id"]] = data
        return d

    def update_entities(self, db_map: DiffDatabaseMapping, updated_entities):
        if db_map not in self.db_map_to_name:
            return
        objects = [entity for entity in updated_entities if entity["entity_type"] == "object"]
        for o in objects:
            o.pop("class_id", None)
        relationships = [entity for entity in updated_entities if entity["entity_type"] == "relationship"]
        for r in relationships:
            r.pop("class_id", None)

        updated_objects, _ = db_map.update_objects(*objects, strict=True)
        updated_relationship, _ = db_map.update_wide_relationships(*relationships, strict=True)

        updated_objects = self._obj_to_dict(updated_objects)
        updated_relationship = self._rel_to_dict(updated_relationship)
        self.entity[db_map].update(updated_objects)
        self.entity[db_map].update(updated_relationship)
        updated_ids = set(updated_objects.keys()).union(set(updated_relationship.keys()))
        entity_data = self.entity[db_map]
        for entity_id in self.entity[db_map].keys():
            if entity_id in updated_ids:
                continue
            if entity_data[entity_id]["entity_type"] == "relationship" and any(
                updated_ids.intersection(set(entity_data[entity_id]["object_id_list"]))
            ):
                updated_ids.add(entity_id)
        if updated_ids:
            self.entities_updated.emit(db_map, updated_ids)

    def update_entity_classes(self, db_map: DiffDatabaseMapping, updated_entities):
        if db_map not in self.db_map_to_name:
            return
        objects = [entity for entity in updated_entities if entity["class_type"] == "object"]
        for o in objects:
            o.pop("class_id", None)
        relationships = [entity for entity in updated_entities if entity["class_type"] == "relationship"]
        for r in relationships:
            r.pop("class_id", None)

        updated_objects, _ = db_map.update_object_classes(*objects, strict=True)
        updated_relationship, _ = db_map.update_wide_relationship_classes(*relationships, strict=True)

        updated_objects = self._obj_class_to_dict(updated_objects)
        updated_relationship = self._rel_class_to_dict(updated_relationship)

        self.entity_class[db_map].update(updated_objects)
        self.entity_class[db_map].update(updated_relationship)
        updated_ids = set(updated_objects.keys()).union(set(updated_relationship.keys()))
        entity_data = self.entity_class[db_map]
        for entity_class_id in self.entity_class[db_map].keys():
            if entity_class_id in updated_ids:
                continue
            if entity_data[entity_class_id]["class_type"] == "relationship" and any(
                updated_ids.intersection(set(entity_data[entity_class_id]["object_class_id_list"]))
            ):
                updated_ids.add(entity_class_id)
        if updated_ids:
            self.entity_classes_updated.emit(db_map, updated_ids)

    def add_entities(self, db_map: DiffDatabaseMapping, new_entities):
        objects = [entity for entity in new_entities if entity["entity_type"] == "object"]
        relationships = [entity for entity in new_entities if entity["entity_type"] == "relationship"]
        new_obj, _ = db_map.add_objects(*objects)
        new_rel, _ = db_map.add_wide_relationships(*relationships)
        new_obj = self._obj_to_dict(new_obj)
        new_rel = self._rel_to_dict(new_rel)
        self.entity[db_map].update(new_obj)
        self.entity[db_map].update(new_rel)
        if new_obj or new_rel:
            self.entities_added.emit(db_map, set(new_obj.keys()).union(set(new_rel.keys())))

    def add_entity_classes(self, db_map: DiffDatabaseMapping, new_entities):
        objects = [entity for entity in new_entities if entity["class_type"] == "object"]
        relationships = [entity for entity in new_entities if entity["class_type"] == "relationship"]
        new_obj, _ = db_map.add_object_classes(*objects, strict=True)
        new_rel, _ = db_map.add_wide_relationship_classes(*relationships, strict=True)
        new_obj = self._obj_class_to_dict(new_obj)
        new_rel = self._rel_class_to_dict(new_rel)
        self.entity_class[db_map].update(new_obj)
        self.entity_class[db_map].update(new_rel)
        if new_obj or new_rel:
            self.entity_classes_added.emit(db_map, set(new_obj.keys()).union(set(new_rel.keys())))

    def delete_entities(self, db_map: DiffDatabaseMapping, entity_ids: Set[int]):
        if db_map in self.db_map_to_name:
            entity_dict = self.entity[db_map]
            object_ids = set(entity_id for entity_id in entity_ids if entity_dict[entity_id]["entity_type"] == "object")
            relationship_ids = set(
                entity_id for entity_id in entity_ids if entity_dict[entity_id]["entity_type"] == "relationship"
            )
            db_map.remove_items(object_ids=object_ids, relationship_ids=relationship_ids)
            entity_data = self.entity[db_map]
            for entity_id in self.entity[db_map].keys():
                if entity_id in entity_ids:
                    continue
                if entity_data[entity_id]["entity_type"] == "relationship" and any(
                    entity_ids.intersection(set(entity_data[entity_id]["object_id_list"]))
                ):
                    entity_ids.add(entity_id)
        if entity_ids:
            self.entities_deleted.emit(db_map, entity_ids)
        return entity_ids

    def delete_entity_classes(self, db_map: DiffDatabaseMapping, entity_class_ids: Set[int]):
        if db_map in self.db_map_to_name:
            entity_dict = self.entity_class[db_map]
            object_ids = set(
                class_id for class_id in entity_class_ids if entity_dict[class_id]["class_type"] == "object"
            )
            relationship_ids = set(
                class_id for class_id in entity_class_ids if entity_dict[class_id]["class_type"] == "relationship"
            )
            db_map.remove_items(object_class_ids=object_ids, relationship_class_ids=relationship_ids)
            entity_data = self.entity_class[db_map]
            for class_id in self.entity_class[db_map].keys():
                if class_id in entity_class_ids:
                    continue
                if entity_data[class_id]["class_type"] == "relationship" and any(
                    entity_class_ids.intersection(set(entity_data[class_id]["object_class_id_list"]))
                ):
                    entity_class_ids.add(class_id)
        if entity_class_ids:
            self.entity_classes_deleted.emit(db_map, entity_class_ids)
        return entity_class_ids

    def get_entities(self, entity_type: Tuple[str, ...] = ("object", "relationship"), filters: dict = None):
        if filters is None:
            filters = dict()
        entities = []
        for db_map in self._db_maps.values():
            id_list = filters.get(db_map, {}).get("id_list", None)
            class_id = filters.get(db_map, {}).get("class_id", None)
            if "object" in entity_type:
                obj = self._obj_to_dict(db_map.object_list(id_list=id_list, class_id=class_id))
                self.entity[db_map].update(obj)
                entities.extend([(db_map, data) for data in obj.values()])
            if "relationship" in entity_type:
                object_id = filters.get(db_map, {}).get("object_id", None)
                rels = self._rel_to_dict(
                    db_map.wide_relationship_list(id_list=id_list, class_id=class_id, object_id=object_id)
                )
                self.entity[db_map].update(rels)
                entities.extend([(db_map, data) for data in rels.values()])
        return entities

    def get_entity_classes(self, entity_class_type: Tuple[str, ...] = ("object", "relationship"), filters: dict = None):
        if filters is None:
            filters = dict()
        classes = []
        for db_map in self._db_maps.values():
            id_list = filters.get(db_map, {}).get("id_list", None)
            if "object" in entity_class_type:
                obj = self._obj_class_to_dict(db_map.object_class_list(id_list=id_list))
                self.entity_class[db_map].update(obj)
                classes.extend([(db_map, data) for data in obj.values()])
            if "relationship" in entity_class_type:
                object_class_id = filters.get(db_map, {}).get("object_class_id", None)
                rel = self._rel_class_to_dict(
                    db_map.wide_relationship_class_list(id_list=id_list, object_class_id=object_class_id)
                )
                self.entity_class[db_map].update(rel)
                classes.extend([(db_map, data) for data in rel.values()])
        return classes
