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
Contains the GraphViewMixin class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""
import itertools
from PySide2.QtCore import Slot, QRectF
from PySide2.QtWidgets import QGraphicsTextItem
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtGui import QPainter
from spinedb_api import to_database, from_database
from ...widgets.custom_qwidgets import ZoomWidgetAction, RotateWidgetAction
from ...widgets.custom_qgraphicsscene import CustomGraphicsScene
from ..graphics_items import (
    EntityItem,
    ObjectItem,
    RelationshipItem,
    ArcItem,
    RodObjectItem,
    RodRelationshipItem,
    RodArcItem,
)
from .graph_view_demo import GraphViewDemo
from .graph_layout_generator import GraphLayoutGenerator
from ...helpers import get_save_file_name_in_last_dir
from .add_items_dialogs import AddReadyRelationshipsDialog


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    _POS_PARAM_NAME = "entity_graph_position"
    _VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.15 * _VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.5 * _VERTEX_EXTENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_relationship_expansion = self.qsettings.value(
            "appSettings/fullRelationshipExpansion", defaultValue="false"
        )
        self.ui.actionFull_relationship_expansion.setChecked(self._full_relationship_expansion == "true")
        self._persistent = False
        self.scene = None
        self.selected_tree_inds = {}
        self.object_ids = list()
        self.relationship_ids = list()
        self.src_inds = list()
        self.dst_inds = list()
        self.hidden_items = list()
        self.prunned_entity_ids = dict()
        self.removed_items = list()
        self.entity_item_selection = list()
        self.added_object_ids = set()
        self.added_relationship_ids = set()
        self._blank_item = None
        self.zoom_widget_action = None
        self.rotate_widget_action = None
        self.layout_gens = list()
        self.ui.graphicsView.connect_data_store_form(self)
        self.setup_widget_actions()

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_entity_graph.toggleViewAction())

    def init_models(self):
        super().init_models()
        self.scene = CustomGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.treeView_object.entity_selection_changed.connect(self.rebuild_graph)
        self.ui.treeView_relationship.entity_selection_changed.connect(self.rebuild_graph)
        self.ui.dockWidget_entity_graph.visibilityChanged.connect(self._handle_entity_graph_visibility_changed)
        self.ui.actionHide_selected.triggered.connect(self.hide_selected_items)
        self.ui.actionShow_hidden.triggered.connect(self.show_hidden_items)
        self.ui.actionPrune_selected_entities.triggered.connect(self.prune_selected_entities)
        self.ui.actionPrune_selected_classes.triggered.connect(self.prune_selected_classes)
        self.ui.actionRestore_all_pruned.triggered.connect(self.restore_all_pruned_items)
        self.ui.actionLive_graph_demo.triggered.connect(self.show_demo)
        self.ui.actionSave_positions.triggered.connect(self.save_positions)
        self.ui.actionClear_positions.triggered.connect(self.clear_saved_positions)
        self.ui.actionExport_graph_as_pdf.triggered.connect(self.export_as_pdf)
        self.ui.actionFull_relationship_expansion.toggled.connect(self.set_full_relationship_expansion)
        # Dock Widgets menu action
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_graph_about_to_show)
        self.zoom_widget_action.minus_pressed.connect(self.ui.graphicsView.zoom_out)
        self.zoom_widget_action.plus_pressed.connect(self.ui.graphicsView.zoom_in)
        self.zoom_widget_action.reset_pressed.connect(self.ui.graphicsView.reset_zoom)
        self.rotate_widget_action.clockwise_pressed.connect(self.ui.graphicsView.rotate_clockwise)
        self.rotate_widget_action.anticlockwise_pressed.connect(self.ui.graphicsView.rotate_anticlockwise)
        self.scene.selectionChanged.connect(self._handle_scene_selection_changed)

    @Slot()
    def _handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        selected_items = self.scene.selectedItems()
        obj_item_selection = [x for x in selected_items if isinstance(x, ObjectItem)]
        rel_item_selection = [x for x in selected_items if isinstance(x, RelationshipItem)]
        self.entity_item_selection = obj_item_selection + rel_item_selection
        selected_objs = {self.db_map: [x.db_representation for x in obj_item_selection]}
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr.db_map_ids(selected_objs))
        selected_rels = {self.db_map: [x.db_representation for x in rel_item_selection] + cascading_rels[self.db_map]}
        self.selected_ent_cls_ids["object class"] = {}
        self.selected_ent_cls_ids["relationship class"] = {}
        for db_map, items in selected_objs.items():
            self.selected_ent_cls_ids["object class"].setdefault(db_map, set()).update({x["class_id"] for x in items})
        for db_map, items in selected_rels.items():
            self.selected_ent_cls_ids["relationship class"].setdefault(db_map, set()).update(
                {x["class_id"] for x in items}
            )
        self.selected_ent_ids["object"] = self.db_mngr.db_map_class_ids(selected_objs)
        self.selected_ent_ids["relationship"] = self.db_mngr.db_map_class_ids(selected_rels)
        self.update_filter()

    @Slot(bool)
    def set_full_relationship_expansion(self, checked):
        self._full_relationship_expansion = "true" if checked else "false"
        self.qsettings.setValue("appSettings/fullRelationshipExpansion", self._full_relationship_expansion)
        self.build_graph()

    def setup_widget_actions(self):
        """Setups zoom and rotate widget action in view menu."""
        self.zoom_widget_action = ZoomWidgetAction(self.ui.menuView)
        self.rotate_widget_action = RotateWidgetAction(self.ui.menuView)
        self.ui.menuGraph.addSeparator()
        self.ui.menuGraph.addAction(self.zoom_widget_action)
        self.ui.menuGraph.addAction(self.rotate_widget_action)

    def receive_objects_added(self, db_map_data):
        """Runs when objects are added to the db.
        Adds the new objects to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_added(db_map_data)
        objects = db_map_data.get(self.db_map, [])
        added_ids = {x["id"] for x in objects}
        restored_ids = self.restore_removed_entities(added_ids)
        added_ids -= restored_ids
        if added_ids:
            self.added_object_ids.update(added_ids)
            self.build_graph(persistent=True)

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Adds the new relationships to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_added(db_map_data)
        relationships = db_map_data.get(self.db_map, [])
        added_ids = {x["id"] for x in relationships}
        restored_ids = self.restore_removed_entities(added_ids)
        added_ids -= restored_ids
        if added_ids:
            self.added_relationship_ids.update(added_ids)
            self.build_graph(persistent=True)

    def receive_object_classes_updated(self, db_map_data):
        super().receive_object_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        super().receive_relationship_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_objects_updated(self, db_map_data):
        """Runs when objects are updated in the db. Refreshes names of objects in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_updated(db_map_data)
        updated_ids = {x["id"]: (x["name"], x["description"]) for x in db_map_data.get(self.db_map, [])}
        for item in self.ui.graphicsView.items():
            if isinstance(item, ObjectItem) and item.entity_id in updated_ids:
                name, description = updated_ids[item.entity_id]
                item.update_name(name)
                item.update_description(description)

    def receive_objects_removed(self, db_map_data):
        """Runs when objects are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_removed(db_map_data)
        self.hide_removed_entities(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        """Runs when relationships are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_removed(db_map_data)
        self.hide_removed_entities(db_map_data)

    def restore_removed_entities(self, added_ids):
        """Restores any entities that have been previously removed and returns their ids.
        This happens in the context of undo/redo.

        Args:
            added_ids (set(int)): Set of newly added ids.

        Returns:
            set(int)
        """
        restored_items = [item for item in self.removed_items if item.entity_id in added_ids]
        for item in restored_items:
            self.removed_items.remove(item)
            item.set_all_visible(True)
        return {item.entity_id for item in restored_items}

    def hide_removed_entities(self, db_map_data):
        """Hides removed entities while saving them into a list attribute.
        This allows entities to be restored in case the user undoes the operation."""
        removed_ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        self.added_object_ids -= removed_ids
        self.added_relationship_ids -= removed_ids
        removed_items = [
            item
            for item in self.ui.graphicsView.items()
            if isinstance(item, EntityItem) and item.entity_id in removed_ids
        ]
        if not removed_items:
            return
        self.removed_items.extend(removed_items)
        removed_item = removed_items.pop()
        if removed_items:
            self.scene.selectionChanged.disconnect(self._handle_scene_selection_changed)
            for item in removed_items:
                item.set_all_visible(False)
            self.scene.selectionChanged.connect(self._handle_scene_selection_changed)
        removed_item.set_all_visible(False)

    def refresh_icons(self, db_map_data):
        """Runs when entity classes are updated in the db. Refreshes icons of entities in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and item.entity_class_id in updated_ids:
                item.refresh_icon()

    @Slot()
    def _handle_menu_graph_about_to_show(self):
        """Enables or disables actions according to current selection in the graph."""
        visible = self.ui.dockWidget_entity_graph.isVisible()
        self.ui.actionSave_positions.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionClear_positions.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionHide_selected.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionShow_hidden.setEnabled(visible and bool(self.hidden_items))
        self.ui.actionPrune_selected_entities.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionPrune_selected_classes.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.menuRestore_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.ui.actionRestore_all_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.zoom_widget_action.setEnabled(visible)
        self.ui.actionPrune_selected_entities.setText(f"Prune {self._get_selected_entity_names()}")
        self.ui.actionPrune_selected_classes.setText(f"Prune {self._get_selected_class_names()}")

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        self.build_graph()

    @Slot(dict)
    def rebuild_graph(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        self.selected_tree_inds = selected
        self.hidden_items.clear()
        self.removed_items.clear()
        self.added_object_ids.clear()
        self.added_relationship_ids.clear()
        self.build_graph()

    def build_graph(self, persistent=False):
        """Builds the graph.

        Args:
            persistent (bool, optional): If True, builds the graph on top of the current one.
        """
        if not self.ui.dockWidget_entity_graph.isVisible():
            return
        self._persistent = persistent
        for layout_gen in self.layout_gens:
            layout_gen.stop()
        self._update_graph_data()
        layout_gen = self._make_layout_generator()
        self.layout_gens.append(layout_gen)
        layout_gen.show_progress_widget(self.ui.graphicsView)
        layout_gen.finished.connect(self._complete_graph)
        layout_gen.done.connect(lambda layout_gen=layout_gen: self.layout_gens.remove(layout_gen))
        layout_gen.start()

    @Slot(object, object)
    def _complete_graph(self, x, y):
        """
        Args:
            x (list): Horizontal coordinates
            y (list): Vertical coordinates
        """
        if self.layout_gens:
            return
        self.scene.clear()
        new_items = self._make_new_items(x, y)
        if not any(new_items):
            self._blank_item = QGraphicsTextItem("Nothing to show.")
            self.scene.addItem(self._blank_item)
            self.ui.actionExport_graph_as_pdf.setEnabled(False)
        else:
            self._add_new_items(*new_items)  # pylint: disable=no-value-for-parameter
            self.ui.actionExport_graph_as_pdf.setEnabled(True)
        if not self._persistent:
            self.ui.graphicsView.reset_zoom()
        else:
            self.ui.graphicsView.apply_zoom()

    def _get_selected_entity_ids(self):
        """Returns a set of ids corresponding to selected entities in the trees.

        Returns:
            set: selected object ids
            set: selected relationship ids
        """
        selected_object_ids = set()
        selected_relationship_ids = set()
        for index in self.selected_tree_inds.get("object", {}):
            item = index.model().item_from_index(index)
            object_id = item.db_map_id(self.db_map)
            selected_object_ids.add(object_id)
        for index in self.selected_tree_inds.get("relationship", {}):
            item = index.model().item_from_index(index)
            relationship_id = item.db_map_id(self.db_map)
            selected_relationship_ids.add(relationship_id)
        for index in self.selected_tree_inds.get("object class", {}):
            item = index.model().item_from_index(index)
            object_ids = set(item._get_children_ids(self.db_map))
            selected_object_ids.update(object_ids)
        for index in self.selected_tree_inds.get("relationship class", {}):
            item = index.model().item_from_index(index)
            relationship_ids = set(item._get_children_ids(self.db_map))
            selected_relationship_ids.update(relationship_ids)
        return selected_object_ids, selected_relationship_ids

    def _get_all_relationships_for_graph(self, object_ids, relationship_ids):
        cond = all if self._full_relationship_expansion == "false" else any
        return [
            x
            for x in self.db_mngr.get_items(self.db_map, "relationship")
            if cond([int(id_) in object_ids for id_ in x["object_id_list"].split(",")])
        ] + [self.db_mngr.get_item(self.db_map, "relationship", id_) for id_ in relationship_ids]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        object_ids, relationship_ids = self._get_selected_entity_ids()
        object_ids.update(self.added_object_ids)
        relationship_ids.update(self.added_relationship_ids)
        prunned_entity_ids = {id_ for ids in self.prunned_entity_ids.values() for id_ in ids}
        object_ids -= prunned_entity_ids
        relationship_ids -= prunned_entity_ids
        relationships = self._get_all_relationships_for_graph(object_ids, relationship_ids)
        object_id_lists = dict()
        for relationship in relationships:
            if relationship["id"] in prunned_entity_ids:
                continue
            object_id_list = {int(x) for x in relationship["object_id_list"].split(",")} - prunned_entity_ids
            if len(object_id_list) < 2:
                continue
            object_ids.update(object_id_list)
            object_id_lists[relationship["id"]] = object_id_list
        self.object_ids = list(object_ids)
        self.relationship_ids = list(object_id_lists)
        self._update_src_dst_inds(object_id_lists)

    def _update_src_dst_inds(self, object_id_lists):
        self.src_inds = list()
        self.dst_inds = list()
        object_ind_lookup = {id_: k for k, id_ in enumerate(self.object_ids)}
        relationship_ind_lookup = {id_: len(self.object_ids) + k for k, id_ in enumerate(self.relationship_ids)}
        for relationship_id, object_id_list in object_id_lists.items():
            object_inds = [object_ind_lookup[object_id] for object_id in object_id_list]
            relationship_ind = relationship_ind_lookup[relationship_id]
            for object_ind in object_inds:
                self.src_inds.append(relationship_ind)
                self.dst_inds.append(object_ind)

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGenerator
        """
        parameter_positions = {
            p["entity_id"]: dict(from_database(p["value"]).value_to_database_data())
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter value", "parameter_name", self._POS_PARAM_NAME
            )
        }
        if self._persistent:
            persisted_positions = {
                item.entity_id: {"x": item.pos().x(), "y": item.pos().y()}
                for item in self.ui.graphicsView.items()
                if isinstance(item, EntityItem)
            }
        else:
            persisted_positions = {}
        persisted_positions.update(parameter_positions)
        entity_ids = self.object_ids + self.relationship_ids
        heavy_positions = {
            ind: persisted_positions[id_] for ind, id_ in enumerate(entity_ids) if id_ in persisted_positions
        }
        return GraphLayoutGenerator(
            len(entity_ids), self.src_inds, self.dst_inds, self._ARC_LENGTH_HINT, heavy_positions=heavy_positions
        )

    def _make_new_items(self, x, y):
        """Returns new items for the graph.

        Args:
            x (list)
            y (list)

        Returns
            list: ObjectItem instances
            list: RelationshipItem instances
            list: ArcItem instances
        """
        object_items = list()
        relationship_items = list()
        arc_items = list()
        for i, object_id in enumerate(self.object_ids):
            object_item = ObjectItem(self, x[i], y[i], self._VERTEX_EXTENT, object_id)
            object_items.append(object_item)
        offset = len(object_items)
        for i, relationship_id in enumerate(self.relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], 0.5 * self._VERTEX_EXTENT, relationship_id
            )
            relationship_items.append(relationship_item)
        for rel_ind, obj_ind in zip(self.src_inds, self.dst_inds):
            arc_item = ArcItem(relationship_items[rel_ind - offset], object_items[obj_ind], self._ARC_WIDTH)
            arc_items.append(arc_item)
        return (object_items, relationship_items, arc_items)

    def _add_new_items(self, object_items, relationship_items, arc_items):
        for item in object_items + relationship_items + arc_items:
            self.scene.addItem(item)

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        self.hidden_items.extend(self.entity_item_selection)
        for item in self.entity_item_selection:
            item.set_all_visible(False)

    @Slot(bool)
    def show_hidden_items(self, checked=False):
        """Shows hidden items."""
        if not self.scene:
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
        self.hidden_items.clear()

    def _get_selected_entity_names(self):
        if len(self.entity_item_selection) == 1:
            return "'" + self.entity_item_selection[0].entity_name + "'"
        return "selected entities"

    def _get_selected_class_names(self):
        if len(self.entity_item_selection) == 1:
            return "'" + self.entity_item_selection[0].entity_class_name + "'"
        return "selected classes"

    @Slot(bool)
    def prune_selected_entities(self, checked=False):
        """Prunes selected items."""
        entity_ids = {x.entity_id for x in self.entity_item_selection}
        key = self._get_selected_entity_names()
        self.prunned_entity_ids[key] = entity_ids
        action = self.ui.menuRestore_pruned.addAction(key)
        action.triggered.connect(lambda checked=False, key=key: self.restore_pruned_items(key))
        self.build_graph()

    @Slot(bool)
    def prune_selected_classes(self, checked=False):
        """Prunes selected items."""
        class_ids = {x.entity_class_id for x in self.entity_item_selection}
        entity_ids = {x["id"] for x in self.db_mngr.get_items(self.db_map, "object") if x["class_id"] in class_ids}
        entity_ids |= {
            x["id"] for x in self.db_mngr.get_items(self.db_map, "relationship") if x["class_id"] in class_ids
        }
        key = self._get_selected_class_names()
        self.prunned_entity_ids[key] = entity_ids
        action = self.ui.menuRestore_pruned.addAction(key)
        action.triggered.connect(lambda checked=False, key=key: self.restore_pruned_items(key))
        self.build_graph()

    @Slot(bool)
    def restore_all_pruned_items(self, checked=False):
        """Reinstates all pruned items."""
        self.prunned_entity_ids.clear()
        self.build_graph()

    def restore_pruned_items(self, key):
        """Reinstates last pruned items."""
        if self.prunned_entity_ids.pop(key, None) is not None:
            action = next(iter(a for a in self.ui.menuRestore_pruned.actions() if a.text() == key))
            self.ui.menuRestore_pruned.removeAction(action)
            self.build_graph()

    @Slot(bool)
    def show_demo(self, checked=False):
        demo = GraphViewDemo(self)
        self.ui.actionLive_graph_demo.setEnabled(False)
        demo.destroyed.connect(self._enable_live_graph_demo_action)
        demo.show()

    @Slot("QObject")
    def _enable_live_graph_demo_action(self, obj=None):
        try:
            self.ui.actionLive_graph_demo.setEnabled(True)
        except RuntimeError:
            pass

    def edit_entity_graph_items(self):
        """Starts editing given indexes."""
        obj_items = [item for item in self.entity_item_selection if isinstance(item, ObjectItem)]
        rel_items = [item for item in self.entity_item_selection if isinstance(item, RelationshipItem)]
        self.show_edit_objects_form(obj_items)
        self.show_edit_relationships_form(rel_items)

    def remove_entity_graph_items(self, checked=False):
        """Removes all selected items in the graph."""
        if not self.entity_item_selection:
            return
        db_map_typed_data = {self.db_map: {}}
        for item in self.entity_item_selection:
            db_item = item.db_representation
            db_map_typed_data[self.db_map].setdefault(item.entity_type, []).append(db_item)
        self.db_mngr.remove_items(db_map_typed_data)

    @Slot(bool)
    def save_positions(self, checked=False):
        items_per_class_id = {}
        for item in self.entity_item_selection:
            items_per_class_id.setdefault(item.entity_class_id, []).append(item)
        pos_def_class_ids = {
            p["entity_class_id"]
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter definition", "parameter_name", self._POS_PARAM_NAME
            )
        }
        defs_to_add = [
            {"name": self._POS_PARAM_NAME, "entity_class_id": class_id}
            for class_id in items_per_class_id.keys() - pos_def_class_ids
        ]
        if defs_to_add:
            self.db_mngr.add_parameter_definitions({self.db_map: defs_to_add})
        pos_def_id_lookup = {
            p["entity_class_id"]: p["id"]
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter definition", "parameter_name", self._POS_PARAM_NAME
            )
        }
        pos_val_id_lookup = {
            (p["entity_class_id"], p["entity_id"]): p["id"]
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter value", "parameter_name", self._POS_PARAM_NAME
            )
        }
        vals_to_add = list()
        vals_to_update = list()
        for class_id, items in items_per_class_id.items():
            for item in items:
                pos_val_id = pos_val_id_lookup.get((class_id, item.entity_id), None)
                value = {"type": "map", "index_type": "str", "data": [["x", item.pos().x()], ["y", item.pos().y()]]}
                if pos_val_id is None:
                    vals_to_add.append(
                        {
                            "name": "pos_x",
                            "entity_class_id": class_id,
                            "entity_id": item.entity_id,
                            "parameter_definition_id": pos_def_id_lookup[class_id],
                            "value": to_database(value),
                        }
                    )
                else:
                    vals_to_update.append({"id": pos_val_id, "value": to_database(value)})
        if vals_to_add:
            self.db_mngr.add_parameter_values({self.db_map: vals_to_add})
        if vals_to_update:
            self.db_mngr.update_parameter_values({self.db_map: vals_to_update})

    @Slot(bool)
    def clear_saved_positions(self, checked=False):
        entity_ids = {x.entity_id for x in self.entity_item_selection}
        vals_to_remove = [
            p
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter value", "parameter_name", self._POS_PARAM_NAME
            )
            if p["entity_id"] in entity_ids
        ]
        if vals_to_remove:
            self.db_mngr.remove_items({self.db_map: {"parameter value": vals_to_remove}})
        self.build_graph()

    @Slot(bool)
    def export_as_pdf(self, checked=False):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, "exportGraphAsPDF", self, "Export as PDF...", self._get_base_dir(), "PDF files (*.pdf)"
        )
        self.qsettings.endGroup()
        if not file_path:
            return
        view = self.ui.graphicsView
        source = view._get_viewport_scene_rect()
        current_zoom_factor = view.zoom_factor
        view._zoom(1.0 / current_zoom_factor)
        self.scene.clearSelection()
        printer = QPrinter()
        printer.setPaperSize(source.size(), QPrinter.Point)
        printer.setOutputFileName(file_path)
        painter = QPainter(printer)
        self.scene.render(painter, QRectF(), source)
        painter.end()
        view._zoom(current_zoom_factor)
        self._insert_open_file_button(file_path)

    def start_relationship_from_object(self, obj_item):
        """Starts a relationship from the given object item.

        Args:
            obj_item (..graphics_items.ObjectItem)
        """
        self.msg.emit("Creating relationship with object '{0}'...".format(obj_item.entity_name))
        rod_obj_item = RodObjectItem(self, obj_item.pos().x(), obj_item.pos().y(), self._VERTEX_EXTENT)
        rod_rel_item = RodRelationshipItem(self, obj_item.pos().x(), obj_item.pos().y(), 0.5 * self._VERTEX_EXTENT)
        rod_arc_item1 = RodArcItem(rod_rel_item, obj_item, self._ARC_WIDTH)
        rod_arc_item2 = RodArcItem(rod_rel_item, rod_obj_item, self._ARC_WIDTH)
        rod_rel_item.refresh_icon()
        self.ui.graphicsView.set_rod_items([rod_obj_item, rod_rel_item, rod_arc_item1, rod_arc_item2])

    def try_and_add_relationships(self, *object_items):
        """Tries to add relationships between the given object items.

        Args:
            object_items (..graphics_items.ObjectItem)
        """
        relationships_per_class = {}
        for rel_cls in self.db_mngr.get_items(self.db_map, "relationship class"):
            object_class_id_list = [int(id_) for id_ in rel_cls["object_class_id_list"].split(",")]
            rel_cls_key = (rel_cls["name"], rel_cls["object_class_name_list"])
            for item_permutation in itertools.permutations(object_items):
                if [item.entity_class_id for item in item_permutation] == object_class_id_list:
                    relationship = [item.entity_name for item in item_permutation]
                    relationships_per_class.setdefault(rel_cls_key, list()).append(relationship)
        if not relationships_per_class:
            self.msg.emit(
                "<p>Sorry, no relationship classes match the given combination of objects.</p>"
                "<p>Try to add a corresponding relationship class first.</p>"
            )
            return
        dialog = AddReadyRelationshipsDialog(self, relationships_per_class, self.db_mngr, *self.db_maps)
        dialog.show()
