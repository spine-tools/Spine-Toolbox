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
Empty models for parameter definitions and values.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""
from PySide2.QtCore import Qt
from ..mvcmodels.empty_row_model import EmptyRowModel
from ..mvcmodels.parameter_mixins import (
    FillInParameterNameMixin,
    MakeRelationshipOnTheFlyMixin,
    InferEntityClassIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    FillInValueListIdMixin,
)

from ..helpers import rows_to_row_count_tuples


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

    @property
    def entity_class_type(self):
        """Either 'object class' or 'relationship class'."""
        raise NotImplementedError()

    @property
    def entity_class_id_key(self):
        return {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.entity_class_type
        ]

    @property
    def entity_class_name_key(self):
        return {"object class": "object_class_name", "relationship class": "relationship_class_name"}[
            self.entity_class_type
        ]

    @property
    def can_be_filtered(self):
        return False

    def accepted_rows(self):
        return list(range(self.rowCount()))

    def db_item(self, _index):  # pylint: disable=no-self-use
        return None

    def flags(self, index):
        flags = super().flags(index)
        if self.header[index.column()] == "parameter_tag_list":
            flags &= ~Qt.ItemIsEditable
        return flags

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (item.get(self.entity_class_name_key), item.get("parameter_name"))

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object or relationship parameter definitions or values.
        Must be reimplemented in subclasses according to the entity type and to whether
        it's a definition or value model. Used by receive_parameter_data_added."""
        raise NotImplementedError()

    def receive_parameter_data_added(self, db_map_data):
        """Runs when parameter definitions or values are added.
        Finds and removes model items that were successfully added to the db."""
        added_ids = set()
        for db_map, items in db_map_data.items():
            ids = {x["id"] for x in items}
            for item in self.get_entity_parameter_data(db_map, ids=ids):
                database = db_map.codename
                unique_id = (database, *self._make_unique_id(item))
                added_ids.add(unique_id)
        removed_rows = []
        for row, data in enumerate(self._main_data):
            item = dict(zip(self.header, data))
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
        self.add_items_to_db(rows)
        return True

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        raise NotImplementedError()

    def _make_db_map_data(self, rows):
        """
        Returns model data grouped by database map.

        Args:
            rows (set): group data from these rows
        """
        items = [dict(zip(self.header, self._main_data[row]), row=row) for row in rows]
        db_map_data = dict()
        for item in items:
            database = item.pop("database")
            db_map = next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
            if not db_map:
                continue
            db_map_data.setdefault(db_map, []).append(item)
        return db_map_data


class EmptyParameterDefinitionModel(
    FillInValueListIdMixin, FillInEntityClassIdMixin, FillInParameterNameMixin, EmptyParameterModel
):
    """An empty parameter definition model."""

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        db_map_data = self._make_db_map_data(rows)
        self.build_lookup_dictionary(db_map_data)
        db_map_param_def = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item, err = self._convert_to_db(item, db_map)
                if self._check_item(def_item):
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if err:
                    db_map_error_log.setdefault(db_map, []).extend(err)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if db_map_error_log:
            self.db_mngr.msg_error.emit(db_map_error_log)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and "name" in item


class EmptyObjectParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty object parameter definition model."""

    @property
    def entity_class_type(self):
        return "object class"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_definitions(db_map, ids=ids)


class EmptyRelationshipParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty relationship parameter definition model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_definitions(db_map, ids=ids)

    def flags(self, index):
        """Additional hack to make the object_class_name_list column non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] == "object_class_name_list":
            flags &= ~Qt.ItemIsEditable
        return flags


class EmptyParameterValueModel(
    InferEntityClassIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    EmptyParameterModel,
):
    """An empty parameter value model."""

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
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (*super()._make_unique_id(item), item.get(self.entity_name_key))

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        db_map_data = self._make_db_map_data(rows)
        self.build_lookup_dictionary(db_map_data)
        db_map_param_val = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                param_val, err = self._convert_to_db(item, db_map)
                if self._check_item(param_val):
                    db_map_param_val.setdefault(db_map, []).append(param_val)
                if err:
                    db_map_error_log.setdefault(db_map, []).extend(err)
        if any(db_map_param_val.values()):
            self.db_mngr.add_parameter_values(db_map_param_val)
        if db_map_error_log:
            self.db_mngr.msg_error.emit(db_map_error_log)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and self.entity_id_key in item and "parameter_definition_id" in item


class EmptyObjectParameterValueModel(EmptyParameterValueModel):
    """An empty object parameter value model."""

    @property
    def entity_class_type(self):
        return "object class"

    @property
    def entity_type(self):
        return "object"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_values(db_map, ids=ids)


class EmptyRelationshipParameterValueModel(MakeRelationshipOnTheFlyMixin, EmptyParameterValueModel):
    """An empty relationship parameter value model."""

    _add_entities_on_the_fly = True

    @property
    def entity_class_type(self):
        return "relationship class"

    @property
    def entity_type(self):
        return "relationship"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_values(db_map, ids=ids)

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        super().add_items_to_db(rows)  # This will also complete the relationship class name
        # Now we try to add relationships
        db_map_data = self._make_db_map_data(rows)
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
            super().add_items_to_db(rows)
        if db_map_error_log:
            self.db_mngr.msg_error.emit(db_map_error_log)
