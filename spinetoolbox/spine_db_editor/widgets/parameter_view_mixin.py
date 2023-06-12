######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the ParameterViewMixin class.
"""

from PySide6.QtCore import Qt, Slot, QModelIndex, QSignalBlocker
from PySide6.QtWidgets import QHeaderView
from PySide6.QtGui import QGuiApplication
from .object_name_list_editor import ObjectNameListEditor
from ..mvcmodels.compound_parameter_models import (
    CompoundObjectParameterDefinitionModel,
    CompoundObjectParameterValueModel,
    CompoundRelationshipParameterDefinitionModel,
    CompoundRelationshipParameterValueModel,
)
from ...helpers import preferred_row_height, DB_ITEM_SEPARATOR


class ParameterViewMixin:
    """
    Provides stacked parameter tables for the Spine db editor.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_class_ids = {}
        self._filter_entity_ids = {}
        self._filter_class_ids_in_cls = {}
        self._filter_class_ids_in_rel = {}
        self._filter_entity_ids_in_cls = {}
        self._filter_entity_ids_in_rel = {}
        self._filter_alternative_ids = {}
        self.object_parameter_value_model = CompoundObjectParameterValueModel(self, self.db_mngr)
        self.relationship_parameter_value_model = CompoundRelationshipParameterValueModel(self, self.db_mngr)
        self.object_parameter_definition_model = CompoundObjectParameterDefinitionModel(self, self.db_mngr)
        self.relationship_parameter_definition_model = CompoundRelationshipParameterDefinitionModel(self, self.db_mngr)
        self._parameter_models = (
            self.object_parameter_value_model,
            self.relationship_parameter_value_model,
            self.object_parameter_definition_model,
            self.relationship_parameter_definition_model,
        )
        self._parameter_value_models = (self.object_parameter_value_model, self.relationship_parameter_value_model)
        views = (
            self.ui.tableView_object_parameter_value,
            self.ui.tableView_relationship_parameter_value,
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
        )
        for view, model in zip(views, self._parameter_models):
            view.setModel(model)
            view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
            view.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
            view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            view.horizontalHeader().setStretchLastSection(True)
            view.horizontalHeader().setSectionsMovable(True)
            view.connect_spine_db_editor(self)

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.alternative_tree_view.alternative_selection_changed.connect(self._handle_alternative_selection_changed)
        self.ui.scenario_tree_view.scenario_selection_changed.connect(
            self._handle_scenario_alternative_selection_changed
        )
        self.ui.treeView_object.object_selection_changed.connect(self._handle_entity_tree_selection_changed)
        self.ui.treeView_relationship.relationship_selection_changed.connect(self._handle_entity_tree_selection_changed)
        self.ui.graphicsView.graph_selection_changed.connect(self._handle_graph_selection_changed)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_parameter_value_model.db_maps = self.db_maps
        self.relationship_parameter_value_model.db_maps = self.db_maps
        self.object_parameter_definition_model.db_maps = self.db_maps
        self.relationship_parameter_definition_model.db_maps = self.db_maps
        self.object_parameter_value_model.init_model()
        self.object_parameter_definition_model.init_model()
        self.relationship_parameter_value_model.init_model()
        self.relationship_parameter_definition_model.init_model()
        self._set_default_parameter_data()

    @Slot(QModelIndex, int, object)
    def show_object_name_list_editor(self, index, rel_cls_id, db_map):
        """Shows the object names list editor.

        Args:
            index (QModelIndex)
            rel_cls_id (int)
            db_map (DiffDatabaseMapping)
        """
        relationship_class = self.db_mngr.get_item(db_map, "relationship_class", rel_cls_id, only_visible=False)
        object_class_id_list = relationship_class.get("object_class_id_list")
        object_class_names = []
        object_names_lists = []
        for id_ in object_class_id_list:
            object_class_name = self.db_mngr.get_item(db_map, "object_class", id_, only_visible=False).get("name")
            object_names_list = [
                x["name"]
                for x in self.db_mngr.get_items_by_field(db_map, "object", "class_id", id_, only_visible=False)
            ]
            object_class_names.append(object_class_name)
            object_names_lists.append(object_names_list)
        object_name_list = index.data(Qt.ItemDataRole.EditRole)
        try:
            current_object_names = object_name_list.split(DB_ITEM_SEPARATOR)
        except AttributeError:
            # Gibberish
            current_object_names = []
        editor = ObjectNameListEditor(self, index, object_class_names, object_names_lists, current_object_names)
        editor.show()

    def _set_default_parameter_data(self, index=None):
        """Sets default rows for parameter models according to given index.

        Args:
            index (QModelIndex): and index of the object or relationship tree
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
        for model in self._parameter_models:
            model.empty_model.db_map = default_db_map
            model.empty_model.set_default_row(**default_data)
            model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

    def clear_all_filters(self):
        for model in self._parameter_models:
            model.clear_auto_filter()
        for model in self._parameter_value_models:
            model.clear_auto_filter()
        self._filter_class_ids = {}
        self._filter_entity_ids = {}
        self._filter_alternative_ids = {}
        self._reset_filters()

    def _reset_filters(self):
        """Resets filters."""
        for model in self._parameter_models:
            model.set_filter_class_ids(self._filter_class_ids)
        for model in self._parameter_value_models:
            model.set_filter_entity_ids(self._filter_entity_ids)
            model.set_filter_alternative_ids(self._filter_alternative_ids)

    @Slot(dict)
    def _handle_graph_selection_changed(self, selected_items):
        """Resets filter according to graph selection."""
        obj_items = selected_items["object"]
        rel_items = selected_items["relationship"]
        active_objs = {}
        for x in obj_items:
            for db_map in x.db_maps:
                active_objs.setdefault(db_map, []).append(x.db_representation(db_map))
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr.db_map_ids(active_objs))
        active_rels = {}
        for x in rel_items:
            for db_map in x.db_maps:
                active_rels.setdefault(db_map, []).append(x.db_representation(db_map))
        for db_map, rels in cascading_rels.items():
            active_rels.setdefault(db_map, []).extend(rels)
        self._filter_class_ids = {}
        for db_map, items in active_objs.items():
            self._filter_class_ids.setdefault(db_map, set()).update({x["class_id"] for x in items})
        for db_map, items in active_rels.items():
            self._filter_class_ids.setdefault(db_map, set()).update({x["class_id"] for x in items})
        self._filter_entity_ids = self.db_mngr.db_map_class_ids(active_objs)
        self._filter_entity_ids.update(self.db_mngr.db_map_class_ids(active_rels))
        self._reset_filters()

    def _handle_object_tree_selection_changed(self, selected_indexes):
        """Resets filter according to object tree selection."""
        obj_cls_inds = set(selected_indexes.get("object_class", {}).keys())
        obj_inds = set(selected_indexes.get("object", {}).keys())
        rel_cls_inds = set(selected_indexes.get("relationship_class", {}).keys())
        active_rel_inds = set(selected_indexes.get("relationship", {}).keys())
        # Compute active indexes by merging in the parents from lower levels recursively
        active_rel_cls_inds = rel_cls_inds | {ind.parent() for ind in active_rel_inds}
        active_obj_inds = obj_inds | {ind.parent() for ind in active_rel_cls_inds}
        active_obj_cls_inds = obj_cls_inds | {ind.parent() for ind in active_obj_inds}
        filter_class_ids = self._db_map_ids(active_obj_cls_inds | active_rel_cls_inds)
        filter_entity_ids = self._db_map_class_ids(active_obj_inds | active_rel_inds)
        # Cascade (note that we carefully select where to cascade from, to avoid 'circularity')
        obj_cls_ids = self._db_map_ids(obj_cls_inds | {ind.parent() for ind in obj_inds})
        obj_ids = self._db_map_ids(obj_inds | {ind.parent() for ind in rel_cls_inds})
        cascading_rel_clss = self.db_mngr.find_cascading_relationship_classes(obj_cls_ids, only_visible=False)
        cascading_rels = self.db_mngr.find_cascading_relationships(obj_ids, only_visible=False)
        for db_map, ids in self.db_mngr.db_map_ids(cascading_rel_clss).items():
            filter_class_ids.setdefault(db_map, set()).update(ids)
        for (db_map, class_id), ids in self.db_mngr.db_map_class_ids(cascading_rels).items():
            filter_entity_ids.setdefault((db_map, class_id), set()).update(ids)
        return filter_class_ids, filter_entity_ids

    def _handle_relationship_tree_selection_changed(self, selected_indexes):
        """Resets filter according to relationship tree selection."""
        rel_cls_inds = set(selected_indexes.get("relationship_class", {}).keys())
        active_rel_inds = set(selected_indexes.get("relationship", {}).keys())
        active_rel_cls_inds = rel_cls_inds | {ind.parent() for ind in active_rel_inds}
        return self._db_map_ids(active_rel_cls_inds), self._db_map_class_ids(active_rel_inds)

    @Slot(dict, bool)
    def _handle_entity_tree_selection_changed(self, selected_indexes, object_tree):
        """Combines object and relationship selections from object and relationship tree views.

        Args:
            selected_indexes (dict): mapping from database map to set of alternative ids
            object_tree (bool): if True, the selection was made in the Object tree, else in the Relationship tree
        """
        if Qt.KeyboardModifier.ControlModifier not in QGuiApplication.keyboardModifiers():
            self._clear_all_other_selections(self.ui.treeView_object, self.ui.treeView_relationship)
            if object_tree:
                self._filter_class_ids_in_rel = {}
                self._filter_entity_ids_in_rel = {}
            else:
                self._filter_class_ids_in_cls = {}
                self._filter_entity_ids_in_cls = {}
            self._filter_alternative_ids.clear()
        if object_tree:
            self._filter_class_ids_in_cls, self._filter_entity_ids_in_cls = self._handle_object_tree_selection_changed(
                selected_indexes
            )
            self._set_default_parameter_data(self.ui.treeView_object.selectionModel().currentIndex())
        else:
            (
                self._filter_class_ids_in_rel,
                self._filter_entity_ids_in_rel,
            ) = self._handle_relationship_tree_selection_changed(selected_indexes)
            self._set_default_parameter_data(self.ui.treeView_relationship.selectionModel().currentIndex())
        self._filter_class_ids = self._dict_intersection(self._filter_class_ids_in_cls, self._filter_class_ids_in_rel)
        self._filter_entity_ids = self._dict_intersection(
            self._filter_entity_ids_in_cls, self._filter_entity_ids_in_rel
        )
        self._reset_filters()

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
        trees = [
            self.ui.treeView_object,
            self.ui.scenario_tree_view,
            self.ui.alternative_tree_view,
            self.ui.treeView_relationship,
        ]
        for tree in trees:
            if tree != current and tree != other:
                with QSignalBlocker(tree) as _:
                    tree.selectionModel().clearSelection()

    @staticmethod
    def _dict_intersection(dict1, dict2):
        """Creates a dictionary from two dicts that is either their union or intersection based on their keys."""
        intersection_dict = {}
        for key1, value1 in dict1.items():
            for key2, value2 in dict2.items():
                if key2 == key1:
                    intersection_dict = {key2: value2 & value1}
                else:
                    intersection_dict.update(dict1)
                    intersection_dict.update(dict2)
        if not intersection_dict:
            intersection_dict = dict1 or dict2
        return intersection_dict
