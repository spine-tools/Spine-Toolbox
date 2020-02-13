:mod:`spinetoolbox.widgets.add_db_items_dialogs`
================================================

.. py:module:: spinetoolbox.widgets.add_db_items_dialogs

.. autoapi-nested-parse::

   Classes for custom QDialogs to add items to databases.

   :author: M. Marin (KTH)
   :date:   13.5.2018



Module Contents
---------------

.. py:class:: AddItemsDialog(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ManageItemsDialog`

   A dialog to query user's preferences for new db items.

   Init class.

   Args
       parent (DataStoreForm)
       db_mngr (SpineDBManager)
       db_maps (iter) DiffDatabaseMapping instances

   .. method:: connect_signals(self)



   .. method:: remove_selected_rows(self, checked=True)



   .. method:: all_databases(self, row)


      Returns a list of db names available for a given row.
      Used by delegates.



.. py:class:: AddObjectClassesDialog(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ShowIconColorEditorMixin`, :class:`spinetoolbox.widgets.add_db_items_dialogs.AddItemsDialog`

   A dialog to query user's preferences for new object classes.

   Init class.

   Args
       parent (DataStoreForm)
       db_mngr (SpineDBManager)
       db_maps (iter) DiffDatabaseMapping instances

   .. method:: connect_signals(self)



   .. method:: accept(self)


      Collect info from dialog and try to add items.



.. py:class:: AddObjectsDialog(parent, db_mngr, *db_maps, class_name=None, force_default=False)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.GetObjectClassesMixin`, :class:`spinetoolbox.widgets.add_db_items_dialogs.AddItemsDialog`

   A dialog to query user's preferences for new objects.


   Init class.

   Args
       parent (DataStoreForm)
       db_mngr (SpineDBManager)
       db_maps (iter) DiffDatabaseMapping instances
       class_name (str): default object class name
       force_default (bool): if True, defaults are non-editable

   .. method:: accept(self)


      Collect info from dialog and try to add items.



.. py:class:: AddRelationshipClassesDialog(parent, db_mngr, *db_maps, object_class_one_name=None, force_default=False)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.GetObjectClassesMixin`, :class:`spinetoolbox.widgets.add_db_items_dialogs.AddItemsDialog`

   A dialog to query user's preferences for new relationship classes.

   Init class.

   Args
       parent (DataStoreForm)
       db_mngr (SpineDBManager)
       db_maps (iter) DiffDatabaseMapping instances
       object_class_one_name (str): default object class name
       force_default (bool): if True, defaults are non-editable

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: _handle_spin_box_value_changed(self, i)



   .. method:: insert_column(self)



   .. method:: remove_column(self)



   .. method:: _handle_model_data_changed(self, top_left, bottom_right, roles)



   .. method:: accept(self)


      Collect info from dialog and try to add items.



.. py:class:: AddRelationshipsDialog(parent, db_mngr, *db_maps, relationship_class_key=None, object_class_name=None, object_name=None, force_default=False)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.GetObjectsMixin`, :class:`spinetoolbox.widgets.add_db_items_dialogs.AddItemsDialog`

   A dialog to query user's preferences for new relationships.

   Init class.

   Args
       parent (DataStoreForm)
       db_mngr (SpineDBManager)
       db_maps (iter) DiffDatabaseMapping instances
       relationship_class_key (tuple): (class_name, object_class_name_list)
       object_name (str): default object name
       object_class_name (str): default object class name
       force_default (bool): if True, defaults are non-editable

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: call_reset_model(self, index)


      Called when relationship class's combobox's index changes.
      Update relationship_class attribute accordingly and reset model.


   .. method:: reset_model(self)


      Setup model according to current relationship class selected in combobox.


   .. method:: _handle_model_data_changed(self, top_left, bottom_right, roles)



   .. method:: accept(self)


      Collect info from dialog and try to add items.



