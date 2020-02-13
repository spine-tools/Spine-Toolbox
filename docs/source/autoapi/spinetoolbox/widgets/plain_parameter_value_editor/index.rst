:mod:`spinetoolbox.widgets.plain_parameter_value_editor`
========================================================

.. py:module:: spinetoolbox.widgets.plain_parameter_value_editor

.. autoapi-nested-parse::

   An editor widget for editing plain number database (relationship) parameter values.

   :author: A. Soininen (VTT)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: _ValueModel(value)

   A model to handle the parameter value in the editor.
   Mostly useful because of the handy conversion of strings to floats or booleans.

   :param value: a parameter value
   :type value: float, bool

   .. method:: value(self)
      :property:


      Returns the value held by the model.



.. py:class:: PlainParameterValueEditor(parent_widget=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget to edit float or boolean type parameter values.

   .. attribute:: parent_widget

      a parent widget

      :type: QWidget

   .. method:: set_value(self, value)


      Sets the value to be edited in this widget.


   .. method:: _value_changed(self)


      Updates the model.


   .. method:: value(self)


      Returns the value currently being edited.



