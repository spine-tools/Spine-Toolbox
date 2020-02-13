:mod:`spinetoolbox.project_item`
================================

.. py:module:: spinetoolbox.project_item

.. autoapi-nested-parse::

   ProjectItem and ProjectItemResource classes.

   :authors: P. Savolainen (VTT)
   :date:   4.10.2018



Module Contents
---------------

.. py:class:: ProjectItem(name, description, x, y, project, logger)

   Bases: :class:`spinetoolbox.metaobject.MetaObject`

   Class for project items that are not category nor root.
   These items can be executed, refreshed, and so on.

   .. attribute:: x

      horizontal position in the screen

      :type: float

   .. attribute:: y

      vertical position in the screen

      :type: float

   :param name: item name
   :type name: str
   :param description: item description
   :type description: str
   :param x: horizontal position on the scene
   :type x: float
   :param y: vertical position on the scene
   :type y: float
   :param project: project item's project
   :type project: SpineToolboxProject
   :param logger: a logger instance
   :type logger: LoggerInterface

   .. attribute:: item_changed
      

      

   .. method:: item_type()
      :staticmethod:
      :abstractmethod:


      Item's type identifier string.


   .. method:: category()
      :staticmethod:
      :abstractmethod:


      Item's category identifier string.


   .. method:: make_signal_handler_dict(self)


      Returns a dictionary of all shared signals and their handlers.
      This is to enable simpler connecting and disconnecting.
      Must be implemented in subclasses.


   .. method:: connect_signals(self)


      Connect signals to handlers.


   .. method:: disconnect_signals(self)


      Disconnect signals from handlers and check for errors.


   .. method:: set_properties_ui(self, properties_ui)



   .. method:: set_icon(self, icon)



   .. method:: get_icon(self)


      Returns the graphics item representing this item in the scene.


   .. method:: clear_notifications(self)


      Clear all notifications from the exclamation icon.


   .. method:: add_notification(self, text)


      Add a notification to the exclamation icon.


   .. method:: set_rank(self, rank)


      Set rank of this item for displaying in the design view.


   .. method:: stop_execution(self)


      Stops executing this View.


   .. method:: execute(self, resources, direction)


      Executes this item in the given direction using the given resources and returns a boolean
      indicating the outcome.

      Subclasses need to implement execute_forward and execute_backward to do the appropriate work
      in each direction.

      :param resources: a list of ProjectItemResources available for execution
      :type resources: list
      :param direction: either "forward" or "backward"
      :type direction: str

      :returns: True if execution succeeded, False otherwise
      :rtype: bool


   .. method:: run_leave_animation(self)


      Runs the animation that represents execution leaving this item.
      Blocks until the animation is finished.


   .. method:: execute_forward(self, resources)


      Executes this item in the forward direction.

      The default implementation just returns True.

      :param resources: a list of ProjectItemResources available for execution
      :type resources: list

      :returns: True if execution succeeded, False otherwise
      :rtype: bool


   .. method:: execute_backward(self, resources)


      Executes this item in the backward direction.

      The default implementation just returns True.

      :param resources: a list of ProjectItemResources available for execution
      :type resources: list

      :returns: True if execution succeeded, False otherwise
      :rtype: bool


   .. method:: output_resources(self, direction)


      Returns output resources for execution in the given direction.

      Subclasses need to implement output_resources_backward and/or output_resources_forward
      if they want to provide resources in any direction.

      :param direction: Direction where output resources are passed
      :type direction: str

      :returns: a list of ProjectItemResources


   .. method:: output_resources_forward(self)


      Returns output resources for forward execution.

      The default implementation returns an empty list.

      :returns: a list of ProjectItemResources


   .. method:: output_resources_backward(self)


      Returns output resources for backward execution.

      The default implementation returns an empty list.

      :returns: a list of ProjectItemResources


   .. method:: handle_dag_changed(self, rank, resources)


      Handles changes in the DAG.

      Subclasses should reimplement the _do_handle_dag_changed() method.

      :param rank: item's execution order
      :type rank: int
      :param resources: resources available from input items
      :type resources: list


   .. method:: _do_handle_dag_changed(self, resources)


      Handles changes in the DAG.

      Usually this entails validating the input resources and populating file references etc.
      The default implementation does nothing.

      :param resources: resources available from input items
      :type resources: list


   .. method:: make_execution_leave_animation(self)


      Returns animation to play when execution leaves this item.

      :returns: QParallelAnimationGroup


   .. method:: invalidate_workflow(self, edges)


      Notifies that this item's workflow is not acyclic.

      :param edges: A list of edges that make the graph acyclic after removing them.
      :type edges: list


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item.


   .. method:: default_name_prefix()
      :staticmethod:
      :abstractmethod:


      prefix for default item name


   .. method:: rename(self, new_name)


      Renames this item.

      If the project item needs any additional steps in renaming, override this
      method in subclass. See e.g. rename() method in DataStore class.

      :param new_name: New name
      :type new_name: str

      :returns: True if renaming succeeded, False otherwise
      :rtype: bool


   .. method:: open_directory(self)


      Open this item's data directory in file explorer.


   .. method:: tear_down(self)


      Tears down this item. Called by toolbox just before closing.
      Implement in subclasses to eg close all QMainWindows opened by this item.


   .. method:: update_name_label(self)
      :abstractmethod:


      Updates the name label on the properties widget when renaming an item.

      Must be reimplemented by subclasses.


   .. method:: notify_destination(self, source_item)


      Informs an item that it has become the destination of a connection between two items.

      The default implementation logs a warning message. Subclasses should reimplement this if they need
      more specific behavior.

      :param source_item: connection source item
      :type source_item: ProjectItem


   .. method:: available_resources_downstream(self, upstream_resources)


      Returns resources available to downstream items.

      Should be reimplemented by subclasses if they want to offer resources
      to downstream items. The default implementation returns an empty list.

      :param upstream_resources: a list of resources available from upstream items
      :type upstream_resources: list

      :returns: a list of ProjectItemResources


   .. method:: available_resources_upstream(self)


      Returns resources available to upstream items.

      Should be reimplemented by subclasses if they want to offer resources
      to upstream items. The default implementation returns an empty list.

      :returns: a list of ProjectItemResources


   .. method:: upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir)
      :staticmethod:


      Upgrades item's dictionary from no version to version 1.

      Subclasses should reimplement this method if their JSON format changed between no version
      and version 1 .proj files.

      :param item_name: item's name
      :type item_name: str
      :param old_item_dict: no version item dictionary
      :type old_item_dict: str
      :param old_project_dir: path to the previous project dir. We use old project directory
                              here since the new project directory may be empty at this point and the directories
                              for the new project items have not been created yet.
      :type old_project_dir: str

      :returns: version 1 item dictionary



.. py:class:: ProjectItemResource(provider, type_, url='', metadata=None)

   Class to hold a resource made available by a project item
   and that may be consumed by another project item.

   Init class.

   :param provider: The item that provides the resource
   :type provider: ProjectItem
   :param type\_: The resource type, either "file" or "database" (for now)
   :type type\_: str
   :param url: The url of the resource
   :type url: str
   :param metadata: Some metadata providing extra information about the resource. For now it has one key:
                    - future (bool): whether the resource is from the future, e.g. Tool output files advertised beforehand
   :type metadata: dict

   .. method:: __eq__(self, other)



   .. method:: __repr__(self)



   .. method:: path(self)
      :property:


      Returns the resource path in the local syntax, as obtained from parsing the url.


   .. method:: scheme(self)
      :property:


      Returns the resource scheme, as obtained from parsing the url.



