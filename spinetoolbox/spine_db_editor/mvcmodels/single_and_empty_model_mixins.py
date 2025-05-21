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

    def _convert_to_db(self, item: dict) -> dict:
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item: the model item

        Returns:
            the db item and error log
        """
        return {self.field_map.get(key, key): value for key, value in item.items()}


class SplitValueAndTypeMixin(ConvertToDBMixin):
    def _convert_to_db(self, item: dict) -> dict:
        item = super()._convert_to_db(item)
        if self.value_field in item:
            value, value_type = split_value_and_type(item[self.value_field])
            item[self.value_field] = value
            item[self.type_field] = value_type
        return item
