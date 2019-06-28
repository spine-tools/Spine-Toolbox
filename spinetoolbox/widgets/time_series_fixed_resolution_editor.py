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
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog
from spinedb_api import duration_to_relativedelta, ParameterValueFormatError, relativedelta_to_duration, TimeSeriesFixedResolution
from time_series_table_model import TimeSeriesTableModel
from ui.time_series_fixed_resolution_editor import Ui_TimeSeriesFixedResolutionEditor
from widgets.plot_widget import PlotWidget


def _resize_value_array(values, length):
    if len(values) == length:
        return values
    if len(values) > length:
        return values[:length]
    zero_padded = np.zeros(length)
    zero_padded[0:len(values)] = values
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


class TimeSeriesFixedResolutionEditor(QDialog):
    """
    A widget for editing time series data with a fixed time step.

    Attributes:
        model (MinimalTableModel): the model cell of which is being edited
        index (QModelIndex): an index to model
        value (ParameterValue): parameter value at index
        parent (QWidget): a parent widget
    """

    def __init__(self, model, index, value, parent=None):
        super().__init__(parent)
        self.ui = Ui_TimeSeriesFixedResolutionEditor()
        self.ui.setupUi(self)
        self._parent_model = model
        self._parent_model_index = index
        stamps = value.indexes
        values = value.values
        self._model = TimeSeriesTableModel(stamps, values)
        self._model.set_fixed_time_stamps(True)
        self._model.dataChanged.connect(self._table_changed)
        self._table_valid = True
        self.ui.start_time_edit.setText(str(value.start))
        self.ui.start_time_edit.editingFinished.connect(self._start_time_changed)
        self._start_time_valid = True
        self._start_time_label_text = self.ui.start_time_label.text()
        self.ui.length_edit.setValue(len(value))
        self.ui.length_edit.editingFinished.connect(self._length_changed)
        self.ui.resolution_edit.setText(_resolution_to_text(value.resolution))
        self.ui.resolution_edit.editingFinished.connect(self._resolution_changed)
        self._resolution_valid = True
        self._resolution_label_text = self.ui.resolution_label.text()
        self.ui.time_series_table.setModel(self._model)
        self.ui.plot_widget = PlotWidget()
        self.ui.splitter.insertWidget(1, self.ui.plot_widget)
        self.ui.plot_widget.canvas.axes.plot(stamps, values)

    @Slot(name='_length_changed')
    def _length_changed(self):
        if not self._valid_inputs():
            return
        length = self.ui.length_edit.value()
        values = self._model.values
        resized = _resize_value_array(values, length)
        timedelta = duration_to_relativedelta(self.ui.resolution_edit.text())
        start = dateutil.parser.parse(self.ui.start_time_edit.text())
        value = TimeSeriesFixedResolution(start, [timedelta], resized, False, False)
        self._parent_model.setData(self._parent_model_index, value.to_database())
        self._silent_reset_model(value)
        self._update_plot(value)

    @Slot(name='_resolution_changed')
    def _resolution_changed(self):
        resolution_text = self.ui.resolution_edit.text()
        tokens = resolution_text.split(',')
        resolution = list()
        for token in tokens:
            try:
                resolution.append(duration_to_relativedelta(token.strip()))
            except ParameterValueFormatError:
                self._resolution_valid = False
                self.ui.resolution_label.setText(self._resolution_label_text + " (syntax error)")
                return
        self.ui.resolution_label.setText(self._resolution_label_text)
        self._resolution_valid = True
        if not self._valid_inputs():
            return
        start = dateutil.parser.parse(self.ui.start_time_edit.text())
        values = self._model.values
        value = TimeSeriesFixedResolution(start, resolution, values, False, False)
        self._parent_model.setData(self._parent_model_index, value.to_database())
        self._silent_reset_model(value)
        self._update_plot(value)

    def _silent_reset_model(self, value):
        self._model.dataChanged.disconnect(self._table_changed)
        self._model.reset(value.indexes, value.values)
        self._model.dataChanged.connect(self._table_changed)

    @Slot(name='_start_time_changed')
    def _start_time_changed(self):
        start_text = self.ui.start_time_edit.text()
        try:
            start = dateutil.parser.parse(start_text)
        except ValueError:
            self._start_time_valid = False
            self.ui.start_time_label.setText(self._start_time_label_text + " (syntax error)")
            return
        self.ui.start_time_label.setText(self._start_time_label_text)
        self._start_time_valid = True
        if not self._valid_inputs():
            return
        timedelta = duration_to_relativedelta(self.ui.resolution_edit.text())
        values = self._model.values
        value = TimeSeriesFixedResolution(start, [timedelta], values, False, False)
        self._parent_model.setData(self._parent_model_index, value.to_database())
        self._silent_reset_model(value)
        self._update_plot(value)

    @Slot("QModelIndex", "QModelIndex", "list", name="_table_changed")
    def _table_changed(self, topLeft, bottomRight, roles=None):
        """A slot to signal that the table view has changed."""
        values = self._model.values
        start = dateutil.parser.parse(self.ui.start_time_edit.text())
        timedelta = duration_to_relativedelta(self.ui.resolution_edit.text())
        value = TimeSeriesFixedResolution(start, timedelta, values, False, False)
        self._parent_model.setData(self._parent_model_index, value.to_database())
        self._update_plot(value)

    def _update_plot(self, value):
        self.ui.plot_widget.canvas.axes.cla()
        self.ui.plot_widget.canvas.axes.plot(value.indexes, value.values)
        self.ui.plot_widget.canvas.draw()

    def _valid_inputs(self):
        return self._table_valid and self._start_time_valid and self._resolution_valid
