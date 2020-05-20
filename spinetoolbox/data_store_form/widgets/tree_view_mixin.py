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
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QInputDialog
from .custom_menus import EntityTreeContextMenu
from .add_items_dialogs import (
    AddObjectClassesDialog,
    AddObjectsDialog,
    AddRelationshipClassesDialog,
    AddRelationshipsDialog,
)
from .edit_or_remove_items_dialogs import (
    EditObjectClassesDialog,
    EditObjectsDialog,
    EditRelationshipClassesDialog,
    EditRelationshipsDialog,
    RemoveEntitiesDialog,
)
from ...mvcmodels.entity_tree_models import ObjectTreeModel, RelationshipTreeModel
from ...helpers import busy_effect
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
        self.object_tree_model = ObjectTreeModel(self, self.db_mngr, *self.db_maps)
        self.relationship_tree_model = RelationshipTreeModel(self, self.db_mngr, *self.db_maps)
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_relationship.setModel(self.relationship_tree_model)

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_tree.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.treeView_object.connect_signals()
        self.ui.treeView_relationship.connect_signals()
        self.ui.treeView_object.entity_selection_changed.connect(self.ui.treeView_relationship.clear_any_selections)
        self.ui.treeView_relationship.entity_selection_changed.connect(self.ui.treeView_object.clear_any_selections)
        self.ui.treeView_object.entity_selection_changed.connect(self.update_object_filter)
        self.ui.treeView_relationship.entity_selection_changed.connect(self.update_relationship_filter)
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionEdit_tree_items.triggered.connect(self.ui.treeView_object.edit_selected)
        self.ui.actionEdit_tree_items.triggered.connect(self.ui.treeView_relationship.edit_selected)
        self.ui.treeView_object.export_requested.connect(self.export_data_from_indexes)
        self.ui.treeView_object.editing_requested.connect(self.edit_object_tree_items)
        self.ui.treeView_object.removing_requested.connect(self.show_remove_entity_tree_items_form)
        self.ui.treeView_relationship.export_requested.connect(self.export_data_from_indexes)
        self.ui.treeView_relationship.editing_requested.connect(self.edit_relationship_tree_items)
        self.ui.treeView_relationship.removing_requested.connect(self.show_remove_entity_tree_items_form)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_relationship.customContextMenuRequested.connect(self.show_relationship_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_relationship)
        self._object_classes_added.connect(lambda: self.ui.treeView_object.resizeColumnToContents(0))
        self._object_classes_fetched.connect(lambda: self.ui.treeView_object.expand(self.object_tree_model.root_index))
        self._relationship_classes_added.connect(lambda: self.ui.treeView_relationship.resizeColumnToContents(0))
        self._relationship_classes_fetched.connect(
            lambda: self.ui.treeView_relationship.expand(self.relationship_tree_model.root_index)
        )

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_tree_model.build_tree()
        self.relationship_tree_model.build_tree()
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

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

    @Slot(dict)
    def update_object_filter(self, selected_indexes):
        """Updates object filter."""
        obj_cls_inds = set(selected_indexes.get("object class", {}).keys())
        obj_inds = set(selected_indexes.get("object", {}).keys())
        rel_cls_inds = set(selected_indexes.get("relationship class", {}).keys())
        active_rel_inds = set(selected_indexes.get("relationship", {}).keys())
        # Compute active indexes by merging in the parents from lower levels recursively
        active_rel_cls_inds = rel_cls_inds | {ind.parent() for ind in active_rel_inds}
        active_obj_inds = obj_inds | {ind.parent() for ind in active_rel_cls_inds}
        active_obj_cls_inds = obj_cls_inds | {ind.parent() for ind in active_obj_inds}
        self.selected_ent_cls_ids["object class"] = self._db_map_ids(active_obj_cls_inds)
        self.selected_ent_cls_ids["relationship class"] = self._db_map_ids(active_rel_cls_inds)
        self.selected_ent_ids["object"] = self._db_map_class_ids(active_obj_inds)
        self.selected_ent_ids["relationship"] = self._db_map_class_ids(active_rel_inds)
        # Cascade (note that we carefuly select where to cascade from, to avoid 'circularity')
        from_obj_cls_inds = obj_cls_inds | {ind.parent() for ind in obj_inds}
        from_obj_inds = obj_inds | {ind.parent() for ind in rel_cls_inds}
        cascading_rel_cls_inds = self.db_mngr.find_cascading_relationship_classes(self._db_map_ids(from_obj_cls_inds))
        cascading_rel_inds = self.db_mngr.find_cascading_relationships(self._db_map_ids(from_obj_inds))
        for db_map, ids in self.db_mngr.db_map_ids(cascading_rel_cls_inds).items():
            self.selected_ent_cls_ids["relationship class"].setdefault(db_map, set()).update(ids)
        for (db_map, class_id), ids in self.db_mngr.db_map_class_ids(cascading_rel_inds).items():
            self.selected_ent_ids["relationship"].setdefault((db_map, class_id), set()).update(ids)
        self.update_filter()

    @Slot(dict)
    def update_relationship_filter(self, selected_indexes):
        """Update relationship filter according to relationship tree selection.
        FIXME: Remove this if the one above suffices.
        """
        rel_cls_inds = set(selected_indexes.get("relationship class", {}).keys())
        active_rel_inds = set(selected_indexes.get("relationship", {}).keys())
        active_rel_cls_inds = rel_cls_inds | {ind.parent() for ind in active_rel_inds}
        self.selected_ent_cls_ids["relationship class"] = self._db_map_ids(active_rel_cls_inds)
        self.selected_ent_ids["relationship"] = self._db_map_class_ids(active_rel_inds)
        self.update_filter()

    @Slot(dict)
    def edit_object_tree_items(self, selected_indexes):
        """Starts editing the given index in the object tree."""
        obj_cls_inds = set(selected_indexes.get("object class", {}).keys())
        obj_inds = set(selected_indexes.get("object", {}).keys())
        rel_cls_inds = set(selected_indexes.get("relationship class", {}).keys())
        rel_inds = set(selected_indexes.get("relationship", {}).keys())
        self.show_edit_object_classes_form(obj_cls_inds)
        self.show_edit_objects_form(obj_inds)
        self.show_edit_relationship_classes_form(rel_cls_inds)
        self.show_edit_relationships_form(rel_inds)

    @Slot(dict)
    def edit_relationship_tree_items(self, selected_indexes):
        """Starts editing the given index in the relationship tree."""
        rel_cls_inds = set(selected_indexes.get("relationship class", {}).keys())
        rel_inds = set(selected_indexes.get("relationship", {}).keys())
        self.show_edit_relationship_classes_form(rel_cls_inds)
        self.show_edit_relationships_form(rel_inds)

    @Slot("QPoint")
    def show_object_tree_context_menu(self, pos):
        """Shows the context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        view = self.ui.treeView_object
        index = view.indexAt(pos)
        if index.column() != 0:
            return
        global_pos = view.viewport().mapToGlobal(pos)
        object_tree_context_menu = EntityTreeContextMenu(self, global_pos, index)
        option = object_tree_context_menu.get_action()
        slot = {
            "Copy text": view.copy,
            "Add object classes": self.show_add_object_classes_form,
            "Add objects": lambda: self.call_show_add_objects_form(index),
            "Add relationship classes": lambda: self.call_show_add_relationship_classes_form(index),
            "Add relationships": lambda: self.call_show_add_relationships_form(index),
            "Edit selected": view.edit_selected,
            "Remove selected": view.remove_selected,
            "Find next": lambda: self.find_next_relationship(index),
            "Fully expand": view.fully_expand,
            "Fully collapse": view.fully_collapse,
            "Duplicate": lambda: self.duplicate_object(index),
            "Export selected": view.export_selected,
        }.get(option)
        object_tree_context_menu.deleteLater()
        if slot is not None:
            slot()

    @Slot("QPoint")
    def show_relationship_tree_context_menu(self, pos):
        """Shows the context for relationship tree.

        Args:
            pos (QPoint): Mouse position
        """
        view = self.ui.treeView_relationship
        index = view.indexAt(pos)
        if index.column() != 0:
            return
        global_pos = view.viewport().mapToGlobal(pos)
        relationship_tree_context_menu = EntityTreeContextMenu(self, global_pos, index)
        option = relationship_tree_context_menu.get_action()
        slot = {
            "Copy text": view.copy,
            "Add relationship classes": self.show_add_relationship_classes_form,
            "Add relationships": lambda: self.call_show_add_relationships_form(index),
            "Edit selected": view.edit_selected,
            "Remove selected": view.remove_selected,
            "Fully expand": view.fully_expand,
            "Fully collapse": view.fully_collapse,
            "Export selected": view.export_selected,
        }.get(option)
        relationship_tree_context_menu.deleteLater()
        if slot is not None:
            slot()

    @Slot(dict)
    def export_data_from_indexes(self, indexes):
        """Exports data from given indexes into a standalone db file."""
        parcel = SpineDBParcel(self.db_mngr)
        obj_cls_inds = set(indexes.get("object class", {}).keys())
        obj_inds = set(indexes.get("object", {}).keys())
        rel_cls_inds = set(indexes.get("relationship class", {}).keys())
        rel_inds = set(indexes.get("relationship", {}).keys())
        db_map_obj_cls_ids = self._db_map_ids(obj_cls_inds)
        db_map_obj_ids = self._db_map_ids(obj_inds)
        db_map_rel_cls_ids = self._db_map_ids(rel_cls_inds)
        db_map_rel_ids = self._db_map_ids(rel_inds)
        parcel.push_object_class_ids(db_map_obj_cls_ids)
        parcel.push_object_ids(db_map_obj_ids)
        parcel.push_relationship_class_ids(db_map_rel_cls_ids)
        parcel.push_relationship_ids(db_map_rel_ids)
        self.export_data(parcel.data)

    @Slot("QModelIndex")
    def find_next_relationship(self, index):
        """Expands next occurrence of a relationship in object tree."""
        next_index = self.object_tree_model.find_next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    def _get_cascading_relationships(self, object_item):
        """
        Returns a dict mapping db maps to a list of cascading relationship for the given object item.

        Args:
            object_item (ObjectItem)

        Returns:
            dict(DiffDatabaseMapping, list)
        """
        return {
            db_map: [
                rel
                for rel in self.db_mngr.get_items(db_map, "relationship")
                if str(object_item.db_map_id(db_map)) in rel["object_id_list"].split(",")
            ]
            for db_map in object_item.db_maps
        }

    @busy_effect
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
            "objects": [(cls_name, dup_name) for (cls_name, obj_name) in data["objects"]],
            "relationships": [
                (cls_name, _replace_name(obj_name_lst)) for (cls_name, obj_name_lst) in data["relationships"]
            ],
            "object_parameter_values": [
                (cls_name, dup_name, param_name, val)
                for (cls_name, obj_name, param_name, val) in data["object_parameter_values"]
            ],
            "relationship_parameter_values": [
                (cls_name, _replace_name(obj_name_lst), param_name, val)
                for (cls_name, obj_name_lst, param_name, val) in data["relationship_parameter_values"]
            ],
        }
        self.db_mngr.import_data({db_map: data for db_map in object_item.db_maps}, command_text="Duplicate object")

    def call_show_add_objects_form(self, index):
        class_name = index.internalPointer().display_data
        self.show_add_objects_form(class_name=class_name)

    def call_show_add_relationship_classes_form(self, index):
        object_class_one_name = index.internalPointer().display_data
        self.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def call_show_add_relationships_form(self, index):
        item = index.internalPointer()
        relationship_class_key = item.display_id
        try:
            object_name = item.parent_item.display_data
            object_class_name = item.parent_item.parent_item.display_data
        except AttributeError:
            object_name = object_class_name = None
        self.show_add_relationships_form(
            relationship_class_key=relationship_class_key, object_class_name=object_class_name, object_name=object_name
        )

    @Slot(bool)
    def show_add_object_classes_form(self, checked=False):
        """Shows dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot(bool)
    def show_add_objects_form(self, checked=False, class_name=""):
        """Shows dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_mngr, *self.db_maps, class_name=class_name)
        dialog.show()

    @Slot(bool)
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Shows dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(
            self, self.db_mngr, *self.db_maps, object_class_one_name=object_class_one_name
        )
        dialog.show()

    @Slot(bool)
    def show_add_relationships_form(
        self, checked=False, relationship_class_key=(), object_class_name="", object_name=""
    ):
        """Shows dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            self.db_mngr,
            *self.db_maps,
            relationship_class_key=relationship_class_key,
            object_class_name=object_class_name,
            object_name=object_name,
        )
        dialog.show()

    def show_edit_object_classes_form(self, indexes):
        if not indexes:
            return
        items = {ind.internalPointer() for ind in indexes}
        dialog = EditObjectClassesDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_objects_form(self, indexes):
        if not indexes:
            return
        items = {ind.internalPointer() for ind in indexes}
        dialog = EditObjectsDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_relationship_classes_form(self, indexes):
        if not indexes:
            return
        items = {ind.internalPointer() for ind in indexes}
        dialog = EditRelationshipClassesDialog(self, self.db_mngr, items)
        dialog.show()

    def show_edit_relationships_form(self, indexes):
        if not indexes:
            return
        items = {ind.internalPointer() for ind in indexes}
        relationship_class_key = lambda item: item.parent_item.display_id
        items_by_class = {}
        for item in items:
            items_by_class.setdefault(relationship_class_key(item), set()).add(item)
        for relationship_class_key, items in items_by_class.items():
            dialog = EditRelationshipsDialog(self, self.db_mngr, items, relationship_class_key)
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

    def receive_object_classes_fetched(self, db_map_data):
        super().receive_object_classes_fetched(db_map_data)
        self._object_classes_fetched.emit()

    def receive_relationship_classes_fetched(self, db_map_data):
        super().receive_object_classes_fetched(db_map_data)
        self._relationship_classes_fetched.emit()

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
