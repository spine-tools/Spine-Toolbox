:mod:`spinetoolbox.widgets.parameter_value_editor`
==================================================

.. py:module:: spinetoolbox.widgets.parameter_value_editor

.. autoapi-nested-parse::

   An editor dialog for editing database (relationship) parameter values.

   :author: A. Soininen (VTT)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: _Editor

   Bases: :class:`enum.Enum`

   Indexes for the specialized editors corresponding to the selector combo box and editor stack.

   .. attribute:: PLAIN_VALUE
      :annotation: = 0

      

   .. attribute:: TIME_SERIES_FIXED_RESOLUTION
      :annotation: = 1

      

   .. attribute:: TIME_SERIES_VARIABLE_RESOLUTION
      :annotation: = 2

      

   .. attribute:: TIME_PATTERN
      :annotation: = 3

      

   .. attribute:: DATETIME
      :annotation: = 4

      

   .. attribute:: DURATION
      :annotation: = 5

      


.. py:class:: ParameterValueEditor(parent_index, value_name='', value=None, parent_widget=None)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   Dialog for editing (relationship) parameter values.

   The dialog takes the editable value from a parent model and shows a specialized editor
   corresponding to the value type in a stack widget. The user can change the value type
   by changing the specialized editor using a combo box.
   When the dialog is closed the value from the currently shown specialized editor is
   written back to the parent model.

   .. attribute:: parent_index

      an index to a parameter value in parent_model

      :type: QModelIndex

   .. attribute:: value_name

      name of the value

      :type: str

   .. attribute:: value

      parameter value or None if it should be loaded from parent_index

   .. attribute:: parent_widget

      a parent widget

      :type: QWidget

   .. method:: accept(self)


      Saves the parameter value shown in the currently selected editor widget back to the parent model.


   .. method:: _change_parameter_type(self, selector_index)


      Handles switching between value types.

      Does a rude conversion between fixed and variable resolution time series.
      In other cases, a default 'empty' value is used.

      :param selector_index: an index to the selector combo box
      :type selector_index: int


   .. method:: _select_editor(self, value)


      Shows the editor widget corresponding to the given value type on the editor stack.


   .. method:: _select_default_view(self, message=None)


      Opens the default editor widget. Optionally, displays a warning dialog indicating the problem.

      :param message:
      :type message: str, optional



