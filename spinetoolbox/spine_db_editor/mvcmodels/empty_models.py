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

"""Empty models for parameter definitions and values."""
from PySide6.QtCore import Qt
from ...mvcmodels.empty_row_model import EmptyRowModel
from .single_and_empty_model_mixins import SplitValueAndTypeMixin, MakeEntityOnTheFlyMixin
from ...mvcmodels.shared import PARSED_ROLE, DB_MAP_ROLE
from ...helpers import rows_to_row_count_tuples, DB_ITEM_SEPARATOR


class EmptyModelBase(EmptyRowModel):
    """Base class for all empty models that go in a CompoundModelBase subclass."""

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (CompoundModelBase): the parent model
        """
        super().__init__(parent, parent.header)
        self.db_mngr = parent.db_mngr
        self.db_map = None
        self.entity_class_id = None

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def field_map(self):
        return self._parent.field_map

    def add_items_to_db(self, db_map_data):
        """Add items to db.

        Args:
            db_map_data (dict): mapping DiffDatabaseMapping instance to list of items
        """
        db_map_items = {}
        db_map_error_log = {}
        for db_map, items in db_map_data.items():
            for item in items:
                item_to_add, errors = self._convert_to_db(item)
                self._autocomplete_row(db_map, item_to_add)
                if self._check_item(item_to_add):
                    db_map_items.setdefault(db_map, []).append(item_to_add)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if any(db_map_items.values()):
            self._do_add_items_to_db(db_map_items)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by handle_items_added to identify
        which rows have been added and thus need to be removed."""
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
            unique_id = (database, *self._make_unique_id(self._convert_to_db(item)[0]))
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
        """Fills in entity_class_name whenever other selections make it obvious."""
        candidates = self._entity_class_name_candidates(db_map, item)
        row = item.pop("row", None)
        if len(candidates) == 1:
            entity_class_name = candidates[0]
            item["entity_class_name"] = entity_class_name
            self._main_data[row][self.header.index("entity_class_name")] = entity_class_name

    def _entity_class_name_candidates(self, db_map, item):
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
        return {"parameter_value": "value", "parameter_definition": "default_value"}[self.item_type]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if self.header[index.column()] == self.value_field and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.ItemDataRole.TextAlignmentRole,
            PARSED_ROLE,
        ):
            data = super().data(index, role=Qt.ItemDataRole.EditRole)
            return self.db_mngr.get_value_from_data(data, role)
        return super().data(index, role)

    @staticmethod
    def _entity_class_name_candidates_by_parameter(db_map, item):
        return [
            x["entity_class_name"]
            for x in db_map.get_items("parameter_definition", name=item.get("parameter_definition_name"))
        ]


class EntityMixin:
    def _do_add_items_to_db(self, db_map_items):
        raise NotImplementedError()

    def add_items_to_db(self, db_map_data):
        """Overriden to add entities on the fly first."""
        db_map_entities = {}
        db_map_error_log = {}
        for db_map, items in db_map_data.items():
            for item in items:
                item_to_add, _ = self._convert_to_db(item)
                self._autocomplete_row(db_map, item_to_add)
                entity, errors = self._make_entity_on_the_fly(item, db_map)
                if entity:
                    entities = db_map_entities.setdefault(db_map, [])
                    if entity not in entities:
                        entities.append(entity)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if any(db_map_entities.values()):
            self.db_mngr.add_entities(db_map_entities)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
        super().add_items_to_db(db_map_data)

    def _make_item(self, row):
        item = super()._make_item(row)
        byname = item["entity_byname"]
        item["entity_byname"] = tuple(byname.split(DB_ITEM_SEPARATOR)) if byname else ()
        return item

    @staticmethod
    def _entity_class_name_candidates_by_entity(db_map, item):
        return [x["entity_class_name"] for x in db_map.get_items("entity", entity_byname=item.get("entity_byname"))]


class EmptyParameterDefinitionModel(SplitValueAndTypeMixin, ParameterMixin, EmptyModelBase):
    """An empty parameter_definition model."""

    @property
    def item_type(self):
        return "parameter_definition"

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "name"))

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return item.get("entity_class_name") and item.get("name")

    def _entity_class_name_candidates(self, db_map, item):
        return []

    def _do_add_items_to_db(self, db_map_items):
        self.db_mngr.add_parameter_definitions(db_map_items)


class EmptyParameterValueModel(
    MakeEntityOnTheFlyMixin, SplitValueAndTypeMixin, ParameterMixin, EntityMixin, EmptyModelBase
):
    """An empty parameter_value model."""

    @property
    def item_type(self):
        return "parameter_value"

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return all(
            key in item
            for key in (
                "entity_class_name",
                "entity_byname",
                "parameter_definition_name",
                "alternative_name",
                "value",
                "type",
            )
        )

    def _make_unique_id(self, item):
        return tuple(
            item.get(x) for x in ("entity_class_name", "entity_byname", "parameter_definition_name", "alternative_name")
        )

    def _do_add_items_to_db(self, db_map_items):
        self.db_mngr.add_parameter_values(db_map_items)

    def _entity_class_name_candidates(self, db_map, item):
        candidates_by_parameter = self._entity_class_name_candidates_by_parameter(db_map, item)
        candidates_by_entity = self._entity_class_name_candidates_by_entity(db_map, item)
        if not candidates_by_parameter:
            return candidates_by_entity
        if not candidates_by_entity:
            return candidates_by_parameter
        return list(
            set(self._entity_class_name_candidates_by_parameter(db_map, item))
            & set(self._entity_class_name_candidates_by_entity(db_map, item))
        )


class EmptyEntityAlternativeModel(MakeEntityOnTheFlyMixin, EntityMixin, EmptyModelBase):
    @property
    def item_type(self):
        return "entity_alternative"

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return all(key in item for key in ("entity_class_name", "entity_byname", "alternative_name", "active"))

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "entity_byname", "alternative_name"))

    def _do_add_items_to_db(self, db_map_items):
        self.db_mngr.add_entity_alternatives(db_map_items)

    def _entity_class_name_candidates(self, db_map, item):
        return self._entity_class_name_candidates_by_entity(db_map, item)
