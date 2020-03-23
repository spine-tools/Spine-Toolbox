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

import enum
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtCore import Signal, Slot, QObject, QThread, Qt
from PySide2.QtWidgets import QProgressBar, QDialogButtonBox, QLabel, QWidget, QVBoxLayout


class _State(enum.Enum):
    """State of GraphLayoutGenerator."""

    ACTIVE = enum.auto()
    STOPPED = enum.auto()
    RUSHED_OUT = enum.auto()


class GraphLayoutGenerator(QObject):
    """Computes the layout for the Entity Graph View."""

    finished = Signal(object, object)
    started = Signal()
    progressed = Signal(int)
    done = Signal()

    def __init__(
        self,
        vertex_count,
        src_inds,
        dst_inds,
        spread,
        heavy_positions=None,
        iterations=10,
        weight_exp=-2,
        initial_diameter=1000,
    ):
        super().__init__()
        if heavy_positions is None:
            heavy_positions = dict()
        self.vertex_count = vertex_count
        self.src_inds = src_inds
        self.dst_inds = dst_inds
        self.spread = spread
        self.heavy_positions = heavy_positions
        self.iterations = iterations
        self.weight_exp = weight_exp
        self.initial_diameter = initial_diameter
        self._state = _State.ACTIVE
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.start()
        qApp.aboutToQuit.connect(self._thread.quit)  # pylint: disable=undefined-variable
        self.started.connect(self.get_coordinates)
        self.finished.connect(self.clean_up)

    def create_progress_widget(self):
        widget = QWidget()
        widget.setAttribute(Qt.WA_NoSystemBackground)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout(widget)
        label = QLabel("Generating layout...")
        progress_bar = QProgressBar()
        progress_bar.setRange(0, self.iterations - 1)
        progress_bar.setTextVisible(False)
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        button = button_box.addButton("Can't wait", QDialogButtonBox.NoRole)
        button.clicked.connect(lambda checked=False: self.rush_out())
        self.progressed.connect(progress_bar.setValue)
        layout.addWidget(label)
        layout.addWidget(progress_bar)
        layout.addWidget(button_box)
        return widget

    def clean_up(self):
        self._thread.quit()
        self.done.emit()

    def stop(self):
        self._state = _State.STOPPED

    def rush_out(self, checked=False):
        self._state = _State.RUSHED_OUT

    def start(self):
        self.started.emit()

    def shortest_path_matrix(self):
        """Returns the shortest-path matrix.
        """
        dist = np.zeros((self.vertex_count, self.vertex_count))
        src_inds = arr(self.src_inds)
        dst_inds = arr(self.dst_inds)
        try:
            dist[src_inds, dst_inds] = dist[dst_inds, src_inds] = self.spread
        except IndexError:
            pass
        matrix = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        matrix[matrix == np.inf] = self.spread * 3
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

    def emit_finished(self, x, y):
        if self._state == _State.STOPPED:
            self.clean_up()
            return
        self.finished.emit(x, y)

    @Slot()
    def get_coordinates(self):
        """Computes and returns x and y coordinates for each vertex in the graph, using VSGD-MS."""
        if self.vertex_count <= 1:
            layout = np.zeros((self.vertex_count, 2))
            x, y = [0], [0]
            self.emit_finished(x, y)
            return x, y
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
        for iteration in range(self.iterations):
            self.progressed.emit(iteration)
            step = maxstep * np.exp(lambda_ * iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(
                self.vertex_count
            )  # we don't want to use the same pair order each iteration
            for s in sets:
                if self._state in (_State.STOPPED, _State.RUSHED_OUT):
                    break
                v1, v2 = rand_order[s[:, 0]], rand_order[s[:, 1]]  # arrays of vertex1 and vertex2
                # current distance (possibly accounting for system rescaling)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] / 2 * (layout[v1] - layout[v2]) / dist[:, None]  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
                if heavy_ind.any():
                    layout[heavy_ind, :] = heavy_pos
            else:  # nobreak
                continue
            break
        x, y = layout[:, 0], layout[:, 1]
        self.emit_finished(x, y)
        return x, y
