:mod:`spinetoolbox.mvcmodels.entity_tree_item`
==============================================

.. py:module:: spinetoolbox.mvcmodels.entity_tree_item

.. autoapi-nested-parse::

   Classes to represent entities in a tree.

   :authors: P. Vennström (VTT), M. Marin (KTH)
   :date:   11.3.2019



Module Contents
---------------

.. py:class:: MultiDBTreeItem(model=None, db_map_id=None)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_tree_model.TreeItem`

   A tree item that may belong in multiple databases.

   Init class.

   :param db_mngr: a database manager
   :type db_mngr: SpineDBManager
   :param db_map_data: maps instances of DiffDatabaseMapping to the id of the item in that db
   :type db_map_data: dict

   .. attribute:: item_type
      

      Item type identifier string. Should be set to a meaningful value by subclasses.


   .. attribute:: visual_key
      :annotation: = ['name']

      

   .. method:: db_mngr(self)
      :property:



   .. method:: child_item_type(self)
      :property:


      Returns the type of child items. Reimplement in subclasses to return something more meaningful.


   .. method:: display_id(self)
      :property:


      "Returns an id for display based on the display key. This id must be the same across all db_maps.
      If it's not, this property becomes None and measures need to be taken (see update_children_by_id).


   .. method:: display_name(self)
      :property:


      "Returns the name for display.


   .. method:: display_database(self)
      :property:


      "Returns the database for display.


   .. method:: display_icon(self)
      :property:


      Returns an icon to display next to the name.
      Reimplement in subclasses to return something nice.


   .. method:: first_db_map(self)
      :property:


      Returns the first associated db_map.


   .. method:: last_db_map(self)
      :property:


      Returns the last associated db_map.


   .. method:: db_maps(self)
      :property:


      Returns a list of all associated db_maps.


   .. method:: add_db_map_id(self, db_map, id_)


      Adds id for this item in the given db_map.


   .. method:: take_db_map(self, db_map)


      Removes the mapping for given db_map and returns it.


   .. method:: deep_remove_db_map(self, db_map)


      Removes given db_map from this item and all its descendants.


   .. method:: deep_take_db_map(self, db_map)


      Takes given db_map from this item and all its descendants.
      Returns a new item from taken data or None if db_map is not present in the first place.


   .. method:: deep_merge(self, other)


      Merges another item and all its descendants into this one.


   .. method:: db_map_id(self, db_map)


      Returns the id for this item in given db_map or None if not present.


   .. method:: db_map_data(self, db_map)


      Returns data for this item in given db_map or None if not present.


   .. method:: db_map_data_field(self, db_map, field, default=None)


      Returns field from data for this item in given db_map or None if not found.


   .. method:: _create_new_children(self, db_map, children_ids)


      Creates new items from ids associated to a db map.

      :param db_map: create children for this db_map
      :type db_map: DiffDatabaseMapping
      :param children_data: create childs from these dictionaries
      :type children_data: iter


   .. method:: _merge_children(self, new_children)


      Merges new children into this item. Ensures that each children has a valid display id afterwards.


   .. method:: has_children(self)


      Returns whether or not this item has or could have children.


   .. method:: fetch_more(self)


      Fetches children from all associated databases.


   .. method:: _get_children_ids(self, db_map)
      :abstractmethod:


      Returns a set of children ids.
      Must be reimplemented in subclasses.


   .. method:: append_children_by_id(self, db_map_ids)


      Appends children by id.

      :param db_map_ids: maps DiffDatabaseMapping instances to list of ids
      :type db_map_ids: dict


   .. method:: remove_children_by_id(self, db_map_ids)


      Removes children by id.

      :param db_map_ids: maps DiffDatabaseMapping instances to list of ids
      :type db_map_ids: dict


   .. method:: update_children_by_id(self, db_map_ids)


      Updates children by id. Essentially makes sure all children have a valid display id
      after updating the underlying data. These may require 'splitting' a child
      into several for different dbs or merging two or more children from different dbs.

      Examples of problems:

      - The user renames an object class in one db but not in the others --> we need to split
      - The user renames an object class and the new name is already 'taken' by another object class in
        another db_map --> we need to merge

      :param db_map_ids: maps DiffDatabaseMapping instances to list of ids
      :type db_map_ids: dict


   .. method:: insert_children(self, position, *children)


      Insert new children at given position. Returns a boolean depending on how it went.

      :param position: insert new items here
      :type position: int
      :param children: insert items from this iterable
      :type children: iter


   .. method:: remove_children(self, position, count)


      Removes count children starting from the given position.


   .. method:: clear_children(self)


      Clear children list.


   .. method:: _refresh_child_map(self)


      Recomputes the child map.


   .. method:: find_children_by_id(self, db_map, *ids, reverse=True)


      Generates children with the given ids in the given db_map.
      If the first id is True, then generates *all* children with the given db_map.


   .. method:: find_rows_by_id(self, db_map, *ids, reverse=True)



   .. method:: _find_unsorted_rows_by_id(self, db_map, *ids)


      Generates rows corresponding to children with the given ids in the given db_map.
      If the first id is True, then generates rows corresponding to *all* children with the given db_map.


   .. method:: data(self, column, role=Qt.DisplayRole)


      Returns data for given column and role.


   .. method:: default_parameter_data(self)


      Returns data to set as default in a parameter table when this item is selected.



.. py:class:: TreeRootItem

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.MultiDBTreeItem`

   .. attribute:: item_type
      :annotation: = root

      

   .. method:: display_id(self)
      :property:


      "See super class.


   .. method:: display_name(self)
      :property:


      "See super class.



.. py:class:: ObjectTreeRootItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.TreeRootItem`

   An object tree root item.

   .. method:: _get_children_ids(self, db_map)


      Returns a set of object class ids.


   .. method:: child_item_type(self)
      :property:


      Returns an ObjectClassItem.



.. py:class:: RelationshipTreeRootItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.TreeRootItem`

   A relationship tree root item.

   .. method:: _get_children_ids(self, db_map)


      Returns a set of relationship class ids.


   .. method:: child_item_type(self)
      :property:


      Returns a RelationshipClassItem.



.. py:class:: EntityClassItem

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.MultiDBTreeItem`

   An entity class item.

   .. method:: data(self, column, role=Qt.DisplayRole)


      Returns data for given column and role.



.. py:class:: ObjectClassItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.EntityClassItem`

   An object class item.

   .. attribute:: item_type
      :annotation: = object class

      

   .. method:: display_icon(self)
      :property:


      Returns the object class icon.


   .. method:: _get_children_ids(self, db_map)


      Returns a set of object ids in this class.


   .. method:: child_item_type(self)
      :property:


      Returns an ObjectItem.


   .. method:: default_parameter_data(self)


      Return data to put as default in a parameter table when this item is selected.



.. py:class:: RelationshipClassItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.EntityClassItem`

   A relationship class item.

   .. attribute:: visual_key
      :annotation: = ['name', 'object_class_name_list']

      

   .. attribute:: item_type
      :annotation: = relationship class

      

   .. method:: display_icon(self)
      :property:


      Returns relationship class icon.


   .. method:: _get_children_ids(self, db_map)


      Returns a set of relationship ids in this class.
      If the parent is an ObjectItem, then only returns ids of relationships involving that object.


   .. method:: child_item_type(self)
      :property:


      Returns a RelationshipItem.


   .. method:: default_parameter_data(self)


      Return data to put as default in a parameter table when this item is selected.



.. py:class:: EntityItem

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.MultiDBTreeItem`

   An entity item.

   .. method:: data(self, column, role=Qt.DisplayRole)


      Returns data for given column and role.



.. py:class:: ObjectItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.EntityItem`

   An object item.

   .. attribute:: item_type
      :annotation: = object

      

   .. method:: _get_children_ids(self, db_map)


      Returns a set of relationship class ids involving this item's class.


   .. method:: child_item_type(self)
      :property:


      Returns a RelationshipClassItem.


   .. method:: display_icon(self)
      :property:


      Returns the object class icon.


   .. method:: default_parameter_data(self)


      Return data to put as default in a parameter table when this item is selected.



.. py:class:: RelationshipItem(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.entity_tree_item.EntityItem`

   An object item.

   Overridden method to parse some data for convenience later.
   Also make sure we never try to fetch this item.

   .. attribute:: visual_key
      :annotation: = ['name', 'object_name_list']

      

   .. attribute:: item_type
      :annotation: = relationship

      

   .. method:: object_name_list(self)
      :property:



   .. method:: display_name(self)
      :property:


      "Returns the name for display.


   .. method:: display_icon(self)
      :property:


      Returns relationship class icon.


   .. method:: has_children(self)


      Returns false, this item never has children.


   .. method:: default_parameter_data(self)


      Return data to put as default in a parameter table when this item is selected.


   .. method:: _get_children_ids(self, db_map)
      :abstractmethod:


      See base class.



