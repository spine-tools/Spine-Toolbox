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
from PySide6.QtCore import QEvent, Qt, Slot
from PySide6.QtGui import QMouseEvent
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
        self.clear_tree_selections = True
        # Filter caches
        self._filter_class_ids = {}  # Class ids from entity class- and entity selections (cascading)
        self._filter_entity_ids = {}  # Entity ids from entity selections
        self._filter_alternative_ids = {}  # Alternative ids
        self._filter_scenario_ids = {}  # Scenario ids by db_map. Each scenario id maps to alternatives sorted by rank.
        self._filter_parameter_value_ids = {}  # Entity ids for currently accepted parameter value rows in tables

    def connect_signals(self):
        """Connects the signals"""
        super().connect_signals()
        self.ui.treeView_entity.tree_selection_changed.connect(self._handle_entity_tree_selection_changed)
        self.ui.alternative_tree_view.alternative_selection_changed.connect(self._handle_alternative_selection_changed)
        self.ui.scenario_tree_view.scenario_selection_changed.connect(
            self._handle_scenario_alternative_selection_changed
        )
        self.entity_alternative_model.dataChanged.connect(self.build_graph)
        self.parameter_value_model.dataChanged.connect(self._refresh_parameters_and_graph)

    def _refresh_parameters_and_graph(self):
        self._update_filter_parameter_value_ids()
        self.build_graph()

    @Slot(dict)
    def _handle_entity_tree_selection_changed(self, selected_indexes):
        entity_indexes = set(selected_indexes.get("entity", {}).keys())
        entity_indexes |= {
            parent
            for parent in (i.parent() for i in entity_indexes)
            if self.entity_tree_model.item_from_index(parent).item_type == "entity"
        }
        entity_class_indexes = set(selected_indexes.get("entity_class", {}).keys()) | {
            parent_ind
            for parent_ind in (ind.parent() for ind in entity_indexes)
            if self.entity_tree_model.item_from_index(parent_ind).item_type == "entity_class"
        }
        self._filter_class_ids = self._db_map_ids(entity_class_indexes)
        self._filter_entity_ids = self.db_mngr.db_map_class_ids(group_items_by_db_map(entity_indexes))
        # View specific stuff:
        self._update_selected_item_type_db_map_ids(selected_indexes)
        self._reset_filters()
        self._set_default_parameter_data(self.ui.treeView_entity.selectionModel().currentIndex())
        self._update_filter_parameter_value_ids()
        self.build_graph()

    @Slot(dict)
    def _handle_alternative_selection_changed(self, selected):
        self._filter_alternative_ids.clear()
        for db_map, alt_ids in selected.items():
            if not alt_ids:
                continue
            self._filter_alternative_ids.setdefault(db_map, set()).update(alt_ids)
        # View specific stuff:
        self._reset_filters()
        self._update_filter_parameter_value_ids()
        self.build_graph()

    @Slot(dict)
    def _handle_scenario_alternative_selection_changed(self, selected_ids):
        self._filter_scenario_ids = selected_ids
        # View specific stuff:
        self._reset_filters()
        self._update_filter_parameter_value_ids()
        self.build_graph()

    def _update_filter_parameter_value_ids(self):
        """Updates the parameter"""
        for db_map in self.db_maps:
            single_models = self.parameter_value_model._models_with_db_map(db_map)
            if not single_models:
                return True
            parameter_value_ids = set()
            for model in single_models:
                for _, row in self.parameter_value_model._row_map_iterator_for_model(model):
                    parameter_value_ids.add(model._db_item(row).get("entity_id"))
            if not parameter_value_ids and db_map in self._filter_parameter_value_ids:
                del self._filter_parameter_value_ids[db_map]
            self._filter_parameter_value_ids[db_map] = parameter_value_ids

    def handle_mousepress(self, tree_view, event):
        """Overrides selection behaviour if the user has selected sticky selection in Settings.
        If sticky selection is enabled, multiple-selection is enabled when selecting items in the Object tree.
        Pressing the Ctrl-button down, enables single selection.

        Args:
            tree_view (QTreeView): The treeview where the mouse click was in.
            event (QMouseEvent): event
        """
        if tree_view == self.ui.treeView_parameter_value_list:
            return event
        self.clear_tree_selections = True
        sticky_selection = self.qsettings.value("appSettings/stickySelection", defaultValue="false")
        if sticky_selection == "false":
            pos = tree_view.viewport().mapFromGlobal(event.globalPos())
            index = tree_view.indexAt(pos)
            modifiers = event.modifiers()
            if modifiers & Qt.ControlModifier:
                self.clear_tree_selections = False
            elif not (tree_view.selectionModel().hasSelection() or index.isValid()):
                # Ensure selection clearing when empty space is clicked on a tree that doesn't have selections.
                self._clear_all_other_selections(tree_view)
            return event
        local_pos = event.position()
        window_pos = event.scenePosition()
        screen_pos = event.globalPosition()
        button = event.button()
        buttons = event.buttons()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            modifiers &= ~Qt.ControlModifier
        else:
            modifiers |= Qt.ControlModifier
            self.clear_tree_selections = False
        source = event.source()
        new_event = QMouseEvent(
            QEvent.MouseButtonPress, local_pos, window_pos, screen_pos, button, buttons, modifiers, source
        )
        return new_event

    def _clear_all_other_selections(self, current):
        """Clears all selections from other tree views except from the current one.

        Args:
            current: the tree where the selection that was made
        """
        for tree in [self.ui.treeView_entity, self.ui.scenario_tree_view, self.ui.alternative_tree_view]:
            if tree != current:
                tree.selectionModel().clearSelection()

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
