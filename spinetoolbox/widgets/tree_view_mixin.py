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

from PySide2.QtCore import Slot
from .custom_menus import ObjectTreeContextMenu, RelationshipTreeContextMenu
from .add_db_items_dialogs import (
    AddObjectClassesDialog,
    AddObjectsDialog,
    AddRelationshipClassesDialog,
    AddRelationshipsDialog,
)
from .edit_db_items_dialogs import (
    EditObjectClassesDialog,
    EditObjectsDialog,
    EditRelationshipClassesDialog,
    EditRelationshipsDialog,
    RemoveEntitiesDialog,
)
from ..mvcmodels.entity_tree_models import ObjectTreeModel, RelationshipTreeModel
from ..helpers import busy_effect


class TreeViewMixin:
    """Provides object and relationship trees for the data store form.
    """

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
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self._handle_object_tree_selection_changed)
        self.ui.treeView_relationship.selectionModel().selectionChanged.connect(
            self._handle_relationship_tree_selection_changed
        )
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionEdit_object_classes.triggered.connect(self.show_edit_object_classes_form)
        self.ui.actionEdit_objects.triggered.connect(self.show_edit_objects_form)
        self.ui.actionEdit_relationship_classes.triggered.connect(self.show_edit_relationship_classes_form)
        self.ui.actionEdit_relationships.triggered.connect(self.show_edit_relationships_form)
        self.object_tree_model.remove_selection_requested.connect(self.show_remove_object_tree_items_form)
        self.relationship_tree_model.remove_selection_requested.connect(self.show_remove_relationship_tree_items_form)
        self.ui.treeView_object.edit_key_pressed.connect(self.edit_object_tree_items)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_relationship)
        self.ui.treeView_relationship.edit_key_pressed.connect(self.edit_relationship_tree_items)
        self.ui.treeView_relationship.customContextMenuRequested.connect(self.show_relationship_tree_context_menu)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_tree_model.build_tree()
        self.relationship_tree_model.build_tree()
        self.ui.treeView_object.expand(self.object_tree_model.root_index)
        self.ui.treeView_relationship.expand(self.relationship_tree_model.root_index)
        self.ui.treeView_object.resizeColumnToContents(0)
        self.ui.treeView_relationship.resizeColumnToContents(0)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Updates object filter and sets default rows."""
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        self.object_tree_model.select_indexes(indexes)
        if not self._accept_selection(self.ui.treeView_object):
            return
        self.set_default_parameter_data(self.ui.treeView_object.currentIndex())
        self._update_object_filter()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_relationship_tree_selection_changed(self, selected, deselected):
        """Updates relationship filter and sets default rows."""
        indexes = self.ui.treeView_relationship.selectionModel().selectedIndexes()
        self.relationship_tree_model.select_indexes(indexes)
        if not self._accept_selection(self.ui.treeView_relationship):
            return
        self.set_default_parameter_data(self.ui.treeView_relationship.currentIndex())
        self._update_relationship_filter()

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

    @staticmethod
    def _db_map_class_id_data(db_map_data):
        """Returns a new dictionary where the class id is also part of the key.

        Returns:
            dict: lists of dictionary items keyed by tuple (DiffDatabaseMapping, integer class id)
        """
        d = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                d.setdefault((db_map, item["class_id"]), set()).add(item["id"])
        return d

    @staticmethod
    def _extend_merge(left, right):
        """Returns a new dictionary by uniting left and right.

        Returns:
            dict: lists of dictionary items keyed by DiffDatabaseMapping
        """
        result = left.copy()
        for key, data in right.items():
            result.setdefault(key, []).extend(data)
        return result

    def _update_object_filter(self):
        """Updates filters object filter according to object tree selection."""
        selected_object_classes = self._db_map_items(self.object_tree_model.selected_object_class_indexes)
        self.selected_ent_cls_ids["object class"] = self.db_mngr._to_ids(selected_object_classes)
        selected_rel_clss = self._db_map_items(self.object_tree_model.selected_relationship_class_indexes)
        cascading_rel_clss = self.db_mngr.find_cascading_relationship_classes(self.selected_ent_cls_ids["object class"])
        selected_rel_clss = self._extend_merge(selected_rel_clss, cascading_rel_clss)
        self.selected_ent_cls_ids["relationship class"] = self.db_mngr._to_ids(selected_rel_clss)
        selected_objs = self._db_map_items(self.object_tree_model.selected_object_indexes)
        selected_rels = self._db_map_items(self.object_tree_model.selected_relationship_indexes)
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr._to_ids(selected_objs))
        selected_rels = self._extend_merge(selected_rels, cascading_rels)
        for db_map, items in selected_rels.items():
            self.selected_ent_cls_ids["relationship class"].setdefault(db_map, set()).update(
                {x["class_id"] for x in items}
            )
        # Accending objects from selected relationships
        ascending_objs = self._db_map_items(
            {ind.parent().parent(): None for ind in self.object_tree_model.selected_relationship_indexes}
        )
        selected_objs = self._extend_merge(selected_objs, ascending_objs)
        # Ascending objects from selected relationship class
        ascending_objs = self._db_map_items(
            {ind.parent(): None for ind in self.object_tree_model.selected_relationship_class_indexes}
        )
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr._to_ids(ascending_objs))
        selected_objs = self._extend_merge(selected_objs, ascending_objs)
        selected_rels = self._extend_merge(selected_rels, cascading_rels)
        for db_map, items in selected_objs.items():
            self.selected_ent_cls_ids["object class"].setdefault(db_map, set()).update({x["class_id"] for x in items})
        self.selected_ent_ids["object"] = self._db_map_class_id_data(selected_objs)
        self.selected_ent_ids["relationship"] = self._db_map_class_id_data(selected_rels)
        self.update_filter()

    def _update_relationship_filter(self):
        """Update filters relationship filter according to relationship tree selection."""
        selected_rel_clss = self._db_map_items(self.relationship_tree_model.selected_relationship_class_indexes)
        self.selected_ent_cls_ids["relationship class"] = self.db_mngr._to_ids(selected_rel_clss)
        selected_rels = self._db_map_items(self.relationship_tree_model.selected_relationship_indexes)
        for db_map, items in selected_rels.items():
            self.selected_ent_cls_ids["relationship class"].setdefault(db_map, set()).update(
                {x["class_id"] for x in items}
            )
        self.selected_ent_ids["relationship"] = self._db_map_class_id_data(selected_rels)
        self.update_filter()

    @Slot("QModelIndex")
    def edit_object_tree_items(self, current):
        """Starts editing the given index in the object tree."""
        current = self.ui.treeView_object.currentIndex()
        current_type = self.object_tree_model.item_from_index(current).item_type
        if current_type == 'object class':
            self.show_edit_object_classes_form()
        elif current_type == 'object':
            self.show_edit_objects_form()
        elif current_type == 'relationship class':
            self.show_edit_relationship_classes_form()
        elif current_type == 'relationship':
            self.show_edit_relationships_form()

    @Slot("QModelIndex")
    def edit_relationship_tree_items(self, current):
        """Starts editing the given index in the relationship tree."""
        current = self.ui.treeView_relationship.currentIndex()
        current_type = self.relationship_tree_model.item_from_index(current).item_type
        if current_type == 'relationship class':
            self.show_edit_relationship_classes_form()
        elif current_type == 'relationship':
            self.show_edit_relationships_form()

    @Slot("QPoint")
    def show_object_tree_context_menu(self, pos):
        """Shows the context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_object.indexAt(pos)
        if index.column() != 0:
            return
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, index)
        option = object_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_object.copy()
        elif option == "Add object classes":
            self.show_add_object_classes_form()
        elif option == "Add objects":
            self.call_show_add_objects_form(index)
        elif option == "Add relationship classes":
            self.call_show_add_relationship_classes_form(index)
        elif option == "Add relationships":
            self.call_show_add_relationships_form(index)
        elif option == "Edit object classes":
            self.show_edit_object_classes_form()
        elif option == "Edit objects":
            self.show_edit_objects_form()
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Find next":
            self.find_next_relationship(index)
        elif option == "Remove selection":
            self.show_remove_object_tree_items_form()
        elif option == "Fully expand":
            self.fully_expand_selection()
        elif option == "Fully collapse":
            self.fully_collapse_selection()
        else:  # No option selected
            pass
        object_tree_context_menu.deleteLater()

    @Slot("QPoint")
    def show_relationship_tree_context_menu(self, pos):
        """Shows the context for relationship tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_relationship.indexAt(pos)
        if index.column() != 0:
            return
        global_pos = self.ui.treeView_relationship.viewport().mapToGlobal(pos)
        relationship_tree_context_menu = RelationshipTreeContextMenu(self, global_pos, index)
        option = relationship_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_relationship.copy()
        elif option == "Add relationship classes":
            self.show_add_relationship_classes_form()
        elif option == "Add relationships":
            self.call_show_add_relationships_form(index)
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Remove selection":
            self.show_remove_relationship_tree_items_form()
        else:  # No option selected
            pass
        relationship_tree_context_menu.deleteLater()

    @busy_effect
    def fully_expand_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in self.object_tree_model.visit_all(index):
                self.ui.treeView_object.expand(self.object_tree_model.index_from_item(item))

    @busy_effect
    def fully_collapse_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in self.object_tree_model.visit_all(index):
                self.ui.treeView_object.collapse(self.object_tree_model.index_from_item(item))

    @Slot("QModelIndex")
    def find_next_relationship(self, index):
        """Expands next occurrence of a relationship in object tree."""
        next_index = self.object_tree_model.find_next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    def call_show_add_objects_form(self, index):
        class_name = index.internalPointer().display_name
        self.show_add_objects_form(class_name=class_name)

    def call_show_add_relationship_classes_form(self, index):
        object_class_one_name = index.internalPointer().display_name
        self.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def call_show_add_relationships_form(self, index):
        item = index.internalPointer()
        relationship_class_key = item.display_id
        try:
            object_name = item.parent_item.display_name
            object_class_name = item.parent_item.parent_item.display_name
        except AttributeError:
            object_name = object_class_name = None
        self.show_add_relationships_form(
            relationship_class_key=relationship_class_key, object_class_name=object_class_name, object_name=object_name
        )

    @Slot("bool")
    def show_add_object_classes_form(self, checked=False):
        """Shows dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot("bool")
    def show_add_objects_form(self, checked=False, class_name=""):
        """Shows dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_mngr, *self.db_maps, class_name=class_name)
        dialog.show()

    @Slot("bool")
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Shows dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(
            self, self.db_mngr, *self.db_maps, object_class_one_name=object_class_one_name
        )
        dialog.show()

    @Slot("bool")
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

    @Slot("bool")
    def show_edit_object_classes_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_class_indexes}
        dialog = EditObjectClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
    def show_edit_objects_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_indexes}
        dialog = EditObjectsDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
    def show_edit_relationship_classes_form(self, checked=False):
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_class_indexes.keys()
            | self.relationship_tree_model.selected_relationship_class_indexes.keys()
        }
        dialog = EditRelationshipClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
    def show_edit_relationships_form(self, checked=False):
        # NOTE: Only edits relationships that are in the same class
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_indexes.keys()
            | self.relationship_tree_model.selected_relationship_indexes.keys()
        }
        first_item = next(iter(selected))
        relationship_class_key = first_item.parent_item.display_id
        selected = {item for item in selected if item.parent_item.display_id == relationship_class_key}
        dialog = EditRelationshipsDialog(self, self.db_mngr, selected, relationship_class_key)
        dialog.show()

    @Slot()
    def show_remove_object_tree_items_form(self):
        """Shows form to remove items from object treeview."""
        selected = {
            item_type: [ind.model().item_from_index(ind) for ind in indexes]
            for item_type, indexes in self.object_tree_model.selected_indexes.items()
        }
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot()
    def show_remove_relationship_tree_items_form(self):
        """Shows form to remove items from relationship treeview."""
        selected = {
            item_type: [ind.model().item_from_index(ind) for ind in indexes]
            for item_type, indexes in self.relationship_tree_model.selected_indexes.items()
        }
        dialog = RemoveEntitiesDialog(self, self.db_mngr, selected)
        dialog.show()

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        super().notify_items_changed(action, item_type, db_map_data)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

    def receive_object_classes_added(self, db_map_data):
        super().receive_object_classes_added(db_map_data)
        self.object_tree_model.add_object_classes(db_map_data)

    def receive_objects_added(self, db_map_data):
        super().receive_objects_added(db_map_data)
        self.object_tree_model.add_objects(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        super().receive_relationship_classes_added(db_map_data)
        self.object_tree_model.add_relationship_classes(db_map_data)
        self.relationship_tree_model.add_relationship_classes(db_map_data)

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
