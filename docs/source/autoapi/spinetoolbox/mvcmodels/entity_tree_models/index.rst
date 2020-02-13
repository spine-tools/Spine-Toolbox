:mod:`spinetoolbox.mvcmodels.entity_tree_models`
================================================

.. py:module:: spinetoolbox.mvcmodels.entity_tree_models

.. autoapi-nested-parse::

   Models to represent entities in a tree.

   :authors: P. Vennström (VTT), M. Marin (KTH)
   :date:   11.3.2019



Module Contents
---------------

.. py:class:: EntityTreeModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_tree_model.MinimalTreeModel`

   Base class for all entity tree models.

   Init class.

   :param parent:
   :type parent: DataStoreForm
   :param db_mngr: A manager for the given db_maps
   :type db_mngr: SpineDBManager
   :param db_maps: DiffDatabaseMapping instances
   :type db_maps: iter

   .. attribute:: remove_selection_requested
      

      

   .. method:: root_item_type(self)
      :property:


      Implement in subclasses to create a model specific to any entity type.


   .. method:: root_item(self)
      :property:



   .. method:: root_index(self)
      :property:



   .. method:: build_tree(self)


      Builds tree.


   .. method:: columnCount(self, parent=QModelIndex())



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: headerData(self, section, orientation, role)



   .. method:: _select_index(self, index)


      Marks the index as selected.


   .. method:: select_indexes(self, indexes)


      Marks given indexes as selected.


   .. method:: find_leaves(self, db_map, *ids_path, parent_items=(), fetch=False)


      Returns leaf-nodes following the given path of ids, where each element in ids_path is
      a set of ids to jump from one level in the tree to the next.
      Optionally fetches nodes as it goes.



.. py:class:: ObjectTreeModel(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_models.EntityTreeModel`

   An 'object-oriented' tree model.

   .. method:: root_item_type(self)
      :property:



   .. method:: selected_object_class_indexes(self)
      :property:



   .. method:: selected_object_indexes(self)
      :property:



   .. method:: selected_relationship_class_indexes(self)
      :property:



   .. method:: selected_relationship_indexes(self)
      :property:



   .. method:: _group_object_data(self, db_map_data)


      Takes given object data and returns the same data keyed by parent tree-item.

      :param db_map_data: maps DiffDatabaseMapping instances to list of items as dict
      :type db_map_data: dict

      :returns: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
      :rtype: result (dict)


   .. method:: _group_relationship_class_data(self, db_map_data)


      Takes given relationship class data and returns the same data keyed by parent tree-item.

      :param db_map_data: maps DiffDatabaseMapping instances to list of items as dict
      :type db_map_data: dict

      :returns: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
      :rtype: result (dict)


   .. method:: _group_relationship_data(self, db_map_data)


      Takes given relationship data and returns the same data keyed by parent tree-item.

      :param db_map_data: maps DiffDatabaseMapping instances to list of items as dict
      :type db_map_data: dict

      :returns: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
      :rtype: result (dict)


   .. method:: add_object_classes(self, db_map_data)



   .. method:: add_objects(self, db_map_data)



   .. method:: add_relationship_classes(self, db_map_data)



   .. method:: add_relationships(self, db_map_data)



   .. method:: remove_object_classes(self, db_map_data)



   .. method:: remove_objects(self, db_map_data)



   .. method:: remove_relationship_classes(self, db_map_data)



   .. method:: remove_relationships(self, db_map_data)



   .. method:: update_object_classes(self, db_map_data)



   .. method:: update_objects(self, db_map_data)



   .. method:: update_relationship_classes(self, db_map_data)



   .. method:: update_relationships(self, db_map_data)



   .. method:: find_next_relationship_index(self, index)


      Find and return next ocurrence of relationship item.



.. py:class:: RelationshipTreeModel(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_models.EntityTreeModel`

   A relationship-oriented tree model.

   .. method:: root_item_type(self)
      :property:



   .. method:: selected_relationship_class_indexes(self)
      :property:



   .. method:: selected_relationship_indexes(self)
      :property:



   .. method:: _group_relationship_data(self, db_map_data)


      Takes given relationship data and returns the same data keyed by parent tree-item.

      :param db_map_data: maps DiffDatabaseMapping instances to list of items as dict
      :type db_map_data: dict

      :returns: maps parent tree-items to DiffDatabaseMapping instances to list of item ids
      :rtype: result (dict)


   .. method:: add_relationship_classes(self, db_map_data)



   .. method:: add_relationships(self, db_map_data)



   .. method:: remove_relationship_classes(self, db_map_data)



   .. method:: remove_relationships(self, db_map_data)



   .. method:: update_relationship_classes(self, db_map_data)



   .. method:: update_relationships(self, db_map_data)




