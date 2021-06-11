..  Plotting
    Created: 15.8.2019

Plotting
========

Basic data visualization is available in the Spine database editors.
Currently, it is possible to plot scalar values
as well as time series, arrays and one dimensional maps with some limitations.

To plot a column, select the values from a table and then *Plot* from the **right click** popup menu.

.. image:: img/plotting_popup_menu.png
   :align: center

.. image:: img/plotting_window_single_column.png
   :align: center

Selecting data in multiple columns plots the selection in a single window.

To add a plot to an existing window select the target plot window
from the *Plot in window* submenu.

.. image:: img/plotting_popup_menu_plot_in_window.png
   :align: center

.. image:: img/plotting_window_added_plot.png
   :align: center

X column in pivot table
-----------------------

It is possible to plot a column of scalar values against a designated X column
in the pivot table.

To set a column as the X column **right click** the top empty area above the column header
and select *Use as X* from the popup menu.
*(X)* in the topmost cell indicates that the column is designated as the X axis.

.. image:: img/plotting_use_as_x_popup.png
   :align: center

When selecting and plotting other columns in the same table the data will be plotted against
the values in the X column instead of row numbers.