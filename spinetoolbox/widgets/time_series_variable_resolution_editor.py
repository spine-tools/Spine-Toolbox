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
Contains logic for the time series editor widget.

:author: A. Soininen (VTT)
:date:   31.5.2019
"""

import dateutil.parser
import numpy as np
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import TimeSeriesVariableResolution
from indexed_value_table_model import IndexedValueTableModel
from ui.time_series_variable_resolution_editor import Ui_TimeSeriesVariableResolutionEditor
from widgets.plot_widget import PlotWidget
from widgets.time_series_fixed_resolution_editor import TimeSeriesAttributesModel


def _resize_series(indexes, values, length):
    old_length = len(indexes)
    if old_length == length:
        return
    if old_length > length:
        return indexes[:length], values[:length]
    step = indexes[-1] - indexes[-2]
    new_indexes = np.empty(length, dtype=indexes.dtype)
    new_indexes[:old_length] = indexes
    for i in range(old_length, length):
        new_indexes[i] = indexes[-1] + (i - old_length + 1) * step
    new_values = np.zeros(length)
    new_values[:old_length] = values
    return new_indexes, new_values


def _text_to_datetime(text):
    return np.datetime64(dateutil.parser.parse(text))


class TimeSeriesVariableResolutionEditor(QWidget):
    """
    A widget for editing time series data.

    Attributes:
        model (MinimalTableModel): the model cell of which is being edited
        index (QModelIndex): an index to model
        value (ParameterValue): parameter value at index
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        stamps = np.array([np.datetime64("2000-01-01T00:00:00"), np.datetime64("2000-01-02T00:00:00")])
        zeros = np.zeros(len(stamps))
        initial_value = TimeSeriesVariableResolution(stamps, zeros, False, False)
        self._table_model = IndexedValueTableModel(
            initial_value.indexes, initial_value.values, _text_to_datetime, float
        )
        self._table_model.set_index_header("Time stamps")
        self._table_model.set_value_header("Values")
        self._table_model.dataChanged.connect(self._table_model_data_changed)
        self._attributes_model = TimeSeriesAttributesModel(initial_value.ignore_year, initial_value.repeat)
        self._ui = Ui_TimeSeriesVariableResolutionEditor()
        self._ui.setupUi(self)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._ui.time_series_table.setModel(self._table_model)
        self._ui.length_edit.setValue(len(initial_value))
        self._ui.length_edit.editingFinished.connect(self._change_length)
        self._ui.ignore_year_check_box.setChecked(self._attributes_model.ignore_year)
        self._ui.repeat_check_box.setChecked(self._attributes_model.repeat)
        self._ui.ignore_year_check_box.toggled.connect(self._change_ignore_year)
        self._ui.repeat_check_box.toggled.connect(self._change_repeat)
        self._update_plot()

    @Slot(bool, name="_change_ignore_year")
    def _change_ignore_year(self, ignore_year):
        self._attributes_model.ignore_year = ignore_year

    @Slot(name='_change_length')
    def _change_length(self):
        length = self._ui.length_edit.value()
        indexes = self._table_model.indexes
        values = self._table_model.values
        resized_indexes, resized_values = _resize_series(indexes, values, length)
        value = TimeSeriesVariableResolution(
            resized_indexes, resized_values, self._attributes_model.ignore_year, self._attributes_model.repeat
        )
        self._silent_reset_model(value)
        self._update_plot()

    @Slot(bool, name="_change_repeat")
    def _change_repeat(self, repeat):
        self._attributes_model.repeat = repeat

    def _reset_attributes_model(self, ignore_year, repeat):
        self._attributes_model.ignore_year = ignore_year
        self._attributes_model.repeat = repeat
        self._ui.ignore_year_check_box.setChecked(ignore_year)
        self._ui.repeat_check_box.setChecked(repeat)

    def set_value(self, value):
        self._silent_reset_model(value)
        self._ui.length_edit.setValue(len(value))
        self._reset_attributes_model(value.ignore_year, value.repeat)
        self._update_plot()

    def _silent_reset_model(self, value):
        self._table_model.dataChanged.disconnect(self._table_model_data_changed)
        self._table_model.reset(value.indexes, value.values)
        self._table_model.dataChanged.connect(self._table_model_data_changed)

    @Slot("QModelIndex", "QModelIndex", "list", name="_table_model_data_changed")
    def _table_model_data_changed(self, topLeft, bottomRight, roles=None):
        """A slot to signal that the table view has changed."""
        self._update_plot()

    def _update_plot(self):
        stamps = self._table_model.indexes
        values = self._table_model.values
        self._plot_widget.canvas.axes.cla()
        self._plot_widget.canvas.axes.plot(stamps, values)
        self._plot_widget.canvas.draw()

    def value(self):
        stamps = self._table_model.indexes
        values = self._table_model.values
        return TimeSeriesVariableResolution(
            stamps, values, self._attributes_model.ignore_year, self._attributes_model.repeat
        )
