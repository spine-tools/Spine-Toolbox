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
from PySide6.QtCore import QEvent, QItemSelection, Qt, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QTreeView
from ...spine_db_parcel import SpineDBParcel
from ..mvcmodels.alternative_model import AlternativeModel
from ..mvcmodels.entity_tree_models import EntityTreeModel, group_items_by_db_map
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..mvcmodels.scenario_model import ScenarioModel
from .add_items_dialogs import (
    AddEntitiesDialog,
    AddEntityClassesDialog,
    AddEntityGroupDialog,
    ManageElementsDialog,
    ManageMembersDialog,
)
from .edit_or_remove_items_dialogs import (
    EditEntitiesDialog,
    EditEntityClassesDialog,
    RemoveEntitiesDialog,
    SelectSuperclassDialog,
)


class TreeViewMixin:
    """Provides entity, alternative, scenario and parameter value list trees for the Spine db editor."""

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
        for multiselection_view in (self.ui.treeView_entity, self.ui.alternative_tree_view, self.ui.scenario_tree_view):
            multiselection_view.set_app_settings(self.qsettings)
            multiselection_view.multitree_selection_clearing_requested.connect(self._clear_tree_selections)

    def connect_signals(self):
        """Connects the signals"""
        super().connect_signals()
        self.ui.treeView_entity.selection_export_requested.connect(self._export_selected_entity_tree_items)
        self.ui.treeView_entity.selection_removal_requested.connect(self._remove_entity_tree_items)
        self.ui.treeView_entity.selection_edit_requested.connect(self._edit_entity_tree_items)
        self.entity_tree_model.dataChanged.connect(self._default_row_generator.entity_or_class_updated)
        self.alternative_model.dataChanged.connect(self._default_row_generator.alternative_updated)

    @Slot(QTreeView)
    def _clear_tree_selections(self, requester: QTreeView) -> None:
        for tree_view in (self.ui.treeView_entity, self.ui.alternative_tree_view, self.ui.scenario_tree_view):
            if tree_view is requester:
                continue
            tree_view.selectionModel().clearSelection()

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

    def _db_map_ids(self, indexes):
        return self.db_mngr.db_map_ids(group_items_by_db_map(indexes))

    @Slot()
    def _export_selected_entity_tree_items(self) -> None:
        """Exports data from given indexes in the entity tree."""
        parcel = SpineDBParcel(self.db_mngr)
        db_map_entity_class_ids = {}
        db_map_entity_ids = {}
        for index in self.ui.treeView_entity.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            item = self.entity_tree_model.item_from_index(index)
            if item.item_type == "entity_class":
                for db_map, item_id in item.db_map_ids.items():
                    db_map_entity_class_ids.setdefault(db_map, set()).add(item_id)
            elif item.item_type == "entity":
                for db_map, item_id in item.db_map_ids.items():
                    db_map_entity_ids.setdefault(db_map, set()).add(item_id)
        parcel.full_push_entity_class_ids(db_map_entity_class_ids)
        parcel.full_push_entity_ids(db_map_entity_ids)
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
        dialog = SelectSuperclassDialog(self, entity_class_item.name, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot()
    def _edit_entity_tree_items(self):
        """Starts editing given indexes."""
        entity_class_items = set()
        entity_items = set()
        for index in self.ui.treeView_entity.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            item = self.entity_tree_model.item_from_index(index)
            if item.item_type == "entity_class":
                entity_class_items.add(item)
            elif item.item_type == "entity":
                entity_items.add(item)
        self.show_edit_entity_classes_form(entity_class_items)
        self.show_edit_entities_form(entity_items)

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

    @Slot()
    def _remove_entity_tree_items(self) -> None:
        """Shows form to remove items from object treeview."""
        selected = {}
        for index in self.ui.treeView_entity.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            item = self.entity_tree_model.item_from_index(index)
            selected.setdefault(item.item_type, []).append(item)
        self.show_remove_entity_tree_items_form(selected)

    def show_remove_entity_tree_items_form(self, selected):
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()
