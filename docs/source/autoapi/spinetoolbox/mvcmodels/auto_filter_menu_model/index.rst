:mod:`spinetoolbox.mvcmodels.auto_filter_menu_model`
====================================================

.. py:module:: spinetoolbox.mvcmodels.auto_filter_menu_model

.. autoapi-nested-parse::

   A model for the auto filter menu widget.

   :authors: M. Marin (KTH)
   :date:   7.10.2019



Module Contents
---------------

.. py:class:: AutoFilterMenuItem(checked, value, classes=())

   An item for the auto filter menu.

   Init class.

   :param checked: the checked status, checked if not filtered
   :type checked: int
   :param value: the value
   :param classes: the entity classes where the value is found
   :type classes: tuple

   .. method:: __repr__(self)




.. py:class:: AutoFilterMenuItemModel(parent=None, fetch_step=32)

   Bases: :class:`PySide2.QtCore.QStringListModel`

   Base class for filter menu widget models.

   Init class.

   .. method:: canFetchMore(self, parent=QModelIndex())


      Returns whether or not there're unfetched rows.


   .. method:: fetchMore(self, parent=QModelIndex())


      Fetches at most _fetch_step rows.


   .. method:: flags(self, index)


      Make the items non-editable.


   .. method:: rowCount(self, parent=QModelIndex())


      Returns number of rows.


   .. method:: index(self, row, column, parent=QModelIndex())


      Returns an index for this model, with the corresponding AutoFilterMenuItem in the internal pointer.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Handle the check state role.


   .. method:: toggle_checked_state(self, index)
      :abstractmethod:


      Toggle checked state of given index.
      Must be reimplemented in subclasses.


   .. method:: reset_model(self, data=None)


      Resets model.

      :param data: a list of AutoFilterMenuItem
      :type data: list



.. py:class:: AutoFilterMenuAllItemModel(parent=None, fetch_step=32)

   Bases: :class:`spinetoolbox.mvcmodels.auto_filter_menu_model.AutoFilterMenuItemModel`

   A model for the 'All' item in the auto filter menu.

   Init class.

   .. attribute:: checked_state_changed
      

      

   .. method:: set_checked_state(self, state)


      Sets the checked state for the item.


   .. method:: toggle_checked_state(self, index)


      Toggle checked state and emit checked_state_changed.



.. py:class:: AutoFilterMenuValueItemModel(parent=None, fetch_step=32)

   Bases: :class:`spinetoolbox.mvcmodels.auto_filter_menu_model.AutoFilterMenuItemModel`

   A model for the value items in the auto filter menu.

   Init class.

   .. attribute:: all_checked_state_changed
      

      

   .. method:: _handle_rows_inserted(self, parent, first, last)


      Builds the row map and call the method that emits all_checked_state_changed appropriatly.


   .. method:: map_to_src(self, index)


      Maps an index using the row map.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the data from the mapped index, as in a filter.


   .. method:: rowCount(self, parent=QModelIndex())


      Returns the length of the row map.


   .. method:: filter_accepts_row(self, row)


      Returns whether or not the row passes the filter, and update the checked count
      so we know how many items are checked for emitting all_checked_state_changed.


   .. method:: set_filter_reg_exp(self, regexp)


      Sets the regular expression to filter row values.


   .. method:: refresh(self)


      Rebuilds the row map so as to update the filter.
      Called when the filter regular expression changes.


   .. method:: build_row_map(self)


      Buils the row map while applying the filter to each row.


   .. method:: set_all_items_checked_state(self, state)


      Set the checked state for all items.


   .. method:: toggle_checked_state(self, index)


      Toggle checked state of given index.


   .. method:: emit_all_checked_state_changed(self)


      Emits signal depending on how many items are checked.


   .. method:: reset_model(self, data=None)


      Resets model.


   .. method:: get_auto_filter(self)


      Returns the output of the auto filter.

      :returns:

                An empty dictionary if *all* values are accepted; None if *no* values are accepted;
                    and a dictionary mapping tuples (db_map, class_id) to a set of values if *some* are accepted.
      :rtype: dict, NoneType



