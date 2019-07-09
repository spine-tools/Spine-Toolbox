######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
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

import dateutil.parser
import numpy as np
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import TimeSeriesVariableResolution
from time_series_model_variable_resolution import TimeSeriesModelVariableResolution
from ui.time_series_variable_resolution_editor import Ui_TimeSeriesVariableResolutionEditor
from widgets.indexed_value_table_context_menu import handle_table_context_menu
from widgets.plot_widget import PlotWidget


def _text_to_datetime(text):
    """Converts a string to a numpy.datetime64 object."""
    return np.datetime64(dateutil.parser.parse(text))


class TimeSeriesVariableResolutionEditor(QWidget):
    """
    A widget for editing variable resolution time series data.

    Attributes:
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        stamps = np.array([np.datetime64("2000-01-01T00:00:00"), np.datetime64("2000-01-01T01:00:00")])
        zeros = np.zeros(len(stamps))
        initial_value = TimeSeriesVariableResolution(stamps, zeros, False, False)
        self._model = TimeSeriesModelVariableResolution(initial_value)
        self._model.dataChanged.connect(self._update_plot)
        self._model.modelReset.connect(self._update_plot)
        self._model.rowsRemoved.connect(self._update_plot)
        self._ui = Ui_TimeSeriesVariableResolutionEditor()
        self._ui.setupUi(self)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._ui.time_series_table.setModel(self._model)
        self._ui.time_series_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.time_series_table.customContextMenuRequested.connect(self._show_table_context_menu)
        self._ui.ignore_year_check_box.toggled.connect(self._change_ignore_year)
        self._ui.ignore_year_check_box.setChecked(self._model.value.ignore_year)
        self._ui.repeat_check_box.toggled.connect(self._change_repeat)
        self._ui.repeat_check_box.setChecked(self._model.value.repeat)
        self._update_plot()

    @Slot(bool, name="_change_ignore_year")
    def _change_ignore_year(self, ignore_year):
        """Updates the attributes model."""
        self._model.ignore_year = ignore_year

    @Slot(bool, name="_change_repeat")
    def _change_repeat(self, repeat):
        """Updates the attributes model."""
        self._model.repeat = repeat

    def _reset_attributes_model(self, ignore_year, repeat):
        """Resets the attributes model."""
        self._attributes_model.ignore_year = ignore_year
        self._attributes_model.repeat = repeat
        self._ui.ignore_year_check_box.setChecked(ignore_year)
        self._ui.repeat_check_box.setChecked(repeat)

    @Slot("QPoint", name="_show_table_context_menu")
    def _show_table_context_menu(self, pos):
        handle_table_context_menu(pos, self._ui.time_series_table, self._model, self)

    def set_value(self, value):
        """Sets the time series being edited."""
        self._model.reset(value)
        self._ui.ignore_year_check_box.setChecked(value.ignore_year)
        self._ui.repeat_check_box.setChecked(value.repeat)

    @Slot("QModelIndex", "QModelIndex", "list", name="_update_plot")
    def _update_plot(self, topLeft=None, bottomRight=None, roles=None):
        """Updates the plot widget."""
        stamps = self._model.value.indexes
        values = self._model.value.values
        self._plot_widget.canvas.axes.cla()
        self._plot_widget.canvas.axes.step(stamps, values, where='post')
        self._plot_widget.canvas.draw()

    def value(self):
        """Return the time series currently being edited."""
        return self._model.value
