:mod:`spinetoolbox.mvcmodels.empty_row_model`
=============================================

.. py:module:: spinetoolbox.mvcmodels.empty_row_model

.. autoapi-nested-parse::

   Contains a table model with an empty last row.

   :authors: M. Marin (KTH)
   :date:   20.5.2018



Module Contents
---------------

.. py:class:: EmptyRowModel(parent=None, header=None)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A table model with a last empty row.

   Init class.

   .. method:: canFetchMore(self, parent=QModelIndex())



   .. method:: fetchMore(self, parent=QModelIndex())



   .. method:: flags(self, index)


      Return default flags except if forcing defaults.


   .. method:: set_default_row(self, **kwargs)


      Set default row data.


   .. method:: clear(self)



   .. method:: reset_model(self, main_data=None)



   .. method:: _handle_data_changed(self, top_left, bottom_right, roles=None)


      Insert a new last empty row in case the previous one has been filled
      with any data other than the defaults.


   .. method:: removeRows(self, row, count, parent=QModelIndex())


      Don't remove the last empty row.


   .. method:: _handle_rows_inserted(self, parent, first, last)


      Handle rowsInserted signal.


   .. method:: set_rows_to_default(self, first, last=None)


      Set default data in newly inserted rows.



