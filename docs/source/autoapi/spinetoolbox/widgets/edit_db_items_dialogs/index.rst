:mod:`spinetoolbox.widgets.edit_db_items_dialogs`
=================================================

.. py:module:: spinetoolbox.widgets.edit_db_items_dialogs

.. autoapi-nested-parse::

   Classes for custom QDialogs to edit items in databases.

   :author: M. Marin (KTH)
   :date:   13.5.2018



Module Contents
---------------

.. py:class:: EditOrRemoveItemsDialog(parent, db_mngr)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ManageItemsDialog`

   .. method:: all_databases(self, row)


      Returns a list of db names available for a given row.
      Used by delegates.



.. py:class:: EditObjectClassesDialog(parent, db_mngr, selected)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ShowIconColorEditorMixin`, :class:`spinetoolbox.widgets.edit_db_items_dialogs.EditOrRemoveItemsDialog`

   A dialog to query user's preferences for updating object classes.

   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the update
   :type db_mngr: SpineDBManager
   :param selected: set of ObjectClassItem instances to edit
   :type selected: set

   .. method:: connect_signals(self)



   .. method:: accept(self)


      Collect info from dialog and try to update items.



.. py:class:: EditObjectsDialog(parent, db_mngr, selected)

   Bases: :class:`spinetoolbox.widgets.edit_db_items_dialogs.EditOrRemoveItemsDialog`

   A dialog to query user's preferences for updating objects.


   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the update
   :type db_mngr: SpineDBManager
   :param selected: set of ObjectItem instances to edit
   :type selected: set

   .. method:: accept(self)


      Collect info from dialog and try to update items.



.. py:class:: EditRelationshipClassesDialog(parent, db_mngr, selected)

   Bases: :class:`spinetoolbox.widgets.edit_db_items_dialogs.EditOrRemoveItemsDialog`

   A dialog to query user's preferences for updating relationship classes.


   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the update
   :type db_mngr: SpineDBManager
   :param selected: set of RelationshipClassItem instances to edit
   :type selected: set

   .. method:: accept(self)


      Collect info from dialog and try to update items.



.. py:class:: EditRelationshipsDialog(parent, db_mngr, selected, class_key)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.GetObjectsMixin`, :class:`spinetoolbox.widgets.edit_db_items_dialogs.EditOrRemoveItemsDialog`

   A dialog to query user's preferences for updating relationships.


   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the update
   :type db_mngr: SpineDBManager
   :param selected: set of RelationshipItem instances to edit
   :type selected: set
   :param class_key: (class_name, object_class_name_list) for identifying the relationship class
   :type class_key: tuple

   .. method:: accept(self)


      Collect info from dialog and try to update items.



.. py:class:: RemoveEntitiesDialog(parent, db_mngr, selected)

   Bases: :class:`spinetoolbox.widgets.edit_db_items_dialogs.EditOrRemoveItemsDialog`

   A dialog to query user's preferences for removing tree items.


   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the removal
   :type db_mngr: SpineDBManager
   :param selected: maps item type (class) to instances
   :type selected: dict

   .. method:: accept(self)


      Collect info from dialog and try to remove items.



.. py:class:: ManageParameterTagsDialog(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ManageItemsDialog`

   A dialog to query user's preferences for managing parameter tags.


   Init class.

   :param parent: data store widget
   :type parent: DataStoreForm
   :param db_mngr: the manager to do the removal
   :type db_mngr: SpineDBManager
   :param db_maps: DiffDatabaseMapping instances
   :type db_maps: iter

   .. method:: all_databases(self, row)


      Returns a list of db names available for a given row.
      Used by delegates.


   .. method:: accept(self)


      Collect info from dialog and try to update, remove, add items.



