:mod:`spinetoolbox.widgets.time_pattern_editor`
===============================================

.. py:module:: spinetoolbox.widgets.time_pattern_editor

.. autoapi-nested-parse::

   An editor widget for editing a time pattern type (relationship) parameter values.

   :author: A. Soininen (VTT)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: TimePatternEditor(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for editing time patterns.

   .. attribute:: parent

      

      :type: QWidget

   .. method:: _show_table_context_menu(self, pos)



   .. method:: set_value(self, value)


      Sets the parameter value to be edited.


   .. method:: value(self)


      Returns the parameter value currently being edited.



