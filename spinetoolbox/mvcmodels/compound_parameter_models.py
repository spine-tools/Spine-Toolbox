######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from PySide2.QtCore import Qt, Signal, Slot, QModelIndex
from PySide2.QtGui import QFont, QIcon
from ..helpers import busy_effect, rows_to_row_count_tuples
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
    remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): the parent QObject, an instance of TreeViewForm or GraphViewForm
            db_mngr (SpineDBManager): a manager for the given db_maps
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._auto_filter = dict()
        self._selected_entity_class_ids = {}
        self.connect_db_mngr_signals()

    @property
    def entity_class_type(self):
        """Either 'object class' or 'relationship class'"""
        raise NotImplementedError()

    @property
    def item_type(self):
        """Either 'parameter definition' or 'parameter value'"""
        raise NotImplementedError()

    @property
    def _single_model_type(self):
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
        return {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.entity_class_type
        ]

    def connect_db_mngr_signals(self):
        """Connect signals from database manager.
        Reimplement in subclasses.
        """

    def _models_with_db_map(self, db_map):
        """Returns a collection of models having the given db_map."""
        return [m for m in self.single_models if m.db_map == db_map]

    @Slot("QVariant")
    def receive_entity_classes_removed(self, db_map_data):
        """Runs entity classes are removed. Remove submodels for those entity classes."""
        self.layoutAboutToBeChanged.emit()
        for db_map, data in db_map_data.items():
            ids = {x["id"] for x in data}
            for model in self._models_with_db_map(db_map):
                if model.entity_class_id in ids:
                    self.sub_models.remove(model)
                    if not model.canFetchMore(QModelIndex()):
                        self._fetched_count -= 1
        self.do_refresh()
        self.layoutChanged.emit()

    @Slot("QVariant")
    def receive_parameter_data_updated(self, db_map_data):
        """Runs when either parameter definitions or values are updated."""
        self._emit_data_changed_for_column("parameter_name")
        # TODO: parameter definition names aren't refreshed unless we emit dataChanged,
        # whereas entity and class names don't need it. Why?

    @Slot("QVariant")
    def receive_parameter_data_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed."""
        self.layoutAboutToBeChanged.emit()
        for db_map, items in db_map_data.items():
            grouped_ids = dict()
            for item in items:
                entity_class_id = item.get(self._entity_class_id_key)
                if not entity_class_id:
                    continue
                grouped_ids.setdefault(entity_class_id, set()).add(item["id"])
            for model in self._models_with_db_map(db_map):
                removed_ids = grouped_ids.get(model.entity_class_id)
                if not removed_ids:
                    continue
                removed_rows = [row for row in range(model.rowCount()) if model._main_data[row] in removed_ids]
                for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
                    del model._main_data[row : row + count]
        self.do_refresh()
        self.layoutChanged.emit()

    @Slot("QVariant")
    def receive_parameter_data_added(self, db_map_data):
        """Runs when either parameter definitions or values are added."""
        new_models = []
        for db_map, items in db_map_data.items():
            grouped_ids = dict()
            for item in items:
                entity_class_id = item.get(self._entity_class_id_key)
                if not entity_class_id:
                    continue
                grouped_ids.setdefault(entity_class_id, []).append(item["id"])
            for entity_class_id, ids in grouped_ids.items():
                model = self._single_model_type(self, self.header, self.db_mngr, db_map, entity_class_id, lazy=False)
                model.reset_model(ids)
                self._handle_single_model_reset(model)
                new_models.append(model)
        pos = len(self.single_models)
        self.sub_models[pos:pos] = new_models

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Use italic font for columns having an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if role == Qt.FontRole and orientation == Qt.Horizontal and self._auto_filter.get(section):
            return italic_font
        return super().headerData(section, orientation, role)

    def _get_entity_classes(self, db_map):
        """Returns entity classes for creating the different single models."""
        raise NotImplementedError()

    def _create_single_models(self):
        """Returns a list of single models."""
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
        """Returns an empty model."""
        return self._empty_model_type(self, self.header, self.db_mngr)

    def filter_accepts_model(self, model):
        """Returns True if the given model should be included in the compound model, otherwise returns False.
        """
        if not model.can_be_filtered:
            return True
        if not self._selected_entity_class_ids:
            return True
        return model.entity_class_id in self._selected_entity_class_ids.get(model.db_map, set())

    def accepted_single_models(self):
        """Returns a list of accepted single models, for convenience."""
        return [m for m in self.single_models if self.filter_accepts_model(m)]

    @staticmethod
    def _settattr_if_different(obj, attr, val):
        """If the given value is different than the current one, set it and returns True.
        Otherwise returns False. Handy for updating filters.
        """
        curr = getattr(obj, attr)
        if curr != val:
            setattr(obj, attr, val)
            return True
        return False

    def update_filter(self):
        """Update filter."""
        updated = self.update_compound_filter()
        for model in self.single_models:
            updated |= self.update_single_model_filter(model)
        if updated:
            self.refresh()

    def update_compound_filter(self):
        """Update the filter."""
        a = False
        if self._auto_filter:
            self._auto_filter.clear()
            a = True
        b = self._settattr_if_different(
            self, "_selected_entity_class_ids", self.parent().selected_entity_class_ids(self.entity_class_type)
        )
        return a or b

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = False
        if model._auto_filter:
            model._auto_filter.clear()
            a = True
        b = self._settattr_if_different(
            model,
            "_selected_param_def_ids",
            self.parent()
            .selected_param_def_ids[self.entity_class_type]
            .get((model.db_map, model.entity_class_id), set()),
        )
        return a or b

    def update_auto_filter(self, column, auto_filter):
        """Updates auto filter for given column.

        Args:
            column (int): the column number
            auto_filter (dict): maps entity ids to a collection of values to be filtered for the column
        """
        self._auto_filter[column] = auto_filter
        updated = False
        for model in self.accepted_single_models():
            updated |= self.update_single_model_auto_filter(model, column)
        if updated:
            self.refresh()

    def update_single_model_auto_filter(self, model, column):
        """Set auto filter values for given column.

        Args:
            model (SingleParameterModel): the model
            column (int): the column number
        """
        values = self._auto_filter[column].get(model.entity_class_id, {})
        if values == model._auto_filter.get(column, {}):
            return False
        model._auto_filter[column] = values
        return True

    def _row_map_for_model(self, model):
        """Returns row map for given model.
        Reimplemented to take filter status into account."""
        if not self.filter_accepts_model(model):
            return []
        return [(model, i) for i in model.accepted_rows()]

    @busy_effect
    def auto_filter_menu_data(self, column):
        """Returns auto filter menu data for the given column.

        Returns:
            menu_data (list): a list of AutoFilterMenuItem
        """
        auto_filter_vals = dict()
        for model in self.accepted_single_models():
            for row in model.accepted_rows(ignored_columns=[column]):
                value = model.index(row, column).data()
                auto_filter_vals.setdefault(value, set()).add(model.entity_class_id)
        column_auto_filter = self._auto_filter.get(column, {})
        filtered = [val for values in column_auto_filter.values() for val in values]
        return [
            AutoFilterMenuItem(Qt.Checked if value not in filtered else Qt.Unchecked, value, class_ids)
            for value, class_ids in auto_filter_vals.items()
        ]

    def _emit_data_changed_for_column(self, field):
        """Emits data changed for an entire column.
        Used by `rename_` and some `remove_` methods because we're too lazy
        to find out the exact rows that changed.

        Args:
            field (str): the column header
        """
        return
        try:
            column = self.header.index(field)
        except ValueError:
            pass
        else:
            self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])


class CompoundObjectParameterMixin:
    """Implements the interface for populating and filtering a compound object parameter model."""

    @property
    def entity_class_type(self):
        return "object class"

    def connect_db_mngr_signals(self):
        """Connect signals from database manager."""
        super().connect_db_mngr_signals()
        self.db_mngr.object_classes_removed.connect(self.receive_entity_classes_removed)

    def _get_entity_classes(self, db_map):
        """Returns a query of object classes to populate the model."""
        return self.db_mngr.get_object_classes(db_map)


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def connect_db_mngr_signals(self):
        """Connect signals from database manager."""
        super().connect_db_mngr_signals()
        self.db_mngr.relationship_classes_removed.connect(self.receive_entity_classes_removed)

    def _get_entity_classes(self, db_map):
        """Returns a query of relationship classes to populate the model."""
        return self.db_mngr.get_relationship_classes(db_map)


class CompoundParameterDefinitionMixin:
    """Handles signals from db mngr for parameter definition models."""

    @property
    def item_type(self):
        return "parameter definition"

    def connect_db_mngr_signals(self):
        """Connect db manager signals."""
        super().connect_db_mngr_signals()
        self.db_mngr.parameter_definitions_updated.connect(self.receive_parameter_data_updated)
        self.db_mngr.parameter_definitions_removed.connect(self.receive_parameter_data_removed)
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_data_added)


class CompoundParameterValueMixin:
    """Handles signals from db mngr for parameter value models."""

    @property
    def item_type(self):
        return "parameter value"

    @property
    def entity_type(self):
        """Either 'object' or 'relationship', used by update_single_model_filter."""
        raise NotImplementedError()

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_entity_ids",
            self.parent().selected_ent_ids[self.entity_type].get((model.db_map, model.entity_class_id), set()),
        )
        return a or b

    def connect_db_mngr_signals(self):
        """Connect db manager signals."""
        super().connect_db_mngr_signals()
        self.db_mngr.parameter_values_updated.connect(self.receive_parameter_data_updated)
        self.db_mngr.parameter_values_removed.connect(self.receive_parameter_data_removed)
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_data_added)


class CompoundObjectParameterDefinitionModel(
    CompoundObjectParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter definition models
    and one empty object parameter definition model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = [
            "object_class_name",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter definition models
    and one empty relationship parameter definition model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = [
            "relationship_class_name",
            "object_class_name_list",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]


class CompoundObjectParameterValueModel(
    CompoundObjectParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter value models
    and one empty object parameter value model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = ["object_class_name", "object_name", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "object"


class CompoundRelationshipParameterValueModel(
    CompoundRelationshipParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter value models
    and one empty relationship parameter value model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "relationship"
