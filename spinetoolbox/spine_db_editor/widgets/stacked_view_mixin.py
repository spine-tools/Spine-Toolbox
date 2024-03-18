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
from PySide6.QtCore import Qt, Slot, QModelIndex, QSignalBlocker
from PySide6.QtWidgets import QHeaderView
from PySide6.QtGui import QGuiApplication
from .element_name_list_editor import ElementNameListEditor
from ..mvcmodels.compound_models import (
    CompoundParameterValueModel,
    CompoundParameterDefinitionModel,
    CompoundEntityAlternativeModel,
)
from ...helpers import preferred_row_height, DB_ITEM_SEPARATOR


class StackedViewMixin:
    """
    Provides stacked parameter tables for the Spine db editor.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_class_ids = {}
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}
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
            view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
            horizontal_header = view.horizontalHeader()
            horizontal_header.setSectionsMovable(True)
            view.connect_spine_db_editor(self)

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.alternative_tree_view.alternative_selection_changed.connect(self._handle_alternative_selection_changed)
        self.ui.scenario_tree_view.scenario_selection_changed.connect(
            self._handle_scenario_alternative_selection_changed
        )
        self.ui.treeView_entity.tree_selection_changed.connect(
            self._handle_entity_tree_selection_changed_in_parameter_tables
        )
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
            db_map (DiffDatabaseMapping)
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
                "entity", entity_class_name=entity_class["name"], byname=tuple(entity_byname.split(DB_ITEM_SEPARATOR))
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
            default_data = dict(database=default_db_map.codename)
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

    def clear_all_filters(self):
        for model in self._all_stacked_models:
            model.clear_auto_filter()
        self._filter_class_ids = {}
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}
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
            model.set_filter_alternative_ids(self._filter_alternative_ids)

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

    @Slot(dict)
    def _handle_entity_tree_selection_changed_in_parameter_tables(self, selected_indexes):
        """Resets filter according to entity tree selection."""
        ent_inds = set(selected_indexes.get("entity", {}).keys())
        ent_cls_inds = set(selected_indexes.get("entity_class", {}).keys()) | {
            parent_ind
            for parent_ind in (ind.parent() for ind in ent_inds)
            if self.entity_tree_model.item_from_index(parent_ind).item_type == "entity_class"
        }
        self._filter_class_ids = self._db_map_ids(ent_cls_inds)
        self._filter_entity_ids = self._db_map_class_ids(ent_inds)
        if Qt.KeyboardModifier.ControlModifier not in QGuiApplication.keyboardModifiers():
            self._filter_alternative_ids.clear()
            self._clear_all_other_selections(self.ui.treeView_entity)
        self._reset_filters()
        self._set_default_parameter_data(self.ui.treeView_entity.selectionModel().currentIndex())

    @Slot(dict)
    def _handle_alternative_selection_changed(self, selected_db_map_alt_ids):
        """Resets filter according to selection in alternative tree view."""
        self._update_alternative_selection(
            selected_db_map_alt_ids, self.ui.scenario_tree_view, self.ui.alternative_tree_view
        )

    @Slot(dict)
    def _handle_scenario_alternative_selection_changed(self, selected_db_map_alt_ids):
        """Resets filter according to selection in scenario tree view."""
        self._update_alternative_selection(
            selected_db_map_alt_ids, self.ui.alternative_tree_view, self.ui.scenario_tree_view
        )

    def _update_alternative_selection(self, selected_db_map_alt_ids, other_tree_view, this_tree_view):
        """Combines alternative selections from alternative and scenario tree views.

        Args:
            selected_db_map_alt_ids (dict): mapping from database map to set of alternative ids
            other_tree_view (AlternativeTreeView or ScenarioTreeView): tree view whose selection didn't change
            this_tree_view (AlternativeTreeView or ScenarioTreeView): tree view whose selection changed
        """
        if Qt.KeyboardModifier.ControlModifier in QGuiApplication.keyboardModifiers():
            alternative_ids = {
                db_map: alt_ids.copy() for db_map, alt_ids in other_tree_view.selected_alternative_ids.items()
            }
        else:
            alternative_ids = {}
            self._clear_all_other_selections(this_tree_view)
            self._filter_class_ids.clear()
            self._filter_entity_ids.clear()
        for db_map, alt_ids in selected_db_map_alt_ids.items():
            alternative_ids.setdefault(db_map, set()).update(alt_ids)
        self._filter_alternative_ids = alternative_ids
        self._reset_filters()

    def _clear_all_other_selections(self, current, other=None):
        """Clears all the other selections besides the one that was just made.

        Args:
            current: the tree where the selection that was just made
            other (optional): other optional tree
        """
        trees = [self.ui.treeView_entity, self.ui.scenario_tree_view, self.ui.alternative_tree_view]
        for tree in trees:
            if tree not in (current, other):
                with QSignalBlocker(tree) as _:
                    tree.selectionModel().clearSelection()

    def tear_down(self):
        if not super().tear_down():
            return False
        for model in self._all_stacked_models:
            model.stop_invalidating_filter()
        return True
