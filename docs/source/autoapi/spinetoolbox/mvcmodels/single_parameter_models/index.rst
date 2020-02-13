:mod:`spinetoolbox.mvcmodels.single_parameter_models`
=====================================================

.. py:module:: spinetoolbox.mvcmodels.single_parameter_models

.. autoapi-nested-parse::

   Single models for parameter definitions and values (as 'for a single entity').

   :authors: M. Marin (KTH)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: SingleParameterModel(parent, header, db_mngr, db_map, entity_class_id, lazy=True)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A parameter model for a single entity class to go in a CompoundParameterModel.
   Provides methods to associate the model to an entity class as well as
   to filter entities within the class.

   Init class.

   :param parent: the parent object
   :type parent: CompoundParameterModel
   :param header: list of field names for the header
   :type header: list

   .. method:: item_type(self)
      :property:


      The item type, either 'parameter value' or 'parameter definition', required by the data method.


   .. method:: entity_class_type(self)
      :property:


      The entity class type, either 'object class' or 'relationship class'.


   .. method:: json_fields(self)
      :property:



   .. method:: fixed_fields(self)
      :property:



   .. method:: group_fields(self)
      :property:



   .. method:: parameter_definition_id_key(self)
      :property:



   .. method:: can_be_filtered(self)
      :property:



   .. method:: insertRows(self, row, count, parent=QModelIndex())


      This model doesn't support row insertion.


   .. method:: db_item(self, index)



   .. method:: flags(self, index)


      Make fixed indexes non-editable.


   .. method:: fetchMore(self, parent=None)


      Fetch data and use it to reset the model.


   .. method:: _fetch_data(self)
      :abstractmethod:


      Returns data to reset the model with and call it fetched.
      Reimplement in subclasses if you want to populate your model automatically.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Gets the id and database for the row, and reads data from the db manager
      using the item_type property.
      Paint the object class icon next to the name.
      Also paint background of fixed indexes gray and apply custom format to JSON fields.


   .. method:: batch_set_data(self, indexes, data)


      Sets data for indexes in batch.
      Sets data directly in database using db mngr. If successful, updated data will be
      automatically seen by the data method.


   .. method:: update_items_in_db(self, items)
      :abstractmethod:


      Update items in db. Required by batch_set_data


   .. method:: _filter_accepts_row(self, row)



   .. method:: _main_filter_accepts_row(self, row)


      Applies the main filter, defined by the selections in the grand parent.


   .. method:: _auto_filter_accepts_row(self, row)


      Applies the autofilter, defined by the autofilter drop down menu.


   .. method:: accepted_rows(self)


      Returns a list of accepted rows, for convenience.



.. py:class:: SingleObjectParameterMixin

   Associates a parameter model with a single object class.

   .. method:: entity_class_type(self)
      :property:




.. py:class:: SingleRelationshipParameterMixin

   Associates a parameter model with a single relationship class.

   .. method:: entity_class_type(self)
      :property:




.. py:class:: SingleParameterDefinitionMixin

   Bases: :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInParameterNameMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.FillInValueListIdMixin`, :class:`spinetoolbox.mvcmodels.parameter_mixins.MakeParameterTagMixin`

   A parameter definition model for a single entity class.

   .. method:: item_type(self)
      :property:



   .. method:: update_items_in_db(self, items)


      Update items in db.

      :param item: dictionary-items
      :type item: list



.. py:class:: SingleParameterValueMixin(*args, **kwargs)

   A parameter value model for a single entity class.

   .. method:: item_type(self)
      :property:



   .. method:: _main_filter_accepts_row(self, row)


      Reimplemented to filter objects.


   .. method:: update_items_in_db(self, items)


      Update items in db.

      :param item: dictionary-items
      :type item: list



.. py:class:: SingleObjectParameterDefinitionModel

   Bases: :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleObjectParameterMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterDefinitionMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterModel`

   An object parameter definition model for a single object class.

   .. method:: _fetch_data(self)


      Returns object parameter definition ids.



.. py:class:: SingleRelationshipParameterDefinitionModel

   Bases: :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleRelationshipParameterMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterDefinitionMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterModel`

   A relationship parameter definition model for a single relationship class.

   .. method:: _fetch_data(self)


      Returns relationship parameter definition ids.



.. py:class:: SingleObjectParameterValueModel

   Bases: :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleObjectParameterMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterValueMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterModel`

   An object parameter value model for a single object class.

   .. method:: _fetch_data(self)


      Returns object parameter value ids.



.. py:class:: SingleRelationshipParameterValueModel

   Bases: :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleRelationshipParameterMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterValueMixin`, :class:`spinetoolbox.mvcmodels.single_parameter_models.SingleParameterModel`

   A relationship parameter value model for a single relationship class.

   .. method:: _fetch_data(self)


      Returns relationship parameter value ids.



