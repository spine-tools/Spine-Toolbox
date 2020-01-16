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
Contains logic for the variable resolution time series editor widget.

:author: A. Soininen (VTT)
:date:   31.5.2019
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import TimeSeriesVariableResolution
from ..plotting import add_time_series_plot
from ..mvcmodels.time_series_model_variable_resolution import TimeSeriesModelVariableResolution
from .custom_qtableview import IndexedValueTableView
from .indexed_value_table_context_menu import handle_table_context_menu
from .plot_widget import PlotWidget


class TimeSeriesVariableResolutionEditor(QWidget):
    """
    A widget for editing variable resolution time series data.

    Attributes:
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        from ..ui.time_series_variable_resolution_editor import Ui_TimeSeriesVariableResolutionEditor

        super().__init__(parent)
        stamps = ["2000-01-01T00:00:00", "2000-01-01T01:00:00"]
        zeros = len(stamps) * [0.0]
        initial_value = TimeSeriesVariableResolution(stamps, zeros, False, False)
        self._model = TimeSeriesModelVariableResolution(initial_value)
        self._model.dataChanged.connect(self._update_plot)
        self._model.modelReset.connect(self._update_plot)
        self._model.rowsInserted.connect(self._update_plot)
        self._model.rowsRemoved.connect(self._update_plot)
        self._ui = Ui_TimeSeriesVariableResolutionEditor()
        self._ui.setupUi(self)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._time_series_table = IndexedValueTableView(self._ui.splitter)
        self._ui.left_layout.addWidget(self._time_series_table)
        self._time_series_table.setModel(self._model)
        self._time_series_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._time_series_table.customContextMenuRequested.connect(self._show_table_context_menu)
        self._ui.ignore_year_check_box.setChecked(self._model.value.ignore_year)
        self._ui.ignore_year_check_box.toggled.connect(self._model.set_ignore_year)
        self._ui.repeat_check_box.setChecked(self._model.value.repeat)
        self._ui.repeat_check_box.toggled.connect(self._model.set_repeat)
        self._update_plot()

    @Slot("QPoint", name="_show_table_context_menu")
    def _show_table_context_menu(self, pos):
        """Shows the table's context menu."""
        handle_table_context_menu(pos, self._time_series_table, self._model, self)

    def set_value(self, value):
        """Sets the time series being edited."""
        self._model.reset(value)
        self._ui.ignore_year_check_box.setChecked(value.ignore_year)
        self._ui.repeat_check_box.setChecked(value.repeat)

    @Slot("QModelIndex", "QModelIndex", "list", name="_update_plot")
    def _update_plot(self, topLeft=None, bottomRight=None, roles=None):
        """Updates the plot widget."""
        self._plot_widget.canvas.axes.cla()
        add_time_series_plot(self._plot_widget, self._model)
        self._plot_widget.canvas.draw()

    def value(self):
        """Return the time series currently being edited."""
        return self._model.value
