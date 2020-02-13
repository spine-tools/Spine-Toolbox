:mod:`spinetoolbox.project_items.view.view`
===========================================

.. py:module:: spinetoolbox.project_items.view.view

.. autoapi-nested-parse::

   Module for view class.

   :authors: P. Savolainen (VTT), M. Marin (KHT), J. Olauson (KTH)
   :date:   14.07.2018



Module Contents
---------------

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



