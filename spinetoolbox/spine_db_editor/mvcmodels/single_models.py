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

"""Single models for parameter definitions and values (as 'for a single entity')."""
from typing import ClassVar, Iterable
from PySide6.QtCore import QModelIndex, Qt, Slot
from spinedb_api.temp_id import TempId
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, order_key, plain_to_rich
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...mvcmodels.shared import DB_MAP_ROLE, PARAMETER_TYPE_VALIDATION_ROLE, PARSED_ROLE
from ..mvcmodels.single_and_empty_model_mixins import SplitValueAndTypeMixin
from .colors import FIXED_FIELD_COLOR
from .utils import make_entity_on_the_fly


class HalfSortedTableModel(MinimalTableModel[TempId]):
    def reset_model(self, main_data=None):
        """Reset model."""
        if main_data is None:
            main_data = []
        self.beginResetModel()
        self._main_data = sorted(main_data, key=self._sort_key)
        self.endResetModel()

    def add_rows(self, data):
        data = [item for item in data if item not in self._main_data]
        if not data:
            return
        self.beginResetModel()
        self._main_data += data
        self._main_data.sort(key=self._sort_key)
        self.endResetModel()

    def _sort_key(self, element):
        return element


class SingleModelBase(HalfSortedTableModel):
    """Base class for all single models that go in a CompoundModelBase subclass."""

    item_type: ClassVar[str] = NotImplemented
    group_fields: ClassVar[Iterable[str]] = ()
    can_be_filtered = True

    def __init__(self, parent, db_map, entity_class_id, committed, lazy=False):
        """
        Args:
            parent (CompoundModelBase): the parent model
            db_map (DatabaseMapping)
            entity_class_id (int)
            committed (bool)
            lazy (bool)
        """
        super().__init__(parent=parent, header=parent.header, lazy=lazy)
        self.db_mngr = parent.db_mngr
        self.db_map = db_map
        self.entity_class_id = entity_class_id
        self._auto_filter = {}  # Maps field to accepted ids for that field
        self.committed = committed

    def __lt__(self, other):
        if self.entity_class_name == other.entity_class_name:
            return self.db_mngr.name_registry.display_name(
                self.db_map.sa_url
            ) < self.db_mngr.name_registry.display_name(other.db_map.sa_url)
        keys = {}
        for side, model in {"left": self, "right": other}.items():
            dim = len(model.dimension_id_list)
            class_name = model.entity_class_name
            keys[side] = (
                dim,
                class_name,
            )
        return keys["left"] < keys["right"]

    @property
    def field_map(self):
        return self._parent.field_map

    def update_items_in_db(self, items):
        """Update items in db. Required by batch_set_data"""
        items_to_upd = []
        for item in items:
            item_to_upd = self._convert_to_db(item)
            if tuple(item_to_upd.keys()) != ("id",):
                items_to_upd.append(item_to_upd)
        if items_to_upd:
            self._do_update_items_in_db({self.db_map: items_to_upd})

    def _convert_to_db(self, item: dict) -> dict:
        return item.copy()

    @property
    def _references(self):
        raise NotImplementedError()

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, "entity_class", self.entity_class_id)["name"]

    @property
    def dimension_id_list(self):
        return self.db_mngr.get_item(self.db_map, "entity_class", self.entity_class_id)["dimension_id_list"]

    @property
    def fixed_fields(self):
        return ["entity_class_name", "database"]

    def _mapped_field(self, field):
        return self.field_map.get(field, field)

    def item_id(self, row):
        """Returns parameter id for row.

        Args:
            row (int): row index

        Returns:
            int: parameter id
        """
        return self._main_data[row]

    def item_ids(self):
        """Returns model's parameter ids.

        Returns:
            set of int: ids
        """
        return set(self._main_data)

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
            return flags & ~Qt.ItemFlag.ItemIsEditable
        return flags

    def _filter_accepts_row(self, row):
        item = self.db_mngr.get_item(self.db_map, self.item_type, self._main_data[row])
        return self.filter_accepts_item(item)

    def filter_accepts_item(self, item):
        return self._auto_filter_accepts_item(item)

    def set_auto_filter(self, field, values):
        if values == self._auto_filter.get(field, set()):
            return False
        self._auto_filter[field] = values
        return True

    def _auto_filter_accepts_item(self, item):
        """Returns the result of the auto filter."""
        if self._auto_filter is None:
            return False
        for field, values in self._auto_filter.items():
            if values and item.get(field) not in values:
                return False
        return True

    def accepted_rows(self):
        """Yields accepted rows, for convenience."""
        for row in range(self.rowCount()):
            if self._filter_accepts_row(row):
                yield row

    def _get_ref(self, db_item, field):
        """Returns the item referred by the given field."""
        ref = self._references.get(field)
        if ref is None:
            return {}
        src_id_key, ref_type = ref
        ref_id = db_item.get(src_id_key)
        return self.db_mngr.get_item(self.db_map, ref_type, ref_id)

    def insertRows(self, row, count, parent=QModelIndex()):
        return False

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        field = self.header[index.column()]
        if role == Qt.ItemDataRole.BackgroundRole and field in self.fixed_fields:
            return FIXED_FIELD_COLOR
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole):
            if field == "database":
                return self.db_mngr.name_registry.display_name(self.db_map.sa_url)
            id_ = self._main_data[index.row()]
            item = self.db_mngr.get_item(self.db_map, self.item_type, id_)
            if role == Qt.ItemDataRole.ToolTipRole:
                ref_item = self._get_ref(item, field)
                if ref_item is not None and (description := ref_item.get("description")):
                    return plain_to_rich(description)
            mapped_field = self._mapped_field(field)
            data = item.get(mapped_field)
            if field in self.group_fields and role != Qt.ItemDataRole.EditRole:
                data = DB_ITEM_SEPARATOR.join(data) if data else None
            return data
        if role == Qt.ItemDataRole.DecorationRole and field == "entity_class_name":
            return self.db_mngr.entity_class_icon(self.db_map, self.entity_class_id)
        if role == DB_MAP_ROLE:
            return self.db_map
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Sets data directly in database using db mngr. If successful, updated data will be
        automatically seen by the data method.
        """
        if not indexes or not data:
            return False
        row_data = {}
        for index, value in zip(indexes, data):
            row_data.setdefault(index.row(), {})[self.header[index.column()]] = value
        items = [{"id": self._main_data[row], **data} for row, data in row_data.items()]
        self.update_items_in_db(items)
        return True


class FilterEntityAlternativeMixin:
    """Provides the interface to filter by entity and alternative."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_alternative_ids = set()
        self._filter_entity_ids = set()

    def set_filter_entity_ids(self, db_map_class_entity_ids):
        # Don't accept entity id filters from entities that don't belong in this model
        filter_entity_ids = set().union(
            *(
                ent_ids
                for (db_map, class_id), ent_ids in db_map_class_entity_ids.items()
                if db_map == self.db_map and (class_id == self.entity_class_id or class_id in self.dimension_id_list)
            )
        )
        if self._filter_entity_ids == filter_entity_ids:
            return False
        self._filter_entity_ids = filter_entity_ids
        return True

    def set_filter_alternative_ids(self, db_map_alternative_ids):
        alternative_ids = db_map_alternative_ids.get(self.db_map, set())
        if self._filter_alternative_ids == alternative_ids:
            return False
        self._filter_alternative_ids = alternative_ids
        return True

    def filter_accepts_item(self, item):
        """Reimplemented to also account for the entity and alternative filter."""
        return (
            super().filter_accepts_item(item)
            and self._entity_filter_accepts_item(item)
            and self._alternative_filter_accepts_item(item)
        )

    def _entity_filter_accepts_item(self, item):
        """Returns the result of the entity filter."""
        if not self._filter_entity_ids:  # If no entities are selected, only entity classes
            return True
        entity_id = item[self._mapped_field("entity_id")]
        return entity_id in self._filter_entity_ids or bool(set(item["element_id_list"]) & self._filter_entity_ids)

    def _alternative_filter_accepts_item(self, item):
        """Returns the result of the alternative filter."""
        if not self._filter_alternative_ids:
            return True
        alternative_id = item.get("alternative_id")
        return alternative_id is None or alternative_id in self._filter_alternative_ids


class ParameterMixin:
    """Provides the data method for parameter values and definitions."""

    value_field: ClassVar[str] = NotImplemented
    type_field: ClassVar[str] = NotImplemented
    parameter_definition_id_key: ClassVar[str] = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ids_pending_type_validation = set()
        self.destroyed.connect(self._stop_waiting_validation)

    @property
    def _references(self):
        return {
            "entity_class_name": ("entity_class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "parameter_name": (self.parameter_definition_id_key, "parameter_definition"),
            "value_list_name": ("value_list_id", "parameter_value_list"),
            "description": ("id", "parameter_definition"),
            "value": ("id", "parameter_value"),
            "default_value": ("id", "parameter_definition"),
            "database": ("database", None),
            "alternative_name": ("alternative_id", "alternative"),
        }

    def reset_model(self, main_data=None):
        """Resets the model."""
        super().reset_model(main_data)
        if self._ids_pending_type_validation:
            self.db_mngr.parameter_type_validator.validated.disconnect(self._parameter_type_validated)
        self._ids_pending_type_validation.clear()
        if main_data:
            self._start_validating_types(main_data)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Gets the id and database for the row, and reads data from the db manager
        using the item_type property.
        Paint the object_class icon next to the name.
        Also paint background of fixed indexes gray and apply custom format to JSON fields."""
        field = self.header[index.column()]
        # Display, edit, tool tip, alignment role of 'value fields'
        if field == self.value_field and role in {
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.ItemDataRole.TextAlignmentRole,
            PARSED_ROLE,
            PARAMETER_TYPE_VALIDATION_ROLE,
        }:
            id_ = self._main_data[index.row()]
            with self.db_mngr.get_lock(self.db_map):
                item = self.db_mngr.get_item(self.db_map, self.item_type, id_)
                return self.db_mngr.get_value(self.db_map, item, role)
        return super().data(index, role)

    def add_rows(self, ids):
        super().add_rows(ids)
        self._start_validating_types(ids)

    def revalidate_item_types(self, items):
        ids = tuple(item["id"] for item in items)
        self._start_validating_types(ids)

    def _start_validating_types(self, ids):
        """"""
        private_ids = set(temp_id.private_id for temp_id in ids)
        new_ids = private_ids - self._ids_pending_type_validation
        if not new_ids:
            return
        self._ids_pending_type_validation |= new_ids
        self.db_mngr.parameter_type_validator.validated.connect(
            self._parameter_type_validated, Qt.ConnectionType.UniqueConnection
        )
        self.db_mngr.parameter_type_validator.start_validating(
            self.db_mngr, self.db_map, (id_ for id_ in ids if id_.private_id in new_ids)
        )

    def _parameter_type_validated(self, keys, is_valid_list):
        """Notifies the model that values have been validated.

        Args:
            keys (list of ValidationKey): validation keys
            is_valid_list (list of bool): True if value type is valid, False otherwise for each key
        """
        db_map_id = id(self.db_map)
        private_ids_of_interest = set()
        for key in keys:
            if key.item_type != self.item_type or key.db_map_id != db_map_id:
                continue
            private_ids_of_interest.add(key.item_private_id)
        if not private_ids_of_interest:
            return
        self._ids_pending_type_validation -= private_ids_of_interest
        if not self._ids_pending_type_validation:
            self.db_mngr.parameter_type_validator.validated.disconnect(self._parameter_type_validated)
        value_column = self.header.index(self.value_field)
        min_row = None
        max_row = None
        for row, id_ in enumerate(self._main_data):
            if id_.private_id in private_ids_of_interest:
                private_ids_of_interest.discard(id_.private_id)
                if min_row is None:
                    min_row = row
                max_row = row
                if not private_ids_of_interest:
                    break
        if min_row is None:
            return
        top_left = self.index(min_row, value_column)
        bottom_right = self.index(max_row, value_column)
        self.dataChanged.emit(top_left, bottom_right, [PARAMETER_TYPE_VALIDATION_ROLE])

    @Slot(object)
    def _stop_waiting_validation(self):
        """Stops the model from waiting for type validation notifications."""
        if self._ids_pending_type_validation:
            self.db_mngr.parameter_type_validator.validated.disconnect(self._parameter_type_validated)
            self._ids_pending_type_validation.clear()


class EntityMixin:
    group_fields = ("entity_byname",)

    def update_items_in_db(self, items):
        """Overriden to create entities on the fly first."""
        for item in items:
            item["entity_class_name"] = self.entity_class_name
        entities = []
        error_log = []
        for item in items:
            entity, errors = make_entity_on_the_fly(item, self.db_map)
            if entity:
                entities.append(entity)
            if errors:
                error_log.extend(errors)
        if entities:
            self.db_mngr.add_items("entity", {self.db_map: entities})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})
        super().update_items_in_db(items)

    def _do_update_items_in_db(self, db_map_data):
        self.db_mngr.update_items(self.item_type, db_map_data)


class SingleParameterDefinitionModel(SplitValueAndTypeMixin, ParameterMixin, SingleModelBase):
    """A parameter_definition model for a single entity_class."""

    item_type = "parameter_definition"
    value_field = "default_value"
    type_field = "default_type"
    parameter_definition_id_key = "id"
    group_fields = ("valid types",)

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        return order_key(item.get("name", ""))

    def _do_update_items_in_db(self, db_map_data):
        self.db_mngr.update_items("parameter_definition", db_map_data)


class SingleParameterValueModel(
    SplitValueAndTypeMixin,
    ParameterMixin,
    EntityMixin,
    FilterEntityAlternativeMixin,
    SingleModelBase,
):
    """A parameter_value model for a single entity_class."""

    item_type = "parameter_value"
    value_field = "value"
    type_field = "type"
    parameter_definition_id_key = "parameter_id"

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        byname = order_key("__".join(item.get("entity_byname", ())))
        parameter_name = order_key(item.get("parameter_name", ""))
        alt_name = order_key(item.get("alternative_name", ""))
        return byname, parameter_name, alt_name


class SingleEntityAlternativeModel(EntityMixin, FilterEntityAlternativeMixin, SingleModelBase):
    """An entity_alternative model for a single entity_class."""

    item_type = "entity_alternative"

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        byname = order_key("__".join(item.get("entity_byname", ())))
        alt_name = order_key(item.get("alternative_name", ""))
        return byname, alt_name

    @property
    def _references(self):
        return {
            "entity_class_name": ("entity_class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "alternative_name": ("alternative_id", "alternative"),
            "database": ("database", None),
        }
