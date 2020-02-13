:mod:`spinetoolbox.widgets.custom_qtableview`
=============================================

.. py:module:: spinetoolbox.widgets.custom_qtableview

.. autoapi-nested-parse::

   Custom QTableView classes that support copy-paste and the like.

   :author: M. Marin (KTH)
   :date:   18.5.2018



Module Contents
---------------

.. py:class:: CopyPasteTableView

   Bases: :class:`PySide2.QtWidgets.QTableView`

   Custom QTableView class with copy and paste methods.

   .. method:: keyPressEvent(self, event)


      Copy and paste to and from clipboard in Excel-like format.


   .. method:: delete_content(self)


      Delete content from editable indexes in current selection.


   .. method:: copy(self)


      Copy current selection to clipboard in excel format.


   .. method:: canPaste(self)



   .. method:: paste(self)


      Paste data from clipboard.


   .. method:: _read_pasted_text(text)
      :staticmethod:


      Parses a tab separated CSV text table.

      :param text: a CSV formatted table
      :type text: str

      :returns: a list of rows


   .. method:: paste_on_selection(self)


      Paste clipboard data on selection, but not beyond.
      If data is smaller than selection, repeat data to fit selection.


   .. method:: paste_normal(self)


      Paste clipboard data, overwriting cells if needed



.. py:class:: PivotTableView(parent=None)

   Bases: :class:`spinetoolbox.widgets.custom_qtableview.CopyPasteTableView`

   Custom QTableView class with pivot capabilities.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the class.


.. py:class:: AutoFilterMenu(parent)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   A widget to show the auto filter 'menu'.

   .. attribute:: parent

      the parent widget.

      :type: QTableView

   Initialize class.

   .. attribute:: asc_sort_triggered
      

      

   .. attribute:: desc_sort_triggered
      

      

   .. attribute:: filter_triggered
      

      

   .. method:: set_data(self, data)


      Set data to show in the menu.


   .. method:: _fix_geometry(self)


      Fix geometry, shrink views as possible.


   .. method:: _handle_ok_action_triggered(self, checked=False)


      Called when user presses Ok.
      Collect selections and emit signal.



.. py:class:: AutoFilterCopyPasteTableView(parent)

   Bases: :class:`spinetoolbox.widgets.custom_qtableview.CopyPasteTableView`

   Custom QTableView class with autofilter functionality.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initializes the view.

   :param parent:
   :type parent: QObject

   .. method:: keyPressEvent(self, event)


      Shows the autofilter menu if the user presses Alt + Down.

      :param event:
      :type event: QEvent


   .. method:: setModel(self, model)


      Disconnects the sectionPressed signal which seems to be connected by the super method.
      Otherwise pressing the header just selects the column.

      :param model:
      :type model: QAbstractItemModel


   .. method:: show_auto_filter_menu(self, logical_index)


      Called when user clicks on a horizontal section header.
      Shows/hides the auto filter widget.

      :param logical_index:
      :type logical_index: int


   .. method:: update_auto_filter(self, auto_filter)


      Called when the user selects Ok in the auto filter menu.
      Sets auto filter in model.

      :param auto_filter:
      :type auto_filter: dict


   .. method:: sort_model_ascending(self)


      Called when the user selects sort ascending in the auto filter widget.


   .. method:: sort_model_descending(self)


      Called when the user selects sort descending in the auto filter widget.



.. py:class:: IndexedParameterValueTableViewBase

   Bases: :class:`spinetoolbox.widgets.custom_qtableview.CopyPasteTableView`

   Custom QTableView base class with copy and paste methods for indexed parameter values.

   .. method:: copy(self)


      Copy current selection to clipboard in CSV format.


   .. method:: _read_pasted_text(text)
      :staticmethod:
      :abstractmethod:


      Reads CSV formatted table.


   .. method:: paste(self)
      :abstractmethod:


      Pastes data from clipboard to selection.


   .. method:: _range(indexes)
      :staticmethod:


      Returns the top left and bottom right corners of selected model indexes.

      :param indexes: a list of selected QModelIndex objects
      :type indexes: list

      :returns: a tuple (top row, bottom row, left column, right column)


   .. method:: _select_pasted(self, indexes)


      Selects the given model indexes.



.. py:class:: TimeSeriesFixedResolutionTableView

   Bases: :class:`spinetoolbox.widgets.custom_qtableview.IndexedParameterValueTableViewBase`

   A QTableView for fixed resolution time series table.

   .. method:: paste(self)


      Pastes data from clipboard.


   .. method:: _read_pasted_text(text)
      :staticmethod:


      Parses the given CSV table.

      Parsing is locale aware.

      :param text: a CSV table containing numbers
      :type text: str

      :returns: A list of floats


   .. method:: _paste_to_values_column(self, values, first_row, paste_length)


      Pastes data to the Values column.

      :param values: a list of float values to paste
      :type values: list
      :param first_row: index of the first row where to paste
      :type first_row: int
      :param paste_length: length of the paste selection (can be different from len(values))
      :type paste_length: int

      :returns: A tuple (list(pasted indexes), list(pasted values))



.. py:class:: IndexedValueTableView

   Bases: :class:`spinetoolbox.widgets.custom_qtableview.IndexedParameterValueTableViewBase`

   A QTableView class with for variable resolution time series and time patterns.

   .. method:: paste(self)


      Pastes data from clipboard.


   .. method:: _paste_two_columns(self, data_indexes, data_values, first_row, paste_length)


      Pastes data indexes and values.

      :param data_indexes: a list of data indexes (time stamps/durations)
      :type data_indexes: list
      :param data_values: a list of data values
      :type data_values: list
      :param first_row: first row index
      :type first_row: int
      :param paste_length: selection length for pasting
      :type paste_length: int

      :returns: a tuple (modified model indexes, modified model values)


   .. method:: _paste_single_column(self, values, first_row, first_column, paste_length)


      Pastes a single column of data

      :param values: a list of data to paste (data indexes or values)
      :type values: list
      :param first_row: first row index
      :type first_row: int
      :param paste_length: selection length for pasting
      :type paste_length: int

      :returns: a tuple (modified model indexes, modified model values)


   .. method:: _read_pasted_text(text)
      :staticmethod:


      Parses a given CSV table

      :param text: a CSV table
      :type text: str

      :returns: a tuple (data indexes, data values)



