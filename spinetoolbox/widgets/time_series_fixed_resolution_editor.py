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
Contains logic for the fixed step time series editor widget.

:author: A. Soininen (VTT)
:date:   14.6.2019
"""

import dateutil.parser
import numpy as np
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import (
    duration_to_relativedelta,
    ParameterValueFormatError,
    relativedelta_to_duration,
    TimeSeriesFixedResolution,
)
from indexed_value_table_model import IndexedValueTableModel
from ui.time_series_fixed_resolution_editor import Ui_TimeSeriesFixedResolutionEditor
from widgets.plot_widget import PlotWidget


def _resize_value_array(values, length):
    if len(values) == length:
        return values
    if len(values) > length:
        return values[:length]
    zero_padded = np.zeros(length)
    zero_padded[0 : len(values)] = values
    return zero_padded


def _resolution_to_text(resolution):
    if len(resolution) == 1:
        return relativedelta_to_duration(resolution[0])
    affix = ''
    text = ''
    for r in resolution:
        text = text + affix + relativedelta_to_duration(r)
        affix = ', '
    return text


class _FixedResolutionModel:
    def __init__(self, start, resolution):
        self._start = start
        self._resolution = resolution

    @property
    def start(self):
        return self._start

    @property
    def resolution(self):
        return self._resolution

    @start.setter
    def start(self, start):
        self._start = dateutil.parser.parse(start)

    @resolution.setter
    def resolution(self, resolution):
        tokens = resolution.split(',')
        self._resolution = list()
        for token in tokens:
            self._resolution.append(duration_to_relativedelta(token.strip()))


class TimeSeriesAttributesModel:
    def __init__(self, ignore_year, repeat):
        self._ignore_year = ignore_year
        self._repeat = repeat

    @property
    def ignore_year(self):
        return self._ignore_year

    @ignore_year.setter
    def ignore_year(self, ignore_year):
        self._ignore_year = ignore_year

    @property
    def repeat(self):
        return self._repeat

    @repeat.setter
    def repeat(self, repeat):
        self._repeat = repeat


class TimeSeriesFixedResolutionEditor(QWidget):
    """
    A widget for editing time series data with a fixed time step.

    Attributes:
        model (MinimalTableModel): the model cell of which is being edited
        index (QModelIndex): an index to model
        value (ParameterValue): parameter value at index
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_model = None
        self._resolution_model = None
        self._ui = Ui_TimeSeriesFixedResolutionEditor()
        self._ui.setupUi(self)
        self._ui.start_time_edit.editingFinished.connect(self._start_time_changed)
        self._ui.length_edit.editingFinished.connect(self._change_length)
        self._ui.resolution_edit.editingFinished.connect(self._resolution_changed)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._attributes_model = TimeSeriesAttributesModel(True, True)
        self._ui.ignore_year_check_box.toggled.connect(self._change_ignore_year)
        self._ui.repeat_check_box.toggled.connect(self._change_repeat)

    @Slot(bool, name="_change_ignore_year")
    def _change_ignore_year(self, ignore_year):
        self._attributes_model.ignore_year = ignore_year

    @Slot(bool, name="_change_repeat")
    def _change_repeat(self, repeat):
        self._attributes_model.repeat = repeat

    @Slot(name='_change_length')
    def _change_length(self):
        length = self._ui.length_edit.value()
        values = self._table_model.values
        resized = _resize_value_array(values, length)
        value = TimeSeriesFixedResolution(
            self._resolution_model.start,
            self._resolution_model.resolution,
            resized,
            self._attributes_model.ignore_year,
            self._attributes_model.repeat,
        )
        self._silent_reset_model(value)
        self._update_plot()

    def _reset_attributes_model(self, ignore_year, repeat):
        self._attributes_model.ignore_year = ignore_year
        self._attributes_model.repeat = repeat
        self._ui.ignore_year_check_box.setChecked(ignore_year)
        self._ui.repeat_check_box.setChecked(repeat)

    @Slot(name='_resolution_changed')
    def _resolution_changed(self):
        try:
            self._resolution_model.resolution = self._ui.resolution_edit.text()
        except ParameterValueFormatError:
            self._ui.resolution_edit.setText(_resolution_to_text(self._resolution_model.resolution))
            return
        values = self._table_model.values
        value = TimeSeriesFixedResolution(
            self._resolution_model.start,
            self._resolution_model.resolution,
            values,
            self._attributes_model.ignore_year,
            self._attributes_model.repeat,
        )
        self._silent_reset_model(value)
        self._update_plot()

    def set_value(self, value):
        self._table_model = IndexedValueTableModel(value.indexes, value.values, None, float)
        self._table_model.set_index_header("Time stamps")
        self._table_model.set_value_header("Values")
        self._table_model.set_fixed_indexes(True)
        self._table_model.dataChanged.connect(self._table_changed)
        self._resolution_model = _FixedResolutionModel(value.start, value.resolution)
        self._ui.time_series_table.setModel(self._table_model)
        self._ui.start_time_edit.setText(str(value.start))
        self._ui.length_edit.setValue(len(value))
        self._ui.resolution_edit.setText(_resolution_to_text(value.resolution))
        self._reset_attributes_model(value.ignore_year, value.repeat)
        self._update_plot()

    def _silent_reset_model(self, value):
        self._table_model.dataChanged.disconnect(self._table_changed)
        self._table_model.reset(value.indexes, value.values)
        self._table_model.dataChanged.connect(self._table_changed)

    @Slot(name='_start_time_changed')
    def _start_time_changed(self):
        start_text = self._ui.start_time_edit.text()
        try:
            self._resolution_model.start = start_text
        except ValueError:
            self._ui.start_time_edit.setText(str(self._resolution_model.start))
            return
        value = TimeSeriesFixedResolution(
            self._resolution_model.start,
            self._resolution_model.resolution,
            self._table_model.values,
            self._attributes_model.ignore_year,
            self._attributes_model.repeat,
        )
        self._silent_reset_model(value)
        self._update_plot()

    @Slot("QModelIndex", "QModelIndex", "list", name="_table_changed")
    def _table_changed(self, topLeft, bottomRight, roles=None):
        """A slot to signal that the table view has changed."""
        self._update_plot()

    def _update_plot(self,):
        self._plot_widget.canvas.axes.cla()
        stamps = self._table_model.indexes
        values = self._table_model.values
        self._plot_widget.canvas.axes.plot(stamps, values)
        self._plot_widget.canvas.draw()

    def value(self):
        values = self._table_model.values
        value = TimeSeriesFixedResolution(
            self._resolution_model.start,
            self._resolution_model.resolution,
            values,
            self._attributes_model.ignore_year,
            self._attributes_model.repeat,
        )
        return value
