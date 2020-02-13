:mod:`spinetoolbox.spine_db_signaller`
======================================

.. py:module:: spinetoolbox.spine_db_signaller

.. autoapi-nested-parse::

   Spine DB Signaller class.

   :authors: M. Marin (KTH)
   :date:   31.10.2019



Module Contents
---------------

.. py:class:: SpineDBSignaller(db_mngr)

   Handles signals from DB manager and channels them to listeners.

   Initializes the signaler object.

   :param db_mngr:
   :type db_mngr: SpineDBManager

   .. method:: add_db_map_listener(self, db_map, listener)


      Adds listener for given db_map.


   .. method:: remove_db_map_listener(self, db_map, listener)


      Removes db_map from the the maps listener listens to.


   .. method:: db_map_listeners(self, db_map)



   .. method:: connect_signals(self)


      Connects signals.


   .. method:: _shared_db_map_data(db_map_data, db_maps)
      :staticmethod:



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



   .. method:: receive_session_refreshed(self, db_maps)



   .. method:: receive_session_committed(self, db_maps)



   .. method:: receive_session_rolled_back(self, db_maps)




