:mod:`spinetoolbox.mvcmodels.parameter_value_list_model`
========================================================

.. py:module:: spinetoolbox.mvcmodels.parameter_value_list_model

.. autoapi-nested-parse::

   A tree model for parameter value lists.

   :authors: M. Marin (KTH)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: EditableMixin

   .. method:: flags(self, column)


      Makes items editable.



.. py:class:: GrayFontMixin

   Paints the text gray.

   .. method:: data(self, column, role=Qt.DisplayRole)




.. py:class:: BoldFontMixin

   Bolds text.

   .. method:: data(self, column, role=Qt.DisplayRole)




.. py:class:: AppendEmptyChildMixin

   Provides a method to append an empty child if needed.

   .. method:: append_empty_child(self, row)


      Append empty child if the row is the last one.



.. py:class:: DBItem(db_map)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_value_list_model.AppendEmptyChildMixin`, :class:`spinetoolbox.mvcmodels.minimal_tree_model.TreeItem`

   An item representing a db.

   Init class.

   Args
       db_mngr (SpineDBManager)
       db_map (DiffDatabaseMapping)

   .. method:: db_mngr(self)
      :property:



   .. method:: fetch_more(self)



   .. method:: empty_child(self)



   .. method:: data(self, column, role=Qt.DisplayRole)


      Shows Spine icon for fun.



.. py:class:: ListItem(db_map, identifier=None, name=None, value_list=())

   Bases: :class:`spinetoolbox.mvcmodels.parameter_value_list_model.GrayFontMixin`, :class:`spinetoolbox.mvcmodels.parameter_value_list_model.BoldFontMixin`, :class:`spinetoolbox.mvcmodels.parameter_value_list_model.AppendEmptyChildMixin`, :class:`spinetoolbox.mvcmodels.parameter_value_list_model.EditableMixin`, :class:`spinetoolbox.mvcmodels.minimal_tree_model.TreeItem`

   A list item.

   .. method:: db_mngr(self)
      :property:



   .. method:: fetch_more(self)



   .. method:: compile_value_list(self)



   .. method:: empty_child(self)



   .. method:: data(self, column, role=Qt.DisplayRole)



   .. method:: set_data(self, column, name)



   .. method:: set_child_data(self, child, value)



   .. method:: update_name_in_db(self, name)



   .. method:: update_value_list_in_db(self, child, value)



   .. method:: add_to_db(self)


      Add item to db.


   .. method:: handle_updated_in_db(self, name, value_list)


      Runs when an item with this id has been updated in the db.


   .. method:: handle_added_to_db(self, identifier, value_list)


      Runs when the item with this name has been added to the db.


   .. method:: reset_value_list(self, value_list)




.. py:class:: ValueItem(value=None)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_value_list_model.GrayFontMixin`, :class:`spinetoolbox.mvcmodels.parameter_value_list_model.EditableMixin`, :class:`spinetoolbox.mvcmodels.minimal_tree_model.TreeItem`

   A value item.

   .. method:: data(self, column, role=Qt.DisplayRole)



   .. method:: set_data(self, column, value)




.. py:class:: ParameterValueListModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_tree_model.MinimalTreeModel`

   A model to display parameter value list data in a tree view.


   :param parent:
   :type parent: DataStoreForm
   :param db_mngr:
   :type db_mngr: SpineDBManager
   :param db_maps: DiffDatabaseMapping instances
   :type db_maps: iter

   Initialize class

   .. attribute:: remove_selection_requested
      

      

   .. attribute:: remove_icon
      

      

   .. method:: receive_parameter_value_lists_added(self, db_map_data)



   .. method:: receive_parameter_value_lists_updated(self, db_map_data)



   .. method:: receive_parameter_value_lists_removed(self, db_map_data)



   .. method:: build_tree(self)


      Initialize the internal data structure of the model.


   .. method:: columnCount(self, parent=QModelIndex())


      Returns the number of columns under the given parent. Always 1.



