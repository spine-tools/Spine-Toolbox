######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the GraphLayoutGeneratorRunnable class.
"""

import numpy as np
from PySide6.QtCore import Signal, Slot, QObject, Qt, QRunnable
from PySide6.QtWidgets import QProgressBar, QDialogButtonBox, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPainter, QColor
from spinedb_api.graph_layout_generator import GraphLayoutGenerator
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
        import scipy.interpolate  # pylint: disable=import-outside-toplevel

        points = np.column_stack((x, y))
        heat_map = scipy.interpolate.griddata(points, values, (xv, yv), method="cubic")
    except ImportError:
        import matplotlib.tri as tri  # pylint: disable=import-outside-toplevel

        triang = tri.Triangulation(x, y)
        interpolator = tri.CubicTriInterpolator(triang, values)
        heat_map = interpolator(xv, yv)
    return heat_map, xv, yv, min_x, min_y, max_x, max_y


class ProgressBarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        inner_widget = QWidget(self)
        layout = QHBoxLayout(self)
        layout.addStretch()
        layout.addWidget(inner_widget)
        layout.addStretch()
        self._label = QLabel()
        self._label.setStyleSheet("QLabel{color:white; font-weight: bold; font-size:18px;}")
        self._label.setAlignment(Qt.AlignHCenter)
        self._progress_bar = QProgressBar()
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        self._previews_button = button_box.addButton("Show previews", QDialogButtonBox.ButtonRole.NoRole)
        self._previews_button.setCheckable(True)
        self._previews_button.toggled.connect(
            lambda checked: self._previews_button.setText(f"{'Hide' if checked else 'Show'} previews")
        )
        self.stop_button = button_box.addButton("Stop", QDialogButtonBox.ButtonRole.NoRole)
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.addStretch()
        inner_layout.addWidget(self._label)
        inner_layout.addWidget(self._progress_bar)
        inner_layout.addWidget(button_box)
        inner_layout.addStretch()
        self._layout_gen = None

    def set_layout_generator(self, layout_generator):
        if self._layout_gen is not None:
            self._layout_gen.finished.disconnect(self.hide)
            self._layout_gen.progressed.disconnect(self._progress_bar.setValue)
            self._layout_gen.msg.disconnect(self._progress_bar.setFormat)
            self._previews_button.toggled.disconnect(self._layout_gen.set_show_previews)
            self.stop_button.clicked.disconnect(self._layout_gen.stop)
        self._layout_gen = layout_generator
        self._label.setText(f"Processing {self._layout_gen.vertex_count} elements")
        self._progress_bar.setRange(0, self._layout_gen.max_iters - 1)
        self._previews_button.toggled.connect(self._layout_gen.set_show_previews)
        self.stop_button.clicked.connect(self._layout_gen.stop)
        self._layout_gen.finished.connect(self.hide)
        self._layout_gen.progressed.connect(self._progress_bar.setValue)
        self._layout_gen.progressed.connect(self.show)
        self._layout_gen.msg.connect(self._progress_bar.setFormat)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 96))
        painter.end()
        super().paintEvent(event)


class GraphLayoutGeneratorRunnable(QRunnable):
    """Computes the layout for the Entity Graph View."""

    class Signals(QObject):
        finished = Signal(object)
        layout_available = Signal(object, object, object)
        progressed = Signal(int)
        msg = Signal(str)

    def __init__(
        self,
        identifier,
        vertex_count,
        src_inds=(),
        dst_inds=(),
        spread=0,
        heavy_positions=None,
        max_iters=12,
        weight_exp=-2,
    ):
        super().__init__()
        self._generator = GraphLayoutGenerator(
            vertex_count,
            src_inds=src_inds,
            dst_inds=dst_inds,
            spread=spread,
            heavy_positions=heavy_positions,
            max_iters=max_iters,
            weight_exp=weight_exp,
            is_stopped=self._is_stopped,
            preview_available=self._preview_available,
            layout_available=self._layout_available,
            layout_progressed=self._layout_progressed,
            message_available=self._message_available,
        )
        self.vertex_count = vertex_count
        self.max_iters = max_iters
        self._id = identifier
        self._signals = self.Signals()
        self._stopped = False
        self._show_previews = False
        self.finished = self._signals.finished
        self.layout_available = self._signals.layout_available
        self.progressed = self._signals.progressed
        self.msg = self._signals.msg

    @Slot(bool)
    def stop(self, _checked=False):
        self._stopped = True

    @Slot(bool)
    def set_show_previews(self, checked):
        self._show_previews = checked

    def _is_stopped(self):
        return self._stopped

    def _layout_progressed(self, iteration):
        self.progressed.emit(iteration)

    def _message_available(self, text):
        self.msg.emit(text)

    def _layout_available(self, x, y):
        self.layout_available.emit(self._id, x, y)

    def _preview_available(self, x, y):
        if self._show_previews:
            self.layout_available.emit(self._id, x, y)

    def run(self):
        self._generator.compute_layout()
        self.finished.emit(self._id)
