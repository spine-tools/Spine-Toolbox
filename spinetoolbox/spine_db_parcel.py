######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""SpineDBParcel class."""
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
        self._data = {}

    @property
    def data(self):
        return self._data

    def _get_field_values(self, db_map, item_type, field, ids):
        """Returns a list of field values for items of given type, having given ids."""
        if ids is Asterisk:
            fields = {x.get(field) for x in self.db_mngr.get_items(db_map, item_type)}
        else:
            fields = {self.db_mngr.get_field(db_map, item_type, id_, field) for id_ in ids}
        fields.discard(None)
        return fields

    def push_entity_class_ids(self, db_map_ids):
        """Pushes entity_class ids."""
        if not any(db_map_ids.values()):
            return
        self._update_ids(db_map_ids, "entity_class_ids")
        self.push_entity_class_ids(
            {
                db_map: {
                    dimension_id
                    for dimension_id_list in self._get_field_values(db_map, "entity_class", "dimension_id_list", ids)
                    for dimension_id in dimension_id_list
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_entity_ids(self, db_map_ids):
        """Pushes entity ids."""
        if not any(db_map_ids.values()):
            return
        self._update_ids(db_map_ids, "entity_ids")
        self.push_entity_class_ids(
            {db_map: self._get_field_values(db_map, "entity", "class_id", ids) for db_map, ids in db_map_ids.items()}
        )
        self.push_entity_ids(
            {
                db_map: {
                    el_id
                    for el_id_list in self._get_field_values(db_map, "entity", "element_id_list", ids)
                    for el_id in el_id_list
                }
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_parameter_value_list_ids(self, db_map_ids):
        """Pushes parameter_value_list ids."""
        self._update_ids(db_map_ids, "parameter_value_list_ids")

    def push_parameter_definition_ids(self, db_map_ids):
        """Pushes parameter_definition ids."""
        self._update_ids(db_map_ids, "parameter_definition_ids")
        self.push_parameter_value_list_ids(
            {
                db_map: self._get_field_values(db_map, "parameter_definition", "value_list_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        self.push_entity_class_ids(
            {
                db_map: self._get_field_values(db_map, "parameter_definition", "entity_class_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_parameter_value_ids(self, db_map_ids):
        """Pushes parameter_value ids."""
        self._update_ids(db_map_ids, "parameter_value_ids")
        self.push_parameter_definition_ids(
            {
                db_map: self._get_field_values(db_map, "parameter_value", "parameter_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        self.push_alternative_ids(
            {
                db_map: self._get_field_values(db_map, "parameter_value", "alternative_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        self.push_entity_ids(
            {
                db_map: self._get_field_values(db_map, "parameter_value", "entity_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_entity_group_ids(self, db_map_ids):
        """Pushes entity group ids."""
        self._update_ids(db_map_ids, "entity_group_ids")
        self.push_entity_ids(
            {
                db_map: self._get_field_values(db_map, "entity_group", "entity_id", ids)
                | self._get_field_values(db_map, "entity_group", "member_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def push_alternative_ids(self, db_map_ids):
        """Pushes alternative ids."""
        self._update_ids(db_map_ids, "alternative_ids")

    def push_scenario_ids(self, db_map_ids):
        """Pushes scenario ids."""
        self._update_ids(db_map_ids, "scenario_ids")

    def push_scenario_alternative_ids(self, db_map_ids):
        """Pushes scenario_alternative ids."""
        self._update_ids(db_map_ids, "scenario_alternative_ids")
        self.push_alternative_ids(
            {
                db_map: self._get_field_values(db_map, "scenario_alternative", "alternative_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )
        self.push_scenario_ids(
            {
                db_map: self._get_field_values(db_map, "scenario_alternative", "scenario_id", ids)
                for db_map, ids in db_map_ids.items()
            }
        )

    def full_push_entity_class_ids(self, db_map_ids):
        """Pushes parameter definitions associated with given entity classes.
        This essentially full_pushes the entity classes, their parameter definitions, and their member entity classes.
        """
        param_def_ids = self.db_mngr.db_map_ids(
            self.db_mngr.find_cascading_parameter_data(db_map_ids, "parameter_definition")
        )
        self.push_parameter_definition_ids(param_def_ids)
        db_map_ids = {db_map: ids - param_def_ids.get(db_map, set()) for db_map, ids in db_map_ids.items()}
        self.push_entity_class_ids(db_map_ids)

    def full_push_entity_ids(self, db_map_ids):
        """Pushes parameter values associated with entities *and* their elements.
        This essentially full_pushes entities, all the parameter values, and all the necessary classes,
        definitions, and lists.
        """
        if not any(db_map_ids.values()):
            return
        self.full_push_entity_ids(self.db_mngr.db_map_ids(self.db_mngr.find_cascading_entities(db_map_ids)))
        param_val_ids = self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids))
        self.push_parameter_value_ids(param_val_ids)
        db_map_ids = {db_map: ids - param_val_ids.get(db_map, set()) for db_map, ids in db_map_ids.items()}
        self.push_entity_ids(db_map_ids)
        self.push_entity_group_ids(self.db_mngr.db_map_ids(self.db_mngr.find_groups_by_entity(db_map_ids)))

    def full_push_scenario_ids(self, db_map_ids):
        self.push_scenario_ids(db_map_ids)
        scenario_alternative_ids = self.db_mngr.db_map_ids(
            self.db_mngr.find_cascading_scenario_alternatives_by_scenario(db_map_ids)
        )
        self.push_scenario_alternative_ids(scenario_alternative_ids)

    def inner_push_entity_ids(self, db_map_ids):
        """Pushes entity ids, cascading entity ids, and the associated parameter values,
        but not any entity classes or parameter definitions.
        Mainly intended for the *Duplicate entity* action.
        """
        if not any(db_map_ids.values()):
            return
        for db_map, ids in db_map_ids.items():
            self._setdefault(db_map)["entity_ids"].update(ids)
        self.inner_push_entity_ids(self.db_mngr.db_map_ids(self.db_mngr.find_cascading_entities(db_map_ids)))
        self.inner_push_parameter_value_ids(
            self.db_mngr.db_map_ids(self.db_mngr.find_cascading_parameter_values_by_entity(db_map_ids))
        )

    def inner_push_parameter_value_ids(self, db_map_ids):
        """Pushes parameter_value ids."""
        self._update_ids(db_map_ids, "parameter_value_ids")

    def _update_ids(self, db_map_ids, key):
        """Updates ids for given database item.

        Args:
            db_map_ids (dict): mapping from :class:`DatabaseMapping` to ids or ``Asterisk``
            key (str): the key
        """
        for db_map, ids in db_map_ids.items():
            if ids is Asterisk:
                self._setdefault(db_map)[key] = ids
            else:
                current = self._setdefault(db_map)[key]
                if current is not Asterisk:
                    current.update(ids)

    def _setdefault(self, db_map):
        """
        Adds new id sets for given ``db_map`` or returns existing ones.

        Args:
            db_map (DatabaseMapping): a database map

        Returns:
            dict: mapping from item name to set of ids
        """
        d = {
            "entity_class_ids": set(),
            "parameter_value_list_ids": set(),
            "entity_ids": set(),
            "entity_group_ids": set(),
            "parameter_definition_ids": set(),
            "parameter_value_ids": set(),
            "alternative_ids": set(),
            "scenario_ids": set(),
            "scenario_alternative_ids": set(),
        }
        return self._data.setdefault(db_map, d)
