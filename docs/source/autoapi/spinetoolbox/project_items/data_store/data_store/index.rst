:mod:`spinetoolbox.project_items.data_store.data_store`
=======================================================

.. py:module:: spinetoolbox.project_items.data_store.data_store

.. autoapi-nested-parse::

   Module for data store class.

   :authors: P. Savolainen (VTT), M. Marin (KTH)
   :date:   18.12.2017



Module Contents
---------------

.. py:class:: DataStore(name, description, x, y, toolbox, project, logger, url=None)

   Bases: :class:`spinetoolbox.project_item.ProjectItem`

   Data Store class.

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
   :param url: SQLAlchemy url
   :type url: str or dict

   .. method:: item_type()
      :staticmethod:


      See base class.


   .. method:: category()
      :staticmethod:


      See base class.


   .. method:: parse_url(self, url)


      Return a complete url dictionary from the given dict or string


   .. method:: make_signal_handler_dict(self)


      Returns a dictionary of all shared signals and their handlers.
      This is to enable simpler connecting and disconnecting.


   .. method:: activate(self)


      Load url into selections and connect signals.


   .. method:: deactivate(self)


      Disconnect signals.


   .. method:: url(self)


      Return the url attribute, for saving the project.


   .. method:: _update_sa_url(self, log_errors=True)



   .. method:: _make_url(self, log_errors=True)


      Returns a sqlalchemy url from the current url attribute or None if not valid.


   .. method:: project(self)


      Returns current project or None if no project open.


   .. method:: set_path_to_sqlite_file(self, file_path)


      Set path to SQLite file.


   .. method:: open_sqlite_file(self, checked=False)


      Open file browser where user can select the path to an SQLite
      file that they want to use.


   .. method:: load_url_into_selections(self)


      Load url attribute into shared widget selections.
      Used when activating the item, and creating a new Spine db.


   .. method:: set_url_key(self, key, value)


      Set url key to value.


   .. method:: refresh_host(self)


      Refresh host from selections.


   .. method:: refresh_port(self)


      Refresh port from selections.


   .. method:: refresh_database(self)


      Refresh database from selections.


   .. method:: refresh_username(self)


      Refresh username from selections.


   .. method:: refresh_password(self)


      Refresh password from selections.


   .. method:: refresh_dialect(self, dialect)



   .. method:: enable_dialect(self, dialect)


      Enable the given dialect in the item controls.


   .. method:: enable_no_dialect(self)


      Adjust widget enabled status to default when no dialect is selected.


   .. method:: enable_mssql(self)


      Adjust controls to mssql connection specification.


   .. method:: enable_sqlite(self)


      Adjust controls to sqlite connection specification.


   .. method:: enable_common(self)


      Adjust controls to 'common' connection specification.


   .. method:: open_ds_view(self, checked=False)


      Opens current url in the data store view.


   .. method:: do_open_ds_view(self)


      Opens current url in the data store view.


   .. method:: _handle_ds_view_destroyed(self)



   .. method:: data_files(self)


      Return a list of files that are in this items data directory.


   .. method:: copy_url(self, checked=False)


      Copy db url to clipboard.


   .. method:: create_new_spine_database(self, checked=False)


      Create new (empty) Spine database.


   .. method:: update_name_label(self)


      Update Data Store tab name label. Used only when renaming project items.


   .. method:: _do_handle_dag_changed(self, resources)


      See base class.


   .. method:: item_dict(self)


      Returns a dictionary corresponding to this item.


   .. method:: upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir)
      :staticmethod:


      See base class.


   .. method:: custom_context_menu(parent, pos)
      :staticmethod:


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

      :returns: True if renaming succeeded, False otherwise
      :rtype: bool


   .. method:: tear_down(self)


      Tears down this item. Called by toolbox just before closing.
      Closes the DataStoreForm instance opened by this item.


   .. method:: notify_destination(self, source_item)


      See base class.


   .. method:: default_name_prefix()
      :staticmethod:


      see base class


   .. method:: output_resources_backward(self)


      See base class.


   .. method:: output_resources_forward(self)


      See base class.



