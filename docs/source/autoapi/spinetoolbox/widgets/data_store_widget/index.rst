:mod:`spinetoolbox.widgets.data_store_widget`
=============================================

.. py:module:: spinetoolbox.widgets.data_store_widget

.. autoapi-nested-parse::

   Contains the DataStoreForm class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: DataStoreFormBase(db_mngr, *db_urls)

   Bases: :class:`PySide2.QtWidgets.QMainWindow`

   Base class for DataStoreForm

   Initializes form.

   :param db_mngr: The manager to use
   :type db_mngr: SpineDBManager
   :param \*db_urls: Database url, codename.
   :type \*db_urls: tuple

   .. attribute:: msg
      

      

   .. attribute:: msg_error
      

      

   .. method:: add_menu_actions(self)


      Adds actions to View and Edit menu.


   .. method:: connect_signals(self)


      Connects signals to slots.


   .. method:: update_undo_redo_actions(self, index)



   .. method:: update_commit_enabled(self, _clean=False)



   .. method:: show_history_dialog(self, checked=False)



   .. method:: init_models(self)


      Initializes models.


   .. method:: add_message(self, msg)


      Appends regular message to status bar.

      :param msg: String to show in QStatusBar
      :type msg: str


   .. method:: restore_dock_widgets(self)


      Docks all floating and or hidden QDockWidgets back to the window.


   .. method:: _handle_menu_edit_about_to_show(self)


      Runs when the edit menu from the main menubar is about to show.
      Enables or disables actions according to selection status.


   .. method:: _find_focus_child(self)



   .. method:: selected_entity_class_ids(self, entity_class_type)


      Returns object class ids selected in object tree *and* parameter tag toolbar.


   .. method:: _accept_selection(self, widget)


      Clears selection from all widgets except the given one, so there's only one selection
      in the form at a time. In addition, registers the given widget as the official source
      for all operations involving selections (copy, remove, edit), but only in case it *has* a selection.


   .. method:: remove_selection(self, checked=False)


      Removes selection of items.


   .. method:: copy(self, checked=False)


      Copies data to clipboard.


   .. method:: paste(self, checked=False)


      Pastes data from clipboard.


   .. method:: show_import_file_dialog(self, checked=False)


      Shows dialog to allow user to select a file to import.


   .. method:: export_database(self, checked=False)


      Exports data from database into a file.


   .. method:: _select_database(self)


      Lets user select a database from available databases.

      Shows a dialog from which user can select a single database.
      If there is only a single database it is selected automatically and no dialog is shown.

      :returns: the database map of the database or None if no database was selected


   .. method:: export_to_excel(self, db_map, file_path)


      Exports data from database into Excel file.


   .. method:: export_to_sqlite(self, db_map, file_path)


      Exports data from database into SQlite file.


   .. method:: refresh_session(self, checked=False)



   .. method:: commit_session(self, checked=False)


      Commits session.


   .. method:: rollback_session(self, checked=False)



   .. method:: receive_session_committed(self, db_maps)



   .. method:: receive_session_rolled_back(self, db_maps)



   .. method:: receive_session_refreshed(self, db_maps)



   .. method:: _handle_tag_button_toggled(self, db_map_ids, checked)


      Updates filter according to selected tags.


   .. method:: show_manage_parameter_tags_form(self, checked=False)



   .. method:: _handle_parameter_value_list_selection_changed(self, selected, deselected)


      Accepts selection.


   .. method:: show_parameter_value_list_context_menu(self, pos)


      Shows the context menu for parameter value list tree view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: remove_parameter_value_lists(self)


      Removes selection of parameter value-lists.


   .. method:: notify_items_changed(self, action, item_type, db_map_data)


      Enables or disables actions and informs the user about what just happened.


   .. method:: receive_object_classes_added(self, db_map_data)



   .. method:: receive_objects_added(self, db_map_data)



   .. method:: receive_relationship_classes_added(self, db_map_data)



   .. method:: receive_relationships_added(self, db_map_data)



   .. method:: receive_parameter_definitions_added(self, db_map_data)



   .. method:: receive_parameter_values_added(self, db_map_data)



   .. method:: receive_parameter_value_lists_added(self, db_map_data)



   .. method:: receive_parameter_tags_added(self, db_map_data)



   .. method:: receive_object_classes_updated(self, db_map_data)



   .. method:: receive_objects_updated(self, db_map_data)



   .. method:: receive_relationship_classes_updated(self, db_map_data)



   .. method:: receive_relationships_updated(self, db_map_data)



   .. method:: receive_parameter_definitions_updated(self, db_map_data)



   .. method:: receive_parameter_values_updated(self, db_map_data)



   .. method:: receive_parameter_value_lists_updated(self, db_map_data)



   .. method:: receive_parameter_tags_updated(self, db_map_data)



   .. method:: receive_parameter_definition_tags_set(self, db_map_data)



   .. method:: receive_object_classes_removed(self, db_map_data)



   .. method:: receive_objects_removed(self, db_map_data)



   .. method:: receive_relationship_classes_removed(self, db_map_data)



   .. method:: receive_relationships_removed(self, db_map_data)



   .. method:: receive_parameter_definitions_removed(self, db_map_data)



   .. method:: receive_parameter_values_removed(self, db_map_data)



   .. method:: receive_parameter_value_lists_removed(self, db_map_data)



   .. method:: receive_parameter_tags_removed(self, db_map_data)



   .. method:: restore_ui(self)


      Restore UI state from previous session.


   .. method:: save_window_state(self)


      Save window state parameters (size, position, state) via QSettings.


   .. method:: closeEvent(self, event)


      Handle close window.

      :param event: Closing event
      :type event: QCloseEvent



.. py:class:: DataStoreForm(db_mngr, *db_urls)

   Bases: :class:`spinetoolbox.widgets.tabular_view_mixin.TabularViewMixin`, :class:`spinetoolbox.widgets.graph_view_mixin.GraphViewMixin`, :class:`spinetoolbox.widgets.parameter_view_mixin.ParameterViewMixin`, :class:`spinetoolbox.widgets.tree_view_mixin.TreeViewMixin`, :class:`spinetoolbox.widgets.data_store_widget.DataStoreFormBase`

   A widget to visualize Spine dbs.

   Initializes everything.

   :param db_mngr: The manager to use
   :type db_mngr: SpineDBManager
   :param \*db_urls: Database url, codename.
   :type \*db_urls: tuple

   .. method:: connect_signals(self)



   .. method:: tabify_and_raise(self, docks)


      Tabifies docks in given list, then raises the first.

      :param docks:
      :type docks: list


   .. method:: begin_style_change(self)


      Begins a style change operation.


   .. method:: end_style_change(self)


      Ends a style change operation.


   .. method:: apply_tree_style(self, checked=False)


      Applies the tree style, inspired in the former tree view.


   .. method:: apply_tabular_style(self, checked=False)


      Applies the tree style, inspired in the former tabular view.


   .. method:: apply_graph_style(self, checked=False)


      Applies the tree style, inspired in the former graph view.



