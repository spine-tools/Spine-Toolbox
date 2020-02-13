:mod:`spinetoolbox.mvcmodels.data_package_models`
=================================================

.. py:module:: spinetoolbox.mvcmodels.data_package_models

.. autoapi-nested-parse::

   Classes for models dealing with Data Packages.

   :authors: M. Marin (KTH)
   :date:   24.6.2018



Module Contents
---------------

.. py:class:: DatapackageResourcesModel(parent)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A model of datapackage resource data, used by SpineDatapackageWidget.

   :param parent:
   :type parent: SpineDatapackageWidget

   .. method:: reset_model(self, resources)



   .. method:: flags(self, index)




.. py:class:: DatapackageFieldsModel(parent)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A model of datapackage field data, used by SpineDatapackageWidget.

   :param parent:
   :type parent: SpineDatapackageWidget

   .. method:: reset_model(self, schema)




.. py:class:: DatapackageForeignKeysModel(parent)

   Bases: :class:`spinetoolbox.mvcmodels.empty_row_model.EmptyRowModel`

   A model of datapackage foreign key data, used by SpineDatapackageWidget.

   :param parent:
   :type parent: SpineDatapackageWidget

   .. method:: reset_model(self, foreign_keys)




