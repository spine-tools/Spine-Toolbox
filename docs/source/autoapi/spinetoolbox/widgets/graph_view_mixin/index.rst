:mod:`spinetoolbox.widgets.graph_view_mixin`
============================================

.. py:module:: spinetoolbox.widgets.graph_view_mixin

.. autoapi-nested-parse::

   Contains the GraphViewMixin class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: GraphViewMixin(*args, **kwargs)

   Provides the graph view for the DS form.

   .. attribute:: graph_created
      

      

   .. attribute:: _node_extent
      :annotation: = 64

      

   .. attribute:: _arc_width
      

      

   .. attribute:: _arc_length_hint
      

      

   .. method:: add_menu_actions(self)


      Adds toggle view actions to View menu.


   .. method:: restore_dock_widgets(self)



   .. method:: connect_signals(self)


      Connects signals.


   .. method:: setup_zoom_widget_action(self)


      Setups zoom widget action in view menu.


   .. method:: init_models(self)


      Initializes models.


   .. method:: receive_object_classes_added(self, db_map_data)



   .. method:: receive_object_classes_updated(self, db_map_data)



   .. method:: receive_object_classes_removed(self, db_map_data)



   .. method:: receive_relationship_classes_added(self, db_map_data)



   .. method:: receive_relationship_classes_updated(self, db_map_data)



   .. method:: receive_relationship_classes_removed(self, db_map_data)



   .. method:: receive_objects_added(self, db_map_data)


      Runs when objects are added to the db.
      Builds a lookup dictionary consumed by ``add_object``.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: receive_objects_updated(self, db_map_data)


      Runs when objects are updated in the db. Refreshes names of objects in graph.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: receive_objects_removed(self, db_map_data)


      Runs when objects are removed from the db. Rebuilds graph if needed.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: receive_relationships_added(self, db_map_data)


      Runs when relationships are added to the db.
      Builds a lookup dictionary consumed by ``add_relationship``.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: receive_relationships_removed(self, db_map_data)


      Runs when relationships are removed from the db. Rebuilds graph if needed.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: receive_entities_removed(self, db_map_data)



   .. method:: refresh_icons(self, db_map_data)


      Runs when entity classes are updated in the db. Refreshes icons of entities in graph.

      :param db_map_data: list of dictionary-items keyed by DiffDatabaseMapping instance.
      :type db_map_data: dict


   .. method:: _add_more_object_classes(self, index)


      Runs when the user clicks on the Item palette Object class view.
      Opens the form  to add more object classes if the index is the one that sayes 'New...'.

      :param index: The clicked index.
      :type index: QModelIndex


   .. method:: _add_more_relationship_classes(self, index)


      Runs when the user clicks on the Item palette Relationship class view.
      Opens the form to add more relationship classes if the index is the one that sayes 'New...'.

      :param index: The clicked index.
      :type index: QModelIndex


   .. method:: _handle_zoom_minus_pressed(self)


      Performs a zoom out on the view.


   .. method:: _handle_zoom_plus_pressed(self)


      Performs a zoom in on the view.


   .. method:: _handle_zoom_reset_pressed(self)


      Resets the zoom on the view.


   .. method:: _handle_menu_graph_about_to_show(self)


      Enables or disables actions according to current selection in the graph.


   .. method:: _handle_menu_help_about_to_show(self)


      Enables or disables action according to current status of the demo.


   .. method:: _handle_item_palette_dock_location_changed(self, area)


      Runs when the item palette dock widget location changes.
      Adjusts splitter orientation accordingly.


   .. method:: _handle_entity_graph_visibility_changed(self, visible)



   .. method:: _handle_item_palette_visibility_changed(self, visible)



   .. method:: _handle_object_tree_selection_changed(self, selected, deselected)


      Builds graph.


   .. method:: build_graph(self, timeit=False)


      Builds the graph.


   .. method:: _get_selected_object_ids(self)


      Returns a set of object ids according to selection in the object tree.

      :returns: set


   .. method:: _get_graph_data(self)


      Returns data for making graph according to selection in Object tree.

      :returns: integer object ids
                list: integer relationship ids
                list: arc source indices
                list: arc destination indices
      :rtype: list


   .. method:: _get_new_items(self)


      Returns new items for the graph.

      :returns: ObjectItem instances
                list: RelationshipItem instances
                list: ArcItem instances
      :rtype: list


   .. method:: _get_wip_relationship_items(self)


      Removes and returns wip relationship items from the current scene.

      :returns: RelationshipItem instances
      :rtype: list


   .. method:: _add_new_items(scene, object_items, relationship_items, arc_items)
      :staticmethod:



   .. method:: _add_wip_relationship_items(scene, wip_relationship_items, new_object_items)
      :staticmethod:


      Adds wip relationship items to the given scene, merging completed members with existing
      object items by entity id.

      :param scene:
      :type scene: QGraphicsScene
      :param wip_relationship_items:
      :type wip_relationship_items: list
      :param new_object_items:
      :type new_object_items: list


   .. method:: shortest_path_matrix(N, src_inds, dst_inds, spread)
      :staticmethod:


      Returns the shortest-path matrix.

      :param N: The number of nodes in the graph.
      :type N: int
      :param src_inds: Source indices
      :type src_inds: list
      :param dst_inds: Destination indices
      :type dst_inds: list
      :param spread: The desired 'distance' between neighbours
      :type spread: int


   .. method:: sets(N)
      :staticmethod:


      Returns sets of vertex pairs indices.

      :param N:
      :type N: int


   .. method:: vertex_coordinates(matrix, heavy_positions=None, iterations=10, weight_exp=-2, initial_diameter=1000)
      :staticmethod:


      Returns x and y coordinates for each vertex in the graph, computed using VSGD-MS.


   .. method:: new_scene(self)


      Replaces the current scene with a new one.


   .. method:: tear_down_scene(self)


      Removes all references to this form in graphics items and schedules
      the scene for deletion.


   .. method:: extend_scene(self)


      Extends the scene to show all items.


   .. method:: _handle_scene_selection_changed(self)


      Filters parameters by selected objects in the graph.


   .. method:: _handle_scene_changed(self, region)


      Enlarges the scene rect if needed.


   .. method:: _handle_item_dropped(self, pos, text)


      Runs when an item is dropped from Item palette onto the view.
      Creates the object or relationship template.

      :param pos:
      :type pos: QPoint
      :param text:
      :type text: str


   .. method:: add_wip_relationship(self, scene, pos, relationship_class_id, center_item=None, center_dimension=None)


      Makes items for a wip relationship and adds them to the scene at the given coordinates.

      :param scene:
      :type scene: QGraphicsScene
      :param pos:
      :type pos: QPointF
      :param relationship_class_id:
      :type relationship_class_id: int
      :param center_item_dimension: A tuple of (ObjectItem, dimension) to put at the center of the wip item.
      :type center_item_dimension: tuple, optional


   .. method:: add_object(self, object_class_id, name)


      Adds object to the database.

      :param object_class_id:
      :type object_class_id: int
      :param name:
      :type name: str

      :returns: The id of the added object if successful, None otherwise.
      :rtype: int, NoneType


   .. method:: update_object(self, object_id, name)


      Updates object in the db.

      :param object_id:
      :type object_id: int
      :param name:
      :type name: str


   .. method:: add_relationship(self, class_id, object_id_list, object_name_list)


      Adds relationship to the db.

      :param class_id:
      :type class_id: int
      :param object_id_list:
      :type object_id_list: list


   .. method:: show_graph_view_context_menu(self, global_pos)


      Shows context menu for graphics view.

      :param global_pos:
      :type global_pos: QPoint


   .. method:: hide_selected_items(self, checked=False)


      Hides selected items.


   .. method:: show_hidden_items(self, checked=False)


      Shows hidden items.


   .. method:: prune_selected_items(self, checked=False)


      Prunes selected items.


   .. method:: restore_pruned_items(self, checked=False)


      Reinstates pruned items.


   .. method:: show_demo(self, checked=False)



   .. method:: show_object_item_context_menu(self, global_pos, main_item)


      Shows context menu for entity item.

      :param global_pos:
      :type global_pos: QPoint
      :param main_item:
      :type main_item: spinetoolbox.widgets.graph_view_graphics_items.ObjectItem


   .. method:: show_relationship_item_context_menu(self, global_pos)


      Shows context menu for entity item.

      :param global_pos:
      :type global_pos: QPoint


   .. method:: _apply_entity_context_menu_option(self, option)



   .. method:: remove_graph_items(self, checked=False)


      Removes all selected items in the graph.


   .. method:: closeEvent(self, event=None)


      Handles close window event.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



