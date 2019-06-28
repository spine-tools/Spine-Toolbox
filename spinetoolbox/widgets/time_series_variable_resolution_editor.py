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

import numpy
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog
from spinedb_api import ParameterValueFormatError, TimeSeriesVariableResolution
from time_series_table_model import TimeSeriesTableModel
from ui.time_series_variable_resolution_editor import Ui_TimeSeriesVariableResolutionEditor
from widgets.plot_widget import PlotWidget


class TimeSeriesVariableResolutionEditor(QDialog):
    """
    A widget for editing time series data.

    Attributes:
        model (MinimalTableModel): the model cell of which is being edited
        index (QModelIndex): an index to model
        value (ParameterValue): parameter value at index
        parent (QWidget): a parent widget
    """

    def __init__(self, model, index, value, parent=None):
        super().__init__(parent)
        self.ui = Ui_TimeSeriesVariableResolutionEditor()
        self.ui.setupUi(self)
        self._parent_model = model
        self._parent_model_index = index
        self._model = TimeSeriesTableModel(value.indexes, value.values)
        self._model.dataChanged.connect(self._model_data_changed)
        self.ui.time_series_table.setModel(self._model)
        self.ui.plot_widget = PlotWidget()
        self.ui.splitter.insertWidget(1, self.ui.plot_widget)
        self.ui.plot_widget.canvas.axes.plot(value.indexes, value.values)

    @Slot("QModelIndex", "QModelIndex", "list", name="_model_data_changed")
    def _model_data_changed(self, topLeft, bottomRight, roles=None):
        """A slot to signal that the table view has changed."""
        try:
            stamps, values = map_from_model(self._model.model_data())
            self._parent_model.setData(self._parent_model_index, TimeSeriesVariableResolution(stamps, values).as_json())
            self.ui.plot_widget.canvas.axes.cla()
            self.ui.plot_widget.canvas.axes.plot(stamps, values)
            self.ui.plot_widget.canvas.draw()
        except (ValueError, ParameterValueFormatError):
            self._invalidate_table(topLeft, bottomRight)

    def _invalidate_table(self, top_left, bottom_right):
        """Write error messages to the table to signal a value conversion error"""
        self._model.dataChanged.disconnect(self._model_data_changed)
        invalid_indexes = list()
        row = top_left.row()
        while row <= bottom_right.row():
            column = top_left.column()
            while column <= bottom_right.column():
                invalid_indexes.append(self._model.index(row, column))
                column += 1
            row += 1
        errors = len(invalid_indexes) * ['Error']
        print(self._model.batch_set_data(invalid_indexes, errors))
        self._model.dataChanged.connect(self._model_data_changed)
