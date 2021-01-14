######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from PySide2.QtCore import Signal, Slot, QRectF, QTimer, Qt
from PySide2.QtWidgets import QLabel, QHBoxLayout, QWidget, QSizePolicy
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtGui import QPainter
from spinedb_api import from_database
from ...widgets.custom_qwidgets import ZoomWidgetAction, RotateWidgetAction
from ...widgets.custom_qgraphicsscene import CustomGraphicsScene
from ..graphics_items import (
    EntityItem,
    ObjectItem,
    RelationshipItem,
    ArcItem,
    CrossHairsItem,
    CrossHairsRelationshipItem,
    CrossHairsArcItem,
    make_figure_graphics_item,
)
from .graph_layout_generator import GraphLayoutGenerator, make_heat_map
from ...helpers import get_save_file_name_in_last_dir
from .add_items_dialogs import AddReadyRelationshipsDialog
from .select_position_parameters_dialog import SelectPositionParametersDialog


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    _VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.15 * _VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.5 * _VERTEX_EXTENT

    graph_selection_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._show_cascading_relationships = (
            self.qsettings.value("appSettings/showCascadingRelationships", defaultValue="false") == "true"
        )
        self.ui.actionShow_cascading_relationships.setChecked(self._show_cascading_relationships)
        self._nothing_to_show_label = QLabel("Nothing to show")
        self._nothing_to_show_label.setAlignment(Qt.AlignCenter)
        self._nothing_to_show_label.setStyleSheet("QLabel{font-weight: bold; font-size:18px;}")
        layout = QHBoxLayout(self.ui.graphicsView)
        layout.addWidget(self._nothing_to_show_label)
        self._nothing_to_show_label.hide()
        self._persistent = False
        self._pos_x_parameter = "x"
        self._pos_y_parameter = "y"
        self.scene = None
        self.object_items = list()
        self.relationship_items = list()
        self.arc_items = list()
        self.selected_tree_inds = {}
        self.object_ids = list()
        self.relationship_ids = list()
        self.src_inds = list()
        self.dst_inds = list()
        self.hidden_items = list()
        self.prunned_entity_ids = dict()
        self.removed_items = list()
        self.selected_items = list()
        self._relationships_being_added = False
        self.added_relationship_ids = set()
        self.wip_relationship_class = None
        self._blank_item = None
        self._point_value_tuples_per_parameter_name = dict()  # Used in the menu add heat map
        self.heat_map_items = []
        self.zoom_widget_action = None
        self.rotate_widget_action = None
        self.layout_gens = list()
        self.ui.graphicsView.connect_spine_db_editor(self)
        self.setup_widget_actions()

    @property
    def entity_items(self):
        return [x for x in self.scene.items() if isinstance(x, EntityItem) and x not in self.removed_items]

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_entity_graph.toggleViewAction())

    def init_models(self):
        super().init_models()
        self.scene = CustomGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)
        self.scene.selectionChanged.connect(self._handle_scene_selection_changed)

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.treeView_object.tree_selection_changed.connect(self.rebuild_graph)
        self.ui.treeView_relationship.tree_selection_changed.connect(self.rebuild_graph)
        self.ui.dockWidget_entity_graph.visibilityChanged.connect(self._handle_entity_graph_visibility_changed)
        self.ui.actionHide_selected.triggered.connect(self.hide_selected_items)
        self.ui.actionShow_hidden.triggered.connect(self.show_hidden_items)
        self.ui.actionPrune_selected_entities.triggered.connect(self.prune_selected_entities)
        self.ui.actionPrune_selected_classes.triggered.connect(self.prune_selected_classes)
        self.ui.actionRestore_all_pruned.triggered.connect(self.restore_all_pruned_items)
        self.ui.actionSelect_position_parameters.triggered.connect(self.select_position_parameters)
        self.ui.actionSave_positions.triggered.connect(self.save_positions)
        self.ui.actionClear_positions.triggered.connect(self.clear_saved_positions)
        self.ui.actionExport_graph_as_pdf.triggered.connect(self.export_as_pdf)
        self.ui.actionRebuild_graph.triggered.connect(self.build_graph)
        self.ui.actionShow_cascading_relationships.toggled.connect(self.set_show_cascading_relationships)
        self.ui.menuAdd_parameter_heat_map.triggered.connect(self.add_heat_map)
        # Dock Widgets menu action
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_graph_about_to_show)
        self.zoom_widget_action.minus_pressed.connect(self.ui.graphicsView.zoom_out)
        self.zoom_widget_action.plus_pressed.connect(self.ui.graphicsView.zoom_in)
        self.zoom_widget_action.reset_pressed.connect(self.ui.graphicsView.reset_zoom)
        self.rotate_widget_action.clockwise_pressed.connect(self.ui.graphicsView.rotate_clockwise)
        self.rotate_widget_action.anticlockwise_pressed.connect(self.ui.graphicsView.rotate_anticlockwise)

    @Slot()
    def _handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        if self.scene is None:
            return
        selected_items = self.scene.selectedItems()
        selected_objs = [x for x in selected_items if isinstance(x, ObjectItem)]
        selected_rels = [x for x in selected_items if isinstance(x, RelationshipItem)]
        self.selected_items = selected_objs + selected_rels
        self.graph_selection_changed.emit({"object": selected_objs, "relationship": selected_rels})

    @Slot(bool)
    def set_show_cascading_relationships(self, checked=False):
        self.ui.actionShow_cascading_relationships.setChecked(checked)
        self._show_cascading_relationships = checked
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
        added_ids = {(db_map, x["id"]) for db_map, objects in db_map_data.items() for x in objects}
        self.restore_removed_entities(added_ids)

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Adds the new relationships to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_added(db_map_data)
        added_ids = {(db_map, x["id"]) for db_map, relationships in db_map_data.items() for x in relationships}
        restored_ids = self.restore_removed_entities(added_ids)
        added_ids -= restored_ids
        if added_ids and self._relationships_being_added:
            self.added_relationship_ids.update(added_ids)
            self.build_graph(persistent=True)
            self._end_add_relationships()

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
        updated_ids = {(db_map, x["id"]): x["name"] for db_map, objects in db_map_data.items() for x in objects}
        for item in self.ui.graphicsView.items():
            if isinstance(item, ObjectItem) and item.entity_id in updated_ids:
                name = updated_ids[item.entity_id]
                item.update_name(name)

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
        removed_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        self.added_relationship_ids -= removed_ids
        removed_items = [
            item
            for item in self.ui.graphicsView.items()
            if isinstance(item, EntityItem) and item.entity_id in removed_ids
        ]
        if not removed_items:
            return
        self.removed_items.extend(removed_items)
        scene = self.scene
        self.scene = None
        for item in removed_items:
            item.set_all_visible(False)
        self.scene = scene

    def refresh_icons(self, db_map_data):
        """Runs when entity classes are updated in the db. Refreshes icons of entities in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and (item.db_map, item.entity_class_id) in updated_ids:
                item.refresh_icon()

    @Slot()
    def _handle_menu_graph_about_to_show(self):
        """Enables or disables actions according to current selection in the graph."""
        visible = self.ui.dockWidget_entity_graph.isVisible()
        self.ui.actionSave_positions.setEnabled(visible and bool(self.selected_items))
        self.ui.actionClear_positions.setEnabled(visible and bool(self.selected_items))
        self.ui.actionHide_selected.setEnabled(visible and bool(self.selected_items))
        self.ui.actionShow_hidden.setEnabled(visible and bool(self.hidden_items))
        self.ui.actionPrune_selected_entities.setEnabled(visible and bool(self.selected_items))
        self.ui.actionPrune_selected_classes.setEnabled(visible and bool(self.selected_items))
        self.ui.menuRestore_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.ui.actionRestore_all_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.zoom_widget_action.setEnabled(visible)
        self.ui.actionPrune_selected_entities.setText(f"Prune {self._get_selected_entity_names()}")
        self.ui.actionPrune_selected_classes.setText(f"Prune {self._get_selected_class_names()}")
        self.ui.actionRebuild_graph.setEnabled(visible)
        self.zoom_widget_action.setEnabled(visible)
        self.rotate_widget_action.setEnabled(visible)
        self.ui.menuAdd_parameter_heat_map.setEnabled(visible)
        if visible:
            self._populate_menu_add_parameter_heat_map()

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        if visible:
            QTimer.singleShot(0, self.build_graph)
        else:
            self._stop_layout_generators()

    @Slot(dict)
    def rebuild_graph(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        self.selected_tree_inds = selected
        self.added_relationship_ids.clear()
        self.build_graph()

    def build_graph(self, persistent=False):
        """Builds the graph.

        Args:
            persistent (bool, optional): If True, builds the graph on top of the current one.
        """
        if not self.ui.dockWidget_entity_graph.isVisible():
            return
        self.ui.graphicsView.clear_cross_hairs_items()  # Needed
        self._persistent = persistent
        self._stop_layout_generators()
        self._update_graph_data()
        layout_gen = self._make_layout_generator()
        self.layout_gens.append(layout_gen)
        self._nothing_to_show_label.hide()
        layout_gen.show_progress_widget(self.ui.graphicsView)
        # NOTE: Connecting like below allows us to connect more than one layout finished to _complete_graph
        layout_gen.finished.connect(lambda x, y: self._complete_graph(x, y))  # pylint: disable=unnecessary-lambda
        layout_gen.destroyed.connect(lambda obj=None, layout_gen=layout_gen: self.layout_gens.remove(layout_gen))
        layout_gen.start()

    def _stop_layout_generators(self):
        for layout_gen in self.layout_gens:
            if layout_gen.is_running():
                layout_gen.stop()

    def _complete_graph(self, x, y):
        """
        Args:
            x (list): Horizontal coordinates
            y (list): Vertical coordinates
        """
        self.hidden_items.clear()
        self.removed_items.clear()
        self.selected_items.clear()
        self.heat_map_items.clear()
        self.scene.clear()
        if not self._make_new_items(x, y):
            self._nothing_to_show_label.show()
            self.ui.actionExport_graph_as_pdf.setEnabled(False)
        else:
            self._add_new_items()  # pylint: disable=no-value-for-parameter
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
        if "root" in self.selected_tree_inds:
            return (
                set((db_map, x["id"]) for db_map in self.db_maps for x in self.db_mngr.get_items(db_map, "object")),
                set(),
            )
        selected_object_ids = set()
        selected_relationship_ids = set()
        for index in self.selected_tree_inds.get("object", {}):
            item = index.model().item_from_index(index)
            for db_map_id in item.db_map_ids.items():
                selected_object_ids.add(db_map_id)
        for index in self.selected_tree_inds.get("relationship", {}):
            item = index.model().item_from_index(index)
            for db_map_id in item.db_map_ids.items():
                selected_relationship_ids.add(db_map_id)
        for index in self.selected_tree_inds.get("object_class", {}):
            item = index.model().item_from_index(index)
            for db_map in item.db_maps:
                object_ids = set((db_map, id_) for id_ in item._get_children_ids(db_map))
                selected_object_ids.update(object_ids)
        for index in self.selected_tree_inds.get("relationship_class", {}):
            item = index.model().item_from_index(index)
            for db_map in item.db_maps:
                relationship_ids = set((db_map, id_) for id_ in item._get_children_ids(db_map))
                selected_relationship_ids.update(relationship_ids)
        return selected_object_ids, selected_relationship_ids

    def _get_all_relationships_for_graph(self, object_ids, relationship_ids):
        cond = any if self._show_cascading_relationships else all
        return [
            (db_map, x)
            for db_map in self.db_maps
            for x in self.db_mngr.get_items(db_map, "relationship")
            if cond([(db_map, int(id_)) in object_ids for id_ in x["object_id_list"].split(",")])
        ] + [(db_map, self.db_mngr.get_item(db_map, "relationship", id_)) for db_map, id_ in relationship_ids]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        object_ids, relationship_ids = self._get_selected_entity_ids()
        relationship_ids.update(self.added_relationship_ids)
        prunned_entity_ids = {id_ for ids in self.prunned_entity_ids.values() for id_ in ids}
        object_ids -= prunned_entity_ids
        relationship_ids -= prunned_entity_ids
        relationships = self._get_all_relationships_for_graph(object_ids, relationship_ids)
        object_id_lists = dict()
        for db_map, relationship in relationships:
            if (db_map, relationship["id"]) in prunned_entity_ids:
                continue
            object_id_list = [
                (db_map, id_)
                for id_ in (int(x) for x in relationship["object_id_list"].split(","))
                if (db_map, id_) not in prunned_entity_ids
            ]
            if len(object_id_list) < 2:
                continue
            object_ids.update(object_id_list)
            object_id_lists[db_map, relationship["id"]] = object_id_list
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

    def _get_parameter_positions(self, parameter_name):
        if not parameter_name:
            yield from []
        for db_map in self.db_maps:
            for p in self.db_mngr.get_items_by_field(db_map, "parameter_value", "parameter_name", parameter_name):
                pos = from_database(p["value"])
                if isinstance(pos, float):
                    yield (db_map, p["entity_id"]), pos

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGenerator
        """
        fixed_positions = {}
        if self._persistent:
            for item in self.ui.graphicsView.items():
                if isinstance(item, EntityItem):
                    fixed_positions[item.entity_id] = {"x": item.pos().x(), "y": item.pos().y()}
        param_pos_x = dict(self._get_parameter_positions(self._pos_x_parameter))
        param_pos_y = dict(self._get_parameter_positions(self._pos_y_parameter))
        for entity_id in param_pos_x.keys() & param_pos_y.keys():
            fixed_positions[entity_id] = {"x": param_pos_x[entity_id], "y": param_pos_y[entity_id]}
        entity_ids = self.object_ids + self.relationship_ids
        heavy_positions = {ind: fixed_positions[id_] for ind, id_ in enumerate(entity_ids) if id_ in fixed_positions}
        return GraphLayoutGenerator(
            len(entity_ids), self.src_inds, self.dst_inds, self._ARC_LENGTH_HINT, heavy_positions=heavy_positions
        )

    def _make_new_items(self, x, y):
        """Returns new items for the graph.

        Args:
            x (list)
            y (list)
        """
        self.object_items = list()
        self.relationship_items = list()
        self.arc_items = list()
        for i, object_id in enumerate(self.object_ids):
            object_item = ObjectItem(self, x[i], y[i], self._VERTEX_EXTENT, object_id)
            self.object_items.append(object_item)
        offset = len(self.object_items)
        for i, relationship_id in enumerate(self.relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], 0.5 * self._VERTEX_EXTENT, relationship_id
            )
            self.relationship_items.append(relationship_item)
        for rel_ind, obj_ind in zip(self.src_inds, self.dst_inds):
            arc_item = ArcItem(self.relationship_items[rel_ind - offset], self.object_items[obj_ind], self._ARC_WIDTH)
            self.arc_items.append(arc_item)
        return any(self.object_items)

    def _add_new_items(self):
        for item in self.object_items + self.relationship_items + self.arc_items:
            self.scene.addItem(item)

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        self.hidden_items.extend(self.selected_items)
        for item in self.selected_items:
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
        if len(self.selected_items) == 1:
            return "'" + self.selected_items[0].entity_name + "'"
        return "selected entities"

    def _get_selected_class_names(self):
        if len(self.selected_items) == 1:
            return "'" + self.selected_items[0].entity_class_name + "'"
        return "selected classes"

    @Slot(bool)
    def prune_selected_entities(self, checked=False):
        """Prunes selected items."""
        entity_ids = {x.entity_id for x in self.selected_items}
        key = self._get_selected_entity_names()
        self.prunned_entity_ids[key] = entity_ids
        action = self.ui.menuRestore_pruned.addAction(key)
        action.triggered.connect(lambda checked=False, key=key: self.restore_pruned_items(key))
        self.build_graph()

    @Slot(bool)
    def prune_selected_classes(self, checked=False):
        """Prunes selected items."""
        db_map_class_ids = {}
        for x in self.selected_items:
            db_map_class_ids.setdefault(x.db_map, set()).add(x.entity_class_id)
        entity_ids = {
            (db_map, x["id"])
            for db_map, class_ids in db_map_class_ids.items()
            for x in self.db_mngr.get_items(db_map, "object")
            if x["class_id"] in class_ids
        }
        entity_ids |= {
            (db_map, x["id"])
            for db_map, class_ids in db_map_class_ids.items()
            for x in self.db_mngr.get_items(db_map, "relationship")
            if x["class_id"] in class_ids
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

    def edit_entity_graph_items(self):
        """Starts editing given indexes."""
        obj_items = [item for item in self.selected_items if isinstance(item, ObjectItem)]
        rel_items = [item for item in self.selected_items if isinstance(item, RelationshipItem)]
        self.show_edit_objects_form(obj_items)
        self.show_edit_relationships_form(rel_items)

    def remove_entity_graph_items(self):
        """Removes all selected items in the graph."""
        if not self.selected_items:
            return
        db_map_typed_data = {}
        for item in self.selected_items:
            db_map, id_ = item.entity_id
            db_map_typed_data.setdefault(db_map, {}).setdefault(item.entity_type, set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    @Slot(bool)
    def select_position_parameters(self, checked=False):
        dialog = SelectPositionParametersDialog(self)
        dialog.show()
        dialog.selection_made.connect(self._set_position_parameters)

    @Slot(str, str)
    def _set_position_parameters(self, parameter_pos_x, parameter_pos_y):
        self._pos_x_parameter = parameter_pos_x
        self._pos_y_parameter = parameter_pos_y

    @Slot(bool)
    def save_positions(self, checked=False):
        if not self._pos_x_parameter or not self._pos_y_parameter:
            msg = "You haven't selected the position parameters. Please go to Graph -> Select position parameters"
            self.msg.emit(msg)
            return
        obj_items = [item for item in self.selected_items if isinstance(item, ObjectItem)]
        rel_items = [item for item in self.selected_items if isinstance(item, RelationshipItem)]
        db_map_class_obj_items = {}
        db_map_class_rel_items = {}
        for item in obj_items:
            db_map_class_obj_items.setdefault(item.db_map, {}).setdefault(item.entity_class_name, []).append(item)
        for item in rel_items:
            db_map_class_rel_items.setdefault(item.db_map, {}).setdefault(item.entity_class_name, []).append(item)
        db_map_data = {}
        for db_map, class_obj_items in db_map_class_obj_items.items():
            data = db_map_data.setdefault(db_map, {})
            for class_name, obj_items in class_obj_items.items():
                data["object_parameters"] = [(class_name, self._pos_x_parameter), (class_name, self._pos_y_parameter)]
                data["object_parameter_values"] = [
                    (class_name, item.entity_name, self._pos_x_parameter, item.pos().x()) for item in obj_items
                ] + [(class_name, item.entity_name, self._pos_y_parameter, item.pos().y()) for item in obj_items]
        for db_map, class_rel_items in db_map_class_rel_items.items():
            data = db_map_data.setdefault(db_map, {})
            for class_name, rel_items in class_rel_items.items():
                data["relationship_parameters"] = [
                    (class_name, self._pos_x_parameter),
                    (class_name, self._pos_y_parameter),
                ]
                data["relationship_parameter_values"] = [
                    (class_name, item.object_name_list.split(","), self._pos_x_parameter, item.pos().x())
                    for item in rel_items
                ] + [
                    (class_name, item.object_name_list.split(","), self._pos_y_parameter, item.pos().y())
                    for item in rel_items
                ]
        self.db_mngr.import_data(db_map_data)

    @Slot(bool)
    def clear_saved_positions(self, checked=False):
        if not self.selected_items:
            return
        db_map_ids = {}
        for item in self.selected_items:
            db_map_ids.setdefault(item.db_map, set()).add(item.id_)
        db_map_typed_data = {}
        for db_map, ids in db_map_ids.items():
            db_map_typed_data[db_map] = {
                "parameter_value": set(
                    pv["id"]
                    for parameter_name in (self._pos_x_parameter, self._pos_y_parameter)
                    for pv in self.db_mngr.get_items_by_field(
                        db_map, "parameter_value", "parameter_name", parameter_name
                    )
                    if pv["entity_id"] in ids
                )
            }
        self.db_mngr.remove_items(db_map_typed_data)
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

    def start_relationship(self, relationship_class, obj_item):
        """Starts a relationship from the given object item.

        Args:
            relationship_class (dict)
            obj_item (..graphics_items.ObjectItem)
        """
        db_map = obj_item.db_map
        object_class_ids_to_go = relationship_class["object_class_id_list"].copy()
        object_class_ids_to_go.remove(obj_item.entity_class_id)
        relationship_class["object_class_ids_to_go"] = object_class_ids_to_go
        ch_item = CrossHairsItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.8 * self._VERTEX_EXTENT, entity_id=(db_map, None)
        )
        ch_rel_item = CrossHairsRelationshipItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.5 * self._VERTEX_EXTENT, entity_id=(db_map, None)
        )
        ch_arc_item1 = CrossHairsArcItem(ch_rel_item, obj_item, self._ARC_WIDTH)
        ch_arc_item2 = CrossHairsArcItem(ch_rel_item, ch_item, self._ARC_WIDTH)
        ch_rel_item.refresh_icon()
        self.ui.graphicsView.set_cross_hairs_items(
            relationship_class, [ch_item, ch_rel_item, ch_arc_item1, ch_arc_item2]
        )

    def finalize_relationship(self, relationship_class, *object_items):
        """Tries to add relationships between the given object items.

        Args:
            relationship_class (dict)
            object_items (..graphics_items.ObjectItem)
        """
        db_map = object_items[0].db_map
        relationships = set()
        object_class_id_list = relationship_class["object_class_id_list"]
        for item_permutation in itertools.permutations(object_items):
            if [item.entity_class_id for item in item_permutation] == object_class_id_list:
                relationship = tuple(item.entity_name for item in item_permutation)
                relationships.add(relationship)
        dialog = AddReadyRelationshipsDialog(self, relationship_class, list(relationships), self.db_mngr, db_map)
        dialog.accepted.connect(self._begin_add_relationships)
        dialog.show()

    def _begin_add_relationships(self):
        self._relationships_being_added = True

    def _end_add_relationships(self):
        self._relationships_being_added = False

    def _populate_menu_add_parameter_heat_map(self):
        """Populates the menu 'Add parameter heat map' with parameters for currently shown items in the graph."""
        db_map_class_ids = {}
        for item in self.entity_items:
            db_map_class_ids.setdefault(item.db_map, set()).add(item.entity_class_id)
        db_map_parameters = self.db_mngr.find_cascading_parameter_data(db_map_class_ids, "parameter_definition")
        db_map_class_parameters = {}
        parameter_value_ids = {}
        for db_map, parameters in db_map_parameters.items():
            for p in parameters:
                db_map_class_parameters.setdefault((db_map, p["entity_class_id"]), []).append(p)
            parameter_value_ids = {
                (db_map, pv["parameter_id"], pv["entity_id"]): pv["id"]
                for pv in self.db_mngr.find_cascading_parameter_values_by_definition(
                    {db_map: {x["id"] for x in parameters}}
                )[db_map]
            }
        self._point_value_tuples_per_parameter_name.clear()
        for item in self.entity_items:
            for parameter in db_map_class_parameters.get((item.db_map, item.entity_class_id), ()):
                pv_id = parameter_value_ids.get((item.db_map, parameter["id"], item.id_))
                try:
                    value = float(self.db_mngr.get_value(item.db_map, "parameter_value", pv_id))
                    pos = item.pos()
                    self._point_value_tuples_per_parameter_name.setdefault(parameter["parameter_name"], []).append(
                        (pos.x(), -pos.y(), value)
                    )
                except (TypeError, ValueError):
                    pass
        self.ui.menuAdd_parameter_heat_map.clear()
        for name, point_value_tuples in self._point_value_tuples_per_parameter_name.items():
            if len(point_value_tuples) > 1:
                self.ui.menuAdd_parameter_heat_map.addAction(name)
        self.ui.menuAdd_parameter_heat_map.setDisabled(self.ui.menuAdd_parameter_heat_map.isEmpty())

    @Slot("QAction")
    def add_heat_map(self, action):
        """Adds heat map for the parameter in the action text.
        """
        self._clean_up_heat_map_items()
        point_value_tuples = self._point_value_tuples_per_parameter_name[action.text()]
        x, y, values = zip(*point_value_tuples)
        heat_map, xv, yv, min_x, min_y, max_x, max_y = make_heat_map(x, y, values)
        heat_map_item, hm_figure = make_figure_graphics_item(self.scene, z=-3, static=True)
        colorbar_item, cb_figure = make_figure_graphics_item(self.scene, z=3, static=False)
        colormesh = hm_figure.gca().pcolormesh(xv, yv, heat_map)
        cb_figure.colorbar(colormesh, fraction=1)
        cb_figure.gca().set_visible(False)
        width = max_x - min_x
        height = max_y - min_y
        heat_map_item.widget().setGeometry(min_x, min_y, width, height)
        colorbar_item.widget().setGeometry(max_x + self._VERTEX_EXTENT, min_y, 2 * self._VERTEX_EXTENT, height)
        self.heat_map_items += [heat_map_item, colorbar_item]

    def _clean_up_heat_map_items(self):
        for item in self.heat_map_items:
            item.hide()
            self.scene.removeItem(item)
        self.heat_map_items.clear()

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        super().closeEvent(event)
        self.scene = None
