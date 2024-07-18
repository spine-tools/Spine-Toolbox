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

"""Contains the StackedViewMixin class."""
from PySide6.QtCore import QItemSelection, QModelIndex, Qt, Slot
from ...helpers import DB_ITEM_SEPARATOR, preferred_row_height
from ..mvcmodels.compound_models import (
    CompoundEntityAlternativeModel,
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from .element_name_list_editor import ElementNameListEditor


class StackedViewMixin:
    """
    Provides stacked parameter tables for the Spine db editor.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameter_value_model = CompoundParameterValueModel(self, self.db_mngr)
        self.parameter_definition_model = CompoundParameterDefinitionModel(self, self.db_mngr)
        self.entity_alternative_model = CompoundEntityAlternativeModel(self, self.db_mngr)
        self._all_stacked_models = {
            self.parameter_value_model: self.ui.tableView_parameter_value,
            self.parameter_definition_model: self.ui.tableView_parameter_definition,
            self.entity_alternative_model: self.ui.tableView_entity_alternative,
        }
        for model, view in self._all_stacked_models.items():
            view.setModel(model)
            dock = view.parent().parent()
            model.dock = dock
            view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
            horizontal_header = view.horizontalHeader()
            horizontal_header.setSectionsMovable(True)
            view.connect_spine_db_editor(self)

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.treeView_entity.model().dataChanged.connect(self._update_empty_rows)
        self.ui.graphicsView.graph_selection_changed.connect(self._handle_graph_selection_changed)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        for model in self._all_stacked_models:
            model.reset_db_maps(self.db_maps)
            model.init_model()
        self._set_default_parameter_data()

    @Slot(QModelIndex, object, object)
    def show_element_name_list_editor(self, index, entity_class_id, db_map):
        """Shows the element name list editor.

        Args:
            index (QModelIndex)
            entity_class_id (int)
            db_map (DatabaseMapping)
        """
        entity_class = self.db_mngr.get_item(db_map, "entity_class", entity_class_id)
        dimension_id_list = entity_class.get("dimension_id_list", ())
        dimension_names = []
        entity_byname_lists = []
        for id_ in dimension_id_list:
            dimension_name = self.db_mngr.get_item(db_map, "entity_class", id_).get("name")
            entity_name_list = [
                x["entity_byname"]
                for k in ("class_id", "superclass_id")
                for x in self.db_mngr.get_items_by_field(db_map, "entity", k, id_)
            ]
            dimension_names.append(dimension_name)
            entity_byname_lists.append(entity_name_list)
        entity_byname = index.data(Qt.ItemDataRole.EditRole)
        if entity_byname is not None:
            entity = db_map.get_item(
                "entity",
                entity_class_name=entity_class["name"],
                entity_byname=tuple(entity_byname.split(DB_ITEM_SEPARATOR)),
            )
            current_element_byname_list = entity["element_byname_list"] if entity else []
        else:
            current_element_byname_list = []
        editor = ElementNameListEditor(self, index, dimension_names, entity_byname_lists, current_element_byname_list)
        editor.show()

    def _set_default_parameter_data(self, index=None):
        """Sets default rows for parameter models according to given index.

        Args:
            index (QModelIndex): an index of the entity tree
        """
        if index is None or not index.isValid():
            default_db_map = next(iter(self.db_maps))
            default_data = {"database": default_db_map.codename}
        else:
            item = index.model().item_from_index(index)
            default_db_map = item.first_db_map
            default_data = item.default_parameter_data()
        self.set_default_parameter_data(default_data, default_db_map)

    def set_default_parameter_data(self, default_data, default_db_map):
        for model in self._all_stacked_models:
            model.empty_model.db_map = default_db_map
            model.empty_model.set_default_row(**default_data)
            model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

    @Slot(QModelIndex, QModelIndex, list)
    def _update_empty_rows(self, top_left, bottom_right, roles):
        """Updates empty default data on empty rows if relevant entity (class) name has changed.

        Args:
            top_left (QModelIndex): top left corner of changed data in Entity tree
            bottom_right (QModelIndex): bottom right corner of changed data in Entity tree
            roles (list of Qt.ItemDataRole): affected item data roles
        """
        entity_selection_model = self.ui.treeView_entity.selectionModel()
        current_entity_index = entity_selection_model.currentIndex()
        if not current_entity_index.isValid() or (roles and Qt.ItemDataRole.DisplayRole not in roles):
            return
        selection = QItemSelection(top_left, bottom_right)
        if selection.contains(current_entity_index):
            self._set_default_parameter_data(current_entity_index)

    def clear_all_filters(self):
        for model in self._all_stacked_models:
            model.clear_auto_filter()
        self._filter_class_ids = {}
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}
        self._filter_scenario_ids = {}
        self._reset_filters()
        trees = [self.ui.treeView_entity, self.ui.scenario_tree_view, self.ui.alternative_tree_view]
        for tree in trees:
            tree.selectionModel().clearSelection()

    def _reset_filters(self):
        """Resets filters."""
        for model in self._all_stacked_models:
            model.set_filter_class_ids(self._filter_class_ids)
        for model in (self.parameter_value_model, self.entity_alternative_model):
            model.set_filter_entity_ids(self._filter_entity_ids)
            alternatives = self.get_all_alternatives()
            model.set_filter_alternative_ids(alternatives)

    def get_all_alternatives(self):
        """Combines alternative ids from Scenario and Alternative tree selections."""
        all_alternatives = self._filter_alternative_ids.copy()
        for db_map, scenarios in self._filter_scenario_ids.get("scenario", {}).items():
            for _, alternatives in scenarios.items():
                all_alternatives.setdefault(db_map, set()).update(alternatives)
        for db_map, alternatives in self._filter_scenario_ids.get("scenario_alternative", {}).items():
            all_alternatives.setdefault(db_map, set()).update(alternatives)
        return all_alternatives

    @Slot(list)
    def _handle_graph_selection_changed(self, selected_items):
        """Resets filter according to graph selection."""
        active_items = {}
        for x in selected_items:
            for db_map in x.db_maps:
                active_items.setdefault(db_map, []).extend(x.db_items(db_map))
        self._filter_class_ids = {}
        for db_map, items in active_items.items():
            self._filter_class_ids.setdefault(db_map, set()).update({x["class_id"] for x in items})
        self._filter_entity_ids = self.db_mngr.db_map_class_ids(active_items)
        self._reset_filters()

    def tear_down(self):
        if not super().tear_down():
            return False
        for model in self._all_stacked_models:
            model.stop_invalidating_filter()
        return True
