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

"""Miscellaneous mixins for parameter models."""

from spinedb_api.parameter_value import split_value_and_type


class ConvertToDBMixin:
    """Base class for all mixins that convert model items (name-based) into database items (id-based)."""

    # pylint: disable=no-self-use
    def _convert_to_db(self, item):
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item (dict): the model item

        Returns:
            dict: the db item
            list: error log
        """
        item = item.copy()
        for field, real_field in self.field_map.items():
            if field in item:
                item[real_field] = item.pop(field)
        return item.copy(), []


class SplitValueAndTypeMixin(ConvertToDBMixin):
    def _convert_to_db(self, item):
        item, err = super()._convert_to_db(item)
        value_field, type_field = {
            "parameter_value": ("value", "type"),
            "parameter_definition": ("default_value", "default_type"),
        }[self.item_type]
        if value_field in item:
            value, value_type = split_value_and_type(item[value_field])
            item[value_field] = value
            item[type_field] = value_type
        return item, err


class MakeEntityOnTheFlyMixin(ConvertToDBMixin):
    """Makes relationships on the fly."""

    @staticmethod
    def _make_entity_on_the_fly(item, db_map):
        """Returns a database entity item (id-based) from the given model parameter_value item (name-based).

        Args:
            item (dict): the model parameter_value item
            db_map (DiffDatabaseMapping): the database where the resulting item belongs

        Returns:
            dict: the db entity item
            list: error log
        """
        entity_class_name = item.get("entity_class_name")
        entity_class = db_map.get_item("entity_class", name=entity_class_name)
        if not entity_class:
            return None, [f"Unknown entity_class {entity_class_name}"] if entity_class_name else []
        entity_byname = item.get("entity_byname")
        if not entity_byname:
            return None, []
        item = {"entity_class_name": entity_class_name, "entity_byname": entity_byname}
        return None if db_map.get_item("entity", **item) else item, []
