:mod:`spinetoolbox.project_items.exporter.widgets.parameter_index_settings_window`
==================================================================================

.. py:module:: spinetoolbox.project_items.exporter.widgets.parameter_index_settings_window

.. autoapi-nested-parse::

   Parameter indexing settings window for .gdx export.

   :author: A. Soininen (VTT)
   :date:   25.11.2019



Module Contents
---------------

.. py:class:: ParameterIndexSettingsWindow(indexing_settings, available_existing_domains, new_domains, database_path, parent)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A window which shows a list of ParameterIndexSettings widgets, one for each parameter with indexed values.

   :param indexing_settings: a map from parameter name to IndexingSettings
   :type indexing_settings: dict
   :param available_existing_domains: a map from existing domain names to lists of record keys
   :type available_existing_domains: dict
   :param new_domains: a map from new domain names to lists of record keys
   :type new_domains: dict
   :param database_path: a database url
   :type database_path: str
   :param parent: a parent widget
   :type parent: QWidget

   .. attribute:: settings_approved
      

      Emitted when the settings have been approved.


   .. attribute:: settings_rejected
      

      Emitted when the settings have been rejected.


   .. method:: indexing_settings(self)
      :property:


      indexing settings dictionary


   .. method:: new_domains(self)
      :property:


      list of additional domains needed for indexing


   .. method:: reorder_indexes(self, domain_name, first, last, target)



   .. method:: _collect_and_hide(self)


      Collects settings from individual ParameterIndexSettings widgets and hides the window.


   .. method:: _reject_and_close(self)




