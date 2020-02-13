:mod:`spinetoolbox.mvcmodels.time_series_model_fixed_resolution`
================================================================

.. py:module:: spinetoolbox.mvcmodels.time_series_model_fixed_resolution

.. autoapi-nested-parse::

   A model for fixed resolution time series, used by the parameter value editors.

   :authors: A. Soininen (VTT)
   :date:   4.7.2019



Module Contents
---------------

.. py:class:: TimeSeriesModelFixedResolution(series)

   Bases: :class:`spinetoolbox.mvcmodels.indexed_value_table_model.IndexedValueTableModel`

   A model for fixed resolution time series type parameter values.

   .. attribute:: series

      a time series

      :type: TimeSeriesFixedResolution

   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the time stamp or the corresponding value at given model index.

      Column index 0 refers to time stamps while index 1 to values.

      :param index: an index to the model
      :type index: QModelIndex
      :param role: a role
      :type role: int


   .. method:: flags(self, index)


      Returns flags at index.


   .. method:: indexes(self)
      :property:


      Returns the time stamps as an array.


   .. method:: insertRows(self, row, count, parent=QModelIndex())


      Inserts new values to the series.

      The new values are set to zero. Start time or resolution are left unchanged.

      :param row: a numeric index to the first stamp/value to insert
      :type row: int
      :param count: number of stamps/values to insert
      :type count: int
      :param parent: index to a parent model
      :type parent: QModelIndex

      :returns: True if the operation was successful


   .. method:: removeRows(self, row, count, parent=QModelIndex())


      Removes values from the series.

      :param row: a numeric index to the series where to begin removing
      :type row: int
      :param count: how many stamps/values to remove
      :type count: int
      :param parent: an index to the parent model
      :type parent: QModelIndex

      :returns: True if the operation was successful.


   .. method:: reset(self, value)


      Resets the model with new time series data.


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Sets a given value in the series.

      Column index 1 refers to values.
      Note it does not make sense to set the time stamps in fixed resolution series.

      :param index: an index to the model
      :type index: QModelIndex
      :param value: a new stamp or value
      :type value: numpy.datetime64, float
      :param role: a role
      :type role: int

      :returns: True if the operation was successful


   .. method:: batch_set_data(self, indexes, values)


      Sets data for several indexes at once.

      Only the values of the series are modified as the time stamps are immutable.

      :param indexes: a sequence of model indexes
      :type indexes: Sequence
      :param values: a sequence of floats corresponding to the indexes
      :type values: Sequence


   .. method:: set_ignore_year(self, ignore_year)


      Sets the ignore_year option of the time series.


   .. method:: set_repeat(self, repeat)


      Sets the repeat option of the time series.


   .. method:: set_resolution(self, resolution)


      Sets the resolution.


   .. method:: set_start(self, start)


      Sets the start datetime.


   .. method:: values(self)
      :property:


      Returns the values of the time series as an array.



