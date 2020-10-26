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

import math
import enum
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtCore import Signal, Slot, QObject, QThread, Qt
from PySide2.QtWidgets import QProgressBar, QDialogButtonBox, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PySide2.QtGui import QPainter, QColor
from spinetoolbox.helpers import busy_effect


@busy_effect
def make_heat_map(x, y, values):
    values = np.array(values)
    min_x, min_y, max_x, max_y = min(x), min(y), max(x), max(y)
    tick_count = round(len(values) ** 2)
    xticks = np.linspace(min_x, max_x, tick_count)
    yticks = np.linspace(min_y, max_y, tick_count)
    xv, yv = np.meshgrid(xticks, yticks)
    try:
        import scipy.interpolate

        points = np.column_stack((x, y))
        heat_map = scipy.interpolate.griddata(points, values, (xv, yv), method="cubic")
    except ImportError:
        import matplotlib.tri as tri

        triang = tri.Triangulation(x, y)
        interpolator = tri.CubicTriInterpolator(triang, values)
        heat_map = interpolator(xv, yv)
    return heat_map, xv, yv, min_x, min_y, max_x, max_y


class _State(enum.Enum):
    """State of GraphLayoutGenerator."""

    SLEEPING = enum.auto()
    STOPPED = enum.auto()
    RUNNING = enum.auto()


class ProgressBarWidget(QWidget):
    def __init__(self, layout_generator, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        inner_widget = QWidget(self)
        layout = QHBoxLayout(self)
        layout.addStretch()
        layout.addWidget(inner_widget)
        layout.addStretch()
        inner_layout = QVBoxLayout(inner_widget)
        label = QLabel()
        label.setStyleSheet("QLabel{color:white; font-weight: bold; font-size:18px;}")
        label.setAlignment(Qt.AlignHCenter)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, layout_generator.iterations - 1)
        progress_bar.setTextVisible(False)
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        previews_button = button_box.addButton("Show previews", QDialogButtonBox.NoRole)
        previews_button.setCheckable(True)
        previews_button.toggled.connect(layout_generator.set_show_previews)
        previews_button.toggled.connect(
            lambda checked: previews_button.setText(f"{'Hide' if checked else 'Show'} previews")
        )
        cancel_button = button_box.addButton("Cancel", QDialogButtonBox.NoRole)
        cancel_button.clicked.connect(layout_generator.stop)
        inner_layout.addStretch()
        inner_layout.addWidget(label)
        inner_layout.addWidget(progress_bar)
        inner_layout.addWidget(button_box)
        inner_layout.addStretch()
        self.setFixedSize(parent.size())
        layout_generator.stopped.connect(self.close)
        layout_generator.progressed.connect(progress_bar.setValue)
        layout_generator.msg.connect(label.setText)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 96))
        super().paintEvent(event)
        painter.end()


class GraphLayoutGenerator(QObject):
    """Computes the layout for the Entity Graph View."""

    finished = Signal(object, object)
    started = Signal()
    progressed = Signal(int)
    stopped = Signal()
    blocked = Signal(bool)
    msg = Signal(str)

    def __init__(self, vertex_count, src_inds, dst_inds, spread, heavy_positions=None, iterations=12, weight_exp=-2):
        super().__init__()
        if vertex_count == 0:
            vertex_count = 1
        if heavy_positions is None:
            heavy_positions = dict()
        self._show_previews = False
        self.vertex_count = vertex_count
        self.src_inds = src_inds
        self.dst_inds = dst_inds
        self.spread = spread
        self.heavy_positions = heavy_positions
        self.iterations = max(3, round(iterations * (1 - len(heavy_positions) / self.vertex_count)))
        self.weight_exp = weight_exp
        self.initial_diameter = (self.vertex_count ** (0.5)) * self.spread
        self._state = _State.SLEEPING
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.start()
        qApp.aboutToQuit.connect(self._thread.quit)  # pylint: disable=undefined-variable
        self.started.connect(self.get_coordinates)
        self.finished.connect(self.clean_up)

    def show_progress_widget(self, parent):
        widget = ProgressBarWidget(self, parent)
        widget.show()

    def clean_up(self):
        self.deleteLater()
        self._thread.quit()

    def is_running(self):
        return self._state == _State.RUNNING

    @Slot(bool)
    def stop(self, _checked=False):
        self._state = _State.STOPPED
        self.clean_up()
        self.stopped.emit()

    @Slot(bool)
    def set_show_previews(self, checked):
        self._show_previews = checked

    def emit_finished(self, x, y):
        if self._state == _State.STOPPED:
            return
        self.finished.emit(x, y)

    def start(self):
        self.started.emit()

    def shortest_path_matrix(self):
        """Returns the shortest-path matrix.
        """
        if not self.src_inds:
            # Introduce fake pair of links to help 'spreadness'
            self.src_inds = [self.vertex_count, self.vertex_count]
            self.dst_inds = [np.random.randint(0, self.vertex_count), np.random.randint(0, self.vertex_count)]
            self.vertex_count += 1
        dist = np.zeros((self.vertex_count, self.vertex_count))
        src_inds = arr(self.src_inds)
        dst_inds = arr(self.dst_inds)
        try:
            dist[src_inds, dst_inds] = dist[dst_inds, src_inds] = self.spread
        except IndexError:
            pass
        start = 0
        slices = []
        iteration = 0
        self.msg.emit("Computing shortest-path matrix...")
        while start < self.vertex_count:
            if self._state == _State.STOPPED:
                return
            self.progressed.emit(iteration)
            stop = min(self.vertex_count, start + math.ceil(self.vertex_count / 10))
            slice_ = dijkstra(dist, directed=False, indices=range(start, stop))
            slices.append(slice_)
            start = stop
            iteration += 1
        matrix = np.vstack(slices)
        # Remove infinites and zeros
        matrix[matrix == np.inf] = self.spread * self.vertex_count ** (0.5)
        matrix[matrix == 0] = self.spread * 1e-6
        return matrix

    def sets(self):
        """Returns sets of vertex pairs indices.
        """
        sets = []
        for n in range(1, self.vertex_count):
            pairs = np.zeros((self.vertex_count - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(self.vertex_count - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(self.vertex_count - n), 2 * n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if s1.any():
                sets.append(s1)
            if s2.any():
                sets.append(s2)
        return sets

    @Slot()
    def get_coordinates(self):
        """Computes and returns x and y coordinates for each vertex in the graph, using VSGD-MS."""
        self._state = _State.RUNNING
        if self.vertex_count <= 1:
            x, y = [0], [0]
            self.emit_finished(x, y)
            self.stop()
            return
        matrix = self.shortest_path_matrix()
        mask = np.ones((self.vertex_count, self.vertex_count)) == 1 - np.tril(
            np.ones((self.vertex_count, self.vertex_count))
        )  # Upper triangular except diagonal
        np.random.seed(0)
        layout = np.random.rand(self.vertex_count, 2) * self.initial_diameter - self.initial_diameter / 2
        heavy_ind_list = list()
        heavy_pos_list = list()
        for ind, pos in self.heavy_positions.items():
            heavy_ind_list.append(ind)
            heavy_pos_list.append([pos["x"], pos["y"]])
        heavy_ind = arr(heavy_ind_list)
        heavy_pos = arr(heavy_pos_list)
        if heavy_ind.any():
            layout[heavy_ind, :] = heavy_pos
        weights = matrix ** self.weight_exp  # bus-pair weights (lower for distant buses)
        maxstep = 1 / np.min(weights[mask])
        minstep = 1 / np.max(weights[mask])
        lambda_ = np.log(minstep / maxstep) / (self.iterations - 1)  # exponential decay of allowed adjustment
        sets = self.sets()  # construct sets of bus pairs
        self.msg.emit("Generating layout...")
        for iteration in range(self.iterations):
            if self._state == _State.STOPPED:
                return
            if self._show_previews:
                x, y = layout[:, 0], layout[:, 1]
                self.emit_finished(x, y)
            self.progressed.emit(iteration)
            step = maxstep * np.exp(lambda_ * iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(
                self.vertex_count
            )  # we don't want to use the same pair order each iteration
            for s in sets:
                v1, v2 = rand_order[s[:, 0]], rand_order[s[:, 1]]  # arrays of vertex1 and vertex2
                # current distance (possibly accounting for system rescaling)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] * (layout[v1] - layout[v2]) / dist[:, None] / 2  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
                if heavy_ind.any():
                    layout[heavy_ind, :] = heavy_pos
        x, y = layout[:, 0], layout[:, 1]
        self.emit_finished(x, y)
        self.stop()
