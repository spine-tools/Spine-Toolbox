:mod:`spinetoolbox.project_items.tool`
======================================

.. py:module:: spinetoolbox.project_items.tool

.. autoapi-nested-parse::

   Tool plugin.

   :author: M. Marin (KTH)
   :date:   12.9.2019



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

   tool/index.rst
   tool_icon/index.rst


Package Contents
----------------

.. py:class:: item_maker(name, description, x, y, toolbox, project, logger, tool='', execute_in_work=True, cmd_line_args=None)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   Tool class.

   :param name: Object name
   :type name: str
   :param description: Object description
   :type description: str
   :param x: Initial X coordinate of item icon
   :type x: float
   :param y: Initial Y coordinate of item icon
   :type y: float
   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param project: the project this item belongs to
   :type project: SpineToolboxProject
   :param logger: a logger instance
   :type logger: LoggerInterface
   :param tool: Name of this Tool's Tool specification
   :type tool: str
   :param execute_in_work: Execute associated Tool specification in work (True) or source directory (False)
   :type execute_in_work: bool
   :param cmd_line_args: Tool command line arguments
   :type cmd_line_args: list

   .. method:: item_type()
      :staticmethod:


      See base class.


   .. method:: category()
      :staticmethod:


      See base class.


   .. method:: make_signal_handler_dict(self)


      Returns a dictionary of all shared signals and their handlers.
      This is to enable simpler connecting and disconnecting.


   .. method:: activate(self)


      Restore selections and connect signals.


   .. method:: deactivate(self)


      Save selections and disconnect signals.


   .. method:: restore_selections(self)


      Restore selections into shared widgets when this project item is selected.


   .. method:: save_selections(self)


      Save selections in shared widgets for this project item into instance variables.


   .. method:: update_execution_mode(self, checked)


      Slot for execute in work radio button toggled signal.


   .. method:: update_tool_specification(self, row)


      Update Tool specification according to selection in the specification comboBox.

      :param row: Selected row in the comboBox
      :type row: int


   .. method:: update_tool_cmd_line_args(self, txt)


      Updates tool cmd line args list as line edit text is changed.


   .. method:: set_tool_specification(self, tool_specification)


      Sets Tool specification for this Tool. Removes Tool specification if None given as argument.

      :param tool_specification: Tool specification of this Tool. None removes the specification.
      :type tool_specification: ToolSpecification


   .. method:: update_tool_ui(self)


      Updates Tool UI to show Tool specification details. Used when Tool specification is changed.
      Overrides execution mode (work or source) with the specification default.


   .. method:: update_tool_models(self)


      Update Tool models with Tool specification details. Used when Tool specification is changed.
      Overrides execution mode (work or source) with the specification default.


   .. method:: open_results(self, checked=False)


      Open output directory in file browser.


   .. method:: edit_tool_specification(self)


      Open Tool specification editor for the Tool specification attached to this Tool.


   .. method:: open_tool_specification_file(self)


      Open Tool specification file.


   .. method:: open_tool_main_program_file(self)


      Open Tool specification main program file in an external text edit application.


   .. method:: open_tool_main_directory(self)


      Open directory where the Tool specification main program is located in file explorer.


   .. method:: tool_specification(self)


      Returns Tool specification.


   .. method:: populate_source_file_model(self, items)


      Add required source files (includes) into a model.
      If items is None or an empty list, model is cleared.


   .. method:: populate_input_file_model(self, items)


      Add required Tool input files into a model.
      If items is None or an empty list, model is cleared.


   .. method:: populate_opt_input_file_model(self, items)


      Add optional Tool specification files into a model.
      If items is None or an empty list, model is cleared.


   .. method:: populate_output_file_model(self, items)


      Add Tool output files into a model.
      If items is None or an empty list, model is cleared.


   .. method:: populate_specification_model(self, populate)


      Add all tool specifications to a single QTreeView.

      :param populate: False to clear model, True to populate.
      :type populate: bool


   .. method:: update_name_label(self)


      Update Tool tab name label. Used only when renaming project items.


   .. method:: _update_base_directory(self)


      Updates the path to the base directory, depending on `execute_in_work`.


   .. method:: output_resources_forward(self)


      See base class.


   .. method:: _find_last_output_files(self)


      Returns a list of most recent output files from the results directory.

      :returns: list


   .. method:: execute_backward(self, resources)


      See base class.


   .. method:: execute_forward(self, resources)


      See base class.


   .. method:: count_files_and_dirs(self)


      Count the number of files and directories in required input files model.

      :returns: Tuple containing the number of required files and directories.


   .. method:: _optional_output_destination_paths(self, paths)


      Returns a dictionary telling where optional output files should be copied to before execution.

      :param paths: key is the optional file name pattern, value is a list of paths to source files
      :type paths: dict

      :returns: a map from source path to destination path
      :rtype: dict


   .. method:: create_input_dirs(self)


      Iterate items in required input files and check
      if there are any directories to create. Create found
      directories directly to work or source directory.

      :returns: Boolean variable depending on success


   .. method:: copy_input_files(self, paths)


      Copy input files from given paths to work or source directory, depending on
      where the Tool specification requires them to be.

      :param paths: Key is path to destination file, value is path to source file.
      :type paths: dict

      :returns: Boolean variable depending on operation success


   .. method:: _copy_optional_input_files(self, paths)


      Copy optional input files from given paths to work or source directory, depending on
      where the Tool specification requires them to be.

      :param paths: key is the source path, value is the destination path
      :type paths: dict


   .. method:: copy_program_files(self)


      Copies Tool specification source files to base directory.


   .. method:: _find_input_files(self, resources)


      Iterates files in required input files model and looks for them in the given resources.

      :param resources: resources available
      :type resources: list

      :returns: Dictionary mapping required files to path where they are found, or to None if not found


   .. method:: _find_optional_input_files(self, resources)


      Tries to find optional input files from previous project items in the DAG. Returns found paths.

      :param resources: resources available
      :type resources: list

      :returns: Dictionary of optional input file paths or an empty dictionary if no files found. Key is the
                optional input item and value is a list of paths that matches the item.


   .. method:: _filepaths_from_resources(resources)
      :staticmethod:


      Returns file paths from given resources.

      :param resources: resources available
      :type resources: list

      :returns: a list of file paths, possibly including patterns


   .. method:: _find_file(self, filename, resources)


      Returns all occurrences of full paths to given file name in resources available.

      :param filename: Searched file name (no path)
      :type filename: str
      :param resources: list of resources available from upstream items
      :type resources: list

      :returns: Full paths to file if found, None if not found
      :rtype: list


   .. method:: _find_optional_files(pattern, available_file_paths)
      :staticmethod:


      Returns a list of found paths to files that match the given pattern in files available
      from the execution instance.

      :param pattern: file pattern
      :type pattern: str
      :param available_file_paths: list of available file paths from upstream items
      :type available_file_paths: list

      :returns: List of (full) paths
      :rtype: list


   .. method:: handle_execution_finished(self, return_code)


      Handles Tool specification execution finished.

      :param return_code: Process exit code
      :type return_code: int


   .. method:: handle_output_files(self, ret)


      Copies Tool specification output files from work directory to result directory.

      :param ret: Tool specification process return value
      :type ret: int


   .. method:: create_output_dirs(self)


      Makes sure that work directory has the necessary output directories for Tool output files.
      Checks only "outputfiles" list. Alternatively you can add directories to "inputfiles" list
      in the tool definition file.

      :returns: True for success, False otherwise.
      :rtype: bool

      :raises OSError: If creating an output directory to work fails.


   .. method:: copy_output_files(self, target_dir)


      Copies Tool specification output files from work directory to given target directory.

      :param target_dir: Destination directory for Tool specification output files
      :type target_dir: str

      :returns: Contains two lists. The first list contains paths to successfully
                copied files. The second list contains paths (or patterns) of Tool specification
                output files that were not found.
      :rtype: tuple

      :raises OSError: If creating a directory fails.


   .. method:: stop_execution(self)


      Stops executing this Tool.


   .. method:: _do_handle_dag_changed(self, resources)


      See base class.


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item.


   .. method:: custom_context_menu(self, parent, pos)


      Returns the context menu for this item.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param pos: Position on screen
      :type pos: QPoint


   .. method:: apply_context_menu_action(self, parent, action)


      Applies given action from context menu. Implement in subclasses as needed.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param action: The selected action
      :type action: str


   .. method:: rename(self, new_name)


      Rename this item.

      :param new_name: New name
      :type new_name: str

      :returns: Boolean value depending on success
      :rtype: bool


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: default_name_prefix()
      :staticmethod:


      see base class


   .. method:: _file_path_duplicates(file_paths)
      :staticmethod:


      Returns a list of lists of duplicate items in file_paths.


   .. method:: _notify_if_duplicate_file_paths(self, duplicates)


      Adds a notification if duplicates contains items.


   .. method:: _flatten_file_path_duplicates(self, file_paths, log_duplicates=False)


      Flattens the extra duplicate dimension in file_paths.


   .. method:: _database_urls(resources)
      :staticmethod:


      Pries database URLs and their providers' names from resources.

      :param resources: a list of ProjectItemResource objects
      :type resources: list

      :returns: a mapping from resource provider's name to a database URL.
      :rtype: dict



.. py:class:: ToolIcon(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   Tool icon for the Design View.

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

   .. method:: _value_for_time(msecs)
      :staticmethod:



   .. method:: start_animation(self)


      Start the animation that plays when the Tool associated to this GraphicsItem is running.


   .. method:: stop_animation(self)


      Stop animation



.. py:class:: ToolPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the Tool Item Properties.

   :param toolbox: The toolbox instance where this widget should be embeded
   :type toolbox: ToolboxUI

   Init class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_tool_properties_context_menu(self, pos)


      Create and show a context-menu in Tool properties
      if selected Tool has a Tool specification.

      :param pos: Mouse position
      :type pos: QPoint



.. py:class:: AddToolWidget(toolbox, x, y)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget that queries user's preferences for a new item.

   .. attribute:: toolbox

      Parent widget

      :type: ToolboxUI

   .. attribute:: x

      X coordinate of new item

      :type: int

   .. attribute:: y

      Y coordinate of new item

      :type: int

   Initialize class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: update_args(self, row)


      Show Tool specification command line arguments in text input.

      :param row: Selected row number
      :type row: int


   .. method:: name_changed(self)


      Update label to show upcoming folder name.


   .. method:: ok_clicked(self)


      Check that given item name is valid and add it to project.


   .. method:: call_add_item(self)


      Creates new Item according to user's selections.


   .. method:: keyPressEvent(self, e)


      Close Setup form when escape key is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



.. data:: item_rank
   :annotation: = 2

   

.. data:: item_category
   

   

.. data:: item_type
   

   

.. data:: item_icon
   :annotation: = :/icons/project_item_icons/hammer.svg

   

.. data:: icon_maker
   

   

.. data:: properties_widget_maker
   

   

.. data:: add_form_maker
   

   

