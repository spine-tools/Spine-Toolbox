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
import bisect
from collections.abc import Iterable
from typing import ClassVar, Type
from PySide6.QtCore import QModelIndex, Qt, QTimer, Slot
from PySide6.QtGui import QFont
from spinedb_api.parameter_value import join_value_and_type
from ...fetch_parent import FlexibleFetchParent
from ...helpers import parameter_identifier, rows_to_row_count_tuples
from ..widgets.custom_menus import AutoFilterMenu
from .compound_table_model import CompoundTableModel
from .single_models import (
    SingleEntityAlternativeModel,
    SingleModelBase,
    SingleParameterDefinitionModel,
    SingleParameterValueModel,
)
from .utils import (
    ENTITY_ALTERNATIVE_MODEL_HEADER,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_DEFINITION_MODEL_HEADER,
    PARAMETER_VALUE_FIELD_MAP,
    PARAMETER_VALUE_MODEL_HEADER,
)


class CompoundStackedModel(CompoundTableModel):
    """A base model for all models that show data in stacked format."""

    item_type: ClassVar[str] = NotImplemented
    field_map: ClassVar[dict[str, str]] = {}

    def __init__(self, parent, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): the parent object
            db_mngr (SpineDBManager): the database manager
            *db_maps (DatabaseMapping): the database maps included in the model
        """
        super().__init__(parent=parent, header=self._make_header())
        self._parent = parent
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._filter_class_ids = {}
        self._auto_filter_menus = {}
        self._auto_filter = {}
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
        self.dock = None
        self._column_filters = {self.header[column]: False for column in range(self.columnCount())}

    @staticmethod
    def _make_header() -> list[str]:
        raise NotImplementedError()

    @property
    def column_filters(self):
        return self._column_filters

    @property
    def group_fields(self) -> Iterable[str]:
        return self._single_model_type.group_fields

    @property
    def _single_model_type(self) -> Type[SingleModelBase]:
        """Returns a constructor for the single models."""
        raise NotImplementedError()

    def canFetchMore(self, _parent):
        result = False
        for db_map in self.db_maps:
            result |= self.db_mngr.can_fetch_more(db_map, self._fetch_parent)
        return result

    def fetchMore(self, _parent):
        for db_map in self.db_maps:
            self.db_mngr.fetch_more(db_map, self._fetch_parent)

    def shows_item(self, item, db_map):
        return any(m.db_map == db_map and m.filter_accepts_item(item) for m in self.accepted_single_models())

    def reset_db_maps(self, db_maps):
        if set(db_maps) == set(self.db_maps):
            return
        self.db_maps = db_maps
        self._fetch_parent.set_obsolete(False)
        self._fetch_parent.reset()

    def _connect_single_model(self, model: SingleModelBase) -> None:
        """Connects signals so changes in the submodels are acknowledged by the compound."""
        model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))
        model.modelAboutToBeReset.connect(lambda model=model: self._handle_single_model_about_to_be_reset(model))
        model.dataChanged.connect(
            lambda top_left, bottom_right, roles, model=model: self.dataChanged.emit(
                self.map_from_sub(model, top_left), self.map_from_sub(model, bottom_right), roles
            )
        )

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

    def get_auto_filter_menu(self, logical_index):
        """Returns auto filter menu for given logical index from header view.

        Args:
            logical_index (int)

        Returns:
            AutoFilterMenu
        """
        return self._make_auto_filter_menu(self.header[logical_index])

    def _make_auto_filter_menu(self, field):
        field = self.field_map.get(field, field)
        if field not in self._auto_filter_menus:
            self._auto_filter_menus[field] = menu = AutoFilterMenu(
                self._parent, self.db_mngr, self.db_maps, self.item_type, field, show_empty=False
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
            and self._auto_filter.get(real_field, {}) != {}
        ):
            return italic_font
        return super().headerData(section, orientation, role)

    def filter_accepts_model(self, model):
        """Returns a boolean indicating whether the given model passes the filter for compound model.

        Args:
            model (SingleModelBase or EmptyModelBase)

        Returns:
            bool
        """
        if not model.can_be_filtered:
            return True
        if not self._auto_filter_accepts_model(model):
            return False
        if not self._class_filter_accepts_model(model):
            return False
        return True

    def _class_filter_accepts_model(self, model):
        if not self._filter_class_ids:
            return True
        class_ids = self._filter_class_ids.get(model.db_map, set())
        return model.entity_class_id in class_ids or bool(set(model.dimension_id_list) & class_ids)

    def _auto_filter_accepts_model(self, model):
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

    def accepted_single_models(self):
        """Returns a list of accepted single models by calling filter_accepts_model
        on each of them, just for convenience.

        Returns:
            list
        """
        return [m for m in self.sub_models if self.filter_accepts_model(m)]

    def _invalidate_filter(self):
        """Sets the filter invalid."""
        self._filter_timer.start()

    def stop_invalidating_filter(self):
        """Stops invalidating the filter."""
        self._filter_timer.stop()

    def set_filter_class_ids(self, class_ids):
        if class_ids != self._filter_class_ids:
            self._filter_class_ids = class_ids
            self._invalidate_filter()

    def clear_auto_filter(self):
        self._auto_filter = {}
        self._invalidate_filter()

    @Slot(str, object)
    def set_auto_filter(self, field, values):
        """Updates and applies the auto filter.

        Args:
            field (str): the field name
            values (dict): mapping (db_map, entity_class_id) to set of valid values
        """
        self._set_compound_auto_filter(field, values)
        for model in self.accepted_single_models():
            self._set_single_auto_filter(model, field)
        if values is None or any(bool(i) for i in values.values()):
            self._column_filters[field] = True
        else:
            self._column_filters[field] = False
        self._parent.handle_column_filters(self)

    def _set_compound_auto_filter(self, field, values):
        """Sets the auto filter for given column in the compound model.

        Args:
            field (str): the field name
            values (set): set of valid (db_map, item_type, id) tuples
        """
        if self._auto_filter.setdefault(field, {}) == values:
            return
        self._auto_filter[field] = values
        self._invalidate_filter()

    def _set_single_auto_filter(self, model, field):
        """Sets the auto filter for given column in the given single model.

        Args:
            model (SingleParameterModel): the model
            field (str): the field name

        Returns:
            bool: True if the auto-filtered values were updated, None otherwise
        """
        values = self._auto_filter[field].get((model.db_map, model.entity_class_id), set())
        if model.set_auto_filter(field, values):
            self._invalidate_filter()

    def _row_map_iterator_for_model(self, model):
        """Yields row map for the given model.
        Reimplemented to take filter status into account.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

        Yields:
            tuple: (model, row number) for each accepted row
        """
        if not self.filter_accepts_model(model):
            return ()
        for i in model.accepted_rows():
            yield (model, i)

    def _models_with_db_map(self, db_map):
        """Returns a collection of single models with given db_map.

        Args:
            db_map (DatabaseMapping)

        Returns:
            list
        """
        return [m for m in self.sub_models if m.db_map == db_map]

    @staticmethod
    def _items_per_class(items):
        """Returns a dict mapping entity_class ids to a set of items.

        Args:
            items (list)

        Returns:
            dict
        """
        d = {}
        for item in items:
            entity_class_id = item.get("entity_class_id")
            if not entity_class_id:
                continue
            d.setdefault(entity_class_id, []).append(item)
        return d

    def handle_items_added(self, db_map_data):
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model, so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of added dict-items keyed by DatabaseMapping
        """
        for db_map, items in db_map_data.items():
            if db_map not in self.db_maps:
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
                        continue
                    if item.is_committed():
                        ids_committed.append(item_id)
                    else:
                        ids_uncommitted.append(item_id)
                self._add_items(db_map, entity_class_id, ids_committed, committed=True)
                self._add_items(db_map, entity_class_id, ids_uncommitted, committed=False)

    def _get_insert_position(self, model):
        if model.committed:
            return bisect.bisect_left(self.sub_models, model)
        return len(self.sub_models)

    def _create_single_model(self, db_map, entity_class_id, committed):
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
            # The QTimer is to avoid funny situations where the user enters new data via the empty row model,
            # and those rows need to be removed at the same time as we fetch the added data.
            # Doing it in the same loop cycle was causing bugs.
            QTimer.singleShot(0, self.layoutChanged.emit)
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

    def _add_items(self, db_map, entity_class_id, ids, committed):
        """Creates new single model and resets it with the given parameter ids.

        Args:
            db_map (DatabaseMapping): database map
            entity_class_id (int): parameter's entity class id
            ids (list of int): parameter ids
            committed (bool): True if the ids have been committed, False otherwise
        """
        if not ids:
            return
        if committed:
            existing = next(
                (m for m in self.sub_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
            )
            if existing is not None:
                existing.add_rows(ids)
                return
        model = self._create_single_model(db_map, entity_class_id, committed)
        model.reset_model(ids)

    def handle_items_updated(self, db_map_data):
        """Runs when either parameter definitions or values are updated in the dbs.
        Emits dataChanged so the parameter_name column is refreshed.

        Args:
            db_map_data (dict): list of updated dict-items keyed by DatabaseMapping
        """
        if all(db_map not in self.db_maps for db_map in db_map_data):
            return
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.ItemDataRole.DisplayRole]
        )

    def handle_items_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DatabaseMapping
        """
        for db_map, items in db_map_data.items():
            if db_map not in self.db_maps:
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

    def _delete_rows_from_single_model(self, model, rows_to_remove):
        """Removes rows from given single model and computes a map from original rows to retained rows.

        Args:
            model (SingleModelBase): single model to delete data from
            rows_to_remove (set of int): row index that should be removed

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

    def _update_single_model_rows_in_row_map(self, model, new_rows):
        """Rewrites single model rows in row map.

        Args:
            model (SingleModelBase): single model whose rows to update
            new_rows (dict): mapping from old row index to updated index
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

    def db_item(self, index):
        sub_index = self.map_to_sub(index)
        return sub_index.model().db_item(sub_index)

    def db_map_id(self, index):
        sub_index = self.map_to_sub(index)
        sub_model = sub_index.model()
        if sub_model is None:
            return None, None
        return sub_model.db_map, sub_model.item_id(sub_index.row())

    def filter_by(self, rows_per_column):
        for column, rows in rows_per_column.items():
            field = self.headerData(column)
            menu = self._make_auto_filter_menu(field)
            accepted_values = {self.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in rows}
            menu.set_filter_accepted_values(accepted_values)

    def filter_excluding(self, rows_per_column):
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

    def set_filter_entity_ids(self, entity_ids):
        self._filter_entity_ids = entity_ids
        for model in self.sub_models:
            if model.set_filter_entity_ids(entity_ids):
                self._invalidate_filter()

    def set_filter_alternative_ids(self, alternative_ids):
        self._filter_alternative_ids = alternative_ids
        for model in self.sub_models:
            if model.set_filter_alternative_ids(alternative_ids):
                self._invalidate_filter()

    def _create_single_model(self, db_map, entity_class_id, committed):
        model = super()._create_single_model(db_map, entity_class_id, committed)
        model.set_filter_entity_ids(self._filter_entity_ids)
        model.set_filter_alternative_ids(self._filter_alternative_ids)
        return model


class EditParameterValueMixin:
    """Provides the interface to edit values via ParameterValueEditor."""

    def handle_items_updated(self, db_map_data):
        changed_rows = []
        for db_map, items in db_map_data.items():
            if db_map not in self.db_maps:
                continue
            items_by_class = self._items_per_class(items)
            for entity_class_id, class_items in items_by_class.items():
                single_model = next(
                    (m for m in self.sub_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
                )
                if single_model is not None:
                    single_model.revalidate_item_types(class_items)
                    changed_rows = [
                        self._inv_row_map[(single_model, single_row)] for single_row in range(single_model.rowCount())
                    ]
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
        if self.item_type == "parameter_definition":
            parameter_name = item["name"]
            names = [item["entity_class_name"]]
            alternative_name = None
        elif self.item_type == "parameter_value":
            parameter_name = item["parameter_name"]
            names = list(item["entity_byname"])
            alternative_name = item["alternative_name"]
        else:
            raise ValueError(
                f"invalid item_type: expected parameter_definition or parameter_value, got {self.item_type}"
            )
        return parameter_identifier(database, parameter_name, names, alternative_name)

    def get_set_data_delayed(self, index):
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.

        Args:
            index (QModelIndex)

        Returns:
            function
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

    @staticmethod
    def _make_header():
        return PARAMETER_DEFINITION_MODEL_HEADER

    @property
    def _single_model_type(self):
        return SingleParameterDefinitionModel


class CompoundParameterValueModel(FilterEntityAlternativeMixin, EditParameterValueMixin, CompoundStackedModel):
    """A model that concatenates several single parameter_value models and one empty parameter_value model."""

    item_type = "parameter_value"
    field_map = PARAMETER_VALUE_FIELD_MAP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._definition_fetch_parent = FlexibleFetchParent(
            "parameter_definition",
            shows_item=lambda item, db_map: True,
            handle_items_updated=self._handle_parameter_definitions_updated,
            owner=self,
        )

    @staticmethod
    def _make_header():
        return PARAMETER_VALUE_MODEL_HEADER

    @property
    def _single_model_type(self):
        return SingleParameterValueModel

    def reset_db_map(self, db_maps):
        super().reset_db_maps(db_maps)
        self._definition_fetch_parent.set_obsolete(False)
        self._definition_fetch_parent.reset()

    def _handle_parameter_definitions_updated(self, db_map_data):
        for db_map, items in db_map_data.items():
            if db_map not in self.db_maps:
                continue
            items_by_class = self._items_per_class(items)
            for entity_class_id, class_items in items_by_class.items():
                single_model = next(
                    (m for m in self.sub_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
                )
                if single_model is not None:
                    single_model.revalidate_item_typs(class_items)


class CompoundEntityAlternativeModel(FilterEntityAlternativeMixin, CompoundStackedModel):

    item_type = "entity_alternative"

    @staticmethod
    def _make_header():
        return ENTITY_ALTERNATIVE_MODEL_HEADER

    @property
    def _single_model_type(self):
        return SingleEntityAlternativeModel
