:mod:`spinetoolbox.mvcmodels.time_pattern_model`
================================================

.. py:module:: spinetoolbox.mvcmodels.time_pattern_model

.. autoapi-nested-parse::

   A model for time patterns, used by the parameter value editors.

   :authors: A. Soininen (VTT)
   :date:   4.7.2019



Module Contents
---------------

.. py:class:: TimePatternModel(value)

   Bases: :class:`spinetoolbox.mvcmodels.indexed_value_table_model.IndexedValueTableModel`

   A model for time pattern type parameter values.

   :param value: a time pattern value
   :type value: TimePattern

   .. method:: flags(self, index)


      Returns flags at index.


   .. method:: insertRows(self, row, count, parent=QModelIndex())


      Inserts new time period - value pairs into the pattern.

      New time periods are initialized to empty strings and the corresponding values to zeros.

      :param row: an index where to insert the new data
      :type row: int
      :param count: number of time period - value pairs to insert
      :type count: int
      :param parent: an index to a parent model
      :type parent: QModelIndex

      :returns: True if the operation was successful


   .. method:: removeRows(self, row, count, parent=QModelIndex())


      Removes time period - value pairs from the pattern.

      :param row: an index where to remove the data
      :type row: int
      :param count: number of time period - value pairs to remove
      :type count: int
      :param parent: an index to a parent model
      :type parent: QModelIndex

      :returns: True if the operation was successful


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Sets a time period or a value in the pattern.

      Column index 0 corresponds to the time periods while 1 corresponds to the values.

      :param index: an index to the model
      :type index: QModelIndex
      :param value: a new time period or value
      :type value: str, float
      :param role: a role
      :type role: int

      :returns: True if the operation was successful


   .. method:: batch_set_data(self, indexes, values)


      Sets data for several indexes at once.

      :param indexes: a sequence of model indexes
      :type indexes: Sequence
      :param values: a sequence of time periods/floats corresponding to the indexes
      :type values: Sequence



