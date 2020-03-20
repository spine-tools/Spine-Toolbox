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
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QFont, QIcon
from ..helpers import rows_to_row_count_tuples
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
        super().__init__(parent=parent, header=self._make_header())
        self._parent = parent
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._accepted_entity_class_ids = {}  # Accepted by main filter
        self.remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self._auto_filter_menus = {}
        self._auto_filter_menu_data = dict()  # Maps field to value to list of (db map, entity id, item id)
        self._inv_auto_filter_menu_data = dict()  # Maps field to (db map, entity id, item id) to value
        self._auto_filter = dict()  # Maps field to db map, to entity id, to *accepted* item ids

    def _make_header(self):
        raise NotImplementedError()

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

    def init_model(self):
        """Initializes the model."""
        super().init_model()
        self._make_auto_filter_menus()

    def _make_auto_filter_menus(self):
        """Makes auto filter menus."""
        self._auto_filter_menus.clear()
        self._auto_filter_menu_data.clear()
        self._inv_auto_filter_menu_data.clear()
        for field in self.header:
            # TODO: show_empty=True
            self._auto_filter_menus[field] = menu = ParameterViewFilterMenu(self._parent, self, show_empty=False)
            menu.filterChanged.connect(
                lambda values, has_filter, field=field: self.update_auto_filter(field, values, has_filter)
            )

    def get_auto_filter_menu(self, logical_index):
        """Returns auto filter menu for given logical index from header view.

        Args:
            logical_index (int)

        Returns:
            ParameterViewFilterMenu
        """
        return self._auto_filter_menus.get(self.header[logical_index], None)

    def _add_data_to_filter_menus(self, sub_model):
        """Adds data of given sub-model to filter menus.

        Args:
            sub_model (SingleParameterModel)
        """
        db_items = sub_model.db_items()
        db_map = sub_model.db_map
        self._do_add_data_to_filter_menus(db_map, db_items)

    def _modify_data_in_filter_menus(self, action, db_map, db_items):
        """Modifies data in filter menus.

        Args:
            action (str): either 'add', 'remove', or 'update'
            db_map (DiffDatabaseMapping)
            db_items (list(dict))
        """

        def get_value_to_remove(db_map, db_item, field, field_menu_data, inv_field_menu_data):
            if action not in ("remove", "update"):
                return None
            entity_class_id = db_item.get(self._entity_class_id_key)
            item_id = db_item["id"]
            identifier = (db_map, entity_class_id, item_id)
            old_value = inv_field_menu_data.pop(identifier)
            old_items = field_menu_data[old_value]
            old_items.remove(identifier)
            if not old_items:
                del field_menu_data[old_value]
                return old_value

        def get_value_to_add(db_map, db_item, field, field_menu_data, inv_field_menu_data):
            if action not in ("add", "update"):
                return None
            entity_class_id = db_item.get(self._entity_class_id_key)
            item_id = db_item["id"]
            identifier = (db_map, entity_class_id, item_id)
            value = db_map.codename if field == "database" else db_item[field]
            inv_field_menu_data[identifier] = value
            if value not in field_menu_data:
                field_menu_data[value] = [identifier]
                return value
            field_menu_data[value].append(identifier)

        for field, menu in self._auto_filter_menus.items():
            values_to_add = list()
            values_to_remove = list()
            field_menu_data = self._auto_filter_menu_data.setdefault(field, {})
            inv_field_menu_data = self._inv_auto_filter_menu_data.setdefault(field, {})
            for db_item in db_items:
                to_remove = get_value_to_remove(db_map, db_item, field, field_menu_data, inv_field_menu_data)
                to_add = get_value_to_add(db_map, db_item, field, field_menu_data, inv_field_menu_data)
                if to_remove is not None:
                    values_to_remove.append(to_remove)
                if to_add is not None:
                    values_to_add.append(to_add)
            if values_to_remove:
                menu.remove_items_from_filter_list(values_to_remove)
            if values_to_add:
                menu.add_items_to_filter_list(values_to_add)

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

    def _create_single_models(self):
        """Returns a list of single models for this compound model, one for each entity class in each database.

        Returns:
            list
        """
        return []

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
            self, "_accepted_entity_class_ids", self._parent.selected_entity_class_ids(self.entity_class_type)
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
        selected_param_def_ids = self._parent.selected_param_def_ids[self.entity_class_type]
        if selected_param_def_ids is not None:
            selected_param_def_ids = selected_param_def_ids.get((model.db_map, model.entity_class_id), set())
        b = self._settattr_if_different(model, "_selected_param_def_ids", selected_param_def_ids)
        return a or b

    def update_auto_filter(self, field, valid_values, has_filter):
        """Updates and applies the auto filter.

        Args:
            field (str): the field name
            valid_values (list(str)): accepted values for the field
            has_filter (bool)
        """
        field_menu_data = self._auto_filter_menu_data[field]
        auto_filter = self._build_auto_filter(field_menu_data, valid_values, has_filter)
        updated = self.update_compound_auto_filter(field, auto_filter)
        for model in self.accepted_single_models():
            updated |= self.update_single_auto_filter(model, field)
        if updated:
            self.refresh()

    @staticmethod
    def _build_auto_filter(field_menu_data, valid_values, has_filter):
        if not has_filter:
            return {}  # All-pass
        if not valid_values:
            return None  # You shall not pass
        auto_filter = {}
        for value in valid_values:
            for db_map, entity_class_id, item_id in field_menu_data[value]:
                auto_filter.setdefault(db_map, {}).setdefault(entity_class_id, []).append(item_id)
        return auto_filter

    def update_compound_auto_filter(self, field, auto_filter):
        """Updates the auto filter for given column in the compound model.

        Args:
            field (str): the field name
            auto_filter (dict): maps tuple (database map, entity class id) to list of accepted ids for the field
        """
        if self._auto_filter.setdefault(field, {}) == auto_filter:
            return False
        self._auto_filter[field] = auto_filter
        return True

    def update_single_auto_filter(self, model, field):
        """Updates the auto filter for given column in the given single model.

        Args:
            model (SingleParameterModel): the model
            field (str): the field name

        Returns:
            bool: True if the auto-filtered values were updated, None otherwise
        """
        values = self._auto_filter[field].get(model.db_map, {}).get(model.entity_class_id, {})
        if values == model._auto_filter.get(field, {}):
            return False
        model._auto_filter[field] = values
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

    def _items_per_class(self, items):
        """Returns a dict mapping entity class ids to a set of items.

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
            d.setdefault(entity_class_id, list()).append(item)
        return d

    def receive_parameter_data_added(self, db_map_data):
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        new_models = []
        for db_map, items in db_map_data.items():
            items_per_class = self._items_per_class(items)
            for entity_class_id, class_items in items_per_class.items():
                ids = [item["id"] for item in class_items]
                model = self._single_model_type(self.header, self.db_mngr, db_map, entity_class_id)
                model.reset_model(ids)
                single_row_map = super()._row_map_for_model(model)  # NOTE: super() is to get all (unfiltered) rows
                self._insert_single_row_map(single_row_map)
                new_models.append(model)
                self._do_add_data_to_filter_menus(db_map, class_items)
        pos = len(self.single_models)
        self.sub_models[pos:pos] = new_models
        self.empty_model.receive_parameter_data_added(db_map_data)

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
        # TODO: parameter definition names aren't refreshed unless we emit dataChanged,
        # whereas entity and class names don't need it. Why?

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
        self.do_refresh()
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


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    @property
    def entity_class_type(self):
        return "relationship class"


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
            self._parent.selected_ent_ids[self.entity_type].get((model.db_map, model.entity_class_id), set()),
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
