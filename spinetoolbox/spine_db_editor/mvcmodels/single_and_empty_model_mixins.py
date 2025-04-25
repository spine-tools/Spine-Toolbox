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
from typing import Optional
from spinedb_api import DatabaseMapping
from spinedb_api.parameter_value import split_value_and_type


class ConvertToDBMixin:
    """Base class for all mixins that convert model items (name-based) into database items (id-based)."""

    def _convert_to_db(self, item: dict) -> tuple[dict, list[str]]:
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item: the model item

        Returns:
            the db item and error log
        """
        item = item.copy()
        for field, real_field in self.field_map.items():
            if field in item:
                item[real_field] = item.pop(field)
        return item, []


class SplitValueAndTypeMixin(ConvertToDBMixin):
    def _convert_to_db(self, item):
        item, err = super()._convert_to_db(item)
        if self.value_field in item:
            value, value_type = split_value_and_type(item[self.value_field])
            item[self.value_field] = value
            item[self.type_field] = value_type
        return item, err


class MakeEntityOnTheFlyMixin(ConvertToDBMixin):
    """Makes relationships on the fly."""

    @staticmethod
    def _make_entity_on_the_fly(item: dict, db_map: DatabaseMapping) -> tuple[Optional[dict], list[str]]:
        """Returns a database entity item (id-based) from the given model parameter_value item (name-based).

        Args:
            item: the model parameter_value item
            db_map: the database where the resulting item belongs

        Returns:
            the db entity item and error log
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
