:mod:`spinetoolbox.mvcmodels.frozen_table_model`
================================================

.. py:module:: spinetoolbox.mvcmodels.frozen_table_model

.. autoapi-nested-parse::

   Contains FrozenTableModel class.

   :author: P. Vennström (VTT)
   :date:   24.9.2019



Module Contents
---------------

.. py:class:: FrozenTableModel(parent, headers=None, data=None)

   Bases: :class:`PySide2.QtCore.QAbstractItemModel`

   Used by custom_qtableview.FrozenTableView

   :param parent:
   :type parent: TabularViewMixin

   .. method:: parent(self, child=None)



   .. method:: index(self, row, column, parent=QModelIndex())



   .. method:: reset_model(self, data, headers)



   .. method:: clear_model(self)



   .. method:: rowCount(self, parent=QModelIndex())



   .. method:: columnCount(self, parent=QModelIndex())



   .. method:: row(self, index)



   .. method:: data(self, index, role)



   .. method:: headers(self)
      :property:




