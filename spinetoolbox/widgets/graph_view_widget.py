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
Contains the TreeViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import time  # just to measure loading time and sqlalchemy ORM performance
import logging
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtWidgets import QApplication, QGraphicsScene, QWidgetAction, QTreeView
from PySide2.QtCore import Qt, Slot, QPointF, QRectF, QEvent
from PySide2.QtGui import QPalette, QMouseEvent
from spinedb_api import SpineDBAPIError, SpineIntegrityError
from .data_store_widget import DataStoreForm
from .custom_menus import SimpleEditableParameterValueContextMenu, ObjectItemContextMenu, GraphViewContextMenu
from .custom_qwidgets import ZoomWidget
from .report_plotting_failure import report_plotting_failure
from .shrinking_scene import ShrinkingScene
from ..mvcmodels.object_relationship_models import ObjectTreeModel, ObjectClassListModel, RelationshipClassListModel
from ..graphics_items import ObjectItem, ArcItem, CustomTextItem
from ..helpers import busy_effect, fix_name_ambiguity
from ..plotting import plot_selection, PlottingError, GraphAndTreeViewPlottingHints


class GraphViewForm(DataStoreForm):
    """A widget to show the graph view.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        db_maps (dict): named DiffDatabaseMapping instances
        read_only (bool): Whether or not the form should be editable
    """

    def __init__(self, project, db_maps, read_only=False):
        """Initialize class."""
        from ..ui.graph_view_form import Ui_MainWindow

        tic = time.clock()
        super().__init__(project, Ui_MainWindow(), db_maps)
        self.db_map = self.db_maps[0]
        self.db_name = self.db_names[0]
        self.ui.graphicsView.set_graph_view_form(self)
        self.read_only = read_only
        self._has_graph = False
        self.extent = 64
        self._spread = 3 * self.extent
        self.object_label_color = self.palette().color(QPalette.Normal, QPalette.ToolTipBase)
        self.object_label_color.setAlphaF(0.8)
        self.arc_token_color = self.palette().color(QPalette.Normal, QPalette.Window)
        self.arc_token_color.setAlphaF(0.8)
        self.arc_color = self.palette().color(QPalette.Normal, QPalette.WindowText)
        self.arc_color.setAlphaF(0.8)
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self, flat=True)
        self.ui.treeView_object.setModel(self.object_tree_model)
        # Data for ObjectItems
        self.object_ids = list()
        self.object_names = list()
        self.object_class_ids = list()
        self.object_class_names = list()
        # Data for ArcItems
        self.arc_object_id_lists = list()
        self.arc_relationship_class_ids = list()
        self.arc_token_object_name_tuple_lists = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        # Data for template ObjectItems and ArcItems (these are persisted across graph builds)
        self.heavy_positions = {}
        self.is_template = {}
        self.template_id_dims = {}
        self.arc_template_ids = {}
        # Data of relationship templates
        self.template_id = 1
        self.relationship_class_dict = {}  # template_id => relationship_class_name, relationship_class_id
        # Item palette models
        self.object_class_list_model = ObjectClassListModel(self)
        self.relationship_class_list_model = RelationshipClassListModel(self)
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)
        # Context menus
        self.object_item_context_menu = None
        self.graph_view_context_menu = None
        # Hidden and rejected items
        self.hidden_items = list()
        self.rejected_items = list()
        # Current item selection
        self.object_item_selection = list()
        self.arc_item_selection = list()
        # Zoom widget and action
        self.zoom_widget_action = None
        self.zoom_widget = None
        # Set up splitters
        area = self.dockWidgetArea(self.ui.dockWidget_item_palette)
        self._handle_item_palette_dock_location_changed(area)
        # Override mouse press event of object tree view
        self.ui.treeView_object.mousePressEvent = self._object_tree_view_mouse_press_event
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

    def show(self):
        """Show usage message together with the form."""
        super().show()
        self.show_usage_msg()

    def init_models(self):
        """Initialize models."""
        super().init_models()
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.has_empty_row = not self.read_only
        self.relationship_parameter_value_model.has_empty_row = not self.read_only
        super().init_parameter_value_models()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.has_empty_row = not self.read_only
        self.relationship_parameter_definition_model.has_empty_row = not self.read_only
        super().init_parameter_definition_models()

    def setup_zoom_action(self):
        """Setup zoom action in view menu."""
        self.zoom_widget = ZoomWidget(self)
        self.zoom_widget_action = QWidgetAction(self)
        self.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.zoom_widget_action)

    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
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

    @Slot("QModelIndex", name="_add_more_object_classes")
    def _add_more_object_classes(self, ind):
        """Opens the add more object classes form when clicking on Add more... item
        in Item palette Object class view."""
        clicked_item = self.object_class_list_model.itemFromIndex(ind)
        if clicked_item.data(Qt.UserRole + 2) == "Add More":
            self.show_add_object_classes_form()

    @Slot("QModelIndex", name="_add_more_relationship_classes")
    def _add_more_relationship_classes(self, ind):
        """Opens the add more relationship classes form when clicking on Add more... item
        in Item palette Relationship class view."""
        clicked_item = self.relationship_class_list_model.itemFromIndex(ind)
        if clicked_item.data(Qt.UserRole + 2) == "Add More":
            self.show_add_relationship_classes_form()

    def _object_tree_view_mouse_press_event(self, event):
        """Overrides mousePressEvent of ui.treeView_object so that Ctrl has the opposite effect.
        That is, if Ctrl is not pressed, then the selection is extended.
        If Ctrl *is* pressed, then the selection is reset.
        """
        local_pos = event.localPos()
        window_pos = event.windowPos()
        screen_pos = event.screenPos()
        button = event.button()
        buttons = event.buttons()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            modifiers &= ~Qt.ControlModifier
        else:
            modifiers |= Qt.ControlModifier
        source = event.source()
        new_event = QMouseEvent(
            QEvent.MouseButtonPress, local_pos, window_pos, screen_pos, button, buttons, modifiers, source
        )
        QTreeView.mousePressEvent(self.ui.treeView_object, new_event)

    @Slot(name="restore_dock_widgets")
    def restore_dock_widgets(self):
        """Dock all floating and or hidden QDockWidgets back to the window at 'factory' positions."""
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

    @Slot(name="_handle_zoom_widget_minus_pressed")
    def _handle_zoom_widget_minus_pressed(self):
        self.ui.graphicsView.zoom_out()

    @Slot(name="_handle_zoom_widget_plus_pressed")
    def _handle_zoom_widget_plus_pressed(self):
        self.ui.graphicsView.zoom_in()

    @Slot(name="_handle_zoom_widget_reset_pressed")
    def _handle_zoom_widget_reset_pressed(self):
        self.ui.graphicsView.reset_zoom()

    @Slot(name="_handle_zoom_widget_action_hovered")
    def _handle_zoom_widget_action_hovered(self):
        """Called when the zoom widget action is hovered. Hide the 'Dock widgets' submenu in case
        it's being shown. This is the default behavior for hovering 'normal' 'QAction's, but for some reason
        it's not the case for hovering 'QWidgetAction's."""
        self.ui.menuDock_Widgets.hide()

    @Slot(name="_handle_menu_about_to_show")
    def _handle_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show."""
        self.ui.actionGraph_hide_selected.setEnabled(bool(self.object_item_selection))
        self.ui.actionGraph_show_hidden.setEnabled(bool(self.hidden_items))
        self.ui.actionGraph_prune_selected.setEnabled(bool(self.object_item_selection))
        self.ui.actionGraph_reinstate_pruned.setEnabled(bool(self.rejected_items))

    @Slot("Qt.DockWidgetArea", name="_handle_item_palette_dock_location_changed")
    def _handle_item_palette_dock_location_changed(self, area):
        """Called when the item palette dock widget location changes.
        Adjust splitter orientation accordingly."""
        if area & (Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea):
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Vertical)
        else:
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Horizontal)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        super().add_toggle_view_actions()
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_tree.toggleViewAction())
        if not self.read_only:
            self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_palette.toggleViewAction())
        else:
            self.ui.dockWidget_item_palette.hide()

    def init_commit_rollback_actions(self):
        if not self.read_only:
            self.commit_available.emit(False)
        else:
            self.ui.menuSession.removeAction(self.ui.actionCommit)
            self.ui.menuSession.removeAction(self.ui.actionRollback)

    @busy_effect
    # @Slot("bool", name="build_graph")
    def build_graph(self):
        """Initialize graph data and build graph."""
        tic = time.clock()
        self.init_graph_data()
        self._has_graph = self.make_graph()
        if self._has_graph:
            self.extend_scene()
            toc = time.clock()
            self.msg.emit("Graph built in {} seconds\t".format(toc - tic))
        else:
            self.show_usage_msg()
        self.hidden_items = list()

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Build_graph."""
        self.build_graph()

    def init_graph_data(self):
        """Initialize graph data."""
        rejected_object_names = [x.object_name for x in self.rejected_items]
        self.object_ids = list()
        self.object_names = list()
        self.object_class_ids = list()
        self.object_class_names = list()
        root_item = self.object_tree_model.root_item
        index = self.object_tree_model.indexFromItem(root_item)
        is_root_selected = self.ui.treeView_object.selectionModel().isSelected(index)
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i, 0)
            object_class_id = object_class_item.data(Qt.UserRole + 1)[self.db_map]['id']
            object_class_name = object_class_item.data(Qt.UserRole + 1)[self.db_map]['name']
            index = self.object_tree_model.indexFromItem(object_class_item)
            is_object_class_selected = self.ui.treeView_object.selectionModel().isSelected(index)
            # Fetch object class if needed
            if is_root_selected or is_object_class_selected and self.object_tree_model.canFetchMore(index):
                self.object_tree_model.fetchMore(index)
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                object_id = object_item.data(Qt.UserRole + 1)[self.db_map]["id"]
                object_name = object_item.data(Qt.UserRole + 1)[self.db_map]["name"]
                if object_name in rejected_object_names:
                    continue
                index = self.object_tree_model.indexFromItem(object_item)
                is_object_selected = self.ui.treeView_object.selectionModel().isSelected(index)
                if is_root_selected or is_object_class_selected or is_object_selected:
                    self.object_ids.append(object_id)
                    self.object_names.append(object_name)
                    self.object_class_ids.append(object_class_id)
                    self.object_class_names.append(object_class_name)
        self.arc_object_id_lists = list()
        self.arc_relationship_class_ids = list()
        self.arc_token_object_name_tuple_lists = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        relationship_class_dict = {
            x.id: {"name": x.name, "object_class_name_list": x.object_class_name_list}
            for x in self.db_map.wide_relationship_class_list()
        }
        for relationship in self.db_map.wide_relationship_list():
            object_class_name_list = relationship_class_dict[relationship.class_id]["object_class_name_list"]
            split_object_class_name_list = object_class_name_list.split(",")
            object_id_list = relationship.object_id_list
            split_object_id_list = [int(x) for x in object_id_list.split(",")]
            split_object_name_list = relationship.object_name_list.split(",")
            for i, src_object_id in enumerate(split_object_id_list):
                try:
                    dst_object_id = split_object_id_list[i + 1]
                except IndexError:
                    dst_object_id = split_object_id_list[0]
                try:
                    src_ind = self.object_ids.index(src_object_id)
                    dst_ind = self.object_ids.index(dst_object_id)
                except ValueError:
                    continue
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                src_object_name = self.object_names[src_ind]
                dst_object_name = self.object_names[dst_ind]
                self.arc_object_id_lists.append(object_id_list)
                self.arc_relationship_class_ids.append(relationship.class_id)
                # Add label items
                arc_token_object_name_tuple_list = list()
                for object_name, object_class_name in zip(split_object_name_list, split_object_class_name_list):
                    if object_name in (src_object_name, dst_object_name):
                        continue
                    arc_token_object_name_tuple_list.append((object_class_name, object_name))
                self.arc_token_object_name_tuple_lists.append(arc_token_object_name_tuple_list)
        # Add template items hanging around
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        self.heavy_positions = {}
        template_object_items = [x for x in scene.items() if isinstance(x, ObjectItem) and x.template_id_dim]
        object_ind = len(self.object_ids)
        self.template_id_dims = {}
        self.is_template = {}
        object_ind_dict = {}  # Dict of object indexes added from this point
        object_ids_copy = self.object_ids.copy()  # Object ids added until this point
        for item in template_object_items:
            object_id = item.object_id
            object_name = item.object_name
            try:
                found_ind = object_ids_copy.index(object_id)
                # Object id is already in list; complete its template information and make it heavy
                self.template_id_dims[found_ind] = item.template_id_dim
                self.is_template[found_ind] = False
                self.heavy_positions[found_ind] = item.pos()
            except ValueError:
                # Object id is not in list; add it together with its template info, and make it heavy
                object_class_id = item.object_class_id
                object_class_name = item.object_class_name
                self.object_ids.append(object_id)
                self.object_names.append(object_name)
                self.object_class_ids.append(object_class_id)
                self.object_class_names.append(object_class_name)
                self.template_id_dims[object_ind] = item.template_id_dim
                self.is_template[object_ind] = item.is_template
                self.heavy_positions[object_ind] = item.pos()
                object_ind_dict[item] = object_ind
                object_ind += 1
        template_arc_items = [x for x in scene.items() if isinstance(x, ArcItem) and x.is_template]
        arc_ind = len(self.arc_token_object_name_tuple_lists)
        self.arc_template_ids = {}
        for item in template_arc_items:
            src_item = item.src_item
            dst_item = item.dst_item
            try:
                src_ind = object_ind_dict[src_item]
            except KeyError:
                src_object_id = src_item.object_id
                src_ind = self.object_ids.index(src_object_id)
            try:
                dst_ind = object_ind_dict[dst_item]
            except KeyError:
                dst_object_id = dst_item.object_id
                dst_ind = self.object_ids.index(dst_object_id)
            self.src_ind_list.append(src_ind)
            self.dst_ind_list.append(dst_ind)
            # NOTE: These arcs correspond to template arcs.
            relationship_class_id = item.relationship_class_id
            self.arc_object_id_lists.append("")  # TODO: is this one filled when creating the relationship?
            self.arc_relationship_class_ids.append(relationship_class_id)
            # Label don't matter
            self.arc_token_object_name_tuple_lists.append(("", ""))
            self.arc_template_ids[arc_ind] = item.template_id
            arc_ind += 1

    @staticmethod
    def shortest_path_matrix(object_name_list, src_ind_list, dst_ind_list, spread):
        """Return the shortest-path matrix."""
        N = len(object_name_list)
        if not N:
            return None
        dist = np.zeros((N, N))
        src_ind = arr(src_ind_list)
        dst_ind = arr(dst_ind_list)
        try:
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = spread
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        d[d == np.inf] = spread * 3
        d[d == 0] = spread * 1e-6
        return d

    @staticmethod
    def sets(N):
        """Return sets of vertex pairs indices."""
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
        """Return x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
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

    def make_graph(self):
        """Make graph."""
        d = self.shortest_path_matrix(self.object_names, self.src_ind_list, self.dst_ind_list, self._spread)
        if d is None:
            return False
        scene = self.new_scene()
        x, y = self.vertex_coordinates(d, self.heavy_positions)
        object_items = list()
        for i in range(len(self.object_names)):
            object_id = self.object_ids[i]
            object_name = self.object_names[i]
            object_class_id = self.object_class_ids[i]
            object_class_name = self.object_class_names[i]
            object_item = ObjectItem(
                self,
                object_name,
                object_class_id,
                object_class_name,
                x[i],
                y[i],
                self.extent,
                object_id=object_id,
                label_color=self.object_label_color,
            )
            try:
                template_id_dim = self.template_id_dims[i]
                object_item.template_id_dim = template_id_dim
                if self.is_template[i]:
                    object_item.make_template()
            except KeyError:
                pass
            scene.addItem(object_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            object_id_list = self.arc_object_id_lists[k]
            relationship_class_id = self.arc_relationship_class_ids[k]
            token_object_name_tuple_list = self.arc_token_object_name_tuple_lists[k]
            arc_item = ArcItem(
                self,
                relationship_class_id,
                object_items[i],
                object_items[j],
                0.25 * self.extent,
                self.arc_color,
                object_id_list=object_id_list,
                token_color=self.arc_token_color,
                token_object_extent=0.75 * self.extent,
                token_object_label_color=self.object_label_color,
                token_object_name_tuple_list=token_object_name_tuple_list,
            )
            try:
                template_id = self.arc_template_ids[k]
                arc_item.template_id = template_id
                arc_item.make_template()
            except KeyError:
                pass
            scene.addItem(arc_item)
        return True

    def new_scene(self):
        """Replaces the current scene with a new one."""
        old_scene = self.ui.graphicsView.scene()
        if old_scene:
            old_scene.deleteLater()
        scene = ShrinkingScene(100.0, 100.0, None)
        self.ui.graphicsView.setScene(scene)
        scene.changed.connect(self._handle_scene_changed)
        scene.selectionChanged.connect(self._handle_scene_selection_changed)
        return scene

    def extend_scene(self):
        """Make scene rect the size of the scene to show all items."""
        bounding_rect = self.ui.graphicsView.scene().itemsBoundingRect()
        self.ui.graphicsView.scene().setSceneRect(bounding_rect)
        self.ui.graphicsView.init_zoom()

    @Slot(name="_handle_scene_selection_changed")
    def _handle_scene_selection_changed(self):
        """Show parameters for selected items."""
        scene = self.ui.graphicsView.scene()  # TODO: should we use sender() here?
        selected_items = scene.selectedItems()
        self.object_item_selection = [x for x in selected_items if isinstance(x, ObjectItem)]
        self.arc_item_selection = [x for x in selected_items if isinstance(x, ArcItem)]
        self.selected_object_class_ids = set()
        self.selected_object_ids = dict()
        self.selected_relationship_class_ids = set()
        self.selected_object_id_lists = dict()
        for item in selected_items:
            if isinstance(item, ObjectItem):
                self.selected_object_class_ids.add(item.object_class_id)
                self.selected_object_ids.setdefault(item.object_class_id, set()).add(item.object_id)
            elif isinstance(item, ArcItem):
                self.selected_relationship_class_ids.add(item.relationship_class_id)
                self.selected_object_id_lists.setdefault(item.relationship_class_id, set()).add(item.object_id_list)
        self.do_update_filter()

    @Slot(list, name="_handle_scene_changed")
    def _handle_scene_changed(self, region):
        """Handle scene changed. Show usage message if no items other than the bg.
        """
        scene_rect = self.ui.graphicsView.scene().sceneRect()
        if all(scene_rect.contains(rect) for rect in region):
            return
        extended_rect = scene_rect
        for rect in region:
            extended_rect = extended_rect.united(rect)
        self.ui.graphicsView.scene().setSceneRect(extended_rect)

    def show_usage_msg(self):
        """Show usage instructions in new scene.
        """
        scene = self.new_scene()
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
        usage_item = CustomTextItem(usage, font)
        usage_item.linkActivated.connect(self._handle_usage_link_activated)
        scene.addItem(usage_item)
        self._has_graph = False
        self.extend_scene()

    @Slot("QString", name="_handle_usage_link_activated")
    def _handle_usage_link_activated(self, link):
        if link == "Object tree":
            self.ui.dockWidget_object_tree.show()
        elif link == "Parameters":
            self.ui.dockWidget_object_parameter_value.show()
            self.ui.dockWidget_object_parameter_definition.show()
            self.ui.dockWidget_relationship_parameter_value.show()
            self.ui.dockWidget_relationship_parameter_definition.show()
        elif link == "Item palette":
            self.ui.dockWidget_item_palette.show()

    @Slot("QPoint", "QString", name="_handle_item_dropped")
    def _handle_item_dropped(self, pos, text):
        if self._has_graph:
            scene = self.ui.graphicsView.scene()
        else:
            scene = self.new_scene()
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        data = eval(text)  # pylint: disable=eval-used
        if data["type"] == "object_class":
            class_id = data["id"]
            class_name = data["name"]
            name = class_name
            object_item = ObjectItem(
                self,
                name,
                class_id,
                class_name,
                scene_pos.x(),
                scene_pos.y(),
                self.extent,
                label_color=self.object_label_color,
            )
            scene.addItem(object_item)
            object_item.make_template()
        elif data["type"] == "relationship_class":
            relationship_class_id = data["id"]
            object_class_id_list = [int(x) for x in data["object_class_id_list"].split(',')]
            object_class_name_list = data["object_class_name_list"].split(',')
            object_name_list = object_class_name_list.copy()
            fix_name_ambiguity(object_name_list)
            relationship_items = self.relationship_items(
                object_name_list,
                object_class_name_list,
                self.extent,
                self._spread,
                label_color=self.object_label_color,
                object_class_id_list=object_class_id_list,
                relationship_class_id=relationship_class_id,
            )
            self.add_relationship_template(scene, scene_pos.x(), scene_pos.y(), *relationship_items)
            self.relationship_class_dict[self.template_id] = {"id": data["id"], "name": data["name"]}
            self.template_id += 1
        self._has_graph = True
        self.extend_scene()

    def relationship_items(
        self,
        object_name_list,
        object_class_name_list,
        extent,
        spread,
        label_color,
        object_class_id_list=None,
        relationship_class_id=None,
    ):
        """Lists of object and arc items that form a relationship."""
        if object_class_id_list is None:
            object_class_id_list = list()
        object_items = list()
        arc_items = list()
        src_ind_list = list(range(len(object_name_list)))
        dst_ind_list = src_ind_list[1:] + src_ind_list[:1]
        d = self.shortest_path_matrix(object_name_list, src_ind_list, dst_ind_list, spread)
        if d is None:
            return [], []
        x, y = self.vertex_coordinates(d)
        for i, object_name in enumerate(object_name_list):
            x_ = x[i]
            y_ = y[i]
            object_class_name = object_class_name_list[i]
            try:
                object_class_id = object_class_id_list[i]
            except IndexError:
                object_class_id = None
            object_item = ObjectItem(
                self, object_name, object_class_id, object_class_name, x_, y_, extent, label_color=label_color
            )
            object_items.append(object_item)
        for i, src_item in enumerate(object_items):
            try:
                dst_item = object_items[i + 1]
            except IndexError:
                dst_item = object_items[0]
            arc_item = ArcItem(self, relationship_class_id, src_item, dst_item, extent / 4, self.arc_color)
            arc_items.append(arc_item)
        return object_items, arc_items

    def add_relationship_template(self, scene, x, y, object_items, arc_items, dimension_at_origin=None):
        """Add relationship parts into the scene to form a 'relationship template'."""
        for item in object_items + arc_items:
            scene.addItem(item)
        # Make template
        for dimension, object_item in enumerate(object_items):
            object_item.template_id_dim[self.template_id] = dimension
            object_item.make_template()
        for arc_item in arc_items:
            arc_item.template_id = self.template_id
            arc_item.make_template()
        # Move
        try:
            rectf = object_items[dimension_at_origin].sceneBoundingRect()
        except (IndexError, TypeError):
            rectf = QRectF()
            for object_item in object_items:
                rectf |= object_item.sceneBoundingRect()
        center = rectf.center()
        for object_item in object_items:
            object_item.moveBy(x - center.x(), y - center.y())
            object_item.move_related_items_by(QPointF(x, y) - center)

    def add_object(self, object_item, name):
        """Try and add object given an object item and a name."""
        item = dict(class_id=object_item.object_class_id, name=name)
        object_d = {self.db_map: (item,)}
        if self.add_objects(object_d):
            object_item.object_name = name
            object_ = self.db_map.query(self.db_map.object_sq).filter_by(name=name).one()
            object_item.object_id = object_.id
            if object_item.template_id_dim:
                object_item.add_into_relationship()
            object_item.remove_template()

    def update_object(self, object_item, name):
        """Try and update object given an object item and a name."""
        item = dict(id=object_item.object_id, name=name)
        object_d = {self.db_map: (item,)}
        if self.update_objects(object_d):
            object_item.object_name = name

    @busy_effect
    def add_relationship(self, template_id, object_items):
        """Try and add relationship given a template id and a list of object items."""
        object_id_list = list()
        object_name_list = list()
        object_dimensions = [x.template_id_dim[template_id] for x in object_items]
        for dimension in sorted(object_dimensions):
            ind = object_dimensions.index(dimension)
            item = object_items[ind]
            object_name = item.object_name
            if not object_name:
                logging.debug("can't find name %s", object_name)
                return False
            object_ = self.db_map.query(self.db_map.object_sq).filter_by(name=object_name).one_or_none()
            if not object_:
                logging.debug("can't find object %s", object_name)
                return False
            object_id_list.append(object_.id)
            object_name_list.append(object_name)
        if len(object_id_list) < 2:
            logging.debug("too short %s", len(object_id_list))
            return False
        name = self.relationship_class_dict[template_id]["name"] + "_" + "__".join(object_name_list)
        class_id = self.relationship_class_dict[template_id]["id"]
        item = {'name': name, 'object_id_list': object_id_list, 'class_id': class_id}
        try:
            wide_relationships, _ = self.db_map.add_wide_relationships(item, strict=True)
            for item in object_items:
                del item.template_id_dim[template_id]
            items = self.ui.graphicsView.scene().items()
            arc_items = [x for x in items if isinstance(x, ArcItem) and x.template_id == template_id]
            for item in arc_items:
                item.remove_template()
                item.template_id = None
                item.object_id_list = ",".join([str(x) for x in object_id_list])
            self.commit_available.emit(True)
            msg = "Successfully added new relationship '{}'.".format(wide_relationships.one().name)
            self.msg.emit(msg)
            return True
        except (SpineIntegrityError, SpineDBAPIError) as e:
            self.msg_error.emit(e.msg)
            return False

    def add_object_classses_to_models(self, db_map, added):
        super().add_object_classses_to_models(db_map, added)
        for object_class in added:
            self.object_class_list_model.add_object_class(object_class)

    def add_relationship_classes_to_models(self, db_map, added):
        """Insert new relationship classes."""
        super().add_relationship_classes_to_models(db_map, added)
        for relationship_class in added:
            self.relationship_class_list_model.add_relationship_class(relationship_class)

    def show_graph_view_context_menu(self, global_pos):
        """Show context menu for graphics view."""
        self.graph_view_context_menu = GraphViewContextMenu(self, global_pos)
        option = self.graph_view_context_menu.get_action()
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
        self.graph_view_context_menu.deleteLater()
        self.graph_view_context_menu = None

    @Slot("bool", name="reinstate_pruned_items")
    def hide_selected_items(self, checked=False):
        """Hide selected items."""
        self.hidden_items.extend(self.object_item_selection)
        for item in self.object_item_selection:
            item.set_all_visible(False)

    @Slot("bool", name="reinstate_pruned_items")
    def show_hidden_items(self, checked=False):
        """Show hidden items."""
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
            self.hidden_items = list()

    @Slot("bool", name="reinstate_pruned_items")
    def prune_selected_items(self, checked=False):
        """Prune selected items."""
        self.rejected_items.extend(self.object_item_selection)
        self.build_graph()

    @Slot("bool", name="reinstate_pruned_items")
    def reinstate_pruned_items(self, checked=False):
        """Reinstate pruned items."""
        self.rejected_items = list()
        self.build_graph()

    def show_object_item_context_menu(self, e, main_item):
        """Show context menu for object_item."""
        global_pos = e.screenPos()
        self.object_item_context_menu = ObjectItemContextMenu(self, global_pos, main_item)
        option = self.object_item_context_menu.get_action()
        if option == 'Hide':
            self.hide_selected_items()
        elif option == 'Prune':
            self.prune_selected_items()
        elif option in ('Set name', 'Rename'):
            main_item.edit_name()
        elif option == 'Remove':
            self.remove_graph_items()
        elif option in self.object_item_context_menu.relationship_class_dict:
            relationship_class = self.object_item_context_menu.relationship_class_dict[option]
            relationship_class_id = relationship_class["id"]
            relationship_class_name = relationship_class["name"]
            object_class_id_list = relationship_class["object_class_id_list"]
            object_class_name_list = relationship_class['object_class_name_list']
            object_name_list = relationship_class['object_name_list']
            dimension = relationship_class['dimension']
            object_items, arc_items = self.relationship_items(
                object_name_list,
                object_class_name_list,
                self.extent,
                self._spread,
                label_color=self.object_label_color,
                object_class_id_list=object_class_id_list,
                relationship_class_id=relationship_class_id,
            )
            scene = self.ui.graphicsView.scene()
            scene_pos = e.scenePos()
            self.add_relationship_template(
                scene, scene_pos.x(), scene_pos.y(), object_items, arc_items, dimension_at_origin=dimension
            )
            object_items[dimension].merge_item(main_item)
            self._has_graph = True
            self.relationship_class_dict[self.template_id] = {
                "id": relationship_class_id,
                "name": relationship_class_name,
            }
            self.template_id += 1
        self.object_item_context_menu.deleteLater()
        self.object_item_context_menu = None

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        self._show_table_context_menu(pos, self.ui.tableView_object_parameter_value, 'value')

    @Slot("QPoint", name="show_object_parameter_definition_context_menu")
    def show_object_parameter_definition_context_menu(self, pos):
        self._show_table_context_menu(pos, self.ui.tableView_object_parameter_definition, 'default_value')

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        self._show_table_context_menu(pos, self.ui.tableView_relationship_parameter_value, 'value')

    @Slot("QPoint", name="show_relationship_parameter_definition_context_menu")
    def show_relationship_parameter_definition_context_menu(self, pos):
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

    @busy_effect
    @Slot("bool", name="remove_graph_items")
    def remove_graph_items(self, checked=False):
        """Remove all selected items in the graph."""
        if not self.object_item_selection:
            return
        removed_objects = list(
            dict(class_id=x.object_class_id, id=x.object_id) for x in self.object_item_selection if x.object_id
        )
        object_ids = set(x['id'] for x in removed_objects)
        try:
            self.db_map.remove_items(object_ids=object_ids)
            self.object_tree_model.remove_objects(self.db_map, object_ids)
            # Parameter models
            self.object_parameter_value_model.remove_objects(self.db_map, removed_objects)
            self.relationship_parameter_value_model.remove_objects(self.db_map, removed_objects)
            self.commit_available.emit(True)
            for item in self.object_item_selection:
                item.wipe_out()
            self.ui.graphicsView.scene().shrink_if_needed()
            self.msg.emit("Successfully removed items.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        scene = self.ui.graphicsView.scene()
        if scene:
            scene.deleteLater()
