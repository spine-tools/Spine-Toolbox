:mod:`spinetoolbox.widgets.import_widget`
=========================================

.. py:module:: spinetoolbox.widgets.import_widget

.. autoapi-nested-parse::

   ImportDialog class.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. py:class:: ImportDialog(settings, parent)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   A widget for importing data into a Spine db. Currently used by DataStoreForm.
   It embeds three widgets that alternate depending on user's actions:
   - `select_widget` is a `QWidget` for selecting the source data type (CSV, Excel, etc.)
   - `_import_preview` is an `ImportPreviewWidget` for defining Mappings to associate with the source data
   - `_error_widget` is an `ImportErrorWidget` to show errors from import operations

   :param settings: settings for storing/restoring window state
   :type settings: QSettings
   :param parent: parent widget
   :type parent: QWidget

   .. attribute:: _SETTINGS_GROUP_NAME
      :annotation: = importDialog

      

   .. method:: mapped_data(self)
      :property:



   .. method:: mapping_errors(self)
      :property:



   .. method:: connector_selected(self, selection)



   .. method:: set_ok_button_availability(self)



   .. method:: import_data(self, data, errors)



   .. method:: data_ready(self, data, errors)



   .. method:: ok_clicked(self)



   .. method:: cancel_clicked(self)



   .. method:: back_clicked(self)



   .. method:: launch_import_preview(self)



   .. method:: _handle_failed_connection(self, msg)


      Handle failed connection, show error message and select widget

      :param msg {str} -- str with message of reason for failed connection.:


   .. method:: set_preview_as_main_widget(self)



   .. method:: set_error_widget_as_main_widget(self)



   .. method:: _restore_preview_ui(self)


      Restore UI state from previous session.


   .. method:: closeEvent(self, event)


      Stores window's settings and accepts the event.



