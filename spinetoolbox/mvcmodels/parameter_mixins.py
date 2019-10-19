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
from PySide2.QtCore import Qt


class ObjectParameterDecorateMixin:
    """Provides decoration features to all object parameter models."""

    def __init__(self, parent, header, db_maps, icon_mngr, *args, **kwargs):
        super().__init__(parent, header, db_maps, *args, **kwargs)
        self.icon_mngr = icon_mngr

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Paint the object class icon next to the name.
        """
        if role == Qt.DecorationRole and self.header[index.column()] == "object_class_name":
            object_class_name = self._main_data[index.row()].object_class_name
            return self.icon_mngr.object_icon(object_class_name)
        return super().data(index, role)


class RelationshipParameterDecorateMixin:
    """Provides decoration features to all relationship parameter models."""

    def __init__(self, parent, header, db_maps, icon_mngr, *args, **kwargs):
        super().__init__(parent, header, db_maps, *args, **kwargs)
        self.icon_mngr = icon_mngr

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Paint the relationship class icon next to the name.
        """
        if role == Qt.DecorationRole and self.header[index.column()] == "relationship_class_name":
            object_class_name_list = self._main_data[index.row()].object_class_name_list
            return self.icon_mngr.relationship_icon(object_class_name_list)
        return super().data(index, role)


class ParameterDefinitionFillInMixin:
    """Provides methods to fill in ids for parameter definition items
    edited by the user, so they can be entered in the database.
    ."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_value_list_lookup = dict()
        self._db_map_tag_lookup = dict()

    def begin_modify_db(self, db_map_data):
        """Begins an operation to add or update database items.
        Populate the lookup dicts with necessary data needed by the _fill_in methods to work.
        """
        # Group data by name
        db_map_value_list_names = dict()
        db_map_parameter_tags = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                value_list_name = item.get("value_list_name")
                db_map_value_list_names.setdefault(db_map, set()).add(value_list_name)
                parameter_tag_list = item.get("parameter_tag_list")
                parameter_tag_list = self._parse_parameter_tag_list(parameter_tag_list)
                if parameter_tag_list:
                    db_map_parameter_tags.setdefault(db_map, set()).update(parameter_tag_list)
        # Build lookup dicts
        self._db_map_value_list_lookup.clear()
        for db_map, names in db_map_value_list_names.items():
            for name in names:
                item = self.db_mngr.get_item_by_field(db_map, "parameter value list", "name", name)
                if item:
                    self._db_map_value_list_lookup.setdefault(db_map, {})[name] = item
        self._db_map_tag_lookup.clear()
        for db_map, tags in db_map_parameter_tags.items():
            for tag in tags:
                item = self.db_mngr.get_item_by_field(db_map, "parameter tag", "tag", tag)
                if item:
                    self._db_map_tag_lookup.setdefault(db_map, {})[name] = item

    @staticmethod
    def _parse_parameter_tag_list(parameter_tag_list):
        try:
            return parameter_tag_list.split(",")
        except AttributeError:
            return None

    @staticmethod
    def _fill_in_parameter_name(item):
        name = item.pop("parameter_name", None)
        if name:
            item["name"] = name

    def _fill_in_parameter_tag_id_list(self, item, db_map):
        value_list_name = item.pop("value_list_name", None)
        value_list = self._db_map_value_list_lookup.get(db_map, {}).get(value_list_name)
        if not value_list:
            return
        item["parameter_value_list_id"] = value_list["id"]

    def _make_param_tag_item(self, item, db_map):
        """Returns a parameter definition tag item that for setting in the database."""
        parameter_tag_list = item.pop("parameter_tag_list", None)
        parameter_tag_list = self._parse_parameter_tag_list(parameter_tag_list)
        if not parameter_tag_list:
            return None
        parameter_tag_id_list = []
        for tag in parameter_tag_list:
            tag_item = self._db_map_value_list_lookup.get(db_map, {}).get(tag)
            if not tag_item:
                return None
            parameter_tag_id_list.append(str(tag_item["id"]))
        return {"parameter_definition_id": item["id"], "parameter_tag_id_list": ",".join(parameter_tag_id_list)}

    def end_modify_db(self):
        """Ends an operation to add or update database items."""
        self._db_map_value_list_lookup.clear()
        self._db_map_tag_lookup.clear()
