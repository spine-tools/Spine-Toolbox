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

"""Contains the TreeViewMixin class."""
from PySide6.QtCore import Slot
from .add_items_dialogs import (
    AddEntityClassesDialog,
    AddEntitiesDialog,
    AddEntityGroupDialog,
    ManageElementsDialog,
    ManageMembersDialog,
)
from .edit_or_remove_items_dialogs import (
    EditEntityClassesDialog,
    EditEntitiesDialog,
    RemoveEntitiesDialog,
    SelectSuperclassDialog,
)
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..mvcmodels.alternative_model import AlternativeModel
from ..mvcmodels.scenario_model import ScenarioModel
from ..mvcmodels.entity_tree_models import EntityTreeModel
from ...spine_db_parcel import SpineDBParcel


class TreeViewMixin:
    """Provides object and relationship trees for the Spine db editor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_tree_model = EntityTreeModel(self, self.db_mngr)
        self.alternative_model = AlternativeModel(self, self.db_mngr)
        self.scenario_model = ScenarioModel(self, self.db_mngr)
        self.parameter_value_list_model = ParameterValueListModel(self, self.db_mngr)
        models = (self.entity_tree_model, self.alternative_model, self.scenario_model, self.parameter_value_list_model)
        views = (
            self.ui.treeView_entity,
            self.ui.alternative_tree_view,
            self.ui.scenario_tree_view,
            self.ui.treeView_parameter_value_list,
        )
        for view, model in zip(views, models):
            view.setModel(model)
            view.connect_spine_db_editor(self)
            view.header().setResizeContentsPrecision(self.visible_rows)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        for view in (
            self.ui.treeView_entity,
            self.ui.alternative_tree_view,
            self.ui.scenario_tree_view,
            self.ui.treeView_parameter_value_list,
        ):
            view.model().db_maps = self.db_maps
            view.model().build_tree()
            for item in view.model().visit_all():
                index = view.model().index_from_item(item)
                view.expand(index)

    @staticmethod
    def _db_map_items(indexes):
        """Groups items from given tree indexes by db map.

        Returns:
            dict: lists of dictionary items keyed by DiffDatabaseMapping
        """
        d = {}
        for index in indexes:
            if index.model() is None:
                continue
            item = index.model().item_from_index(index)
            if item.item_type == "root":
                continue
            for db_map in item.db_maps:
                d.setdefault(db_map, []).append(item.db_map_data(db_map))
        return d

    def _db_map_ids(self, indexes):
        return self.db_mngr.db_map_ids(self._db_map_items(indexes))

    def _db_map_class_ids(self, indexes):
        return self.db_mngr.db_map_class_ids(self._db_map_items(indexes))

    def export_selected(self, selected_indexes):
        """Exports data from given indexes in the entity tree."""
        parcel = SpineDBParcel(self.db_mngr)
        ent_cls_inds = set(selected_indexes.get("entity_class", {}).keys())
        ent_inds = set(selected_indexes.get("entity", {}).keys())
        db_map_ent_cls_ids = self._db_map_ids(ent_cls_inds)
        db_map_ent_ids = self._db_map_ids(ent_inds)
        parcel.full_push_entity_class_ids(db_map_ent_cls_ids)
        parcel.full_push_entity_ids(db_map_ent_ids)
        self.export_data(parcel.data)

    def show_add_entity_classes_form(self, parent_item):
        """Shows dialog to add new entity classes."""
        dialog = AddEntityClassesDialog(self, parent_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_add_entities_form(self, parent_item):
        """Shows dialog to add new entities."""
        dialog = AddEntitiesDialog(self, parent_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_add_entity_group_form(self, entity_class_item):
        """Shows dialog to add new entity group."""
        dialog = AddEntityGroupDialog(self, entity_class_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_manage_members_form(self, entity_item):
        """Shows dialog to manage an entity group."""
        dialog = ManageMembersDialog(self, entity_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_manage_elements_form(self, parent_item):
        if not parent_item.display_id[1]:  # Don't show for 0-dimensional entity classes
            return
        dialog = ManageElementsDialog(self, parent_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_select_superclass_form(self, entity_class_item):
        dialog = SelectSuperclassDialog(self, entity_class_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def edit_entity_tree_items(self, selected_indexes):
        """Starts editing given indexes."""
        ent_cls_items = {ind.internalPointer() for ind in selected_indexes.get("entity_class", {})}
        ent_items = {ind.internalPointer() for ind in selected_indexes.get("entity", {})}
        self.show_edit_entity_classes_form(ent_cls_items)
        self.show_edit_entities_form(ent_items)

    def show_edit_entity_classes_form(self, items):
        if not items:
            return
        dialog = EditEntityClassesDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_entities_form(self, items):
        if not items:
            return
        items_by_class = {}
        for item in items:
            data = item.db_map_data(item.first_db_map)
            class_key = tuple(data[k] for k in ["entity_class_name", "dimension_name_list", "superclass_name"])
            items_by_class.setdefault(class_key, set()).add(item)
        for class_key, classed_items in items_by_class.items():
            dialog = EditEntitiesDialog(self, self.db_mngr, classed_items, class_key)
            dialog.show()

    @Slot(dict)
    def remove_entity_tree_items(self, selected_indexes):
        """Shows form to remove items from object treeview."""
        selected = {
            item_type: [ind.model().item_from_index(ind) for ind in indexes]
            for item_type, indexes in selected_indexes.items()
        }
        self.show_remove_entity_tree_items_form(selected)

    def show_remove_entity_tree_items_form(self, selected):
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()
