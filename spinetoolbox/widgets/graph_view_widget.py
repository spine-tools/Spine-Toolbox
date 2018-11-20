######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget to show graph view form.

:author: M. Marin (KTH), J. Olauson (KTH)
:date:   5.11.2018
"""

import logging
from ui.graph_view_form import Ui_MainWindow
from PySide2.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QErrorMessage, QToolButton, \
    QAction, QGraphicsRectItem, QMessageBox, QCheckBox, QTableView
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon, QPalette
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QPointF, QRectF, QItemSelection, QItemSelectionModel, QSize
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog
from widgets.custom_menus import ObjectItemContextMenu, GraphViewContextMenu
from models import ObjectTreeModel, ObjectClassListModel, RelationshipClassListModel
from graphics_items import ObjectItem, ArcItem, CustomTextItem
from helpers import busy_effect
from config import STATUSBAR_SS


class GraphViewForm(QMainWindow):
    """A widget to show the graph view.

    Attributes:
        owner (View or Data Store): View or DataStore instance
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
        read_only (bool): Whether or not the form should be editable
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, owner, db_map, database, read_only=False):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._owner = owner
        self.db_map = db_map
        self.database = database
        self.read_only = read_only
        self._has_graph = False
        self._scene_bg = None
        self.object_item_placeholder = None
        self.err_msg = QErrorMessage(self)
        self.font = QFont("", 64)
        self.font_metric = QFontMetrics(self.font)
        self._spread = self.font_metric.width("Spine Toolbox")
        self.label_color = self.palette().color(QPalette.Normal, QPalette.Window)
        self.arc_color = self.palette().color(QPalette.Normal, QPalette.WindowText)
        self.label_color.setAlphaF(.5)
        self.arc_color.setAlphaF(.75)
        self.object_name_list = list()
        self.object_class_name_list = list()
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        self.heavy_positions = {}
        self.template_id = 1
        self.relationship_class_dict = {}  # template_id => relationship_class_name, relationship_class_id
        self.template_id_dims = {}
        self.is_template = {}
        self.arc_template_ids = {}
        self.object_tree_model = ObjectTreeModel(self)
        self.object_class_list_model = ObjectClassListModel(self)
        self.relationship_class_list_model = RelationshipClassListModel(self)
        self.object_item_context_menu = None
        self.graph_view_context_menu = None
        self.hidden_items = list()
        self.rejected_items = list()
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphicsView._graph_view_form = self
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.treeView.setModel(self.object_tree_model)
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)
        self.init_models()
        self.setup_views()
        self.connect_signals()
        self.restore_ui()
        self.add_toggle_view_actions()
        self.init_commit_rollback_actions()
        self.build_graph()
        title = database + " (read only) " if read_only else database
        self.setWindowTitle("Data store graph view    -- {} --".format(title))
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_models(self):
        """Initialize models and their respective views."""
        self.object_tree_model.build_flat_tree(self.database)
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()
        self.ui.treeView.resizeColumnToContents(0)
        self.ui.treeView.expand(self.object_tree_model.root_item.index())

    def setup_views(self):
        """Setup 'Add more' action and button."""
        # object class
        index = self.object_class_list_model.add_more_index
        action = QAction()
        icon = QIcon(":/icons/plus_object_icon.png")
        action.setIcon(icon)
        action.setText(index.data(Qt.DisplayRole))
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(64, 56)
        self.ui.listView_object_class.setIndexWidget(index, button)
        action.triggered.connect(self.show_add_object_classes_form)
        # relationship class
        index = self.relationship_class_list_model.add_more_index
        action = QAction()
        icon = QIcon(":/icons/plus_relationship_icon.png")
        action.setIcon(icon)
        action.setText(index.data(Qt.DisplayRole))
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(64, 56)
        self.ui.listView_relationship_class.setIndexWidget(index, button)
        action.triggered.connect(self.show_add_relationship_classes_form)

    def connect_signals(self):
        """Connect signals."""
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self.ui.treeView.selectionModel().selectionChanged.connect(self.receive_item_tree_selection_changed)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionBuild.triggered.connect(self.build_graph)
        self.ui.graphicsView.item_dropped.connect(self.handle_item_dropped)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(" ".join([current_msg, msg]), 5000)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show in QErrorMessage
        """
        self.err_msg.showMessage(msg)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_tree.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_parameters.toggleViewAction())
        if not self.read_only:
            self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_palette.toggleViewAction())
        else:
            self.ui.dockWidget_item_palette.hide()

    def set_commit_rollback_actions_enabled(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    def init_commit_rollback_actions(self):
        if not self.read_only:
            self.set_commit_rollback_actions_enabled(False)
        else:
            self.ui.menuSession.removeAction(self.ui.actionCommit)
            self.ui.menuSession.removeAction(self.ui.actionRollback)

    @Slot(name="show_commit_session_dialog")
    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes():
            self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            self.db_map.commit_session(commit_msg)
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        try:
            self.db_map.rollback_session()
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes since last commit rolled back successfully."
        self.msg.emit(msg)
        self.init_models()

    @Slot(name="refresh_session")
    def refresh_session(self):
        msg = "Session refreshed."
        self.msg.emit(msg)
        self.init_models()

    @busy_effect
    @Slot("bool", name="build_graph")
    def build_graph(self, checked=True):
        """Initialize graph data and build graph."""
        self.init_graph_data()
        self._has_graph = self.make_graph()
        if self._has_graph:
            self.ui.graphicsView.scale_to_fit_scene()
        self.hidden_items = list()

    @Slot("QItemSelection", "QItemSelection", name="receive_item_tree_selection_changed")
    def receive_item_tree_selection_changed(self, selected, deselected):
        """Call build graph."""
        self.build_graph()

    def receive_graph_view_selection_changed(self, selected, deselected):
        self.ui.horizontalLayout_parameters.addWidget(QTableView(self))


    def init_graph_data(self):
        """Initialize graph data by querying db_map."""
        rejected_object_names = [x._object_name for x in self.rejected_items]
        self.object_name_list = list()
        self.object_class_name_list = list()
        root_item = self.object_tree_model.root_item
        index = self.object_tree_model.indexFromItem(root_item)
        is_root_selected = self.ui.treeView.selectionModel().isSelected(index)
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i, 0)
            object_class_name = object_class_item.data(Qt.EditRole)
            index = self.object_tree_model.indexFromItem(object_class_item)
            is_object_class_selected = self.ui.treeView.selectionModel().isSelected(index)
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                object_name = object_item.data(Qt.EditRole)
                if object_name in rejected_object_names:
                    continue
                index = self.object_tree_model.indexFromItem(object_item)
                is_object_selected = self.ui.treeView.selectionModel().isSelected(index)
                if is_root_selected or is_object_class_selected or is_object_selected:
                    self.object_name_list.append(object_name)
                    self.object_class_name_list.append(object_class_name)
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.arc_object_class_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        relationship_class_dict = {
            x.id: {
                "name": x.name,
                "object_class_name_list": x.object_class_name_list.split(",")
            } for x in self.db_map.wide_relationship_class_list()
        }
        for relationship in self.db_map.wide_relationship_list():
            relationship_class_name = relationship_class_dict[relationship.class_id]["name"]
            object_class_name_list = relationship_class_dict[relationship.class_id]["object_class_name_list"]
            object_name_list = relationship.object_name_list.split(",")
            for i in range(len(object_name_list)):
                src_object_name = object_name_list[i]
                try:
                    dst_object_name = object_name_list[i + 1]
                except IndexError:
                    dst_object_name = object_name_list[0]
                try:
                    src_ind = self.object_name_list.index(src_object_name)
                    dst_ind = self.object_name_list.index(dst_object_name)
                except ValueError:
                    continue
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                self.arc_relationship_class_name_list.append(relationship_class_name)
                arc_object_names = list()
                arc_object_class_names = list()
                for x, y in zip(object_name_list, object_class_name_list):
                    if x in (src_object_name, dst_object_name):
                        continue
                    arc_object_names.append(x)
                    arc_object_class_names.append(y)
                self.arc_object_names_list.append(arc_object_names)
                self.arc_object_class_names_list.append(arc_object_class_names)
        # Add template items hanging around
        scene = self.ui.graphicsView.scene()
        if scene:
            self.heavy_positions = {}
            object_items = [x for x in scene.items() if isinstance(x, ObjectItem) and x.template_id_dim]
            object_ind = len(self.object_name_list)
            self.template_id_dims = {}
            self.is_template = {}
            object_ind_dict = {}
            for item in object_items:
                object_name = item._object_name
                try:
                    found_ind = self.object_name_list.index(object_name)
                    is_template = self.is_template.get(found_ind)
                    if not is_template:
                        self.template_id_dims[found_ind] = item.template_id_dim
                        self.is_template[found_ind] = False
                        self.heavy_positions[found_ind] = item.pos()
                        continue
                except ValueError:
                    pass
                object_class_name = item._object_class_name
                self.object_name_list.append(object_name)
                self.object_class_name_list.append(object_class_name)
                self.template_id_dims[object_ind] = item.template_id_dim
                self.is_template[object_ind] = item.is_template
                self.heavy_positions[object_ind] = item.pos()
                object_ind_dict[item] = object_ind
                object_ind += 1
            arc_items = [x for x in scene.items() if isinstance(x, ArcItem) and x.is_template]
            arc_ind = len(self.arc_object_names_list)
            self.arc_template_ids = {}
            for item in arc_items:
                src_item = item.src_item
                dst_item = item.dst_item
                try:
                    src_ind = object_ind_dict[src_item]
                except KeyError:
                    src_object_name = src_item._object_name
                    src_ind = self.object_name_list.index(src_object_name)
                try:
                    dst_ind = object_ind_dict[dst_item]
                except KeyError:
                    dst_object_name = dst_item._object_name
                    dst_ind = self.object_name_list.index(dst_object_name)
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                self.arc_relationship_class_name_list.append("")
                self.arc_object_names_list.append("")
                self.arc_object_class_names_list.append("")
                self.arc_template_ids[arc_ind] = item.template_id
                arc_ind += 1

    def shortest_path_matrix(self, object_name_list, src_ind_list, dst_ind_list, spread):
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

    def sets(self, N):
        """Return sets of vertex pairs indices."""
        sets = []
        for n in range(1, N):
            pairs = np.zeros((N - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(N - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(N - n), 2 * n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if len(s1) > 0:
                sets.append(s1)
            if len(s2) > 0:
                sets.append(s2)
        return sets

    def vertex_coordinates(self, matrix, heavy_positions={}, iterations=10, weight_exp=-2, initial_diameter=100):
        """Return x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
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
            # Shift random layout to the center of heavy position
            shift = np.mean(matrix[heavy_ind, :][:, heavy_ind], axis=0)
            layout[:, 0] += shift[0]
            layout[:, 1] += shift[1]
            # Apply heavy positions
            layout[heavy_ind, :] = heavy_pos
        weights = matrix ** weight_exp  # bus-pair weights (lower for distant buses)
        maxstep = 1 / np.min(weights[mask])
        minstep = 1 / np.max(weights[mask])
        lambda_ = np.log(minstep / maxstep) / (iterations - 1)  # exponential decay of allowed adjustment
        sets = self.sets(N)  # construct sets of bus pairs
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
                    # Apply heavy positions
                    layout[heavy_ind, :] = heavy_pos
        return layout[:, 0], layout[:, 1]

    def make_graph(self):
        """Make graph."""
        scene = self.new_scene()
        d = self.shortest_path_matrix(self.object_name_list, self.src_ind_list, self.dst_ind_list, self._spread)
        if d is None:
            return False
        x, y = self.vertex_coordinates(d, self.heavy_positions)
        object_items = list()
        for i in range(len(self.object_name_list)):
            object_name = self.object_name_list[i]
            object_class_name = self.object_class_name_list[i]
            extent = 2 * self.font.pointSize()
            object_item = ObjectItem(
                self, object_name, object_class_name, x[i], y[i], extent,
                label_font=self.font, label_color=self.label_color)
            try:
                template_id_dim = self.template_id_dims[i]
                if self.is_template[i]:
                    object_item.make_template()
                object_item.template_id_dim = template_id_dim
            except KeyError:
                pass
            scene.addItem(object_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            # relationship_class_name = self.arc_relationship_class_name_list[k]
            object_class_names = self.arc_object_class_names_list[k]
            object_names = self.arc_object_names_list[k]
            extent = 2 * self.font.pointSize()
            label_parts = self.relationship_parts(
                object_class_names, object_names, extent, self.font,
                object_label_position="beside_icon")
            arc_item = ArcItem(
                self, object_items[i], object_items[j], .25 * extent,
                self.arc_color, label_color=self.label_color, label_parts=label_parts)
            try:
                template_id = self.arc_template_ids[k]
                arc_item.make_template()
                arc_item.template_id = template_id
            except KeyError:
                pass
            scene.addItem(arc_item)
        return True

    def new_scene(self):
        """A new scene with a background."""
        self._scene_bg = QGraphicsRectItem()
        self._scene_bg.setPen(Qt.NoPen)
        self._scene_bg.setZValue(-100)
        scene = QGraphicsScene()
        self.ui.graphicsView.setScene(scene)
        scene.addItem(self._scene_bg)
        scene.changed.connect(self.handle_scene_changed)
        return scene

    @Slot("QList<QRectF>", name="handle_scene_changed")
    def handle_scene_changed(self, region):
        """Make a new scene with usage instructions if previous is empty,
        where empty means the only item is the bg.
        """
        if len(self.ui.graphicsView.scene().items()) > 1:
            return
        scene = self.new_scene()
        msg = "\t• Select items in the 'Object tree' to show objects here.\t\n" \
            + "\t\tYou can select multiple ones by holding the 'Ctrl' key.\t\n\n"
        if not self.read_only:
            msg += "\t• Drag icons from the 'Item palette' and drop them here to add new.\t\n"
        msg_item = CustomTextItem(msg, self.font)
        scene.addItem(msg_item)
        self._has_graph = False
        self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QPoint", "QString", name="handle_item_dropped")
    def handle_item_dropped(self, pos, text):
        if self._has_graph:
            scene = self.ui.graphicsView.scene()
        else:
            scene = self.new_scene()
        # Make scene background the size of the scene
        view_rect = self.ui.graphicsView.viewport().rect()
        top_left = self.ui.graphicsView.mapToScene(view_rect.topLeft())
        bottom_right = self.ui.graphicsView.mapToScene(view_rect.bottomRight())
        rectf = QRectF(top_left, bottom_right)
        self._scene_bg.setRect(rectf)
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        data = eval(text)
        if data["type"] == "object_class":
            class_name = data["name"]
            extent = 2 * self.font.pointSize()
            self.object_item_placeholder = ObjectItem(
                self, None, class_name, scene_pos.x(), scene_pos.y(), extent)
            scene.addItem(self.object_item_placeholder)
            class_id = data["id"]
            self.show_add_objects_form(class_id)
        elif data["type"] == "relationship_class":
            object_class_name_list = data["object_class_name_list"].split(',')
            object_name_list = object_class_name_list
            extent = 2 * self.font.pointSize()
            relationship_parts = self.relationship_parts(
                object_class_name_list, object_name_list, extent,
                self.font, arc_pen_style=Qt.DotLine)
            self.add_relationship_template(scene, scene_pos.x(), scene_pos.y(), *relationship_parts)
            self._has_graph = True
            self.relationship_class_dict[self.template_id] = {"id": data["id"], "name": data["name"]}
            self.template_id += 1

    def add_relationship_template(self, scene, x, y, object_items, arc_items):
        """Add relationship parts into the scene to form a 'relationship template'."""
        for item in object_items + arc_items:
            scene.addItem(item)
        # Move
        rectf = QRectF()
        for object_item in object_items:
            rectf |= object_item.sceneBoundingRect()
        center = rectf.center()
        for object_item in object_items:
            object_item.moveBy(x - center.x(), y - center.y())
            object_item.move_related_items_by(QPointF(x, y) - center)
        for dimension, object_item in enumerate(object_items):
            object_item.make_template()
            object_item.template_id_dim[self.template_id] = dimension
        for arc_item in arc_items:
            arc_item.make_template()
            arc_item.template_id = self.template_id

    @busy_effect
    def add_relationship(self, template_id, object_items):
        """Try and add relationship given a template id and a list of object items."""
        object_id_list = list()
        object_name_list = list()
        object_dimensions = [x.template_id_dim[template_id] for x in object_items]
        for dimension in sorted(object_dimensions):
            ind = object_dimensions.index(dimension)
            item = object_items[ind]
            object_name = item._object_name
            if not object_name:
                logging.debug("can't find name {}".format(object_name))
                return False
            object_ = self.db_map.single_object(name=object_name).one_or_none()
            if not object_:
                logging.debug("can't find object {}".format(object_name))
                return False
            object_id_list.append(object_.id)
            object_name_list.append(object_name)
        if len(object_id_list) < 2:
            logging.debug("too short {}".format(len(object_id_list)))
            return False
        name = self.relationship_class_dict[template_id]["name"] + "_" + "__".join(object_name_list)
        class_id = self.relationship_class_dict[template_id]["id"]
        wide_kwargs = {
            'name': name,
            'object_id_list': object_id_list,
            'class_id': class_id
        }
        try:
            wide_relationship = self.db_map.add_wide_relationships(*[wide_kwargs])[0]
            for item in object_items:
                del item.template_id_dim[template_id]
            items = self.ui.graphicsView.scene().items()
            arc_items = [x for x in items if isinstance(x, ArcItem) and x.template_id == template_id]
            for item in arc_items:
                item.remove_template()
                item.template_id = None
            self.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new relationship '{}'.".format(wide_relationship.name)
            self.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return False

    def relationship_parts(self, object_class_name_list, object_name_list, extent, font,
                           arc_pen_style=Qt.SolidLine, object_label_position="under_icon"):
        """Lists of object and arc items that form a relationship."""
        object_items = list()
        arc_items = list()
        src_ind_list = list(range(len(object_name_list)))
        dst_ind_list = src_ind_list[1:] + src_ind_list[:1]
        d = self.shortest_path_matrix(object_name_list, src_ind_list, dst_ind_list, self._spread / 2)
        if d is None:
            return [], []
        x, y = self.vertex_coordinates(d)
        for x_, y_, object_name, object_class_name in zip(x, y, object_name_list, object_class_name_list):
            object_item = ObjectItem(
                self, object_name, object_class_name, x_, y_, extent,
                label_font=font, label_color=Qt.transparent, label_position=object_label_position)
            object_items.append(object_item)
        for i in range(len(object_items)):
            src_item = object_items[i]
            try:
                dst_item = object_items[i + 1]
            except IndexError:
                dst_item = object_items[0]
            arc_item = ArcItem(self, src_item, dst_item, extent / 4, self.arc_color, pen_style=arc_pen_style)
            arc_items.append(arc_item)
        return object_items, arc_items

    @Slot(name="show_add_object_classes_form")
    def show_add_object_classes_form(self):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self)
        dialog.show()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        for object_class in object_classes:
            self.object_tree_model.add_object_class(object_class)
            self.object_class_list_model.add_object_class(object_class)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    def show_add_relationship_classes_form(self):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self)
        dialog.show()

    def add_relationship_classes(self, wide_relationship_classes):
        """Insert new relationship classes."""
        dim_count_list = list()
        for wide_relationship_class in wide_relationship_classes:
            self.relationship_class_list_model.add_relationship_class(wide_relationship_class)
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully added new relationship classes '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    def show_add_objects_form(self, class_id=None):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, class_id=class_id, force_default=True)
        dialog.rejected.connect(lambda: self.ui.graphicsView.scene().removeItem(self.object_item_placeholder))
        dialog.show()

    def add_objects(self, objects):
        """Insert new objects."""
        for object_ in objects:
            self.object_tree_model.add_object(object_, flat=True)
        object_name_list = [x.name for x in objects]
        src_ind_list = list()
        dst_ind_list = list()
        d = self.shortest_path_matrix(object_name_list, src_ind_list, dst_ind_list, self._spread)
        x, y = self.vertex_coordinates(d)
        scene = self.ui.graphicsView.scene()
        object_class_name = self.object_item_placeholder._object_class_name
        x_offset = self.object_item_placeholder.x()
        y_offset = self.object_item_placeholder.y()
        extent = self.object_item_placeholder._extent
        scene.removeItem(self.object_item_placeholder)
        for x_, y_, object_name in zip(x, y, object_name_list):
            object_item = ObjectItem(
                self, object_name, object_class_name, x_offset + x_, y_offset + y_, extent,
                label_font=self.font, label_color=self.label_color)
            scene.addItem(object_item)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)
        self._has_graph = True

    def restore_ui(self):
        """Restore UI state from previous session."""
        graph_view_widget = "graphViewWidget" if not self.read_only else "graphViewWidgetReadOnly"
        window_size = self.qsettings.value("{0}/windowSize".format(graph_view_widget))
        window_state = self.qsettings.value("{0}/windowState".format(graph_view_widget))
        window_pos = self.qsettings.value("{0}/windowPosition".format(graph_view_widget))
        window_maximized = self.qsettings.value("{0}/windowMaximized".format(graph_view_widget), defaultValue='false')
        n_screens = self.qsettings.value("{0}/n_screens".format(graph_view_widget), defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def show_graph_view_context_menu(self, global_pos):
        """Show context menu for graphics view."""
        self.graph_view_context_menu = GraphViewContextMenu(self, global_pos)
        option = self.graph_view_context_menu.get_action()
        if option == "Reset graph":
            self.rejected_items = list()
            self.build_graph()
        elif option == "Show hidden items":
            scene = self.ui.graphicsView.scene()
            if scene:
                for item in self.hidden_items:
                    item.set_all_visible(True)
                self.hidden_items = list()
        else:
            pass
        self.graph_view_context_menu.deleteLater()
        self.graph_view_context_menu = None

    def show_object_item_context_menu(self, global_pos):
        """Show context menu for object_item."""
        self.object_item_context_menu = ObjectItemContextMenu(self, global_pos)
        option = self.object_item_context_menu.get_action()
        scene = self.ui.graphicsView.scene()
        if scene:
            object_items = [x for x in scene.selectedItems() if isinstance(x, ObjectItem)]
            if option == "Hide selected":
                self.hidden_items.extend(object_items)
                for item in object_items:
                    item.set_all_visible(False)
            elif option == "Ignore selected and rebuild graph":
                self.rejected_items.extend(object_items)
                self.build_graph()
            else:
                pass
        self.object_item_context_menu.deleteLater()
        self.object_item_context_menu = None

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        config = self._owner._toolbox._config
        commit_at_exit = config.get("settings", "commit_at_exit")
        if commit_at_exit == "0":
            # Don't commit session and don't show message box
            return
        elif commit_at_exit == "1":  # Default
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit pending changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setInformativeText("WARNING: If you choose not to commit, all changes will be lost.")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            chk = chkbox.checkState()
            if answer == QMessageBox.Yes:
                self.show_commit_session_dialog()
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "2")
            else:
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "0")
        elif commit_at_exit == "2":
            # Commit session and don't show message box
            self.show_commit_session_dialog()
        else:
            config.set("settings", "commit_at_exit", "1")
        return

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        graph_view_widget = "graphViewWidget" if not self.read_only else "graphViewWidgetReadOnly"
        self.qsettings.setValue("{0}/windowSize".format(graph_view_widget), self.size())
        self.qsettings.setValue("{0}/windowPosition".format(graph_view_widget), self.pos())
        self.qsettings.setValue("{0}/windowState".format(graph_view_widget), self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("{0}/windowMaximized".format(graph_view_widget), True)
        else:
            self.qsettings.setValue("{0}/windowMaximized".format(graph_view_widget), False)
        if self.db_map.has_pending_changes():
            self.show_commit_session_prompt()
        self.db_map.close()
        if event:
            event.accept()
