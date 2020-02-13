:mod:`spinetoolbox.project_items.importer.importer`
===================================================

.. py:module:: spinetoolbox.project_items.importer.importer

.. autoapi-nested-parse::

   Contains Importer project item class.

   :authors: P. Savolainen (VTT), P. Vennström (VTT), A. Soininen (VTT)
   :date:   10.6.2019



Module Contents
---------------

.. data:: _CONNECTOR_NAME_TO_CLASS
   

   

.. py:class:: Importer(name, description, mappings, x, y, toolbox, project, logger, cancel_on_error=True)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   Importer class.

   :param name: Project item name
   :type name: str
   :param description: Project item description
   :type description: str
   :param mappings: List where each element contains two dicts (path dict and mapping dict)
   :type mappings: list
   :param x: Initial icon scene X coordinate
   :type x: float
   :param y: Initial icon scene Y coordinate
   :type y: float
   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param project: the project this item belongs to
   :type project: SpineToolboxProject
   :param logger: a logger instance
   :type logger: LoggerInterface
   :param cancel_on_error: if True the item's execution will stop on import error
   :type cancel_on_error: bool

   .. method:: item_type()
      :staticmethod:


      See base class.


   .. method:: category()
      :staticmethod:


      See base class.


   .. method:: _handle_file_model_item_changed(self, item)



   .. method:: make_signal_handler_dict(self)


      Returns a dictionary of all shared signals and their handlers.
      This is to enable simpler connecting and disconnecting.


   .. method:: activate(self)


      Restores selections, cancel on error checkbox and connects signals.


   .. method:: deactivate(self)


      Saves selections and disconnects signals.


   .. method:: restore_selections(self)


      Restores selections into shared widgets when this project item is selected.


   .. method:: save_selections(self)


      Saves selections in shared widgets for this project item into instance variables.


   .. method:: update_name_label(self)


      Update Importer properties tab name label. Used only when renaming project items.


   .. method:: _handle_import_editor_clicked(self, checked=False)


      Opens Import editor for the file selected in list view.


   .. method:: _handle_files_double_clicked(self, index)


      Opens Import editor for the double clicked index.


   .. method:: open_import_editor(self, index)


      Opens Import editor for the given index.


   .. method:: get_connector(self, importee)


      Shows a QDialog to select a connector for the given source file.
      Mimics similar routine in `spine_io.widgets.import_widget.ImportDialog`

      :param importee: Path to file acting as an importee
      :type importee: str

      :returns: Asynchronous data reader class for the given importee


   .. method:: select_connector_type(self, index)


      Opens dialog to select connector type for the given index.


   .. method:: _connection_failed(self, msg, importee)



   .. method:: get_settings(self, importee)


      Returns the mapping dictionary for the file in given path.

      :param importee: Absolute path to a file, whose mapping is queried
      :type importee: str

      :returns: Mapping dictionary for the requested importee or an empty dict if not found
      :rtype: dict


   .. method:: save_settings(self, settings, importee)


      Updates an existing mapping or adds a new mapping
       (settings) after closing the import preview window.

      :param settings: Updated mapping (settings) dictionary
      :type settings: dict
      :param importee: Absolute path to a file, whose mapping has been updated
      :type importee: str


   .. method:: _preview_destroyed(self, importee)


      Destroys preview widget instance for the given importee.

      :param importee: Absolute path to a file, whose preview widget is destroyed
      :type importee: str


   .. method:: update_file_model(self, items)


      Adds given list of items to the file model. If None or
      an empty list is given, the model is cleared.

      :param items: Set of absolute file paths
      :type items: set


   .. method:: _run_importer_program(self, args)


      Starts and runs the importer program in a separate process.

      :param args: List of arguments for the importer program
      :type args: list


   .. method:: _log_importer_process_stdout(self)



   .. method:: _log_importer_process_stderr(self)



   .. method:: execute_backward(self, resources)


      See base class.


   .. method:: execute_forward(self, resources)


      See base class.


   .. method:: stop_execution(self)


      Stops executing this Importer.


   .. method:: _do_handle_dag_changed(self, resources)


      See base class.


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item.


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: default_name_prefix()
      :staticmethod:


      see base class


   .. method:: tear_down(self)


      Closes all preview widgets.


   .. method:: _notify_if_duplicate_file_paths(self, file_list)


      Adds a notification if file_list contains duplicate entries.


   .. method:: upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir)
      :staticmethod:


      Converts mappings to a list, where each element contains two dictionaries,
      the serialized path dictionary and the mapping dictionary for the file in that
      path.


   .. method:: deserialize_mappings(mappings, project_path)
      :staticmethod:


      Returns mapping settings as dict with absolute paths as keys.

      :param mappings: List where each element contains two dictionaries (path dict and mapping dict)
      :type mappings: list
      :param project_path: Path to project directory
      :type project_path: str

      :returns: Dictionary with absolute paths as keys and mapping settings as values
      :rtype: dict


   .. method:: serialize_mappings(mappings, project_path)
      :staticmethod:


      Returns a list of mappings, where each element contains two dictionaries,
      the 'serialized' path in a dictionary and the mapping dictionary.

      :param mappings: Dictionary with mapping specifications
      :type mappings: dict
      :param project_path: Path to project directory
      :type project_path: str

      :returns: List where each element contains two dictionaries.
      :rtype: list



.. function:: _fix_csv_connector_settings(settings)

   CSVConnector saved the table names as the filepath, change that
   to 'csv' instead. This function will mutate the dictionary.

   :param settings: Mapping settings that should be updated
   :type settings: dict


