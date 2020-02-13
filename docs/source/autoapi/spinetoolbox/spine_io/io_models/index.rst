:mod:`spinetoolbox.spine_io.io_models`
======================================

.. py:module:: spinetoolbox.spine_io.io_models

.. autoapi-nested-parse::

   Classes for handling models in PySide2's model/view framework.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. data:: Margin
   

   

.. data:: _MAPPING_COLORS
   

   

.. data:: _ERROR_COLOR
   

   

.. data:: _COLUMN_TYPE_ROLE
   

   

.. data:: _COLUMN_NUMBER_ROLE
   

   

.. data:: _ALLOWED_TYPES
   

   

.. data:: _TYPE_TO_FONT_AWESOME_ICON
   

   

.. data:: _MAPTYPE_DISPLAY_NAME
   

   

.. data:: _DISPLAY_TYPE_TO_TYPE
   

   

.. data:: _TYPE_TO_DISPLAY_TYPE
   

   

.. py:class:: MappingPreviewModel(parent=None)

   Bases: :class:`spinetoolbox.mvcmodels.minimal_table_model.MinimalTableModel`

   A model for highlighting columns, rows, and so on, depending on Mapping specification.
   Used by ImportPreviewWidget.

   .. attribute:: columnTypesUpdated
      

      

   .. attribute:: rowTypesUpdated
      

      

   .. attribute:: mappingChanged
      

      

   .. method:: mapping(self)



   .. method:: clear(self)



   .. method:: reset_model(self, main_data=None)



   .. method:: set_mapping(self, mapping)


      Set mapping to display colors from

      :param mapping {MappingSpecModel} -- mapping model:


   .. method:: validate(self, section, orientation=Qt.Horizontal)



   .. method:: get_type(self, section, orientation=Qt.Horizontal)



   .. method:: get_types(self, orientation=Qt.Horizontal)



   .. method:: set_type(self, section, section_type, orientation=Qt.Horizontal)



   .. method:: _mapping_data_changed(self)



   .. method:: update_colors(self)



   .. method:: data_error(self, index, role=Qt.DisplayRole, orientation=Qt.Horizontal)



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: data_color(self, index)


      returns background color for index depending on mapping

      :param index {PySide2.QtCore.QModelIndex} -- index:

      :returns: [QColor] -- QColor of index


   .. method:: index_in_mapping(self, mapping, index)


      Checks if index is in mapping

      :param mapping {Mapping} -- mapping:
      :param index {QModelIndex} -- index:

      :returns: [bool] -- returns True if mapping is in index


   .. method:: mapping_column_ref_int_list(self)


      Returns a list of column indexes that are not pivoted

      :returns: [List[int]] -- list of ints



.. py:class:: MappingSpecModel(model, parent=None)

   Bases: :class:`PySide2.QtCore.QAbstractTableModel`

   A model to hold a Mapping specification.

   .. method:: skip_columns(self)
      :property:



   .. method:: map_type(self)
      :property:



   .. method:: last_pivot_row(self)
      :property:



   .. method:: dimension(self)
      :property:



   .. method:: import_objects(self)
      :property:



   .. method:: parameter_type(self)
      :property:



   .. method:: is_pivoted(self)
      :property:



   .. method:: read_start_row(self)
      :property:



   .. method:: set_read_start_row(self, row)



   .. method:: set_import_objects(self, flag)



   .. method:: set_mapping(self, mapping)



   .. method:: set_dimension(self, dim)



   .. method:: change_model_class(self, new_class)


      Change model between Relationship and Object class


   .. method:: change_parameter_type(self, new_type)


      Change parameter type


   .. method:: update_display_table(self)



   .. method:: get_map_type_display(self, mapping, name)



   .. method:: get_map_value_display(self, mapping, name)



   .. method:: get_map_append_display(self, mapping, name)



   .. method:: get_map_prepend_display(self, mapping, name)



   .. method:: data(self, index, role)



   .. method:: data_color(self, display_name)



   .. method:: rowCount(self, index=None)



   .. method:: columnCount(self, index=None)



   .. method:: headerData(self, section, orientation, role)



   .. method:: flags(self, index)



   .. method:: setData(self, index, value, role)



   .. method:: set_type(self, name, value)



   .. method:: set_value(self, name, value)



   .. method:: set_append_str(self, name, value)



   .. method:: set_prepend_str(self, name, value)



   .. method:: get_mapping_from_name(self, name)



   .. method:: set_mapping_from_name(self, name, mapping)



   .. method:: set_skip_columns(self, columns=None)



   .. method:: set_time_series_repeat(self, repeat)


      Toggles the repeat flag in the parameter's options.


   .. method:: model_parameters(self)


      Returns the mapping's parameters.



.. py:class:: MappingListModel(mapping_list, parent=None)

   Bases: :class:`PySide2.QtCore.QAbstractListModel`

   A model to hold a list of Mappings.

   .. method:: set_model(self, model)



   .. method:: get_mappings(self)



   .. method:: rowCount(self, index=None)



   .. method:: data_mapping(self, index)



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: add_mapping(self)



   .. method:: remove_mapping(self, row)




.. py:class:: HeaderWithButton(orientation, parent=None)

   Bases: :class:`PySide2.QtWidgets.QHeaderView`

   Class that reimplements the QHeaderView section paint event to draw a button
   that is used to display and change the type of that column or row.

   .. method:: display_all(self)
      :property:



   .. method:: sections_with_buttons(self)
      :property:



   .. method:: _create_menu(self)



   .. method:: _menu_pressed(self, action)



   .. method:: widget_width(self)


      Width of widget

      :returns: [int] -- Width of widget


   .. method:: widget_height(self)


      Height of widget

      :returns: [int] -- Height of widget


   .. method:: mouseMoveEvent(self, mouse_event)


      Moves the button to the correct section so that interacting with the button works.


   .. method:: mousePressEvent(self, mouse_event)


      Move the button to the pressed location and show or hide it if button should not be shown.


   .. method:: leaveEvent(self, event)


      Hide button


   .. method:: _set_button_geometry(self, button, index)


      Sets a buttons geometry depending on the index.

      :param button {QWidget} -- QWidget that geometry should be set:
      :param index {int} -- logical_index to set position and geometry to.:


   .. method:: _section_resize(self, i)


      When a section is resized.

      :param i {int} -- logical index to section being resized:


   .. method:: paintSection(self, painter, rect, logical_index)


      Paints a section of the QHeader view.

      Works by drawing a pixmap of the button to the left of the orignial paint rectangle.
      Then shifts the original rect to the right so these two doesn't paint over eachother.


   .. method:: sectionSizeFromContents(self, logical_index)


      Add the button width to the section so it displays right.

      :param logical_index {int} -- logical index of section:

      :returns: [QSize] -- Size of section


   .. method:: _section_move(self, logical, old_visual_index, new_visual_index)


      Section beeing moved.

      :param logical {int} -- logical index of section beeing moved.:
      :param old_visual_index {int} -- old visual index of section:
      :param new_visual_index {int} -- new visual index of section:


   .. method:: fix_widget_positions(self)


      Update position of interaction button


   .. method:: set_margins(self, margins)




.. py:class:: TableViewWithButtonHeader(parent=None)

   Bases: :class:`PySide2.QtWidgets.QTableView`

   .. method:: scrollContentsBy(self, dx, dy)




