:mod:`spinetoolbox.mvcmodels.parameter_mixins`
==============================================

.. py:module:: spinetoolbox.mvcmodels.parameter_mixins

.. autoapi-nested-parse::

   Miscelaneous mixins for parameter models

   :authors: M. Marin (KTH)
   :date:   4.10.2019



Module Contents
---------------

.. function:: _parse_csv_list(csv_list)


.. py:class:: ConvertToDBMixin

   Base class for all mixins that convert model items (name-based) into database items (id-based).

   .. method:: build_lookup_dictionary(self, db_map_data)


      Begins an operation to convert items.


   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict



.. py:class:: FillInParameterNameMixin

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Fills in parameter names.

   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict



.. py:class:: FillInValueListIdMixin(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Fills in value list ids.

   Initializes lookup dicts.

   .. method:: build_lookup_dictionary(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict


   .. method:: _fill_in_value_list_id(self, item, db_map)


      Fills in the value list id in the given db item.

      :param item: the db item
      :type item: dict
      :param db_map: the database where the given item belongs
      :type db_map: DiffDatabaseMapping

      :returns: error log
      :rtype: list



.. py:class:: MakeParameterTagMixin(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Makes parameter tag items.

   Initializes lookup dicts.

   .. method:: build_lookup_dictionary(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _make_parameter_definition_tag(self, item, db_map)


      Returns a db parameter definition tag item (id-based) from the given model parameter definition item (name-based).

      :param item: the model parameter definition item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db parameter definition tag item
                list: error log
      :rtype: dict



.. py:class:: FillInEntityClassIdMixin(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Fills in entity class ids.

   Initializes lookup dicts.

   .. method:: build_lookup_dictionary(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _fill_in_entity_class_id(self, item, db_map)


      Fills in the entity class id in the given db item.

      :param item: the db item
      :type item: dict
      :param db_map: the database where the given item belongs
      :type db_map: DiffDatabaseMapping

      :returns: error log
      :rtype: list


   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict



.. py:class:: FillInEntityIdsMixin(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Fills in entity ids.

   Initializes lookup dicts.

   .. attribute:: _add_entities_on_the_fly
      :annotation: = False

      

   .. method:: build_lookup_dictionary(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _fill_in_entity_ids(self, item, db_map)


      Fills in all possible entity ids keyed by entity class id in the given db item
      (as there can be more than entity for the same name).

      :param item: the db item
      :type item: dict
      :param db_map: the database where the given item belongs
      :type db_map: DiffDatabaseMapping

      :returns: error log
      :rtype: list


   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict



.. py:class:: FillInParameterDefinitionIdsMixin(*args, **kwargs)

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Fills in parameter definition ids.

   Initializes lookup dicts.

   .. method:: build_lookup_dictionary(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _fill_in_parameter_ids(self, item, db_map)


      Fills in all possible parameter definition ids keyed by entity class id in the given db item
      (as there can be more than parameter definition for the same name).

      :param item: the db item
      :type item: dict
      :param db_map: the database where the given item belongs
      :type db_map: DiffDatabaseMapping

      :returns: error log
      :rtype: list


   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict



.. py:class:: InferEntityClassIdMixin

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.ConvertToDBMixin`

   Infers object class ids.

   .. method:: _convert_to_db(self, item, db_map)


      Returns a db item (id-based) from the given model item (name-based).

      :param item: the model item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db item
                list: error log
      :rtype: dict


   .. method:: _infer_and_fill_in_entity_class_id(self, item, db_map)


      Fills the entity class id in the given db item, by intersecting entity ids and parameter ids.
      Then picks the correct entity id and parameter definition id.
      Also sets the inferred entity class name in the model.

      :param item: the db item
      :type item: dict
      :param db_map: the database where the given item belongs
      :type db_map: DiffDatabaseMapping

      :returns: error log
      :rtype: list



.. py:class:: MakeRelationshipOnTheFlyMixin(*args, **kwargs)

   Makes relationships on the fly.

   Initializes lookup dicts.

   .. method:: _make_unique_relationship_id(item)
      :staticmethod:


      Returns a unique name-based identifier for db relationships.


   .. method:: build_lookup_dictionaries(self, db_map_data)


      Builds a name lookup dictionary for the given data.

      :param db_map_data: lists of model items keyed by DiffDatabaseMapping.
      :type db_map_data: dict


   .. method:: _make_relationship_on_the_fly(self, item, db_map)


      Returns database relationship item (id-based) from the given model parameter value item (name-based).

      :param item: the model parameter value item
      :type item: dict
      :param db_map: the database where the resulting item belongs
      :type db_map: DiffDatabaseMapping

      :returns: the db relationship item
                list: error log
      :rtype: dict



