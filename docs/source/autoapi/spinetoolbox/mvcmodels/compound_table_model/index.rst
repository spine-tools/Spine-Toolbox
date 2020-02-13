:mod:`spinetoolbox.mvcmodels.compound_table_model`
==================================================

.. py:module:: spinetoolbox.mvcmodels.compound_table_model

.. autoapi-nested-parse::

   Models that vertically concatenate two or more table models.

   :authors: M. Marin (KTH)
   :date:   9.10.2019



Module Contents
---------------

.. py:class:: CompoundTableModel(parent, header=None)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A model that concatenates several sub table models vertically.

   Initializes model.

   :param parent: the parent object
   :type parent: QObject

   .. method:: map_to_sub(self, index)


      Returns an equivalent submodel index.

      :param index: the compound model index.
      :type index: QModelIndex

      :returns: the equivalent index in one of the submodels
      :rtype: QModelIndex


   .. method:: map_from_sub(self, sub_model, sub_index)


      Returns an equivalent compound model index.

      :param sub_model: the submodel
      :type sub_model: MinimalTableModel
      :param sub_index: the submodel index.
      :type sub_index: QModelIndex

      :returns: the equivalent index in the compound model
      :rtype: QModelIndex


   .. method:: item_at_row(self, row)


      Returns the item at given row.

      :param row:
      :type row: int

      :returns: object


   .. method:: sub_model_at_row(self, row)


      Returns the submodel corresponding to the given row in the compound model.

      :param row:
      :type row: int

      :returns: MinimalTableModel


   .. method:: refresh(self)


      Refreshes the layout by computing a new row map.


   .. method:: do_refresh(self)


      Recomputes the row and inverse row maps.


   .. method:: _append_row_map(self, row_map)


      Appends given row map to the tail of the model.

      :param row_map: tuples (model, row number)
      :type row_map: list


   .. method:: _row_map_for_model(model)
      :staticmethod:


      Returns row map for given model.
      The base class implementation just returns all model rows.

      :param model:
      :type model: MinimalTableModel

      :returns: tuples (model, row number)
      :rtype: list


   .. method:: canFetchMore(self, parent=QModelIndex())


      Returns True if any of the submodels that haven't been fetched yet can fetch more.


   .. method:: fetchMore(self, parent=QModelIndex())


      Fetches the next sub model and increments the fetched counter.


   .. method:: flags(self, index)



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: rowCount(self, parent=QModelIndex())


      Returns the sum of rows in all models.


   .. method:: batch_set_data(self, indexes, data)


      Sets data for indexes in batch.
      Distributes indexes and values among the different submodels
      and calls batch_set_data on each of them.


   .. method:: insertRows(self, row, count, parent=QModelIndex())


      Insert count rows after the given row under the given parent.
      Localizes the appropriate submodel and calls insertRows on it.



.. py:class:: CompoundWithEmptyTableModel

   Bases: :class:`spinetoolbox.mvcmodels.compound_table_model.CompoundTableModel`

   A compound parameter table model where the last model is an empty row model.

   .. method:: single_models(self)
      :property:



   .. method:: empty_model(self)
      :property:



   .. method:: _create_single_models(self)
      :abstractmethod:


      Returns a list of single models.


   .. method:: _create_empty_model(self)
      :abstractmethod:


      Returns an empty model.


   .. method:: init_model(self)


      Initializes the compound model. Basically populates the sub_models list attribute
      with the result of _create_single_models and _create_empty_model.


   .. method:: connect_model_signals(self)


      Connects signals so changes in the submodels are acknowledge by the compound.


   .. method:: _recompute_empty_row_map(self)


      Recomputeds the part of the row map corresponding to the empty model.


   .. method:: _handle_empty_rows_removed(self, parent, empty_first, empty_last)


      Runs when rows are removed from the empty model.
      Updates row_map, then emits rowsRemoved so the removed rows are no longer visible.


   .. method:: _handle_empty_rows_inserted(self, parent, empty_first, empty_last)


      Runs when rows are inserted to the empty model.
      Updates row_map, then emits rowsInserted so the new rows become visible.


   .. method:: _handle_single_model_reset(self, single_model)


      Runs when one of the single models is reset.
      Updates row_map, then emits rowsInserted so the new rows become visible.


   .. method:: _insert_single_row_map(self, single_row_map)


      Inserts given row map just before the empty model's.


   .. method:: clear_model(self)


      Clears the model.



