:mod:`spinetoolbox.mvcmodels.pivot_model`
=========================================

.. py:module:: spinetoolbox.mvcmodels.pivot_model

.. autoapi-nested-parse::

   Provides PivotModel.

   :author: P. Vennström (VTT)
   :date:   1.11.2018



Module Contents
---------------

.. py:class:: PivotModel

   .. method:: reset_model(self, data, index_ids=(), rows=(), columns=(), frozen=(), frozen_value=())


      Resets the model.


   .. method:: clear_model(self)



   .. method:: update_model(self, data)



   .. method:: add_to_model(self, data)



   .. method:: remove_from_model(self, data)



   .. method:: _check_pivot(self, rows, columns, frozen, frozen_value)


      Checks if given pivot is valid.

      :returns: error message or None if no error
      :rtype: str, NoneType


   .. method:: _index_key_getter(self, indexes)


      Returns an itemgetter that always returns tuples from list of indexes


   .. method:: _get_unique_index_values(self, indexes)


      Returns unique indexes that match the frozen condition.

      :param indexes:
      :type indexes: list

      Returns
          list


   .. method:: set_pivot(self, rows, columns, frozen, frozen_value)


      Sets pivot.


   .. method:: set_frozen_value(self, value)


      Sets values for the frozen indexes.


   .. method:: get_pivoted_data(self, row_mask, column_mask)


      Returns data for indexes in row_mask and column_mask.

      :param row_mask:
      :type row_mask: list
      :param column_mask:
      :type column_mask: list

      :returns: list(list)


   .. method:: row_key(self, row)



   .. method:: column_key(self, column)



   .. method:: rows(self)
      :property:



   .. method:: columns(self)
      :property:




