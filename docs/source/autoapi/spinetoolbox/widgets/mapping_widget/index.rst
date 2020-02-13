:mod:`spinetoolbox.widgets.mapping_widget`
==========================================

.. py:module:: spinetoolbox.widgets.mapping_widget

.. autoapi-nested-parse::

   MappingWidget and MappingOptionsWidget class.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. data:: MAPPING_CHOICES
   :annotation: = ['Constant', 'Column', 'Row', 'Header', 'None']

   

.. py:class:: MappingWidget(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for managing Mappings (add, remove, edit, visualize, and so on).
   Intended to be embedded in a ImportPreviewWidget.

   .. attribute:: mappingChanged
      

      

   .. attribute:: mappingDataChanged
      

      

   .. method:: set_data_source_column_num(self, num)



   .. method:: set_model(self, model)


      Sets new model


   .. method:: data_changed(self)



   .. method:: new_mapping(self)


      Adds new empty mapping


   .. method:: delete_selected_mapping(self)


      deletes selected mapping


   .. method:: select_mapping(self, selection)


      gets selected mapping and emits mappingChanged



.. py:class:: MappingOptionsWidget(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for managing Mapping options (class type, dimensions, parameter type, ignore columns, and so on).
   Intended to be embedded in a MappingWidget.

   .. method:: set_num_available_columns(self, num)



   .. method:: change_skip_columns(self, skip_cols)



   .. method:: set_model(self, model)



   .. method:: update_ui(self)


      updates ui to RelationshipClassMapping or ObjectClassMapping model


   .. method:: change_class(self, new_class)



   .. method:: change_dimension(self, dim)



   .. method:: change_parameter(self, par)



   .. method:: change_import_objects(self, state)



   .. method:: change_read_start_row(self, row)



   .. method:: _update_time_series_options(self)




