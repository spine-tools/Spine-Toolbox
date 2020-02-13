:mod:`spinetoolbox.spine_db_manager`
====================================

.. py:module:: spinetoolbox.spine_db_manager

.. autoapi-nested-parse::

   The SpineDBManager class

   :authors: P. Vennström (VTT) and M. Marin (KTH)
   :date:   2.10.2019



Module Contents
---------------

.. function:: do_create_new_spine_database(url, for_spine_model)

   Creates a new spine database at the given url.


.. py:class:: SpineDBManager(logger, project)

   Bases: :class:`PySide2.QtCore.QObject`

   Class to manage DBs within a project.

   TODO: Expand description, how it works, the cache, the signals, etc.

   Initializes the instance.

   :param logger:
   :type logger: LoggingInterface
   :param project:
   :type project: SpineToolboxProject

   .. attribute:: msg_error
      

      

   .. attribute:: session_refreshed
      

      

   .. attribute:: session_committed
      

      

   .. attribute:: session_rolled_back
      

      

   .. attribute:: object_classes_added
      

      

   .. attribute:: objects_added
      

      

   .. attribute:: relationship_classes_added
      

      

   .. attribute:: relationships_added
      

      

   .. attribute:: parameter_definitions_added
      

      

   .. attribute:: _parameter_definitions_added
      

      

   .. attribute:: parameter_values_added
      

      

   .. attribute:: _parameter_values_added
      

      

   .. attribute:: parameter_value_lists_added
      

      

   .. attribute:: parameter_tags_added
      

      

   .. attribute:: object_classes_removed
      

      

   .. attribute:: objects_removed
      

      

   .. attribute:: relationship_classes_removed
      

      

   .. attribute:: relationships_removed
      

      

   .. attribute:: parameter_definitions_removed
      

      

   .. attribute:: parameter_values_removed
      

      

   .. attribute:: parameter_value_lists_removed
      

      

   .. attribute:: parameter_tags_removed
      

      

   .. attribute:: object_classes_updated
      

      

   .. attribute:: objects_updated
      

      

   .. attribute:: relationship_classes_updated
      

      

   .. attribute:: relationships_updated
      

      

   .. attribute:: parameter_definitions_updated
      

      

   .. attribute:: _parameter_definitions_updated
      

      

   .. attribute:: parameter_values_updated
      

      

   .. attribute:: _parameter_values_updated
      

      

   .. attribute:: parameter_value_lists_updated
      

      

   .. attribute:: parameter_tags_updated
      

      

   .. attribute:: parameter_definition_tags_set
      

      

   .. attribute:: items_removed_from_cache
      

      

   .. attribute:: _GROUP_SEP
      :annotation: =  ǀ 

      

   .. method:: db_maps(self)
      :property:



   .. method:: create_new_spine_database(self, url, for_spine_model=False)



   .. method:: close_session(self, url)


      Pops any db map on the given url and closes its connection.

      :param url:
      :type url: str


   .. method:: close_all_sessions(self)


      Closes connections to all database mappings.


   .. method:: get_db_map(self, url, upgrade=False, codename=None)


      Returns a DiffDatabaseMapping instance from url if possible, None otherwise.
      If needed, asks the user to upgrade to the latest db version.

      :param url:
      :type url: str, URL
      :param upgrade:
      :type upgrade: bool, optional
      :param codename:
      :type codename: str, NoneType, optional

      :returns: DiffDatabaseMapping, NoneType


   .. method:: do_get_db_map(self, url, upgrade, codename)


      Returns a memorized DiffDatabaseMapping instance from url.
      Called by `get_db_map`.

      :param url:
      :type url: str, URL
      :param upgrade:
      :type upgrade: bool, optional
      :param codename:
      :type codename: str, NoneType, optional

      :returns: DiffDatabaseMapping


   .. method:: get_db_map_for_listener(self, listener, url, upgrade=False, codename=None)



   .. method:: remove_db_map_listener(self, db_map, listener)



   .. method:: refresh_session(self, *db_maps)



   .. method:: commit_session(self, *db_maps)



   .. method:: _get_commit_msg(db_map)
      :staticmethod:



   .. method:: rollback_session(self, *db_maps)



   .. method:: _commit_db_map_session(self, db_map)



   .. method:: _rollback_db_map_session(self, db_map)



   .. method:: ok_to_close(self, db_map)


      Prompts the user to commit or rollback changes to given database map.

      :returns: True if successfully committed or rolled back, False otherwise
      :rtype: bool


   .. method:: connect_signals(self)


      Connects signals.


   .. method:: receive_error_msg(self, db_map_error_log)



   .. method:: cache_items(self, item_type, db_map_data)


      Caches data for a given type.
      It works for both insert and update operations.

      :param item_type:
      :type item_type: str
      :param db_map_data: lists of dictionary items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cache_parameter_definition_tags(self, db_map_data)


      Caches parameter definition tags in the parameter definition dictionary.

      :param db_map_data: lists of parameter definition items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: uncache_items(self, item_type, db_map_data)


      Removes data from cache.

      :param item_type:
      :type item_type: str
      :param db_map_data: lists of dictionary items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_icons(self, db_map_data)


      Runs when object classes are added or updated. Setups icons for those classes.
      :param item_type:
      :type item_type: str
      :param db_map_data: lists of dictionary items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: entity_class_icon(self, db_map, entity_type, entity_class_id)


      Returns an appropriate icon for a given entity class.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param entity_type: either 'object class' or 'relationship class'
      :type entity_type: str
      :param entity_class_id:
      :type entity_class_id: int

      :returns: QIcon


   .. method:: get_item(self, db_map, item_type, id_)


      Returns the item of the given type in the given db map that has the given id,
      or an empty dict if not found.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param item_type:
      :type item_type: str
      :param id\_:
      :type id\_: int

      :returns: dict


   .. method:: get_item_by_field(self, db_map, item_type, field, value)


      Returns the first item of the given type in the given db map
      that has the given value for the given field
      Returns an empty dictionary if none found.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param item_type:
      :type item_type: str
      :param field:
      :type field: str
      :param value:

      :returns: dict


   .. method:: get_items_by_field(self, db_map, item_type, field, value)


      Returns all items of the given type in the given db map that have the given value
      for the given field. Returns an empty list if none found.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param item_type:
      :type item_type: str
      :param field:
      :type field: str
      :param value:

      :returns: list


   .. method:: get_items(self, db_map, item_type)


      Returns all the items of the given type in the given db map,
      or an empty list if none found.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param item_type:
      :type item_type: str

      :returns: list


   .. method:: _get_items_from_db(self, db_map, item_type)


      Returns all items of the given type in the given db map.
      Called by the above methods whenever they don't find what they're looking for in cache.


   .. method:: get_value(self, db_map, item_type, id_, field, role=Qt.DisplayRole)


      Returns the value or default value of a parameter.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param item_type: either "parameter definition" or "parameter value"
      :type item_type: str
      :param id\_:
      :type id\_: int
      :param field: either "value" or "default_value"
      :type field: str
      :param role:
      :type role: int, optional


   .. method:: _display_data(parsed_value)
      :staticmethod:


      Returns the value's database representation formatted for Qt.DisplayRole.


   .. method:: _tool_tip_data(parsed_value)
      :staticmethod:


      Returns the value's database representation formatted for Qt.ToolTipRole.


   .. method:: get_object_classes(self, db_map, cache=True)


      Returns object classes from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping

      :returns: dictionary items
      :rtype: list


   .. method:: get_objects(self, db_map, class_id=None, cache=True)


      Returns objects from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param class_id:
      :type class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_relationship_classes(self, db_map, ids=None, object_class_id=None, cache=True)


      Returns relationship classes from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param object_class_id:
      :type object_class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_relationships(self, db_map, ids=None, class_id=None, object_id=None, cache=True)


      Returns relationships from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param class_id:
      :type class_id: int, optional
      :param object_id:
      :type object_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_object_parameter_definitions(self, db_map, ids=None, object_class_id=None, cache=True)


      Returns object parameter definitions from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param object_class_id:
      :type object_class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_relationship_parameter_definitions(self, db_map, ids=None, relationship_class_id=None, cache=True)


      Returns relationship parameter definitions from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param relationship_class_id:
      :type relationship_class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_object_parameter_values(self, db_map, ids=None, object_class_id=None, cache=True)


      Returns object parameter values from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set
      :param object_class_id:
      :type object_class_id: int

      :returns: dictionary items
      :rtype: list


   .. method:: get_relationship_parameter_values(self, db_map, ids=None, relationship_class_id=None, cache=True)


      Returns relationship parameter values from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set
      :param relationship_class_id:
      :type relationship_class_id: int

      :returns: dictionary items
      :rtype: list


   .. method:: get_parameter_definitions(self, db_map, ids=None, entity_class_id=None, cache=True)


      Returns both object and relationship parameter definitions.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param entity_class_id:
      :type entity_class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_parameter_values(self, db_map, ids=None, entity_class_id=None, cache=True)


      Returns both object and relationship parameter values.

      :param db_map:
      :type db_map: DiffDatabaseMapping
      :param ids:
      :type ids: set, optional
      :param entity_class_id:
      :type entity_class_id: int, optional

      :returns: dictionary items
      :rtype: list


   .. method:: get_parameter_value_lists(self, db_map, cache=True)


      Returns parameter value lists from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping

      :returns: dictionary items
      :rtype: list


   .. method:: get_parameter_tags(self, db_map, cache=True)


      Get parameter tags from database.

      :param db_map:
      :type db_map: DiffDatabaseMapping

      :returns: dictionary items
      :rtype: list


   .. method:: add_or_update_items(self, db_map_data, method_name, signal_name)


      Adds or updates items in db.

      :param db_map_data: lists of items to add or update keyed by DiffDatabaseMapping
      :type db_map_data: dict
      :param method_name: attribute of DiffDatabaseMapping to call for performing the operation
      :type method_name: str
      :param signal_name: signal attribute of SpineDBManager to emit if successful
      :type signal_name: str


   .. method:: add_object_classes(self, db_map_data)


      Adds object classes to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_objects(self, db_map_data)


      Adds objects to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_relationship_classes(self, db_map_data)


      Adds relationship classes to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_relationships(self, db_map_data)


      Adds relationships to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_parameter_definitions(self, db_map_data)


      Adds parameter definitions to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_parameter_values(self, db_map_data)


      Adds parameter values to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_checked_parameter_values(self, db_map_data)


      Adds parameter values in db without checking integrity.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_parameter_value_lists(self, db_map_data)


      Adds parameter value lists to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: add_parameter_tags(self, db_map_data)


      Adds parameter tags to db.

      :param db_map_data: lists of items to add keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_object_classes(self, db_map_data)


      Updates object classes in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_objects(self, db_map_data)


      Updates objects in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_relationship_classes(self, db_map_data)


      Updates relationship classes in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_relationships(self, db_map_data)


      Updates relationships in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_parameter_definitions(self, db_map_data)


      Updates parameter definitions in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_parameter_values(self, db_map_data)


      Updates parameter values in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_checked_parameter_values(self, db_map_data)


      Updates parameter values in db without checking integrity.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_parameter_value_lists(self, db_map_data)


      Updates parameter value lists in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: update_parameter_tags(self, db_map_data)


      Updates parameter tags in db.

      :param db_map_data: lists of items to update keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: set_parameter_definition_tags(self, db_map_data)


      Sets parameter definition tags in db.

      :param db_map_data: lists of items to set keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: remove_items(self, db_map_typed_data)



   .. method:: do_remove_items(self, db_map_typed_data)


      Removes items from database.

      :param db_map_typed_data: lists of items to remove, keyed by item type (str), keyed by DiffDatabaseMapping
      :type db_map_typed_data: dict


   .. method:: _to_ids(db_map_data)
      :staticmethod:



   .. method:: cascade_remove_objects(self, db_map_data)


      Removes objects in cascade when removing object classes.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_relationship_classes(self, db_map_data)


      Removes relationship classes in cascade when removing object classes.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_relationships_by_class(self, db_map_data)


      Removes relationships in cascade when removing objects.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_relationships_by_object(self, db_map_data)


      Removes relationships in cascade when removing relationship classes.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_parameter_definitions(self, db_map_data)


      Removes parameter definitions in cascade when removing entity classes.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_parameter_values_by_entity_class(self, db_map_data)


      Removes parameter values in cascade when removing entity classes.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_parameter_values_by_entity(self, db_map_data)


      Removes parameter values in cascade when removing entity classes when removing entities.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_remove_parameter_values_by_definition(self, db_map_data)


      Removes parameter values in cascade when when removing parameter definitions.

      :param db_map_data: lists of removed items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_relationship_classes(self, db_map_data)


      Refreshes cached relationship classes when updating object classes.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_relationships_by_object(self, db_map_data)


      Refreshed cached relationships in cascade when updating objects.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_definitions(self, db_map_data)


      Refreshes cached parameter definitions in cascade when updating entity classes.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_definitions_by_value_list(self, db_map_data)


      Refreshes cached parameter definitions when updating parameter value lists.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_definitions_by_tag(self, db_map_data)


      Refreshes cached parameter definitions when updating parameter tags.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_values_by_entity_class(self, db_map_data)


      Refreshes cached parameter values in cascade when updating entity classes.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_values_by_entity(self, db_map_data)


      Refreshes cached parameter values in cascade when updating entities.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: cascade_refresh_parameter_values_by_definition(self, db_map_data)


      Refreshes cached parameter values in cascade when updating parameter definitions.

      :param db_map_data: lists of updated items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: find_cascading_relationship_classes(self, db_map_ids)


      Finds and returns cascading relationship classes for the given object class ids.


   .. method:: find_cascading_entities(self, db_map_ids, item_type)


      Finds and returns cascading entities for the given entity class ids.


   .. method:: find_cascading_relationships(self, db_map_ids)


      Finds and returns cascading relationships for the given object ids.


   .. method:: find_cascading_parameter_data(self, db_map_ids, item_type)


      Finds and returns cascading parameter definitions or values for the given entity class ids.


   .. method:: find_cascading_parameter_definitions_by_value_list(self, db_map_ids)


      Finds and returns cascading parameter definitions for the given parameter value list ids.


   .. method:: find_cascading_parameter_definitions_by_tag(self, db_map_ids)


      Finds and returns cascading parameter definitions for the given parameter tag ids.


   .. method:: find_cascading_parameter_values_by_entity(self, db_map_ids)


      Finds and returns cascading parameter values for the given entity ids.


   .. method:: find_cascading_parameter_values_by_definition(self, db_map_ids)


      Finds and returns cascading parameter values for the given parameter definition ids.


   .. method:: do_add_parameter_definitions(self, db_map_data)


      Adds parameter definitions in extended format given data in compact format.

      :param db_map_data: lists of parameter definition items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: do_add_parameter_values(self, db_map_data)


      Adds parameter values in extended format given data in compact format.

      :param db_map_data: lists of parameter value items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: do_update_parameter_definitions(self, db_map_data)


      Updates parameter definitions in extended format given data in compact format.

      :param db_map_data: lists of parameter definition items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: do_update_parameter_values(self, db_map_data)


      Updates parameter values in extended format given data in compact format.

      :param db_map_data: lists of parameter value items keyed by DiffDatabaseMapping
      :type db_map_data: dict



