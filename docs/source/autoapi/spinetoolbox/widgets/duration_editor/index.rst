:mod:`spinetoolbox.widgets.duration_editor`
===========================================

.. py:module:: spinetoolbox.widgets.duration_editor

.. autoapi-nested-parse::

   An editor widget for editing duration database (relationship) parameter values.

   :author: A. Soininen (VTT)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: DurationEditor(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   An editor widget for Duration type parameter values.

   .. attribute:: parent

      a parent widget

      :type: QWidget

   .. method:: _change_duration(self)


      Updates the value being edited.


   .. method:: set_value(self, value)


      Sets the value for editing.


   .. method:: value(self)


      Returns the current Duration.



