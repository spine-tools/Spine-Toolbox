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

""" Compound models. These models concatenate several 'single' models and one 'empty' model. """
from PySide6.QtCore import Qt, Slot, QTimer, QModelIndex
from PySide6.QtGui import QFont
from spinedb_api.parameter_value import join_value_and_type
from ...helpers import parameter_identifier, rows_to_row_count_tuples
from ...fetch_parent import FlexibleFetchParent
from ...mvcmodels.compound_table_model import CompoundWithEmptyTableModel
from ..widgets.custom_menus import AutoFilterMenu
from .empty_models import EmptyParameterDefinitionModel, EmptyParameterValueModel, EmptyEntityAlternativeModel
from .single_models import SingleParameterDefinitionModel, SingleParameterValueModel, SingleEntityAlternativeModel


class CompoundModelBase(CompoundWithEmptyTableModel):
    """A base model for all models that show data in stacked format."""

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

    def _make_header(self):
        raise NotImplementedError()

    @property
    def field_map(self):
        return {}

    @property
    def item_type(self):
        """Returns the DB item type, e.g., 'parameter_value'.

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def _single_model_type(self):
        """
        Returns a constructor for the single models.

        Returns:
            SingleParameterModel
        """
        raise NotImplementedError()

    @property
    def _empty_model_type(self):
        """
        Returns a constructor for the empty model.

        Returns:
            EmptyParameterModel
        """
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

    def init_model(self):
        """Initializes the model."""
        super().init_model()
        self._filter_class_ids = {}
        self._auto_filter = {}
        self.empty_model.fetchMore(QModelIndex())
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

    def _create_empty_model(self):
        """Returns the empty model for this compound model.

        Returns:
            EmptyParameterModel
        """
        return self._empty_model_type(self)

    def filter_accepts_model(self, model):
        """Returns a boolean indicating whether the given model passes the filter for compound model.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

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
        return model.entity_class_id in self._filter_class_ids.get(model.db_map, set()) or bool(
            set(model.dimension_id_list) & self._filter_class_ids.get(model.db_map, set())
        )

    def _auto_filter_accepts_model(self, model):
        if None in self._auto_filter.values():
            return False
        for values in self._auto_filter.values():
            if not values:
                continue
            for db_map, entity_class_id in values:
                if model.db_map == db_map and (entity_class_id is None or model.entity_class_id == entity_class_id):
                    break
            else:  # nobreak
                return False
        return True

    def accepted_single_models(self):
        """Returns a list of accepted single models by calling filter_accepts_model
        on each of them, just for convenience.

        Returns:
            list
        """
        return [m for m in self.single_models if self.filter_accepts_model(m)]

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
        return [m for m in self.single_models if m.db_map == db_map]

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
        Also notifies the empty model so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of added dict-items keyed by DatabaseMapping
        """
        for db_map, items in db_map_data.items():
            db_map_single_models = [m for m in self.single_models if m.db_map is db_map]
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
        self.empty_model.handle_items_added(db_map_data)

    def _get_insert_position(self, model):
        if model.committed:
            return super()._get_insert_position(model)
        return len(self.single_models)

    def _create_single_model(self, db_map, entity_class_id, committed):
        model = self._single_model_type(self, db_map, entity_class_id, committed)
        self._connect_single_model(model)
        for field in self._auto_filter:
            self._set_single_auto_filter(model, field)
        return model

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
                (m for m in self.single_models if (m.db_map, m.entity_class_id) == (db_map, entity_class_id)), None
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
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.ItemDataRole.DisplayRole]
        )

    def handle_items_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, items in db_map_data.items():
            items_per_class = self._items_per_class(items)
            emptied_single_model_indexes = []
            for model_index, model in enumerate(self.single_models):
                if model.db_map != db_map:
                    continue
                removed_ids = {x["id"] for x in items_per_class.get(model.entity_class_id, {})}
                if not removed_ids:
                    continue
                removed_rows = []
                for row in range(model.rowCount()):
                    id_ = model._main_data[row]
                    if id_ in removed_ids:
                        removed_rows.append(row)
                        removed_ids.remove(id_)
                        if not removed_ids:
                            break
                for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
                    del model._main_data[row : row + count]
                if model.rowCount() == 0:
                    emptied_single_model_indexes.append(model_index)
            for model_index in reversed(emptied_single_model_indexes):
                model = self.sub_models.pop(model_index)
                model.deleteLater()
        self._do_refresh()
        self.layoutChanged.emit()

    def db_item(self, index):
        sub_index = self.map_to_sub(index)
        return sub_index.model().db_item(sub_index)

    def db_map_id(self, index):
        sub_index = self.map_to_sub(index)
        sub_model = sub_index.model()
        if sub_model is None:
            return None, None
        return sub_model.db_map, sub_model.item_id(sub_index.row())

    def get_entity_class_id(self, index, db_map):
        entity_class_name = index.sibling(index.row(), self.header.index("entity_class_name")).data()
        entity_class = db_map.get_item("entity_class", name=entity_class_name)
        return entity_class.get("id")

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
        for model in self.single_models:
            if model.set_filter_entity_ids(entity_ids):
                self._invalidate_filter()

    def set_filter_alternative_ids(self, alternative_ids):
        self._filter_alternative_ids = alternative_ids
        for model in self.single_models:
            if model.set_filter_alternative_ids(alternative_ids):
                self._invalidate_filter()

    def _create_single_model(self, db_map, entity_class_id, committed):
        model = super()._create_single_model(db_map, entity_class_id, committed)
        model.set_filter_entity_ids(self._filter_entity_ids)
        model.set_filter_alternative_ids(self._filter_alternative_ids)
        return model


class EditParameterValueMixin:
    """Provides the interface to edit values via ParameterValueEditor."""

    def index_name(self, index):
        """Generates a name for data at given index.

        Args:
            index (QModelIndex): index to model

        Returns:
            str: label identifying the data
        """
        item = self.db_item(index)
        if item is None:
            return ""
        database = self.index(index.row(), self.columnCount() - 1).data()
        if self.item_type == "parameter_definition":
            parameter_name = item["name"]
            names = [item["entity_class_name"]]
        elif self.item_type == "parameter_value":
            parameter_name = item["parameter_name"]
            names = list(item["entity_byname"])
        else:
            raise ValueError(
                f"invalid item_type: expected parameter_definition or parameter_value, got {self.item_type}"
            )
        alternative_name = {"parameter_definition": lambda x: None, "parameter_value": lambda x: x["alternative_name"]}[
            self.item_type
        ](item)
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
        if sub_model == self.empty_model:
            return lambda value_and_type, index=index: self.setData(index, join_value_and_type(*value_and_type))
        id_ = self.item_at_row(index.row())
        value_field = {"parameter_value": "value", "parameter_definition": "default_value"}[self.item_type]
        return lambda value_and_type, sub_model=sub_model, id_=id_: sub_model.update_items_in_db(
            [{"id": id_, value_field: join_value_and_type(*value_and_type)}]
        )


class CompoundParameterDefinitionModel(EditParameterValueMixin, CompoundModelBase):
    """A model that concatenates several single parameter_definition models and one empty parameter_definition model."""

    @property
    def item_type(self):
        return "parameter_definition"

    def _make_header(self):
        return [
            "entity_class_name",
            "parameter_name",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]

    @property
    def field_map(self):
        return {"parameter_name": "name", "value_list_name": "parameter_value_list_name"}

    @property
    def _single_model_type(self):
        return SingleParameterDefinitionModel

    @property
    def _empty_model_type(self):
        return EmptyParameterDefinitionModel


class CompoundParameterValueModel(FilterEntityAlternativeMixin, EditParameterValueMixin, CompoundModelBase):
    """A model that concatenates several single parameter_value models and one empty parameter_value model."""

    @property
    def item_type(self):
        return "parameter_value"

    def _make_header(self):
        return [
            "entity_class_name",
            "entity_byname",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]

    @property
    def field_map(self):
        return {"parameter_name": "parameter_definition_name"}

    @property
    def _single_model_type(self):
        return SingleParameterValueModel

    @property
    def _empty_model_type(self):
        return EmptyParameterValueModel


class CompoundEntityAlternativeModel(FilterEntityAlternativeMixin, CompoundModelBase):
    @property
    def item_type(self):
        return "entity_alternative"

    def _make_header(self):
        return [
            "entity_class_name",
            "entity_byname",
            "alternative_name",
            "active",
            "database",
        ]

    @property
    def _single_model_type(self):
        return SingleEntityAlternativeModel

    @property
    def _empty_model_type(self):
        return EmptyEntityAlternativeModel
