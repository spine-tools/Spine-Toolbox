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

"""A Qt widget to use as a matplotlib backend."""
from enum import auto, Enum, unique
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6 import QtWidgets


@unique
class LegendPosition(Enum):
    BOTTOM = auto()
    RIGHT = auto()


class PlotCanvas(FigureCanvasQTAgg):
    """A widget for plotting with matplotlib."""

    def __init__(self, parent=None, legend_axes_position=LegendPosition.BOTTOM):
        """
        Args:
            legend_axes_position (LegendPosition): legend axes position relative to plot axes
            parent (QWidget, optional): a parent widget
        """
        width = 7.0 + (0.0 if legend_axes_position == LegendPosition.BOTTOM else 6.0)  # inches
        height = 5.0  # inches
        fig = Figure(figsize=(width, height), tight_layout=True)
        if legend_axes_position == LegendPosition.BOTTOM:
            grid_spec = fig.add_gridspec(2, 1, height_ratios=[1, 0])
            self._axes = fig.add_subplot(grid_spec[0, 0])
            self._legend_axes = fig.add_subplot(grid_spec[1, 0])
        elif legend_axes_position == LegendPosition.RIGHT:
            grid_spec = fig.add_gridspec(1, 2, width_ratios=[1, 0])
            self._axes = fig.add_subplot(grid_spec[0, 0])
            self._legend_axes = fig.add_subplot(grid_spec[0, 1])
        else:
            raise RuntimeError(f"unknown legend position {legend_axes_position}")
        self._legend_axes.axis("off")
        super().__init__(fig)
        self.setParent(parent)
        super().setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        super().updateGeometry()

    @property
    def axes(self):
        """:obj:`matplotlib.axes.Axes`: figure's axes"""
        return self._axes

    @property
    def legend_axes(self):
        """:obj:`matplotlib.axes.Axes`: figure's legend axes"""
        return self._legend_axes

    def has_twinned_axes(self):
        """Checks whether the axes have been twinned.

        Returns:
            bool: True if axes have been twinned, False otherwise
        """
        siblings = self._axes.get_shared_x_axes().get_siblings(self._axes)
        if len(siblings) > 1:
            return any(ax.bbox.bounds == self._axes.bbox.bounds for ax in siblings if ax is not self._axes)
        return False

    def twinned_axes(self):
        """Returns twinned axes.

        Returns:
            list of Axes: twinned axes
        """
        siblings = self._axes.get_shared_x_axes().get_siblings(self._axes)
        return [ax for ax in siblings if ax is not self._axes and ax.bbox.bounds == self._axes.bbox.bounds]
