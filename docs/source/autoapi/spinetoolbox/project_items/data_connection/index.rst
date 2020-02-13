:mod:`spinetoolbox.project_items.data_connection`
=================================================

.. py:module:: spinetoolbox.project_items.data_connection

.. autoapi-nested-parse::

   Data connection plugin.

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

   data_connection/index.rst
   data_connection_icon/index.rst


Package Contents
----------------

.. py:class:: DataConnectionIcon(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   Data Connection icon for the Design View.

   :param toolbox: main window instance
   :type toolbox: ToolboxUI
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

   .. py:class:: _SignalHolder

      Bases: :class:`PySide2.QtCore.QObject`

      .. attribute:: files_dropped_on_icon
         

         A signal that it triggered when files are dragged and dropped on the item.



   .. method:: dragEnterEvent(self, event)


      Drag and drop action enters.
      Accept file drops from the filesystem.

      :param event: Event
      :type event: QGraphicsSceneDragDropEvent


   .. method:: dragLeaveEvent(self, event)


      Drag and drop action leaves.

      :param event: Event
      :type event: QGraphicsSceneDragDropEvent


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit files_dropped_on_dc signal from scene,
      with this instance, and a list of files for each dropped url.


   .. method:: select_on_drag_over(self)


      Called when the timer started in drag_enter_event is elapsed.
      Select this item if the drag action is still over it.



.. py:class:: item_maker(name, description, x, y, toolbox, project, logger, references=None)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   Data Connection class.

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
   :param references: a list of file paths
   :type references: list

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


   .. method:: add_files_to_references(self, paths)


      Add multiple file paths to reference list.

      :param paths: A list of paths to files
      :type paths: list


   .. method:: receive_files_dropped_on_icon(self, icon, file_paths)


      Called when files are dropped onto a data connection graphics item.
      If the item is this Data Connection's graphics item, add the files to data.


   .. method:: add_files_to_data_dir(self, file_paths)


      Add files to data directory


   .. method:: add_references(self, checked=False)


      Let user select references to files for this data connection.


   .. method:: remove_references(self, checked=False)


      Remove selected references from reference list.
      Do not remove anything if there are no references selected.


   .. method:: copy_to_project(self, checked=False)


      Copy selected file references to this Data Connection's data directory.


   .. method:: open_reference(self, index)


      Open reference in default program.


   .. method:: open_data_file(self, index)


      Open data file in default program.


   .. method:: show_spine_datapackage_form(self)


      Show spine_datapackage_form widget.


   .. method:: datapackage_form_destroyed(self)


      Notify a connection that datapackage form has been destroyed.


   .. method:: make_new_file(self)


      Create a new blank file to this Data Connections data directory.


   .. method:: remove_files(self)


      Remove selected files from data directory.


   .. method:: file_references(self)


      Returns a list of paths to files that are in this item as references.


   .. method:: data_files(self)


      Returns a list of files that are in the data directory.


   .. method:: refresh(self, path=None)


      Refresh data files in Data Connection Properties.
      NOTE: Might lead to performance issues.


   .. method:: populate_reference_list(self, items, emit_item_changed=True)


      List file references in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: populate_data_list(self, items)


      List project internal data (files) in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: update_name_label(self)


      Update Data Connection tab name label. Used only when renaming project items.


   .. method:: output_resources_forward(self)


      see base class


   .. method:: _do_handle_dag_changed(self, resources)


      See base class.


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item.


   .. method:: rename(self, new_name)


      Rename this item.

      :param new_name: New name
      :type new_name: str

      :returns: True if renaming succeeded, False otherwise
      :rtype: bool


   .. method:: tear_down(self)


      Tears down this item. Called by toolbox just before closing.
      Closes the SpineDatapackageWidget instances opened.


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: default_name_prefix()
      :staticmethod:


      See base class.



.. py:class:: DataConnectionPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the Data Connection Item Properties.

   :param toolbox: The toolbox instance where this widget should be embedded
   :type toolbox: ToolboxUI

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_references_context_menu(self, pos)


      Create and show a context-menu in data connection properties
      references view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_data_context_menu(self, pos)


      Create and show a context-menu in data connection properties
      data view.

      :param pos: Mouse position
      :type pos: QPoint



.. py:class:: AddDataConnectionWidget(toolbox, x, y)

   Bases: :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`

   A widget to query user's preferences for a new item.

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

   .. method:: call_add_item(self)


      Creates new Item according to user's selections.



.. data:: item_rank
   :annotation: = 1

   

.. data:: item_category
   

   

.. data:: item_type
   

   

.. data:: item_icon
   :annotation: = :/icons/project_item_icons/file-alt.svg

   

.. data:: icon_maker
   

   

.. data:: properties_widget_maker
   

   

.. data:: add_form_maker
   

   

