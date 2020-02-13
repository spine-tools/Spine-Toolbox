:mod:`spinetoolbox.mvcmodels.entity_list_models`
================================================

.. py:module:: spinetoolbox.mvcmodels.entity_list_models

.. autoapi-nested-parse::

   List models for object and relationship classes.

   :authors: M. Marin (KTH)
   :date:   28.6.2019



Module Contents
---------------

.. py:class:: EntityListModel(graph_view_form, db_mngr, db_map)

   Bases: :class:`PySide2.QtGui.QStandardItemModel`

   A model for listing entity classes in the GraphViewForm.

   Initialize class

   .. method:: add_more_icon(self)
      :property:



   .. method:: entity_type(self)
      :property:



   .. method:: _get_entity_class_ids(self)
      :abstractmethod:



   .. method:: populate_list(self)


      Populate model.


   .. method:: add_entity_class(self, entity_class_id)


      Add entity class item to model.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the data stored under the given role for the item referred to by the index.


   .. method:: _data(self, index)



   .. method:: receive_entity_classes_added(self, db_map_data)


      Runs when entity classes are added.


   .. method:: receive_entity_classes_updated(self, db_map_data)


      Runs when entity classes are update.


   .. method:: receive_entity_classes_removed(self, db_map_data)


      Runs when entity classes are removed.


   .. method:: flags(self, index)




.. py:class:: ObjectClassListModel

   Bases: :class:`spinetoolbox.mvcmodels.entity_list_models.EntityListModel`

   A model for listing object classes in the GraphViewForm.

   .. method:: add_more_icon(self)
      :property:



   .. method:: entity_type(self)
      :property:



   .. method:: _get_entity_class_ids(self)




.. py:class:: RelationshipClassListModel

   Bases: :class:`spinetoolbox.mvcmodels.entity_list_models.EntityListModel`

   A model for listing relationship classes in the GraphViewForm.

   .. method:: add_more_icon(self)
      :property:



   .. method:: entity_type(self)
      :property:



   .. method:: _get_entity_class_ids(self)




