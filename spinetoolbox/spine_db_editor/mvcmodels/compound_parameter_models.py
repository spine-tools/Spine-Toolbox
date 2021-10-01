######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Compound models for object parameter definitions and values.
These models concatenate several 'single' models and one 'empty' model.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""
from PySide2.QtCore import Qt, Slot, QTimer, QModelIndex
from PySide2.QtGui import QFont
from spinedb_api.parameter_value import join_value_and_type
from ...helpers import rows_to_row_count_tuples, parameter_identifier
from ..widgets.custom_menus import ParameterViewFilterMenu
from ...mvcmodels.compound_table_model import CompoundWithEmptyTableModel
from .empty_parameter_models import (
    EmptyObjectParameterDefinitionModel,
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterDefinitionModel,
    EmptyRelationshipParameterValueModel,
)
from .single_parameter_models import (
    SingleObjectParameterDefinitionModel,
    SingleObjectParameterValueModel,
    SingleRelationshipParameterDefinitionModel,
    SingleRelationshipParameterValueModel,
)


class CompoundParameterModel(CompoundWithEmptyTableModel):
    """A model that concatenates several single parameter models
    and one empty parameter model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model.

        Args:
            parent (SpineDBEditor): the parent object
            db_mngr (SpineDBManager): the database manager
            *db_maps (DiffDatabaseMapping): the database maps included in the model
        """
        super().__init__(parent=parent, header=self._make_header())
        self._parent = parent
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._filter_class_ids = {}
        self._auto_filter_menus = {}
        self._auto_filter = dict()  # Maps field to db map, to entity id, to *accepted* item ids
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(100)
        self._filter_timer.timeout.connect(self.refresh)

    def canFetchMore(self, _parent):
        return any(self.db_mngr.can_fetch_more(db_map, self.item_type, parent=self) for db_map in self.db_maps)

    def fetchMore(self, _parent):
        for db_map in self.db_maps:
            self.db_mngr.fetch_more(db_map, self.item_type, parent=self)

    def fetch_successful(self, db_map, item):
        entity_class_id = item.get(self.entity_class_id_key)
        if entity_class_id is None:
            return False
        model = self._create_single_model(db_map, entity_class_id)
        return self.filter_accepts_model(model) and model.filter_accepts_item(item)

    def fetch_id(self):
        return str(self.__dict__)

    def _make_header(self):
        raise NotImplementedError()

    @property
    def entity_class_type(self):
        """Returns the entity_class type, either 'object_class' or 'relationship_class'.

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def item_type(self):
        """Returns the parameter item type, either 'parameter_definition' or 'parameter_value'.

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
        return {
            "object_class": {
                "parameter_definition": SingleObjectParameterDefinitionModel,
                "parameter_value": SingleObjectParameterValueModel,
            },
            "relationship_class": {
                "parameter_definition": SingleRelationshipParameterDefinitionModel,
                "parameter_value": SingleRelationshipParameterValueModel,
            },
        }[self.entity_class_type][self.item_type]

    @property
    def _empty_model_type(self):
        """
        Returns a constructor for the empty model.

        Returns:
            EmptyParameterModel
        """
        return {
            "object_class": {
                "parameter_definition": EmptyObjectParameterDefinitionModel,
                "parameter_value": EmptyObjectParameterValueModel,
            },
            "relationship_class": {
                "parameter_definition": EmptyRelationshipParameterDefinitionModel,
                "parameter_value": EmptyRelationshipParameterValueModel,
            },
        }[self.entity_class_type][self.item_type]

    @property
    def entity_class_id_key(self):
        """
        Returns the key corresponding to the entity_class id (either "object_class_id" or "relationship_class_id")

        Returns:
            str
        """
        return {"object_class": "object_class_id", "relationship_class": "relationship_class_id"}[
            self.entity_class_type
        ]

    @property
    def parameter_definition_id_key(self):
        return {"parameter_definition": "id", "parameter_value": "parameter_id"}[self.item_type]

    def init_model(self):
        """Initializes the model."""
        super().init_model()
        self.empty_model.fetchMore(QModelIndex())
        self._make_auto_filter_menus()

    def _make_auto_filter_menus(self):
        """Makes auto filter menus."""
        self._auto_filter_menus.clear()
        for field in self.header:
            # TODO: show_empty=True
            self._auto_filter_menus[field] = menu = ParameterViewFilterMenu(self._parent, self, field, show_empty=False)
            menu.filterChanged.connect(self.set_auto_filter)

    def get_auto_filter_menu(self, logical_index):
        """Returns auto filter menu for given logical index from header view.

        Args:
            logical_index (int)

        Returns:
            ParameterViewFilterMenu
        """
        return self._auto_filter_menus.get(self.header[logical_index], None)

    def _modify_data_in_filter_menus(self, action, db_map, db_items):
        """Modifies data in filter menus.

        Args:
            action (str): either 'add', 'remove', or 'update'
            db_map (DiffDatabaseMapping)
            db_items (list(dict))
        """
        for menu in self._auto_filter_menus.values():
            menu.modify_menu_data(action, db_map, db_items)

    def _do_add_data_to_filter_menus(self, db_map, db_items):
        self._modify_data_in_filter_menus("add", db_map, db_items)

    def _do_update_data_in_filter_menus(self, db_map, db_items):
        self._modify_data_in_filter_menus("update", db_map, db_items)

    def _do_remove_data_from_filter_menus(self, db_map, db_items):
        self._modify_data_in_filter_menus("remove", db_map, db_items)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Returns an italic font in case the given column has an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if (
            role == Qt.FontRole
            and orientation == Qt.Horizontal
            and self._auto_filter.get(self.header[section], {}) != {}
        ):
            return italic_font
        return super().headerData(section, orientation, role)

    def _create_empty_model(self):
        """Returns the empty model for this compound model.

        Returns:
            EmptyParameterModel
        """
        return self._empty_model_type(self, self.header, self.db_mngr)

    def filter_accepts_model(self, model):
        """Returns a boolean indicating whether or not the given model passes the filter for compound model.

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
        return model.entity_class_id in self._filter_class_ids.get(model.db_map, set())

    def _auto_filter_accepts_model(self, model):
        if None in self._auto_filter.values():
            return False
        for auto_filter in self._auto_filter.values():
            if not auto_filter:
                continue
            if model.db_map not in auto_filter:
                return False
            if model.entity_class_id not in auto_filter[model.db_map]:
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

    def set_filter_class_ids(self, class_ids):
        if class_ids != self._filter_class_ids:
            self._filter_class_ids = class_ids
            self._invalidate_filter()

    @Slot(str, dict)
    def set_auto_filter(self, field, values):
        """Updates and applies the auto filter.

        Args:
            field (str): the field name
            values (dict): mapping db_map to entity_class id to accepted values for the field
        """
        self._set_compound_auto_filter(field, values)
        for model in self.accepted_single_models():
            self._set_single_auto_filter(model, field)

    def _set_compound_auto_filter(self, field, values):
        """Sets the auto filter for given column in the compound model.

        Args:
            field (str): the field name
            values (dict): maps tuple (database map, entity_class id) to list of accepted ids for the field
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
        values = self._auto_filter[field].get(model.db_map, {}).get(model.entity_class_id, {})
        if model.set_auto_filter(field, values):
            self._invalidate_filter()

    def _row_map_for_model(self, model):
        """Returns the row map for the given model.
        Reimplemented to take filter status into account.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

        Returns:
            list: tuples (model, row number) for each accepted row
        """
        if not self.filter_accepts_model(model):
            return []
        return [(model, i) for i in model.accepted_rows()]

    def _models_with_db_map(self, db_map):
        """Returns a collection of single models with given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list
        """
        return [m for m in self.single_models if m.db_map == db_map]

    def receive_entity_classes_removed(self, db_map_data):
        """Runs when entity classes are removed from the dbs.
        Removes sub-models for the given entity classes and dbs.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, data in db_map_data.items():
            ids = {x["id"] for x in data}
            for model in self._models_with_db_map(db_map):
                if model.entity_class_id in ids:
                    self.sub_models.remove(model)
        self._do_refresh()
        self.layoutChanged.emit()

    def _items_per_class(self, items):
        """Returns a dict mapping entity_class ids to a set of items.

        Args:
            items (list)

        Returns:
            dict
        """
        d = dict()
        for item in items:
            entity_class_id = item.get(self.entity_class_id_key)
            if not entity_class_id:
                continue
            d.setdefault(entity_class_id, list()).append(item)
        return d

    def receive_parameter_data_added(self, db_map_data):
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of added dict-items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            items_per_class = self._items_per_class(items)
            for entity_class_id, class_items in items_per_class.items():
                ids = [item["id"] for item in class_items]
                self._add_parameter_data(db_map, entity_class_id, ids)
                self._do_add_data_to_filter_menus(db_map, class_items)
        self.empty_model.receive_parameter_data_added(db_map_data)

    def _create_single_model(self, db_map, entity_class_id):
        model = self._single_model_type(self.header, self.db_mngr, db_map, entity_class_id)
        self._connect_single_model(model)
        for field in self._auto_filter:
            self._set_single_auto_filter(model, field)
        return model

    def _add_parameter_data(self, db_map, entity_class_id, ids):
        existing = next((m for m in self.single_models if m.entity_class_id == entity_class_id), None)
        if existing is not None:
            existing.add_rows(ids)
            return
        model = self._create_single_model(db_map, entity_class_id)
        model.reset_model(ids)

    def receive_parameter_data_updated(self, db_map_data):
        """Runs when either parameter definitions or values are updated in the dbs.
        Emits dataChanged so the parameter_name column is refreshed.

        Args:
            db_map_data (dict): list of updated dict-items keyed by DiffDatabaseMapping
        """
        for db_map, items in db_map_data.items():
            items_per_class = self._items_per_class(items)
            for class_items in items_per_class.values():
                self._do_update_data_in_filter_menus(db_map, class_items)
        self._emit_data_changed_for_column("parameter_name")
        # NOTE: parameter_definition names aren't refreshed unless we emit dataChanged,
        # whereas entity and class names are. Why?

    def receive_parameter_data_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, items in db_map_data.items():
            items_per_class = self._items_per_class(items)
            for model in self._models_with_db_map(db_map):
                removed_ids = [x["id"] for x in items_per_class.get(model.entity_class_id, {})]
                if not removed_ids:
                    continue
                removed_rows = [row for row in range(model.rowCount()) if model._main_data[row] in removed_ids]
                for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
                    del model._main_data[row : row + count]
            for class_items in items_per_class.values():
                self._do_remove_data_from_filter_menus(db_map, class_items)
        self._do_refresh()
        self.layoutChanged.emit()

    def _emit_data_changed_for_column(self, field):
        """Lazily emits data changed for an entire column.

        Args:
            field (str): the column header
        """
        try:
            column = self.header.index(field)
        except ValueError:
            return
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])

    def db_item(self, index):
        sub_index = self.map_to_sub(index)
        return sub_index.model().db_item(sub_index)

    def db_map_id(self, index):
        sub_index = self.map_to_sub(index)
        sub_model = sub_index.model()
        return sub_model.db_map, sub_model.item_id(sub_index.row())

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
        database = self.index(index.row(), self.columnCount() - 1).data() if len(self.db_maps) > 1 else None
        entity_name_key = {
            "parameter_definition": {
                "object_class": "object_class_name",
                "relationship_class": "relationship_class_name",
            },
            "parameter_value": {"object_class": "object_name", "relationship_class": "object_name_list"},
        }[self.item_type][self.entity_class_type]
        entity_names = item[entity_name_key].split(",")
        return parameter_identifier(database, item["parameter_name"], item["alternative_name"], entity_names)

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

    def get_entity_class_id(self, index, db_map):
        entity_class_name_key = {"object_class": "object_class_name", "relationship_class": "relationship_class_name"}[
            self.entity_class_type
        ]
        entity_class_name = index.sibling(index.row(), self.header.index(entity_class_name_key)).data()
        entity_class = self.db_mngr.get_item_by_field(db_map, self.entity_class_type, "name", entity_class_name)
        return entity_class.get("id")

    def filter_by(self, rows_per_column):
        for column, rows in rows_per_column.items():
            field = self.headerData(column)
            menu = self._auto_filter_menus[field]
            accepted_values = {self.index(row, column).data(Qt.EditRole) for row in rows}
            menu.set_filter_accepted_values(accepted_values)
            menu._filter._apply_filter()

    def filter_excluding(self, rows_per_column):
        for column, rows in rows_per_column.items():
            field = self.headerData(column)
            menu = self._auto_filter_menus[field]
            rejected_values = {self.index(row, column).data(Qt.EditRole) for row in rows}
            menu.set_filter_rejected_values(rejected_values)
            menu._filter._apply_filter()


class CompoundObjectParameterMixin:
    """Implements the interface for populating and filtering a compound object parameter model."""

    @property
    def entity_class_type(self):
        return "object_class"


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    @property
    def entity_class_type(self):
        return "relationship_class"


class CompoundParameterDefinitionMixin:
    """Handles signals from db mngr for parameter_definition models."""

    @property
    def item_type(self):
        return "parameter_definition"


class CompoundParameterValueMixin:
    """Handles signals from db mngr for parameter_value models."""

    _filter_entity_ids = dict()
    _filter_alternative_ids = dict()

    @property
    def item_type(self):
        return "parameter_value"

    @property
    def entity_type(self):
        """Returns the entity type, either 'object' or 'relationship'
        Used by update_single_main_filter.

        Returns:
            str
        """
        raise NotImplementedError()

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

    def _create_single_model(self, db_map, entity_class_id):
        model = super()._create_single_model(db_map, entity_class_id)
        model.set_filter_entity_ids(self._filter_entity_ids)
        model.set_filter_alternative_ids(self._filter_alternative_ids)
        return model

    def receive_alternatives_updated(self, db_map_data):
        """Updated alternative column

        Args:
            db_map_data (dict): list of updated dict-items keyed by DiffDatabaseMapping
        """
        self._emit_data_changed_for_column("alternative_id")


class CompoundObjectParameterDefinitionModel(
    CompoundObjectParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter_definition models
    and one empty object parameter_definition model.
    """

    def _make_header(self):
        return ["object_class_name", "parameter_name", "value_list_name", "default_value", "description", "database"]


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter_definition models
    and one empty relationship parameter_definition model.
    """

    def _make_header(self):
        return [
            "relationship_class_name",
            "object_class_name_list",
            "parameter_name",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]


class CompoundObjectParameterValueModel(
    CompoundObjectParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter_value models
    and one empty object parameter_value model.
    """

    def _make_header(self):
        return ["object_class_name", "object_name", "parameter_name", "alternative_name", "value", "database"]

    @property
    def entity_type(self):
        return "object"


class CompoundRelationshipParameterValueModel(
    CompoundRelationshipParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter_value models
    and one empty relationship parameter_value model.
    """

    def _make_header(self):
        return [
            "relationship_class_name",
            "object_name_list",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]

    @property
    def entity_type(self):
        return "relationship"
