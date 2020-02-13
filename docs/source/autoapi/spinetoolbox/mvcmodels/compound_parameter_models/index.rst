:mod:`spinetoolbox.mvcmodels.compound_parameter_models`
=======================================================

.. py:module:: spinetoolbox.mvcmodels.compound_parameter_models

.. autoapi-nested-parse::

   Compound models for object parameter definitions and values.
   These models concatenate several 'single' models and one 'empty' model.

   :authors: M. Marin (KTH)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: CompoundParameterModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.compound_table_model.CompoundWithEmptyTableModel`

   A model that concatenates several single parameter models
   and one empty parameter model.

   Initializes model.

   :param parent: the parent object
   :type parent: DataStoreForm
   :param db_mngr: the database manager
   :type db_mngr: SpineDBManager
   :param \*db_maps: the database maps included in the model
   :type \*db_maps: DiffDatabaseMapping

   .. attribute:: remove_selection_requested
      

      

   .. method:: entity_class_type(self)
      :property:


      Returns the entity class type, either 'object class' or 'relationship class'.

      :returns: str


   .. method:: item_type(self)
      :property:


      Returns the parameter item type, either 'parameter definition' or 'parameter value'.

      :returns: str


   .. method:: _single_model_type(self)
      :property:


      Returns a constructor for the single models.

      :returns: SingleParameterModel


   .. method:: _empty_model_type(self)
      :property:


      Returns a constructor for the empty model.

      :returns: EmptyParameterModel


   .. method:: _entity_class_id_key(self)
      :property:


      Returns the key of the entity class id in the model items (either "object_class_id" or "relationship_class_id")

      :returns: str


   .. method:: headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole)


      Returns an italic font in case the given column has an autofilter installed.


   .. method:: _get_entity_classes(self, db_map)
      :abstractmethod:


      Returns a list of entity classes from the given db_map.

      :param db_map:
      :type db_map: DiffDatabaseMapping

      :returns: list


   .. method:: _create_single_models(self)


      Returns a list of single models for this compound model, one for each entity class in each database.

      :returns: list


   .. method:: _create_empty_model(self)


      Returns the empty model for this compound model.

      :returns: EmptyParameterModel


   .. method:: filter_accepts_model(self, model)


      Returns a boolean indicating whether or not the given model should be included in this compound model.

      :param model:
      :type model: SingleParameterModel, EmptyParameterModel

      :returns: bool


   .. method:: _main_filter_accepts_model(self, model)



   .. method:: _auto_filter_accepts_model(self, model)



   .. method:: accepted_single_models(self)


      Returns a list of accepted single models by calling filter_accepts_model
      on each of them, just for convenience.

      :returns: list


   .. method:: _settattr_if_different(obj, attr, val)
      :staticmethod:


      Sets the given attribute of the given object to the given value if it's different
      from the one currently stored. Used for updating filters.

      :returns: True if the attributed was set, False otherwise
      :rtype: bool


   .. method:: update_main_filter(self)


      Updates and applies the main filter.


   .. method:: update_compound_main_filter(self)


      Updates the main filter in the compound model by setting the _accepted_entity_class_ids attribute.

      :returns: True if the filter was updated, None otherwise
      :rtype: bool


   .. method:: update_single_main_filter(self, model)


      Updates the filter in the given single model by setting its _selected_param_def_ids attribute.

      :param model:
      :type model: SingleParameterModel

      :returns: True if the filter was updated, None otherwise
      :rtype: bool


   .. method:: update_auto_filter(self, column, auto_filter)


      Updates and applies the auto filter.

      :param column: the column number
      :type column: int
      :param auto_filter: list of accepted values for the column keyed by tuple (database map, entity class id)
      :type auto_filter: dict


   .. method:: update_compound_auto_filter(self, column, auto_filter)


      Updates the auto filter for given column in the compound model.

      :param column: the column number
      :type column: int
      :param auto_filter: list of accepted values for the column keyed by tuple (database map, entity class id)
      :type auto_filter: dict


   .. method:: update_single_auto_filter(self, model, column)


      Updates the auto filter for given column in the given single model.

      :param model: the model
      :type model: SingleParameterModel
      :param column: the column number
      :type column: int

      :returns: True if the auto-filtered values were updated, None otherwise
      :rtype: bool


   .. method:: _row_map_for_model(self, model)


      Returns the row map for the given model.
      Reimplemented to take filter status into account.

      :param model:
      :type model: SingleParameterModel, EmptyParameterModel

      :returns: tuples (model, row number) for each accepted row
      :rtype: list


   .. method:: auto_filter_menu_data(self, column)


      Returns auto filter menu data for the given column.

      :returns: AutoFilterMenuItem instances to populate the auto filter menu.
      :rtype: list


   .. method:: _models_with_db_map(self, db_map)


      Returns a collection of single models with given db_map.

      :param db_map:
      :type db_map: DiffDatabaseMapping

      :returns: list


   .. method:: receive_entity_classes_removed(self, db_map_data)


      Runs when entity classes are removed from the dbs.
      Removes sub-models for the given entity classes and dbs.

      :param db_map_data: list of removed dict-items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: receive_parameter_data_updated(self, db_map_data)


      Runs when either parameter definitions or values are updated in the dbs.
      Emits dataChanged so the parameter_name column is refreshed.

      :param db_map_data: list of updated dict-items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _entity_ids_per_class_id(self, items)


      Returns a dict mapping entity class ids to a set of entity ids.

      :param items:
      :type items: list

      :returns: dict


   .. method:: receive_parameter_data_removed(self, db_map_data)


      Runs when either parameter definitions or values are removed from the dbs.
      Removes the affected rows from the corresponding single models.

      :param db_map_data: list of removed dict-items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: receive_parameter_data_added(self, db_map_data)


      Runs when either parameter definitions or values are added to the dbs.
      Adds necessary sub-models and initializes them with data.
      Also notifies the empty model so it can remove rows that are already in.

      :param db_map_data: list of removed dict-items keyed by DiffDatabaseMapping
      :type db_map_data: dict


   .. method:: _emit_data_changed_for_column(self, field)


      Lazily emits data changed for an entire column.

      :param field: the column header
      :type field: str


   .. method:: db_item(self, index)



   .. method:: value_name(self, index)




.. py:class:: CompoundObjectParameterMixin

   Implements the interface for populating and filtering a compound object parameter model.

   .. method:: entity_class_type(self)
      :property:



   .. method:: _get_entity_classes(self, db_map)




.. py:class:: CompoundRelationshipParameterMixin

   Implements the interface for populating and filtering a compound relationship parameter model.

   .. method:: entity_class_type(self)
      :property:



   .. method:: _get_entity_classes(self, db_map)




.. py:class:: CompoundParameterDefinitionMixin

   Handles signals from db mngr for parameter definition models.

   .. method:: item_type(self)
      :property:



   .. method:: receive_parameter_definition_tags_set(self, db_map_data)




.. py:class:: CompoundParameterValueMixin

   Handles signals from db mngr for parameter value models.

   .. method:: item_type(self)
      :property:



   .. method:: entity_type(self)
      :property:


      Returns the entity type, either 'object' or 'relationship'
      Used by update_single_main_filter.

      :returns: str


   .. method:: update_single_main_filter(self, model)


      Update the filter for the given model.



.. py:class:: CompoundObjectParameterDefinitionModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundObjectParameterMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterDefinitionMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterModel`

   A model that concatenates several single object parameter definition models
   and one empty object parameter definition model.

   Initializes model header.


.. py:class:: CompoundRelationshipParameterDefinitionModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundRelationshipParameterMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterDefinitionMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterModel`

   A model that concatenates several single relationship parameter definition models
   and one empty relationship parameter definition model.

   Initializes model header.


.. py:class:: CompoundObjectParameterValueModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundObjectParameterMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterValueMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterModel`

   A model that concatenates several single object parameter value models
   and one empty object parameter value model.

   Initializes model header.

   .. method:: entity_type(self)
      :property:




.. py:class:: CompoundRelationshipParameterValueModel(parent, db_mngr, *db_maps)

   Bases: :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundRelationshipParameterMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterValueMixin`, :class:`spinetoolbox.mvcmodels.compound_parameter_models.CompoundParameterModel`

   A model that concatenates several single relationship parameter value models
   and one empty relationship parameter value model.

   Initializes model header.

   .. method:: entity_type(self)
      :property:




