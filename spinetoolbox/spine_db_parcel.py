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
SpineDBParcel class.

:authors: M. Marin (KTH)
:date:   10.5.2020
"""


class SpineDBParcel:
    """
    A class to create parcels of data from a Spine db.
    Mainly intended for the *Export selection* action in the Data Store form.

    The strategy is the following:
        - `_push` methods (with a leading underscore) push items with everything they need to live in a standalone db.
            These are private methods.
        - `push` methods (no leading underscore) call the `_push` methods to get away with pushing some specific content.
            These are public methods.
    """

    def __init__(self, db_mngr):
        """Initializes the parcel object.

        Args:
            db_mngr (SpineDBManager)
        """
        super().__init__()
        self.db_mngr = db_mngr
        self._data = dict()

    @property
    def data(self):
        return self._data

    def _push_object_class_ids(self, db_map_ids):
        """Pushes object class ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("object_class_ids", set()).update(ids)

    def _push_relationship_class_ids(self, db_map_ids):
        """Pushes relationship class ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("relationship_class_ids", set()).update(ids)
        self._push_object_class_ids(
            {
                db_map: {
                    int(obj_cls_id)
                    for rel_cls in (self.db_mngr.get_item(db_map, "relationship class", id_) for id_ in ids)
                    if rel_cls
                    for obj_cls_id in rel_cls.get("object_class_id_list", "").split(",")
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def _push_object_ids(self, db_map_ids):
        """Pushes object ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("object_ids", set()).update(ids)
        self._push_object_class_ids(
            {
                db_map: {
                    obj["class_id"] for obj in (self.db_mngr.get_item(db_map, "object", id_) for id_ in ids) if obj
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def _push_relationship_ids(self, db_map_ids):
        """Pushes relationship ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("relationship_ids", set()).update(ids)
        self._push_object_ids(
            {
                db_map: {
                    int(obj_id)
                    for rel in (self.db_mngr.get_item(db_map, "relationship", id_) for id_ in ids)
                    if rel
                    for obj_id in rel.get("object_id_list", "").split(",")
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def _push_parameter_value_list_ids(self, db_map_ids):
        """Pushes parameter value list ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("parameter_value_list_ids", set()).update(ids)

    def _push_parameter_definition_ids(self, db_map_ids, entity_type):
        """Pushes parameter definition ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault(entity_type + "_parameter_ids", set()).update(ids)
        self._push_parameter_value_list_ids(
            {
                db_map: {
                    par_def["value_list_id"]
                    for par_def in (self.db_mngr.get_item(db_map, "parameter definition", id_) for id_ in ids)
                    if par_def
                }
                for db_map, ids in db_map_ids.items()
            }
        )
        if entity_type == "object":
            self._push_object_class_ids(
                {
                    db_map: {
                        par_def["object_class_id"]
                        for par_def in (self.db_mngr.get_item(db_map, "parameter definition", id_) for id_ in ids)
                        if par_def
                    }
                    for db_map, ids in db_map_ids.items()
                }
            )
        elif entity_type == "relationship":
            self._push_relationship_class_ids(
                {
                    db_map: {
                        par_def["relationship_class_id"]
                        for par_def in (self.db_mngr.get_item(db_map, "parameter definition", id_) for id_ in ids)
                        if par_def
                    }
                    for db_map, ids in db_map_ids.items()
                }
            )

    def _push_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter value ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault(entity_type + "_parameter_value_ids", set()).update(ids)
        self._push_parameter_definition_ids(
            {
                db_map: {
                    par_val["parameter_id"]
                    for par_val in (self.db_mngr.get_item(db_map, "parameter value", id_) for id_ in ids)
                    if par_val
                }
                for db_map, ids in db_map_ids.items()
            },
            entity_type,
        )
        if entity_type == "object":
            self._push_object_ids(
                {
                    db_map: {
                        par_val["object_id"]
                        for par_val in (self.db_mngr.get_item(db_map, "parameter value", id_) for id_ in ids)
                        if par_val
                    }
                    for db_map, ids in db_map_ids.items()
                }
            )
        elif entity_type == "relationship":
            self._push_relationship_ids(
                {
                    db_map: {
                        par_val["relationship_id"]
                        for par_val in (self.db_mngr.get_item(db_map, "parameter value", id_) for id_ in ids)
                        if par_val
                    }
                    for db_map, ids in db_map_ids.items()
                }
            )

    def push_object_class_ids(self, db_map_ids):
        """Pushes parameter definitions associated with given object classes.
        This essentially pushes the object classes and their parameter definitions.
        """
        self._push_parameter_definition_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter definition")),
            "object",
        )

    def push_relationship_class_ids(self, db_map_ids):
        """Pushes parameter definitions associated with given relationship classes.
        This essentially pushes the relationships classes, their parameter definitions, and their member object classes.
        """
        self._push_parameter_definition_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter definition")),
            "relationship",
        )

    def push_object_ids(self, db_map_ids):
        """Pushes parameter values associated with objects and with any relationships involving those objects.
        This essentially pushes objects, their relationships, all the parameter values, and all the necessary classes,
        definitions, and lists.
        """
        self.push_relationship_ids(self.db_mngr.db_map_ids(self.db_mngr.find_cascading_relationships(db_map_ids)))
        self._push_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "object"
        )

    def push_relationship_ids(self, db_map_ids):
        """Pushes parameter values associated with relationships.
        This essentially pushes relationships, their parameter values, and all the necessary classes,
        definitions, and lists.
        """
        self._push_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "relationship"
        )

    def push_inside_object_ids(self, db_map_ids):
        """Pushes object ids, cascading relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions.
        Mainly intended for the *Duplicate object* action.
        """
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("object_ids", set()).update(ids)
        self.push_inside_relationship_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_relationships(db_map_ids))
        )
        self.push_inside_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "object"
        )

    def push_inside_relationship_ids(self, db_map_ids):
        """Pushes relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("relationship_ids", set()).update(ids)
        self.push_inside_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "relationship"
        )

    def push_inside_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter value ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault(entity_type + "_parameter_value_ids", set()).update(ids)
