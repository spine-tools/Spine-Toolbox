:mod:`spinetoolbox.project_items.exporter.exporter`
===================================================

.. py:module:: spinetoolbox.project_items.exporter.exporter

.. autoapi-nested-parse::

   Exporter project item.

   :author: A. Soininen (VTT)
   :date:   5.9.2019



Module Contents
---------------

.. py:class:: Exporter(name, description, settings_packs, x, y, toolbox, project, logger)

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



.. py:class:: _SettingsPack(output_file_name)

   Bases: :class:`PySide2.QtCore.QObject`

   Keeper of all settings and stuff needed for exporting a database.

   .. attribute:: output_file_name

      name of the export file

      :type: str

   .. attribute:: settings

      export settings

      :type: Settings

   .. attribute:: indexing_settings

      parameter indexing settings

      :type: dict

   .. attribute:: additional_domains

      extra domains needed for parameter indexing

      :type: list

   .. attribute:: settings_window

      settings editor window

      :type: GdxExportSettings

   :param output_file_name: name of the export file
   :type output_file_name: str

   .. attribute:: state_changed
      

      Emitted when the pack's state changes.


   .. method:: state(self)
      :property:


      State of the pack.


   .. method:: to_dict(self)


      Stores the settings pack into a JSON compatible dictionary.


   .. method:: from_dict(pack_dict, database_url)
      :staticmethod:


      Restores the settings pack from a dictionary.



.. py:class:: _Notifications

   Bases: :class:`PySide2.QtCore.QObject`

   Holds flags for different error conditions.

   .. attribute:: duplicate_output_file_name

      if True there are duplicate output file names

      :type: bool

   .. attribute:: missing_output_file_name

      if True the output file name is missing

      :type: bool

   .. attribute:: missing_parameter_indexing

      if True there are indexed parameters without indexing domains

      :type: bool

   .. attribute:: erroneous_database

      if True the database has issues

      :type: bool

   .. attribute:: changed_due_to_settings_state
      

      Emitted when notifications have changed due to changes in settings state.


   .. method:: __ior__(self, other)


      ORs the flags with another notifications.

      :param other: a _Notifications object
      :type other: _Notifications


   .. method:: update_settings_state(self, state)


      Updates the notifications according to settings state.



.. function:: _normalize_url(url)

   Normalized url's path separators to their OS specific characters.

   This function is needed during the transition period from no-version to version 1 project files.
   It should be removed once we are using version 1 files.


