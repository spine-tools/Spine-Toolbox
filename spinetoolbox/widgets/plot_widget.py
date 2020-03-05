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
A Qt widget showing a toolbar and a matplotlib plotting canvas.

:author: A. Soininen (VTT)
:date:   27.6.2019
"""

import itertools
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
from PySide2.QtCore import QMetaObject, Qt
from PySide2.QtWidgets import QVBoxLayout, QWidget
from spinedb_api import IndexedValue, Map, TimeSeries
from .plot_canvas import PlotCanvas


class PlotWidget(QWidget):
    """
    A widget that contains a toolbar and a plotting canvas.

    Attributes:
        canvas (PlotCanvas): the plotting canvas
        plot_type (type): type of currently plotted data or None
    """

    plot_windows = dict()
    """A global list of plot windows."""

    def __init__(self):
        super().__init__()
        self.plot_type = None
        self._layout = QVBoxLayout(self)
        self.canvas = PlotCanvas(self)
        self._toolbar = NavigationToolBar(self.canvas, self)
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self.canvas)
        QMetaObject.connectSlotsByName(self)

    def closeEvent(self, event):
        """Removes the window from plot_windows and closes."""
        for name, widget in PlotWidget.plot_windows.items():
            if self is widget:
                del PlotWidget.plot_windows[name]
                break
        super().closeEvent(event)

    def infer_plot_type(self, values):
        """Decides suitable plot_type according to a list of values."""
        first_value = values[0]
        if isinstance(first_value, TimeSeries):
            self.plot_type = TimeSeries
        elif isinstance(first_value, Map):
            self.plot_type = Map
        elif isinstance(first_value, IndexedValue):
            self.plot_type = type(first_value)
        else:
            # It is some scalar type
            self.plot_type = type(values[1][0])

    def use_as_window(self, parent_window, document_name):
        """
        Prepares the widget to be used as a window and adds it to plot_windows list.

        Args:
            parent_window (QWidget): a parent window
            document_name (str): a string to add to the window title
        """
        self.setParent(parent_window)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowTitle(f"Plot    -- {document_name} --")
        PlotWidget.plot_windows[self._unique_window_name(document_name)] = self

    @staticmethod
    def _unique_window_name(document_name):
        """Returns an unique identifier for a new plot window."""
        if document_name not in PlotWidget.plot_windows:
            return document_name
        for i in itertools.count(0):
            proposition = f"{document_name} ({i + 1})"
            if proposition not in PlotWidget.plot_windows:
                return proposition
