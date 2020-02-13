:mod:`spinetoolbox.project`
===========================

.. py:module:: spinetoolbox.project

.. autoapi-nested-parse::

   Spine Toolbox project class.

   :authors: P. Savolainen (VTT), E. Rinne (VTT)
   :date:   10.1.2018



Module Contents
---------------

.. py:class:: SpineToolboxProject(toolbox, name, description, p_dir, project_item_model, settings, logger)

   Bases: :class:`spinetoolbox.metaobject.MetaObject`

   Class for Spine Toolbox projects.

   :param toolbox: toolbox of this project
   :type toolbox: ToolboxUI
   :param name: Project name
   :type name: str
   :param description: Project description
   :type description: str
   :param p_dir: Project directory
   :type p_dir: str
   :param project_item_model: project item tree model
   :type project_item_model: ProjectItemModel
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. attribute:: dag_execution_finished
      

      

   .. attribute:: dag_execution_about_to_start
      

      Emitted just before an engine runs. Provides a reference to the engine.


   .. attribute:: project_execution_about_to_start
      

      Emitted just before the entire project is executed.


   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: _create_project_structure(self, directory)


      Makes the given directory a Spine Toolbox project directory.
      Creates directories and files that are common to all projects.

      :param directory: Abs. path to a directory that should be made into a project directory
      :type directory: str

      :returns: True if project structure was created successfully, False otherwise
      :rtype: bool


   .. method:: change_name(self, name)


      Changes project name.

      :param name: New project name
      :type name: str


   .. method:: save(self, tool_def_paths)


      Collects project information and objects
      into a dictionary and writes it to a JSON file.

      :param tool_def_paths: List of absolute paths to tool specification files
      :type tool_def_paths: list

      :returns: True or False depending on success
      :rtype: bool


   .. method:: load(self, objects_dict)


      Populates project item model with items loaded from project file.

      :param objects_dict: Dictionary containing all project items in JSON format
      :type objects_dict: dict

      :returns: True if successful, False otherwise
      :rtype: bool


   .. method:: load_tool_specification_from_file(self, jsonfile)


      Returns a Tool specification from a definition file.

      :param jsonfile: Path of the tool specification definition file
      :type jsonfile: str

      :returns: ToolSpecification or None if reading the file failed


   .. method:: load_tool_specification_from_dict(self, definition, path)


      Returns a Tool specification from a definition dictionary.

      :param definition: Dictionary with the tool definition
      :type definition: dict
      :param path: Directory where main program file is located
      :type path: str

      :returns: ToolSpecification, NoneType


   .. method:: add_project_items(self, category_name, *items, set_selected=False, verbosity=True)


      Adds item to project.

      :param category_name: The items' category
      :type category_name: str
      :param items: one or more dict of items to add
      :type items: dict
      :param set_selected: Whether to set item selected after the item has been added to project
      :type set_selected: bool
      :param verbosity: If True, prints message
      :type verbosity: bool


   .. method:: add_to_dag(self, item_name)


      Add new node (project item) to the directed graph.


   .. method:: set_item_selected(self, item)


      Sets item selected and shows its info screen.

      :param item: Project item to select
      :type item: BaseProjectTreeItem


   .. method:: execute_dags(self, dags, execution_permits)


      Executes given dags.

      :param dags:
      :type dags: Sequence(DiGraph)
      :param execution_permits:
      :type execution_permits: Sequence(dict)


   .. method:: execute_next_dag(self)


      Executes next dag in the execution list.


   .. method:: execute_dag(self, dag, execution_permits, dag_identifier)


      Executes given dag.

      :param dag: Executed DAG
      :type dag: DiGraph
      :param execution_permits: Dictionary, where keys are node names in dag and value is a boolean
      :type execution_permits: dict
      :param dag_identifier: Identifier number for printing purposes
      :type dag_identifier: str


   .. method:: execute_selected(self)


      Executes DAGs corresponding to all selected project items.


   .. method:: execute_project(self)


      Executes all dags in the project.


   .. method:: stop(self)


      Stops execution. Slot for the main window Stop tool button in the toolbar.


   .. method:: export_graphs(self)


      Exports all valid directed acyclic graphs in project to GraphML files.


   .. method:: notify_changes_in_dag(self, dag)


      Notifies the items in given dag that the dag has changed.


   .. method:: notify_changes_in_all_dags(self)


      Notifies all items of changes in all dags in the project.


   .. method:: notify_changes_in_containing_dag(self, item)


      Notifies items in dag containing the given item that the dag has changed.


   .. method:: settings(self)
      :property:




