:mod:`spinetoolbox.widgets.spine_datapackage_widget`
====================================================

.. py:module:: spinetoolbox.widgets.spine_datapackage_widget

.. autoapi-nested-parse::

   Widget shown to user when opening a 'datapackage.json' file
   in Data Connection item.

   :author: M. Marin (KTH)
   :date:   7.7.2018



Module Contents
---------------

.. py:class:: SpineDatapackageWidget(data_connection)

   Bases: :class:`PySide2.QtWidgets.QMainWindow`

   A widget to allow user to edit a datapackage and convert it
   to a Spine database in SQLite.

   .. attribute:: data_connection

      Data Connection associated to this widget

      :type: DataConnection

   Initialize class.

   .. attribute:: msg
      

      

   .. attribute:: msg_proc
      

      

   .. attribute:: msg_error
      

      

   .. method:: add_toggle_view_actions(self)


      Add toggle view actions to View menu.


   .. method:: show(self)


      Called when the form shows. Init datapackage
      (either from existing datapackage.json or by inferring a new one from sources)
      and update ui.


   .. method:: infer_datapackage(self, checked=False)


      Called when the user triggers the infer action.
      Infer datapackage from sources and update ui.


   .. method:: load_datapackage(self)


      Load datapackage from 'datapackage.json' file in data directory,
      or infer one from CSV files in that directory.


   .. method:: infer_datapackage_(self)


      Infer datapackage from CSV files in data directory.


   .. method:: update_ui(self)


      Update ui from datapackage attribute.


   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: restore_ui(self)


      Restore UI state from previous session.


   .. method:: _handle_menu_about_to_show(self)


      Called when a menu from the menubar is about to show.
      Adjust infer action depending on whether or not we have a datapackage.
      Adjust copy paste actions depending on which widget has the focus.
      TODO Enable/disable action to save datapackage depending on status.


   .. method:: add_message(self, msg)


      Prepend regular message to status bar.

      :param msg: String to show in QStatusBar
      :type msg: str


   .. method:: add_process_message(self, msg)


      Show process message in status bar. This messages stays until replaced.

      :param msg: String to show in QStatusBar
      :type msg: str


   .. method:: add_error_message(self, msg)


      Show error message.

      :param msg: String to show
      :type msg: str


   .. method:: save_datapackage(self, checked=False)


      Write datapackage to file 'datapackage.json' in data directory.


   .. method:: show_export_to_spine_dialog(self, checked=False)


      Show dialog to allow user to select a file to export.


   .. method:: export_to_spine(self, file_path)


      Export datapackage into Spine SQlite file.


   .. method:: _handle_converter_progressed(self, step, msg)



   .. method:: _handle_converter_failed(self, msg)



   .. method:: _handle_converter_finished(self)



   .. method:: copy(self, checked=False)


      Copy data to clipboard.


   .. method:: paste(self, checked=False)


      Paste data from clipboard.


   .. method:: load_resource_data(self)


      Load resource data into a local list of tables.


   .. method:: reset_resource_models(self, current, previous)


      Reset resource data and schema models whenever a new resource is selected.


   .. method:: reset_resource_data_model(self)


      Reset resource data model with data from newly selected resource.


   .. method:: update_resource_data(self, index, new_value)


      Update resource data with newly edited data.


   .. method:: _handle_resource_name_data_committed(self, index, new_name)


      Called when line edit delegate wants to edit resource name data.
      Update resources model and descriptor with new resource name.


   .. method:: _handle_field_name_data_committed(self, index, new_name)


      Called when line edit delegate wants to edit field name data.
      Update name in fields_model, resource_data_model's header and datapackage descriptor.


   .. method:: _handle_primary_key_data_committed(self, index)


      Called when checkbox delegate wants to edit primary key data.
      Add or remove primary key field accordingly.


   .. method:: _handle_foreign_keys_data_committed(self, index, value)



   .. method:: _handle_foreign_keys_data_changed(self, top_left, bottom_right, roles=None)


      Called when foreign keys data is updated in model.
      Update descriptor accordingly.


   .. method:: _handle_foreign_keys_model_rows_inserted(self, parent, first, last)



   .. method:: create_remove_foreign_keys_row_button(self, index)


      Create button to remove foreign keys row.


   .. method:: remove_foreign_key_row(self, button)



   .. method:: closeEvent(self, event=None)


      Handle close event.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



.. py:class:: CustomPackage(descriptor=None, base_path=None, strict=False, storage=None)

   Bases: :class:`datapackage.Package`

   Custom datapackage class.

   .. method:: rename_resource(self, old, new)



   .. method:: rename_field(self, resource, old, new)


      Rename a field.


   .. method:: set_primary_key(self, resource, *primary_key)


      Set primary key for a given resource in the package


   .. method:: append_to_primary_key(self, resource, field)


      Append field to resources's primary key.


   .. method:: remove_from_primary_key(self, resource, field)


      Remove field from resources's primary key.


   .. method:: insert_foreign_key(self, row, resource_name, field_names, reference_resource_name, reference_field_names)


      Insert foreign key to a given resource in the package at a given row.


   .. method:: remove_primary_key(self, resource, *primary_key)


      Remove the primary key for a given resource in the package


   .. method:: remove_foreign_key(self, resource, fields, reference_resource, reference_fields)


      Remove foreign key from the package


   .. method:: remove_foreign_keys_row(self, row, resource)


      Remove foreign keys row from the package



