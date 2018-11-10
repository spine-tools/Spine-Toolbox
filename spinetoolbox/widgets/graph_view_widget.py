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

import os
from ui.graph_view_form import Ui_MainWindow
from PySide2.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsItem, QGraphicsSimpleTextItem, QGraphicsPixmapItem, \
    QGraphicsLineItem
from PySide2.QtGui import QPixmap, QFont, QFontMetrics, QPen, QColor
from PySide2.QtCore import Qt, Slot
import numpy as np
from numpy import flatnonzero as find
from numpy import atleast_1d as arr
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import minimize
import logging
from models import FlatObjectTreeModel
from widgets.custom_delegates import CheckBoxDelegate


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
        self.setWindowTitle("Data store graph view    -- {} --".format(database))
        self._scene = QGraphicsScene()
        self.font = QFont("", 64)
        self.font_metric = QFontMetrics(self.font)
        self.ui.graphicsView.setScene(self._scene)
        self.object_name_list = list()
        self.pixmap_dict = {}
        self.arc_name_list = list()
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
        self.add_toggle_view_actions()
        self.build_graph()

    def show(self):
        """Adjust splitter so that object tree is pretty visible."""
        super().show()
        length = self.ui.treeView.header().length()
        sizes = self.ui.splitter_tree_graph.sizes()
        self.ui.splitter_tree_graph.setSizes([length, sizes[1] - (length - sizes[0])])

    def connect_signals(self):
        """Connect signals."""
        self.ui.treeView.itemDelegateForColumn(1).commit_data.connect(self.status_data_changed)
        self.ui.actionBuild.triggered.connect(self.build_graph)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        pass

    @Slot("bool", name="build_graph")
    def build_graph(self, checked=True):
        self.init_graph_data()
        self.make_graph()
        self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QModelIndex", name="status_data_changed")
    def status_data_changed(self, index):
        """Called when checkbox delegate wants to edit status data."""
        status = self.object_tree_model.data(index, Qt.EditRole)
        def set_status(index):
            sibling = index.sibling(index.row(), 1)
            sibling.model().setData(sibling, not status, Qt.EditRole)
        parent = index.sibling(index.row(), 0)
        self.object_tree_model.forward_sweep(parent, call=set_status)

    def init_graph_data(self):
        """Initialize vertex and edge data by querying db_map."""
        self.object_name_list = list()
        self.pixmap_dict = {}
        root_item = self.object_tree_model.root_item
        for i in range(root_item.rowCount()):
            object_class_name_item = root_item.child(i, 0)
            object_class_status_item = root_item.child(i, 1)
            pixmap = object_class_name_item.data(Qt.DecorationRole).pixmap(2 * self.font.pointSize())
            if not object_class_status_item.data(Qt.EditRole):
                continue
            for j in range(object_class_name_item.rowCount()):
                object_name_item = object_class_name_item.child(j, 0)
                object_status_item = object_class_name_item.child(j, 1)
                if not object_status_item.data(Qt.EditRole):
                    continue
                object_name = object_name_item.data(Qt.EditRole)
                self.object_name_list.append(object_name)
                self.pixmap_dict[object_name] = pixmap
        self.arc_name_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        for relationship in self.db_map.wide_relationship_list():
            accepted_object_name_list = list()
            ignored_object_name_list = list()
            for name in relationship.object_name_list.split(","):
                if name in self.object_name_list:
                    accepted_object_name_list.append(name)
                else:
                    ignored_object_name_list.append(name)
            arc_name = ", ".join(ignored_object_name_list)
            for i in range(len(accepted_object_name_list) - 1):
                src_object_name = accepted_object_name_list[i]
                dst_object_name = accepted_object_name_list[i + 1]
                self.arc_name_list.append(arc_name)
                self.src_ind_list.append(self.object_name_list.index(src_object_name))
                self.dst_ind_list.append(self.object_name_list.index(dst_object_name))

    def shortest_path_matrix(self):
        """Return the shortest-path matrix."""
        N = len(self.object_name_list)
        dist = np.zeros((N, N))
        src_ind = arr(self.src_ind_list)
        dst_ind = arr(self.dst_ind_list)
        max_length = max([self.font_metric.width(x) for x in self.object_name_list], default=0)
        try:
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = self.spacing_factor * max_length
        except IndexError:
            return None
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        d[d == np.inf] = np.max(d[d != np.inf])
        d[d == 0] = max_length * 1e-6
        return d

    def sets(self, N):
        """Make sets of bus pairs (indices)."""
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

    def layout(self, matrix, iterations=10, weight_exp=-2, initial_diameter=100):
        """Return x, y coordinates, using VSGD-MS."""
        N = len(matrix)
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
        self._scene.clear()
        d = self.shortest_path_matrix()
        if d is None:
            text = """
                Check the boxes on the left pane
                to choose which objects to show.
                Once you're ready, press Ctrl+B to build the graph.
            """
            text_item = CustomTextItem(text, self.font)
            self._scene.addItem(text_item)
            self.ui.graphicsView.max_d = self.font_metric.width("Check the boxes on the left pane")
            return
        x, y = self.layout(d)
        object_items = list()
        for i, object_name in enumerate(self.object_name_list):
            pixmap = self.pixmap_dict[object_name]
            object_item = ObjectItem(pixmap, x[i], y[i], 2 * self.font.pointSize())
            text_item = CustomTextItem(object_name, self.font)
            object_item.set_text_item(text_item)
            self._scene.addItem(object_item)
            self._scene.addItem(text_item)
            object_items.append(object_item)
        for i, j, arc_name in zip(self.src_ind_list, self.dst_ind_list, self.arc_name_list):
            arc_item = ArcItem(x[i], y[i], x[j], y[j], self.font.pointSize() / 3)
            text_item = CustomTextItem(arc_name, self.font)
            arc_item.set_text_item(text_item)
            self._scene.addItem(arc_item)
            self._scene.addItem(text_item)
            object_items[i].add_outgoing_arc_item(arc_item)
            object_items[j].add_incoming_arc_item(arc_item)
        self.ui.graphicsView.max_d = np.max(d)


class ObjectItem(QGraphicsPixmapItem):
    """Object item that is drawn into QGraphicsScene.

    Attributes:
        pixmap (QPixmap): pixmap to use
        x (float): x-coordinate of initial position
        y (float): y-coordinate of initial position
        size (int): custom size
    """
    def __init__(self, pixmap, x, y, size):
        super().__init__()
        self.size = size
        self.setPixmap(pixmap.scaled(self.size, self.size))
        self.setPos(x - 0.5 * self.size, y - 0.5 * self.size)
        self.text_item = None
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.setZValue(-1)

    def set_text_item(self, item):
        self.text_item = item
        self.text_item.setPos(self.x() + 0.75 * self.size, self.y() + 0.5 * self.size)

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def mouseMoveEvent(self, event):
        """Reset position of text, incoming and outgoing arcs."""
        super().mouseMoveEvent(event)
        self.text_item.setPos(self.x() + 0.75 * self.size, self.y() + 0.5 * self.size)
        for item in self.outgoing_arc_items:
            item.set_source(self.x() + 0.5 * self.size, self.y() + 0.5 * self.size)
        for item in self.incoming_arc_items:
            item.set_destination(self.x() + 0.5 * self.size, self.y() + 0.5 * self.size)


class ArcItem(QGraphicsLineItem):
    """Arc item that is drawn into QGraphicsScene.

    Attributes:
        x1, y1 (float): source position
        x2, y2 (float): destination position
        width (int): Preferred line width
    """
    def __init__(self, x1, y1, x2, y2, width):
        """Init class."""
        super().__init__(x1, y1, x2, y2)
        self.text_item = None
        self.width = width
        pen = QPen(QColor(64, 64, 64))
        pen.setWidth(self.width)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)
        self.setZValue(-2)

    def set_text_item(self, item):
        self.text_item = item
        self.text_item.hide()

    def set_source(self, x, y):
        """Reset the source point. Used when moving ObjectItems around."""
        x1 = x
        y1 = y
        x2 = self.line().x2()
        y2 = self.line().y2()
        self.setLine(x1, y1, x2, y2)

    def set_destination(self, x, y):
        """Reset the destination point. Used when moving ObjectItems around."""
        x1 = self.line().x1()
        y1 = self.line().y1()
        x2 = x
        y2 = y
        self.setLine(x1, y1, x2, y2)

    def hoverEnterEvent(self, event):
        """Show text on hover."""
        self.text_item.setPos(event.pos().x(), event.pos().y())
        self.text_item.show()

    def hoverMoveEvent(self, event):
        """Reset text position."""
        self.text_item.setPos(event.pos().x(), event.pos().y())

    def hoverLeaveEvent(self, event):
        """Hide text on hover."""
        self.text_item.hide()


class CustomTextItem(QGraphicsSimpleTextItem):
    """Text item that is drawn into QGraphicsScene.

    Attributes:
        text (str): text to show
        font (QFont): font to display the text
    """
    def __init__(self, text, font):
        """Init class."""
        super().__init__(text)
        font.setWeight(QFont.Black)
        self.setFont(font)
        outline_pen = QPen(Qt.white, 2, Qt.SolidLine)
        self.setPen(outline_pen)
        self.setZValue(1)
