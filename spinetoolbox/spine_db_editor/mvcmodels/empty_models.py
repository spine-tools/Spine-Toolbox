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
from .single_and_empty_model_mixins import (
    SplitValueAndTypeMixin,
    FillInParameterNameMixin,
    MakeEntityOnTheFlyMixin,
    InferEntityClassIdMixin,
    FillInAlternativeIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    FillInValueListIdMixin,
)
from ...mvcmodels.shared import PARSED_ROLE, DB_MAP_ROLE
from ...helpers import rows_to_row_count_tuples, DB_ITEM_SEPARATOR


class EmptyModelBase(EmptyRowModel):
    """Base class for all empty models that go in a CompoundModelBase subclass."""

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
        raise NotImplementedError()

    def add_items_to_db(self, db_map_data):
        """Add items to db.

        Args:
            db_map_data (dict): mapping DiffDatabaseMapping instance to list of items
        """
        raise NotImplementedError()

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by handle_items_added."""
        raise NotImplementedError()

    @property
    def can_be_filtered(self):
        return False

    def accepted_rows(self):
        return range(self.rowCount())

    def db_item(self, _index):  # pylint: disable=no-self-use
        return None

    def item_id(self, _row):  # pylint: disable=no-self-use
        return None

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

    def _autocomplete_row(self, db_map, item):
        entity_class_id = item.get("entity_class_id")
        if entity_class_id:
            entity_class = self.db_mngr.get_item(db_map, "entity_class", entity_class_id, only_visible=False)
            self._main_data[item["row"]][self.header.index("entity_class_name")] = entity_class["name"]

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
        db_map_data = {}
        for item in items:
            database = item.pop("database")
            db_map = next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
            if not db_map:
                continue
            item = {k: v for k, v in item.items() if v is not None}
            db_map_data.setdefault(db_map, []).append(item)
        return db_map_data

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == DB_MAP_ROLE:
            database = self.data(index, Qt.ItemDataRole.DisplayRole)
            return next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
        return super().data(index, role)


class ParameterMixin:
    @property
    def value_field(self):
        return {"parameter_value": "value", "parameter_definition": "default_value"}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if self.header[index.column()] == self.value_field and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.TextAlignmentRole,
            PARSED_ROLE,
        ):
            data = super().data(index, role=Qt.ItemDataRole.EditRole)
            return self.db_mngr.get_value_from_data(data, role)
        return super().data(index, role)


class EntityMixin:
    def _do_add_items_to_db(self, db_map_items):
        raise NotImplementedError()

    def add_items_to_db(self, db_map_data, second_pass=False):
        """See base class."""
        # First add whatever is ready and also try to add entities on the fly
        self.build_lookup_dictionary(db_map_data)
        db_map_items = {}
        db_map_entities = {}
        db_map_error_log = {}
        for db_map, items in db_map_data.items():
            for item in items:
                item_to_add, errors = self._convert_to_db(item, db_map)
                entity, more_errors = self._make_entity_on_the_fly(item, db_map)
                if self._check_item(db_map, item_to_add):
                    db_map_items.setdefault(db_map, []).append(item_to_add)
                if entity:
                    already_added = db_map_entities.setdefault(db_map, [])
                    # If the entity exists already, don't try to add it a second time
                    if entity not in already_added:
                        already_added.append(entity)
                all_errors = errors + more_errors
                if all_errors:
                    db_map_error_log.setdefault(db_map, []).extend(all_errors)
                self._autocomplete_row(db_map, item_to_add)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
        if any(db_map_entities.values()):
            self.db_mngr.add_entities(db_map_entities)
        if any(db_map_items.values()) and second_pass:
            self._do_add_items_to_db(db_map_items)
        # Something might have become ready after adding the entities, so we do one more pass
        if not second_pass:
            self.add_items_to_db(db_map_data, second_pass=True)

    def _make_item(self, row):
        item = super()._make_item(row)
        if item["entity_byname"]:
            item["entity_byname"] = tuple(item["entity_byname"].split(DB_ITEM_SEPARATOR))
        return item


class EmptyParameterDefinitionModel(
    FillInValueListIdMixin,
    FillInEntityClassIdMixin,
    FillInParameterNameMixin,
    SplitValueAndTypeMixin,
    ParameterMixin,
    EmptyModelBase,
):
    """An empty parameter_definition model."""

    @property
    def item_type(self):
        return "parameter_definition"

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by handle_items_added."""
        return (item.get("entity_class_name"), item.get("parameter_name"))

    def add_items_to_db(self, db_map_data):
        """See base class."""
        self.build_lookup_dictionary(db_map_data)
        db_map_param_def = {}
        db_map_error_log = {}
        for db_map, items in db_map_data.items():
            for item in items:
                param_def, errors = self._convert_to_db(item, db_map)
                if self._check_item(param_def):
                    db_map_param_def.setdefault(db_map, []).append(param_def)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
                self._autocomplete_row(db_map, param_def)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return "entity_class_id" in item and "name" in item


class EmptyParameterValueModel(
    MakeEntityOnTheFlyMixin,
    InferEntityClassIdMixin,
    FillInAlternativeIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    SplitValueAndTypeMixin,
    ParameterMixin,
    EntityMixin,
    EmptyModelBase,
):
    """An empty parameter_value model."""

    @property
    def item_type(self):
        return "parameter_value"

    def _check_item(self, db_map, item):
        """Checks if a db item is ready to be inserted."""
        return all(
            key in item
            for key in ("entity_class_id", "entity_id", "parameter_definition_id", "alternative_id", "value")
        )

    def _make_unique_id(self, item):
        entity_byname = item.get("entity_byname")
        if entity_byname is None:
            entity_byname = ()
        return (
            item.get("entity_class_name"),
            DB_ITEM_SEPARATOR.join(entity_byname),
            item.get("parameter_name"),
            item.get("alternative_name"),
        )

    def _do_add_items_to_db(self, db_map_items):
        self.db_mngr.add_parameter_values(db_map_items)


class EmptyEntityAlternativeModel(
    MakeEntityOnTheFlyMixin,
    InferEntityClassIdMixin,
    FillInAlternativeIdMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    EntityMixin,
    EmptyModelBase,
):
    @property
    def item_type(self):
        return "entity_alternative"

    def _check_item(self, db_map, item):
        """Checks if a db item is ready to be inserted."""
        return all(key in item for key in ("entity_class_id", "entity_id", "alternative_id", "active"))

    def _make_unique_id(self, item):
        entity_byname = item.get("entity_byname")
        if entity_byname is None:
            entity_byname = ()
        return (
            item.get("entity_class_name"),
            DB_ITEM_SEPARATOR.join(entity_byname),
            item.get("alternative_name"),
        )

    def _do_add_items_to_db(self, db_map_items):
        self.db_mngr.add_entity_alternatives(db_map_items)
