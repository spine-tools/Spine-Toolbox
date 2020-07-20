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
Contains the ParameterViewMixin class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QHeaderView
from .toolbars import ParameterTagToolBar
from .object_name_list_editor import ObjectNameListEditor
from ..mvcmodels.compound_parameter_models import (
    CompoundObjectParameterDefinitionModel,
    CompoundObjectParameterValueModel,
    CompoundRelationshipParameterDefinitionModel,
    CompoundRelationshipParameterValueModel,
)
from .manage_items_dialogs import ManageParameterTagsDialog


class ParameterViewMixin:
    """
    Provides stacked parameter tables for the data store form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_class_ids = {}
        self.filter_entity_ids = {}
        self.filter_tag_ids = dict()
        self.tag_filter_class_ids = {}
        self.filter_parameter_ids = {}
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_mngr, *self.db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        self.object_parameter_value_model = CompoundObjectParameterValueModel(self, self.db_mngr, *self.db_maps)
        self.relationship_parameter_value_model = CompoundRelationshipParameterValueModel(
            self, self.db_mngr, *self.db_maps
        )
        self.object_parameter_definition_model = CompoundObjectParameterDefinitionModel(
            self, self.db_mngr, *self.db_maps
        )
        self.relationship_parameter_definition_model = CompoundRelationshipParameterDefinitionModel(
            self, self.db_mngr, *self.db_maps
        )
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
            view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            view.verticalHeader().setDefaultSectionSize(self.default_row_height)
            view.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
            view.horizontalHeader().setSectionsMovable(True)
            view.connect_data_store_form(self)

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.parameter_tag_toolbar.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_object_parameter_value.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_object_parameter_definition.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_parameter_value.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_parameter_definition.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.parameter_tag_toolbar.manage_tags_action_triggered.connect(self.show_manage_parameter_tags_form)
        self.parameter_tag_toolbar.tag_button_toggled.connect(self._handle_tag_button_toggled)
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.set_default_parameter_data)
        self.ui.treeView_relationship.selectionModel().currentChanged.connect(self.set_default_parameter_data)
        self.ui.treeView_object.tree_selection_changed.connect(self._handle_object_tree_selection_changed)
        self.ui.treeView_relationship.tree_selection_changed.connect(self._handle_relationship_tree_selection_changed)
        self.graph_selection_changed.connect(self._handle_graph_selection_changed)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.parameter_tag_toolbar.init_toolbar()
        self.object_parameter_value_model.init_model()
        self.object_parameter_definition_model.init_model()
        self.relationship_parameter_value_model.init_model()
        self.relationship_parameter_definition_model.init_model()
        self.set_default_parameter_data()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    @Slot("QModelIndex", "QVariant")
    def set_parameter_data(self, index, new_value):  # pylint: disable=no-self-use
        """Updates (object or relationship) parameter_definition or value with newly edited data."""
        index.model().setData(index, new_value)

    @Slot("QModelIndex", int, "QVariant")
    def show_object_name_list_editor(self, index, rel_cls_id, db_map):
        """Shows the object names list editor.

        Args:
            index (QModelIndex)
            rel_cls_id (int)
            db_map (DiffDatabaseMapping)
        """
        relationship_class = self.db_mngr.get_item(db_map, "relationship_class", rel_cls_id)
        object_class_id_list = relationship_class.get("object_class_id_list")
        object_class_names = []
        object_names_lists = []
        for id_ in object_class_id_list.split(","):
            id_ = int(id_)
            object_class_name = self.db_mngr.get_item(db_map, "object_class", id_).get("name")
            object_names_list = [x["name"] for x in self.db_mngr.get_items_by_field(db_map, "object", "class_id", id_)]
            object_class_names.append(object_class_name)
            object_names_lists.append(object_names_list)
        object_name_list = index.data(Qt.EditRole)
        try:
            current_object_names = object_name_list.split(",")
        except AttributeError:
            # Gibberish
            current_object_names = []
        editor = ObjectNameListEditor(self, index, object_class_names, object_names_lists, current_object_names)
        editor.show()

    def set_default_parameter_data(self, index=None):
        """Sets default rows for parameter models according to given index.

        Args:
            index (QModelIndex): and index of the object or relationship tree
        """
        if index is None or not index.isValid():
            default_data = dict(database=next(iter(self.db_maps)).codename)
        else:
            default_data = index.model().item_from_index(index).default_parameter_data()

        def set_and_apply_default_rows(model, default_data):
            model.empty_model.set_default_row(**default_data)
            model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

        set_and_apply_default_rows(self.object_parameter_definition_model, default_data)
        set_and_apply_default_rows(self.object_parameter_value_model, default_data)
        set_and_apply_default_rows(self.relationship_parameter_definition_model, default_data)
        set_and_apply_default_rows(self.relationship_parameter_value_model, default_data)

    def _get_filter_class_ids(self):
        """Returns filter class ids by combining filter class ids from entity tree *and* parameter_tag toolbar.

        Returns:
            dict, NoneType: mapping db maps to sets of ids, or None if no filter (none shall pass)
        """
        if self.tag_filter_class_ids is None:
            return None
        filter_class_ids = dict()
        for db_map in self.filter_class_ids.keys() | self.tag_filter_class_ids.keys():
            if db_map not in self.filter_class_ids:
                filter_class_ids[db_map] = self.tag_filter_class_ids[db_map]
            elif db_map not in self.tag_filter_class_ids:
                filter_class_ids[db_map] = self.filter_class_ids[db_map]
            else:
                filter_class_ids[db_map] = self.tag_filter_class_ids[db_map] & self.filter_class_ids[db_map]
        return filter_class_ids

    def reset_filters(self):
        """Resets filters."""
        for model in self._parameter_models:
            model.set_filter_class_ids(self._get_filter_class_ids())
            model.set_filter_parameter_ids(self.filter_parameter_ids)
        for model in self._parameter_value_models:
            model.set_filter_entity_ids(self.filter_entity_ids)

    @Slot(dict)
    def _handle_graph_selection_changed(self, selected_items):
        """Resets filter according to graph selection."""
        obj_items = selected_items["object"]
        rel_items = selected_items["relationship"]
        active_objs = {self.db_map: [x.db_representation for x in obj_items]}
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr.db_map_ids(active_objs))
        active_rels = {self.db_map: [x.db_representation for x in rel_items] + cascading_rels[self.db_map]}
        self.filter_class_ids = {}
        for db_map, items in active_objs.items():
            self.filter_class_ids.setdefault(db_map, set()).update({x["class_id"] for x in items})
        for db_map, items in active_rels.items():
            self.filter_class_ids.setdefault(db_map, set()).update({x["class_id"] for x in items})
        self.filter_entity_ids = self.db_mngr.db_map_class_ids(active_objs)
        self.filter_entity_ids.update(self.db_mngr.db_map_class_ids(active_rels))
        self.reset_filters()

    @Slot(dict)
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
        self.filter_class_ids = self._db_map_ids(active_obj_cls_inds | active_rel_cls_inds)
        self.filter_entity_ids = self._db_map_class_ids(active_obj_inds | active_rel_inds)
        # Cascade (note that we carefuly select where to cascade from, to avoid 'circularity')
        from_obj_cls_inds = obj_cls_inds | {ind.parent() for ind in obj_inds}
        from_obj_inds = obj_inds | {ind.parent() for ind in rel_cls_inds}
        cascading_rel_cls_inds = self.db_mngr.find_cascading_relationship_classes(self._db_map_ids(from_obj_cls_inds))
        cascading_rel_inds = self.db_mngr.find_cascading_relationships(self._db_map_ids(from_obj_inds))
        for db_map, ids in self.db_mngr.db_map_ids(cascading_rel_cls_inds).items():
            self.filter_class_ids.setdefault(db_map, set()).update(ids)
        for (db_map, class_id), ids in self.db_mngr.db_map_class_ids(cascading_rel_inds).items():
            self.filter_entity_ids.setdefault((db_map, class_id), set()).update(ids)
        self.reset_filters()

    @Slot(dict)
    def _handle_relationship_tree_selection_changed(self, selected_indexes):
        """Resets filter according to relationship tree selection."""
        rel_cls_inds = set(selected_indexes.get("relationship_class", {}).keys())
        active_rel_inds = set(selected_indexes.get("relationship", {}).keys())
        active_rel_cls_inds = rel_cls_inds | {ind.parent() for ind in active_rel_inds}
        self.filter_class_ids = self._db_map_ids(active_rel_cls_inds)
        self.filter_entity_ids = self._db_map_class_ids(active_rel_inds)
        self.reset_filters()

    @Slot("QVariant", bool)
    def _handle_tag_button_toggled(self, db_map_ids, checked):
        """Resets filter according to selection in parameter_tag toolbar."""
        for db_map, id_ in db_map_ids:
            if checked:
                self.filter_tag_ids.setdefault(db_map, set()).add(id_)
            else:
                self.filter_tag_ids[db_map].remove(id_)
        self.filter_tag_ids = {db_map: ids for db_map, ids in self.filter_tag_ids.items() if ids}
        filter_parameters = self.db_mngr.find_cascading_parameter_definitions_by_tag(self.filter_tag_ids)
        self.filter_parameter_ids = d = {}
        for db_map, params in filter_parameters.items():
            for param in params:
                d.setdefault((db_map, param["entity_class_id"]), set()).add(param["id"])
        if self.filter_tag_ids and not any(filter_parameters.values()):
            # There are tags selected but no matching parameter definitions ~> no class shall pass
            self.tag_filter_class_ids = None
            self.reset_filters()
            return
        self.tag_filter_class_ids = d = {}
        for db_map, params in filter_parameters.items():
            for param in params:
                d.setdefault(db_map, set()).add(param["entity_class_id"])
        self.reset_filters()

    @Slot(bool)
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    def restore_dock_widgets(self):
        """Restores parameter_tag toolbar."""
        super().restore_dock_widgets()
        self.parameter_tag_toolbar.setVisible(True)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)

    def restore_ui(self):
        """Restores UI state from previous session."""
        super().restore_ui()
        self.qsettings.beginGroup(self.settings_group)
        header_states = (
            self.qsettings.value("objParDefHeaderState"),
            self.qsettings.value("objParValHeaderState"),
            self.qsettings.value("relParDefHeaderState"),
            self.qsettings.value("relParValHeaderState"),
        )
        self.qsettings.endGroup()
        views = (
            self.ui.tableView_object_parameter_definition.horizontalHeader(),
            self.ui.tableView_object_parameter_value.horizontalHeader(),
            self.ui.tableView_relationship_parameter_definition.horizontalHeader(),
            self.ui.tableView_relationship_parameter_value.horizontalHeader(),
        )
        for view, state in zip(views, header_states):
            if state:
                curr_state = view.saveState()
                view.restoreState(state)
                if view.count() != view.model().columnCount():
                    # This can happen when switching to a version where the model has a different header
                    view.restoreState(curr_state)

    def save_window_state(self):
        """Saves window state parameters (size, position, state) via QSettings."""
        super().save_window_state()
        self.qsettings.beginGroup(self.settings_group)
        h = self.ui.tableView_object_parameter_definition.horizontalHeader()
        self.qsettings.setValue("objParDefHeaderState", h.saveState())
        h = self.ui.tableView_object_parameter_value.horizontalHeader()
        self.qsettings.setValue("objParValHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_definition.horizontalHeader()
        self.qsettings.setValue("relParDefHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_value.horizontalHeader()
        self.qsettings.setValue("relParValHeaderState", h.saveState())
        self.qsettings.endGroup()

    def receive_alternatives_updated(self, db_map_data):
        super().receive_alternatives_updated(db_map_data)
        self.object_parameter_value_model.receive_alternatives_updated(db_map_data)
        self.relationship_parameter_value_model.receive_alternatives_updated(db_map_data)

    def receive_parameter_tags_fetched(self, db_map_data):
        super().receive_parameter_tags_fetched(db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_added(db_map_data)

    def receive_parameter_definitions_fetched(self, db_map_data):
        super().receive_parameter_definitions_added(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_values_fetched(self, db_map_data):
        super().receive_parameter_values_added(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_tags_added(self, db_map_data):
        super().receive_parameter_tags_added(db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_added(db_map_data)

    def receive_parameter_definitions_added(self, db_map_data):
        super().receive_parameter_definitions_added(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        super().receive_parameter_values_added(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_tags_updated(self, db_map_data):
        super().receive_parameter_tags_updated(db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_updated(db_map_data)

    def receive_parameter_definitions_updated(self, db_map_data):
        super().receive_parameter_definitions_updated(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        super().receive_parameter_values_updated(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_definition_tags_set(self, db_map_data):
        super().receive_parameter_definition_tags_set(db_map_data)
        self.object_parameter_definition_model.receive_parameter_definition_tags_set(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_definition_tags_set(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        super().receive_object_classes_removed(db_map_data)
        self.object_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.object_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        super().receive_relationship_classes_removed(db_map_data)
        self.relationship_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.relationship_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_parameter_tags_removed(self, db_map_data):
        super().receive_parameter_tags_removed(db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_removed(db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        super().receive_parameter_definitions_removed(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_removed(db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        super().receive_parameter_values_removed(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_removed(db_map_data)
