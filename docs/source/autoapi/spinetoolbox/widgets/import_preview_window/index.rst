:mod:`spinetoolbox.widgets.import_preview_window`
=================================================

.. py:module:: spinetoolbox.widgets.import_preview_window

.. autoapi-nested-parse::

   Contains ImportPreviewWindow class.

   :authors: P. Savolainen (VTT), A. Soininen (VTT), P. Vennström (VTT)
   :date:   10.6.2019



Module Contents
---------------

.. py:class:: ImportPreviewWindow(importer, filepath, connector, settings, toolbox)

   Bases: :class:`PySide2.QtWidgets.QMainWindow`

   A QMainWindow to let users define Mappings for an Importer item.

   :param importer: Project item that owns this preview window
   :type importer: spinetoolbox.project_items.importer.importer.Importer
   :param filepath: Importee path
   :type filepath: str
   :param connector: Asynchronous data reader
   :type connector: SourceConnection
   :param settings: Default mapping specification
   :type settings: dict
   :param toolbox: ToolboxUI class
   :type toolbox: QMainWindow

   .. attribute:: settings_updated
      

      

   .. attribute:: connection_failed
      

      

   .. method:: import_mapping_from_file(self)


      Imports mapping spec from a user selected .json file to the preview window.


   .. method:: export_mapping_to_file(self)


      Exports all mapping specs in current preview window to .json file.


   .. method:: apply_and_close(self)


      Apply changes to mappings and close preview window.


   .. method:: start_ui(self)



   .. method:: restore_ui(self)


      Restore UI state from previous session.


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



