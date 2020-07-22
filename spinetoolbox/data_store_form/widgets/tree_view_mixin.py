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
Contains the TreeViewMixin class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""
from PySide2.QtCore import Signal, Slot, QTimer
from PySide2.QtWidgets import QInputDialog
from .add_items_dialogs import (
    AddObjectClassesDialog,
    AddObjectsDialog,
    AddRelationshipClassesDialog,
    AddRelationshipsDialog,
    AddObjectGroupDialog,
    ManageRelationshipsDialog,
    ManageObjectGroupDialog,
)
from .edit_or_remove_items_dialogs import (
    EditObjectClassesDialog,
    EditObjectsDialog,
    EditRelationshipClassesDialog,
    EditRelationshipsDialog,
    RemoveEntitiesDialog,
)
from ..mvcmodels.alternative_scenario_model import AlternativeScenarioModel
from ..mvcmodels.entity_tree_models import ObjectTreeModel, RelationshipTreeModel
from ...spine_db_parcel import SpineDBParcel


class TreeViewMixin:
    """Provides object and relationship trees for the data store form.
    """

    _object_classes_added = Signal()
    _relationship_classes_added = Signal()
    _object_classes_fetched = Signal()
    _relationship_classes_fetched = Signal()
    """Emitted from fetcher thread, connected to Slots in GUI thread."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Selected ids
        self.alternative_scenario_model = AlternativeScenarioModel(self, self.db_mngr, *self.db_maps)
        self.object_tree_model = ObjectTreeModel(self, self.db_mngr, *self.db_maps)
        self.relationship_tree_model = RelationshipTreeModel(self, self.db_mngr, *self.db_maps)
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_relationship.setModel(self.relationship_tree_model)
        self.ui.treeView_alternative_scenario.setModel(self.alternative_scenario_model)
        self.ui.treeView_alternative_scenario.connect_data_store_form(self)
        self.ui.treeView_object.connect_data_store_form(self)
        self.ui.treeView_relationship.connect_data_store_form(self)

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_tree.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_alternative_scenario_tree.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.treeView_object.tree_selection_changed.connect(self.ui.treeView_relationship.clear_any_selections)
        self.ui.treeView_relationship.tree_selection_changed.connect(self.ui.treeView_object.clear_any_selections)
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionManage_relationships.triggered.connect(self.show_manage_relationships_form)
        self._object_classes_added.connect(lambda: self.ui.treeView_object.resizeColumnToContents(0))
        self._object_classes_fetched.connect(lambda: self.ui.treeView_object.expand(self.object_tree_model.root_index))
        self._relationship_classes_added.connect(lambda: self.ui.treeView_relationship.resizeColumnToContents(0))
        self._relationship_classes_fetched.connect(
            lambda: self.ui.treeView_relationship.expand(self.relationship_tree_model.root_index)
        )

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.alternative_scenario_model.build_tree()
        for item in self.alternative_scenario_model.visit_all():
            index = self.alternative_scenario_model.index_from_item(item)
            self.ui.treeView_alternative_scenario.expand(index)
        self.ui.treeView_alternative_scenario.resizeColumnToContents(0)
        self.object_tree_model.build_tree()
        self.relationship_tree_model.build_tree()
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Updates object filter and sets default rows."""
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        self.object_tree_model.select_indexes(indexes)
        self._clear_tree_selections_silently(self.ui.treeView_relationship)
        self.set_default_parameter_data(self.ui.treeView_object.currentIndex())
        self._update_object_filter()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_relationship_tree_selection_changed(self, selected, deselected):
        """Updates relationship filter and sets default rows."""
        indexes = self.ui.treeView_relationship.selectionModel().selectedIndexes()
        self.relationship_tree_model.select_indexes(indexes)
        self._clear_tree_selections_silently(self.ui.treeView_object)
        self.set_default_parameter_data(self.ui.treeView_relationship.currentIndex())
        self._update_relationship_filter()

    @staticmethod
    def _clear_tree_selections_silently(tree_view):
        """Clears the selections on a given abstract item view without emitting any signals."""
        selection_model = tree_view.selectionModel()
        if selection_model.hasSelection():
            selection_model.blockSignals(True)
            selection_model.clearSelection()
            selection_model.blockSignals(False)

    @staticmethod
    def _db_map_items(indexes):
        """Groups items from given tree indexes by db map.

        Returns:
            dict: lists of dictionary items keyed by DiffDatabaseMapping
        """
        d = dict()
        for index in indexes:
            item = index.model().item_from_index(index)
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
        obj_cls_inds = set(selected_indexes.get("object_class", {}).keys())
        obj_inds = set(selected_indexes.get("object", {}).keys())
        rel_cls_inds = set(selected_indexes.get("relationship_class", {}).keys())
        rel_inds = set(selected_indexes.get("relationship", {}).keys())
        db_map_obj_cls_ids = self._db_map_ids(obj_cls_inds)
        db_map_obj_ids = self._db_map_ids(obj_inds)
        db_map_rel_cls_ids = self._db_map_ids(rel_cls_inds)
        db_map_rel_ids = self._db_map_ids(rel_inds)
        parcel.push_object_class_ids(db_map_obj_cls_ids)
        parcel.push_object_ids(db_map_obj_ids)
        parcel.push_relationship_class_ids(db_map_rel_cls_ids)
        parcel.push_relationship_ids(db_map_rel_ids)
        self.export_data(parcel.data)

    def duplicate_object(self, index):
        """
        Duplicates the object at the given object tree model index.

        Args:
            index (QModelIndex)
        """
        orig_name = index.data()
        dup_name, ok = QInputDialog.getText(
            self, "Duplicate object", "Enter a name for the duplicate object:", text=orig_name + "_copy"
        )
        if not ok:
            return
        _replace_name = lambda name_list: [name if name != orig_name else dup_name for name in name_list]
        parcel = SpineDBParcel(self.db_mngr)
        object_item = index.internalPointer()
        db_map_obj_ids = {db_map: {object_item.db_map_id(db_map)} for db_map in object_item.db_maps}
        parcel.push_inside_object_ids(db_map_obj_ids)
        data = self._make_data_for_export(parcel.data)
        data = {
            "objects": [
                (cls_name, dup_name, description) for (cls_name, obj_name, description) in data.get("objects", [])
            ],
            "relationships": [
                (cls_name, _replace_name(obj_name_lst)) for (cls_name, obj_name_lst) in data.get("relationships", [])
            ],
            "object_parameter_values": [
                (cls_name, dup_name, param_name, val)
                for (cls_name, obj_name, param_name, val) in data.get("object_parameter_values", [])
            ],
            "relationship_parameter_values": [
                (cls_name, _replace_name(obj_name_lst), param_name, val)
                for (cls_name, obj_name_lst, param_name, val) in data.get("relationship_parameter_values", [])
            ],
        }
        self.db_mngr.import_data({db_map: data for db_map in object_item.db_maps}, command_text="Duplicate object")

    @Slot(bool)
    def show_add_object_classes_form(self, checked=False):
        """Shows dialog to add new object classes."""
        dialog = AddObjectClassesDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot(bool)
    def show_add_objects_form(self, checked=False, class_name=""):
        """Shows dialog to add new objects."""
        dialog = AddObjectsDialog(self, self.db_mngr, *self.db_maps, class_name=class_name)
        dialog.show()

    def show_add_object_group_form(self, object_class_item):
        """Shows dialog to add new object group."""
        dialog = AddObjectGroupDialog(self, object_class_item, self.db_mngr, *self.db_maps)
        dialog.show()

    def show_manage_object_group_form(self, object_item):
        """Shows dialog to manage an object group."""
        dialog = ManageObjectGroupDialog(self, object_item, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot(bool)
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Shows dialog to add new relationship_class."""
        dialog = AddRelationshipClassesDialog(
            self, self.db_mngr, *self.db_maps, object_class_one_name=object_class_one_name
        )
        dialog.show()

    def show_add_relationships_form(self, checked=False, relationship_class_key=None, object_names_by_class_name=None):
        """Shows dialog to add new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            self.db_mngr,
            *self.db_maps,
            relationship_class_key=relationship_class_key,
            object_names_by_class_name=object_names_by_class_name
        )
        dialog.show()

    @Slot(bool)
    def show_manage_relationships_form(self, checked=False, relationship_class_key=None):
        dialog = ManageRelationshipsDialog(
            self, self.db_mngr, *self.db_maps, relationship_class_key=relationship_class_key
        )
        dialog.show()

    def edit_entity_tree_items(self, selected_indexes):
        """Starts editing given indexes."""
        obj_cls_items = {ind.internalPointer() for ind in selected_indexes.get("object_class", {})}
        obj_items = {ind.internalPointer() for ind in selected_indexes.get("object", {})}
        rel_cls_items = {ind.internalPointer() for ind in selected_indexes.get("relationship_class", {})}
        rel_items = {ind.internalPointer() for ind in selected_indexes.get("relationship", {})}
        self.show_edit_object_classes_form(obj_cls_items)
        self.show_edit_objects_form(obj_items)
        self.show_edit_relationship_classes_form(rel_cls_items)
        self.show_edit_relationships_form(rel_items)

    def show_edit_object_classes_form(self, items):
        if not items:
            return
        dialog = EditObjectClassesDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_objects_form(self, items):
        if not items:
            return
        dialog = EditObjectsDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_relationship_classes_form(self, items):
        if not items:
            return
        dialog = EditRelationshipClassesDialog(self, self.db_mngr, items)
        dialog.show()

    @Slot()
    def show_remove_alternative_tree_items_form(self):
        """Shows form to remove items from object treeview."""
        selected = {
            item_type: [ind.model().item_from_index(ind) for ind in indexes]
            for item_type, indexes in self.alternative_scenario_model.selected_indexes.items()
        }
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()

    def show_edit_relationships_form(self, items):
        if not items:
            return
        items_by_class = {}
        for item in items:
            data = item.db_map_data(item.first_db_map)
            relationship_class_name = data["class_name"]
            object_class_name_list = data["object_class_name_list"]
            class_key = (relationship_class_name, object_class_name_list)
            items_by_class.setdefault(class_key, set()).add(item)
        for class_key, classed_items in items_by_class.items():
            dialog = EditRelationshipsDialog(self, self.db_mngr, classed_items, class_key)
            dialog.show()

    @Slot(dict)
    def show_remove_entity_tree_items_form(self, selected_indexes):
        """Shows form to remove items from object treeview."""
        selected = {
            item_type: [ind.model().item_from_index(ind) for ind in indexes]
            for item_type, indexes in selected_indexes.items()
        }
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        super().notify_items_changed(action, item_type, db_map_data)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

    def receive_alternatives_fetched(self, db_map_data):
        super().receive_alternatives_fetched(db_map_data)
        self.alternative_scenario_model.add_alternatives(db_map_data)
        self._alternatives_fetched.emit(list(db_map_data.keys()))

    def receive_scenarios_fetched(self, db_map_data):
        super().receive_scenarios_fetched(db_map_data)
        self.alternative_scenario_model.add_scenarios(db_map_data)
        self._scenarios_fetched.emit(list(db_map_data.keys()))

    def receive_object_classes_fetched(self, db_map_data):
        super().receive_object_classes_fetched(db_map_data)
        self._object_classes_fetched.emit()

    def receive_relationship_classes_fetched(self, db_map_data):
        super().receive_object_classes_fetched(db_map_data)
        self._relationship_classes_fetched.emit()

    def receive_alternatives_added(self, db_map_data):
        super().receive_alternatives_added(db_map_data)
        self.alternative_scenario_model.add_alternatives(db_map_data)

    def receive_scenarios_added(self, db_map_data):
        super().receive_scenarios_added(db_map_data)
        self.alternative_scenario_model.add_scenarios(db_map_data)

    def receive_object_classes_added(self, db_map_data):
        super().receive_object_classes_added(db_map_data)
        self.object_tree_model.add_object_classes(db_map_data)
        self._object_classes_added.emit()

    def receive_objects_added(self, db_map_data):
        super().receive_objects_added(db_map_data)
        self.object_tree_model.add_objects(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        super().receive_relationship_classes_added(db_map_data)
        self.object_tree_model.add_relationship_classes(db_map_data)
        self.relationship_tree_model.add_relationship_classes(db_map_data)
        self._relationship_classes_added.emit()

    def receive_relationships_added(self, db_map_data):
        super().receive_relationships_added(db_map_data)
        self.object_tree_model.add_relationships(db_map_data)
        self.relationship_tree_model.add_relationships(db_map_data)

    def receive_alternatives_updated(self, db_map_data):
        super().receive_alternatives_updated(db_map_data)
        self.alternative_scenario_model.update_alternatives(db_map_data)

    def receive_scenarios_updated(self, db_map_data):
        super().receive_scenarios_updated(db_map_data)
        self.alternative_scenario_model.update_scenarios(db_map_data)

    def receive_entity_groups_added(self, db_map_data):
        super().receive_entity_groups_added(db_map_data)
        self.object_tree_model.raise_entity_groups(db_map_data)
        self.ui.treeView_object.refresh_active_member_indexes()

    def receive_object_classes_updated(self, db_map_data):
        super().receive_object_classes_updated(db_map_data)
        self.object_tree_model.update_object_classes(db_map_data)

    def receive_objects_updated(self, db_map_data):
        super().receive_objects_updated(db_map_data)
        self.object_tree_model.update_objects(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        super().receive_relationship_classes_updated(db_map_data)
        self.object_tree_model.update_relationship_classes(db_map_data)
        self.relationship_tree_model.update_relationship_classes(db_map_data)

    def receive_relationships_updated(self, db_map_data):
        super().receive_relationships_updated(db_map_data)
        self.object_tree_model.update_relationships(db_map_data)
        self.relationship_tree_model.update_relationships(db_map_data)

    def receive_alternatives_removed(self, db_map_data):
        super().receive_alternatives_removed(db_map_data)
        self.alternative_scenario_model.remove_alternatives(db_map_data)

    def receive_scenarios_removed(self, db_map_data):
        super().receive_scenarios_removed(db_map_data)
        self.alternative_scenario_model.remove_scenarios(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        super().receive_object_classes_removed(db_map_data)
        self.object_tree_model.remove_object_classes(db_map_data)

    def receive_objects_removed(self, db_map_data):
        super().receive_objects_removed(db_map_data)
        self.object_tree_model.remove_objects(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        super().receive_relationship_classes_removed(db_map_data)
        self.object_tree_model.remove_relationship_classes(db_map_data)
        self.relationship_tree_model.remove_relationship_classes(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        super().receive_relationships_removed(db_map_data)
        self.object_tree_model.remove_relationships(db_map_data)
        self.relationship_tree_model.remove_relationships(db_map_data)

    def receive_entity_groups_removed(self, db_map_data):
        super().receive_entity_groups_removed(db_map_data)
        QTimer.singleShot(0, self.ui.treeView_object.refresh_active_member_indexes)
