:mod:`spinetoolbox.project_items.exporter.widgets.export_list_item`
===================================================================

.. py:module:: spinetoolbox.project_items.exporter.widgets.export_list_item

.. autoapi-nested-parse::

   A small widget to set up a database export in Gdx Export settings.

   :author: A. Soininen (VTT)
   :date:   10.9.2019



Module Contents
---------------

.. py:class:: ExportListItem(url, file_name, settings_state, parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget with few controls to select the output file name and open a settings window.

   :param url: database's identifier to be shown on a label
   :type url: str
   :param file_name: relative path to the exported file name
   :type file_name: str
   :param parent: a parent widget
   :type parent: QWidget

   .. attribute:: open_settings_clicked
      

      signal that is triggered when settings window should be opened


   .. attribute:: file_name_changed
      

      signal that is fired when the file name field is changed


   .. method:: out_file_name_edit(self)
      :property:


      export file name QLineEdit


   .. method:: url_field(self)
      :property:


      Text in the database URL field.


   .. method:: settings_state_changed(self, state)



   .. method:: _emit_file_name_changed(self, file_name)


      Emits file_name_changed signal.


   .. method:: _emit_open_settings_clicked(self, _)


      Emits open_settings_clicked signal.



