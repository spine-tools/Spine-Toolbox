:mod:`spinetoolbox.plotting`
============================

.. py:module:: spinetoolbox.plotting

.. autoapi-nested-parse::

   Functions for plotting on PlotWidget.

   Currently plotting from the table views found in Graph, Tree and Tabular views are supported.

   The main entrance points to plotting are:
   - plot_selection() which plots selected cells on a table view returning a PlotWidget object
   - plot_pivot_column() which is a specialized method for plotting entire columns of a pivot table
   - add_time_series_plot() which adds a time series plot to an existing PlotWidget

   :author: A. Soininen(VTT)
   :date:   9.7.2019



Module Contents
---------------

.. py:exception:: PlottingError(message)

   Bases: :class:`Exception`

   An exception signalling failure in plotting.

   :param message: an error message
   :type message: str

   .. method:: message(self)
      :property:


      Returns the error message.



.. function:: _add_plot_to_widget(values, labels, plot_widget)

   Adds a new plot to plot_widget.


.. function:: _raise_if_types_inconsistent(values)

   Raises an exception if not all values are TimeSeries or floats.


.. function:: _filter_name_columns(selections)

   Returns a dict with all but the entry with the greatest key removed.


.. function:: _organize_selection_to_columns(indexes)

   Organizes a list of model indexes into a dictionary of {column: (rows)} entries.


.. function:: _collect_single_column_values(model, column, rows, hints)

   Collects selected parameter values from a single column.

   The return value of this function depends on what type of data the given column contains.
   In case of plain numbers, a list of floats and a single label string are returned.
   In case of time series, a list of TimeSeries objects is returned, accompanied
   by a list of labels, each label corresponding to one of the time series.

   :param model: a table model
   :type model: QAbstractTableModel
   :param column: a column index to the model
   :type column: int
   :param rows: row indexes to plot
   :type rows: Sequence
   :param hints: a plot support object
   :type hints: PlottingHints

   :returns: a tuple of values and label(s)


.. function:: _collect_column_values(model, column, rows, hints)

   Collects selected parameter values from a single column for plotting.

   The return value of this function depends on what type of data the given column contains.
   In case of plain numbers, a single tuple of two lists of x and y values
   and a single label string are returned.
   In case of time series, a list of TimeSeries objects is returned, accompanied
   by a list of labels, each label corresponding to one of the time series.

   :param model: a table model
   :type model: QAbstractTableModel
   :param column: a column index to the model
   :type column: int
   :param rows: row indexes to plot
   :type rows: Sequence
   :param hints: a support object
   :type hints: PlottingHints

   :returns: a tuple of values and label(s)


.. function:: plot_pivot_column(proxy_model, column, hints)

   Returns a plot widget with a plot of an entire column in PivotTableModel.

   :param proxy_model: a pivot table filter
   :type proxy_model: PivotTableSortFilterProxy
   :param column: a column index to the model
   :type column: int
   :param hints: a helper needed for e.g. plot labels
   :type hints: PlottingHints

   :returns: a PlotWidget object


.. function:: plot_selection(model, indexes, hints)

   Returns a plot widget with plots of the selected indexes.

   :param model: a model
   :type model: QAbstractTableModel
   :param indexes: a list of QModelIndex objects for plotting
   :type indexes: Iterable
   :param hints: a helper needed for e.g. plot labels
   :type hints: PlottingHints

   :returns: a PlotWidget object


.. function:: add_time_series_plot(plot_widget, value, label=None)

   Adds a time series step plot to a plot widget.

   :param plot_widget: a plot widget to modify
   :type plot_widget: PlotWidget
   :param value: the time series to plot
   :type value: TimeSeries
   :param label: a label for the time series
   :type label: str


.. py:class:: PlottingHints

   A base class for plotting hints.

   The functionality in this class allows the plotting functions to work
   without explicit knowledge of the underlying table model or widget.

   .. method:: cell_label(self, model, index)
      :abstractmethod:


      Returns a label for the cell given by index in a table.


   .. method:: column_label(self, model, column)
      :abstractmethod:


      Returns a label for a column.


   .. method:: filter_columns(self, selections, model)
      :abstractmethod:


      Filters columns and returns the filtered selections.


   .. method:: is_index_in_data(self, model, index)
      :abstractmethod:


      Returns true if the cell given by index is actually plottable data.


   .. method:: special_x_values(self, model, column, rows)
      :abstractmethod:


      Returns X values if available, otherwise returns None.


   .. method:: x_label(self, model)
      :abstractmethod:


      Returns a label for the x axis.



.. py:class:: ParameterTablePlottingHints

   Bases: :class:`spinetoolbox.plotting.PlottingHints`

   Support for plotting data in Parameter table views.

   .. method:: cell_label(self, model, index)


      Returns a label build from the columns on the left from the data column.


   .. method:: column_label(self, model, column)


      Returns the column header.


   .. method:: filter_columns(self, selections, model)


      Returns the 'value' or 'default_value' column only.


   .. method:: is_index_in_data(self, model, index)


      Always returns True.


   .. method:: special_x_values(self, model, column, rows)


      Always returns None.


   .. method:: x_label(self, model)


      Returns an empty string for the x axis label.



.. py:class:: PivotTablePlottingHints

   Bases: :class:`spinetoolbox.plotting.PlottingHints`

   Support for plotting data in Tabular view.

   .. method:: cell_label(self, model, index)


      Returns a label for the table cell given by index.


   .. method:: column_label(self, model, column)


      Returns a label for a table column.


   .. method:: filter_columns(self, selections, model)


      Filters the X column from selections.


   .. method:: is_index_in_data(self, model, index)


      Returns True if index is in the data portion of the table.


   .. method:: special_x_values(self, model, column, rows)


      Returns the values from the X column if one is designated otherwise returns None.


   .. method:: x_label(self, model)


      Returns the label of the X column, if available.


   .. method:: _map_column_to_source(proxy_model, proxy_column)
      :staticmethod:


      Maps a proxy model column to source model.


   .. method:: _map_column_from_source(proxy_model, source_column)
      :staticmethod:


      Maps a source model column to proxy model.



