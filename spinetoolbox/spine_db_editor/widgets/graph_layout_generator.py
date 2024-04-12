######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains the GraphLayoutGeneratorRunnable class."""
from PySide6.QtCore import Signal, Slot, QObject, QRunnable
from spinedb_api.graph_layout_generator import GraphLayoutGenerator


class GraphLayoutGeneratorRunnable(QRunnable):
    """Computes the layout for the Entity Graph View."""

    class Signals(QObject):
        finished = Signal(object)
        layout_available = Signal(object, object, object)
        progressed = Signal(int)

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

    def _layout_available(self, x, y):
        self.layout_available.emit(self._id, x, y)

    def _preview_available(self, x, y):
        if self._show_previews:
            self.layout_available.emit(self._id, x, y)

    def run(self):
        self._generator.compute_layout()
        self.finished.emit(self._id)
