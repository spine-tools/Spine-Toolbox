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
Miscelaneous mixins for parameter models

:authors: M. Marin (KTH)
:date:   4.10.2019
"""


class ConvertToDBMixin:
    """Base class for all mixins that convert model items (name-based) into database items (id-based)."""

    def build_lookup_dictionary(self, db_map_data):
        """Begins an operation to convert items."""

    def _convert_to_db(self, item, db_map):
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item (dict): the model item
            db_map (DiffDatabaseMapping): the database where the resulting item belongs

        Returns:
            dict: the db item
            list: error log
        """
        return item.copy(), []


class FillInParameterNameMixin(ConvertToDBMixin):
    """Fills in parameter names."""

    def _convert_to_db(self, item, db_map):
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item (dict): the model item
            db_map (DiffDatabaseMapping): the database where the resulting item belongs

        Returns:
            dict: the db item
            list: error log
        """
        item, err = super()._convert_to_db(item, db_map)
        name = item.pop("parameter_name", None)
        if name:
            item["name"] = name
        return item, err


class FillInValueListIdMixin(ConvertToDBMixin):
    """Fills in value list ids."""

    def __init__(self, *args, **kwargs):
        """Initializes lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_value_list_lookup = dict()

    def build_lookup_dictionary(self, db_map_data):
        """Builds a name lookup dictionary for the given data.

        Args:
            db_map_data (dict): lists of model items keyed by DiffDatabaseMapping
        """
        super().build_lookup_dictionary(db_map_data)
        # Group data by name
        db_map_value_list_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                value_list_name = item.get("value_list_name")
                db_map_value_list_names.setdefault(db_map, set()).add(value_list_name)
        # Build lookup dict
        self._db_map_value_list_lookup.clear()
        for db_map, names in db_map_value_list_names.items():
            for name in names:
                item = self.db_mngr.get_item_by_field(db_map, "parameter value list", "name", name)
                if item:
                    self._db_map_value_list_lookup.setdefault(db_map, {})[name] = item

    def _convert_to_db(self, item, db_map):
        """Returns a db item (id-based) from the given model item (name-based).

        Args:
            item (dict): the model item
            db_map (DiffDatabaseMapping): the database where the resulting item belongs

        Returns:
            dict: the db item
            list: error log
        """
        item, err1 = super()._convert_to_db(item, db_map)
        err2 = self._fill_in_value_list_id(item, db_map)
        return item, err1 + err2

    def _fill_in_value_list_id(self, item, db_map):
        """Fills in the value list id in the given db item.

        Args:
            item (dict): the db item
            db_map (DiffDatabaseMapping): the database where the given item belongs

        Returns:
            list: error log
        """
        value_list_name = item.pop("value_list_name", None)
        value_list = self._db_map_value_list_lookup.get(db_map, {}).get(value_list_name)
        if not value_list:
            return [f"Unknow value list name {value_list_name}"] if value_list_name else []
        item["parameter_value_list_id"] = value_list["id"]
        return []


class MakeParameterTagMixin(ConvertToDBMixin):
    """Makes parameter tag items."""

    def __init__(self, *args, **kwargs):
        """Initializes lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_tag_lookup = dict()

    def build_lookup_dictionary(self, db_map_data):
        """Builds a name lookup dictionary for the given data.

        Args:
            db_map_data (dict): lists of model items keyed by DiffDatabaseMapping
        """
        super().build_lookup_dictionary(db_map_data)
        # Group data by name
        db_map_parameter_tags = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                parameter_tag_list = item.get("parameter_tag_list")
                parameter_tag_list = self._parse_parameter_tag_list(parameter_tag_list)
                if parameter_tag_list:
                    db_map_parameter_tags.setdefault(db_map, set()).update(parameter_tag_list)
        # Build lookup dict
        self._db_map_tag_lookup.clear()
        for db_map, tags in db_map_parameter_tags.items():
            for tag in tags:
                item = self.db_mngr.get_item_by_field(db_map, "parameter tag", "tag", tag)
                if item:
                    self._db_map_tag_lookup.setdefault(db_map, {})[tag] = item

    def _make_parameter_definition_tag(self, item, db_map):
        """Returns a db parameter definition tag item (id-based) from the given model parameter definition item (name-based).

        Args:
            item (dict): the model parameter definition item
            db_map (DiffDatabaseMapping): the database where the resulting item belongs

        Returns:
            dict: the db parameter definition tag item
            list: error log
        """
        parameter_tag_list = item.pop("parameter_tag_list", None)
        parsed_parameter_tag_list = self._parse_parameter_tag_list(parameter_tag_list)
        if not parsed_parameter_tag_list:
            return None, [f"Unable to parse {parameter_tag_list}"] if parameter_tag_list else []
        parameter_tag_id_list = []
        for tag in parsed_parameter_tag_list:
            tag_item = self._db_map_tag_lookup.get(db_map, {}).get(tag)
            if not tag_item:
                return None, [f"Unknown tag {tag}"]
            parameter_tag_id_list.append(str(tag_item["id"]))
        return {"parameter_definition_id": item["id"], "parameter_tag_id_list": ",".join(parameter_tag_id_list)}, []

    @staticmethod
    def _parse_parameter_tag_list(parameter_tag_list):
        try:
            return parameter_tag_list.split(",")
        except AttributeError:
            return None
