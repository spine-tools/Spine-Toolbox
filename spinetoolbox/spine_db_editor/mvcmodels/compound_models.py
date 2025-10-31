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

"""Compound models. These models concatenate several 'single' models and one 'empty' model."""
from __future__ import annotations
import bisect
from collections.abc import Callable, Iterable, Iterator, Sequence
from functools import cache
from typing import TYPE_CHECKING, ClassVar, Type
from PySide6.QtCore import QModelIndex, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont
from spinedb_api import DatabaseMapping
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.parameter_value import join_value_and_type
from spinedb_api.temp_id import TempId
from ...fetch_parent import FlexibleFetchParent
from ...helpers import DBMapPublicItems, parameter_identifier, rows_to_row_count_tuples
from ...mvcmodels.shared import ITEM_ID_ROLE
from ...spine_db_manager import SpineDBManager
from ..widgets.custom_menus import AutoFilterMenu
from .compound_table_model import CompoundTableModel
from .single_models import (
    SingleEntityAlternativeModel,
    SingleEntityModel,
    SingleModelBase,
    SingleParameterDefinitionModel,
    SingleParameterValueModel,
)
from .utils import (
    ENTITY_ALTERNATIVE_FIELD_MAP,
    ENTITY_FIELD_MAP,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_VALUE_FIELD_MAP,
)

if TYPE_CHECKING:
    from ..widgets.spine_db_editor import SpineDBEditor


class CompoundStackedModel(CompoundTableModel):
    """A base model for all models that show data in stacked format."""

    item_type: ClassVar[str] = NotImplemented
    field_map: ClassVar[dict[str, str]] = {}

    non_committed_items_about_to_be_added = Signal()
    non_committed_items_added = Signal()

    def __init__(self, parent: SpineDBEditor, db_mngr: SpineDBManager, *db_maps):
        """
        Args:
            parent: the parent object
            db_mngr: the database manager
            *db_maps: the database maps included in the model
        """
        super().__init__(parent=parent, header=self._make_header())
        self._parent = parent
        self.db_mngr = db_mngr
        self._db_maps: list[DatabaseMapping] = list(db_maps)
        self._filter_class_ids: dict[DatabaseMapping, set[TempId]] = {}
        self._auto_filter_menus: dict[str, AutoFilterMenu] = {}
        self._auto_filter: dict[str, dict[tuple[DatabaseMapping, TempId], set]] = {}
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(100)
        self._filter_timer.timeout.connect(self.refresh)
        self._fetch_parent = FlexibleFetchParent(
            self.item_type,
            shows_item=self.shows_item,
            handle_items_added=self.handle_items_added,
            handle_items_removed=self.handle_items_removed,
            handle_items_updated=self.handle_items_updated,
            owner=self,
        )
        for db_map in self._db_maps:
            self.db_mngr.register_fetch_parent(db_map, self._fetch_parent)
        self._column_filters = {self.header[column]: False for column in range(self.columnCount())}

    @classmethod
    @cache
    def field_to_header(cls, field: str) -> str:
        return dict(zip(cls.field_map.values(), cls.field_map.keys()))[field]

    @classmethod
    def _make_header(cls) -> list[str]:
        return list(cls.field_map)

    @property
    def column_filters(self) -> dict[str, bool]:
        return self._column_filters

    @property
    def group_columns(self) -> set[int]:
        return self._single_model_type.group_columns

    @property
    def _single_model_type(self) -> Type[SingleModelBase]:
        """Returns a constructor for the single models."""
        raise NotImplementedError()

    def canFetchMore(self, _parent):
        return bool(self._db_maps) and not self._fetch_parent.is_fetched

    def fetchMore(self, _parent):
        for db_map in self._db_maps:
            self.db_mngr.fetch_more(db_map, self._fetch_parent)

    def shows_item(self, item: PublicItem, db_map: DatabaseMapping) -> bool:
        return any(m.db_map == db_map and m.filter_accepts_item(item) for m in self.accepted_single_models())

    def reset_db_maps(self, db_maps: Sequence[DatabaseMapping]) -> None:
        if set(db_maps) == set(self._db_maps):
            return
        self._fetch_parent.set_obsolete(False)
        self._fetch_parent.reset()
        for old_db_map in self._db_maps:
            if old_db_map not in db_maps:
                self.db_mngr.unregister_fetch_parent(old_db_map, self._fetch_parent)
        for new_db_map in db_maps:
            if new_db_map not in self._db_maps:
                self.db_mngr.register_fetch_parent(new_db_map, self._fetch_parent)
        self._db_maps = db_maps

    def _connect_single_model(self, model: SingleModelBase) -> None:
        """Connects signals so changes in the submodels are acknowledged by the compound."""
        model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))
        model.modelAboutToBeReset.connect(lambda model=model: self._handle_single_model_about_to_be_reset(model))
        model.dataChanged.connect(
            lambda top_left, bottom_right, roles, model=model: self._handle_single_model_data_changed(
                top_left, bottom_right, roles, model
            )
        )

    def _handle_single_model_data_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: list[Qt.ItemDataRole] | None,
        model: SingleModelBase,
    ) -> None:
        top_left = self.map_from_sub(model, top_left)
        bottom_right = self.map_from_sub(model, bottom_right)
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(top_left, bottom_right, roles)

    def _handle_single_model_about_to_be_reset(self, model: SingleModelBase) -> None:
        """Runs when given model is about to reset."""
        if model not in self.sub_models:
            return
        row_map = self._row_map_for_model(model)
        if not row_map:
            return
        removed_rows = []
        for mapped_row in row_map:
            try:
                removed_rows.append(self._inv_row_map[mapped_row])
            except KeyError:
                pass
        for first, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            last = first + count - 1
            tail_row_map = self._row_map[last + 1 :]
            self.beginRemoveRows(QModelIndex(), first, last)
            for key in self._row_map[first:]:
                del self._inv_row_map[key]
            del self._row_map[first:]
            self._append_row_map(tail_row_map)
            self.endRemoveRows()

    def _handle_single_model_reset(self, model: SingleModelBase) -> None:
        """Runs when given model is reset."""
        if model in self.sub_models:
            self._refresh_single_model(model)
        else:
            self._insert_single_model(model)

    def _refresh_single_model(self, model: SingleModelBase) -> None:
        single_row_map = self._row_map_for_model(model)
        pos = self.sub_models.index(model) + 1
        self._insert_row_map(pos, single_row_map)

    def init_model(self) -> None:
        """Initializes the model."""
        if self._row_map:
            self.beginResetModel()
            self._row_map.clear()
            self.endResetModel()
        for m in self.sub_models:
            m.deleteLater()
        self.sub_models.clear()
        self._inv_row_map.clear()
        self._filter_class_ids = {}
        self._auto_filter = {}
        while self._auto_filter_menus:
            _, menu = self._auto_filter_menus.popitem()
            menu.deleteLater()

    def get_auto_filter_menu(self, logical_index: int) -> AutoFilterMenu:
        """Returns auto filter menu for given logical index from header view."""
        return self._make_auto_filter_menu(self.header[logical_index])

    def _make_auto_filter_menu(self, field: str) -> AutoFilterMenu:
        field = self.field_map.get(field, field)
        if field not in self._auto_filter_menus:
            self._auto_filter_menus[field] = menu = AutoFilterMenu(
                self._parent, self.db_mngr, self._db_maps, self.item_type, field, show_empty=False
            )
            menu.filterChanged.connect(self.set_auto_filter)
        return self._auto_filter_menus[field]

    def headerData(self, section, orientation=Qt.Orientation.Horizontal, role=Qt.ItemDataRole.DisplayRole):
        """Returns an italic font in case the given column has an autofilter installed."""
        field = self.header[section]
        real_field = self.field_map.get(field, field)
        italic_font = QFont()
        italic_font.setItalic(True)
        if (
            role == Qt.ItemDataRole.FontRole
            and orientation == Qt.Orientation.Horizontal
            and self._auto_filter.get(real_field)
        ):
            return italic_font
        return super().headerData(section, orientation, role)

    def filter_accepts_model(self, model: SingleModelBase) -> bool:
        """Returns a boolean indicating whether the given model passes the filter for compound model."""
        if not self._auto_filter_accepts_model(model):
            return False
        if not self._class_filter_accepts_model(model):
            return False
        return True

    def _class_filter_accepts_model(self, model: SingleModelBase) -> bool:
        if not self._filter_class_ids:
            return True
        class_ids = self._filter_class_ids.get(model.db_map, set())
        return model.entity_class_id in class_ids or not class_ids.isdisjoint(model.dimension_id_list)

    def _auto_filter_accepts_model(self, model: SingleModelBase) -> bool:
        if None in self._auto_filter.values():
            return False
        for values in self._auto_filter.values():
            if not values:
                continue
            for db_map, entity_class_id in values:
                if model.db_map == db_map and (entity_class_id is None or model.entity_class_id == entity_class_id):
                    break
            else:
                return False
        return True

    def accepted_single_models(self) -> list[SingleModelBase]:
        """Returns a list of accepted single models by calling filter_accepts_model
        on each of them, just for convenience.
        """
        return [m for m in self.sub_models if self.filter_accepts_model(m)]

    def _invalidate_filter(self) -> None:
        """Sets the filter invalid."""
        self._filter_timer.start()

    def stop_invalidating_filter(self) -> None:
        """Stops invalidating the filter."""
        self._filter_timer.stop()

    def set_filter_class_ids(self, class_ids: dict[DatabaseMapping, set[TempId]]) -> None:
        if class_ids != self._filter_class_ids:
            self._filter_class_ids = class_ids
            self._invalidate_filter()

    def clear_auto_filter(self) -> None:
        self._auto_filter = {}
        self._invalidate_filter()

    @Slot(str, object)
    def set_auto_filter(self, field: str, values: dict[tuple[DatabaseMapping, TempId], set]):
        """Updates and applies the auto filter.

        Args:
            field : the field name
            values: mapping (db_map, entity_class_id) to set of valid values
        """
        self._set_compound_auto_filter(field, values)
        for model in self.accepted_single_models():
            self._set_single_auto_filter(model, field)
        if values is None or any(bool(i) for i in values.values()):
            self._column_filters[field] = True
        else:
            self._column_filters[field] = False
        self._parent.handle_column_filters(self)

    def _set_compound_auto_filter(self, field: str, values: dict[tuple[DatabaseMapping, TempId], set]) -> None:
        """Sets the auto filter for given column in the compound model.

        Args:
            field: the field name
            values: mapping from (db map, id) to a set of valid values
        """
        if self._auto_filter.setdefault(field, {}) == values:
            return
        self._auto_filter[field] = values
        self._invalidate_filter()

    def _set_single_auto_filter(self, model: SingleModelBase, field: str) -> None:
        """Sets the auto filter for given column in the given single model.

        Args:
            model: the model
            field: the field name
        """
        values = self._auto_filter[field].get((model.db_map, model.entity_class_id), set())
        if model.set_auto_filter(field, values):
            self._invalidate_filter()

    def _row_map_iterator_for_model(self, model: SingleModelBase) -> Iterator[tuple[SingleModelBase, int]]:
        """Yields row map for the given model.
        Reimplemented to take filter status into account.

        Args:
            model: single model

        Yields:
            (model, row number) for each accepted row
        """
        if not self.filter_accepts_model(model):
            return
        for i in model.accepted_rows():
            yield (model, i)

    def _models_with_db_map(self, db_map: DatabaseMapping) -> list[SingleModelBase]:
        """Returns a collection of single models with given db_map."""
        return [m for m in self.sub_models if m.db_map == db_map]

    @staticmethod
    def _items_per_class(items: Iterable[PublicItem]) -> dict[TempId, list[PublicItem]]:
        """Returns a dict mapping entity_class ids to a set of items."""
        d = {}
        for item in items:
            entity_class_id = item["entity_class_id"]
            d.setdefault(entity_class_id, []).append(item)
        return d

    def handle_items_added(self, db_map_data: DBMapPublicItems) -> None:
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model, so it can remove rows that are already in.

        Args:
            db_map_data: list of added items keyed by DatabaseMapping
        """
        for db_map, items in db_map_data.items():
            if db_map not in self._db_maps:
                continue
            db_map_single_models = [m for m in self.sub_models if m.db_map is db_map]
            existing_ids = set().union(*(m.item_ids() for m in db_map_single_models))
            items_per_class = self._items_per_class(items)
            for entity_class_id, class_items in items_per_class.items():
                ids_committed = []
                ids_uncommitted = []
                for item in class_items:
                    item_id = item["id"]
                    if item_id in existing_ids:
                        existing_ids.remove(item_id)
                        continue
                    if item.is_committed():
                        ids_committed.append(item_id)
                    else:
                        ids_uncommitted.append(item_id)
                if ids_committed:
                    self._add_items(db_map, entity_class_id, ids_committed, committed=True)
                if ids_uncommitted:
                    self.non_committed_items_about_to_be_added.emit()
                    self._add_items(db_map, entity_class_id, ids_uncommitted, committed=False)
                    self.non_committed_items_added.emit()

    def _get_insert_position(self, model: SingleModelBase) -> int:
        if model.committed:
            return bisect.bisect_left(self.sub_models, model)
        return len(self.sub_models)

    def _create_single_model(
        self, db_map: DatabaseMapping, entity_class_id: TempId, committed: bool
    ) -> SingleModelBase:
        model = self._single_model_type(self, db_map, entity_class_id, committed)
        self._connect_single_model(model)
        for field in self._auto_filter:
            self._set_single_auto_filter(model, field)
        return model

    def _insert_single_model(self, model: SingleModelBase) -> None:
        single_row_map = self._row_map_for_model(model)
        pos = self._get_insert_position(model)
        self._insert_row_map(pos, single_row_map)
        self.sub_models.insert(pos, model)

    def _get_row_for_insertion(self, pos: int) -> int:
        for model in self.sub_models[pos:]:
            first_row_map_item = next(self._row_map_iterator_for_model(model), None)
            if first_row_map_item is not None:
                try:
                    return self._inv_row_map[first_row_map_item]
                except KeyError:
                    # Sometimes the submodel is not yet in the inverted row map.
                    # In this case we just skip it and try another insertion point.
                    pass
        return self.rowCount()

    def _insert_row_map(self, pos: int, single_row_map: list[tuple[SingleModelBase, int]]) -> None:
        if not single_row_map:
            # Emit layoutChanged to trigger fetching.
            print("Layout changed!")
            self.layoutChanged.emit()
            return
        row = self._get_row_for_insertion(pos)
        last = row + len(single_row_map) - 1
        self.beginInsertRows(QModelIndex(), row, last)
        self._row_map, tail_row_map = self._row_map[:row], self._row_map[row:]
        self._append_row_map(single_row_map)
        self._append_row_map(tail_row_map)
        self.endInsertRows()

    def remove_rows(self, rows: Iterable[int]) -> None:
        """Removes given rows by removing the corresponding items from the db map."""
        db_map_typed_data = {}
        for row in sorted(rows, reverse=True):
            sub_model = self.sub_model_at_row(row)
            db_map = sub_model.db_map
            id_ = self.item_at_row(row)
            db_map_typed_data.setdefault(db_map, {}).setdefault(self.item_type, []).append(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def _add_items(self, db_map: DatabaseMapping, entity_class_id: TempId, ids: list[TempId], committed: bool) -> None:
        """Creates new single model and resets it with the given parameter ids.

        Args:
            db_map: database map
            entity_class_id: parameter's entity class id
            ids: parameter ids
            committed: True if the ids have been committed, False otherwise
        """
        if committed:
            existing = next(
                (m for m in self.sub_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
            )
            if existing is not None:
                existing.add_rows(ids)
                return
        model = self._create_single_model(db_map, entity_class_id, committed)
        model.reset_model(ids)

    def handle_items_updated(self, db_map_data: DBMapPublicItems) -> None:
        """Runs when either parameter definitions or values are updated in the dbs.
        Emits dataChanged so the parameter_name column is refreshed.

        Args:
            db_map_data: list of updated dict-items keyed by DatabaseMapping
        """
        if all(db_map not in self._db_maps for db_map in db_map_data):
            return
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.ItemDataRole.DisplayRole]
        )

    def handle_items_removed(self, db_map_data: DBMapPublicItems) -> None:
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data: list of removed dict-items keyed by DatabaseMapping
        """
        for db_map, items in db_map_data.items():
            if db_map not in self._db_maps:
                continue
            items_per_class = self._items_per_class(items)
            emptied_single_model_indexes = []
            for model_index, model in enumerate(self.sub_models):
                if model.db_map != db_map:
                    continue
                removed_ids = {x["id"] for x in items_per_class.get(model.entity_class_id, {})}
                if not removed_ids:
                    continue
                removed_invisible_rows = set()
                removed_visible_rows = []
                for row in range(model.rowCount()):
                    id_ = model._main_data[row]
                    if id_ in removed_ids:
                        removed_ids.remove(id_)
                        if (model, row) in self._inv_row_map:
                            removed_visible_rows.append(row)
                        else:
                            removed_invisible_rows.add(row)
                removed_compound_rows = [self._inv_row_map[(model, row)] for row in removed_visible_rows]
                if removed_invisible_rows:
                    new_kept_rows = self._delete_rows_from_single_model(model, removed_invisible_rows)
                    self._update_single_model_rows_in_row_map(model, new_kept_rows)
                for first_compound_row, count in sorted(rows_to_row_count_tuples(removed_compound_rows), reverse=True):
                    self.beginRemoveRows(QModelIndex(), first_compound_row, first_compound_row + count - 1)
                    removed_model_rows = {
                        self._row_map[r][1] for r in range(first_compound_row, first_compound_row + count)
                    }
                    new_kept_rows = self._delete_rows_from_single_model(model, removed_model_rows)
                    for row in removed_model_rows:
                        del self._inv_row_map[(model, row)]
                    self._update_single_model_rows_in_row_map(model, new_kept_rows)
                    del self._row_map[first_compound_row : first_compound_row + count]
                    for row, mapped_row in enumerate(self._row_map[first_compound_row:]):
                        self._inv_row_map[mapped_row] = row + first_compound_row
                    self.endRemoveRows()
                if model.rowCount() == 0:
                    emptied_single_model_indexes.append(model_index)
            for model_index in reversed(emptied_single_model_indexes):
                model = self.sub_models.pop(model_index)
                model.deleteLater()

    def _delete_rows_from_single_model(self, model: SingleModelBase, rows_to_remove: Iterable[int]) -> dict[int, int]:
        """Removes rows from given single model and computes a map from original rows to retained rows.

        Args:
            model: single model to delete data from
            rows_to_remove: row index that should be removed

        Returns:
            dict: mapping from original row index to post-removal row index
        """
        new_kept_rows = {}
        sorted_deleted_rows = []
        for row in range(model.rowCount()):
            if row in rows_to_remove:
                sorted_deleted_rows.append(row)
            else:
                new_kept_rows[row] = row - len(sorted_deleted_rows)
        for row in reversed(sorted_deleted_rows):
            del model._main_data[row]
        return new_kept_rows

    def _update_single_model_rows_in_row_map(self, model: SingleModelBase, new_rows: dict[int, int]) -> None:
        """Rewrites single model rows in row map.

        Args:
            model: single model whose rows to update
            new_rows: mapping from old row index to updated index
        """
        new_inv_row_map = {}
        for row, new_row in new_rows.items():
            try:
                compound_row = self._inv_row_map.pop((model, row))
            except KeyError:
                continue
            self._row_map[compound_row] = (model, new_row)
            new_inv_row_map[(model, new_row)] = compound_row
        for mapped_row, compound_row in new_inv_row_map.items():
            self._inv_row_map[mapped_row] = compound_row

    def db_item(self, index: QModelIndex) -> PublicItem:
        sub_index = self.map_to_sub(index)
        return sub_index.model().db_item(sub_index)

    def db_map_id(self, index: QModelIndex) -> tuple[DatabaseMapping, TempId] | tuple[None, None]:
        sub_index = self.map_to_sub(index)
        sub_model = sub_index.model()
        if sub_model is None:
            return None, None
        return sub_model.db_map, sub_model.item_id(sub_index.row())

    def filter_by(self, rows_per_column: dict[int, list[int]]) -> None:
        for column, rows in rows_per_column.items():
            field = self.headerData(column)
            menu = self._make_auto_filter_menu(field)
            accepted_values = {self.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in rows}
            menu.set_filter_accepted_values(accepted_values)

    def filter_excluding(self, rows_per_column: dict[int, list[int]]) -> None:
        for column, rows in rows_per_column.items():
            field = self.headerData(column)
            menu = self._make_auto_filter_menu(field)
            rejected_values = {self.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in rows}
            menu.set_filter_rejected_values(rejected_values)


class FilterEntityAlternativeMixin:
    """Provides the interface to filter by entity and alternative."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}

    def init_model(self):
        super().init_model()
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}

    def set_filter_entity_ids(self, entity_ids: dict[DatabaseMapping, set[TempId]]) -> None:
        self._filter_entity_ids = entity_ids
        for model in self.sub_models:
            if model.set_filter_entity_ids(entity_ids):
                self._invalidate_filter()

    def set_filter_alternative_ids(self, alternative_ids: dict[DatabaseMapping, set[TempId]]) -> None:
        self._filter_alternative_ids = alternative_ids
        for model in self.sub_models:
            if model.set_filter_alternative_ids(alternative_ids):
                self._invalidate_filter()

    def _create_single_model(
        self, db_map: DatabaseMapping, entity_class_id: TempId, committed: bool
    ) -> SingleModelBase:
        model = super()._create_single_model(db_map, entity_class_id, committed)
        model.set_filter_entity_ids(self._filter_entity_ids)
        model.set_filter_alternative_ids(self._filter_alternative_ids)
        return model


class EditParameterValueMixin:
    """Provides the interface to edit values via ParameterValueEditor."""

    def handle_items_updated(self, db_map_data):
        changed_rows = []
        for db_map, items in db_map_data.items():
            if db_map not in self._db_maps:
                continue
            items_by_class = self._items_per_class(items)
            for entity_class_id, class_items in items_by_class.items():
                single_model = next(
                    (m for m in self.sub_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
                )
                if single_model is not None:
                    single_model.revalidate_item_types(class_items)
                    ids = {item["id"] for item in class_items}
                    changed_rows = []
                    for single_row in range(single_model.rowCount()):
                        key = (single_model, single_row)
                        if (
                            key in self._inv_row_map
                            and (item_id := single_model.index(single_row, 0).data(ITEM_ID_ROLE)) in ids
                        ):
                            changed_rows.append(self._inv_row_map[key])
                            ids.remove(item_id)
        if changed_rows:
            column_count = self.columnCount()
            for first_row, count in rows_to_row_count_tuples(changed_rows):
                top_left = self.index(first_row, 0)
                bottom_right = self.index(first_row + count - 1, column_count - 1)
                self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def index_name(self, index: QModelIndex) -> str:
        """Generates a name for data at given index.

        Args:
            index to model

        Returns:
            label identifying the data
        """
        item = self.db_item(index)
        if item is None:
            return ""
        database = self.index(index.row(), self.columnCount() - 1).data()
        entity_class_name = item["entity_class_name"]
        if self.item_type == "parameter_definition":
            parameter_name = item["name"]
            entity_byame = None
            alternative_name = None
        elif self.item_type == "parameter_value":
            parameter_name = item["parameter_name"]
            entity_byame = list(item["entity_byname"])
            alternative_name = item["alternative_name"]
        else:
            raise ValueError(
                f"invalid item_type: expected parameter_definition or parameter_value, got {self.item_type}"
            )
        return parameter_identifier(database, entity_class_name, entity_byame, parameter_name, alternative_name)

    def get_set_data_delayed(self, index: QModelIndex) -> Callable[tuple[bytes, str], None]:
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.
        """
        sub_model = self.sub_model_at_row(index.row())
        id_ = self.item_at_row(index.row())
        return lambda value_and_type, sub_model=sub_model, id_=id_: sub_model.update_items_in_db(
            [{"id": id_, sub_model.value_field: join_value_and_type(*value_and_type)}]
        )


class CompoundParameterDefinitionModel(EditParameterValueMixin, CompoundStackedModel):
    """A model that concatenates several single parameter_definition models and one empty parameter_definition model."""

    item_type = "parameter_definition"
    field_map = PARAMETER_DEFINITION_FIELD_MAP

    @property
    def _single_model_type(self):
        return SingleParameterDefinitionModel


class CompoundParameterValueModel(FilterEntityAlternativeMixin, EditParameterValueMixin, CompoundStackedModel):
    """A model that concatenates several single parameter_value models and one empty parameter_value model."""

    item_type = "parameter_value"
    field_map = PARAMETER_VALUE_FIELD_MAP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mngr.items_updated.connect(self._handle_parameter_definitions_updated)

    @property
    def _single_model_type(self):
        return SingleParameterValueModel

    def _handle_parameter_definitions_updated(
        self, item_type: str, db_map_data: dict[DatabaseMapping, list[PublicItem]]
    ) -> None:
        if item_type != "parameter_definition":
            return
        for db_map, definition_items in db_map_data.items():
            if db_map not in self._db_maps:
                continue
            value_table = db_map.mapped_table("parameter_value")
            for sub_model in self.sub_models:
                if sub_model.db_map is not db_map:
                    continue
                value_items = {}
                validatable_value_items = []
                for sub_row in sub_model.accepted_rows():
                    value_item = value_table[sub_model.item_id(sub_row)]
                    value_items[(value_item["entity_class_id"], value_item["parameter_definition_id"])] = value_item
                leftover_definition_items = []
                for definition_item in definition_items:
                    key = (definition_item["entity_class_id"], definition_item["id"])
                    if key not in value_items:
                        leftover_definition_items.append(definition_item)
                        continue
                    validatable_value_items.append(value_items[key])
                sub_model.revalidate_item_types(validatable_value_items)
                if not leftover_definition_items:
                    break
                definition_items = leftover_definition_items


class CompoundEntityAlternativeModel(FilterEntityAlternativeMixin, CompoundStackedModel):

    item_type = "entity_alternative"
    field_map = ENTITY_ALTERNATIVE_FIELD_MAP

    @property
    def _single_model_type(self):
        return SingleEntityAlternativeModel


class CompoundEntityModel(FilterEntityAlternativeMixin, CompoundStackedModel):
    item_type = "entity"
    field_map = ENTITY_FIELD_MAP

    @property
    def _single_model_type(self) -> Type[SingleEntityModel]:
        return SingleEntityModel

    @staticmethod
    def _items_per_class(items: Iterable[PublicItem]) -> dict[TempId, list[PublicItem]]:
        """Returns a dict mapping entity_class ids to a set of items."""
        d = {}
        for item in items:
            entity_class_id = item["class_id"]
            d.setdefault(entity_class_id, []).append(item)
        return d
