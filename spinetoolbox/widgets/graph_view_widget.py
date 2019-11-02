######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the GraphViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import time
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtWidgets import QApplication, QWidgetAction
from PySide2.QtCore import Qt, Slot
from .data_store_widget import DataStoreForm
from .custom_menus import (
    SimpleEditableParameterValueContextMenu,
    GraphViewContextMenu,
    ObjectItemContextMenu,
    RelationshipItemContextMenu,
)
from .custom_qwidgets import ZoomWidget
from .report_plotting_failure import report_plotting_failure
from .shrinking_scene import ShrinkingScene
from ..mvcmodels.entity_list_models import ObjectClassListModel, RelationshipClassListModel
from ..graph_view_graphics_items import EntityItem, ObjectItem, RelationshipItem, ArcItem, InteractiveTextItem
from ..helpers import busy_effect
from ..plotting import plot_selection, PlottingError, GraphAndTreeViewPlottingHints


class GraphViewForm(DataStoreForm):
    """A widget to show Spine databases in a graph."""

    _node_extent = 64
    _arc_width = 0.2 * _node_extent
    _arc_length_hint = 3 * _node_extent

    def __init__(self, project, *db_maps, read_only=False):
        """Initializes class.

        Args:
            project (SpineToolboxProject): The project instance that owns this form.
            *db_maps (DiffDatabaseMapping): Databases to view.
            read_only (bool): Whether or not the form should be editable.
        """
        from ..ui.graph_view_form import Ui_MainWindow

        tic = time.clock()
        super().__init__(project, Ui_MainWindow(), *db_maps)
        self.db_map = next(iter(db_maps))
        self.db_name = self.db_map.codename
        self.read_only = read_only
        self._usage_item = None
        # Lookups, used for adding objects and relationships
        self._added_objects = {}
        self._added_relationships = {}
        # Item palette models
        self.object_class_list_model = ObjectClassListModel(self, self.db_mngr, self.db_map)
        self.relationship_class_list_model = RelationshipClassListModel(self, self.db_mngr, self.db_map)
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)
        # Hidden and rejected items
        self.hidden_items = list()
        self.rejected_items = list()
        # Current item selection
        self.entity_item_selection = list()
        self.arc_item_selection = list()
        # Zoom widget and action
        self.zoom_widget_action = None
        self.zoom_widget = None
        # Set up splitters
        area = self.dockWidgetArea(self.ui.dockWidget_item_palette)
        self._handle_item_palette_dock_location_changed(area)
        # Override mouse press event of object tree view
        self.ui.treeView_object.qsettings = self.qsettings
        # Set up dock widgets
        self.restore_dock_widgets()
        # Initialize stuff
        self.init_models()
        self.setup_delegates()
        self.add_toggle_view_actions()
        self.setup_zoom_action()
        self.connect_signals()
        self.settings_group = "graphViewWidget" if not self.read_only else "graphViewWidgetReadOnly"
        self.restore_ui()
        self.init_commit_rollback_actions()
        title = self.db_name + " (read only) " if read_only else self.db_name
        self.setWindowTitle("Data store graph view    -- {} --".format(title))
        toc = time.clock()
        self.msg.emit("Graph view form created in {} seconds\t".format(toc - tic))

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.graphicsView.context_menu_requested.connect(self.show_graph_view_context_menu)
        self.ui.graphicsView.item_dropped.connect(self._handle_item_dropped)
        self.ui.dockWidget_item_palette.dockLocationChanged.connect(self._handle_item_palette_dock_location_changed)
        self.ui.actionGraph_hide_selected.triggered.connect(self.hide_selected_items)
        self.ui.actionGraph_show_hidden.triggered.connect(self.show_hidden_items)
        self.ui.actionGraph_prune_selected.triggered.connect(self.prune_selected_items)
        self.ui.actionGraph_reinstate_pruned.triggered.connect(self.reinstate_pruned_items)
        self.ui.tableView_object_parameter_value.customContextMenuRequested.connect(
            self.show_object_parameter_value_context_menu
        )
        self.ui.tableView_object_parameter_definition.customContextMenuRequested.connect(
            self.show_object_parameter_definition_context_menu
        )
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.connect(
            self.show_relationship_parameter_value_context_menu
        )
        self.ui.tableView_relationship_parameter_definition.customContextMenuRequested.connect(
            self.show_relationship_parameter_definition_context_menu
        )
        # Dock Widgets menu action
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_about_to_show)
        self.zoom_widget_action.hovered.connect(self._handle_zoom_widget_action_hovered)
        self.zoom_widget.minus_pressed.connect(self._handle_zoom_widget_minus_pressed)
        self.zoom_widget.plus_pressed.connect(self._handle_zoom_widget_plus_pressed)
        self.zoom_widget.reset_pressed.connect(self._handle_zoom_widget_reset_pressed)
        # Connect Add more items in Item palette
        self.ui.listView_object_class.clicked.connect(self._add_more_object_classes)
        self.ui.listView_relationship_class.clicked.connect(self._add_more_relationship_classes)

    def setup_zoom_action(self):
        """Setups zoom action in view menu."""
        self.zoom_widget = ZoomWidget(self)
        self.zoom_widget_action = QWidgetAction(self)
        self.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.zoom_widget_action)

    @Slot(name="restore_dock_widgets")
    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window at 'factory' positions."""
        # Place docks
        self.ui.dockWidget_object_parameter_value.setVisible(True)
        self.ui.dockWidget_object_parameter_value.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ui.dockWidget_object_parameter_value)
        self.ui.dockWidget_object_parameter_definition.setVisible(True)
        self.ui.dockWidget_object_parameter_definition.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ui.dockWidget_object_parameter_definition)
        self.ui.dockWidget_relationship_parameter_value.setVisible(True)
        self.ui.dockWidget_relationship_parameter_value.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ui.dockWidget_relationship_parameter_value)
        self.ui.dockWidget_relationship_parameter_definition.setVisible(True)
        self.ui.dockWidget_relationship_parameter_definition.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ui.dockWidget_relationship_parameter_definition)
        self.ui.dockWidget_object_tree.setVisible(True)
        self.ui.dockWidget_object_tree.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.ui.dockWidget_object_tree)
        self.ui.dockWidget_item_palette.setVisible(True)
        self.ui.dockWidget_item_palette.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ui.dockWidget_item_palette)
        self.ui.dockWidget_parameter_value_list.setVisible(True)
        self.ui.dockWidget_parameter_value_list.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ui.dockWidget_parameter_value_list)
        # Tabify
        self.tabifyDockWidget(self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_object_parameter_definition)
        self.tabifyDockWidget(
            self.ui.dockWidget_relationship_parameter_value, self.ui.dockWidget_relationship_parameter_definition
        )
        self.ui.dockWidget_object_parameter_value.raise_()
        self.ui.dockWidget_relationship_parameter_value.raise_()

    def _make_usage_item(self):
        """Makes item with usage instructions.

        Returns:
            InteractiveTextItem
        """
        usage = """
            <html>
            <head>
            <style type="text/css">
            ol {
                margin-left: 80px;
                padding-left: 0px;
            }
            ul {
                margin-left: 40px;
                padding-left: 0px;
            }
            </style>
            </head>
            <h3>Usage:</h3>
            <ol>
            <li>Select items in <a href="Object tree">Object tree</a> to show objects here.
                <ul>
                <li>Ctrl + click starts a new selection.</li>
                <li>Selected objects become vertices in the graph,
                while relationships between those objects become edges.
                </ul>
            </li>
            <li>Select items here to show their parameters in <a href="Parameters">Parameters</a>.
                <ul>
                <li>Hold down 'Ctrl' to add multiple items to the selection.</li>
                <li> Hold down 'Ctrl' and drag your mouse to perform a rubber band selection.</li>
                </ul>
            </li>
        """
        if not self.read_only:
            usage += """
                <li>Drag icons from <a href="Item palette">Item palette</a>
                and drop them here to create new items.</li>
            """
        usage += """
            </ol>
            </html>
        """
        font = QApplication.font()
        font.setPointSize(64)
        usage_item = InteractiveTextItem(usage, font)
        usage_item.linkActivated.connect(self._handle_usage_link_activated)
        return usage_item

    @Slot("QString", name="_handle_usage_link_activated")
    def _handle_usage_link_activated(self, link):
        """Runs when one of the links in the usage message is activated.
        Shows the corresponding widget."""
        if link == "Object tree":
            self.ui.dockWidget_object_tree.show()
        elif link == "Parameters":
            self.ui.dockWidget_object_parameter_value.show()
            self.ui.dockWidget_object_parameter_definition.show()
            self.ui.dockWidget_relationship_parameter_value.show()
            self.ui.dockWidget_relationship_parameter_definition.show()
        elif link == "Item palette":
            self.ui.dockWidget_item_palette.show()

    def show(self):
        """Shows usage message together with the form."""
        super().show()
        self.show_usage_msg()

    def show_usage_msg(self):
        """Shows usage instructions in new scene."""
        scene = self.new_scene()
        self._usage_item = self._make_usage_item()
        scene.addItem(self._usage_item)
        self.extend_scene()

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()

    def init_parameter_value_models(self):
        """Initializes parameter value models from source database."""
        # FIXME:
        self.object_parameter_value_model.has_empty_row = not self.read_only
        self.relationship_parameter_value_model.has_empty_row = not self.read_only
        super().init_parameter_value_models()

    def init_parameter_definition_models(self):
        """Initializes parameter (definition) models from source database."""
        # FIXME:
        self.object_parameter_definition_model.has_empty_row = not self.read_only
        self.relationship_parameter_definition_model.has_empty_row = not self.read_only
        super().init_parameter_definition_models()

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

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_added(db_map_data)
        self._added_objects = {(x["class_id"], x["name"]): x["id"] for x in db_map_data.get(self.db_map, [])}

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

    def receive_objects_removed(self, db_map_data):
        """Runs when objects are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_removed(db_map_data)
        self.receive_entities_removed(db_map_data)

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Builds a lookup dictionary consumed by ``add_relationship``.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_added(db_map_data)
        self._added_relationships = {
            (x["class_id"], x["object_id_list"]): x["id"] for x in db_map_data.get(self.db_map, [])
        }

    def receive_relationships_removed(self, db_map_data):
        """Runs when relationships are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_removed(db_map_data)
        self.receive_entities_removed(db_map_data)

    def receive_entities_removed(self, db_map_data):
        removed_ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        entity_ids = {x.entity_id for x in self.ui.graphicsView.items() if isinstance(x, EntityItem)}
        if entity_ids.intersection(removed_ids):
            self.build_graph()

    def refresh_icons(self, db_map_data):
        """Runs when entity classes are updated in the db. Refreshes icons of entities in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {x["id"] for x in db_map_data.get(self.db_map, [])}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and item.entity_class_id in updated_ids:
                item.refresh_icon()

    @Slot("QModelIndex", name="_add_more_object_classes")
    def _add_more_object_classes(self, index):
        """Runs when the user clicks on the Item palette Object class view.
        Opens the form  to add more object classes if the index is the one that sayes 'New...'.

        Args:
            index (QModelIndex): The clicked index.
        """
        if index == index.model().new_index:
            self.show_add_object_classes_form()

    @Slot("QModelIndex", name="_add_more_relationship_classes")
    def _add_more_relationship_classes(self, index):
        """Runs when the user clicks on the Item palette Relationship class view.
        Opens the form to add more relationship classes if the index is the one that sayes 'New...'.

        Args:
            index (QModelIndex): The clicked index.
        """
        if index == index.model().new_index:
            self.show_add_relationship_classes_form()

    @Slot(name="_handle_zoom_widget_minus_pressed")
    def _handle_zoom_widget_minus_pressed(self):
        """Performs a zoom out on the view."""
        self.ui.graphicsView.zoom_out()

    @Slot(name="_handle_zoom_widget_plus_pressed")
    def _handle_zoom_widget_plus_pressed(self):
        """Performs a zoom in on the view."""
        self.ui.graphicsView.zoom_in()

    @Slot(name="_handle_zoom_widget_reset_pressed")
    def _handle_zoom_widget_reset_pressed(self):
        """Resets the zoom on the view."""
        self.ui.graphicsView.reset_zoom()

    @Slot(name="_handle_zoom_widget_action_hovered")
    def _handle_zoom_widget_action_hovered(self):
        """Runs when the zoom widget action is hovered. Hides the 'Dock widgets' submenu in case
        it's being shown. This is the default behavior for hovering 'normal' 'QAction's, but for some reason
        it's not the case for hovering 'QWidgetAction's."""
        self.ui.menuDock_Widgets.hide()

    @Slot(name="_handle_menu_about_to_show")
    def _handle_menu_about_to_show(self):
        """Runs when a menu from the main menubar is about to show.
        Enables or disables the menu actions according to current status of the form.
        """
        self.ui.actionGraph_hide_selected.setEnabled(bool(self.entity_item_selection))
        self.ui.actionGraph_show_hidden.setEnabled(bool(self.hidden_items))
        self.ui.actionGraph_prune_selected.setEnabled(bool(self.entity_item_selection))
        self.ui.actionGraph_reinstate_pruned.setEnabled(bool(self.rejected_items))

    @Slot("Qt.DockWidgetArea", name="_handle_item_palette_dock_location_changed")
    def _handle_item_palette_dock_location_changed(self, area):
        """Runs when the item palette dock widget location changes.
        Adjusts splitter orientation accordingly."""
        if area & (Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea):
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Vertical)
        else:
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Horizontal)

    def add_toggle_view_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_toggle_view_actions()
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_tree.toggleViewAction())
        if not self.read_only:
            self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_palette.toggleViewAction())
        else:
            self.ui.dockWidget_item_palette.hide()

    def init_commit_rollback_actions(self):
        """Initializes commit and rollback actions."""
        if self.read_only:
            self.ui.menuSession.removeAction(self.ui.actionCommit)
            self.ui.menuSession.removeAction(self.ui.actionRollback)

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Builds graph."""
        super()._handle_object_tree_selection_changed(selected, deselected)
        self.build_graph()

    @busy_effect
    def build_graph(self, timeit=False):
        """Initializes graph data and builds the graph."""
        tic = time.clock()
        object_ids, relationship_ids, src_inds, dst_inds = self.get_graph_data()
        if self.make_graph(object_ids, relationship_ids, src_inds, dst_inds):
            self.extend_scene()
            toc = time.clock()
            timeit and self.msg.emit("Graph built in {} seconds\t".format(toc - tic))
        else:
            self.show_usage_msg()
        self.hidden_items = list()

    def _selected_object_ids(self):
        """Returns a set of selected object ids.

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

    def get_graph_data(self):
        """Returns data for making graph according to selection in Object tree.

        Returns:
            list: integer object ids
            list: integer relationship ids
            list: source indices
            list: destination indices
        """
        rejected_entity_ids = {x.entity_id for x in self.rejected_items}
        object_ids = list(self._selected_object_ids() - rejected_entity_ids)
        src_inds = list()
        dst_inds = list()
        relationship_ids = list()
        relationship_ind = len(object_ids)
        for relationship in self.db_mngr.get_relationships(self.db_map):
            if relationship["id"] in rejected_entity_ids:
                continue
            object_id_list = relationship["object_id_list"]
            object_id_list = [int(x) for x in object_id_list.split(",")]
            object_inds = list()
            for object_id in object_id_list:
                try:
                    object_ind = object_ids.index(object_id)
                    object_inds.append(object_ind)
                except ValueError:
                    pass
            if len(object_inds) < 2:
                continue
            relationship_ids.append(relationship["id"])
            for object_ind in object_inds:
                src_inds.append(relationship_ind)
                dst_inds.append(object_ind)
            relationship_ind += 1
        return object_ids, relationship_ids, src_inds, dst_inds

    def make_graph(self, object_ids, relationship_ids, src_inds, dst_inds):
        """Makes graph.

        Returns:
            bool: True if a graph was made, False otherwise
        """
        wip_relationship_items = self._get_wip_relationship_items()
        scene = self.new_scene()
        object_items_lookup = self._add_new_items(scene, object_ids, relationship_ids, src_inds, dst_inds)
        if not wip_relationship_items and not object_items_lookup:
            return False
        self._add_wip_relationship_items(scene, wip_relationship_items, object_items_lookup)
        return True

    def _get_wip_relationship_items(self):
        """Removes and returns wip relationship items from the current scene.

        Returns:
            list
        """
        scene = self.ui.graphicsView.scene()
        if not scene:
            return []
        wip_items = []
        for item in scene.items():
            if isinstance(item, RelationshipItem) and item.is_wip:
                for arc_item in item.arc_items:
                    scene.removeItem(arc_item)
                    scene.removeItem(arc_item.obj_item)
                scene.removeItem(item)
                wip_items.append(item)
        return wip_items

    def _add_new_items(self, scene, object_ids, relationship_ids, src_inds, dst_inds):
        """Adds new items to the given scene.

        Args:
            scene (QGraphicsScene)

        Returns:
            dict: Added ObjectItem instances keyed by integer object id.
        """
        d = self.shortest_path_matrix(
            len(object_ids) + len(relationship_ids), src_inds, dst_inds, self._arc_length_hint
        )
        if d is None:
            return {}
        x, y = self.vertex_coordinates(d)
        entity_items = list()
        object_items_lookup = dict()
        for i, object_id in enumerate(object_ids):
            object_item = ObjectItem(self, x[i], y[i], self._node_extent, entity_id=object_id)
            scene.addItem(object_item)
            entity_items.append(object_item)
            object_items_lookup[object_id] = object_item
        offset = len(entity_items)
        for i, relationship_id in enumerate(relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], self._node_extent, entity_id=relationship_id
            )
            scene.addItem(relationship_item)
            entity_items.append(relationship_item)
        for rel_ind, obj_ind in zip(src_inds, dst_inds):
            arc_item = ArcItem(entity_items[rel_ind], entity_items[obj_ind], self._arc_width)
            scene.addItem(arc_item)
        return object_items_lookup

    @staticmethod
    def _add_wip_relationship_items(scene, wip_relationship_items, object_items_lookup):
        """Adds wip relationship items to the given scene, merging completed members with existing
        object items by entity id.

        Args:
            scene (QGraphicsScene)
            wip_relationship_items (list)
            object_items_lookup (dict): Dictionary of ObjectItem instances keyed by integer object id
        """
        for rel_item in wip_relationship_items:
            scene.addItem(rel_item)
            for arc_item in rel_item.arc_items:
                scene.addItem(arc_item)
                obj_item = arc_item.obj_item
                scene.addItem(obj_item)
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
        sets = GraphViewForm.sets(N)  # construct sets of bus pairs
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

    @Slot(name="_handle_scene_selection_changed")
    def _handle_scene_selection_changed(self):
        """Filters parameters by selected objects in the graph."""
        scene = self.ui.graphicsView.scene()
        selected_items = scene.selectedItems()
        self.entity_item_selection = [x for x in selected_items if isinstance(x, EntityItem)]
        self.arc_item_selection = [x for x in selected_items if isinstance(x, ArcItem)]
        self.selected_ent_cls_ids["object class"] = selected_obj_cls_ids = {}
        self.selected_ent_cls_ids["relationship class"] = selected_rel_cls_ids = {}
        self.selected_ent_ids["object"] = selected_obj_ids = {}
        self.selected_ent_ids["relationship"] = selected_rel_ids = {}
        for item in selected_items:
            if isinstance(item, ObjectItem):
                selected_obj_cls_ids.setdefault(self.db_map, set()).add(item.entity_class_id)
                selected_obj_ids.setdefault((self.db_map, item.entity_class_id), set()).add(item.entity_id)
            elif isinstance(item, RelationshipItem):
                selected_rel_cls_ids.setdefault(self.db_map, set()).add(item.entity_class_id)
                selected_rel_ids.setdefault((self.db_map, item.entity_class_id), set()).add(item.entity_id)
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

    @Slot("QPoint", "QString", name="_handle_item_dropped")
    def _handle_item_dropped(self, pos, text):
        """Runs when an item is dropped from Item palette onto the view.
        Creates the object or relationship template.

        Args:
            pos (QPoint)
            text (str)
        """
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        if self._usage_item in scene.items():
            scene.removeItem(self._usage_item)
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
        object_id = self._added_objects.get((object_class_id, name))
        self._added_objects.clear()
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
        relationship_id = self._added_relationships.get((class_id, object_id_list))
        self._added_relationships.clear()
        return relationship_id

    @Slot("QPoint")
    def show_graph_view_context_menu(self, global_pos):
        """Shows context menu for graphics view.

        Args:
            global_pos (QPoint)
        """
        menu = GraphViewContextMenu(self, global_pos)
        option = menu.get_action()
        if option == "Hide selected items":
            self.hide_selected_items()
        elif option == "Show hidden items":
            self.show_hidden_items()
        elif option == "Prune selected items":
            self.prune_selected_items()
        elif option == "Reinstate pruned items":
            self.reinstate_pruned_items()
        else:
            pass
        menu.deleteLater()

    @Slot("bool", name="reinstate_pruned_items")
    def hide_selected_items(self, checked=False):
        """Hides selected items."""
        self.hidden_items.extend(self.entity_item_selection)
        for item in self.entity_item_selection:
            item.set_all_visible(False)

    @Slot("bool", name="reinstate_pruned_items")
    def show_hidden_items(self, checked=False):
        """Shows hidden items."""
        if not self.ui.graphicsView.scene():
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
        self.hidden_items.clear()

    @Slot("bool", name="reinstate_pruned_items")
    def prune_selected_items(self, checked=False):
        """Prunes selected items."""
        self.rejected_items.extend(self.entity_item_selection)
        self.build_graph()

    @Slot("bool", name="reinstate_pruned_items")
    def reinstate_pruned_items(self, checked=False):
        """Reinstates pruned items."""
        self.rejected_items.clear()
        self.build_graph()

    def show_object_item_context_menu(self, global_pos, main_item):
        """Shows context menu for entity item.

        Args:
            global_pos (QPoint)
            main_item (ObjectItem)
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

    @Slot("bool", name="remove_graph_items")
    def remove_graph_items(self, checked=False):
        """Removes all selected items in the graph."""
        if not self.entity_item_selection:
            return
        db_map_typed_data = {self.db_map: {}}
        for item in self.entity_item_selection:
            if item.is_wip:
                item.wipe_out()
            if item.entity_id:
                db_item = item.db_representation
                db_map_typed_data[self.db_map].setdefault(item.entity_type, []).append(db_item)
        self.db_mngr.remove_items(db_map_typed_data)

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        """Shows context menu for object parameter value table.

        Args:
            pos (QPoint)
        """
        self._show_table_context_menu(pos, self.ui.tableView_object_parameter_value, 'value')

    @Slot("QPoint", name="show_object_parameter_definition_context_menu")
    def show_object_parameter_definition_context_menu(self, pos):
        """Shows context menu for object parameter definition table.

        Args:
            pos (QPoint)
        """
        self._show_table_context_menu(pos, self.ui.tableView_object_parameter_definition, 'default_value')

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Shows context menu for relationship parameter value table.

        Args:
            pos (QPoint)
        """
        self._show_table_context_menu(pos, self.ui.tableView_relationship_parameter_value, 'value')

    @Slot("QPoint", name="show_relationship_parameter_definition_context_menu")
    def show_relationship_parameter_definition_context_menu(self, pos):
        """Shows context menu for relationship parameter definition table.

        Args:
            pos (QPoint)
        """
        self._show_table_context_menu(pos, self.ui.tableView_relationship_parameter_definition, 'default_value')

    def _show_table_context_menu(self, position, table_view, column_name):
        index = table_view.indexAt(position)
        global_pos = table_view.viewport().mapToGlobal(position)
        model = table_view.model()
        flags = model.flags(index)
        editable = (flags & Qt.ItemIsEditable) == Qt.ItemIsEditable
        is_value = model.headerData(index.column(), Qt.Horizontal) == column_name
        if editable and is_value:
            menu = SimpleEditableParameterValueContextMenu(self, global_pos, index)
        else:
            return
        option = menu.get_action()
        if option == "Open in editor...":
            self.show_parameter_value_editor(index, table_view)
        elif option == "Plot":
            selection = table_view.selectedIndexes()
            try:
                hints = GraphAndTreeViewPlottingHints(table_view)
                plot_widget = plot_selection(model, selection, hints)
            except PlottingError as error:
                report_plotting_failure(error, self)
                return
            if (
                table_view is self.ui.tableView_object_parameter_value
                or table_view is self.ui.tableView_object_parameter_definition
            ):
                plot_window_title = "Object parameter plot    -- {} --".format(column_name)
            elif (
                table_view is self.ui.tableView_relationship_parameter_value
                or table_view is self.ui.tableView_relationship_parameter_definition
            ):
                plot_window_title = "Relationship parameter plot    -- {} --".format(column_name)
            else:
                plot_window_title = "Plot"
            plot_widget.setWindowTitle(plot_window_title)
            plot_widget.show()
        menu.deleteLater()

    def closeEvent(self, event=None):
        """Handles close window event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        self.tear_down_scene()
