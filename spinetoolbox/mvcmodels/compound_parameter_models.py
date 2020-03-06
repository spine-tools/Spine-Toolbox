######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from PySide2.QtCore import Qt, Signal, QModelIndex
from PySide2.QtGui import QFont, QIcon
from ..helpers import busy_effect, rows_to_row_count_tuples
from ..widgets.custom_menus import ParameterViewFilterMenu
from .compound_table_model import CompoundWithEmptyTableModel
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
from .auto_filter_menu_model import AutoFilterMenuItem


class CompoundParameterModel(CompoundWithEmptyTableModel):
    """A model that concatenates several single parameter models
    and one empty parameter model.
    """

    remove_selection_requested = Signal()

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model.

        Args:
            parent (DataStoreForm): the parent object
            db_mngr (SpineDBManager): the database manager
            *db_maps (DiffDatabaseMapping): the database maps included in the model
        """
        super().__init__(parent, header=self._make_header())
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._auto_filter = dict()
        self._accepted_entity_class_ids = {}  # Accepted by main filter
        self.remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self._auto_filter_menus = {}
        self._make_auto_filter_menus()
        self._field_value_row_map = dict()  # Maps fields to values to the first model row where it's encountered

    def _make_header(self):
        raise NotImplementedError()

    def _make_auto_filter_menus(self):
        self._auto_filter_menus = {
            h: ParameterViewFilterMenu(self.parent(), self, column) for column, h in enumerate(self.header)
        }

    def get_auto_filter_menu(self, logical_index):
        return self._auto_filter_menus[self.header[logical_index]]

    def fetchMore(self, parent=QModelIndex()):
        """Populates filter menus as submodels are fetched."""
        super().fetchMore(parent=parent)
        if not self._fetch_sub_model in self.sub_models:
            return
        db_items = self._fetch_sub_model.db_items()
        for sub_row, db_item in enumerate(db_items):
            for field, value in db_item.items():
                row = self._inv_row_map[self._fetch_sub_model, sub_row]
                self._field_value_row_map.setdefault(field, dict()).setdefault(value, row)
        for field, menu in self._auto_filter_menus.items():
            rows = self._field_value_row_map.get(field, {}).values()
            menu.add_items_to_filter_list(rows)

    @property
    def entity_class_type(self):
        """Returns the entity class type, either 'object class' or 'relationship class'.

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def item_type(self):
        """Returns the parameter item type, either 'parameter definition' or 'parameter value'.

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
            "object class": {
                "parameter definition": SingleObjectParameterDefinitionModel,
                "parameter value": SingleObjectParameterValueModel,
            },
            "relationship class": {
                "parameter definition": SingleRelationshipParameterDefinitionModel,
                "parameter value": SingleRelationshipParameterValueModel,
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
            "object class": {
                "parameter definition": EmptyObjectParameterDefinitionModel,
                "parameter value": EmptyObjectParameterValueModel,
            },
            "relationship class": {
                "parameter definition": EmptyRelationshipParameterDefinitionModel,
                "parameter value": EmptyRelationshipParameterValueModel,
            },
        }[self.entity_class_type][self.item_type]

    @property
    def _entity_class_id_key(self):
        """
        Returns the key of the entity class id in the model items (either "object_class_id" or "relationship_class_id")

        Returns:
            str
        """
        return {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.entity_class_type
        ]

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Returns an italic font in case the given column has an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if role == Qt.FontRole and orientation == Qt.Horizontal and self._auto_filter.get(section):
            return italic_font
        return super().headerData(section, orientation, role)

    def _get_entity_classes(self, db_map):
        """Returns a list of entity classes from the given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list
        """
        raise NotImplementedError()

    def _create_single_models(self):
        """Returns a list of single models for this compound model, one for each entity class in each database.

        Returns:
            list
        """
        d = dict()
        for db_map in self.db_maps:
            for entity_class in self._get_entity_classes(db_map):
                d.setdefault(entity_class["name"], {}).setdefault(db_map, set()).add(entity_class["id"])
        models = []
        for db_map_ids in d.values():
            for db_map, entity_class_ids in db_map_ids.items():
                for entity_class_id in entity_class_ids:
                    models.append(self._single_model_type(self, self.header, self.db_mngr, db_map, entity_class_id))
        return models

    def _create_empty_model(self):
        """Returns the empty model for this compound model.

        Returns:
            EmptyParameterModel
        """
        return self._empty_model_type(self, self.header, self.db_mngr)

    def filter_accepts_model(self, model):
        """Returns a boolean indicating whether or not the given model should be included in this compound model.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

        Returns:
            bool
        """
        if not model.can_be_filtered:
            return True
        if not self._auto_filter_accepts_model(model):
            return False
        if not self._main_filter_accepts_model(model):
            return False
        return True

    def _main_filter_accepts_model(self, model):
        if self._accepted_entity_class_ids is None:
            return False
        if self._accepted_entity_class_ids == {}:
            return True
        return model.entity_class_id in self._accepted_entity_class_ids.get(model.db_map, set())

    def _auto_filter_accepts_model(self, model):
        if None in [value for column, value in self._auto_filter.items()]:
            return False
        for auto_filter in self._auto_filter.values():
            if not auto_filter:
                continue
            if (model.db_map, model.entity_class_id) not in auto_filter.keys():
                return False
        return True

    def accepted_single_models(self):
        """Returns a list of accepted single models by calling filter_accepts_model
        on each of them, just for convenience.

        Returns:
            list
        """
        return [m for m in self.single_models if self.filter_accepts_model(m)]

    @staticmethod
    def _settattr_if_different(obj, attr, val):
        """Sets the given attribute of the given object to the given value if it's different
        from the one currently stored. Used for updating filters.

        Returns:
            bool: True if the attributed was set, False otherwise
        """
        curr = getattr(obj, attr)
        if curr != val:
            setattr(obj, attr, val)
            return True
        return False

    def update_main_filter(self):
        """Updates and applies the main filter."""
        updated = self.update_compound_main_filter()
        for model in self.single_models:
            updated |= self.update_single_main_filter(model)
        if updated:
            self.refresh()

    def update_compound_main_filter(self):
        """Updates the main filter in the compound model by setting the _accepted_entity_class_ids attribute.

        Returns:
            bool: True if the filter was updated, None otherwise
        """
        a = bool(self._auto_filter)
        self._auto_filter = dict()
        b = self._settattr_if_different(
            self, "_accepted_entity_class_ids", self.parent().selected_entity_class_ids(self.entity_class_type)
        )
        return a or b

    def update_single_main_filter(self, model):
        """Updates the filter in the given single model by setting its _selected_param_def_ids attribute.

        Args:
            model (SingleParameterModel)

        Returns:
            bool: True if the filter was updated, None otherwise
        """
        a = bool(model._auto_filter)
        model._auto_filter.clear()
        selected_param_def_ids = self.parent().selected_param_def_ids[self.entity_class_type]
        if selected_param_def_ids is not None:
            selected_param_def_ids = selected_param_def_ids.get((model.db_map, model.entity_class_id), set())
        b = self._settattr_if_different(model, "_selected_param_def_ids", selected_param_def_ids)
        return a or b

    def update_auto_filter(self, column, auto_filter):
        """Updates and applies the auto filter.

        Args:
            column (int): the column number
            auto_filter (dict): list of accepted values for the column keyed by tuple (database map, entity class id)
        """
        updated = self.update_compound_auto_filter(column, auto_filter)
        for model in self.accepted_single_models():
            updated |= self.update_single_auto_filter(model, column)
        if updated:
            self.refresh()

    def update_compound_auto_filter(self, column, auto_filter):
        """Updates the auto filter for given column in the compound model.

        Args:
            column (int): the column number
            auto_filter (dict): list of accepted values for the column keyed by tuple (database map, entity class id)
        """
        if self._auto_filter.setdefault(column, {}) == auto_filter:
            return False
        self._auto_filter[column] = auto_filter
        return True

    def update_single_auto_filter(self, model, column):
        """Updates the auto filter for given column in the given single model.

        Args:
            model (SingleParameterModel): the model
            column (int): the column number

        Returns:
            bool: True if the auto-filtered values were updated, None otherwise
        """
        values = self._auto_filter[column].get((model.db_map, model.entity_class_id), {})
        if values == model._auto_filter.get(column, {}):
            return False
        model._auto_filter[column] = values
        return True

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

    @busy_effect
    def auto_filter_menu_data(self, column):
        """Returns auto filter menu data for the given column.

        Returns:
            list: AutoFilterMenuItem instances to populate the auto filter menu.
        """
        auto_filter_vals = dict()
        for model in self.single_models:
            if not self._main_filter_accepts_model(model):
                continue
            for row in range(model.rowCount()):
                if not model._main_filter_accepts_row(row):
                    continue
                value = model.index(row, column).data()
                auto_filter_vals.setdefault(value, set()).add((model.db_map, model.entity_class_id))
        column_auto_filter = self._auto_filter.get(column, {})
        if column_auto_filter is None:
            return [AutoFilterMenuItem(Qt.Unchecked, value, classes) for value, classes in auto_filter_vals.items()]
        if column_auto_filter == {}:
            return [AutoFilterMenuItem(Qt.Checked, value, classes) for value, classes in auto_filter_vals.items()]
        return [
            AutoFilterMenuItem(
                Qt.Checked if any(value in values for values in column_auto_filter.values()) else Qt.Unchecked,
                value,
                classes,
            )
            for value, classes in auto_filter_vals.items()
        ]

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
        self.do_refresh()
        self.layoutChanged.emit()

    def receive_parameter_data_updated(self, db_map_data):
        """Runs when either parameter definitions or values are updated in the dbs.
        Emits dataChanged so the parameter_name column is refreshed.

        Args:
            db_map_data (dict): list of updated dict-items keyed by DiffDatabaseMapping
        """
        self._emit_data_changed_for_column("parameter_name")
        # TODO: parameter definition names aren't refreshed unless we emit dataChanged,
        # whereas entity and class names don't need it. Why?

    def _entity_ids_per_class_id(self, items):
        """Returns a dict mapping entity class ids to a set of entity ids.

        Args:
            items (list)

        Returns:
            dict
        """
        d = dict()
        for item in items:
            entity_class_id = item.get(self._entity_class_id_key)
            if not entity_class_id:
                continue
            d.setdefault(entity_class_id, list()).append(item["id"])
        return d

    def receive_parameter_data_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, items in db_map_data.items():
            entity_ids_per_class_id = self._entity_ids_per_class_id(items)
            for model in self._models_with_db_map(db_map):
                removed_ids = entity_ids_per_class_id.get(model.entity_class_id)
                if not removed_ids:
                    continue
                removed_rows = [row for row in range(model.rowCount()) if model._main_data[row] in removed_ids]
                for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
                    del model._main_data[row : row + count]
        self.do_refresh()
        self.layoutChanged.emit()

    def receive_parameter_data_added(self, db_map_data):
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        new_models = []
        for db_map, items in db_map_data.items():
            entity_ids_per_class_id = self._entity_ids_per_class_id(items)
            for entity_class_id, ids in entity_ids_per_class_id.items():
                model = self._single_model_type(self, self.header, self.db_mngr, db_map, entity_class_id, lazy=False)
                model.reset_model(ids)
                single_row_map = super()._row_map_for_model(model)  # NOTE: super() prevents filtering
                self._insert_single_row_map(single_row_map)
                new_models.append(model)
        pos = len(self.single_models)
        self.sub_models[pos:pos] = new_models
        self.empty_model.receive_parameter_data_added(db_map_data)

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

    def value_name(self, index):
        item = self.db_item(index)
        if item is None:
            return ""
        entity_name_key = {
            "parameter definition": {
                "object class": "object_class_name",
                "relationship class": "relationship_class_name",
            },
            "parameter value": {"object class": "object_name", "relationship class": "object_name_list"},
        }[self.item_type][self.entity_class_type]
        entity_name = item[entity_name_key].replace(",", self.db_mngr._GROUP_SEP)
        return entity_name + " - " + item["parameter_name"]


class CompoundObjectParameterMixin:
    """Implements the interface for populating and filtering a compound object parameter model."""

    @property
    def entity_class_type(self):
        return "object class"

    def _get_entity_classes(self, db_map):
        return self.db_mngr.get_object_classes(db_map)


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def _get_entity_classes(self, db_map):
        return self.db_mngr.get_relationship_classes(db_map)


class CompoundParameterDefinitionMixin:
    """Handles signals from db mngr for parameter definition models."""

    @property
    def item_type(self):
        return "parameter definition"

    def receive_parameter_definition_tags_set(self, db_map_data):
        self._emit_data_changed_for_column("parameter_tag_list")


class CompoundParameterValueMixin:
    """Handles signals from db mngr for parameter value models."""

    @property
    def item_type(self):
        return "parameter value"

    @property
    def entity_type(self):
        """Returns the entity type, either 'object' or 'relationship'
        Used by update_single_main_filter.

        Returns:
            str
        """
        raise NotImplementedError()

    def update_single_main_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_main_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_entity_ids",
            self.parent().selected_ent_ids[self.entity_type].get((model.db_map, model.entity_class_id), set()),
        )
        return a or b


class CompoundObjectParameterDefinitionModel(
    CompoundObjectParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter definition models
    and one empty object parameter definition model.
    """

    def _make_header(self):
        return [
            "object_class_name",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "description",
            "database",
        ]


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter definition models
    and one empty relationship parameter definition model.
    """

    def _make_header(self):
        return [
            "relationship_class_name",
            "object_class_name_list",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "description",
            "database",
        ]


class CompoundObjectParameterValueModel(
    CompoundObjectParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter value models
    and one empty object parameter value model.
    """

    def _make_header(self):
        return ["object_class_name", "object_name", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "object"


class CompoundRelationshipParameterValueModel(
    CompoundRelationshipParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter value models
    and one empty relationship parameter value model.
    """

    def _make_header(self):
        return ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "relationship"
