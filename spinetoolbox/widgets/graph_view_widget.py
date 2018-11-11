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
from PySide2.QtWidgets import QMainWindow, QGraphicsScene
from PySide2.QtGui import QFont, QFontMetrics, QColor, QGuiApplication
from PySide2.QtCore import Qt, Slot, QSettings
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from widgets.custom_delegates import CheckBoxDelegate
from models import FlatObjectTreeModel
from graphics_items import ObjectItem, ArcItem, ObjectLabelItem, ArcLabelItem, CustomTextItem
from helpers import busy_effect
from config import STATUSBAR_SS


class GraphViewForm(QMainWindow):
    """A widget to show the graph view.

    Attributes:
        view (View): View instance that owns this form
    """

    def __init__(self, view, db_map, database):
        """Initialize class."""
        super().__init__(flags=Qt.Window)  # Setting the parent inherits the stylesheet
        self._view = view
        self.db_map = db_map
        self.spacing_factor = 1.0
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.setWindowTitle("Data store graph view    -- {} --".format(database))
        self.font = QFont("", 64)
        self.font_metric = QFontMetrics(self.font)
        self.object_name_list = list()
        self.pixmap_dict = {}
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        self.object_tree_model = FlatObjectTreeModel(self)
        self.object_tree_model.build_tree(database)
        self.ui.treeView.setModel(self.object_tree_model)
        self.ui.treeView.setItemDelegateForColumn(1, CheckBoxDelegate(self))
        self.ui.treeView.resizeColumnToContents(0)
        self.ui.treeView.resizeColumnToContents(1)
        self.ui.treeView.expand(self.object_tree_model.root_item.index())
        self.ui.treeView.header().swapSections(0, 1)
        self.connect_signals()
        self.restore_ui()
        self.add_toggle_view_actions()
        self.build_graph()

    def show(self):
        """Make sure object tree is somewhat visible."""
        super().show()
        length = self.ui.treeView.header().length()
        sizes = self.ui.splitter_tree_graph.sizes()
        if sizes[0] < length:
            self.ui.splitter_tree_graph.setSizes([length, sizes[1] - (length - sizes[0])])

    def connect_signals(self):
        """Connect signals."""
        self.ui.treeView.itemDelegateForColumn(1).commit_data.connect(self.status_data_changed)
        self.ui.actionBuild.triggered.connect(self.build_graph)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        pass

    @busy_effect
    @Slot("bool", name="build_graph")
    def build_graph(self, checked=True):
        self.init_graph_data()
        self.make_graph()
        self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QModelIndex", name="status_data_changed")
    def status_data_changed(self, index):
        """Called when checkbox delegate wants to edit 'show?' data."""
        self.ui.treeView.setEnabled(False)
        status = self.object_tree_model.data(index, Qt.EditRole)
        if status == "True":
            new_status = "False"
        else:
            new_status = "True"
        def set_status(index, model=self.object_tree_model):
            """Set new satatus for index."""
            sibling = index.sibling(index.row(), 1)
            model.setData(sibling, new_status, Qt.EditRole)
        def update_status(index, model=self.object_tree_model):
            """Update status according to children."""
            if not model.hasChildren(index):
                return
            children_status = list()
            for i in range(model.rowCount(index)):
                child = model.index(i, 1, index)
                children_status.append(child.data(Qt.EditRole))
            sibling = index.sibling(index.row(), 1)
            if all(x == "True" for x in children_status):
                model.setData(sibling, 'True', Qt.EditRole)
            elif all(x == "False" for x in children_status):
                model.setData(sibling, 'False', Qt.EditRole)
            else:
                model.setData(sibling, 'Depends', Qt.EditRole)
        parent = index.sibling(index.row(), 0)
        self.object_tree_model.forward_sweep(parent, call=set_status)
        self.object_tree_model.backward_sweep(parent, call=update_status)
        self.build_graph()
        self.ui.treeView.setEnabled(True)

    def init_graph_data(self):
        """Initialize graph data by querying db_map."""
        self.object_name_list = list()
        self.pixmap_dict = {}
        root_item = self.object_tree_model.root_item
        for i in range(root_item.rowCount()):
            object_class_name_item = root_item.child(i, 0)
            pixmap = object_class_name_item.data(Qt.DecorationRole).pixmap(2 * self.font.pointSize())
            for j in range(object_class_name_item.rowCount()):
                object_name_item = object_class_name_item.child(j, 0)
                object_name = object_name_item.data(Qt.EditRole)
                self.pixmap_dict[object_name] = pixmap
                object_status_item = object_class_name_item.child(j, 1)
                if object_status_item.data(Qt.EditRole) == "True":
                    self.object_name_list.append(object_name)
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        relationship_class_name_dict = {x.id: x.name for x in self.db_map.wide_relationship_class_list()}
        for relationship in self.db_map.wide_relationship_list():
            relationship_class_name = relationship_class_name_dict[relationship.class_id]
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
                arc_object_names = [x for x in object_name_list if x not in (src_object_name, dst_object_name)]
                self.arc_object_names_list.append(arc_object_names)

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
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = self.spacing_factor * max_sep
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        # d[d == np.inf] = np.max(d[d != np.inf])
        d[d == np.inf] = self.spacing_factor * max_sep * 3
        d[d == 0] = self.spacing_factor * max_sep * 1e-6
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
        scene = QGraphicsScene()
        self.ui.graphicsView.setScene(scene)
        d = self.shortest_path_matrix()
        if d is None:
            msg = """
                Check boxes on the left pane to show objects here.
            """
            msg_item = CustomTextItem(msg, self.font)
            scene.addItem(msg_item)
            return
        x, y = self.vertex_coordinates(d)
        object_items = list()
        for i, object_name in enumerate(self.object_name_list):
            pixmap = self.pixmap_dict[object_name]
            object_item = ObjectItem(pixmap, x[i], y[i], 2 * self.font.pointSize())
            label_item = ObjectLabelItem(object_name, self.font, QColor(224, 224, 224, 128))
            object_item.set_label_item(label_item)
            scene.addItem(object_item)
            scene.addItem(label_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            relationship_class_name = self.arc_relationship_class_name_list[k]
            object_names = self.arc_object_names_list[k]
            arc_item = ArcItem(x[i], y[i], x[j], y[j], .5 * self.font.pointSize())
            arc_label_item = ArcLabelItem(
                relationship_class_name, [self.pixmap_dict[x] for x in object_names], object_names,
                2 * self.font.pointSize(), self.font, QColor(224, 224, 224, 224))
            arc_item.set_label_item(arc_label_item)
            scene.addItem(arc_item)
            scene.addItem(arc_label_item)
            object_items[i].add_outgoing_arc_item(arc_item)
            object_items[j].add_incoming_arc_item(arc_item)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("graphViewWidget/windowSize")
        window_pos = self.qsettings.value("graphViewWidget/windowPosition")
        splitter_tree_graph_state = self.qsettings.value("graphViewWidget/splitterTreeGraphState")
        window_maximized = self.qsettings.value("graphViewWidget/windowMaximized", defaultValue='false')  # returns str
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_tree_graph_state:
            self.ui.splitter_tree_graph.restoreState(splitter_tree_graph_state)
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
        self.qsettings.setValue(
            "graphViewWidget/splitterTreeGraphState",
            self.ui.splitter_tree_graph.saveState())
        self.qsettings.setValue("graphViewWidget/windowSize", self.size())
        self.qsettings.setValue("graphViewWidget/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("graphViewWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("graphViewWidget/windowMaximized", False)
        self.db_map.close()
        if event:
            event.accept()
