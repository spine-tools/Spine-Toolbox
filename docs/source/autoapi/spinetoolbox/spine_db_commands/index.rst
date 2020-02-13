:mod:`spinetoolbox.spine_db_commands`
=====================================

.. py:module:: spinetoolbox.spine_db_commands

.. autoapi-nested-parse::

   QUndoCommand subclasses for modifying the db.

   :authors: M. Marin (KTH)
   :date:   31.1.2020



Module Contents
---------------

.. function:: _cache_to_db_relationship_class(item)


.. function:: _cache_to_db_relationship(item)


.. function:: _cache_to_db_parameter_definition(item)


.. function:: _cache_to_db_parameter_value(item)


.. function:: _cache_to_db_parameter_value_list(item)


.. function:: _cache_to_db_item(item_type, item)


.. function:: _format_item(item_type, item)


.. py:class:: AgedUndoStack

   Bases: :class:`PySide2.QtWidgets.QUndoStack`

   .. method:: redo_age(self)
      :property:



   .. method:: undo_age(self)
      :property:



   .. method:: commands(self)




.. py:class:: CommandBase(db_mngr, db_map)

   Bases: :class:`PySide2.QtWidgets.QUndoCommand`

   :param db_mngr: SpineDBManager instance
   :type db_mngr: SpineDBManager
   :param db_map: DiffDatabaseMapping instance
   :type db_map: DiffDatabaseMapping

   .. method:: age(self)
      :property:



   .. method:: redomethod(func)
      :staticmethod:



   .. method:: receive_items_changed(self, db_map_data)



   .. method:: data(self)
      :abstractmethod:




.. py:class:: AddItemsCommand(db_mngr, db_map, data, item_type)

   Bases: :class:`spinetoolbox.spine_db_commands.CommandBase`

   :param db_mngr: SpineDBManager instance
   :type db_mngr: SpineDBManager
   :param db_map: DiffDatabaseMapping instance
   :type db_map: DiffDatabaseMapping
   :param data: list of dict-items to add
   :type data: list
   :param item_type: the item type
   :type item_type: str

   .. attribute:: _command_name
      

      

   .. attribute:: _method_name
      

      

   .. attribute:: _redo_method_name
      

      

   .. attribute:: _emit_signal_name
      

      

   .. attribute:: _receive_signal_name
      

      

   .. method:: redo(self)



   .. method:: undo(self)



   .. method:: receive_items_changed(self, db_map_data)



   .. method:: data(self)




.. py:class:: AddCheckedParameterValuesCommand(db_mngr, db_map, data)

   Bases: :class:`spinetoolbox.spine_db_commands.AddItemsCommand`


.. py:class:: UpdateItemsCommand(db_mngr, db_map, data, item_type)

   Bases: :class:`spinetoolbox.spine_db_commands.CommandBase`

   :param db_mngr: SpineDBManager instance
   :type db_mngr: SpineDBManager
   :param db_map: DiffDatabaseMapping instance
   :type db_map: DiffDatabaseMapping
   :param data: list of dict-items to update
   :type data: list
   :param item_type: the item type
   :type item_type: str

   .. attribute:: _command_name
      

      

   .. attribute:: _method_name
      

      

   .. attribute:: _emit_signal_name
      

      

   .. method:: _undo_item(self, db_map, redo_item)



   .. method:: redo(self)



   .. method:: undo(self)



   .. method:: data(self)




.. py:class:: UpdateCheckedParameterValuesCommand(db_mngr, db_map, data)

   Bases: :class:`spinetoolbox.spine_db_commands.UpdateItemsCommand`


.. py:class:: SetParameterDefinitionTagsCommand(db_mngr, db_map, data)

   Bases: :class:`spinetoolbox.spine_db_commands.CommandBase`

   .. method:: _undo_item(self, db_map, redo_item)



   .. method:: redo(self)



   .. method:: undo(self)




.. py:class:: RemoveItemsCommand(db_mngr, db_map, typed_data)

   Bases: :class:`spinetoolbox.spine_db_commands.CommandBase`

   :param db_mngr: SpineDBManager instance
   :type db_mngr: SpineDBManager
   :param db_map: DiffDatabaseMapping instance
   :type db_map: DiffDatabaseMapping
   :param typed_data: lists of dict-items to remove keyed by string type
   :type typed_data: dict

   .. attribute:: _undo_method_name
      

      

   .. attribute:: _emit_signal_name
      

      

   .. method:: redo(self)



   .. method:: undo(self)



   .. method:: receive_items_changed(self, db_map_typed_data)



   .. method:: data(self)




