######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Functions for plotting on PlotWidget.

:author: A. Soininen(VTT)
:date:   9.7.2019
"""

import numpy as np
from spinedb_api import from_database, TimeSeries
from widgets.plot_widget import PlotWidget


class PlottingError(Exception):
    def __init__(self, message):
        super().__init__()
        self._message = message

    @property
    def message(self):
        return self._message


def _organize_selection_to_columns(indexes):
    selections = dict()
    for index in indexes:
        column = index.column()
        if column not in selections:
            selections[column] = set()
        selections[column].add(index.row())
    return selections


def _collect_pivot_single_column_values(model, column, rows):
    values = list()
    labels = list()
    for row in sorted(rows):
        data_index = model.index(row, column)
        if not model.index_in_data(data_index):
            continue
        data = model.data(data_index)
        if data:
            value = from_database(data)
            if isinstance(value, (float, int)):
                values.append(float(value))
            elif isinstance(value, TimeSeries):
                labels.append(', '.join(model.get_key(data_index)))
                values.append(value)
            else:
                raise PlottingError("Cannot plot value on row {}".format(row))
    if not values:
        return values, labels
    if isinstance(values[0], TimeSeries):
        if not all(isinstance(value, TimeSeries) for value in values):
            raise PlottingError("Cannot plot a mixture of time series and other data")
    else:
        if not all(isinstance(value, float) for value in values):
            raise PlottingError("Cannot plot a mixture of time series and other data")
        labels.append(', '.join(model.get_col_key(column)))
    return values, labels


def _collect_pivot_column_values(model, column, rows):
    values, labels = _collect_pivot_single_column_values(model, column, rows)
    if values and isinstance(values[0], float):
        # Collect the y values as well
        if model.plot_y_column is not None and column != model.plot_y_column:
            y_values, _ = _collect_pivot_single_column_values(model, model.plot_y_column, rows)
        else:
            y_values = np.arange(1.0, float(len(values) + 1.0))
        return (y_values, values), labels
    return values, labels


def plot_pivot_column(model, column):
    plot_widget = PlotWidget()
    values, labels = _collect_pivot_column_values(model, column, range(model.first_data_row(), model.rowCount()))
    add_plot_to_widget(values, labels, plot_widget)
    if len(plot_widget.canvas.axes.get_lines()) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    return plot_widget


def plot_pivot_selection(model, indexes):
    plot_widget = PlotWidget()
    selections = _organize_selection_to_columns(indexes)
    first_column_value_type = None
    for column, rows in selections.items():
        values, labels = _collect_pivot_column_values(model, column, rows)
        if first_column_value_type is None and values:
            if isinstance(values[0], TimeSeries):
                first_column_value_type = TimeSeries
            else:
                first_column_value_type = type(values[0][1])
        elif values:
            if isinstance(values[0], TimeSeries) and not isinstance(first_column_value_type, TimeSeries):
                raise PlottingError("Cannot plot a mixture of time series and other data")
            elif not isinstance(values[0][1], first_column_value_type):
                raise PlottingError("Cannot plot a mixture of time series and other data")
        add_plot_to_widget(values, labels, plot_widget)
    plot_lines = plot_widget.canvas.axes.get_lines()
    if len(plot_lines) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    elif len(plot_lines) == 1:
        plot_widget.canvas.axes.set_title(plot_lines[0].get_label())
    return plot_widget


def add_plot_to_widget(values, labels, plot_widget):
    if not values:
        return
    if isinstance(values[0], TimeSeries):
        for value, label in zip(values, labels):
            plot_widget.canvas.axes.step(value.indexes, value.values, label=label, where='post')
    else:
        plot_widget.canvas.axes.plot(values[0], values[1], label=labels[0])
