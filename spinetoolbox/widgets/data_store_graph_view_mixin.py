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

from PySide2.QtCore import Qt, Signal, Slot, QTimer, QRectF
from PySide2.QtWidgets import QGraphicsTextItem
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtGui import QPainter
from spinedb_api import to_database, from_database
from .custom_menus import GraphViewContextMenu, ObjectItemContextMenu, RelationshipItemContextMenu
from .custom_qwidgets import ZoomWidgetAction
from .shrinking_scene import ShrinkingScene
from .data_store_graphics_items import EntityItem, ObjectItem, RelationshipItem, ArcItem
from .data_store_graph_view_demo import GraphViewDemo
from .data_store_graph_layout_generator import GraphLayoutGenerator
from ..mvcmodels.entity_list_models import ObjectClassListModel, RelationshipClassListModel
from ..helpers import get_save_file_name_in_last_dir


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    objects_added_to_graph = Signal()
    relationships_added_to_graph = Signal()

    _POS_STR = "graph_view_position"
    _VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.15 * _VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.5 * _VERTEX_EXTENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._added_objects = {}
        self._added_relationships = {}
        self.object_class_list_model = ObjectClassListModel(self, self.db_mngr, self.db_map)
        self.relationship_class_list_model = RelationshipClassListModel(self, self.db_mngr, self.db_map)
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)
        self.object_ids = list()
        self.relationship_ids = list()
        self.src_inds = list()
        self.dst_inds = list()
        self.wip_items = tuple()
        self.hidden_items = list()
        self.prunned_entity_ids = dict()
        self.removed_items = list()
        self.entity_item_selection = list()
        self._blank_item = None
        self.zoom_widget_action = None
        self.layout_gens = list()
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
        self.ui.actionPrune_selected_entities.triggered.connect(self.prune_selected_entities)
        self.ui.actionPrune_selected_classes.triggered.connect(self.prune_selected_classes)
        self.ui.actionRestore_all_pruned.triggered.connect(self.restore_all_pruned_items)
        self.ui.actionLive_graph_demo.triggered.connect(self.show_demo)
        self.ui.actionSave_positions.triggered.connect(self.save_positions)
        self.ui.actionClear_positions.triggered.connect(self.clear_saved_positions)
        self.ui.actionExport_as_pdf.triggered.connect(self.export_as_pdf)
        # Dock Widgets menu action
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_graph_about_to_show)
        self.zoom_widget_action.minus_pressed.connect(self._handle_zoom_minus_pressed)
        self.zoom_widget_action.plus_pressed.connect(self._handle_zoom_plus_pressed)
        self.zoom_widget_action.reset_pressed.connect(self._handle_zoom_reset_pressed)
        # Connect Add more items in Item palette
        self.ui.listView_object_class.clicked.connect(self._add_more_object_classes)
        self.ui.listView_relationship_class.clicked.connect(self._add_more_relationship_classes)
        # Added to graph
        self.objects_added_to_graph.connect(self._ensure_objects_in_graph)
        self.relationships_added_to_graph.connect(self._ensure_relationships_in_graph)

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

    def receive_object_classes_fetched(self, db_map_data):
        super().receive_object_classes_fetched(db_map_data)
        self.object_class_list_model.receive_entity_classes_added(db_map_data)

    def receive_relationship_classes_fetched(self, db_map_data):
        super().receive_relationship_classes_fetched(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_added(db_map_data)

    def receive_object_classes_added(self, db_map_data):
        super().receive_object_classes_added(db_map_data)
        self.object_class_list_model.receive_entity_classes_added(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        super().receive_relationship_classes_added(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_added(db_map_data)

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
        self.objects_added_to_graph.emit()

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
        self.relationships_added_to_graph.emit()

    def receive_object_classes_updated(self, db_map_data):
        super().receive_object_classes_updated(db_map_data)
        self.object_class_list_model.receive_entity_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        super().receive_relationship_classes_updated(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_updated(db_map_data)
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

    def receive_object_classes_removed(self, db_map_data):
        super().receive_object_classes_removed(db_map_data)
        self.object_class_list_model.receive_entity_classes_removed(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        super().receive_relationship_classes_removed(db_map_data)
        self.relationship_class_list_model.receive_entity_classes_removed(db_map_data)

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

    @Slot()
    def _ensure_objects_in_graph(self):
        QTimer.singleShot(0, self._do_ensure_objects_in_graph)

    @Slot()
    def _do_ensure_objects_in_graph(self):
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

    @Slot()
    def _ensure_relationships_in_graph(self):
        QTimer.singleShot(0, self._do_ensure_relationships_in_graph)

    @Slot()
    def _do_ensure_relationships_in_graph(self):
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
        scene = self.ui.graphicsView.scene()
        has_graph = scene is not None and scene.items() != [self._blank_item]
        self.ui.actionSave_positions.setEnabled(has_graph)
        self.ui.actionClear_positions.setEnabled(has_graph)
        self.ui.actionExport_as_pdf.setEnabled(has_graph)
        self.ui.actionHide_selected.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionShow_hidden.setEnabled(visible and bool(self.hidden_items))
        self.ui.actionPrune_selected_entities.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.actionPrune_selected_classes.setEnabled(visible and bool(self.entity_item_selection))
        self.ui.menuRestore_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.ui.actionRestore_all_pruned.setEnabled(visible and any(self.prunned_entity_ids.values()))
        self.zoom_widget_action.setEnabled(visible)
        self.ui.actionPrune_selected_entities.setText(f"Prune {self._get_selected_entity_names()}")
        self.ui.actionPrune_selected_classes.setText(f"Prune {self._get_selected_class_names()}")

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

    @Slot("QItemSelection", "QItemSelection")
    def _handle_relationship_tree_selection_changed(self, selected, deselected):
        """Builds graph."""
        super()._handle_relationship_tree_selection_changed(selected, deselected)
        if self.ui.dockWidget_entity_graph.isVisible():
            self.build_graph()

    def build_graph(self):
        """Builds the graph."""
        for layout_gen in self.layout_gens:
            layout_gen.stop()
        self.object_ids, self.relationship_ids, self.src_inds, self.dst_inds = self._get_graph_data()
        if not self.wip_items:
            self.wip_items = self._get_wip_items()
        layout_gen = self._make_layout_generator()
        self.layout_gens.append(layout_gen)
        progress_widget = layout_gen.create_progress_widget()
        scene = self.new_scene()
        scene.addWidget(progress_widget)
        self.extend_scene()
        self.ui.graphicsView.gentle_zoom(0.5)
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
        new_items = self._get_new_items(x, y)
        scene = self.new_scene()
        self.hidden_items.clear()
        self.removed_items.clear()
        if not any(new_items) and not any(self.wip_items):
            self._blank_item = QGraphicsTextItem("Nothing to show.")
            scene.addItem(self._blank_item)
        else:
            if new_items:
                object_items = new_items[0]
                self._add_new_items(scene, *new_items)  # pylint: disable=no-value-for-parameter
            else:
                object_items = []
            if self.wip_items:
                self._add_wip_items(scene, object_items, *self.wip_items)  # pylint: disable=no-value-for-parameter
                self.wip_items = tuple()
        self.extend_scene()

    def _get_selected_entity_ids(self):
        """Returns a set of ids corresponding to selected entities in the trees.

        Returns:
            set: selected object ids
            set: selected relationship ids
        """
        if self._selection_source not in (self.ui.treeView_object, self.ui.treeView_relationship):
            return set(), set()
        model = self._selection_source.model()
        if self._selection_source.selectionModel().isSelected(model.root_index):
            if self._selection_source is self.ui.treeView_object:
                return {x["id"] for x in self.db_mngr.get_items(self.db_map, "object")}, set()
            return set(), {x["id"] for x in self.db_mngr.get_items(self.db_map, "relationship")}
        selected_object_ids = set()
        selected_relationship_ids = set()
        for index in model.selected_object_indexes:
            item = index.model().item_from_index(index)
            object_id = item.db_map_id(self.db_map)
            selected_object_ids.add(object_id)
        for index in model.selected_relationship_indexes:
            item = index.model().item_from_index(index)
            relationship_id = item.db_map_id(self.db_map)
            selected_relationship_ids.add(relationship_id)
        for index in model.selected_object_class_indexes:
            item = index.model().item_from_index(index)
            object_ids = set(item._get_children_ids(self.db_map))
            selected_object_ids.update(object_ids)
        for index in model.selected_relationship_class_indexes:
            item = index.model().item_from_index(index)
            relationship_ids = set(item._get_children_ids(self.db_map))
            selected_relationship_ids.update(relationship_ids)
        return selected_object_ids, selected_relationship_ids

    def _get_graph_data(self):
        """Returns data for making graph according to selection in trees.

        Returns:

        """
        object_ids, relationship_ids = self._get_selected_entity_ids()
        prunned_entity_ids = {id_ for ids in self.prunned_entity_ids.values() for id_ in ids}
        object_ids -= prunned_entity_ids
        relationship_ids -= prunned_entity_ids
        only_selected_objects = self.qsettings.value("appSettings/onlySelectedObjects", defaultValue="false")
        cond = all if only_selected_objects == "true" else any
        relationships = [
            x
            for x in self.db_mngr.get_items(self.db_map, "relationship")
            if cond([int(id_) in object_ids for id_ in x["object_id_list"].split(",")])
        ]
        relationships += [self.db_mngr.get_item(self.db_map, "relationship", id_) for id_ in relationship_ids]
        relationship_ids = list()
        object_id_lists = list()
        for relationship in relationships:
            if relationship["id"] in prunned_entity_ids:
                continue
            object_id_list = {int(x) for x in relationship["object_id_list"].split(",")} - prunned_entity_ids
            if len(object_id_list) < 2:
                continue
            object_ids.update(object_id_list)
            relationship_ids.append(relationship["id"])
            object_id_lists.append(object_id_list)
        object_ids = list(object_ids)
        src_inds, dst_inds = self._get_src_dst_inds(object_ids, object_id_lists)
        return object_ids, relationship_ids, src_inds, dst_inds

    @staticmethod
    def _get_src_dst_inds(object_ids, object_id_lists):
        src_inds = list()
        dst_inds = list()
        relationship_ind = len(object_ids)
        for object_id_list in object_id_lists:
            object_inds = [object_ids.index(id_) for id_ in object_id_list]
            for object_ind in object_inds:
                src_inds.append(relationship_ind)
                dst_inds.append(object_ind)
            relationship_ind += 1
        return src_inds, dst_inds

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGenerator
        """
        entity_ids = self.object_ids + self.relationship_ids
        pos_lookup = {
            p["entity_id"]: dict(from_database(p["value"]).value_to_database_data())
            for p in self.db_mngr.get_items_by_field(self.db_map, "parameter value", "parameter_name", self._POS_STR)
        }
        heavy_positions = {ind: pos_lookup[id_] for ind, id_ in enumerate(entity_ids) if id_ in pos_lookup}
        return GraphLayoutGenerator(
            len(entity_ids), self.src_inds, self.dst_inds, self._ARC_LENGTH_HINT, heavy_positions=heavy_positions
        )

    def _get_new_items(self, x, y):
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
            object_item = ObjectItem(self, x[i], y[i], self._VERTEX_EXTENT, entity_id=object_id)
            object_items.append(object_item)
        offset = len(object_items)
        for i, relationship_id in enumerate(self.relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], 0.5 * self._VERTEX_EXTENT, entity_id=relationship_id
            )
            relationship_items.append(relationship_item)
        for rel_ind, obj_ind in zip(self.src_inds, self.dst_inds):
            arc_item = ArcItem(relationship_items[rel_ind - offset], object_items[obj_ind], self._ARC_WIDTH)
            arc_items.append(arc_item)
        return (object_items, relationship_items, arc_items)

    def _get_wip_items(self):
        """Removes wip items from the current scene and returns them.

        Returns:
            list: ObjectItem instances
            list: RelationshipItem instances
            list: ArcItem instances
        """
        scene = self.ui.graphicsView.scene()
        if not scene:
            return ()
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
        return (list(obj_items), rel_items, arc_items)

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
        if scene.items() == [self._blank_item]:
            scene.removeItem(self._blank_item)
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        entity_type, entity_class_id = text.split(":")
        entity_class_id = int(entity_class_id)
        if entity_type == "object class":
            object_item = ObjectItem(
                self, scene_pos.x(), scene_pos.y(), self._VERTEX_EXTENT, entity_class_id=entity_class_id
            )
            scene.addItem(object_item)
            self.ui.graphicsView.setFocus()
            object_item.edit_name()
        elif entity_type == "relationship class":
            self.add_wip_relationship(scene, scene_pos, entity_class_id)
        self.extend_scene()

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
        layout_gen = GraphLayoutGenerator(dimension_count + 1, rel_inds, obj_inds, self._ARC_LENGTH_HINT)
        x, y = layout_gen.get_coordinates()
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
            self, x[-1], y[-1], 0.5 * self._VERTEX_EXTENT, entity_class_id=relationship_class_id
        )
        object_items = list()
        arc_items = list()
        for i, object_class_id in enumerate(object_class_id_list):
            object_item = ObjectItem(self, x[i], y[i], self._VERTEX_EXTENT, entity_class_id=object_class_id)
            object_items.append(object_item)
            arc_item = ArcItem(relationship_item, object_item, self._ARC_WIDTH, is_wip=True)
            arc_items.append(arc_item)
        entity_items = object_items + [relationship_item]
        for item in entity_items + arc_items:
            scene.addItem(item)
        if center_item and center_dimension is not None:
            center_item._merge_target = object_items[center_dimension]
            center_item.merge_into_target()

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
        menu = GraphViewContextMenu(self)
        menu.exec_(global_pos)
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

    def show_object_item_context_menu(self, global_pos, main_item):
        """Shows context menu for entity item.

        Args:
            global_pos (QPoint)
            main_item (spinetoolbox.widgets.graph_view_graphics_items.ObjectItem)
        """
        menu = ObjectItemContextMenu(self, global_pos, main_item)
        option = menu.get_action()
        if option == 'Remove':
            self.remove_graph_items()
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
        if option == 'Remove':
            self.remove_graph_items()
        menu.deleteLater()

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

    @Slot(bool)
    def save_positions(self, checked=False):
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        class_items = {}
        for item in scene.items():
            if isinstance(item, EntityItem):
                class_items.setdefault(item.entity_class_id, []).append(item)
        pos_def_class_ids = {
            p["entity_class_id"]
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter definition", "parameter_name", self._POS_STR
            )
        }
        defs_to_add = [
            {"name": self._POS_STR, "entity_class_id": class_id} for class_id in class_items.keys() - pos_def_class_ids
        ]
        if defs_to_add:
            self.db_mngr.add_parameter_definitions({self.db_map: defs_to_add})
        pos_def_id_lookup = {
            p["entity_class_id"]: p["id"]
            for p in self.db_mngr.get_items_by_field(
                self.db_map, "parameter definition", "parameter_name", self._POS_STR
            )
        }
        pos_val_id_lookup = {
            (p["entity_class_id"], p["entity_id"]): p["id"]
            for p in self.db_mngr.get_items_by_field(self.db_map, "parameter value", "parameter_name", self._POS_STR)
        }
        vals_to_add = list()
        vals_to_update = list()
        for class_id, items in class_items.items():
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
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        entity_ids = {x.entity_id for x in scene.items() if isinstance(x, EntityItem)}
        vals_to_remove = [
            p
            for p in self.db_mngr.get_items_by_field(self.db_map, "parameter value", "parameter_name", self._POS_STR)
            if p["entity_id"] in entity_ids
        ]
        if vals_to_remove:
            self.db_mngr.remove_items({self.db_map: {"parameter value": vals_to_remove}})
        self.build_graph()

    @Slot(bool)
    def export_as_pdf(self, checked=False):
        self.qsettings.beginGroup(self.settings_group)
        file_name, _ = get_save_file_name_in_last_dir(
            self.qsettings,
            "exportGraphAsPDF",
            self,
            "Export as PDF...",
            self._get_base_dir(),
            filter_="PDF files (*.pdf)",
        )
        self.qsettings.endGroup()
        if not file_name:
            return
        scene = self.ui.graphicsView.scene()
        source = scene.itemsBoundingRect()
        printer = QPrinter()
        printer.setPaperSize(source.size(), QPrinter.Point)
        printer.setOutputFileName(file_name)
        painter = QPainter(printer)
        scene.render(painter, QRectF(), source)
        painter.end()
        self.msg.emit(f"File {file_name} successfully exported.")

    def closeEvent(self, event=None):
        """Handles close window event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        self.tear_down_scene()
