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
from __future__ import annotations
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from typing import ClassVar, Optional
from PySide6.QtCore import QModelIndex, QObject, Qt, Signal, Slot
from PySide6.QtGui import QUndoStack
from spinedb_api import DatabaseMapping
from spinedb_api.parameter_value import load_db_value
from spinedb_api.temp_id import TempId
from ...fetch_parent import FlexibleFetchParent
from ...helpers import DB_ITEM_SEPARATOR, DBMapDictItems, rows_to_row_count_tuples
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...mvcmodels.shared import DB_MAP_ROLE, PARSED_ROLE
from ...spine_db_manager import SpineDBManager
from ..commands import AppendEmptyRow, InsertEmptyModelRow, RemoveEmptyModelRow, UpdateEmptyModel
from .single_and_empty_model_mixins import SplitValueAndTypeMixin
from .utils import (
    ENTITY_ALTERNATIVE_MODEL_HEADER,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_DEFINITION_MODEL_HEADER,
    PARAMETER_VALUE_FIELD_MAP,
    PARAMETER_VALUE_MODEL_HEADER,
    make_entity_on_the_fly,
)


class EmptyModelBase(EmptyRowModel):
    """Base class for all empty models that add new items to the database."""

    item_type: ClassVar[str] = NotImplemented
    can_be_filtered: ClassVar[bool] = False
    field_map: ClassVar[dict[str, str]] = {}
    group_fields: ClassVar[Iterable[str]] = ()

    def __init__(self, header: list[str], db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(parent, header)
        self.db_mngr = db_mngr
        self._undo_stack: Optional[QUndoStack] = None
        self._entity_class_column = header.index("entity_class_name")
        self._database_column = header.index("database")
        self.entity_class_id: Optional[TempId] = None
        self._fetch_parent = FlexibleFetchParent(
            self.item_type,
            handle_items_added=self.handle_items_added,
            owner=self,
        )

    def set_undo_stack(self, undo_stack: QUndoStack) -> None:
        self._undo_stack = undo_stack
        self.modelReset.connect(self._clear_undo_stack)

    @Slot()
    def _clear_undo_stack(self):
        self._undo_stack.clear()

    def fetchMore(self, parent):
        self.append_empty_row()
        self._fetched = True

    def add_items_to_db(self, db_map_data: DBMapDictItems) -> None:
        """Adds items to db.

        Args:
            db_map_data: mapping DatabaseMapping instance to list of items
        """
        db_map_items = self._data_to_items(db_map_data)
        if any(db_map_items.values()):
            self.db_mngr.add_items(self.item_type, db_map_items)

    def _data_to_items(self, db_map_data: DBMapDictItems) -> DBMapDictItems:
        db_map_items = {}
        for db_map, items in db_map_data.items():
            for item in items:
                item_to_add = self._convert_to_db(item)
                if self._check_item(item_to_add):
                    db_map_items.setdefault(db_map, []).append(item_to_add)
        return db_map_items

    def _make_unique_id(self, item: dict) -> tuple:
        """Returns a unique id for the given model item (name-based). Used by handle_items_added to identify
        which rows have been added and thus need to be removed."""
        raise NotImplementedError()

    def append_empty_row(self) -> None:
        last = len(self._main_data)
        self.beginInsertRows(QModelIndex(), last, last)
        self._main_data.append([self.default_row.get(self.header[column]) for column in range(len(self.header))])
        self.endInsertRows()

    def remove_empty_row(self) -> None:
        last = len(self._main_data) - 1
        self.beginRemoveRows(QModelIndex(), last, last)
        self._main_data = self._main_data[:-1]
        self.endRemoveRows()

    def remove_rows(self, rows: Iterable[int]) -> None:
        self._undo_stack.beginMacro("remove rows")
        for row in sorted(rows, reverse=True):
            self._undo_stack.push(RemoveEmptyModelRow(self, row))
        self._undo_stack.endMacro()

    def removeRows(self, row, count, parent=QModelIndex()):
        self._undo_stack.beginMacro("remove rows")
        for _ in range(count):
            self._undo_stack.push(RemoveEmptyModelRow(self, row))
        self._undo_stack.endMacro()
        return self._undo_stack.command(self._undo_stack.count() - 1).isObsolete()

    def do_remove_rows(self, row: int, count: int) -> None:
        super().removeRows(row, count)

    def insertRows(self, row, count, parent=QModelIndex()):
        self._undo_stack.beginMacro("insert rows")
        for _ in range(count):
            self._undo_stack.push(InsertEmptyModelRow(self, row))
        self._undo_stack.endMacro()
        return not self._undo_stack.command(self._undo_stack.count() - 1).isObsolete()

    def do_insert_rows(self, row: int, count: int) -> None:
        super().insertRows(row, count)

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
            unique_id = (database, *self._make_unique_id(self._convert_to_db(item)))
            if unique_id in added_ids:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.do_remove_rows(row, count)
        self._undo_stack.clear()

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch. If successful, add items to db."""
        modified_indexes = []
        modified_data = []
        data_by_row = defaultdict(dict)
        for index, cell_data in zip(indexes, data):
            if index.data() == cell_data:
                continue
            modified_indexes.append(index)
            modified_data.append(cell_data)
            data_by_row[index.row()][index.column()] = cell_data
        db_map_cache = _TempDBMapCache(self.db_mngr)
        for row, row_data in data_by_row.items():
            main_data_row = self._main_data[row]
            if (self._paste and self._entity_class_column in row_data) or main_data_row[self._entity_class_column]:
                continue
            combined_row = [row_data.get(column, main_data_row[column]) for column in range(len(main_data_row))]
            db_name = combined_row[self._database_column]
            db_map = db_map_cache.get(db_name)
            if db_map is None:
                continue
            candidates = self._entity_class_name_candidates(db_map, combined_row)
            if len(candidates) == 1:
                modified_indexes.append(self.index(row, self._entity_class_column))
                modified_data.extend(candidates)
        if not modified_indexes:
            return False
        command = UpdateEmptyModel(self, modified_indexes, modified_data)
        self._undo_stack.beginMacro(f"update unfinished {self.item_type}")
        self._undo_stack.push(command)
        self._undo_stack.endMacro()
        return not command.isObsolete()

    def do_batch_set_data(self, indexes: Iterable[QModelIndex], data: Iterable) -> bool:
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row() for ind in indexes}
        db_map_data = self._make_db_map_data(rows)
        self.add_items_to_db(db_map_data)
        return True

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_data_changed(self, top_left, bottom_right, roles=None):
        """Inserts a new last empty row in case the previous one has been filled
        with any data other than the defaults."""
        if roles and Qt.ItemDataRole.EditRole not in roles:
            return
        last_row = self._main_data[-1]
        for column, data in enumerate(last_row):
            try:
                field = self.header[column]
            except IndexError:
                field = None
            default = self.default_row.get(field)
            if (data or default) and data != default:
                self._undo_stack.push(AppendEmptyRow(self))
                break

    def _entity_class_name_candidates(self, db_map: DatabaseMapping, item: list) -> list[str]:
        raise NotImplementedError()

    def _make_item(self, row: int) -> dict:
        return dict(zip(self.header, self._main_data[row]))

    def _make_db_map_data(self, rows: Iterable[int]) -> DBMapDictItems:
        """
        Returns model data grouped by database map.

        Args:
            rows: group data from these rows

        Returns:
            mapping DatabaseMapping instance to list of items
        """
        db_map_data = {}
        db_map_cache = _TempDBMapCache(self.db_mngr)
        for row in rows:
            item = self._make_item(row)
            database = item.pop("database")
            db_map = db_map_cache.get(database)
            if db_map is None:
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
        if (role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.ToolTipRole) and self.header[
            index.column()
        ] in self.group_fields:
            data = super().data(index, role)
            return DB_ITEM_SEPARATOR.join(data) if data else None
        return super().data(index, role)

    def _convert_to_db(self, item: dict) -> dict:
        """Returns a db item (id-based) from the given model item (name-based)."""
        return item.copy()

    @staticmethod
    def _check_item(item: dict) -> bool:
        """Checks if a db item is ready to be inserted."""
        raise NotImplementedError()

    def set_default_row(self, **kwargs) -> None:
        """Sets default row data."""
        if self.default_row != kwargs:
            super().set_default_row(**kwargs)
            self._undo_stack.clear()

    def reset_db_maps(self, db_maps: Iterable[DatabaseMapping]):
        self._fetch_parent.set_obsolete(False)
        self._fetch_parent.reset()
        for db_map in db_maps:
            self.db_mngr.register_fetch_parent(db_map, self._fetch_parent)


class _TempDBMapCache:
    def __init__(self, db_mngr: SpineDBManager):
        self._db_mngr = db_mngr
        self._db_maps: dict[str, DatabaseMapping] = {}

    def get(self, name: str) -> Optional[DatabaseMapping]:
        try:
            return self._db_maps[name]
        except KeyError:
            try:
                db_map = next(
                    iter(x for x in self._db_mngr.db_maps if self._db_mngr.name_registry.display_name(x.sa_url) == name)
                )
            except StopIteration:
                return None
        self._db_maps[name] = db_map
        return db_map


class ParameterMixin:
    value_field: ClassVar[str] = NotImplemented
    type_field: ClassVar[str] = NotImplemented
    parameter_name_column: ClassVar[int] = NotImplemented
    index_name_fields: ClassVar[tuple[str, ...]] = NotImplemented

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

    @classmethod
    def _entity_class_name_candidates_by_parameter(cls, db_map: DatabaseMapping, row_data: list) -> list[str]:
        name = row_data[cls.parameter_name_column]
        if not name:
            return []
        return [x["entity_class_name"] for x in db_map.get_items("parameter_definition", name=name)]

    def index_name(self, index: QModelIndex) -> str:
        """Generates a name for data at given index.

        Args:
            index to model

        Returns:
            label identifying the data
        """
        row_data = self._main_data[index.row()]
        names = []
        for index_field in self.index_name_fields:
            column = self.header.index(index_field)
            data = row_data[column]
            names.append(data if data is not None else f"<{index_field}>")
        return " - ".join(names)

    def get_set_data_delayed(self, index: QModelIndex) -> Callable[[tuple[bytes, Optional[str]]], None]:
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.
        """
        return DelayedDataSetter(self, index)


class DelayedDataSetter:
    def __init__(self, model: MinimalTableModel, index: QModelIndex):
        self._model = model
        self._row = index.row()
        self._column = index.column()
        self._model.rowsInserted.connect(self._rows_inserted)
        self._model.rowsRemoved.connect(self._rows_removed)
        self._model.modelReset.connect(self._invalidate)
        self._valid = True

    def __call__(self, value_and_type: tuple[bytes, Optional[str]]) -> None:
        self._model.rowsInserted.disconnect(self._rows_inserted)
        self._model.rowsRemoved.disconnect(self._rows_removed)
        self._model.modelReset.disconnect(self._invalidate)
        if not self._valid:
            return
        index = self._model.index(self._row, self._column)
        self._model.batch_set_data([index], [load_db_value(*value_and_type)])

    def _rows_inserted(self, _: QModelIndex, first: int, last: int) -> None:
        if first > self._row:
            return
        self._row += last - first + 1

    def _rows_removed(self, _: QModelIndex, first: int, last: int) -> None:
        if first > self._row:
            return
        if first <= self._row <= last:
            self._valid = False
            return
        self._row -= last - first + 1

    def _invalidate(self) -> None:
        self._valid = False


class EntityMixin:
    group_fields = ("entity_byname",)
    entities_added = Signal(object)
    entity_byname_column: ClassVar[int] = NotImplemented

    def add_items_to_db(self, db_map_data):
        """Overridden to add entities on the fly first."""
        db_map_entities = {}
        db_map_error_log = {}
        for db_map, items in db_map_data.items():
            for item in items:
                item_to_add = self._convert_to_db(item)
                entity, errors = make_entity_on_the_fly(item_to_add, db_map)
                if entity:
                    entities = db_map_entities.setdefault(db_map, [])
                    if entity not in entities:
                        entities.append(entity)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)
        db_map_items = self._data_to_items(db_map_data)
        if any(db_map_items.values()):
            db_map_entities_to_add = self._clean_to_be_added_entities(db_map_entities, db_map_items)
            if any(db_map_entities_to_add.values()):
                self.db_mngr.add_items("entity", db_map_entities_to_add)
                self.entities_added.emit(db_map_entities_to_add)
            self.db_mngr.add_items(self.item_type, db_map_items)

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

    @classmethod
    def _entity_class_name_candidates_by_entity(cls, db_map: DatabaseMapping, row_data: list) -> list[str]:
        byname = row_data[cls.entity_byname_column]
        if not byname:
            return []
        return [x["entity_class_name"] for x in db_map.find_entities(entity_byname=byname)]


class EmptyParameterDefinitionModel(SplitValueAndTypeMixin, ParameterMixin, EmptyModelBase):
    """An empty parameter_definition model."""

    item_type = "parameter_definition"
    field_map = PARAMETER_DEFINITION_FIELD_MAP
    value_field = "default_value"
    type_field = "default_type"
    parameter_name_column = PARAMETER_DEFINITION_MODEL_HEADER.index("parameter_name")
    index_name_fields = ("database", "entity_class_name", "parameter_name")
    group_fields = ("valid types",)

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(PARAMETER_DEFINITION_MODEL_HEADER, db_mngr, parent)

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "name"))

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return item.get("entity_class_name") and item.get("name")

    def _entity_class_name_candidates(self, db_map, row_data):
        return self._entity_class_name_candidates_by_parameter(db_map, row_data)


class EmptyParameterValueModel(SplitValueAndTypeMixin, ParameterMixin, EntityMixin, EmptyModelBase):
    """A self-contained empty parameter_value model."""

    item_type = "parameter_value"
    field_map = PARAMETER_VALUE_FIELD_MAP
    index_name_fields: ClassVar[tuple[str, ...]] = (
        "database",
        "entity_class",
    )
    value_field = "value"
    type_field = "type"
    entity_byname_column = PARAMETER_VALUE_MODEL_HEADER.index("entity_byname")
    parameter_name_column = PARAMETER_VALUE_MODEL_HEADER.index("parameter_name")
    index_name_fields = ("database", "entity_class_name", "entity_byname", "parameter_name", "alternative_name")

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

    def _entity_class_name_candidates(self, db_map, row_data):
        candidates_by_parameter = self._entity_class_name_candidates_by_parameter(db_map, row_data)
        candidates_by_entity = self._entity_class_name_candidates_by_entity(db_map, row_data)
        if not candidates_by_parameter:
            return candidates_by_entity
        if not candidates_by_entity:
            return candidates_by_parameter
        return list(set(candidates_by_parameter) & set(candidates_by_entity))


class EmptyEntityAlternativeModel(EntityMixin, EmptyModelBase):
    item_type = "entity_alternative"
    entity_byname_column = ENTITY_ALTERNATIVE_MODEL_HEADER.index("entity_byname")

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject]):
        super().__init__(ENTITY_ALTERNATIVE_MODEL_HEADER, db_mngr, parent)

    @staticmethod
    def _check_item(item):
        """Checks if a db item is ready to be inserted."""
        return all(key in item for key in ("entity_class_name", "entity_byname", "alternative_name", "active"))

    def _make_unique_id(self, item):
        return tuple(item.get(x) for x in ("entity_class_name", "entity_byname", "alternative_name"))

    def _entity_class_name_candidates(self, db_map, row_data):
        return self._entity_class_name_candidates_by_entity(db_map, row_data)


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
