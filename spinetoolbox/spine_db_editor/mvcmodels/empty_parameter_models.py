######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Empty models for parameter definitions and values.
"""
from PySide6.QtCore import Qt
from ...mvcmodels.empty_row_model import EmptyRowModel
from .parameter_mixins import (
    FillInParameterNameMixin,
    MakeRelationshipOnTheFlyMixin,
    InferEntityClassIdMixin,
    FillInAlternativeIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    FillInValueListIdMixin,
)
from ...mvcmodels.shared import PARSED_ROLE, DB_MAP_ROLE
from ...helpers import rows_to_row_count_tuples, DB_ITEM_SEPARATOR


class EmptyParameterModel(EmptyRowModel):
    """An empty parameter model."""

    def __init__(self, parent, header, db_mngr):
        """Initialize class.

        Args:
            parent (Object): the parent object, typically a CompoundParameterModel
            header (list): list of field names for the header
            db_mngr (SpineDBManager)
        """
        super().__init__(parent, header)
        self.db_mngr = db_mngr
        self.db_map = None
        self.entity_class_id = None

    @property
    def item_type(self):
        """The item type, either 'parameter_value' or 'parameter_definition', required by the value_field property."""
        raise NotImplementedError()

    @property
    def entity_class_type(self):
        """Either 'object_class' or 'relationship_class'."""
        raise NotImplementedError()

    @property
    def entity_class_id_key(self):
        return {"object_class": "object_class_id", "relationship_class": "relationship_class_id"}[
            self.entity_class_type
        ]

    @property
    def entity_class_name_key(self):
        return {"object_class": "object_class_name", "relationship_class": "relationship_class_name"}[
            self.entity_class_type
        ]

    @property
    def can_be_filtered(self):
        return False

    @property
    def value_field(self):
        return {"parameter_definition": "default_value", "parameter_value": "value"}[self.item_type]

    def accepted_rows(self):
        return range(self.rowCount())

    def db_item(self, _index):  # pylint: disable=no-self-use
        return None

    def item_id(self, _row):  # pylint: disable=no-self-use
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == DB_MAP_ROLE:
            database = self.data(index, Qt.ItemDataRole.DisplayRole)
            return next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
        if self.header[index.column()] == self.value_field and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.TextAlignmentRole,
            PARSED_ROLE,
        ):
            data = super().data(index, role=Qt.ItemDataRole.EditRole)
            return self.db_mngr.get_value_from_data(data, role)
        return super().data(index, role)

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by handle_items_added."""
        return (item.get(self.entity_class_name_key), item.get("parameter_name"))

    def handle_items_added(self, db_map_data):
        """Runs when parameter definitions or values are added.
        Finds and removes model items that were successfully added to the db."""
        added_ids = set()
        for db_map, items in db_map_data.items():
            for item in items:
                database = db_map.codename
                unique_id = (database, *self._make_unique_id(item))
                added_ids.add(unique_id)
        removed_rows = []
        for row in range(self.rowCount()):
            item = self._make_item(row)
            database = item.get("database")
            unique_id = (database, *self._make_unique_id(item))
            if unique_id in added_ids:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.removeRows(row, count)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch. If successful, add items to db."""
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row() for ind in indexes}
        db_map_data = self._make_db_map_data(rows)
        self.add_items_to_db(db_map_data)
        return True

    def add_items_to_db(self, db_map_data):
        """Add items to db.

        Args:
            db_map_data (dict): mapping DiffDatabaseMapping instance to list of items
        """
        raise NotImplementedError()

    def _make_item(self, row):
        return dict(zip(self.header, self._main_data[row]), row=row)

    def _make_db_map_data(self, rows):
        """
        Returns model data grouped by database map.

        Args:
            rows (set): group data from these rows

        Returns:
            dict: mapping DiffDatabaseMapping instance to list of items
        """
        items = [self._make_item(row) for row in rows]
        db_map_data = dict()
        for item in items:
            database = item.pop("database")
            db_map = next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
            if not db_map:
                continue
            item = {k: v for k, v in item.items() if v is not None}
            db_map_data.setdefault(db_map, []).append(item)
        return db_map_data


class EmptyParameterDefinitionModel(
    FillInValueListIdMixin, FillInEntityClassIdMixin, FillInParameterNameMixin, EmptyParameterModel
):
    """An empty parameter_definition model."""

    @property
    def item_type(self):
        return "parameter_definition"

    @property
    def entity_class_type(self):
        """See base class."""
        raise NotImplementedError()

    def add_items_to_db(self, db_map_data):
        """See base class."""
        self.build_lookup_dictionary(db_map_data)
        db_map_param_def = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item, errors = self._convert_to_db(item, db_map)
                if self._check_item(def_item):
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and "name" in item


class EmptyObjectParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty object parameter_definition model."""

    @property
    def entity_class_type(self):
        return "object_class"


class EmptyRelationshipParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty relationship parameter_definition model."""

    @property
    def entity_class_type(self):
        return "relationship_class"

    def flags(self, index):
        """Additional hack to make the object_class_name_list column non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] == "object_class_name_list":
            flags &= ~Qt.ItemIsEditable
        return flags


class EmptyParameterValueModel(
    InferEntityClassIdMixin,
    FillInAlternativeIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    EmptyParameterModel,
):
    """An empty parameter_value model."""

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

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by handle_items_added."""
        return (*super()._make_unique_id(item), item.get("alternative_name"))

    def add_items_to_db(self, db_map_data):
        """See base class."""
        self.build_lookup_dictionary(db_map_data)
        db_map_param_val = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                param_val, errors = self._convert_to_db(item, db_map)
                if self._check_item(db_map, param_val):
                    db_map_param_val.setdefault(db_map, []).append(param_val)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if any(db_map_param_val.values()):
            self.db_mngr.add_parameter_values(db_map_param_val)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def _check_item(self, db_map, item):
        """Checks if a db item is ready to be inserted."""
        return (
            self.entity_class_id_key in item
            and self.entity_id_key in item
            and "parameter_definition_id" in item
            and "alternative_id" in item
            and "value" in item
        )


class EmptyObjectParameterValueModel(EmptyParameterValueModel):
    """An empty object parameter_value model."""

    @property
    def entity_class_type(self):
        return "object_class"

    @property
    def entity_type(self):
        return "object"

    def _make_unique_id(self, item):
        return (*super()._make_unique_id(item), item.get("name"))


class EmptyRelationshipParameterValueModel(MakeRelationshipOnTheFlyMixin, EmptyParameterValueModel):
    """An empty relationship parameter_value model."""

    _add_entities_on_the_fly = True

    @property
    def entity_class_type(self):
        return "relationship_class"

    @property
    def entity_type(self):
        return "relationship"

    def _make_unique_id(self, item):
        object_name_list = item.get("object_name_list")
        return (
            *super()._make_unique_id(item),
            DB_ITEM_SEPARATOR.join(object_name_list) if object_name_list is not None else None,
        )

    def _make_item(self, row):
        item = super()._make_item(row)
        if item["object_name_list"]:
            item["object_name_list"] = tuple(item["object_name_list"].split(DB_ITEM_SEPARATOR))
        return item

    def add_items_to_db(self, db_map_data):
        """See base class."""
        # Call the super method to add whatever is ready.
        # This will fill the relationship_class_name as a side effect
        super().add_items_to_db(db_map_data)
        # Now we try to add relationships
        self.build_lookup_dictionaries(db_map_data)
        db_map_relationships = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                relationship, err = self._make_relationship_on_the_fly(item, db_map)
                if relationship:
                    db_map_relationships.setdefault(db_map, []).append(relationship)
                if err:
                    db_map_error_log.setdefault(db_map, []).extend(err)
        if any(db_map_relationships.values()):
            self.db_mngr.add_relationships(db_map_relationships)
            # Something might have become ready after adding the relationship(s), so we do one more pass
            super().add_items_to_db(db_map_data)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
