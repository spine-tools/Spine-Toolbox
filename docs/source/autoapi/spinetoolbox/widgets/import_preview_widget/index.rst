:mod:`spinetoolbox.widgets.import_preview_widget`
=================================================

.. py:module:: spinetoolbox.widgets.import_preview_widget

.. autoapi-nested-parse::

   Contains ImportPreviewWidget, and MappingTableMenu classes.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. py:class:: ImportPreviewWidget(connector, parent)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A Widget for defining one or more Mappings associated to a data Source (CSV file, Excel file, etc).
   Currently it's being embedded in ImportDialog and ImportPreviewWindow.

   :param connector:
   :type connector: ConnectionManager

   .. attribute:: tableChecked
      

      

   .. attribute:: mappedDataReady
      

      

   .. attribute:: previewDataUpdated
      

      

   .. method:: checked_tables(self)
      :property:



   .. method:: set_loading_status(self, status)


      Sets widgets enable state


   .. method:: connection_ready(self)


      Requests new tables data from connector


   .. method:: select_table(self, selection)


      Set selected table and request data from connector


   .. method:: check_list_item(self, item)


      Set the check state of item


   .. method:: handle_connector_error(self, error_message)



   .. method:: request_mapped_data(self)



   .. method:: update_tables(self, tables)


      Update list of tables


   .. method:: update_preview_data(self, data, header)



   .. method:: use_settings(self, settings)



   .. method:: get_settings_dict(self)


      Returns a dictionary with type of connector, connector options for tables,
      mappings for tables, selected tables.

      :returns: [Dict] -- dict with settings


   .. method:: close_connection(self)


      Close connector connection.


   .. method:: _new_column_types(self)



   .. method:: _new_row_types(self)



   .. method:: _update_display_row_types(self)




.. py:class:: MappingTableMenu(parent=None)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   A menu to let users define a Mapping from a data table.
   Used to generate the context menu for ImportPreviewWidget._ui_table

   .. method:: set_model(self, model)



   .. method:: set_mapping(self, name='', map_type=None, value=None)



   .. method:: request_menu(self, QPos=None)




.. function:: _sanitize_data(data, header)

   Fills empty data cells with None.


