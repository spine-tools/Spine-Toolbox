######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from spinedb_api import Asterisk


class SpineDBParcel:
    """
    A class to create parcels of data from a Spine db.
    Mainly intended for the *Export selection* action in the Spine db editor:

        - ``push`` methods push items with everything they need to live in a standalone db.
        - ``full_push`` and ``inner_push`` methods do something more specific
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

    def _get_fields(self, db_map, item_type, field, ids):
        if ids is Asterisk:
            fields = {x.get(field) for x in self.db_mngr.get_items(db_map, item_type)}
        else:
            fields = {self.db_mngr.get_field(db_map, item_type, id_, field) for id_ in ids}
        fields.discard(None)
        return fields

    def push_object_class_ids(self, db_map_ids):
        """Pushes object_class ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["object_class_ids"].update(ids)

    def push_relationship_class_ids(self, db_map_ids):
        """Pushes relationship_class ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["relationship_class_ids"].update(ids)
        self.push_object_class_ids(
            {
                db_map: {
                    int(obj_cls_id)
                    for obj_cls_id_list in self._get_fields(db_map, "relationship_class", "object_class_id_list", ids)
                    for obj_cls_id in obj_cls_id_list.split(",")
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_object_ids(self, db_map_ids):
        """Pushes object ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["object_ids"].update(ids)
        self.push_object_class_ids(
            {db_map: self._get_fields(db_map, "object", "class_id", ids) for db_map, ids in db_map_ids.items()}
        )

    def push_relationship_ids(self, db_map_ids):
        """Pushes relationship ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["relationship_ids"].update(ids)
        self.push_object_ids(
            {
                db_map: {
                    int(obj_id)
                    for obj_id_list in self._get_fields(db_map, "relationship", "object_id_list", ids)
                    for obj_id in obj_id_list.split(",")
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_parameter_value_list_ids(self, db_map_ids):
        """Pushes parameter_value_list ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["parameter_value_list_ids"].update(ids)

    def push_parameter_definition_ids(self, db_map_ids, entity_type):
        """Pushes parameter_definition ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)[entity_type + "_parameter_ids"].update(ids)
        self.push_parameter_value_list_ids(
            {
                db_map: self._get_fields(db_map, "parameter_definition", "value_list_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        if entity_type == "object":
            self.push_object_class_ids(
                {
                    db_map: self._get_fields(db_map, "parameter_definition", "object_class_id", ids)
                    for db_map, ids in db_map_ids.items()
                }
            )
        elif entity_type == "relationship":
            self.push_relationship_class_ids(
                {
                    db_map: self._get_fields(db_map, "parameter_definition", "relationship_class_id", ids)
                    for db_map, ids in db_map_ids.items()
                }
            )

    def push_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter_value ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)[entity_type + "_parameter_value_ids"].update(ids)
        self.push_parameter_definition_ids(
            {
                db_map: self._get_fields(db_map, "parameter_value", "parameter_id", ids)
                for db_map, ids in db_map_ids.items()
            },
            entity_type,
        )
        self.push_alternative_ids(
            {
                db_map: self._get_fields(db_map, "parameter_value", "alternative_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        if entity_type == "object":
            self.push_object_ids(
                {
                    db_map: self._get_fields(db_map, "parameter_value", "object_id", ids)
                    for db_map, ids in db_map_ids.items()
                }
            )
        elif entity_type == "relationship":
            self.push_relationship_ids(
                {
                    db_map: self._get_fields(db_map, "parameter_value", "relationship_id", ids)
                    for db_map, ids in db_map_ids.items()
                }
            )

    def push_object_group_ids(self, db_map_ids):
        """Pushes object group ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["object_group_ids"].update(ids)
        self.push_object_ids(
            {
                db_map: self._get_fields(db_map, "entity_group", "entity_id", ids)
                | self._get_fields(db_map, "entity_group", "member_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_alternative_ids(self, db_map_ids):
        """Pushes alternative ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["alternative_ids"].update(ids)

    def push_scenario_ids(self, db_map_ids):
        """Pushes scenario ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["scenario_ids"].update(ids)

    def push_scenario_alternative_ids(self, db_map_ids):
        """Pushes scenario_alternative ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["scenario_alternative_ids"].update(ids)
        self.push_alternative_ids(
            {
                db_map: self._get_fields(db_map, "scenario_alternative", "alternative_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        self.push_scenario_ids(
            {
                db_map: self._get_fields(db_map, "scenario_alternative", "scenario_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def full_push_object_class_ids(self, db_map_ids):
        """Pushes parameter definitions associated with given object classes.
        This essentially full_pushes the object classes and their parameter definitions.
        """
        param_def_ids = self.db_mngr.db_map_ids(
            self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter_definition")
        )
        self.push_parameter_definition_ids(param_def_ids, "object")
        db_map_ids = {db_map: ids for db_map, ids in db_map_ids.items() if not param_def_ids[db_map]}
        self.push_object_class_ids(db_map_ids)

    def full_push_relationship_class_ids(self, db_map_ids):
        """Pushes parameter definitions associated with given relationship classes.
        This essentially full_pushes the relationships classes, their parameter definitions, and their member object classes.
        """
        param_def_ids = self.db_mngr.db_map_ids(
            self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter_definition")
        )
        self.push_parameter_definition_ids(param_def_ids, "relationship")
        db_map_ids = {db_map: ids for db_map, ids in db_map_ids.items() if not param_def_ids[db_map]}
        self.push_relationship_class_ids(db_map_ids)

    def full_push_object_ids(self, db_map_ids):
        """Pushes parameter values associated with objects and with any relationships involving those objects.
        This essentially full_pushes objects, their relationships, all the parameter values, and all the necessary classes,
        definitions, and lists.
        """
        self.full_push_relationship_ids(self.db_mngr.db_map_ids(self.db_mngr.find_cascading_relationships(db_map_ids)))
        param_val_ids = self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids))
        self.push_parameter_value_ids(param_val_ids, "object")
        db_map_ids = {db_map: ids for db_map, ids in db_map_ids.items() if not param_val_ids[db_map]}
        self.push_object_ids(db_map_ids)
        self.push_object_group_ids(self.db_mngr.db_map_ids(self.db_mngr.find_groups_by_entity(db_map_ids)))

    def full_push_relationship_ids(self, db_map_ids):
        """Pushes parameter values associated with relationships.
        This essentially full_pushes relationships, their parameter values, and all the necessary classes,
        definitions, and lists.
        """
        param_val_ids = self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids))
        self.push_parameter_value_ids(param_val_ids, "relationship")
        db_map_ids = {db_map: ids for db_map, ids in db_map_ids.items() if not param_val_ids[db_map]}
        self.push_relationship_ids(db_map_ids)

    def inner_push_object_ids(self, db_map_ids):
        """Pushes object ids, cascading relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions.
        Mainly intended for the *Duplicate object* action.
        """
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["object_ids"].update(ids)
        self.inner_push_relationship_ids(self.db_mngr.db_map_ids(self.db_mngr.find_cascading_relationships(db_map_ids)))
        self.inner_push_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "object"
        )

    def inner_push_relationship_ids(self, db_map_ids):
        """Pushes relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["relationship_ids"].update(ids)
        self.inner_push_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "relationship"
        )

    def inner_push_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter_value ids."""
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)[entity_type + "_parameter_value_ids"].update(ids)

    def _setdefault(self, db_map):
        d = {
            "object_class_ids": set(),
            "relationship_class_ids": set(),
            "parameter_value_list_ids": set(),
            "object_ids": set(),
            "relationship_ids": set(),
            "object_group_ids": set(),
            "object_parameter_ids": set(),
            "relationship_parameter_ids": set(),
            "object_parameter_value_ids": set(),
            "relationship_parameter_value_ids": set(),
            "alternative_ids": set(),
            "scenario_ids": set(),
            "scenario_alternative_ids": set(),
        }
        return self._data.setdefault(db_map, d)
