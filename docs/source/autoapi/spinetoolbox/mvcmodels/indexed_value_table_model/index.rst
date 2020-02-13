:mod:`spinetoolbox.mvcmodels.indexed_value_table_model`
=======================================================

.. py:module:: spinetoolbox.mvcmodels.indexed_value_table_model

.. autoapi-nested-parse::

   A model for indexed parameter values, used by the parameter value editors.

   :authors: A. Soininen (VTT)
   :date:   18.6.2019



Module Contents
---------------

.. py:class:: IndexedValueTableModel(value, index_header, value_header)

   Bases: :class:`PySide2.QtCore.QAbstractTableModel`

   A base class for time pattern and time series models.

   :param value: a parameter value
   :type value: TimePattern, TimeSeriesFixedStep, TimeSeriesVariableStep
   :param index_header: a header for the index column
   :type index_header: str
   :param value_header: a header for the value column
   :type value_header: str

   .. method:: columnCount(self, parent=QModelIndex())


      Returns the number of columns which is two.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the data at index for given role.


   .. method:: headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole)


      Returns a header.


   .. method:: reset(self, value)


      Resets the model.


   .. method:: rowCount(self, parent=QModelIndex())


      Returns the number of rows.


   .. method:: value(self)
      :property:


      Returns the parameter value associated with the model.



