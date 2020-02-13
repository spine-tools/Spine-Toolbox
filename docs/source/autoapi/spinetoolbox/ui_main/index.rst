:mod:`spinetoolbox.ui_main`
===========================

.. py:module:: spinetoolbox.ui_main

.. autoapi-nested-parse::

   Contains ToolboxUI class.

   :author: P. Savolainen (VTT)
   :date:   14.12.2017



Module Contents
---------------

.. py:class:: ToolboxUI

   Bases: :class:`PySide2.QtWidgets.QMainWindow`

   Class for application main GUI functions.

   Initialize application and main window.

   .. attribute:: msg
      

      

   .. attribute:: msg_success
      

      

   .. attribute:: msg_error
      

      

   .. attribute:: msg_warning
      

      

   .. attribute:: msg_proc
      

      

   .. attribute:: information_box
      

      

   .. attribute:: error_box
      

      

   .. attribute:: msg_proc_error
      

      

   .. attribute:: tool_specification_model_changed
      

      

   .. method:: connect_signals(self)


      Connect signals.


   .. method:: parse_project_item_modules(self)


      Collects attributes from project item modules into a dict.
      This dict is then used to perform all project item related tasks.


   .. method:: set_work_directory(self, new_work_dir=None)


      Creates a work directory if it does not exist or changes the current work directory to given.

      :param new_work_dir: If given, changes the work directory to given
      :type new_work_dir: str
      :param and creates the directory if it does not exist.:


   .. method:: project(self)


      Returns current project or None if no project open.


   .. method:: qsettings(self)


      Returns application preferences object.


   .. method:: init_project(self, project_dir)


      Initializes project at application start-up. Opens the last project that was open
      when app was closed (if enabled in Settings) or starts the app without a project.


   .. method:: new_project(self)


      Opens a file dialog where user can select a directory where a project is created.
      Pops up a question box if selected directory is not empty or if it already contains
      a Spine Toolbox project. Initial project name is the directory name.


   .. method:: create_project(self, name, description, location)


      Creates new project and sets it active.

      :param name: Project name
      :type name: str
      :param description: Project description
      :type description: str
      :param location: Path to project directory
      :type location: str


   .. method:: open_project(self, load_dir=None, clear_logs=True)


      Opens project from a selected or given directory.

      :param load_dir: Path to project base directory. If default value is used,
      :type load_dir: str
      :param a file explorer dialog is opened where the user can select the:
      :param project to open.:
      :param clear_logs: True clears Event and Process Log, False does not
      :type clear_logs: bool

      :returns: True when opening the project succeeded, False otherwise
      :rtype: bool


   .. method:: restore_project(self, project_info, project_dir, clear_logs)


      Initializes UI, Creates project, models, connections, etc., when opening a project.

      :param project_info: Project information dictionary
      :type project_info: dict
      :param project_dir: Project directory
      :type project_dir: str
      :param clear_logs: True clears Event and Process Log, False does not
      :type clear_logs: bool

      :returns: True when restoring project succeeded, False otherwise
      :rtype: bool


   .. method:: show_recent_projects_menu(self)


      Updates and sets up the recent projects menu to File-Open recent menu item.


   .. method:: save_project(self)


      Save project.


   .. method:: save_project_as(self)


      Ask user for a new project name and save. Creates a duplicate of the open project.


   .. method:: upgrade_project(self, checked=False)


      Upgrades an old style project (.proj file) to a new directory based Spine Toolbox project.
      Note that this method can be removed when we no longer want to support upgrading .proj projects.
      Project upgrading should happen later automatically when opening a project.


   .. method:: init_project_item_model(self)


      Initializes project item model. Create root and category items and
      add them to the model.


   .. method:: init_tool_specification_model(self, tool_specification_paths)


      Initializes Tool specification model.

      :param tool_specification_paths: List of tool definition file paths used in this project
      :type tool_specification_paths: list


   .. method:: restore_ui(self)


      Restore UI state from previous session.


   .. method:: clear_ui(self)


      Clean UI to make room for a new or opened project.


   .. method:: overwrite_check(self, project_dir)


      Checks if given directory is a project directory and/or empty
      And asks the user what to do in that case.

      :param project_dir: Abs. path to a directory
      :type project_dir: str

      :returns: True if user wants to overwrite an existing project or
                if the directory is not empty and the user wants to make it
                into a Spine Toolbox project directory anyway. False if user
                cancels the action.
      :rtype: bool


   .. method:: item_selection_changed(self, selected, deselected)


      Synchronize selection with scene. Check if only one item is selected and make it the
      active item: disconnect signals of previous active item, connect signals of current active item
      and show correct properties tab for the latter.


   .. method:: activate_no_selection_tab(self)


      Shows 'No Selection' tab.


   .. method:: activate_item_tab(self, item)


      Shows project item properties tab according to item type.
      Note: Does not work if a category item is given as argument.

      :param item: Instance of a project item
      :type item: ProjectItem


   .. method:: open_tool_specification(self)


      Opens a file dialog where the user can select an existing tool specification
      definition file (.json). If file is valid, calls add_tool_specification().


   .. method:: add_tool_specification(self, tool_specification)


      Adds a ToolSpecification instance to project, which then can be added to a Tool item.
      Adds the tool specification file path into project file (project.json)

      :param tool_specification: Tool specification that is added to project
      :type tool_specification: ToolSpecification


   .. method:: update_tool_specification(self, row, tool_specification)


      Updates a Tool specification and refreshes all Tools that use it.

      :param row: Row of tool specification in ToolSpecificationModel
      :type row: int
      :param tool_specification: An updated Tool specification
      :type tool_specification: ToolSpecification


   .. method:: remove_selected_tool_specification(self, checked=False)


      Prepares to remove tool specification selected in QListView.


   .. method:: remove_tool_specification(self, index, ask_verification=True)


      Removes tool specification from ToolSpecificationModel
      and tool specification file path from project file.
      Removes also Tool specifications from all Tool items
      that use this specification.

      :param index: Index of selected Tool specification in ToolSpecificationModel
      :type index: QModelIndex
      :param ask_verification: If True, displays a dialog box asking user to verify the removal
      :type ask_verification: bool


   .. method:: remove_all_items(self)


      Removes all items from project. Slot for Remove All button.


   .. method:: remove_item(self, ind, delete_item=False, check_dialog=False)


      Removes item from project when it's index in the project model is known.
      To remove all items in project, loop all indices through this method.
      This method is used in both opening and creating a new project as
      well as when item(s) are deleted from project.
      Use delete_item=False when closing the project or creating a new one.
      Setting delete_item=True deletes the item irrevocably. This means that
      data directories will be deleted from the hard drive. Handles also
      removing the node from the dag graph that contains it.

      :param ind: Index of removed item in project model
      :type ind: QModelIndex
      :param delete_item: If set to True, deletes the directories and data associated with the item
      :type delete_item: bool
      :param check_dialog: If True, shows 'Are you sure?' message box
      :type check_dialog: bool


   .. method:: open_anchor(self, qurl)


      Open file explorer in the directory given in qurl.

      :param qurl: Directory path or a file to open
      :type qurl: QUrl


   .. method:: edit_tool_specification(self, index)


      Open the tool specification widget for editing an existing tool specification.

      :param index: Index of the item (from double-click or contex menu signal)
      :type index: QModelIndex


   .. method:: open_tool_specification_file(self, index)


      Open the Tool specification definition file in the default (.json) text-editor.

      :param index: Index of the item
      :type index: QModelIndex


   .. method:: open_tool_main_program_file(self, index)


      Open the tool specification's main program file in the default editor.

      :param index: Index of the item
      :type index: QModelIndex


   .. method:: export_as_graphml(self)


      Exports all DAGs in project to separate GraphML files.


   .. method:: _handle_zoom_minus_pressed(self)


      Slot for handling case when '-' button in menu is pressed.


   .. method:: _handle_zoom_plus_pressed(self)


      Slot for handling case when '+' button in menu is pressed.


   .. method:: _handle_zoom_reset_pressed(self)


      Slot for handling case when 'reset zoom' button in menu is pressed.


   .. method:: setup_zoom_widget_action(self)


      Setups zoom widget action in view menu.


   .. method:: restore_dock_widgets(self)


      Dock all floating and or hidden QDockWidgets back to the main window.


   .. method:: set_debug_qactions(self)


      Set shortcuts for QActions that may be needed in debugging.


   .. method:: add_toggle_view_actions(self)


      Add toggle view actions to View menu.


   .. method:: toggle_properties_tabbar_visibility(self)


      Shows or hides the tab bar in properties dock widget. For debugging purposes.


   .. method:: update_datetime(self)


      Returns a boolean, which determines whether
      date and time is prepended to every Event Log message.


   .. method:: add_message(self, msg)


      Append regular message to Event Log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_success_message(self, msg)


      Append message with green text color to Event Log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_error_message(self, msg)


      Append message with red color to Event Log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_warning_message(self, msg)


      Append message with yellow (golden) color to Event Log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_process_message(self, msg)


      Writes message from stdout to process output QTextBrowser.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_process_error_message(self, msg)


      Writes message from stderr to process output QTextBrowser.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: show_add_project_item_form(self, item_category, x=0, y=0)


      Show add project item widget.


   .. method:: show_tool_specification_form(self, tool_specification=None)


      Show tool specification widget.


   .. method:: show_settings(self)


      Show Settings widget.


   .. method:: show_tool_config_asst(self)


      Show Tool configuration assistant widget.


   .. method:: show_about(self)


      Show About Spine Toolbox form.


   .. method:: show_user_guide(self)


      Open Spine Toolbox documentation index page in browser.


   .. method:: show_getting_started_guide(self)


      Open Spine Toolbox Getting Started HTML page in browser.


   .. method:: show_item_context_menu(self, pos)


      Context menu for project items listed in the project QTreeView.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_item_image_context_menu(self, pos, name)


      Context menu for project item images on the QGraphicsView.

      :param pos: Mouse position
      :type pos: QPoint
      :param name: The name of the concerned item
      :type name: str


   .. method:: show_project_item_context_menu(self, pos, ind)


      Create and show project item context menu.

      :param pos: Mouse position
      :type pos: QPoint
      :param ind: Index of concerned item
      :type ind: QModelIndex


   .. method:: show_link_context_menu(self, pos, link)


      Context menu for connection links.

      :param pos: Mouse position
      :type pos: QPoint
      :param link: The concerned link
      :type link: Link(QGraphicsPathItem)


   .. method:: show_tool_specification_context_menu(self, pos)


      Context menu for tool specifications.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: tear_down_items(self)


      Calls the tear_down method on all project items, so they can clean up their mess if needed.


   .. method:: _tasks_before_exit(self)


      Returns a list of tasks to perform before exiting the application.

      Possible tasks are:

      - `"prompt exit"`: prompt user if quitting is really desired
      - `"prompt save"`: prompt user if project should be saved before quitting
      - `"save"`: save project before quitting

      :returns: a list containing zero or more tasks


   .. method:: _perform_pre_exit_tasks(self)


      Prompts user to confirm quitting and saves the project if necessary.

      :returns: True if exit should proceed, False if the process was cancelled


   .. method:: _confirm_exit(self)


      Confirms exiting from user.

      :returns: True if exit should proceed, False if user cancelled


   .. method:: _confirm_save_and_exit(self)


      Confirms exit from user and saves the project if requested.

      :returns: True if exiting should proceed, False if user cancelled


   .. method:: remove_path_from_recent_projects(self, p)


      Removes entry that contains given path from the recent project files list in QSettings.

      :param p: Full path to a project directory
      :type p: str


   .. method:: update_recent_projects(self)


      Adds a new entry to QSettings variable that remembers the five most recent project paths.


   .. method:: closeEvent(self, event)


      Method for handling application exit.

      :param event: PySide2 event
      :type event: QCloseEvent


   .. method:: _serialize_selected_items(self)


      Serializes selected project items into a dictionary.

      The serialization protocol tries to imitate the format in which projects are saved.
      The format of the dictionary is following:
      `{"item_category_1": [{"name": "item_1_name", ...}, ...], ...}`

      :returns: a dict containing serialized version of selected project items


   .. method:: _deserialized_item_position_shifts(self, serialized_items)


      Calculates horizontal and vertical shifts for project items being deserialized.

      If the mouse cursor is on the Design view we try to place the items unders the cursor.
      Otherwise the items will get a small shift so they don't overlap a possible item below.
      In case the items don't fit the scene rect we clamp their coordinates within it.

      :param serialized_items: a dictionary of serialized items being deserialized
      :type serialized_items: dict

      :returns: a tuple of (horizontal shift, vertical shift) in scene's coordinates


   .. method:: _set_deserialized_item_position(item_dict, shift_x, shift_y, scene_rect)
      :staticmethod:


      Moves item's position by shift_x and shift_y while keeping it within the limits of scene_rect.


   .. method:: _deserialize_items(self, serialized_items)


      Deserializes project items from a dictionary and adds them to the current project.

      :param serialized_items: serialized project items
      :type serialized_items: dict


   .. method:: project_item_to_clipboard(self)


      Copies the selected project items to system's clipboard.


   .. method:: project_item_from_clipboard(self)


      Adds project items in system's clipboard to the current project.


   .. method:: duplicate_project_item(self)


      Duplicates the selected project items.


   .. method:: propose_item_name(self, prefix)


      Proposes a name for a project item.

      The format is `prefix_xx` where `xx` is a counter value [01..99].

      :param prefix: a prefix for the name
      :type prefix: str

      :returns: a name string


   .. method:: _item_edit_actions(self)


      Creates project item edit actions (copy, paste, duplicate) and adds them to proper places.


   .. method:: _scroll_event_log_to_end(self)



   .. method:: _show_message_box(self, title, message)


      Shows an information message box.


   .. method:: _show_error_box(self, title, message)



   .. method:: _connect_project_signals(self)


      Connects signals emitted by project.



