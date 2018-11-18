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
    QAction, QGraphicsRectItem
from PySide2.QtGui import QFont, QFontMetrics, QColor, QGuiApplication, QIcon
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QPointF, QRectF, QItemSelection, QItemSelectionModel, QSize
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog
from models import ObjectTreeModel, ObjectClassListModel, RelationshipClassListModel
from graphics_items import ObjectItem, ArcItem, ObjectLabelItem, CustomTextItem
from helpers import busy_effect
from config import STATUSBAR_SS


class GraphViewForm(QMainWindow):
    """A widget to show the graph view.

    Attributes:
        view (View): View instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, view, db_map, database):
        """Initialize class."""
        super().__init__(flags=Qt.Window)  # Setting the parent inherits the stylesheet
        self._view = view
        self.db_map = db_map
        self._spacing_factor = 1.0
        self._has_graph = False
        self._scene_bg = None
        self.database = database
        self.object_item_placeholder = None
        self.err_msg = QErrorMessage(self)
        self.font = QFont("", 64)
        self.font_metric = QFontMetrics(self.font)
        self.object_name_list = list()
        self.object_class_name_list = list()
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        self.object_template_inds = list()
        self.arc_template_inds = list()
        self.object_tree_model = ObjectTreeModel(self)
        self.object_class_list_model = ObjectClassListModel(self)
        self.relationship_class_list_model = RelationshipClassListModel(self)
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
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
        self.set_commit_rollback_actions_enabled(False)
        self.build_graph()
        self.setWindowTitle("Data store graph view    -- {} --".format(database))
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_models(self):
        """Initialize models and their respective views."""
        self.object_tree_model.build_flat_tree(self.database)
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()
        self.ui.treeView.resizeColumnToContents(0)
        self.ui.treeView.expand(self.object_tree_model.root_item.index())

    def setup_views(self):
        """Adjust grid width to largest item; setup 'Add more' action and button."""
        # object class
        width_list = list()
        for item in self.object_class_list_model.findItems("*", Qt.MatchWildcard):
            data = item.data(Qt.DisplayRole)
            font = item.data(Qt.FontRole)
            width = QFontMetrics(font).width(data)
            width_list.append(width)
        width = max(width_list)
        height = self.ui.listView_object_class.gridSize().height()
        #self.ui.listView_object_class.setGridSize(QSize(width, height))
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
        width_list = list()
        for item in self.relationship_class_list_model.findItems("*", Qt.MatchWildcard):
            data = item.data(Qt.DisplayRole)
            font = item.data(Qt.FontRole)
            width = QFontMetrics(font).width(data)
            width_list.append(width)
        width = max(width_list)
        height = self.ui.listView_relationship_class.gridSize().height()
        #self.ui.listView_relationship_class.setGridSize(QSize(width, height))
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
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_palette.toggleViewAction())

    def set_commit_rollback_actions_enabled(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

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
        if not self.init_graph_data():
            return
        self._has_graph = self.make_graph()
        if self._has_graph:
            self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QItemSelection", "QItemSelection", name="receive_item_tree_selection_changed")
    def receive_item_tree_selection_changed(self, selected, deselected):
        """Select or deselect all children when selecting or deselecting the parent."""
        model = self.ui.treeView.selectionModel()
        current = model.currentIndex()
        current_is_selected = model.isSelected(current)
        # Deselect children of newly deselected items
        new_selection = QItemSelection()
        for index in deselected.indexes():
            if not self.object_tree_model.hasChildren(index):
                continue
            row_count = self.object_tree_model.rowCount(index)
            top = self.object_tree_model.index(0, 0, index)
            bottom = self.object_tree_model.index(row_count - 1, 0, index)
            new_selection.merge(QItemSelection(top, bottom), QItemSelectionModel.Select)
        model.select(new_selection, QItemSelectionModel.Deselect)
        # Select children of newly selected items (and of current item, if selected)
        if current_is_selected:
            model.select(current, QItemSelectionModel.Select)
            selected.select(current, current)
        new_selection = QItemSelection()
        for index in selected.indexes():
            if not self.object_tree_model.hasChildren(index):
                continue
            row_count = self.object_tree_model.rowCount(index)
            top = self.object_tree_model.index(0, 0, index)
            bottom = self.object_tree_model.index(row_count - 1, 0, index)
            new_selection.merge(QItemSelection(top, bottom), QItemSelectionModel.Select)
        model.select(new_selection, QItemSelectionModel.Select)
        self.build_graph()

    def init_graph_data(self):
        """Initialize graph data by querying db_map.

        Returns:
            True if graph data changed, False otherwise
        """
        last_object_name_list = self.object_name_list.copy()
        self.object_name_list = list()
        self.object_class_name_list = list()
        selection_model = self.ui.treeView.selectionModel()
        root_item = self.object_tree_model.root_item
        for i in range(root_item.rowCount()):
            object_class_name_item = root_item.child(i, 0)
            object_class_name = object_class_name_item.data(Qt.EditRole)
            for j in range(object_class_name_item.rowCount()):
                object_name_item = object_class_name_item.child(j, 0)
                object_name = object_name_item.data(Qt.EditRole)
                index = self.object_tree_model.indexFromItem(object_name_item)
                if selection_model.isSelected(index):
                    self.object_name_list.append(object_name)
                    self.object_class_name_list.append(object_class_name)
        if last_object_name_list and last_object_name_list == self.object_name_list:
            return False
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
        self.object_template_inds = list()
        self.arc_template_inds = list()
        if scene:
            object_items = [x for x in scene.items() if isinstance(x, ObjectItem) and x.is_template]
            object_ind = len(self.object_name_list)
            object_ind_dict = {}
            for item in object_items:
                object_class_name = item._object_class_name
                self.object_name_list.append(object_class_name)
                self.object_class_name_list.append(object_class_name)
                object_ind_dict[item] = object_ind
                self.object_template_inds.append(object_ind)
                object_ind += 1
            arc_ind = len(self.arc_object_names_list)
            arc_items = [x for x in scene.items() if isinstance(x, ArcItem) and x.is_template]
            for item in arc_items:
                src_item = item.src_item
                dst_item = item.dst_item
                try:
                    src_ind = object_ind_dict[src_item]
                except KeyError:
                    try:
                        src_object_name = src_item.label_item.text_item.text()
                        src_ind = self.object_name_list.index(src_object_name)
                    except ValueError:
                        object_class_name = src_item._object_class_name
                        self.object_name_list.append(src_object_name)
                        self.object_class_name_list.append(object_class_name)
                        src_ind = object_ind
                        object_ind_dict[src_item] = object_ind
                        object_ind += 1
                try:
                    dst_ind = object_ind_dict[dst_item]
                except KeyError:
                    try:
                        dst_object_name = dst_item.label_item.text_item.text()
                        dst_ind = self.object_name_list.index(dst_object_name)
                    except ValueError:
                        object_class_name = dst_item._object_class_name
                        self.object_name_list.append(dst_object_name)
                        self.object_class_name_list.append(object_class_name)
                        dst_ind = object_ind
                        object_ind_dict[dst_item] = object_ind
                        object_ind += 1
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                self.arc_relationship_class_name_list.append("")
                self.arc_object_names_list.append("")
                self.arc_object_class_names_list.append("")
                self.arc_template_inds.append(arc_ind)
                arc_ind += 1
        return True

    def shortest_path_matrix(self):
        """Return the shortest-path matrix."""
        N = len(self.object_name_list)
        if not N:
            return None
        dist = np.zeros((N, N))
        src_ind = arr(self.src_ind_list)
        dst_ind = arr(self.dst_ind_list)
        max_sep = max([self.font_metric.width(x) for x in self.object_name_list], default=0)
        try:
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = self._spacing_factor * max_sep
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        # d[d == np.inf] = np.max(d[d != np.inf])
        d[d == np.inf] = self._spacing_factor * max_sep * 3
        d[d == 0] = self._spacing_factor * max_sep * 1e-6
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

    def vertex_coordinates(self, matrix, iterations=10, weight_exp=-2, initial_diameter=100):
        """Return x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
        N = len(matrix)
        if N == 1:
            return [0], [0]
        mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))  # Upper triangular except diagonal
        np.random.seed(0)
        layout = np.random.rand(N, 2) * initial_diameter - initial_diameter / 2  # Random layout with diameter 100
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
                # current distance (possibly accounting for rescaling of system)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] / 2 * (layout[v1] - layout[v2]) / dist[:, None]  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
        return layout[:, 0], layout[:, 1]

    def make_graph(self):
        """Make graph."""
        scene = self.new_scene()
        d = self.shortest_path_matrix()
        if d is None:
            return False
        x, y = self.vertex_coordinates(d)
        object_items = list()
        for i in range(len(self.object_name_list)):
            object_name = self.object_name_list[i]
            object_class_name = self.object_class_name_list[i]
            extent = 2 * self.font.pointSize()
            object_item = ObjectItem(object_class_name, x[i], y[i], extent)
            if i in self.object_template_inds:
                object_item.make_template()
            label_item = ObjectLabelItem(object_name, self.font, QColor(224, 224, 224, 128))
            object_item.set_label_item(label_item)
            scene.addItem(object_item)
            scene.addItem(label_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            extent = 2 * self.font.pointSize()
            arc_item = ArcItem(object_items[i], object_items[j], .25 * extent)
            object_class_names = self.arc_object_class_names_list[k]
            object_names = self.arc_object_names_list[k]
            if k in self.arc_template_inds:
                arc_item.make_template()
            # relationship_class_name = self.arc_relationship_class_name_list[k]
            relationship_parts = self.relationship_parts(
                object_class_names, object_names, extent,
                self.font, QColor(224, 224, 224, 128), spread_factor=2)
            arc_label_item = self.arc_label_item(QColor(224, 224, 224, 128), *relationship_parts)
            arc_item.set_label_item(arc_label_item)
            scene.addItem(arc_item)
            scene.addItem(arc_label_item)
        return True

    def arc_label_item(self, color, object_items, label_items, arc_items):
        """A QGraphicsRectItem with a relationship to use as arc label"""
        label = QGraphicsRectItem()
        for item in object_items + label_items + arc_items:
            item.setParentItem(label)
        rect = label.childrenBoundingRect()
        label.setBrush(color)
        label.setPen(Qt.NoPen)
        label.setRect(rect)
        label.setZValue(-2)
        return label

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
        msg = """
            * Select classes and objects in the 'Object tree' to show them here.
               You can select multiple items by holding the 'Ctrl' key.
            * Drag icons from the 'Item palette' and drop them here to add new items.
        """
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
            self.object_item_placeholder = ObjectItem(class_name, scene_pos.x(), scene_pos.y(), extent)
            scene.addItem(self.object_item_placeholder)
            class_id = data["id"]
            self.show_add_objects_form(class_id)
        elif data["type"] == "relationship_class":
            object_class_name_list = data["object_class_name_list"].split(',')
            extent = 2 * self.font.pointSize()
            relationship_parts = self.relationship_parts(
                object_class_name_list, [], extent,
                self.font, QColor(224, 224, 224, 128))
            self.add_relationship_template(scene, scene_pos.x(), scene_pos.y(), *relationship_parts)
            self._has_graph = True

    def add_relationship_template(self, scene, x, y, object_items, label_items, arc_items):
        """Add relationship parts into the scene in form of a template."""
        for item in object_items + label_items + arc_items:
            scene.addItem(item)
        # Move
        rectf = QRectF()
        for object_item in object_items:
            rectf |= object_item.sceneBoundingRect()
        center = rectf.center()
        for object_item in object_items:
            object_item.moveBy(x - center.x(), y - center.y())
            object_item.move_related_items_by(QPointF(x, y) - center)
        for object_item in object_items:
            object_item.make_template()
        for arc_item in arc_items:
            arc_item.make_template()

    def relationship_parts(self, object_class_name_list, object_name_list, extent, font, color,
                           spread_factor=4, arc_pen_style=Qt.SolidLine):
        """Lists of object, label, and arc items to form a relationship."""
        object_items = list()
        label_items = list()
        arc_items = list()
        object_class_name_matrix = [object_class_name_list[i:i + 2] for i in range(0, len(object_class_name_list), 2)]
        x_offset = 0
        x_step = spread_factor * extent
        y_offset = spread_factor * extent
        k = 0
        for object_class_name_row in object_class_name_matrix:
            for j, object_class_name in enumerate(object_class_name_row):
                if j % 2 == 1:
                    x_ = x_offset + x_step / 2
                    y_ = y_offset
                else:
                    x_ = x_offset
                    y_ = 0
                object_item = ObjectItem(object_class_name, x_, y_, extent)
                object_items.append(object_item)
                try:
                    object_name = object_name_list[k]
                except IndexError:
                    object_name = object_class_name
                label_item = ObjectLabelItem(object_name, font, Qt.transparent)
                object_item.set_label_item(label_item)
                label_items.append(label_item)
                k += 1
            x_offset += x_step
        for i in range(len(object_items)):
            src_item = object_items[i]
            try:
                dst_item = object_items[i + 1]
            except IndexError:
                dst_item = object_items[0]
            arc_item = ArcItem(src_item, dst_item, extent / 4, pen_style=arc_pen_style)
            arc_items.append(arc_item)
        return object_items, label_items, arc_items

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
        dialog = AddObjectsDialog(self, class_id=class_id)
        dialog.rejected.connect(lambda: self.ui.graphicsView.scene().removeItem(self.object_item_placeholder))
        dialog.show()

    def add_objects(self, objects):
        """Insert new objects."""
        scene = self.ui.graphicsView.scene()
        object_class_name = self.object_item_placeholder._object_class_name
        x = self.object_item_placeholder.x()
        y = self.object_item_placeholder.y()
        extent = self.object_item_placeholder._extent
        scene.removeItem(self.object_item_placeholder)
        for k, object_ in enumerate(objects):
            self.object_tree_model.add_object(object_, flat=True)
            object_item = ObjectItem(object_class_name, x + .5 * extent, y + (k + .5) * extent, extent)
            label_item = ObjectLabelItem(object_.name, self.font, QColor(224, 224, 224, 128))
            object_item.set_label_item(label_item)
            scene.addItem(object_item)
            scene.addItem(label_item)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)
        self._has_graph = True

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("graphViewWidget/windowSize")
        window_state = self.qsettings.value("graphViewWidget/windowState")
        window_pos = self.qsettings.value("graphViewWidget/windowPosition")
        window_maximized = self.qsettings.value("graphViewWidget/windowMaximized", defaultValue='false')  # returns str
        n_screens = self.qsettings.value("graphViewWidget/n_screens", defaultValue=1)
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

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("graphViewWidget/windowSize", self.size())
        self.qsettings.setValue("graphViewWidget/windowPosition", self.pos())
        self.qsettings.setValue("graphViewWidget/windowState", self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("graphViewWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("graphViewWidget/windowMaximized", False)
        self.db_map.close()
        if event:
            event.accept()
