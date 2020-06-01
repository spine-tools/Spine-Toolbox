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
Contains custom QHeaderView for the pivot table.

:author: M. Marin (KTH)
:date:   2.12.2019
"""

from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QHeaderView, QMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, _prepare_plot_in_window_menu
from ...plotting import plot_pivot_column, PlottingError, PivotTablePlottingHints
from ...config import PIVOT_TABLE_HEADER_COLOR


class PivotTableHeaderView(QHeaderView):

    header_dropped = Signal(object, object)

    def __init__(self, orientation, area, pivot_table_view):
        super().__init__(orientation, parent=pivot_table_view)
        self._area = area
        self._proxy_model = pivot_table_view.model()
        self._model_index = None
        self._menu = QMenu(self)
        self._plot_action = self._menu.addAction("Plot single column", self._plot_column)
        self._add_to_plot_menu = self._menu.addMenu("Plot in window")
        self._add_to_plot_menu.triggered.connect(self._add_column_to_plot)
        self._set_as_x_action = self._menu.addAction("Use as X", self._set_x_flag)
        self._set_as_x_action.setCheckable(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("QHeaderView::section {background-color: " + PIVOT_TABLE_HEADER_COLOR + ";}")

    @property
    def area(self):
        return self._area

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        self.header_dropped.emit(event.source(), self)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        self._menu.move(event.globalPos())
        self._model_index = self.parent().indexAt(event.pos())
        source_index = self._proxy_model.mapToSource(self._model_index)
        if self._proxy_model.sourceModel().column_is_index_column(self._model_index.column()):
            self._plot_action.setEnabled(False)
            self._set_as_x_action.setEnabled(True)
            self._set_as_x_action.setChecked(source_index.column() == self._proxy_model.sourceModel().plot_x_column)
        elif self._model_index.column() < self._proxy_model.sourceModel().headerColumnCount():
            self._plot_action.setEnabled(False)
            self._set_as_x_action.setEnabled(False)
            self._set_as_x_action.setChecked(False)
        else:
            self._plot_action.setEnabled(True)
            self._set_as_x_action.setEnabled(True)
            self._set_as_x_action.setChecked(source_index.column() == self._proxy_model.sourceModel().plot_x_column)
        _prepare_plot_in_window_menu(self._add_to_plot_menu)
        self._menu.show()

    @Slot("QAction")
    def _add_column_to_plot(self, action):
        """Adds a single column to existing plot window."""
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self._plot_column()
            return
        try:
            support = PivotTablePlottingHints()
            plot_pivot_column(self._proxy_model, self._model_index.column(), support, plot_window)
        except PlottingError as error:
            report_plotting_failure(error, self)

    @Slot()
    def _plot_column(self):
        """Plots a single column not the selection."""
        try:
            support = PivotTablePlottingHints()
            plot_window = plot_pivot_column(self._proxy_model, self._model_index.column(), support)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plot_window.use_as_window(
            self.parentWidget(), support.column_label(self._proxy_model, self._model_index.column())
        )
        plot_window.show()

    @Slot()
    def _set_x_flag(self):
        """Sets the X flag for a column."""
        index = self._proxy_model.mapToSource(self._model_index)
        self._proxy_model.sourceModel().set_plot_x_column(index.column(), self._set_as_x_action.isChecked())
