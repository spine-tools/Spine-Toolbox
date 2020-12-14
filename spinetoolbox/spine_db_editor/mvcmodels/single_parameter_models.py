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
Single models for parameter definitions and values (as 'for a single entity').

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QGuiApplication
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ..mvcmodels.parameter_mixins import (
    FillInParameterNameMixin,
    FillInValueListIdMixin,
    MakeParameterTagMixin,
    MakeRelationshipOnTheFlyMixin,
    ValidateValueInListForUpdateMixin,
    FillInAlternativeIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    ImposeEntityClassIdMixin,
)
from ...mvcmodels.shared import PARSED_ROLE


class SingleParameterModel(MinimalTableModel):
    """A parameter model for a single entity_class to go in a CompoundParameterModel.
    Provides methods to associate the model to an entity_class as well as
    to filter entities within the class.
    """

    def __init__(self, header, db_mngr, db_map, entity_class_id, lazy=False):
        """Init class.

        Args:
            header (list): list of field names for the header
        """
        super().__init__(header=header, lazy=lazy)
        self.db_mngr = db_mngr
        self.db_map = db_map
        self.entity_class_id = entity_class_id
        self._auto_filter = dict()  # Maps field to accepted ids for that field
        self._filter_parameter_ids = dict()

    @property
    def item_type(self):
        """The item type, either 'parameter_value' or 'parameter_definition', required by the data method."""
        raise NotImplementedError()

    @property
    def entity_class_type(self):
        """The entity_class type, either 'object_class' or 'relationship_class'."""
        raise NotImplementedError()

    @property
    def entity_class_name_field(self):
        return {"object_class": "object_class_name", "relationship_class": "relationship_class_name",}[
            self.entity_class_type
        ]

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, self.entity_class_type, self.entity_class_id)["name"]

    @property
    def entity_class_id_key(self):
        return {"object_class": "object_class_id", "relationship_class": "relationship_class_id"}[
            self.entity_class_type
        ]

    @property
    def json_fields(self):
        return {"parameter_definition": ["default_value"], "parameter_value": ["value"]}[self.item_type]

    @property
    def fixed_fields(self):
        return {
            "object_class": ["object_class_name", "database"],
            "relationship_class": ["relationship_class_name", "object_class_name_list", "database"],
        }[self.entity_class_type]

    @property
    def group_fields(self):
        return {
            "object_class": {"parameter_definition": ["parameter_tag_list"], "parameter_value": []},
            "relationship_class": {
                "parameter_definition": ["object_class_name_list", "parameter_tag_list"],
                "parameter_value": ["object_name_list"],
            },
        }[self.entity_class_type][self.item_type]

    @property
    def parameter_definition_id_key(self):
        return {"parameter_definition": "id", "parameter_value": "parameter_id"}[self.item_type]

    @property
    def can_be_filtered(self):
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """This model doesn't support row insertion."""
        return False

    def item_id(self, row):
        return self._main_data[row]

    def db_item(self, index):
        return self._db_item(index.row())

    def _db_item(self, row):
        id_ = self._main_data[row]
        return self.db_item_from_id(id_)

    def db_item_from_id(self, id_):
        return self.db_mngr.get_item(self.db_map, self.item_type, id_)

    def db_items(self):
        return [self._db_item(row) for row in range(self.rowCount())]

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] in self.fixed_fields:
            return flags & ~Qt.ItemIsEditable
        return flags

    def get_field_item_data(self, field):
        """Returns item data for given field.

        Args:
            field (str): A field from the header

        Returns:
            str, str
        """
        return {
            "object_class_name": ("object_class_id", "object_class"),
            "relationship_class_name": ("relationship_class_id", "relationship_class"),
            "object_class_name_list": ("relationship_class_id", "relationship_class"),
            "object_name": ("object_id", "object"),
            "object_name_list": ("relationship_id", "relationship"),
            "parameter_name": (self.parameter_definition_id_key, "parameter_definition"),
            "value_list_name": ("value_list_id", "parameter_value_list"),
            "description": ("id", "parameter_definition"),
            "value": ("id", "parameter_value"),
            "default_value": ("id", "parameter_definition"),
            "database": ("database", None),
            "alternative_id": ("alternative_id", "alternative"),
        }.get(field)

    def get_id_key(self, field):
        field_item_data = self.get_field_item_data(field)
        if field_item_data is None:
            return None
        return field_item_data[0]

    def get_field_item(self, field, db_item):
        """Returns a db item corresponding to the given field from the table header,
        or an empty dict if the field doesn't contain db items.
        """
        field_item_data = self.get_field_item_data(field)
        if field_item_data is None:
            return {}
        id_key, item_type = field_item_data
        item_id = db_item.get(id_key)
        return self.db_mngr.get_item(self.db_map, item_type, item_id)

    def data(self, index, role=Qt.DisplayRole):
        """Gets the id and database for the row, and reads data from the db manager
        using the item_type property.
        Paint the object_class icon next to the name.
        Also paint background of fixed indexes gray and apply custom format to JSON fields."""
        field = self.header[index.column()]
        # Background role
        if role == Qt.BackgroundRole and field in self.fixed_fields:
            return QGuiApplication.palette().button()
        # Display, edit, tool tip, alignment role of 'json fields'
        if field in self.json_fields and role in (
            Qt.DisplayRole,
            Qt.EditRole,
            Qt.ToolTipRole,
            Qt.TextAlignmentRole,
            PARSED_ROLE,
        ):
            id_ = self._main_data[index.row()]
            return self.db_mngr.get_value(self.db_map, self.item_type, id_, role)
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            if field == "database":
                return self.db_map.codename
            id_ = self._main_data[index.row()]
            item = self.db_mngr.get_item(self.db_map, self.item_type, id_)
            if role == Qt.ToolTipRole:
                description = self.get_field_item(field, item).get("description", None)
                if description not in (None, ""):
                    return description
            data = item.get(field)
            if role == Qt.DisplayRole and data and field in self.group_fields:
                data = data.replace(",", self.db_mngr._GROUP_SEP)
            return data
        # Decoration role

        if role == Qt.DecorationRole and field == self.entity_class_name_field:
            return self.db_mngr.entity_class_icon(self.db_map, self.entity_class_type, self.entity_class_id)
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Sets data directly in database using db mngr. If successful, updated data will be
        automatically seen by the data method.
        """
        if not indexes or not data:
            return False
        row_data = dict()
        for index, value in zip(indexes, data):
            row_data.setdefault(index.row(), {})[self.header[index.column()]] = value
        items = [dict(id=self._main_data[row], **data) for row, data in row_data.items()]
        self.update_items_in_db(items)
        return True

    def update_items_in_db(self, items):
        """Update items in db. Required by batch_set_data"""
        raise NotImplementedError()

    def set_filter_parameter_ids(self, parameter_ids):
        if self._filter_parameter_ids == parameter_ids:
            return False
        self._filter_parameter_ids = parameter_ids
        return True

    def _filter_accepts_row(self, row):
        return self._parameter_filter_accepts_row(row) and self._auto_filter_accepts_row(row)

    def _parameter_filter_accepts_row(self, row):
        """Returns the result of the parameter filter."""
        if not self._filter_parameter_ids:
            return True
        parameter_id = self.db_mngr.get_item(self.db_map, self.item_type, self._main_data[row])[
            self.parameter_definition_id_key
        ]
        return parameter_id in self._filter_parameter_ids.get((self.db_map, self.entity_class_id), set())

    def _auto_filter_accepts_row(self, row):
        """Returns the result of the auto filter."""
        if self._auto_filter is None:
            return False
        item_id = self._main_data[row]
        for accepted_ids in self._auto_filter.values():
            if accepted_ids and item_id not in accepted_ids:
                return False
        return True

    def accepted_rows(self):
        """Returns a list of accepted rows, for convenience."""
        return [row for row in range(self.rowCount()) if self._filter_accepts_row(row)]

    def _get_field_item(self, field, id_):
        """Returns a item from the db_mngr.get_item depending on the field.
        If a field doesn't correspond to a item in the database then an empty dict is returned.
        """
        data = self.db_mngr.get_item(self.db_map, self.item_type, id_)
        header_to_id = {
            "object_class_name": ("entity_class_id", "object_class"),
            "relationship_class_name": ("entity_class_id", "relationship_class"),
            "object_name": ("entity_id", "object"),
            "object_name_list": ("entity_id", "relationship"),
            "parameter_name": (self.parameter_definition_id_key, "parameter_definition"),
        }
        if field not in header_to_id:
            return {}
        id_field, item_type = header_to_id[field]
        item_id = data.get(id_field)
        return self.db_mngr.get_item(self.db_map, item_type, item_id)


class SingleObjectParameterMixin:
    """Associates a parameter model with a single object_class."""

    @property
    def entity_class_type(self):
        return "object_class"


class SingleRelationshipParameterMixin:
    """Associates a parameter model with a single relationship_class."""

    @property
    def entity_class_type(self):
        return "relationship_class"


class SingleParameterDefinitionMixin(FillInParameterNameMixin, FillInValueListIdMixin, MakeParameterTagMixin):
    """A parameter_definition model for a single entity_class."""

    @property
    def item_type(self):
        return "parameter_definition"

    def update_items_in_db(self, items):
        """Update items in db.

        Args:
            item (list): dictionary-items
        """
        self.build_lookup_dictionary({self.db_map: items})
        param_defs = list()
        param_def_tags = list()
        error_log = list()
        for item in items:
            param_def_tag, err2 = self._make_parameter_definition_tag(item, self.db_map)
            param_def, err1 = self._convert_to_db(item, self.db_map)
            if tuple(param_def.keys()) != ("id",):
                param_defs.append(param_def)
            if param_def_tag:
                param_def_tags.append(param_def_tag)
            if err1 or err2:
                error_log += err1 + err2
        if param_def_tags:
            self.db_mngr.set_parameter_definition_tags({self.db_map: param_def_tags})
        if param_defs:
            self.db_mngr.update_parameter_definitions({self.db_map: param_defs})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})


class SingleParameterValueMixin(
    ValidateValueInListForUpdateMixin,
    FillInAlternativeIdMixin,
    ImposeEntityClassIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
):
    """A parameter_value model for a single entity_class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_db_map_class_entity_ids = dict()
        self._filter_alternative_ids = set()
        self._filter_entity_ids = set()

    @property
    def item_type(self):
        return "parameter_value"

    @property
    def entity_type(self):
        """Either 'object' or "relationship'."""
        raise NotImplementedError()

    @property
    def entity_id_key(self):
        return {"object": "object_id", "relationship": "relationship_id"}[self.entity_type]

    @property
    def entity_name_key(self):
        return {"object": "object_name", "relationship": "object_name_list"}[self.entity_type]

    @property
    def entity_name_key_in_cache(self):
        return {"object": "name", "relationship": "object_name_list"}[self.entity_type]

    def set_filter_entity_ids(self, db_map_class_entity_ids):
        if self._filter_db_map_class_entity_ids == db_map_class_entity_ids:
            return False
        self._filter_db_map_class_entity_ids = db_map_class_entity_ids
        self._filter_entity_ids = db_map_class_entity_ids.get((self.db_map, self.entity_class_id), set())
        return True

    def set_filter_alternative_ids(self, db_map_alternative_ids):
        alternative_ids = db_map_alternative_ids.get(self.db_map, set())
        if self._filter_alternative_ids == alternative_ids:
            return False
        self._filter_alternative_ids = alternative_ids
        return True

    def _filter_accepts_row(self, row):
        """Reimplemented to also account for the entity filter."""
        return (
            self._parameter_filter_accepts_row(row)
            and self._entity_filter_accepts_row(row)
            and self._auto_filter_accepts_row(row)
            and self._alternative_filter_accepts_row(row)
        )

    def _entity_filter_accepts_row(self, row):
        """Returns the result of the entity filter."""
        if not self._filter_db_map_class_entity_ids:
            return True
        entity_id_key = {"object_class": "object_id", "relationship_class": "relationship_id"}[self.entity_class_type]
        entity_id = self.db_mngr.get_item(self.db_map, self.item_type, self._main_data[row])[entity_id_key]
        return entity_id in self._filter_entity_ids

    def _alternative_filter_accepts_row(self, row):
        """Returns the result of the alternative filter."""
        if not self._filter_alternative_ids:
            return True
        alt_id = self.db_mngr.get_item(self.db_map, self.item_type, self._main_data[row])["alternative_id"]
        return alt_id in self._filter_alternative_ids

    def update_items_in_db(self, items):
        """Update items in db.

        Args:
            item (list): dictionary-items
        """
        param_vals = list()
        error_log = list()
        db_map_data = dict()
        db_map_data[self.db_map] = items
        self.build_lookup_dictionary(db_map_data)
        for item in items:
            param_val, convert_errors = self._convert_to_db(item, self.db_map)
            param_val, check_errors = self._check_item(param_val)
            if param_val:
                param_vals.append(param_val)
            errors = convert_errors + check_errors
            if errors:
                error_log += errors
        if param_vals:
            self.db_mngr.update_parameter_values({self.db_map: param_vals})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})

    def _check_item(self, item):
        """Checks if a db item is good to be updated."""
        item = item.copy()
        id_ = item.get("id")
        has_valid_value_from_list = item.pop("has_valid_value_from_list", True)
        if not all([id_, has_valid_value_from_list, len(item) > 1]):
            return None, []
        existing_items = {
            (x["entity_class_id"], x["entity_id"], x["parameter_id"], x["alternative_id"]): (
                x.get("object_name") or x.get("object_name_list"),
                x["parameter_name"],
                x["alternative_name"],
            )
            for x in self.db_mngr.get_items(self.db_map, "parameter_value")
            if x["id"] != id_
        }
        existing = self.db_mngr.get_item(self.db_map, "parameter_value", id_).copy()
        entity_class_id = item.get("entity_class_id") or existing["entity_class_id"]
        entity_id = item.get("entity_id") or existing["entity_id"]
        parameter_id = item.get("parameter_definition_id") or existing["parameter_id"]
        alternative_id = item.get("alternative_id") or existing["alternative_id"]
        dupe = existing_items.get((entity_class_id, entity_id, parameter_id, alternative_id))
        if dupe is not None:
            entity_name, parameter_name, alternative_name = dupe
            return None, [f"The '{alternative_name}' value of '{parameter_name}' for '{entity_name}' is already set"]
        return item, []


class SingleObjectParameterDefinitionModel(
    SingleObjectParameterMixin, SingleParameterDefinitionMixin, SingleParameterModel
):
    """An object parameter_definition model for a single object_class."""


class SingleRelationshipParameterDefinitionModel(
    SingleRelationshipParameterMixin, SingleParameterDefinitionMixin, SingleParameterModel
):
    """A relationship parameter_definition model for a single relationship_class."""


class SingleObjectParameterValueModel(SingleObjectParameterMixin, SingleParameterValueMixin, SingleParameterModel):
    """An object parameter_value model for a single object_class."""

    @property
    def entity_type(self):
        return "object"


class SingleRelationshipParameterValueModel(
    SingleRelationshipParameterMixin, MakeRelationshipOnTheFlyMixin, SingleParameterValueMixin, SingleParameterModel
):
    """A relationship parameter_value model for a single relationship_class."""

    @property
    def entity_type(self):
        return "relationship"

    def update_items_in_db(self, items):
        """Update items in db.

        Args:
            item (list): dictionary-items
        """
        for item in items:
            item["relationship_class_name"] = self.entity_class_name
        db_map_data = {self.db_map: items}
        self.build_lookup_dictionaries(db_map_data)
        db_map_relationships = dict()
        db_map_error_log = dict()
        for db_map, data in db_map_data.items():
            for item in data:
                relationship, err = self._make_relationship_on_the_fly(item, db_map)
                if relationship:
                    db_map_relationships.setdefault(db_map, []).append(relationship)
                if err:
                    db_map_error_log.setdefault(db_map, []).extend(err)
        if any(db_map_relationships.values()):
            self.db_mngr.add_relationships(db_map_relationships)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
        super().update_items_in_db(items)
