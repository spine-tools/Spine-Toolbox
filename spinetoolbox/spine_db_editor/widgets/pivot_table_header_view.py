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

"""Contains custom QHeaderView for the pivot table."""
from PySide6.QtCore import Signal, Slot, Qt, QPoint
from PySide6.QtWidgets import QHeaderView, QMenu, QWidget
from PySide6.QtGui import QAction
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, prepare_plot_in_window_menu
from ...plotting import PlottingError, plot_pivot_table_selection
from ..mvcmodels.colors import PIVOT_TABLE_HEADER_COLOR


class PivotTableHeaderView(QHeaderView):
    """Header view for the pivot table."""

    header_dropped = Signal(QWidget, QWidget)

    def __init__(self, orientation, area, pivot_table_view):
        """
        Args:
            orientation (Qt.Orientation): Qt.Orientation.Horizontal or Qt.Orientation.Vertical
            area (str): which pivot area the header represents: "columns", "rows" or "frozen"
            pivot_table_view (PivotTableView): parent view
        """
        super().__init__(orientation, parent=pivot_table_view)
        self._area = area
        self.setAcceptDrops(True)
        self.setStyleSheet(f"QHeaderView::section {{background-color: {PIVOT_TABLE_HEADER_COLOR.name()};}}")
        self.setSectionsClickable(True)
        self.setVisible(True)

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


class ParameterValuePivotHeaderView(PivotTableHeaderView):
    """Header view for the pivot table in parameter value and index expansion mode."""

    def __init__(self, orientation, area, pivot_table_view):
        """
        Args:
            orientation (Qt.Orientation): Qt.Orientation.Horizontal or Qt.Orientation.Vertical
            area (str): which pivot area the header represents: "columns", "rows" or "frozen"
            pivot_table_view (PivotTableView): parent view
        """
        super().__init__(orientation, area, pivot_table_view)
        self._proxy_model = pivot_table_view.model()
        self._model_index = None
        self.setContextMenuPolicy(
            Qt.DefaultContextMenu if orientation == Qt.Orientation.Horizontal else Qt.NoContextMenu
        )
        self._menu = QMenu(self)
        self._plot_action = self._menu.addAction("Plot single column", self._plot_column)
        self._add_to_plot_menu = self._menu.addMenu("Plot in window")
        self._add_to_plot_menu.triggered.connect(self._add_column_to_plot)
        self._set_as_x_action = self._menu.addAction("Use as X", self._set_x_flag)
        self._set_as_x_action.setCheckable(True)

    def _column_selection(self):
        """Lists current column's indexes that contain some data.

        Returns:
            list of QModelIndex: column indexes
        """
        column = self._model_index.column()
        first_data_row = self._proxy_model.sourceModel().headerRowCount()
        data_rows_end = self._proxy_model.rowCount()
        return [self._proxy_model.index(row, column) for row in range(first_data_row, data_rows_end)]

    @Slot(QAction)
    def _add_column_to_plot(self, action):
        """Adds a single column to existing plot window."""
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self._plot_column()
            return
        column = self._model_index.column()
        selection = self._column_indexes(column)
        try:
            plot_pivot_table_selection(self._proxy_model, selection, plot_window)
        except PlottingError as error:
            report_plotting_failure(error, self)

    @Slot()
    def _plot_column(self):
        """Plots a single column not the selection."""
        column = self._model_index.column()
        selection = self._column_indexes(column)
        try:
            plot_window = plot_pivot_table_selection(self._proxy_model, selection)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        column_label = self._proxy_model.sourceModel().column_name(column)
        plot_window.use_as_window(self.parentWidget(), column_label)
        plot_window.show()

    def _column_indexes(self, column):
        """Makes indexes for given column.

        Args:
            column (int): column

        Returns:
            list of QModelIndex: column indexes
        """
        first_data_row = self._proxy_model.sourceModel().headerRowCount()
        data_rows_end = self._proxy_model.sourceModel().rowCount()
        return [self._proxy_model.index(row, column) for row in range(first_data_row, data_rows_end)]

    @Slot()
    def _set_x_flag(self):
        """Sets the X flag for a column."""
        index = self._proxy_model.mapToSource(self._model_index)
        self._proxy_model.sourceModel().set_plot_x_column(index.column(), self._set_as_x_action.isChecked())

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
        prepare_plot_in_window_menu(self._add_to_plot_menu)
        self._menu.show()


class ScenarioAlternativePivotHeaderView(PivotTableHeaderView):
    """Header view for the pivot table in parameter value and index expansion mode."""

    context_menu_requested = Signal(QPoint)
    """Requests a header context menu be shown at given global position."""

    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(event.globalPos())
