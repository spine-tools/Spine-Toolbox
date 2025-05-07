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

"""Empty models for dialogs as well as parameter definitions and values."""
from collections.abc import Iterable, Iterator
from typing import ClassVar, Optional
from PySide6.QtCore import QObject, Qt, Signal
from spinedb_api import DatabaseMapping
from spinedb_api.temp_id import TempId
from ...fetch_parent import FlexibleFetchParent
from ...helpers import DB_ITEM_SEPARATOR, DBMapDictItems, rows_to_row_count_tuples
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.shared import DB_MAP_ROLE, PARSED_ROLE
from ...spine_db_manager import SpineDBManager
from .single_and_empty_model_mixins import MakeEntityOnTheFlyMixin, SplitValueAndTypeMixin
from .utils import (
    ENTITY_ALTERNATIVE_MODEL_HEADER,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_DEFINITION_MODEL_HEADER,
    PARAMETER_VALUE_FIELD_MAP,
    PARAMETER_VALUE_MODEL_HEADER,
    cull_equal_rows_at_end,
)


class EmptyModelBase(EmptyRowModel):
    """Base class for all empty models that add new items to the database."""

    item_type: ClassVar[str] = NotImplemented
    can_be_filtered: ClassVar[bool] = False
    field_map: ClassVar[dict[str, str]] = {}

    def __init__(self, header: list[str], db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(parent, header)
        self.db_mngr = db_mngr
        self.entity_class_id: Optional[TempId] = None
        self._fetch_parent = FlexibleFetchParent(
            self.item_type,
            handle_items_added=self.handle_items_added,
            owner=self,
        )

    def add_items_to_db(self, db_map_data: DBMapDictItems) -> None:
        """Adds items to db.

        Args:
            db_map_data: mapping DatabaseMapping instance to list of items
        """
        db_map_items, db_map_error_log = self._data_to_items(db_map_data)
        if any(db_map_items.values()):
            self.db_mngr.add_items(self.item_type, db_map_items)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def _data_to_items(self, db_map_data: DBMapDictItems) -> tuple[DBMapDictItems, dict[DatabaseMapping, list[str]]]:
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
        return db_map_items, db_map_error_log

    def _make_unique_id(self, item: dict) -> tuple:
        """Returns a unique id for the given model item (name-based). Used by handle_items_added to identify
        which rows have been added and thus need to be removed."""
        raise NotImplementedError()

    def remove_rows(self, rows: Iterable[int]) -> None:
        """Removes given rows by removing the corresponding items from the db map."""
        for row in sorted(rows, reverse=True):
            self.removeRow(row)

    def accepted_rows(self) -> Iterator[int]:
        yield from range(self.rowCount())

    def handle_items_added(self, db_map_data: DBMapDictItems) -> None:
        """Finds and removes model items that were successfully added to the db."""
        added_ids = set()
        for db_map, items in db_map_data.items():
            database = self.db_mngr.name_registry.display_name(db_map.sa_url)
            for item in items:
                unique_id = (database, *self._make_unique_id(item))
                added_ids.add(unique_id)
        removed_rows = []
        for row in range(len(self._main_data)):
            item = self._make_item(row)
            database = item.get("database")
            unique_id = (database, *self._make_unique_id(self._convert_to_db(item)[0]))
            if unique_id in added_ids:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.removeRows(row, count)
        if len(self._main_data) > 1:
            cull_equal_rows_at_end(self._main_data, self.removeRow)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch. If successful, add items to db."""
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row() for ind in indexes}
        db_map_data = self._make_db_map_data(rows)
        self.add_items_to_db(db_map_data)
        return True

    def _autocomplete_row(self, db_map: DatabaseMapping, item: dict) -> None:
        """Fills in entity_class_name whenever other selections make it obvious."""
        if self._paste and item.get("entity_class_name"):
            # If the data is pasted and the entity class column is already filled,
            # trust that the user knows what they are doing. This makes pasting large
            # amounts of data significantly faster.
            del item["row"]
            return
        candidates = self._entity_class_name_candidates(db_map, item)
        row = item.pop("row", None)
        if len(candidates) == 1:
            entity_class_name = candidates[0]
            item["entity_class_name"] = entity_class_name
            self._main_data[row][self.header.index("entity_class_name")] = entity_class_name

    def _entity_class_name_candidates(self, db_map: DatabaseMapping, item: dict) -> list[str]:
        raise NotImplementedError()

    def _make_item(self, row: int) -> dict:
        return dict(zip(self.header, self._main_data[row]), row=row)

    def _make_db_map_data(self, rows: Iterable[int]) -> DBMapDictItems:
        """
        Returns model data grouped by database map.

        Args:
            rows: group data from these rows

        Returns:
            mapping DatabaseMapping instance to list of items
        """
        db_map_data = {}
        for row in rows:
            item = self._make_item(row)
            database = item.pop("database")
            try:
                db_map = next(
                    iter(
                        x for x in self.db_mngr.db_maps if self.db_mngr.name_registry.display_name(x.sa_url) == database
                    )
                )
            except StopIteration:
                continue
            item = {k: v for k, v in item.items() if v is not None}
            db_map_data.setdefault(db_map, []).append(item)
        return db_map_data

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == DB_MAP_ROLE:
            database = self.data(index, Qt.ItemDataRole.DisplayRole)
            return next(
                iter(x for x in self.db_mngr.db_maps if self.db_mngr.name_registry.display_name(x.sa_url) == database),
                None,
            )
        return super().data(index, role)

    def _convert_to_db(self, item: dict) -> dict:
        """Returns a db item (id-based) from the given model item (name-based)."""
        raise NotImplementedError()

    @staticmethod
    def _check_item(item: dict) -> bool:
        """Checks if a db item is ready to be inserted."""
        raise NotImplementedError()

    def reset_db_maps(self, db_maps: Iterable[DatabaseMapping]):
        self._fetch_parent.set_obsolete(False)
        self._fetch_parent.reset()
        for db_map in db_maps:
            self.db_mngr.register_fetch_parent(db_map, self._fetch_parent)


class ParameterMixin:
    value_field: ClassVar[str] = NotImplemented
    type_field: ClassVar[str] = NotImplemented

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if self.header[index.column()] == self.value_field and role in {
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.ItemDataRole.TextAlignmentRole,
            PARSED_ROLE,
        }:
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
    entities_added = Signal(object)

    def add_items_to_db(self, db_map_data):
        """Overridden to add entities on the fly first."""
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
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
        db_map_items, db_map_error_log = self._data_to_items(db_map_data)
        if any(db_map_items.values()):
            db_map_entities_to_add = self._clean_to_be_added_entities(db_map_entities, db_map_items)
            if any(db_map_entities_to_add.values()):
                self.db_mngr.add_items("entity", db_map_entities_to_add)
                self.entities_added.emit(db_map_entities_to_add)
            self.db_mngr.add_items(self.item_type, db_map_items)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    @staticmethod
    def _clean_to_be_added_entities(db_map_entities: DBMapDictItems, db_map_items: DBMapDictItems) -> DBMapDictItems:
        entity_names_by_db = {}
        for db_map, items in db_map_items.items():
            for item in items:
                entity_names_by_db.setdefault(db_map, set()).add(item["entity_byname"])
        new_to_be_added = {}
        for db_map, items in db_map_entities.items():
            for item in items:
                entity_names = entity_names_by_db.get(db_map)
                if entity_names and item["entity_byname"] in entity_names:
                    new_to_be_added.setdefault(db_map, []).append(item)
        return new_to_be_added

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

    item_type = "parameter_definition"
    field_map = PARAMETER_DEFINITION_FIELD_MAP
    value_field = "default_value"
    type_field = "default_type"

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(PARAMETER_DEFINITION_MODEL_HEADER, db_mngr, parent)

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "name"))

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return item.get("entity_class_name") and item.get("name")

    def _entity_class_name_candidates(self, db_map, item):
        return []


class EmptyParameterValueModel(
    MakeEntityOnTheFlyMixin, SplitValueAndTypeMixin, ParameterMixin, EntityMixin, EmptyModelBase
):
    """A self-contained empty parameter_value model."""

    item_type = "parameter_value"
    field_map = PARAMETER_VALUE_FIELD_MAP
    value_field = "value"
    type_field = "type"

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(PARAMETER_VALUE_MODEL_HEADER, db_mngr, parent)

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
    item_type = "entity_alternative"

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(ENTITY_ALTERNATIVE_MODEL_HEADER, db_mngr, parent)

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return all(key in item for key in ("entity_class_name", "entity_byname", "alternative_name", "active"))

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "entity_byname", "alternative_name"))

    def _entity_class_name_candidates(self, db_map, item):
        return self._entity_class_name_candidates_by_entity(db_map, item)


class EmptyAddEntityOrClassRowModel(EmptyRowModel):
    """A table model with a last empty row."""

    def __init__(self, parent=None, header=None):
        super().__init__(parent, header=header)
        self._entity_name_user_defined = False

    def batch_set_data(self, indexes, data):
        """Reimplemented to fill the entity class name automatically if its data is removed via pressing del."""
        if not indexes or not data:
            return False
        rows = []
        columns = []
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            if column == self.header.index(self._parent.dialog_item_name()) and not value:
                self._entity_name_user_defined = False
                self._main_data[row][column] = self._parent.construct_composite_name(index.row())
            else:
                self._main_data[row][column] = value
            rows.append(row)
            columns.append(column)
        if not (rows and columns):
            return False
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(
            self.index(top, left), self.index(bottom, right), [Qt.ItemDataRole.EditRole, Qt.ItemDataRole.DisplayRole]
        )
        return True

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Reimplemented to not overwrite user defined entity/class names with automatic composite names."""
        if index.column() != self.header.index(self._parent.dialog_item_name()):
            return super().setData(index, value, role)
        if role == Qt.ItemDataRole.UserRole:
            if self._entity_name_user_defined:
                return False
            role = Qt.ItemDataRole.EditRole
        else:
            self._entity_name_user_defined = bool(value)
        return super().setData(index, value, role)
