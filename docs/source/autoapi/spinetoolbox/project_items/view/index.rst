:mod:`spinetoolbox.project_items.view`
======================================

.. py:module:: spinetoolbox.project_items.view

.. autoapi-nested-parse::

   View plugin.

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

   view/index.rst
   view_icon/index.rst


Package Contents
----------------

.. py:class:: View(name, description, x, y, toolbox, project, logger)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   View class.

   :param name: Object name
   :type name: str
   :param description: Object description
   :type description: str
   :param x: Initial X coordinate of item icon
   :type x: float
   :param y: Initial Y coordinate of item icon
   :type y: float
   :param toolbox: a toolbox instance
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
      This is to enable simpler connecting and disconnecting.


   .. method:: activate(self)


      Restore selections and connect signals.


   .. method:: deactivate(self)


      Save selections and disconnect signals.


   .. method:: restore_selections(self)


      Restore selections into shared widgets when this project item is selected.


   .. method:: save_selections(self)


      Save selections in shared widgets for this project item into instance variables.


   .. method:: open_view(self, checked=False)


      Opens references in a view window.


   .. method:: populate_reference_list(self)


      Populates reference list.


   .. method:: update_name_label(self)


      Update View tab name label. Used only when renaming project items.


   .. method:: execute_forward(self, resources)


      see base class


   .. method:: _do_handle_dag_changed(self, resources)


      Update the list of references that this item is viewing.


   .. method:: _update_references_list(self, resources_upstream)


      Updates the references list with resources upstream.

      :param resources_upstream: ProjectItemResource instances
      :type resources_upstream: list


   .. method:: _selected_indexes(self)


      Returns selected indexes.


   .. method:: _database_urls(self, indexes)


      Returns list of tuples (url, provider) for given indexes.


   .. method:: _restore_existing_view_window(self, view_id)


      Restores an existing view window and returns True if the operation was successful.


   .. method:: _make_view_window(self, db_maps)



   .. method:: tear_down(self)


      Tears down this item. Called by toolbox just before closing. Closes all view windows.


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: default_name_prefix()
      :staticmethod:


      see base class



.. py:class:: ViewIcon(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   View icon for the Design View.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolBoxUI
   :param x: Icon x coordinate
   :type x: float
   :param y: Icon y coordinate
   :type y: float
   :param w: Width of background rectangle
   :type w: float
   :param h: Height of background rectangle
   :type h: float
   :param name: Item name
   :type name: str


.. py:class:: ViewPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the View Item Properties.

   :param toolbox: The toolbox instance where this widget should be embeded
   :type toolbox: ToolboxUI

   Init class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_view_properties_context_menu(self, pos)


      Create and show a context-menu in View properties.

      :param pos: Mouse position
      :type pos: QPoint



.. py:class:: AddViewWidget(toolbox, x, y)

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
   :annotation: = 3

   

.. data:: item_category
   

   

.. data:: item_type
   

   

.. data:: item_icon
   :annotation: = :/icons/project_item_icons/binoculars.svg

   

.. data:: item_maker
   

   

.. data:: icon_maker
   

   

.. data:: properties_widget_maker
   

   

.. data:: add_form_maker
   

   

