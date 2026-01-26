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
from __future__ import annotations
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, ClassVar
from PySide6.QtCore import QModelIndex, Qt, Slot
from spinedb_api import Asterisk, DatabaseMapping
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.helpers import AsteriskType
from spinedb_api.temp_id import TempId
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, order_key, order_key_from_names, plain_to_rich
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...mvcmodels.shared import (
    DB_MAP_ROLE,
    HAS_METADATA_ROLE,
    ITEM_ID_ROLE,
    ITEM_ROLE,
    PARAMETER_TYPE_VALIDATION_ROLE,
    PARSED_ROLE,
)
from ...parameter_type_validation import ValidationKey
from ..mvcmodels.single_and_empty_model_mixins import SplitValueAndTypeMixin
from ..selection_for_filtering import AlternativeSelection, EntitySelection, ScenarioSelection
from .colors import FIXED_FIELD_COLOR
from .utils import (
    ENTITY_ALTERNATIVE_FIELD_MAP,
    ENTITY_FIELD_MAP,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_VALUE_FIELD_MAP,
    field_index,
    make_entity_on_the_fly,
)

if TYPE_CHECKING:
    from .compound_models import CompoundStackedModel


class HalfSortedTableModel(MinimalTableModel[TempId]):
    def reset_model(self, main_data: list[TempId] | None = None):
        """Reset model."""
        if main_data is None:
            main_data = []
        self.beginResetModel()
        self._main_data = sorted(main_data, key=self._sort_key)
        self.endResetModel()

    def add_rows(self, data: list[TempId]) -> None:
        data = [item for item in data if item not in self._main_data]
        if not data:
            return
        self.beginResetModel()
        self._main_data += data
        self._main_data.sort(key=self._sort_key)
        self.endResetModel()

    def _sort_key(self, item_id: TempId) -> str | tuple[str, ...]:
        raise NotImplementedError()


class SingleModelBase(HalfSortedTableModel):
    """Base class for all single models that go in a CompoundModelBase subclass."""

    entity_class_column: ClassVar[int] = NotImplemented
    database_column: ClassVar[int] = NotImplemented
    group_columns: ClassVar[set[int]] = set()
    fixed_columns: ClassVar[tuple[int, ...]] = ()
    _AUTO_FILTER_FORCE_COMPARE_DISPLAY_VALUES: ClassVar[set[str]] = set()

    def __init__(
        self,
        parent: CompoundStackedModel,
        db_map: DatabaseMapping,
        entity_class_id: TempId,
        committed: bool,
        lazy: bool = False,
    ):
        super().__init__(parent=parent, header=parent.header, lazy=lazy)
        self.db_mngr = parent.db_mngr
        self.db_map = db_map
        self._mapped_table = self.db_map.mapped_table(parent.item_type)
        self.entity_class_id = entity_class_id
        self._auto_filter: dict[str, set] = {}
        self.committed = committed

    def __lt__(self, other):
        entity_class = self.db_map.mapped_table("entity_class")[self.entity_class_id]
        class_name = entity_class["name"]
        other_entity_class = other.db_map.mapped_table("entity_class")[other.entity_class_id]
        other_class_name = other_entity_class["name"]
        if class_name == other_class_name:
            return self.db_mngr.name_registry.display_name(
                self.db_map.sa_url
            ) < self.db_mngr.name_registry.display_name(other.db_map.sa_url)
        keys = (len(entity_class["dimension_id_list"]), class_name)
        other_keys = (len(other_entity_class["dimension_id_list"]), other_class_name)
        return keys < other_keys

    @property
    def item_type(self) -> str:
        return self._parent.item_type

    @property
    def field_map(self) -> dict[str, str]:
        return self._parent.field_map

    def update_items_in_db(self, items: list[dict]) -> None:
        """Update items in db. Required by batch_set_data"""
        items_to_upd = []
        for item in items:
            item_to_upd = self._convert_to_db(item)
            if tuple(item_to_upd.keys()) != ("id",):
                items_to_upd.append(item_to_upd)
        if items_to_upd:
            self.db_mngr.update_items(self._parent.item_type, {self.db_map: items_to_upd})

    def _convert_to_db(self, item: dict) -> dict:
        return item

    @property
    def _references(self) -> dict[str, tuple[str, str | None]]:
        raise NotImplementedError()

    def item_id(self, row: int) -> TempId:
        """Returns item's id for row.

        Args:
            row: row index

        Returns:
            item's id
        """
        return self._main_data[row]

    def item_ids(self) -> set[TempId]:
        """Returns model's parameter ids."""
        return set(self._main_data)

    def db_item(self, index: QModelIndex) -> PublicItem:
        id_ = self._main_data[index.row()]
        return self._mapped_table[id_]

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if index.column() in self.fixed_columns:
            return flags & ~Qt.ItemFlag.ItemIsEditable
        return flags

    def _display_value_for_forced_comparison(self, item: PublicItem) -> str:
        raise NotImplementedError()

    def filter_accepts_item(self, item: PublicItem) -> bool:
        if not self._auto_filter:
            return True
        for field, values in self._auto_filter.items():
            if field in self._AUTO_FILTER_FORCE_COMPARE_DISPLAY_VALUES:
                display_value = self._display_value_for_forced_comparison(item)
                if display_value not in values:
                    return False
            elif item[field] not in values:
                return False
        return True

    def set_auto_filter(self, auto_filter: dict[str, set | None]) -> None:
        self._auto_filter = auto_filter

    def accepted_rows(self) -> Iterator[int]:
        """Yields accepted rows, for convenience."""
        mapped_table = self._mapped_table
        for row in range(self.rowCount()):
            item = mapped_table[self._main_data[row]]
            if self.filter_accepts_item(item):
                yield row

    def _get_ref(self, db_item: PublicItem, field: str) -> PublicItem | None:
        """Returns the item referred by the given field."""
        ref = self._references.get(field)
        if ref is None:
            return None
        src_id_key, ref_type = ref
        ref_id = db_item.get(src_id_key)
        if ref_id is None:
            return None
        mapped_ref_table = self.db_map.mapped_table(ref_type)
        return mapped_ref_table[ref_id]

    def insertRows(self, row, count, parent=QModelIndex()):
        return False

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        column = index.column()
        if role == Qt.ItemDataRole.BackgroundRole and column in self.fixed_columns:
            return FIXED_FIELD_COLOR
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole):
            if column == self.database_column:
                return self.db_mngr.name_registry.display_name(self.db_map.sa_url)
            id_ = self._main_data[index.row()]
            item = self._mapped_table[id_]
            field = self._parent.field_map[self.header[column]]
            if role == Qt.ItemDataRole.ToolTipRole:
                ref_item = self._get_ref(item, field)
                if ref_item is not None and (description := ref_item.get("description")):
                    return plain_to_rich(description)
            data = item.get(field)
            if index.column() in self.group_columns and role != Qt.ItemDataRole.EditRole:
                data = DB_ITEM_SEPARATOR.join(data) if data else None
            return data
        if role == Qt.ItemDataRole.DecorationRole and column == self.entity_class_column:
            return self.db_mngr.entity_class_icon(self.db_map, self.entity_class_id)
        if role == DB_MAP_ROLE:
            return self.db_map
        if role == ITEM_ID_ROLE:
            return self._main_data[index.row()]
        if role == ITEM_ROLE:
            return self._mapped_table[self._main_data[index.row()]]
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Sets data directly in database using db mngr. If successful, updated data will be
        automatically seen by the data method.
        """
        if not indexes or not data:
            return False
        row_data = {}
        field_map = self._parent.field_map
        for index, value in zip(indexes, data):
            row_data.setdefault(index.row(), {})[field_map[self.header[index.column()]]] = value
        items = [{"id": self._main_data[row], **data} for row, data in row_data.items()]
        self.update_items_in_db(items)
        return True


class FilterEntityMixin:
    """Provides the interface to filter by entity."""

    _ENTITY_ID_FIELD: ClassVar[str] = "entity_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_entity_ids: set[TempId] | AsteriskType = Asterisk

    def set_filter_entity_ids(self, entity_selection: EntitySelection) -> bool:
        if entity_selection is Asterisk or not entity_selection:
            entity_ids = Asterisk
        else:
            try:
                selected_entities_by_class = entity_selection[self.db_map]
            except KeyError:
                entity_ids = set()
            else:
                if self.entity_class_id in selected_entities_by_class:
                    entity_ids = selected_entities_by_class[self.entity_class_id]
                else:
                    entity_ids = set()
                    for class_id, entity_selection in selected_entities_by_class.items():
                        if entity_selection is Asterisk:
                            entity_ids = Asterisk
                            break
                        entity_ids.update(entity_selection)
        if entity_ids == self._filter_entity_ids:
            return False
        self._filter_entity_ids = entity_ids
        return True

    def filter_accepts_item(self, item: PublicItem) -> bool:
        """Reimplemented to also account for the entity filter."""
        if self._filter_entity_ids is Asterisk:
            return super().filter_accepts_item(item)
        entity_id = item[self._ENTITY_ID_FIELD]
        entity_accepts = entity_id in self._filter_entity_ids or self.db_mngr.relationship_graph.is_any_id_reachable(
            self.db_map, entity_id, self._filter_entity_ids
        )
        return entity_accepts and super().filter_accepts_item(item)


class FilterAlternativeMixin:
    """Provides the interface to filter by alternative."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_alternative_ids = set()

    def set_filter_alternative_ids(self, alternative_selection: AlternativeSelection) -> bool:
        if alternative_selection is Asterisk:
            alternative_ids = Asterisk
        else:
            alternative_ids = alternative_selection.get(self.db_map, set())
        if self._filter_alternative_ids == alternative_ids:
            return False
        self._filter_alternative_ids = alternative_ids
        return True

    def filter_accepts_item(self, item: PublicItem) -> bool:
        """Reimplemented to also account for the alternative filter."""
        if self._filter_alternative_ids is Asterisk:
            return super().filter_accepts_item(item)
        return item["alternative_id"] in self._filter_alternative_ids and super().filter_accepts_item(item)


class ParameterMixin:
    """Provides the data method for parameter values and definitions."""

    value_field: ClassVar[str] = NotImplemented
    VALUE_COLUMN: ClassVar[int] = NotImplemented
    type_field: ClassVar[str] = NotImplemented
    parameter_definition_id_key: ClassVar[str] = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ids_pending_type_validation = set()
        self.destroyed.connect(self._stop_waiting_validation)

    @property
    def _references(self) -> dict[str, tuple[str, str | None]]:
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

    def reset_model(self, main_data: list[TempId] | None = None) -> None:
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
        if index.column() == self.VALUE_COLUMN and role in {
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.ItemDataRole.TextAlignmentRole,
            PARSED_ROLE,
            PARAMETER_TYPE_VALIDATION_ROLE,
        }:
            id_ = self._main_data[index.row()]
            with self.db_mngr.get_lock(self.db_map):
                item = self._mapped_table[id_]
                return self.db_mngr.get_value(self.db_map, item, role)
        return super().data(index, role)

    def add_rows(self, ids: list[TempId]) -> None:
        super().add_rows(ids)
        self._start_validating_types(ids)

    def revalidate_item_types(self, items: PublicItem) -> None:
        ids = tuple(item["id"] for item in items)
        self._start_validating_types(ids)

    def _start_validating_types(self, ids: Iterable[TempId]) -> None:
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

    def _parameter_type_validated(self, keys: list[ValidationKey], is_valid_list: list[bool]) -> None:
        """Notifies the model that values have been validated.

        Args:
            keys: validation keys
            is_valid_list: True if value type is valid, False otherwise for each key
        """
        db_map_id = id(self.db_map)
        private_ids_of_interest = set()
        for key in keys:
            if key.item_type != self._parent.item_type or key.db_map_id != db_map_id:
                continue
            private_ids_of_interest.add(key.item_private_id)
        if not private_ids_of_interest:
            return
        self._ids_pending_type_validation -= private_ids_of_interest
        if not self._ids_pending_type_validation:
            self.db_mngr.parameter_type_validator.validated.disconnect(self._parameter_type_validated)
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
        top_left = self.index(min_row, self.VALUE_COLUMN)
        bottom_right = self.index(max_row, self.VALUE_COLUMN)
        self.dataChanged.emit(top_left, bottom_right, [PARAMETER_TYPE_VALIDATION_ROLE])

    @Slot(object)
    def _stop_waiting_validation(self) -> None:
        """Stops the model from waiting for type validation notifications."""
        if self._ids_pending_type_validation:
            self.db_mngr.parameter_type_validator.validated.disconnect(self._parameter_type_validated)
            self._ids_pending_type_validation.clear()

    def _display_value_for_forced_comparison(self, item):
        return self.db_mngr.get_value(self.db_map, item, Qt.ItemDataRole.DisplayRole)


class EntityMixin:

    def update_items_in_db(self, items: list[dict]) -> None:
        """Overridden to create entities on the fly first."""
        class_name = self.db_map.mapped_table("entity_class")[self.entity_class_id]["name"]
        for item in items:
            item["entity_class_name"] = class_name
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


class SingleParameterDefinitionModel(SplitValueAndTypeMixin, ParameterMixin, SingleModelBase):
    """A parameter_definition model for a single entity_class."""

    entity_class_column = field_index("entity_class_name", PARAMETER_DEFINITION_FIELD_MAP)
    database_column = field_index("database", PARAMETER_DEFINITION_FIELD_MAP)
    value_field = "default_value"
    VALUE_COLUMN = field_index("default_value", PARAMETER_DEFINITION_FIELD_MAP)
    type_field = "default_type"
    parameter_definition_id_key = "id"
    group_columns = {field_index("parameter_type_list", PARAMETER_DEFINITION_FIELD_MAP)}
    fixed_columns = (
        field_index("entity_class_name", PARAMETER_DEFINITION_FIELD_MAP),
        field_index("database", PARAMETER_DEFINITION_FIELD_MAP),
    )
    _AUTO_FILTER_FORCE_COMPARE_DISPLAY_VALUES = {"default_value"}

    def _sort_key(self, item_id):
        item = self._mapped_table[item_id]
        return order_key(item["name"])


class SingleParameterValueModel(
    SplitValueAndTypeMixin,
    ParameterMixin,
    EntityMixin,
    FilterAlternativeMixin,
    FilterEntityMixin,
    SingleModelBase,
):
    """A parameter_value model for a single entity_class."""

    entity_class_column = field_index("entity_class_name", PARAMETER_VALUE_FIELD_MAP)
    database_column = field_index("database", PARAMETER_VALUE_FIELD_MAP)
    group_columns = {field_index("entity_byname", PARAMETER_VALUE_FIELD_MAP)}
    fixed_columns = (
        field_index("entity_class_name", PARAMETER_VALUE_FIELD_MAP),
        field_index("database", PARAMETER_VALUE_FIELD_MAP),
    )
    value_field = "value"
    VALUE_COLUMN = field_index("value", PARAMETER_VALUE_FIELD_MAP)
    type_field = "type"
    parameter_definition_id_key = "parameter_id"
    _AUTO_FILTER_FORCE_COMPARE_DISPLAY_VALUES = {"value"}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == HAS_METADATA_ROLE:
            metadata_table = self.db_map.mapped_table("parameter_value_metadata")
            value_id = self._main_data[index.row()]
            return any(metadata_item["parameter_value_id"] == value_id for metadata_item in metadata_table.values())
        return super().data(index, role)

    def _sort_key(self, item_id):
        item = self._mapped_table[item_id]
        byname = order_key_from_names(item["entity_byname"])
        parameter_name = order_key(item["parameter_name"])
        alt_name = order_key(item["alternative_name"])
        return byname, parameter_name, alt_name


class SingleEntityAlternativeModel(FilterAlternativeMixin, FilterEntityMixin, SingleModelBase):
    """An entity_alternative model for a single entity_class."""

    entity_class_column = field_index("entity_class_name", ENTITY_ALTERNATIVE_FIELD_MAP)
    database_column = field_index("database", ENTITY_ALTERNATIVE_FIELD_MAP)
    fixed_columns = (
        field_index("entity_class_name", ENTITY_ALTERNATIVE_FIELD_MAP),
        field_index("database", ENTITY_ALTERNATIVE_FIELD_MAP),
    )
    group_columns = {field_index("entity_byname", ENTITY_ALTERNATIVE_FIELD_MAP)}

    def _sort_key(self, item_id):
        item = self._mapped_table[item_id]
        byname = order_key_from_names(item["entity_byname"])
        alt_name = order_key(item["alternative_name"])
        return byname, alt_name

    @property
    def _references(self):
        return {
            "entity_class_name": ("entity_class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "alternative_name": ("alternative_id", "alternative"),
            "database": ("database", None),
        }


class SingleEntityModel(FilterEntityMixin, SingleModelBase):
    entity_class_column = field_index("entity_class_name", ENTITY_FIELD_MAP)
    database_column = field_index("database", ENTITY_FIELD_MAP)
    _NUMERICAL_COLUMNS: ClassVar[set[int]] = {
        field_index("lat", ENTITY_FIELD_MAP),
        field_index("lon", ENTITY_FIELD_MAP),
        field_index("alt", ENTITY_FIELD_MAP),
    }
    _BYNAME_COLUMN: ClassVar[int] = field_index("entity_byname", ENTITY_FIELD_MAP)
    _SHAPE_BLOB_COLUMN: ClassVar[int] = field_index("shape_blob", ENTITY_FIELD_MAP)
    fixed_columns = (field_index("entity_class_name", ENTITY_FIELD_MAP), field_index("database", ENTITY_FIELD_MAP))
    group_columns = {field_index("entity_byname", ENTITY_FIELD_MAP)}
    _ENTITY_ID_FIELD = "id"
    _AUTO_FILTER_FORCE_COMPARE_DISPLAY_VALUES = {"shape_blob"}

    def __init__(
        self,
        parent: CompoundStackedModel,
        db_map: DatabaseMapping,
        entity_class_id: TempId,
        committed: bool,
        lazy: bool = False,
    ):
        super().__init__(parent, db_map, entity_class_id, committed, lazy)
        self._entity_class_dimensions = len(db_map.mapped_table("entity_class")[entity_class_id]["dimension_id_list"])
        self._filter_scenario_ids: set[TempId] | AsteriskType = Asterisk

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == self._BYNAME_COLUMN and self._entity_class_dimensions == 0:
            flags = flags & ~Qt.ItemFlag.ItemIsEditable
        return flags

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        column = index.column()
        if role == HAS_METADATA_ROLE:
            metadata_table = self.db_map.mapped_table("entity_metadata")
            entity_id = self._main_data[index.row()]
            return any(metadata_item["entity_id"] == entity_id for metadata_item in metadata_table.values())
        if column in self._NUMERICAL_COLUMNS:
            if role == Qt.ItemDataRole.DisplayRole:
                data = super().data(index, role)
                return str(data) if data is not None else None
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        elif column == self._SHAPE_BLOB_COLUMN and role == Qt.ItemDataRole.DisplayRole:
            entity_item = self._mapped_table[self._main_data[index.row()]]
            return None if entity_item["shape_blob"] is None else "<geojson>"
        elif (
            column == self._BYNAME_COLUMN
            and role == Qt.ItemDataRole.BackgroundRole
            and self._entity_class_dimensions == 0
        ):
            return FIXED_FIELD_COLOR
        return super().data(index, role)

    def _sort_key(self, item_id: TempId) -> list[str]:
        item = self._mapped_table[item_id]
        byname = order_key_from_names(item["entity_byname"])
        return byname

    @property
    def _references(self) -> dict[str, tuple[str, str | None]]:
        return {
            "entity_class_name": ("class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "database": ("database", None),
        }

    def set_filter_scenario_ids(self, scenario_selection: ScenarioSelection) -> bool:
        if scenario_selection is Asterisk:
            scenario_ids = Asterisk
        else:
            try:
                scenario_ids = scenario_selection[self.db_map]
            except KeyError:
                scenario_ids = set()
        if scenario_ids == self._filter_scenario_ids:
            return False
        self._filter_scenario_ids = scenario_ids
        return True

    def filter_accepts_item(self, item: PublicItem) -> bool:
        if self._filter_scenario_ids is Asterisk:
            return super().filter_accepts_item(item)
        if not self._filter_scenario_ids:
            return False
        active_by_default = self.db_map.mapped_table("entity_class")[self.entity_class_id]["active_by_default"]
        for scenario_id in self._filter_scenario_ids:
            is_active = self.db_map.item_active_in_scenario(item, scenario_id)
            if is_active is False or (is_active is None and not active_by_default):
                return False
        return super().filter_accepts_item(item)

    def _display_value_for_forced_comparison(self, item):
        return "<geojson>" if item["shape_blob"] is not None else None
