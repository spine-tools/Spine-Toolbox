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
A Qt widget showing a toolbar and a matplotlib plotting canvas.

:author: A. Soininen (VTT)
:date:   27.6.2019
"""

import itertools
import io
import csv

import numpy
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
from PySide2.QtCore import QMetaObject, Qt
from PySide2.QtWidgets import QVBoxLayout, QWidget, QMenu, QApplication
from .plot_canvas import PlotCanvas, LegendPosition
from .custom_qtableview import CopyPasteTableView
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..helpers import busy_effect


class PlotWidget(QWidget):
    """
    A widget that contains a toolbar and a plotting canvas.

    Attributes:
        canvas (PlotCanvas): the plotting canvas
        original_xy_data (list of XYData): unmodified data on which the plots are based
    """

    plot_windows = dict()
    """A global list of plot windows."""

    def __init__(self, parent=None, legend_axes_position=LegendPosition.BOTTOM):
        """
        Args:
            parent (QWidget, optional): parent widget
            legend_axes_position (LegendPosition): legend axes position relative to plot axes
        """
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self.canvas = PlotCanvas(self, legend_axes_position)
        self._toolbar = NavigationToolBar(self.canvas, self)
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self.canvas)
        self.original_xy_data = list()
        QMetaObject.connectSlotsByName(self)

    def closeEvent(self, event):
        """Removes the window from plot_windows and closes."""
        closed = set(name for name, widget in PlotWidget.plot_windows.items() if widget is self)
        for name in closed:
            del PlotWidget.plot_windows[name]
        super().closeEvent(event)

    def contextMenuEvent(self, event):
        """Shows plot context menu."""
        menu = QMenu(self)
        menu.addAction("Show plot data...", self.show_plot_data)
        menu.addAction("Copy plot data", self.copy_plot_data)
        menu.exec_(event.globalPos())

    def _get_plot_data(self):
        """Gathers plot data into a table.

        Returns:
            list of list: data as table
        """
        header = ["indexes"]
        indexes = []
        data_dicts = []
        for xy_data in self.original_xy_data:
            label = " | ".join(xy_data.data_index)
            header.append(label)
            indexes.append(xy_data.x)
            data_dict = dict(zip(xy_data.x, xy_data.y))
            data_dicts.append(data_dict)
        all_indexes = numpy.unique(numpy.concatenate(indexes))
        rows = [header]
        for index in all_indexes:
            row = [str(index)] + [str(data_dict.get(index, "")) for data_dict in data_dicts]
            rows.append(row)
        return rows

    @busy_effect
    def copy_plot_data(self):
        """Copies plot data to clipboard."""
        rows = self._get_plot_data()
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter="\t", quotechar="'")
            for row in rows:
                writer.writerow(row)
            QApplication.clipboard().setText(output.getvalue())

    @busy_effect
    def show_plot_data(self):
        """Opens a separate window that shows the plot data."""
        rows = self._get_plot_data()
        widget = _PlotDataWidget(rows, self)
        widget.setWindowFlag(Qt.Window, True)
        title = "Plot data"
        widget.setWindowTitle(title)
        widget.show()

    def add_legend(self, handles):
        """Adds a legend to the plot's legend axes.

        Args:
            handles (list): legend handles
        """
        self.canvas.legend_axes.legend(handles=handles, loc="upper center")

    def use_as_window(self, parent_window, document_name):
        """
        Prepares the widget to be used as a window and adds it to plot_windows list.

        Args:
            parent_window (QWidget): a parent window
            document_name (str): a string to add to the window title
        """
        self.setParent(parent_window)
        self.setWindowFlag(Qt.Window, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        title = "Plot"
        if document_name:
            title += f"    -- {document_name} --"
        self.setWindowTitle(title)
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


class _PlotDataView(CopyPasteTableView):
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Select all", self.selectAll)
        menu.addAction("Copy", self.copy).setEnabled(self.can_copy())
        menu.exec_(event.globalPos())


class _PlotDataWidget(QWidget):
    def __init__(self, rows, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Plot data")
        layout = QVBoxLayout(self)
        self._view = _PlotDataView(self)
        self._model = MinimalTableModel(self)
        self._view.setModel(self._model)
        self._model.reset_model(rows)
        self._view.resizeColumnsToContents()
        self._view.horizontalHeader().hide()
        self._view.verticalHeader().hide()
        layout.addWidget(self._view)
        self.setAttribute(Qt.WA_DeleteOnClose)


def prepare_plot_in_window_menu(menu):
    """Fills a given menu with available plot window names.

    Args:
        menu (QMenu): menu to modify
    """
    menu.clear()
    plot_windows = PlotWidget.plot_windows
    if not plot_windows:
        menu.setEnabled(False)
        return
    menu.setEnabled(True)
    window_names = list(plot_windows.keys())
    for name in sorted(window_names):
        menu.addAction(name)
