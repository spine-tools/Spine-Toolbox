:mod:`spinetoolbox.widgets.tabular_view_mixin`
==============================================

.. py:module:: spinetoolbox.widgets.tabular_view_mixin

.. autoapi-nested-parse::

   Contains TabularViewMixin class.

   :author: P. Vennström (VTT)
   :date:   1.11.2018



Module Contents
---------------

.. py:class:: TabularViewMixin(*args, **kwargs)

   Provides the pivot table and its frozen table for the DS form.

   .. attribute:: _PARAMETER_VALUE
      :annotation: = Parameter value

      

   .. attribute:: _RELATIONSHIP
      :annotation: = Relationship

      

   .. attribute:: _PARAMETER
      :annotation: = parameter

      

   .. attribute:: _PARAM_INDEX_ID
      

      

   .. method:: setup_delegates(self)


      Sets delegates for tables.


   .. method:: add_menu_actions(self)


      Adds toggle view actions to View menu.


   .. method:: connect_signals(self)


      Connects signals to slots.


   .. method:: _handle_pivot_table_selection_changed(self, selected, deselected)


      Accepts selection.


   .. method:: is_value_input_type(self)



   .. method:: _set_model_data(self, index, value)



   .. method:: current_object_class_id_list(self)



   .. method:: current_object_class_name_list(self)



   .. method:: _is_class_index(index, class_type)
      :staticmethod:


      Returns whether or not the given tree index is a class index.

      :param index: index from object or relationship tree
      :type index: QModelIndex
      :param class_type:
      :type class_type: str

      :returns: bool


   .. method:: _handle_pivot_table_visibility_changed(self, visible)



   .. method:: _handle_frozen_table_visibility_changed(self, visible)



   .. method:: _handle_entity_tree_selection_changed(self, selected, deselected)



   .. method:: _get_entities(self, class_id=None, class_type=None)


      Returns a list of dict items from the object or relationship tree model
      corresponding to the given class id.

      :param class_id:
      :type class_id: int
      :param class_type:
      :type class_type: str

      :returns: list(dict)


   .. method:: load_empty_relationship_data(self, objects_per_class=None)


      Returns a dict containing all possible relationships in the current class.

      :param objects_per_class:
      :type objects_per_class: dict

      :returns: Key is object id tuple, value is None.
      :rtype: dict


   .. method:: load_full_relationship_data(self, relationships=None, action='add')


      Returns a dict of relationships in the current class.

      :returns: Key is object id tuple, value is relationship id.
      :rtype: dict


   .. method:: load_relationship_data(self)


      Returns a dict that merges empty and full relationship data.

      :returns: Key is object id tuple, value is True if a relationship exists, False otherwise.
      :rtype: dict


   .. method:: _get_parameter_value_or_def_ids(self, item_type)


      Returns a set of integer ids from the parameter model
      corresponding to the currently selected class and the given item type.

      :param item_type: either "parameter value" or "parameter definition"
      :type item_type: str

      :returns: set(int)


   .. method:: _get_parameter_values_or_defs(self, item_type)


      Returns a list of dict items from the parameter model
      corresponding to the currently selected class and the given item type.

      :param item_type: either "parameter value" or "parameter definition"
      :type item_type: str

      :returns: list(dict)


   .. method:: load_empty_parameter_value_data(self, entities=None, parameter_ids=None)


      Returns a dict containing all possible combinations of entities and parameters for the current class.

      :param entities: if given, only load data for these entities
      :type entities: list, optional
      :param parameter_ids: if given, only load data for these parameter definitions
      :type parameter_ids: set, optional

      :returns: Key is a tuple object_id, ..., parameter_id, value is None.
      :rtype: dict


   .. method:: load_full_parameter_value_data(self, parameter_values=None, action='add')


      Returns a dict of parameter values for the current class.

      :param parameter_values:
      :type parameter_values: list, optional

      :returns: Key is a tuple object_id, ..., parameter_id, value is the parameter value.
      :rtype: dict


   .. method:: load_parameter_value_data(self)


      Returns a dict that merges empty and full parameter value data.

      :returns: Key is a tuple object_id, ..., parameter_id, value is the parameter value or None if not specified.
      :rtype: dict


   .. method:: get_pivot_preferences(self, selection_key)


      Returns saved or default pivot preferences.

      :param selection_key: Tuple of class id, class type, and input type.
      :type selection_key: tuple(int,str,str)

      Returns
          list: indexes in rows
          list: indexes in columns
          list: frozen indexes
          tuple: selection in frozen table


   .. method:: reload_pivot_table(self, text='')


      Updates current class (type and id) and reloads pivot table for it.


   .. method:: do_reload_pivot_table(self)


      Reloads pivot table.


   .. method:: clear_pivot_table(self)



   .. method:: wipe_out_filter_menus(self)



   .. method:: make_pivot_headers(self)


      Turns top left indexes in the pivot table into TabularViewHeaderWidget.


   .. method:: make_frozen_headers(self)


      Turns indexes in the first row of the frozen table into TabularViewHeaderWidget.


   .. method:: create_filter_menu(self, identifier)


      Returns a filter menu for given given object class identifier.

      :param identifier:
      :type identifier: int

      :returns: TabularViewFilterMenu


   .. method:: create_header_widget(self, identifier, area, with_menu=True)


      Returns a TabularViewHeaderWidget for given object class identifier.

      :param identifier:
      :type identifier: int
      :param area:
      :type area: str
      :param with_menu:
      :type with_menu: bool

      :returns: TabularViewHeaderWidget


   .. method:: _get_insert_index(pivot_list, catcher, position)
      :staticmethod:


      Returns an index for inserting a new element in the given pivot list.

      :returns: int


   .. method:: handle_header_dropped(self, dropped, catcher, position='')


      Updates pivots when a header is dropped.

      :param dropped:
      :type dropped: TabularViewHeaderWidget
      :param catcher:
      :type catcher: TabularViewHeaderWidget, PivotTableHeaderView, FrozenTableView
      :param position: either "before", "after", or ""
      :type position: str


   .. method:: get_frozen_value(self, index)


      Returns the value in the frozen table corresponding to the given index.

      :param index:
      :type index: QModelIndex

      :returns: tuple


   .. method:: change_frozen_value(self, current, previous)


      Sets the frozen value from selection in frozen table.


   .. method:: change_filter(self, identifier, valid_values, has_filter)



   .. method:: reload_frozen_table(self)


      Resets the frozen model according to new selection in entity trees.


   .. method:: find_frozen_values(self, frozen)


      Returns a list of tuples containing unique values (object ids) for the frozen indexes (object class ids).

      :param frozen: A tuple of currently frozen indexes
      :type frozen: tuple(int)

      :returns: list(tuple(list(int)))


   .. method:: refresh_table_view(table_view)
      :staticmethod:



   .. method:: _group_by_class(items, get_class_id)
      :staticmethod:



   .. method:: receive_data_added_or_removed(self, data, action)



   .. method:: receive_objects_added_or_removed(self, db_map_data, action)



   .. method:: receive_relationships_added_or_removed(self, db_map_data, action)



   .. method:: receive_parameter_definitions_added_or_removed(self, db_map_data, action)



   .. method:: receive_parameter_values_added_or_removed(self, db_map_data, action)



   .. method:: receive_db_map_data_updated(self, db_map_data, get_class_id)



   .. method:: receive_classes_removed(self, db_map_data)



   .. method:: receive_objects_added(self, db_map_data)


      Reacts to objects added event.


   .. method:: receive_relationships_added(self, db_map_data)


      Reacts to relationships added event.


   .. method:: receive_parameter_definitions_added(self, db_map_data)


      Reacts to parameter definitions added event.


   .. method:: receive_parameter_values_added(self, db_map_data)


      Reacts to parameter values added event.


   .. method:: receive_object_classes_updated(self, db_map_data)


      Reacts to object classes updated event.


   .. method:: receive_objects_updated(self, db_map_data)


      Reacts to objects updated event.


   .. method:: receive_relationship_classes_updated(self, db_map_data)


      Reacts to relationship classes updated event.


   .. method:: receive_relationships_updated(self, db_map_data)


      Reacts to relationships updated event.


   .. method:: receive_parameter_values_updated(self, db_map_data)


      Reacts to parameter values added event.


   .. method:: receive_parameter_definitions_updated(self, db_map_data)


      Reacts to parameter definitions updated event.


   .. method:: receive_object_classes_removed(self, db_map_data)


      Reacts to object classes removed event.


   .. method:: receive_objects_removed(self, db_map_data)


      Reacts to objects removed event.


   .. method:: receive_relationship_classes_removed(self, db_map_data)


      Reacts to relationship classes remove event.


   .. method:: receive_relationships_removed(self, db_map_data)


      Reacts to relationships removed event.


   .. method:: receive_parameter_definitions_removed(self, db_map_data)


      Reacts to parameter definitions removed event.


   .. method:: receive_parameter_values_removed(self, db_map_data)


      Reacts to parameter values removed event.


   .. method:: receive_session_rolled_back(self, db_maps)


      Reacts to session rolled back event.



