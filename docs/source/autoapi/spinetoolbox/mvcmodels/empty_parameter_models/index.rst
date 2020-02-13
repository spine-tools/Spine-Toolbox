:mod:`spinetoolbox.mvcmodels.empty_parameter_models`
====================================================

.. py:module:: spinetoolbox.mvcmodels.empty_parameter_models

.. autoapi-nested-parse::

   Empty models for parameter definitions and values.

   :authors: M. Marin (KTH)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: EmptyParameterModel(parent, header, db_mngr)

   Bases: :class:`spinetoolbox.mvcmodels.empty_row_model.EmptyRowModel`

   An empty parameter model.

   Initialize class.

   :param parent: the parent object, typically a CompoundParameterModel
   :type parent: Object
   :param header: list of field names for the header
   :type header: list
   :param db_mngr:
   :type db_mngr: SpineDBManager

   .. method:: entity_class_type(self)
      :property:


      Either 'object class' or 'relationship class'.


   .. method:: entity_class_id_key(self)
      :property:



   .. method:: entity_class_name_key(self)
      :property:



   .. method:: can_be_filtered(self)
      :property:



   .. method:: accepted_rows(self)



   .. method:: db_item(self, _index)



   .. method:: flags(self, index)



   .. method:: _make_unique_id(self, item)


      Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added.


   .. method:: get_entity_parameter_data(self, db_map, ids=None)
      :abstractmethod:


      Returns object or relationship parameter definitions or values.
      Must be reimplemented in subclasses according to the entity type and to whether
      it's a definition or value model. Used by receive_parameter_data_added.


   .. method:: receive_parameter_data_added(self, db_map_data)


      Runs when parameter definitions or values are added.
      Finds and removes model items that were successfully added to the db.


   .. method:: batch_set_data(self, indexes, data)


      Sets data for indexes in batch. If successful, add items to db.


   .. method:: add_items_to_db(self, rows)
      :abstractmethod:


      Add items to db.

      :param rows: add data from these rows
      :type rows: set


   .. method:: _make_db_map_data(self, rows)


      Returns model data grouped by database map.

      :param rows: group data from these rows
      :type rows: set



.. py:class:: EmptyParameterDefinitionModel

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInValueListIdMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInEntityClassIdMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInParameterNameMixin`, :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterModel`

   An empty parameter definition model.

   .. method:: add_items_to_db(self, rows)


      Add items to db.

      :param rows: add data from these rows
      :type rows: set


   .. method:: _check_item(self, item)


      Checks if a db item is ready to be inserted.



.. py:class:: EmptyObjectParameterDefinitionModel

   Bases: :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterDefinitionModel`

   An empty object parameter definition model.

   .. method:: entity_class_type(self)
      :property:



   .. method:: get_entity_parameter_data(self, db_map, ids=None)


      Returns object parameter definitions. Used by receive_parameter_data_added.



.. py:class:: EmptyRelationshipParameterDefinitionModel

   Bases: :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterDefinitionModel`

   An empty relationship parameter definition model.

   .. method:: entity_class_type(self)
      :property:



   .. method:: get_entity_parameter_data(self, db_map, ids=None)


      Returns relationship parameter definitions. Used by receive_parameter_data_added.


   .. method:: flags(self, index)


      Additional hack to make the object_class_name_list column non-editable.



.. py:class:: EmptyParameterValueModel

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.InferEntityClassIdMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInParameterDefinitionIdsMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInEntityIdsMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInEntityClassIdMixin`, :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterModel`

   An empty parameter value model.

   .. method:: entity_type(self)
      :property:


      Either 'object' or "relationship'.


   .. method:: entity_id_key(self)
      :property:



   .. method:: entity_name_key(self)
      :property:



   .. method:: entity_name_key_in_cache(self)
      :property:



   .. method:: _make_unique_id(self, item)


      Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added.


   .. method:: add_items_to_db(self, rows)


      Add items to db.

      :param rows: add data from these rows
      :type rows: set


   .. method:: _check_item(self, item)


      Checks if a db item is ready to be inserted.



.. py:class:: EmptyObjectParameterValueModel

   Bases: :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterValueModel`

   An empty object parameter value model.

   .. method:: entity_class_type(self)
      :property:



   .. method:: entity_type(self)
      :property:



   .. method:: get_entity_parameter_data(self, db_map, ids=None)


      Returns object parameter values. Used by receive_parameter_data_added.



.. py:class:: EmptyRelationshipParameterValueModel

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.MakeRelationshipOnTheFlyMixin`, :class:`spinetoolbox.mvcmodels.empty_parameter_models.EmptyParameterValueModel`

   An empty relationship parameter value model.

   .. attribute:: _add_entities_on_the_fly
      :annotation: = True

      

   .. method:: entity_class_type(self)
      :property:



   .. method:: entity_type(self)
      :property:



   .. method:: get_entity_parameter_data(self, db_map, ids=None)


      Returns relationship parameter values. Used by receive_parameter_data_added.


   .. method:: add_items_to_db(self, rows)


      Add items to db.

      :param rows: add data from these rows
      :type rows: set



