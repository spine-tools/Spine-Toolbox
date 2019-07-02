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
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import ParameterValueFormatError, TimeSeriesVariableResolution
from indexed_value_table_model import IndexedValueTableModel
from ui.time_series_variable_resolution_editor import Ui_TimeSeriesVariableResolutionEditor
from widgets.plot_widget import PlotWidget
from widgets.time_series_fixed_resolution_editor import TimeSeriesAttributesModel


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
        self._table_model = None
        self._attributes_model = TimeSeriesAttributesModel(True, True)
        self._ui = Ui_TimeSeriesVariableResolutionEditor()
        self._ui.setupUi(self)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._ui.ignore_year_check_box.setChecked(self._attributes_model.ignore_year)
        self._ui.ignore_year_check_box.toggled.connect(self._change_ignore_year)
        self._ui.repeat_check_box.setChecked(self._attributes_model.repeat)
        self._ui.repeat_check_box.toggled.connect(self._change_repeat)

    @Slot(bool, name="_change_ignore_year")
    def _change_ignore_year(self, ignore_year):
        self._attributes_model.ignore_year = ignore_year

    @Slot(bool, name="_change_repeat")
    def _change_repeat(self, repeat):
        self._attributes_model.repeat = repeat

    def _reset_attributes_model(self, ignore_year, repeat):
        self._attributes_model.ignore_year = ignore_year
        self._attributes_model.repeat = repeat
        self._ui.ignore_year_check_box.setChecked(ignore_year)
        self._ui.repeat_check_box.setChecked(repeat)

    @Slot("QModelIndex", "QModelIndex", "list", name="_table_model_data_changed")
    def _table_model_data_changed(self, topLeft, bottomRight, roles=None):
        """A slot to signal that the table view has changed."""
        stamps = self._table_model.indexes
        values = self._table_model.values
        self._plot_widget.canvas.axes.cla()
        self._plot_widget.canvas.axes.plot(stamps, values)
        self._plot_widget.canvas.draw()

    def set_value(self, value):
        self._table_model = IndexedValueTableModel(value.indexes, value.values, dateutil.parser.parse, float)
        self._table_model.set_index_header("Time stamps")
        self._table_model.set_value_header("Values")
        self._table_model.dataChanged.connect(self._table_model_data_changed)
        self._ui.time_series_table.setModel(self._table_model)
        self._reset_attributes_model(value.ignore_year, value.repeat)
        self._plot_widget.canvas.axes.plot(value.indexes, value.values)

    def value(self):
        stamps = self._table_model.indexes
        values = self._table_model.values
        return TimeSeriesVariableResolution(
            stamps, values, self._attributes_model.ignore_year, self._attributes_model.repeat
        )
