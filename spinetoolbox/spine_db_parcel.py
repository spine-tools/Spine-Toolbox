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
        """Pushes relationship class ids with the necessary object class ids."""
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
        """Pushes object ids with the necessary object class ids."""
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

    def _push_parameter_definition_ids(self, db_map_ids, entity_type):
        """Pushes parameter definition ids, assuming all necessary classes are already pushed."""
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

    def _push_parameter_value_list_ids(self, db_map_ids):
        """Pushes parameter value list ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("parameter_value_list_ids", set()).update(ids)

    def _push_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter value ids with the necessary parameter definition ids,
        assuming all necessary entities and classes are already pushed."""
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

    def push_object_class_ids(self, db_map_ids):
        """Pushes object class ids together with the associated parameter definitions."""
        self._push_object_class_ids(db_map_ids)
        self._push_parameter_definition_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter definition")),
            "object",
        )

    def push_relationship_class_ids(self, db_map_ids):
        """Pushes relationship class ids with the necessary object class ids,
        together with the associated relationship parameter definitions."""
        self._push_relationship_class_ids(db_map_ids)
        self._push_parameter_definition_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter definition")),
            "relationship",
        )

    def push_object_ids(self, db_map_ids):
        """Pushes object ids, cascading relationship ids, and the associated parameter values,
        together with all the necessary entity classes and parameter definitions."""
        self._push_object_ids(db_map_ids)
        self.push_relationship_ids(self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_relationships(db_map_ids)))
        self._push_parameter_value_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "object"
        )

    def push_relationship_ids(self, db_map_ids):
        """Pushes relationship ids and the associated parameter values,
        together with all the necessary objects, entity classes and parameter definitions."""
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
        self._push_relationship_class_ids(
            {
                db_map: {
                    rel["class_id"]
                    for rel in (self.db_mngr.get_item(db_map, "relationship", id_) for id_ in ids)
                    if rel
                }
                for db_map, ids in db_map_ids.items()
            }
        )
        self._push_parameter_value_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)),
            "relationship",
        )

    def push_inside_object_ids(self, db_map_ids):
        """Pushes object ids, cascading relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions.
        Mainly intended for the *Duplicate object* action.
        """
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("object_ids", set()).update(ids)
        self._push_inside_relationship_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_relationships(db_map_ids))
        )
        self._push_inside_parameter_value_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)), "object"
        )

    def _push_inside_relationship_ids(self, db_map_ids):
        """Pushes relationship ids, and the associated parameter values,
        but not any entity classes or parameter definitions."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault("relationship_ids", set()).update(ids)
        self._push_inside_parameter_value_ids(
            self.db_mngr.ids_per_db_map(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids)),
            "relationship",
        )

    def _push_inside_parameter_value_ids(self, db_map_ids, entity_type):
        """Pushes parameter value ids."""
        for db_map, ids in db_map_ids.items():
            self._data.setdefault(db_map, {}).setdefault(entity_type + "_parameter_value_ids", set()).update(ids)
