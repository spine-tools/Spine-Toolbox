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

Currently plotting from the table views found in Graph, Tree and Tabular views are supported.

The main entrance points to plotting are:
- plot_selection() which plots selected cells on a table view returning a PlotWidget object
- plot_pivot_column() which is a specialized method for plotting entire columns of a pivot table
- add_time_series_plot() which adds a time series plot to an existing PlotWidget

:author: A. Soininen(VTT)
:date:   9.7.2019
"""

import numpy as np
from PySide2.QtCore import Qt
from spinedb_api import from_database, ParameterValueFormatError, TimeSeries
from .widgets.plot_widget import PlotWidget


class PlottingError(Exception):
    def __init__(self, message):
        """An exception signalling failure in plotting.

        Args:
            message (str): an error message
        """
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
            add_time_series_plot(plot_widget, value, label)
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


def _collect_single_column_values(model, column, rows, hints):
    """
    Collects selected parameter values from a single column in a PivotTableModel.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a list of floats and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (QAbstractTableModel): a table model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot
        hints (PlottingHints): a plot support object

    Returns:
        a tuple of values and label(s)
    """
    values = list()
    labels = list()
    for row in sorted(rows):
        data_index = model.index(row, column)
        if not hints.is_index_in_data(model, data_index):
            continue
        data = model.data(data_index, role=Qt.EditRole)
        if data:
            try:
                value = from_database(data)
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (float, int)):
                values.append(float(value))
            elif isinstance(value, TimeSeries):
                labels.append(hints.cell_label(model, data_index))
                values.append(value)
            else:
                raise PlottingError("Cannot plot value on row {}".format(row))
    if not values:
        return values, labels
    _raise_if_types_inconsistent(values)
    if isinstance(values[0], float):
        labels.append(hints.column_label(model, column))
    return values, labels


def _collect_column_values(model, column, rows, hints):
    """
    Collects selected parameter values from a single column in a PivotTableModel for plotting.

    The return value of this function depends on what type of data the given column contains.
    In case of plain numbers, a single tuple of two lists of x and y values
    and a single label string are returned.
    In case of time series, a list of TimeSeries objects is returned, accompanied
    by a list of labels, each label corresponding to one of the time series.

    Args:
        model (QAbstractTableModel): a table model
        column (int): a column index to the model
        rows (Sequence): row indexes to plot
        hints (PlottingHints): a support object

    Returns:
        a tuple of values and label(s)
    """
    values, labels = _collect_single_column_values(model, column, rows, hints)
    if values and isinstance(values[0], float):
        # Collect the y values as well
        x_values = hints.special_x_values(model, column, rows)
        if x_values is None:
            x_values = np.arange(1.0, float(len(values) + 1.0))
        return (x_values, values), labels
    return values, labels


def plot_pivot_column(model, column, hints):
    """
    Returns a plot widget with a plot of an entire column in PivotTableModel.

    Args:
        model (PivotTableModel): a pivot table model
        column (int): a column index to the model
        hints (PlottingHints): a helper needed for e.g. plot labels

    Returns:
        a PlotWidget object
    """
    plot_widget = PlotWidget()
    values, labels = _collect_column_values(model, column, range(model.first_data_row(), model.rowCount()), hints)
    _add_plot_to_widget(values, labels, plot_widget)
    if len(plot_widget.canvas.axes.get_lines()) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    plot_widget.canvas.axes.set_xlabel(hints.x_label(model))
    plot_lines = plot_widget.canvas.axes.get_lines()
    plot_widget.canvas.axes.set_title(plot_lines[0].get_label())
    return plot_widget


def plot_selection(model, indexes, hints):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        indexes (Iterable): a list of QModelIndex objects for plotting
        hints (PlottingHints): a helper needed for e.g. plot labels

    Returns:
        a PlotWidget object
    """
    plot_widget = PlotWidget()
    selections = hints.filter_columns(_organize_selection_to_columns(indexes), model)
    first_column_value_type = None
    for column, rows in selections.items():
        values, labels = _collect_column_values(model, column, rows, hints)
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
    plot_widget.canvas.axes.set_xlabel(hints.x_label(model))
    plot_lines = plot_widget.canvas.axes.get_lines()
    if len(plot_lines) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    elif len(plot_lines) == 1:
        plot_widget.canvas.axes.set_title(plot_lines[0].get_label())
    return plot_widget


def add_time_series_plot(plot_widget, value, label=None):
    """
    Adds a time series step plot to a plot widget.

    Args:
        plot_widget (PlotWidget): a plot widget to modify
        value (TimeSeries): the time series to plot
        label (str): a label for the time series
    """
    plot_widget.canvas.axes.step(value.indexes, value.values, label=label, where='post')
    # matplotlib cannot have time stamps before 0001-01-01T00:00 on the x axis
    left, _ = plot_widget.canvas.axes.get_xlim()
    if left < 1.0:
        # 1.0 corresponds to 0001-01-01T00:00
        plot_widget.canvas.axes.set_xlim(left=1.0)
    plot_widget.canvas.figure.autofmt_xdate()


def tree_graph_view_parameter_value_name(index, table_view):
    """
    Returns a label for Tree or Graph view table cell.

    Args:
        index (QModelIndex): an index to the table model
        table_view (QTableView): a table view widget corresponding to index

    Returns:
        a unique name for the parameter value as a string
    """
    tokens = list()
    for column in range(index.column()):
        if not table_view.isColumnHidden(column):
            token = index.model().index(index.row(), column).data()
            if token is not None:
                tokens.append(token)
    return ", ".join(tokens)


class PlottingHints:
    """A base class for plotting hints.

    The functionality in this class allows the plotting functions to work
    without explicit knowledge of the underlying table model or widget.
    """

    def cell_label(self, model, index):
        """Returns a label for the cell given by index in a table."""
        raise NotImplementedError()

    def column_label(self, model, column):
        """Returns a label for a column."""
        raise NotImplementedError()

    def filter_columns(self, selections, model):
        """Filters columns and returns the filtered selections."""
        raise NotImplementedError()

    def is_index_in_data(self, model, index):
        """Returns true if the cell given by index is actually plottable data."""
        raise NotImplementedError()

    def special_x_values(self, model, column, rows):
        """Returns X values if available, otherwise returns None."""
        raise NotImplementedError()

    def x_label(self, model):
        """Returns a label for the x axis."""
        raise NotImplementedError()


class GraphAndTreeViewPlottingHints(PlottingHints):
    def __init__(self, table_view):
        """Support for plotting data in Graph and Tree views.

        Args:
            table_view (QTableView): a parameter value or definition widget
        """
        self._table_view = table_view

    def cell_label(self, model, index):
        """Returns a label build from the columns on the left from the data column."""
        return tree_graph_view_parameter_value_name(index, self._table_view)

    def column_label(self, model, column):
        """Returns the column header."""
        return model.headerData(column)

    def filter_columns(self, selections, model):
        """Returns the 'value' or 'default_value' column only."""
        columns = selections.keys()
        filtered = dict()
        for column in columns:
            header = model.headerData(column)
            if header in ("value", "default_value"):
                filtered[column] = selections[column]
        return filtered

    def is_index_in_data(self, model, index):
        """Always returns True."""
        return True

    def special_x_values(self, model, column, rows):
        """Always returns None."""
        return None

    def x_label(self, model):
        """Returns an empty string for the x axis label."""
        return ""


class PivotTablePlottingHints(PlottingHints):
    """Support for plotting data in Tabular view."""

    def cell_label(self, model, index):
        """Returns a label for the table cell given by index."""
        return ", ".join(model.get_key(index))

    def column_label(self, model, column):
        """Returns a label for a table column."""
        return ", ".join(model.get_col_key(column))

    def filter_columns(self, selections, model):
        """Filters the X column from selections."""
        x_column = model.plot_x_column
        if x_column is None:
            return selections
        filtered = dict()
        columns = selections.keys()
        for column in columns:
            if column != x_column:
                filtered[column] = selections[column]
        return filtered

    def is_index_in_data(self, model, index):
        """Returns True if index is in the data portion of the table."""
        return model.index_in_data(index)

    def special_x_values(self, model, column, rows):
        """Returns the values from the X column if one is designated otherwise returns None."""
        if model.plot_x_column is not None and column != model.plot_x_column:
            x_values, _ = _collect_single_column_values(model, model.plot_x_column, rows, self)
            return x_values
        return None

    def x_label(self, model):
        """Returns the label of the X column, if available."""
        x_column = model.plot_x_column
        if x_column is None:
            return ""
        return self.column_label(model, x_column)
