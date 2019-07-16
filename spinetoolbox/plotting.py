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
from PySide2.QtCore import Qt
from spinedb_api import from_database, TimeSeries
from tabularview_models import PivotTableModel
from widgets.plot_widget import PlotWidget


class PlottingError(Exception):
    """
    An exception signalling failure in plotting.

    Attributes:
        message (str): an error message
    """

    def __init__(self, message):
        super().__init__()
        self._message = message

    @property
    def message(self):
        """Returns the error message."""
        return self._message


def _add_plot_to_widget(values, labels, plot_widget):
    """Adds a new plot to plot_widget."""
    if not values:
        return
    if isinstance(values[0], TimeSeries):
        for value, label in zip(values, labels):
            plot_widget.canvas.axes.step(value.indexes, value.values, label=label, where='post')
    else:
        plot_widget.canvas.axes.plot(values[0], values[1], label=labels[0])


def _raise_if_types_inconsistent(values):
    """Raises an exception if not all values are TimeSeries or floats."""
    if not all(isinstance(value, TimeSeries) for value in values) and not all(
        isinstance(value, float) for value in values
    ):
        raise PlottingError("Cannot plot a mixture of time series and other data")


def _filter_name_columns(selections):
    """Returns a dict with all but the entry with the greatest key removed."""
    # In case of Tree and Graph views the user may have selected non-data columns for plotting.
    # This function removes those from the selected columns.
    last_column = max(selections.keys())
    return {last_column: selections[last_column]}


def _organize_selection_to_columns(indexes):
    """Organizes a list of model indexes into a dictionary of {column: (rows)} entries."""
    selections = dict()
    for index in indexes:
        column = index.column()
        if column not in selections:
            selections[column] = set()
        selections[column].add(index.row())
    return selections


def _collect_single_column_values(model, column, rows):
    """
    Collects selected parameter values from a single column.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a list of floats and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (QAbstractTableModel): a Tree or Graph view model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot

    Returns:
        a tuple of values and label(s)
    """
    values = list()
    labels = list()
    for row in sorted(rows):
        data_index = model.index(row, column)
        data = model.data(data_index, role=Qt.EditRole)
        if data:
            value = from_database(data)
            if isinstance(value, (float, int)):
                values.append(float(value))
            elif isinstance(value, TimeSeries):
                names = list()
                for col in range(column):
                    data = model.data(model.index(row, col))
                    if isinstance(data, str):
                        names.append(data)
                labels.append(', '.join(names))
                values.append(value)
            else:
                raise PlottingError("Cannot plot value on row {}".format(row))
    if not values:
        return values, labels
    _raise_if_types_inconsistent(values)
    if isinstance(values[0], float):
        labels.append("value")
    return values, labels


def _collect_pivot_single_column_values(model, column, rows):
    """
    Collects selected parameter values from a single column in a PivotTableModel.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a list of floats and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (PivotTableModel): a Tree or Graph view model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot

    Returns:
        a tuple of values and label(s)
    """
    values = list()
    labels = list()
    for row in sorted(rows):
        data_index = model.index(row, column)
        if not model.index_in_data(data_index):
            continue
        data = model.data(data_index, role=Qt.EditRole)
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
    _raise_if_types_inconsistent(values)
    if isinstance(values[0], float):
        labels.append(', '.join(model.get_col_key(column)))
    return values, labels


def _collect_column_values(model, column, rows):
    """
    Collects selected parameter values from a single column for plotting.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a single tuple of two lists of x and y values
    and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (QAbstractTableModel): a Tree or Graph view model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot

    Returns:
        a tuple of values and label(s)
    """
    values, labels = _collect_single_column_values(model, column, rows)
    if values and isinstance(values[0], float):
        x_values = np.arange(1.0, float(len(values) + 1.0))
        return (x_values, values), labels
    return values, labels


def _collect_pivot_column_values(model, column, rows):
    """
    Collects selected parameter values from a single column in a PivotTableModel for plotting.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a single tuple of two lists of x and y values
    and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (PivotTableModel): a Tree or Graph view model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot

    Returns:
        a tuple of values and label(s)
    """
    values, labels = _collect_pivot_single_column_values(model, column, rows)
    if values and isinstance(values[0], float):
        # Collect the y values as well
        if model.plot_x_column is not None and column != model.plot_x_column:
            x_values, _ = _collect_pivot_single_column_values(model, model.plot_x_column, rows)
        else:
            x_values = np.arange(1.0, float(len(values) + 1.0))
        return (x_values, values), labels
    return values, labels


def plot_pivot_column(model, column):
    """
    Returns a plot widget with a plot of an entire column in PivotTableModel.

    Args:
        model (PivotTableModel): a pivot table model
        column (int): a column index to the model
    Returns:
        a PlotWidget object
    """
    plot_widget = PlotWidget()
    values, labels = _collect_pivot_column_values(model, column, range(model.first_data_row(), model.rowCount()))
    _add_plot_to_widget(values, labels, plot_widget)
    if len(plot_widget.canvas.axes.get_lines()) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    return plot_widget


def plot_selection(model, indexes):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        indexes (Iterable): a list of QModelIndex objects for plotting
    Returns:
        a PlotWidget object
    """
    plot_widget = PlotWidget()
    selections = _organize_selection_to_columns(indexes)
    if isinstance(model, PivotTableModel):
        collect_column_values = _collect_pivot_column_values
    else:
        collect_column_values = _collect_column_values
        selections = _filter_name_columns(selections)
    first_column_value_type = None
    for column, rows in selections.items():
        values, labels = collect_column_values(model, column, rows)
        if first_column_value_type is None and values:
            if isinstance(values[0], TimeSeries):
                first_column_value_type = TimeSeries
            else:
                first_column_value_type = type(values[1][0])
        elif values:
            if isinstance(values[0], TimeSeries) and not isinstance(first_column_value_type, TimeSeries):
                raise PlottingError("Cannot plot a mixture of time series and other data")
            if not isinstance(values[0][1], first_column_value_type):
                raise PlottingError("Cannot plot a mixture of time series and other data")
        _add_plot_to_widget(values, labels, plot_widget)
    plot_lines = plot_widget.canvas.axes.get_lines()
    if len(plot_lines) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    elif len(plot_lines) == 1:
        plot_widget.canvas.axes.set_title(plot_lines[0].get_label())
    return plot_widget


def tree_graph_view_parameter_value_name(index, table_view):
    tokens = list()
    for column in range(index.column()):
        if not table_view.isColumnHidden(column):
            token = index.model().index(index.row(), column).data()
            if token is not None:
                tokens.append(token)
    return ", ".join(tokens)
