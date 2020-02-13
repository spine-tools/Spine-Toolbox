:mod:`spinetoolbox.widgets.object_name_list_editor`
===================================================

.. py:module:: spinetoolbox.widgets.object_name_list_editor

.. autoapi-nested-parse::

   Contains the ObjectNameListEditor class.


   :author: M. Marin (KTH)
   :date:   27.11.2019



Module Contents
---------------

.. py:class:: SearchBarDelegate

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A custom delegate to use with ObjectNameListEditor.

   .. attribute:: data_committed
      

      

   .. method:: setModelData(self, editor, model, index)



   .. method:: createEditor(self, parent, option, index)



   .. method:: updateEditorGeometry(self, editor, option, index)



   .. method:: close_editor(self, editor, index, model)



   .. method:: eventFilter(self, editor, event)




.. py:class:: ObjectNameListEditor(parent, index, object_class_names, object_names_lists, current_object_names)

   Bases: :class:`spinetoolbox.widgets.manage_db_items_dialog.ManageItemsDialog`

   A dialog to select the object name list for a relationship using Google-like search bars.

   Initializes widget.

   :param parent:
   :type parent: DataStoreForm
   :param index:
   :type index: QModelIndex
   :param object_class_names: string object class names
   :type object_class_names: list
   :param object_names_lists: lists of string object names
   :type object_names_lists: list
   :param current_object_names:
   :type current_object_names: list

   .. method:: init_model(self, object_class_names, object_names_lists, current_object_names)



   .. method:: accept(self)




