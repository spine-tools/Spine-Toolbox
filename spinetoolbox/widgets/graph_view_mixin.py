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

import time
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtCore import Qt, Signal, Slot, QTimer
from PySide2.QtWidgets import QGraphicsTextItem
from .custom_menus import GraphViewContextMenu, ObjectItemContextMenu, RelationshipItemContextMenu
from .custom_qwidgets import ZoomWidgetAction
from .shrinking_scene import ShrinkingScene
from .graph_view_graphics_items import EntityItem, ObjectItem, RelationshipItem, ArcItem
from .graph_view_demo import GraphViewDemo
from ..mvcmodels.entity_list_models import ObjectClassListModel, RelationshipClassListModel
from ..helpers import busy_effect


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    graph_created = Signal()

    _node_extent = 64
    _arc_width = 0.25 * _node_extent
    _arc_length_hint = 3 * _node_extent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._added_objects = {}
        self._added_relationships = {}
        self.object_class_list_model = ObjectClassListModel(self, self.db_mngr, self.db_map)
        self.relationship_class_list_model = RelationshipClassListModel(self, self.db_mngr, self.db_map)
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)
        self.hidden_items = list()
        self.rejected_items = list()
        self.removed_items = list()
        self.entity_item_selection = list()
        self._nothing_item = QGraphicsTextItem("Nothing to show.")
        self.zoom_widget_action = None
        area = self.dockWidgetArea(self.ui.dockWidget_item_palette)
        self._handle_item_palette_dock_location_changed(area)
        self.ui.treeView_object.qsettings = self.qsettings
        self.setup_zoom_widget_action()

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_entity_graph.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_item_palette.toggleViewAction())

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.graphicsView.context_menu_requested.connect(self.show_graph_view_context_menu)
        self.ui.graphicsView.item_dropped.connect(self._handle_item_dropped)
        self.ui.dockWidget_entity_graph.visibilityChanged.connect(self._handle_entity_graph_visibility_changed)
        self.ui.dockWidget_item_palette.visibilityChanged.connect(self._handle_item_palette_visibility_changed)
        self.ui.dockWidget_item_palette.dockLocationChanged.connect(self._handle_item_palette_dock_location_changed)
        self.ui.actionHide_selected.triggered.connect(self.hide_selected_items)
        self.ui.actionShow_hidden.triggered.connect(self.show_hidden_items)
        self.ui.actionPrune_selected.triggered.connect(self.prune_selected_items)
        self.ui.actionRestore_pruned.triggered.connect(self.restore_pruned_items)
        self.ui.actionLive_graph_demo.triggered.connect(self.show_demo)
        # Dock Widgets menu action
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_graph_about_to_show)
        self.zoom_widget_action.minus_pressed.connect(self._handle_zoom_minus_pressed)
        self.zoom_widget_action.plus_pressed.connect(self._handle_zoom_plus_pressed)
        self.zoom_widget_action.reset_pressed.connect(self._handle_zoom_reset_pressed)
        # Connect Add more items in Item palette
        self.ui.listView_object_class.clicked.connect(self._add_more_object_classes)
        self.ui.listView_relationship_class.clicked.connect(self._add_more_relationship_classes)

    def setup_zoom_widget_action(self):
        """Setups zoom widget action in view menu."""
        self.zoom_widget_action = ZoomWidgetAction(self.ui.menuView)
        self.ui.menuGraph.addSeparator()
        self.ui.menuGraph.addAction(self.zoom_widget_action)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()

    def receive_object_classes_added(self, db_map_data):
        super().receive_object_classes_added(db_map_data)
        self.object_class_list_model.receive_entity_classes_added(db_map_data)

    def receive_object_classes_updated(self, db_map_data):
        super().receive_object_classes_updated(db_map_data)
        self.object_class_list_model.receive_entity_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        super().receive_object_classes_removed(db_map_data)
        self.object_class_list_model.receive_entity_classes_removed(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        super().receive_relationship_classes_added(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_added(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        super().receive_relationship_classes_updated(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        super().receive_relationship_classes_removed(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_removed(db_map_data)

    def receive_objects_added(self, db_map_data):
        """Runs when objects are added to the db.
        Builds a lookup dictionary consumed by ``add_object``.
        Also, adds the new objects to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_added(db_map_data)
        objects = db_map_data.get(self.db_map, [])
        self._added_objects = {x["id"]: x for x in objects}
        QTimer.singleShot(0, self._ensure_objects_in_graph)

    @Slot()
    def _ensure_objects_in_graph(self):
        """Makes sure all objects in ``self._added_objects`` are materialized in the graph if corresponds.
        It is assumed that ``self._added_objects`` doesn't contain information regarding objects added
        from the graph itself (through Item Palette etc.). These are materialized in ``add_object()``.
        """
        object_ids = self._added_objects.keys()
        restored_ids = self.restore_removed_entities(object_ids)
        rem_class_ids = {x["class_id"] for id_, x in self._added_objects.items() if id_ not in restored_ids}
        sel_class_ids = {
            ind.model().item_from_index(ind).db_map_id(self.db_map)
            for ind in self.object_tree_model.selected_object_class_indexes
        }
        self._added_objects.clear()
        if rem_class_ids.intersection(sel_class_ids):
            self.build_graph()

    def receive_objects_updated(self, db_map_data):
        """Runs when objects are updated in the db. Refreshes names of objects in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_updated(db_map_data)
        updated_ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for item in self.ui.graphicsView.items():
            if isinstance(item, ObjectItem) and item.entity_id in updated_ids:
                item.refresh_name()
                item.refresh_description()

    def receive_objects_removed(self, db_map_data):
        """Runs when objects are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_removed(db_map_data)
        self.hide_removed_entities(db_map_data)

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Builds a lookup dictionary consumed by ``add_relationship``.
        Also, adds the new relationships to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_added(db_map_data)
        relationships = db_map_data.get(self.db_map, [])
        self._added_relationships = {x["id"]: x for x in relationships}
        QTimer.singleShot(0, self._ensure_relationships_in_graph)

    @Slot()
    def _ensure_relationships_in_graph(self):
        """Makes sure all relationships in ``self._added_relationships`` are materialized in the graph if corresponds.
        It is assumed that ``self._added_relationships`` doesn't contain information regarding relationships added
        from the graph itself (through Item Palette etc.). These are materialized in ``add_relationship()``.
        """
        relationship_ids = self._added_relationships.keys()
        restored_ids = self.restore_removed_entities(relationship_ids)
        rem_relationships = [x for id_, x in self._added_relationships.items() if id_ not in restored_ids]
        rem_object_id_lists = [{int(id_) for id_ in x["object_id_list"].split(",")} for x in rem_relationships]
        object_ids = {x.entity_id for x in self.ui.graphicsView.items() if isinstance(x, ObjectItem)}
        self._added_relationships.clear()
        if any(object_ids.intersection(object_id_list) for object_id_list in rem_object_id_lists):
            self.build_graph()

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
            scene = self.ui.graphicsView.scene()
            scene.selectionChanged.disconnect(self._handle_scene_selection_changed)
            for item in removed_items:
                item.set_all_visible(False)
            scene.selectionChanged.connect(self._handle_scene_selection_changed)
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

    @Slot("QModelIndex")
    def _add_more_object_classes(self, index):
        """Runs when the user clicks on the Item palette Object class view.
        Opens the form  to add more object classes if the index is the one that sayes 'New...'.

        Args:
            index (QModelIndex): The clicked index.
        """
        if index == index.model().new_index:
            self.show_add_object_classes_form()

    @Slot("QModelIndex")
    def _add_more_relationship_classes(self, index):
        """Runs when the user clicks on the Item palette Relationship class view.
        Opens the form to add more relationship classes if the index is the one that sayes 'New...'.

        Args:
            index (QModelIndex): The clicked index.
        """
        if index == index.model().new_index:
            self.show_add_relationship_classes_form()

    @Slot()
    def _handle_zoom_minus_pressed(self):
        """Performs a zoom out on the view."""
        self.ui.graphicsView.zoom_out()

    @Slot()
    def _handle_zoom_plus_pressed(self):
        """Performs a zoom in on the view."""
        self.ui.graphicsView.zoom_in()

    @Slot()
    def _handle_zoom_reset_pressed(self):
        """Resets the zoom on the view."""
        self.ui.graphicsView.reset_zoom()

    @Slot()
    def _handle_menu_graph_about_to_show(self):
        """Enables or disables actions according to current selection in the graph."""
        visible = self.ui.dockWidget_entity_graph.isVisible()
        self.ui.actionHide_selected.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionShow_hidden.setEnabled(visible and bool(self.hidden_items))
        self.ui.actionPrune_selected.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionRestore_pruned.setEnabled(visible and bool(self.rejected_items))
        self.zoom_widget_action.setEnabled(visible)

    @Slot("Qt.DockWidgetArea")
    def _handle_item_palette_dock_location_changed(self, area):
        """Runs when the item palette dock widget location changes.
        Adjusts splitter orientation accordingly."""
        if area & (Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea):
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Vertical)
        else:
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Horizontal)

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        if visible:
            self.build_graph()
            self.ui.dockWidget_item_palette.setVisible(True)

    @Slot(bool)
    def _handle_item_palette_visibility_changed(self, visible):
        if visible:
            self.ui.dockWidget_entity_graph.show()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Builds graph."""
        super()._handle_object_tree_selection_changed(selected, deselected)
        if self.ui.dockWidget_entity_graph.isVisible():
            self.build_graph()

    @busy_effect
    def build_graph(self, timeit=False):
        """Builds the graph."""
        tic = time.clock()
        new_items = self._get_new_items()
        wip_items = self._get_wip_items()
        scene = self.new_scene()
        self.hidden_items.clear()
        self.removed_items.clear()
        if not new_items and not wip_items:
            scene.addItem(self._nothing_item)
        else:
            if new_items:
                object_items = new_items[0]
                self._add_new_items(scene, *new_items)  # pylint: disable=no-value-for-parameter
            else:
                object_items = []
            if wip_items:
                self._add_wip_items(scene, object_items, *wip_items)  # pylint: disable=no-value-for-parameter
        self.extend_scene()
        toc = time.clock()
        _ = timeit and self.msg.emit("Graph built in {} seconds\t".format(toc - tic))
        self.graph_created.emit()

    def _get_selected_object_ids(self):
        """Returns a set of ids corresponding to selected objects in the object tree.

        Returns:
            set
        """
        root_index = self.object_tree_model.root_index
        if self.ui.treeView_object.selectionModel().isSelected(root_index):
            return {x["id"] for x in self.db_mngr.get_objects(self.db_map)}
        unique_object_ids = set()
        for index in self.object_tree_model.selected_object_indexes:
            item = index.model().item_from_index(index)
            object_id = item.db_map_id(self.db_map)
            unique_object_ids.add(object_id)
        for index in self.object_tree_model.selected_object_class_indexes:
            item = index.model().item_from_index(index)
            object_class_id = item.db_map_id(self.db_map)
            object_ids = {x["id"] for x in self.db_mngr.get_objects(self.db_map, class_id=object_class_id)}
            unique_object_ids.update(object_ids)
        return unique_object_ids

    def _get_graph_data(self):
        """Returns data for making graph according to selection in Object tree.

        Returns:
            list: integer object ids
            list: integer relationship ids
            list: arc source indices
            list: arc destination indices
        """
        rejected_entity_ids = {x.entity_id for x in self.rejected_items}
        object_ids = self._get_selected_object_ids() - rejected_entity_ids
        relationship_ids = list()
        object_id_lists = list()
        for relationship in self.db_mngr.find_cascading_relationships({self.db_map: object_ids}).get(self.db_map, []):
            if relationship["id"] in rejected_entity_ids:
                continue
            object_id_list = {int(x) for x in relationship["object_id_list"].split(",")} - rejected_entity_ids
            if len(object_id_list) < 2:
                continue
            relationship_ids.append(relationship["id"])
            object_id_lists.append(object_id_list)
            object_ids.update(object_id_list)
        src_inds = list()
        dst_inds = list()
        object_ids = list(object_ids)
        relationship_ind = len(object_ids)
        for object_id_list in object_id_lists:
            object_inds = [object_ids.index(id_) for id_ in object_id_list]
            for object_ind in object_inds:
                src_inds.append(relationship_ind)
                dst_inds.append(object_ind)
            relationship_ind += 1
        return object_ids, relationship_ids, src_inds, dst_inds

    def _get_new_items(self):
        """Returns new items for the graph.

        Returns:
            list: ObjectItem instances
            list: RelationshipItem instances
            list: ArcItem instances
        """
        object_ids, relationship_ids, src_inds, dst_inds = self._get_graph_data()
        d = self.shortest_path_matrix(
            len(object_ids) + len(relationship_ids), src_inds, dst_inds, self._arc_length_hint
        )
        if d is None:
            return []
        x, y = self.vertex_coordinates(d)
        object_items = list()
        relationship_items = list()
        arc_items = list()
        for i, object_id in enumerate(object_ids):
            object_item = ObjectItem(self, x[i], y[i], self._node_extent, entity_id=object_id)
            object_items.append(object_item)
        offset = len(object_items)
        for i, relationship_id in enumerate(relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], self._node_extent, entity_id=relationship_id
            )
            relationship_items.append(relationship_item)
        for rel_ind, obj_ind in zip(src_inds, dst_inds):
            arc_item = ArcItem(relationship_items[rel_ind - offset], object_items[obj_ind], self._arc_width)
            arc_items.append(arc_item)
        return object_items, relationship_items, arc_items

    def _get_wip_items(self):
        """Removes wip items from the current scene and returns them.

        Returns:
            list: ObjectItem instances
            list: RelationshipItem instances
            list: ArcItem instances
        """
        scene = self.ui.graphicsView.scene()
        if not scene:
            return []
        obj_items = set()
        rel_items = list()
        arc_items = list()
        for item in scene.items():
            if isinstance(item, RelationshipItem) and item.is_wip:
                rel_items.append(item)
                arc_items.extend(item.arc_items)
                obj_items.update(arc_item.obj_item for arc_item in item.arc_items)
        for obj_item in obj_items:
            obj_item.arc_items = [arc for arc in obj_item.arc_items if arc in arc_items]
            scene.removeItem(obj_item)
        for arc_item in arc_items:
            scene.removeItem(arc_item)
        for rel_item in rel_items:
            scene.removeItem(rel_item)
        return list(obj_items), rel_items, arc_items

    @staticmethod
    def _add_new_items(scene, object_items, relationship_items, arc_items):
        for item in object_items + relationship_items + arc_items:
            scene.addItem(item)

    @staticmethod
    def _add_wip_items(scene, new_object_items, wip_object_items, wip_relationship_items, wip_arc_items):
        """Adds wip items to the given scene, merging wip object items with existing ones by entity id.

        Args:
            scene (QGraphicsScene)
            new_object_items (list)
            wip_object_items (list)
            wip_relationship_items (list)
            wip_arc_items (list)
        """
        object_items_lookup = dict()
        for object_item in new_object_items:
            object_items_lookup[object_item.entity_id] = object_item
        for item in wip_object_items + wip_relationship_items + wip_arc_items:
            scene.addItem(item)
        for obj_item in wip_object_items:
            obj_item._merge_target = object_items_lookup.get(obj_item.entity_id)
            if obj_item._merge_target:
                obj_item.merge_into_target(force=True)

    @staticmethod
    def shortest_path_matrix(N, src_inds, dst_inds, spread):
        """Returns the shortest-path matrix.

        Args:
            N (int): The number of nodes in the graph.
            src_inds (list): Source indices
            dst_inds (list): Destination indices
            spread (int): The desired 'distance' between neighbours
        """
        if not N:
            return None
        dist = np.zeros((N, N))
        src_inds = arr(src_inds)
        dst_inds = arr(dst_inds)
        try:
            dist[src_inds, dst_inds] = dist[dst_inds, src_inds] = spread
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        d[d == np.inf] = spread * 3
        d[d == 0] = spread * 1e-6
        return d

    @staticmethod
    def sets(N):
        """Returns sets of vertex pairs indices.

        Args:
            N (int)
        """
        sets = []
        for n in range(1, N):
            pairs = np.zeros((N - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(N - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(N - n), 2 * n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if s1.any():
                sets.append(s1)
            if s2.any():
                sets.append(s2)
        return sets

    @staticmethod
    def vertex_coordinates(matrix, heavy_positions=None, iterations=10, weight_exp=-2, initial_diameter=1000):
        """Returns x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
        if heavy_positions is None:
            heavy_positions = dict()
        N = len(matrix)
        if N == 1:
            return [0], [0]
        mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))  # Upper triangular except diagonal
        np.random.seed(0)
        layout = np.random.rand(N, 2) * initial_diameter - initial_diameter / 2  # Random layout with initial diameter
        heavy_ind_list = list()
        heavy_pos_list = list()
        for ind, pos in heavy_positions.items():
            heavy_ind_list.append(ind)
            heavy_pos_list.append([pos.x(), pos.y()])
        heavy_ind = arr(heavy_ind_list)
        heavy_pos = arr(heavy_pos_list)
        if heavy_ind.any():
            layout[heavy_ind, :] = heavy_pos
        weights = matrix ** weight_exp  # bus-pair weights (lower for distant buses)
        maxstep = 1 / np.min(weights[mask])
        minstep = 1 / np.max(weights[mask])
        lambda_ = np.log(minstep / maxstep) / (iterations - 1)  # exponential decay of allowed adjustment
        sets = GraphViewMixin.sets(N)  # construct sets of bus pairs
        for iteration in range(iterations):
            step = maxstep * np.exp(lambda_ * iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(N)  # we don't want to use the same pair order each iteration
            for p in sets:
                v1, v2 = rand_order[p[:, 0]], rand_order[p[:, 1]]  # arrays of vertex1 and vertex2
                # current distance (possibly accounting for system rescaling)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] / 2 * (layout[v1] - layout[v2]) / dist[:, None]  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
                if heavy_ind.any():
                    layout[heavy_ind, :] = heavy_pos
        return layout[:, 0], layout[:, 1]

    def new_scene(self):
        """Replaces the current scene with a new one."""
        self.tear_down_scene()
        scene = ShrinkingScene(100.0, 100.0, None)
        self.ui.graphicsView.setScene(scene)
        scene.changed.connect(self._handle_scene_changed)
        scene.selectionChanged.connect(self._handle_scene_selection_changed)
        return scene

    def tear_down_scene(self):
        """Removes all references to this form in graphics items and schedules
        the scene for deletion."""
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        scene.deleteLater()

    def extend_scene(self):
        """Extends the scene to show all items."""
        bounding_rect = self.ui.graphicsView.scene().itemsBoundingRect()
        self.ui.graphicsView.scene().setSceneRect(bounding_rect)
        self.ui.graphicsView.init_zoom()

    @Slot()
    def _handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        scene = self.ui.graphicsView.scene()
        selected_items = scene.selectedItems()
        self.entity_item_selection = [x for x in selected_items if isinstance(x, EntityItem)]
        selected_objs = {self.db_map: []}
        selected_rels = {self.db_map: []}
        for item in selected_items:
            if isinstance(item, ObjectItem):
                selected_objs[self.db_map].append(item.db_representation)
            elif isinstance(item, RelationshipItem):
                selected_rels[self.db_map].append(item.db_representation)
        cascading_rels = self.db_mngr.find_cascading_relationships(self.db_mngr._to_ids(selected_objs))
        selected_rels = self._extend_merge(selected_rels, cascading_rels)
        for db_map, items in selected_objs.items():
            self.selected_ent_cls_ids["object class"].setdefault(db_map, set()).update({x["class_id"] for x in items})
        for db_map, items in selected_rels.items():
            self.selected_ent_cls_ids["relationship class"].setdefault(db_map, set()).update(
                {x["class_id"] for x in items}
            )
        self.selected_ent_ids["object"] = self._db_map_class_id_data(selected_objs)
        self.selected_ent_ids["relationship"] = self._db_map_class_id_data(selected_rels)
        self.update_filter()

    @Slot(list)
    def _handle_scene_changed(self, region):
        """Enlarges the scene rect if needed."""
        scene_rect = self.ui.graphicsView.scene().sceneRect()
        if all(scene_rect.contains(rect) for rect in region):
            return
        extended_rect = scene_rect
        for rect in region:
            extended_rect = extended_rect.united(rect)
        self.ui.graphicsView.scene().setSceneRect(extended_rect)

    @Slot("QPoint", "QString")
    def _handle_item_dropped(self, pos, text):
        """Runs when an item is dropped from Item palette onto the view.
        Creates the object or relationship template.

        Args:
            pos (QPoint)
            text (str)
        """
        scene = self.ui.graphicsView.scene()
        if not scene:
            scene = self.new_scene()
        if scene.items() == [self._nothing_item]:
            scene.removeItem(self._nothing_item)
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        entity_type, entity_class_id = text.split(":")
        entity_class_id = int(entity_class_id)
        if entity_type == "object class":
            object_item = ObjectItem(
                self, scene_pos.x(), scene_pos.y(), self._node_extent, entity_class_id=entity_class_id
            )
            scene.addItem(object_item)
            self.ui.graphicsView.setFocus()
            object_item.edit_name()
        elif entity_type == "relationship class":
            self.add_wip_relationship(scene, scene_pos, entity_class_id)
        self.extend_scene()
        self.graph_created.emit()

    def add_wip_relationship(self, scene, pos, relationship_class_id, center_item=None, center_dimension=None):
        """Makes items for a wip relationship and adds them to the scene at the given coordinates.

        Args:
            scene (QGraphicsScene)
            pos (QPointF)
            relationship_class_id (int)
            center_item_dimension (tuple, optional): A tuple of (ObjectItem, dimension) to put at the center of the wip item.

        """
        relationship_class = self.db_mngr.get_item(self.db_map, "relationship class", relationship_class_id)
        if not relationship_class:
            return
        object_class_id_list = [int(id_) for id_ in relationship_class["object_class_id_list"].split(",")]
        dimension_count = len(object_class_id_list)
        rel_inds = [dimension_count for _ in range(dimension_count)]
        obj_inds = list(range(dimension_count))
        d = self.shortest_path_matrix(dimension_count + 1, rel_inds, obj_inds, self._arc_length_hint)
        if d is None:
            return
        x, y = self.vertex_coordinates(d)
        # Fix position
        x_offset = pos.x()
        y_offset = pos.y()
        if center_item:
            center = center_item.sceneBoundingRect().center()
            x_offset -= pos.x() - center.x()
            y_offset -= pos.y() - center.y()
        x += x_offset
        y += y_offset
        relationship_item = RelationshipItem(
            self, x[-1], y[-1], self._node_extent, entity_class_id=relationship_class_id
        )
        object_items = list()
        arc_items = list()
        for i, object_class_id in enumerate(object_class_id_list):
            object_item = ObjectItem(self, x[i], y[i], self._node_extent, entity_class_id=object_class_id)
            object_items.append(object_item)
            arc_item = ArcItem(relationship_item, object_item, self._arc_width, is_wip=True)
            arc_items.append(arc_item)
        entity_items = object_items + [relationship_item]
        for item in entity_items + arc_items:
            scene.addItem(item)
        if center_item and center_dimension is not None:
            center_item._merge_target = object_items[center_dimension]
            center_item.merge_into_target()
        self.extend_scene()

    def add_object(self, object_class_id, name):
        """Adds object to the database.

        Args:
            object_class_id (int)
            name (str)

        Returns:
            int, NoneType: The id of the added object if successful, None otherwise.
        """
        item = dict(class_id=object_class_id, name=name)
        db_map_data = {self.db_map: [item]}
        self.db_mngr.add_objects(db_map_data)
        object_lookup = {(v["class_id"], v["name"]): k for k, v in self._added_objects.items()}
        object_id = object_lookup.get((object_class_id, name), None)
        if object_id is not None:
            self._added_objects.pop(object_id)
        return object_id

    def update_object(self, object_id, name):
        """Updates object in the db.

        Args:
            object_id (int)
            name (str)
        """
        item = dict(id=object_id, name=name)
        db_map_data = {self.db_map: [item]}
        self.db_mngr.update_objects(db_map_data)

    def add_relationship(self, class_id, object_id_list, object_name_list):
        """Adds relationship to the db.

        Args:
            class_id (int)
            object_id_list (list)
        """
        class_name = self.db_mngr.get_item(self.db_map, "relationship class", class_id)["name"]
        name = class_name + "_" + "__".join(object_name_list)
        relationship = {'name': name, 'object_id_list': object_id_list, 'class_id': class_id}
        self.db_mngr.add_relationships({self.db_map: [relationship]})
        object_id_list = ",".join([str(id_) for id_ in object_id_list])
        relationship_lookup = {(v["class_id"], v["object_id_list"]): k for k, v in self._added_relationships.items()}
        relationship_id = relationship_lookup.get((class_id, object_id_list), None)
        if relationship_id is not None:
            self._added_relationships.pop(relationship_id)
        return relationship_id

    @Slot("QPoint")
    def show_graph_view_context_menu(self, global_pos):
        """Shows context menu for graphics view.

        Args:
            global_pos (QPoint)
        """
        menu = GraphViewContextMenu(self, global_pos)
        option = menu.get_action()
        if option == "Hide selected":
            self.hide_selected_items()
        elif option == "Show hidden":
            self.show_hidden_items()
        elif option == "Prune selected":
            self.prune_selected_items()
        elif option == "Restore pruned":
            self.restore_pruned_items()
        else:
            pass
        menu.deleteLater()

    @Slot(bool)
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        self.hidden_items.extend(self.entity_item_selection)
        for item in self.entity_item_selection:
            item.set_all_visible(False)

    @Slot(bool)
    def show_hidden_items(self, checked=False):
        """Shows hidden items."""
        if not self.ui.graphicsView.scene():
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
        self.hidden_items.clear()

    @Slot(bool)
    def prune_selected_items(self, checked=False):
        """Prunes selected items."""
        self.rejected_items.extend(self.entity_item_selection)
        self.build_graph()

    @Slot(bool)
    def restore_pruned_items(self, checked=False):
        """Reinstates pruned items."""
        self.rejected_items.clear()
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

    def show_object_item_context_menu(self, global_pos, main_item):
        """Shows context menu for entity item.

        Args:
            global_pos (QPoint)
            main_item (spinetoolbox.widgets.graph_view_graphics_items.ObjectItem)
        """
        menu = ObjectItemContextMenu(self, global_pos, main_item)
        option = menu.get_action()
        if self._apply_entity_context_menu_option(option):
            pass
        elif option in ('Set name', 'Rename'):
            main_item.edit_name()
        elif option in menu.relationship_class_dict:
            relationship_class = menu.relationship_class_dict[option]
            relationship_class_id = relationship_class["id"]
            dimension = relationship_class['dimension']
            scene = self.ui.graphicsView.scene()
            self.add_wip_relationship(
                scene, global_pos, relationship_class_id, center_item=main_item, center_dimension=dimension
            )
        menu.deleteLater()

    def show_relationship_item_context_menu(self, global_pos):
        """Shows context menu for entity item.

        Args:
            global_pos (QPoint)
        """
        menu = RelationshipItemContextMenu(self, global_pos)
        option = menu.get_action()
        self._apply_entity_context_menu_option(option)
        menu.deleteLater()

    def _apply_entity_context_menu_option(self, option):
        if option == 'Hide':
            self.hide_selected_items()
        elif option == 'Prune':
            self.prune_selected_items()
        elif option == 'Remove':
            self.remove_graph_items()
        else:
            return False
        return True

    @Slot("bool")
    def remove_graph_items(self, checked=False):
        """Removes all selected items in the graph."""
        if not self.entity_item_selection:
            return
        db_map_typed_data = {self.db_map: {}}
        for item in self.entity_item_selection:
            if item.is_wip:
                item.wipe_out()
            else:
                db_item = item.db_representation
                db_map_typed_data[self.db_map].setdefault(item.entity_type, []).append(db_item)
        self.db_mngr.remove_items(db_map_typed_data)

    def closeEvent(self, event=None):
        """Handles close window event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        self.tear_down_scene()
