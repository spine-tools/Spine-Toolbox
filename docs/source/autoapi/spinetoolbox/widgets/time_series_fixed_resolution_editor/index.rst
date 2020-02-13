:mod:`spinetoolbox.widgets.time_series_fixed_resolution_editor`
===============================================================

.. py:module:: spinetoolbox.widgets.time_series_fixed_resolution_editor

.. autoapi-nested-parse::

   Contains logic for the fixed step time series editor widget.

   :author: A. Soininen (VTT)
   :date:   14.6.2019



Module Contents
---------------

.. function:: _resolution_to_text(resolution)

   Converts a list of durations into a string of comma-separated durations.


.. function:: _text_to_resolution(text)

   Converts a comma-separated string of durations into a resolution array.


.. py:class:: TimeSeriesFixedResolutionEditor(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for editing time series data with a fixed time step.

   .. attribute:: parent

      a parent widget

      :type: QWidget

   .. method:: _resolution_changed(self)


      Updates the models after resolution change.


   .. method:: _show_table_context_menu(self, pos)


      Shows the table's context menu.


   .. method:: _select_date(self, selected_date)



   .. method:: set_value(self, value)


      Sets the parameter value for editing in this widget.


   .. method:: _show_calendar(self)



   .. method:: _start_time_changed(self)


      Updates the model due to start time change.


   .. method:: _update_plot(self, topLeft=None, bottomRight=None, roles=None)


      Updated the plot.


   .. method:: value(self)


      Returns the parameter value currently being edited.



