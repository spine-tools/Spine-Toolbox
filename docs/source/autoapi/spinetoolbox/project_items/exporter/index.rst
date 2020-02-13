:mod:`spinetoolbox.project_items.exporter`
==========================================

.. py:module:: spinetoolbox.project_items.exporter

.. autoapi-nested-parse::

   Exporter project item plugin.

   :author: A. Soininen (VTT)
   :date:   25.9.2019



Subpackages
-----------
.. toctree::
   :titlesonly:
   :maxdepth: 3

   widgets/index.rst


Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   exporter/index.rst
   exporter_icon/index.rst
   list_utils/index.rst
   settings_state/index.rst
   worker/index.rst


Package Contents
----------------

.. py:class:: item_maker(name, description, settings_packs, x, y, toolbox, project, logger)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   This project item handles all functionality regarding exporting a database to a file.

   Currently, only .gdx format is supported.

   :param name: item name
   :type name: str
   :param description: item description
   :type description: str
   :param settings_packs: dicts mapping database URLs to _SettingsPack objects
   :type settings_packs: list
   :param x: initial X coordinate of item icon
   :type x: float
   :param y: initial Y coordinate of item icon
   :type y: float
   :param toolbox: a ToolboxUI instance
   :type toolbox: ToolboxUI
   :param project: the project this item belongs to
   :type project: SpineToolboxProject
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. method:: item_type()
      :staticmethod:


      See base class.


   .. method:: category()
      :staticmethod:


      See base class.


   .. method:: make_signal_handler_dict(self)


      Returns a dictionary of all shared signals and their handlers.


   .. method:: activate(self)


      Restores selections and connects signals.


   .. method:: deactivate(self)


      Saves selections and disconnects signals.


   .. method:: _update_properties_tab(self)


      Updates the database list in the properties tab.


   .. method:: execute_forward(self, resources)


      See base class.


   .. method:: _do_handle_dag_changed(self, resources)


      See base class.


   .. method:: _start_worker(self, database_url)


      Starts fetching settings using a worker in another thread.


   .. method:: _update_export_settings(self, database_url, settings)


      Sets new settings for given database.


   .. method:: _update_indexing_settings(self, database_url, indexing_settings)


      Sets new indexing settings for given database.


   .. method:: _worker_finished(self, database_url)


      Cleans up after a worker has finished fetching export settings.


   .. method:: _worker_failed(self, database_url, exception)


      Clean up after a worker has failed fetching export settings.


   .. method:: _check_state(self, clear_before_check=True)


      Checks the status of database export settings.

      Updates both the notification message (exclamation icon) and settings states.


   .. method:: _check_missing_file_names(self)


      Checks the status of output file names.


   .. method:: _check_duplicate_file_names(self)


      Checks for duplicate output file names.


   .. method:: _check_missing_parameter_indexing(self)


      Checks the status of parameter indexing settings.


   .. method:: _check_erroneous_databases(self)


      Checks errors in settings fetching from a database.


   .. method:: _report_notifications(self)


      Updates the exclamation icon and notifications labels.


   .. method:: _show_settings(self, database_url)


      Opens the item's settings window.


   .. method:: _reset_settings_window(self, database_url)


      Sends new settings to Gdx Export Settings window.


   .. method:: _dispose_settings_window(self, database_url)


      Deletes rejected export settings windows.


   .. method:: _update_out_file_name(self, file_name, database_path)


      Updates the output file name for given database


   .. method:: _update_settings_from_settings_window(self, database_path)


      Updates the export settings for given database from the settings window.


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item's configuration.


   .. method:: _discard_settings_window(self, database_path)


      Discards the settings window for given database.


   .. method:: _send_settings_to_window(self, database_url)


      Resets settings in given export settings window.


   .. method:: update_name_label(self)


      See base class.


   .. method:: _resolve_gams_system_directory(self)


      Returns GAMS system path from Toolbox settings or None if GAMS default is to be used.


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: _update_settings_after_db_commit(self, committed_db_maps)


      Refreshes export settings for databases after data has been committed to them.


   .. method:: default_name_prefix()
      :staticmethod:


      See base class.


   .. method:: output_resources_forward(self)


      See base class.


   .. method:: tear_down(self)


      See base class.



.. py:class:: icon_maker(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   Exporter icon for the Design View.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolBoxUI
   :param x: Icon x coordinate
   :type x: float
   :param y: Icon y coordinate
   :type y: float
   :param w: Width of master icon
   :type w: float
   :param h: Height of master icon
   :type h: float
   :param name: Item name
   :type name: str


.. py:class:: add_form_maker(toolbox, x, y)

   Bases: :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`

   A widget to query user's preferences for a new item.

   :param toolbox: Parent widget
   :type toolbox: ToolboxUI
   :param x: X coordinate of new item
   :type x: int
   :param y: Y coordinate of new item
   :type y: int

   .. method:: call_add_item(self)


      Creates new Item according to user's selections.



.. py:class:: properties_widget_maker(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A main window widget to show Gdx Export item's properties.

   :param toolbox: a main window instance
   :type toolbox: ToolboxUI

   .. method:: ui(self)
      :property:


      The UI form of this widget.



.. data:: item_rank
   :annotation: = 5

   

.. data:: item_category
   

   

.. data:: item_type
   

   

.. data:: item_icon
   :annotation: = :/icons/project_item_icons/database-export.svg

   

