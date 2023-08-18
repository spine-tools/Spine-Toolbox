..  Parameter value editor

**********************
Parameter Value Editor
**********************

Parameter value editor is used to edit object and relationship parameter values
such as time series, time patterns or durations.
It can also convert between different value types, e.g. from a time series to a time pattern.

The editor can be opened by right clicking on the value field that you want to edit
in a Spine database editor and selecting **Edit...** from the popup menu.
In most cases the editor can be opened again by double clicking an existing value.
With plain values like strings and floats this won't be work since double clicking
starts the text editor in that field.

Choosing value type
-------------------

The combo box at the top of the editor window allows changing the type of the current value.

.. image:: img/value_editor_parameter_type.png
   :align: center

Plain values
------------

The simplest parameter values are of the *Plain value* type.
The editor window lets you to write a number or string directly to the input field
or set it to true, false or null as needed.

.. image:: img/value_editor_plain.png
   :align: center
   :width: 70%

Numbers and strings can also be inserted without going through the value editor by double clicking
on a value field. If the users input is a number like 3.14, the value type will be interpreted
as *number or string*. If the input is a string like "ok", the value type will automatically be set as *string*.

Maps
----

Maps are versatile nested data structures designed to contain complex data
including one and multi dimensional indexed arrays.
In Parameter value editor a map is shown as a table where the last non-empty cell on each row
contains the value while the preceding cells contain the value's indexes.

.. image:: img/value_editor_map.png
   :align: center

The extra gray column on the right allows expanding the map with a new dimension.
You can append a value to the map by editing the bottom gray row.
The reddish cells are merely a guide for the eye to indicate that the map has different nesting depths.

A **Right click** popup menu gives options to open a value editor for individual cells,
plot individual and multiple cells, insert/remove rows or columns (effectively changing
map's dimensions), trim empty columns from the right hand side and to copy and paste data.
Copying and pasting data works between cells and external programs and can be also done
using the usual **Ctrl+C** and **Ctrl+V** keyboard shortcuts.

The default name for new columns is *x*. Index names can however be modified. If a column
holds both indices and data, the column header can also be modified. The last column of a
map has to always contain values and therefore the header can't be modified from the default
name *Value*.

**Convert leaves to time series** 'compacts' the map by converting the last dimension into time series.
This works only if the last dimension's type is datetime.
For example the following map contains two time dimensions.
Since the indexes are datetimes, the 'inner' dimension can be converted to time series.

.. image:: img/value_editor_map_before_conversion.png
   :align: center
   :width: 70%

After clicking **Convert leaves to time series** the map looks like this:

.. image:: img/value_editor_map_after_conversion.png
   :align: center
   :width: 70%

Time series
-----------

There are two types of time series: *variable* and *fixed resolution*.
Variable resolution means that the time stamps can be arbitrary
while in fixed resolution series the time steps between consecutive stamps are fixed.

.. image:: img/value_editor_time_series_fixed.png
   :align: center

.. image:: img/value_editor_time_series_variable.png
   :align: center

The editor window is split into two in both cases.
The left side holds all the options and a table with all the data
while the right side shows a plot of the series.
The plot is not editable and is for visualization purposes only.

In the table rows can be added or removed from a popup menu available by a **right click**.
Editing the last gray row appends a new value to the series.
Data can be copied and pasted by **Ctrl+C** and **Ctrl+V**.
Copying from/to an external spreadsheet program is supported.

The time steps of a fixed resolution series are edited by the *Start time* and *Resolution* fields.
The format for the start time is `ISO8601 <https://en.wikipedia.org/wiki/ISO_8601>`_.
The *Resolution* field takes a single time step or a comma separated list of steps.
If a list of resolution steps is provided then the steps are repeated so as to fit the data in the table.

The *Ignore year* option available for both variable and fixed resolution time series
allows the time series to be used independent of the year.
Only the month, day and time information is used by the model.

The *Repeat* option means that the time series is cycled,
i.e. it starts from the beginning once the time steps run out.

Time patterns
-------------

The time pattern editor holds a single table which shows the *time period* on the right column
and the corresponding values on the left.
Inserting/removing rows and copy-pasting works as in the time series editor.

.. image:: img/value_editor_time_pattern.png
   :align: center

Time periods consist of the following elements:

- An *interval* of time in a given *time-unit*.
  The format is ``Ua-b``, where ``U`` is either ``Y`` (for year), ``M`` (for month), ``D`` (for day), ``WD`` (for weekday),
  ``h`` (for hour), ``m`` (for minute), or ``s`` (for second);
  and ``a`` and ``b`` are two integers corresponding to the lower and upper bound, respectively.
- An *intersection* of intervals.
  The format is ``s1;s2;...``,
  where ``s1``, ``s2``, ..., are intervals as described above.
- A *union of ranges*.
  The format is ``r1,r2,...``,
  where ``r1``, ``r2``, ..., are either intervals or intersections of intervals as described above.

Arrays
------

Arrays are lists of values of a single type.
Their editor is split into two:
the left side holds the actual array while the right side contains a plot of the array values
versus the values' positions within the array.
Note that not all value types can be plotted.
The type can be selected from the *Value type* combobox.
Inserting/removing rows and copy-pasting works as in the time series editor.

.. image:: img/value_editor_array.png
   :align: center

Datetimes
---------

The datetime value should be entered in `ISO8601 <https://en.wikipedia.org/wiki/ISO_8601>`_ format.
Clicking small arrow on right end of the input field opens up a calendar that can be used to select a date.

.. image:: img/value_editor_datetime.png
   :align: center
   :width: 70%

Durations
---------

A single value or a comma separated list of time durations can be entered to the *Duration* field.

.. image:: img/value_editor_duration.png
   :align: center
   :width: 70%
