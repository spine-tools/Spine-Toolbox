:mod:`spinetoolbox.widgets.datetime_editor`
===========================================

.. py:module:: spinetoolbox.widgets.datetime_editor

.. autoapi-nested-parse::

   An editor widget for editing datetime database (relationship) parameter values.

   :author: A. Soininen (VTT)
   :date:   28.6.2019



Module Contents
---------------

.. function:: _QDateTime_to_datetime(dt)

   Converts a QDateTime object to Python's datetime.datetime type.


.. function:: _datetime_to_QDateTime(dt)

   Converts Python's datetime.datetime object to QDateTime.


.. py:class:: DatetimeEditor(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   An editor widget for DateTime type parameter values.

   .. attribute:: parent

      a parent widget

      :type: QWidget

   .. method:: _change_datetime(self, new_datetime)


      Updates the internal DateTime value


   .. method:: set_value(self, value)


      Sets the value to be edited.


   .. method:: value(self)


      Returns the editor's current value.



