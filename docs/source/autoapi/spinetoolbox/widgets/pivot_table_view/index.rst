:mod:`spinetoolbox.widgets.pivot_table_view`
============================================

.. py:module:: spinetoolbox.widgets.pivot_table_view

.. autoapi-nested-parse::

   Custom QTableView classes that support copy-paste and the like.

   :author: M. Marin (KTH)
   :date:   18.5.2018



Module Contents
---------------

.. py:class:: PivotTableView(parent=None)

   Bases: :class:`PySide2.QtWidgets.QTableView`

   Custom QTableView class with pivot capabilities.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the class.

   .. method:: clipboard_data_changed(self)



   .. method:: keyPressEvent(self, event)


      Copy and paste to and from clipboard in Excel-like format.



