:mod:`spinetoolbox.widgets.manage_db_items_dialog`
==================================================

.. py:module:: spinetoolbox.widgets.manage_db_items_dialog

.. autoapi-nested-parse::

   Classes for custom QDialogs to add edit and remove database items.

   :author: M. Marin (KTH)
   :date:   13.5.2018



Module Contents
---------------

.. py:class:: ManageItemsDialog(parent, db_mngr)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   A dialog with a CopyPasteTableView and a QDialogButtonBox. Base class for all
   dialogs to query user's preferences for adding/editing/managing data items.

   .. attribute:: parent

      data store widget

      :type: DataStoreForm

   .. attribute:: db_mngr

      

      :type: SpineDBManager

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: resize_window_to_columns(self, height=None)



   .. method:: _handle_model_data_changed(self, top_left, bottom_right, roles)


      Reimplement in subclasses to handle changes in model data.


   .. method:: set_model_data(self, index, data)


      Update model data.


   .. method:: _handle_model_reset(self)


      Resize columns and form.



.. py:class:: GetObjectClassesMixin

   Provides a method to retrieve object classes for AddObjectsDialog and AddRelationshipClassesDialog.

   .. method:: make_db_map_obj_cls_lookup(self)



   .. method:: object_class_name_list(self, row)


      Return a list of object class names present in all databases selected for given row.
      Used by `ManageObjectsDelegate`.



.. py:class:: GetObjectsMixin

   Provides a method to retrieve objects for AddRelationshipsDialog and EditRelationshipsDialog.

   .. method:: make_db_map_obj_lookup(self)



   .. method:: make_db_map_rel_cls_lookup(self)



   .. method:: object_name_list(self, row, column)


      Return a list of object names present in all databases selected for given row.
      Used by `ManageRelationshipsDelegate`.



.. py:class:: ShowIconColorEditorMixin

   Provides methods to show an `IconColorEditor` upon request.

   .. method:: show_icon_color_editor(self, index)



   .. method:: create_object_pixmap(self, object_class_name)




.. py:class:: CommitDialog(parent, *db_names)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   A dialog to query user's preferences for new commit.

   .. attribute:: db_names

      database names

      :type: Iterable

   Initialize class

   .. method:: receive_text_changed(self)


      Called when text changes in the commit msg text edit.
      Enable/disable commit button accordingly.



