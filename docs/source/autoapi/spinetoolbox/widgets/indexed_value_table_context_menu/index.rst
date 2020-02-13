:mod:`spinetoolbox.widgets.indexed_value_table_context_menu`
============================================================

.. py:module:: spinetoolbox.widgets.indexed_value_table_context_menu

.. autoapi-nested-parse::

   Offers a convenience function for time pattern and time series editor widgets.

   :author: A. Soininen (VTT)
   :date:   5.7.2019



Module Contents
---------------

.. function:: handle_table_context_menu(click_pos, table_view, model, parent_widget)

   Shows a context menu for parameter value tables and handles the selection.

   :param click_pos {QPoint): position from the context menu event
   :param table_view: the table widget
   :type table_view: QTableView
   :param model: a model
   :type model: TimePatternModel, TimeSeriesModelFixedResolution, TimeSeriesModelVariableResolution
   :param parent_widget (QWidget: context menu's parent widget


.. function:: _remove_rows(selected_rows, model)

   Packs consecutive rows into a single removeRows call.


