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
Functions for plotting on PlotWidget.

Currently plotting from the table views found in Graph, Tree and Tabular views are supported.

The main entrance points to plotting are:
- plot_selection() which plots selected cells on a table view returning a PlotWidget object
- plot_pivot_column() which is a specialized method for plotting entire columns of a pivot table
- add_time_series_plot() which adds a time series plot to an existing PlotWidget
- add_map_plot() which adds a map plot to an existing PlotWidget

:author: A. Soininen(VTT)
:date:   9.7.2019
"""

from matplotlib.ticker import MaxNLocator
import numpy as np
from PySide2.QtCore import QModelIndex, Qt
from spinedb_api import from_database, IndexedValue, Map, ParameterValueFormatError, TimeSeries
from .widgets.plot_widget import PlotWidget


class PlottingError(Exception):
    """An exception signalling failure in plotting."""

    def __init__(self, message):
        """
        Args:
            message (str): an error message
        """
        super().__init__()
        self._message = message

    @property
    def message(self):
        """str: the error message."""
        return self._message


def plot_pivot_column(proxy_model, column, hints, plot_widget=None):
    """
    Returns a plot widget with a plot of an entire column in PivotTableModel.

    Args:
        proxy_model (PivotTableSortFilterProxy): a pivot table filter
        column (int): a column index to the model
        hints (PlottingHints): a helper needed for e.g. plot labels
        plot_widget (PlotWidget): an existing plot widget to draw into or None to create a new widget
    Returns:
        PlotWidget: a plot widget
    """
    if plot_widget is None:
        plot_widget = PlotWidget()
        needs_redraw = False
    else:
        needs_redraw = True
    first_data_row = proxy_model.sourceModel().first_data_row()
    values, labels = _collect_column_values(proxy_model, column, range(first_data_row, proxy_model.rowCount()), hints)
    if values:
        if plot_widget.plot_type is None:
            plot_widget.infer_plot_type(values)
        else:
            _raise_if_value_types_clash(values, plot_widget)
    _add_plot_to_widget(values, labels, plot_widget)
    if len(plot_widget.canvas.axes.get_lines()) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    plot_widget.canvas.axes.set_xlabel(hints.x_label(proxy_model))
    plot_lines = plot_widget.canvas.axes.get_lines()
    if plot_lines:
        plot_widget.canvas.axes.set_title(plot_lines[0].get_label())
    if needs_redraw:
        plot_widget.canvas.draw()
    return plot_widget


def plot_selection(model, indexes, hints, plot_widget=None):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        indexes (Iterable): a list of QModelIndex objects for plotting
        hints (PlottingHints): a helper needed for e.g. plot labels
        plot_widget (PlotWidget): an existing plot widget to draw into or None to create a new widget
    Returns:
        a PlotWidget object
    """
    if plot_widget is None:
        plot_widget = PlotWidget()
        needs_redraw = False
    else:
        needs_redraw = True
    selections = hints.filter_columns(_organize_selection_to_columns(indexes), model)
    all_labels = list()
    for column, rows in selections.items():
        values, labels = _collect_column_values(model, column, rows, hints)
        all_labels += labels
        if values:
            if plot_widget.plot_type is None:
                plot_widget.infer_plot_type(values)
            else:
                _raise_if_value_types_clash(values, plot_widget)
        _add_plot_to_widget(values, labels, plot_widget)
    plot_widget.canvas.axes.set_xlabel(hints.x_label(model))
    if len(all_labels) > 1:
        plot_widget.canvas.axes.legend(loc="best", fontsize="small")
    elif len(all_labels) == 1:
        plot_widget.canvas.axes.set_title(all_labels[0])
    if needs_redraw:
        plot_widget.canvas.draw()
    return plot_widget


def add_map_plot(plot_widget, map_value, label=None):
    """
    Adds a map plot to a plot widget.

    Args:
        plot_widget (PlotWidget): a plot widget to modify
        map_value (Map): the map to plot
        label (str): a label for the map
    """
    if not map_value.indexes:
        return
    if map_value.is_nested():
        raise PlottingError("Plotting of nested maps is not supported.")
    if not all(isinstance(value, float) for value in map_value.values):
        raise PlottingError("Cannot plot non-numerical values in map.")
    if not isinstance(map_value.indexes[0], str):
        if hasattr(map_value.indexes[0], "to_text"):
            indexes_as_strings = [index.to_text() for index in map_value.indexes]
        else:
            indexes_as_strings = list(map(str, map_value.indexes))
    else:
        indexes_as_strings = map_value.indexes
    plot_widget.canvas.axes.plot(indexes_as_strings, map_value.values, label=label, linestyle="", marker="o")
    plot_widget.canvas.axes.xaxis.set_major_locator(MaxNLocator(10))


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


class ParameterTablePlottingHints(PlottingHints):
    """Support for plotting data in Parameter table views."""

    def cell_label(self, model, index):
        """Returns a label build from the columns on the left from the data column."""
        return model.value_name(index)

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
        return model.sourceModel().value_name(index)

    def column_label(self, model, column):
        """Returns a label for a table column."""
        return model.sourceModel().column_name(column)

    def filter_columns(self, selections, model):
        """Filters the X column from selections."""
        x_column = model.sourceModel().plot_x_column
        if x_column is None or not model.filterAcceptsColumn(x_column, QModelIndex()):
            return selections
        proxy_x_column = self._map_column_from_source(model, x_column)
        filtered = dict()
        columns = selections.keys()
        for column in columns:
            if column != proxy_x_column:
                filtered[column] = selections[column]
        return filtered

    def is_index_in_data(self, model, index):
        """Returns True if index is in the data portion of the table."""
        return model.sourceModel().index_in_data(index)

    def special_x_values(self, model, column, rows):
        """Returns the values from the X column if one is designated otherwise returns None."""
        x_column = model.sourceModel().plot_x_column
        if x_column is not None and model.filterAcceptsColumn(x_column, QModelIndex()):
            proxy_x_column = self._map_column_from_source(model, x_column)
            if column != proxy_x_column:
                x_values, _ = _collect_single_column_values(model, proxy_x_column, rows, self)
                return x_values
        return None

    def x_label(self, model):
        """Returns the label of the X column, if available."""
        x_column = model.sourceModel().plot_x_column
        if x_column is None or not model.filterAcceptsColumn(x_column, QModelIndex()):
            return ""
        return self.column_label(model, self._map_column_from_source(model, x_column))

    @staticmethod
    def _map_column_to_source(proxy_model, proxy_column):
        """Maps a proxy model column to source model."""
        return proxy_model.mapToSource(proxy_model.index(0, proxy_column)).column()

    @staticmethod
    def _map_column_from_source(proxy_model, source_column):
        """Maps a source model column to proxy model."""
        source_index = proxy_model.sourceModel().index(0, source_column)
        return proxy_model.mapFromSource(source_index).column()


def _add_plot_to_widget(values, labels, plot_widget):
    """Adds a new plot to plot_widget."""
    if not values:
        return
    if isinstance(values[0], TimeSeries):
        for value, label in zip(values, labels):
            add_time_series_plot(plot_widget, value, label)
    elif isinstance(values[0], Map):
        for value, label in zip(values, labels):
            add_map_plot(plot_widget, value, label)
    else:
        plot_widget.canvas.axes.plot(values[0], values[1], label=labels[0])


def _raise_if_types_inconsistent(values):
    """Raises an exception if not all values are TimeSeries or floats."""
    if not values:
        return
    first_value_type = type(values[0])
    if issubclass(first_value_type, TimeSeries):
        # Clump fixed and variable step time series together. We can plot both at the same time.
        first_value_type = TimeSeries
    if not all(isinstance(value, first_value_type) for value in values[1:]):
        raise PlottingError("Cannot plot a mixture of indexed and other data")


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
        selections.setdefault(index.column(), set()).add(index.row())
    return selections


def _collect_single_column_values(model, column, rows, hints):
    """
    Collects selected parameter values from a single column.

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
            elif isinstance(value, (Map, TimeSeries)):
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
    Collects selected parameter values from a single column for plotting.

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


def _raise_if_value_types_clash(values, plot_widget):
    """Raises a PlottingError if values type is incompatible with plot_widget."""
    if isinstance(values[0], IndexedValue):
        if isinstance(values[0], TimeSeries) and not plot_widget.plot_type == TimeSeries:
            raise PlottingError("Cannot plot a mixture of time series and other value types.")
        if isinstance(values[0], Map) and not plot_widget.plot_type == Map:
            raise PlottingError("Cannot plot a mixture of maps and other value types.")
    elif not isinstance(values[0][1], plot_widget.plot_type):
        raise PlottingError("Cannot plot a mixture of indexed values and scalars.")
