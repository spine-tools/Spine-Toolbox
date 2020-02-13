:mod:`spinetoolbox.widgets.tree_view_mixin`
===========================================

.. py:module:: spinetoolbox.widgets.tree_view_mixin

.. autoapi-nested-parse::

   Contains the TreeViewMixin class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: TreeViewMixin(*args, **kwargs)

   Provides object and relationship trees for the data store form.

   .. method:: add_menu_actions(self)


      Adds toggle view actions to View menu.


   .. method:: connect_signals(self)


      Connects signals to slots.


   .. method:: init_models(self)


      Initializes models.


   .. method:: _handle_object_tree_selection_changed(self, selected, deselected)


      Updates object filter and sets default rows.


   .. method:: _handle_relationship_tree_selection_changed(self, selected, deselected)


      Updates relationship filter and sets default rows.


   .. method:: _db_map_items(indexes)
      :staticmethod:


      Groups items from given tree indexes by db map.

      :returns: lists of dictionary items keyed by DiffDatabaseMapping
      :rtype: dict


   .. method:: _db_map_class_id_data(db_map_data)
      :staticmethod:


      Returns a new dictionary where the class id is also part of the key.

      :returns: lists of dictionary items keyed by tuple (DiffDatabaseMapping, integer class id)
      :rtype: dict


   .. method:: _extend_merge(left, right)
      :staticmethod:


      Returns a new dictionary by uniting left and right.

      :returns: lists of dictionary items keyed by DiffDatabaseMapping
      :rtype: dict


   .. method:: _update_object_filter(self)


      Updates filters object filter according to object tree selection.


   .. method:: _update_relationship_filter(self)


      Update filters relationship filter according to relationship tree selection.


   .. method:: edit_object_tree_items(self, current)


      Starts editing the given index in the object tree.


   .. method:: edit_relationship_tree_items(self, current)


      Starts editing the given index in the relationship tree.


   .. method:: show_object_tree_context_menu(self, pos)


      Shows the context menu for object tree.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_relationship_tree_context_menu(self, pos)


      Shows the context for relationship tree.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: fully_expand_selection(self)



   .. method:: fully_collapse_selection(self)



   .. method:: find_next_relationship(self, index)


      Expands next occurrence of a relationship in object tree.


   .. method:: call_show_add_objects_form(self, index)



   .. method:: call_show_add_relationship_classes_form(self, index)



   .. method:: call_show_add_relationships_form(self, index)



   .. method:: show_add_object_classes_form(self, checked=False)


      Shows dialog to let user select preferences for new object classes.


   .. method:: show_add_objects_form(self, checked=False, class_name='')


      Shows dialog to let user select preferences for new objects.


   .. method:: show_add_relationship_classes_form(self, checked=False, object_class_one_name=None)


      Shows dialog to let user select preferences for new relationship class.


   .. method:: show_add_relationships_form(self, checked=False, relationship_class_key=(), object_class_name='', object_name='')


      Shows dialog to let user select preferences for new relationships.


   .. method:: show_edit_object_classes_form(self, checked=False)



   .. method:: show_edit_objects_form(self, checked=False)



   .. method:: show_edit_relationship_classes_form(self, checked=False)



   .. method:: show_edit_relationships_form(self, checked=False)



   .. method:: show_remove_object_tree_items_form(self)


      Shows form to remove items from object treeview.


   .. method:: show_remove_relationship_tree_items_form(self)


      Shows form to remove items from relationship treeview.


   .. method:: notify_items_changed(self, action, item_type, db_map_data)


      Enables or disables actions and informs the user about what just happened.


   .. method:: receive_object_classes_added(self, db_map_data)



   .. method:: receive_objects_added(self, db_map_data)



   .. method:: receive_relationship_classes_added(self, db_map_data)



   .. method:: receive_relationships_added(self, db_map_data)



   .. method:: receive_object_classes_updated(self, db_map_data)



   .. method:: receive_objects_updated(self, db_map_data)



   .. method:: receive_relationship_classes_updated(self, db_map_data)



   .. method:: receive_relationships_updated(self, db_map_data)



   .. method:: receive_object_classes_removed(self, db_map_data)



   .. method:: receive_objects_removed(self, db_map_data)



   .. method:: receive_relationship_classes_removed(self, db_map_data)



   .. method:: receive_relationships_removed(self, db_map_data)




