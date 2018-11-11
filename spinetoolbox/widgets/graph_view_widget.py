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
from PySide2.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsItem, QGraphicsSimpleTextItem, \
    QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsRectItem
from PySide2.QtGui import QPixmap, QFont, QFontMetrics, QPen, QColor, QBrush, QPainterPath
from PySide2.QtCore import Qt, Slot
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from models import FlatObjectTreeModel
from widgets.custom_delegates import CheckBoxDelegate
from helpers import busy_effect


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


class ObjectItem(QGraphicsPixmapItem):
    """Object item to use with GraphViewForm.

    Attributes:
        pixmap (QPixmap): pixmap to use
        x (float): x-coordinate of central point
        y (float): y-coordinate of central point
        extent (int): extent
    """
    def __init__(self, pixmap, x, y, extent):
        super().__init__()
        self.extent = extent
        self.setPixmap(pixmap.scaled(self.extent, self.extent))
        self.setPos(x - 0.5 * self.extent, y - 0.5 * self.extent)
        self.label_item = None
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

    def shape(self):
        """Return shape."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def set_label_item(self, item):
        self.label_item = item
        self.label_item.setPos(self.x() + self.extent, self.y())

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def mouseMoveEvent(self, event):
        """Reset position of text, incoming and outgoing arcs."""
        super().mouseMoveEvent(event)
        self.label_item.setPos(self.x() + self.extent, self.y())
        for item in self.outgoing_arc_items:
            item.set_source_point(self.x() + 0.5 * self.extent, self.y() + 0.5 * self.extent)
        for item in self.incoming_arc_items:
            item.set_destination_point(self.x() + 0.5 * self.extent, self.y() + 0.5 * self.extent)

    def hoverEnterEvent(self, event):
        """Show text on hover."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = True
        for item in self.outgoing_arc_items:
            item.is_src_hovered = True

    def hoverLeaveEvent(self, event):
        """Hide text on hover."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = False
        for item in self.outgoing_arc_items:
            item.is_src_hovered = False


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm.

    Attributes:
        x1, y1 (float): source position
        x2, y2 (float): destination position
        width (int): Preferred line width
    """
    def __init__(self, x1, y1, x2, y2, width):
        """Init class."""
        super().__init__(x1, y1, x2, y2)
        self.label_item = None
        self.width = width
        self.is_src_hovered = False
        self.is_dst_hovered = False
        pen = QPen(QColor(64, 64, 64))
        pen.setWidth(self.width)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)
        self.setZValue(-2)
        self.shape_item = QGraphicsLineItem(x1, y1, x2, y2)
        shape_pen = QPen()
        shape_pen.setWidth(3 * self.width)
        self.shape_item.setPen(shape_pen)
        self.shape_item.hide()

    def shape(self):
        return self.shape_item.shape()

    def set_label_item(self, item):
        self.label_item = item
        self.label_item.hide()

    def set_source_point(self, x, y):
        """Reset the source point. Used when moving ObjectItems around."""
        x1 = x
        y1 = y
        x2 = self.line().x2()
        y2 = self.line().y2()
        self.setLine(x1, y1, x2, y2)
        self.shape_item.setLine(x1, y1, x2, y2)

    def set_destination_point(self, x, y):
        """Reset the destination point. Used when moving ObjectItems around."""
        x1 = self.line().x1()
        y1 = self.line().y1()
        x2 = x
        y2 = y
        self.setLine(x1, y1, x2, y2)
        self.shape_item.setLine(x1, y1, x2, y2)

    def hoverEnterEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(event.pos().x(), event.pos().y())
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverMoveEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(event.pos().x(), event.pos().y())
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverLeaveEvent(self, event):
        """Hide label."""
        self.label_item.hide()


class ObjectLabelItem(QGraphicsRectItem):
    """Label item for objects to use with GraphViewForm.

    Attributes:
        object_name (str): object name
        font (QFont): font to display the text
        color (QColor): color to paint the label
    """
    def __init__(self, object_name, font, color):
        super().__init__()
        self.title_item = CustomTextItem(object_name, font)
        self.title_item.setParentItem(self)
        self.setRect(self.childrenBoundingRect())
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setZValue(0)


class ArcLabelItem(QGraphicsRectItem):
    """Label item for arcs to use with GraphViewForm.

    Attributes:
        relationship_class_name (str): relationship class name
        object_pixmaps (list): object pixmaps
        object_names (list): object names
        extent (int): extent of object items
        font (QFont): font to display the text
        color (QColor): color to paint the label
    """
    def __init__(self, relationship_class_name, object_pixmaps, object_names, extent, font, color):
        super().__init__()
        self.title_item = CustomTextItem(relationship_class_name, font)
        self.title_item.setParentItem(self)
        self.object_items = []
        y_offset = self.title_item.boundingRect().height()
        for k in range(len(object_pixmaps)):
            object_pixmap = object_pixmaps[k]
            object_name = object_names[k]
            object_item = ObjectItem(object_pixmap, .5 * extent, y_offset + (k + .5) * extent, extent)
            object_item.setParentItem(self)
            label_item = ObjectLabelItem(object_name, font, Qt.transparent)
            label_item.setParentItem(self)
            object_item.set_label_item(label_item)
            self.object_items.append(object_item)
        self.setRect(self.childrenBoundingRect())
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setZValue(1)


class CustomTextItem(QGraphicsSimpleTextItem):
    """Custom text item to use with GraphViewForm.

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
