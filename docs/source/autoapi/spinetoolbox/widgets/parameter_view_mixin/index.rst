:mod:`spinetoolbox.widgets.parameter_view_mixin`
================================================

.. py:module:: spinetoolbox.widgets.parameter_view_mixin

.. autoapi-nested-parse::

   Contains the ParameterViewMixin class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: ParameterViewMixin(*args, **kwargs)

   Provides stacked parameter tables for the data store form.

   .. method:: add_menu_actions(self)


      Adds toggle view actions to View menu.


   .. method:: connect_signals(self)


      Connects signals to slots.


   .. method:: init_models(self)


      Initializes models.


   .. method:: _setup_delegate(self, table_view, column, delegate_class)


      Returns a custom delegate for a given view.


   .. method:: setup_delegates(self)


      Sets delegates for tables.


   .. method:: set_parameter_data(self, index, new_value)


      Updates (object or relationship) parameter definition or value with newly edited data.


   .. method:: show_object_name_list_editor(self, index, rel_cls_id, db_map)


      Shows the object names list editor.

      :param index:
      :type index: QModelIndex
      :param rel_cls_id:
      :type rel_cls_id: int
      :param db_map:
      :type db_map: DiffDatabaseMapping


   .. method:: show_parameter_value_editor(self, index, value_name='', value=None)


      Shows the parameter value editor for the given index of given table view.


   .. method:: _handle_object_parameter_tab_changed(self, index)


      Updates filter.


   .. method:: _handle_relationship_parameter_tab_changed(self, index)


      Updates filter.


   .. method:: _handle_object_parameter_value_visibility_changed(self, visible)



   .. method:: _handle_object_parameter_definition_visibility_changed(self, visible)



   .. method:: _handle_relationship_parameter_value_visibility_changed(self, visible)



   .. method:: _handle_relationship_parameter_definition_visibility_changed(self, visible)



   .. method:: _handle_object_parameter_definition_selection_changed(self, selected, deselected)


      Enables/disables the option to remove rows.


   .. method:: _handle_object_parameter_value_selection_changed(self, selected, deselected)


      Enables/disables the option to remove rows.


   .. method:: _handle_relationship_parameter_definition_selection_changed(self, selected, deselected)


      Enables/disables the option to remove rows.


   .. method:: _handle_relationship_parameter_value_selection_changed(self, selected, deselected)


      Enables/disables the option to remove rows.


   .. method:: set_default_parameter_data(self, index=None)


      Sets default rows for parameter models according to given index.

      :param index: and index of the object or relationship tree
      :type index: QModelIndex


   .. method:: set_and_apply_default_rows(model, default_data)
      :staticmethod:



   .. method:: update_filter(self)


      Updates filters.


   .. method:: show_object_parameter_value_context_menu(self, pos)


      Shows the context menu for object parameter value table view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_relationship_parameter_value_context_menu(self, pos)


      Shows the context menu for relationship parameter value table view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_object_parameter_definition_context_menu(self, pos)


      Shows the context menu for object parameter table view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_relationship_parameter_definition_context_menu(self, pos)


      Shows the context menu for relationship parameter table view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: _show_parameter_context_menu(self, position, table_view, value_column_header)


      Shows the context menu for the given parameter table.

      :param position: local mouse position in the table view
      :type position: QPoint
      :param table_view: the table view where the context menu was triggered
      :type table_view: QTableView
      :param value_column_header: column header for editable/plottable values
      :type value_column_header: str


   .. method:: remove_object_parameter_values(self)


      Removes selected rows from object parameter value table.


   .. method:: remove_relationship_parameter_values(self)


      Removes selected rows from relationship parameter value table.


   .. method:: remove_object_parameter_definitions(self)


      Removes selected rows from object parameter definition table.


   .. method:: remove_relationship_parameter_definitions(self)


      Removes selected rows from relationship parameter definition table.


   .. method:: _remove_parameter_data(self, table_view, item_type)


      Removes selected rows from parameter table.

      :param table_view: remove selection from this view
      :type table_view: QTableView
      :param item_type:
      :type item_type: str


   .. method:: restore_ui(self)


      Restores UI state from previous session.


   .. method:: save_window_state(self)


      Saves window state parameters (size, position, state) via QSettings.


   .. method:: receive_parameter_definitions_added(self, db_map_data)



   .. method:: receive_parameter_values_added(self, db_map_data)



   .. method:: receive_parameter_definitions_updated(self, db_map_data)



   .. method:: receive_parameter_values_updated(self, db_map_data)



   .. method:: receive_parameter_definition_tags_set(self, db_map_data)



   .. method:: receive_object_classes_removed(self, db_map_data)



   .. method:: receive_relationship_classes_removed(self, db_map_data)



   .. method:: receive_parameter_definitions_removed(self, db_map_data)



   .. method:: receive_parameter_values_removed(self, db_map_data)




