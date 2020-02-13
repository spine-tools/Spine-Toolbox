:mod:`spinetoolbox.widgets.time_series_variable_resolution_editor`
==================================================================

.. py:module:: spinetoolbox.widgets.time_series_variable_resolution_editor

.. autoapi-nested-parse::

   Contains logic for the variable resolution time series editor widget.

   :author: A. Soininen (VTT)
   :date:   31.5.2019



Module Contents
---------------

.. py:class:: TimeSeriesVariableResolutionEditor(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for editing variable resolution time series data.

   .. attribute:: parent

      a parent widget

      :type: QWidget

   .. method:: _show_table_context_menu(self, pos)


      Shows the table's context menu.


   .. method:: set_value(self, value)


      Sets the time series being edited.


   .. method:: _update_plot(self, topLeft=None, bottomRight=None, roles=None)


      Updates the plot widget.


   .. method:: value(self)


      Return the time series currently being edited.



