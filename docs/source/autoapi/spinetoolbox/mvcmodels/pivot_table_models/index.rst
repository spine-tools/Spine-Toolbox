:mod:`spinetoolbox.mvcmodels.pivot_table_models`
================================================

.. py:module:: spinetoolbox.mvcmodels.pivot_table_models

.. autoapi-nested-parse::

   Provides pivot table models for the Tabular View.

   :author: P. Vennström (VTT)
   :date:   1.11.2018



Module Contents
---------------

.. py:class:: PivotTableModel(parent)

   Bases: :class:`PySide2.QtCore.QAbstractTableModel`

   :param parent:
   :type parent: TabularViewForm

   .. attribute:: _V_HEADER_WIDTH
      :annotation: = 5

      

   .. attribute:: _ITEMS_TO_FETCH
      :annotation: = 1024

      

   .. method:: reset_data_count(self)



   .. method:: canFetchMore(self, parent)



   .. method:: fetchMore(self, parent)



   .. method:: fetch_more_rows(self, parent)



   .. method:: fetch_more_columns(self, parent)



   .. method:: reset_model(self, data, index_ids, rows=(), columns=(), frozen=(), frozen_value=())



   .. method:: clear_model(self)



   .. method:: update_model(self, data)



   .. method:: add_to_model(self, data)



   .. method:: remove_from_model(self, data)



   .. method:: set_pivot(self, rows, columns, frozen, frozen_value)



   .. method:: set_frozen_value(self, frozen_value)



   .. method:: set_plot_x_column(self, column, is_x)


      Sets or clears the Y flag on a column


   .. method:: plot_x_column(self)
      :property:


      Returns the index of the column designated as Y values for plotting or None.


   .. method:: first_data_row(self)


      Returns the row index to the first data row.


   .. method:: headerRowCount(self)


      Returns number of rows occupied by header.


   .. method:: headerColumnCount(self)


      Returns number of columns occupied by header.


   .. method:: dataRowCount(self)


      Returns number of rows that contain actual data.


   .. method:: dataColumnCount(self)


      Returns number of columns that contain actual data.


   .. method:: emptyRowCount(self)



   .. method:: emptyColumnCount(self)



   .. method:: rowCount(self, parent=QModelIndex())


      Number of rows in table, number of header rows + datarows + 1 empty row


   .. method:: columnCount(self, parent=QModelIndex())


      Number of columns in table, number of header columns + datacolumns + 1 empty columns


   .. method:: flags(self, index)


      Roles for data


   .. method:: top_left_indexes(self)


      Returns indexes in the top left area.

      Returns
          list(QModelIndex): top indexes (horizontal headers, associated to rows)
          list(QModelIndex): left indexes (vertical headers, associated to columns)


   .. method:: index_in_top(self, index)



   .. method:: index_in_left(self, index)



   .. method:: index_in_top_left(self, index)


      Returns whether or not the given index is in top left corner, where pivot names are displayed


   .. method:: index_in_column_headers(self, index)


      Returns whether or not the given index is in column headers (horizontal) area


   .. method:: index_in_row_headers(self, index)


      Returns whether or not the given index is in row headers (vertical) area


   .. method:: index_in_headers(self, index)



   .. method:: index_in_empty_column_headers(self, index)


      Returns whether or not the given index is in empty column headers (vertical) area


   .. method:: index_in_empty_row_headers(self, index)


      Returns whether or not the given index is in empty row headers (vertical) area


   .. method:: index_in_data(self, index)


      Returns whether or not the given index is in data area


   .. method:: headerData(self, section, orientation, role=Qt.DisplayRole)



   .. method:: map_to_pivot(self, index)


      Returns a tuple of row and column in the pivot model that corresponds to the given model index.

      :param index:
      :type index: QModelIndex

      :returns: row
                int: column
      :rtype: int


   .. method:: _top_left_id(self, index)


      Returns the id of the top left header corresponding to the given header index.

      :param index:
      :type index: QModelIndex

      :returns: int, NoneType


   .. method:: _header_id(self, index)


      Returns the id of the given row or column header index.

      :param index:
      :type index: QModelIndex

      :returns: int, NoneType


   .. method:: _header_ids(self, row, column)


      Returns the ids for the headers at given row *and* column.

      :param row:
      :type row: int
      :param column:
      :type column: int

      :returns: tuple(int)


   .. method:: _header_name(self, top_left_id, header_id)


      Returns the name of the header given by top_left_id and header_id.

      :param top_left_id: The id of the top left header
      :type top_left_id: int
      :param header_id: The header id
      :type header_id: int

      Returns
          str


   .. method:: header_name(self, index)


      Returns the name corresponding to the given header index.

      :param index:
      :type index: QModelIndex

      :returns: str


   .. method:: header_names(self, index)


      Returns the header names corresponding to the given data index.

      :param index:
      :type index: QModelIndex

      :returns: object names
                str: parameter name
      :rtype: list(str)


   .. method:: value_name(self, index)


      Returns a string that concatenates the header names corresponding to the given data index.

      :param index:
      :type index: QModelIndex

      :returns: str


   .. method:: column_name(self, column)


      Returns a string that concatenates the header names corresponding to the given column.

      :param column:
      :type column: int

      :returns: str


   .. method:: _color_data(self, index)



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: setData(self, index, value, role=Qt.EditRole)



   .. method:: batch_set_data(self, indexes, values)



   .. method:: _batch_set_inner_data(self, inner_data)



   .. method:: _batch_set_parameter_value_data(self, row_map, column_map, data, values)



   .. method:: _checked_parameter_values(self, items)



   .. method:: _add_parameter_values(self, items)



   .. method:: _update_parameter_values(self, items)



   .. method:: _batch_set_relationship_data(self, row_map, column_map, data, values)



   .. method:: _batch_set_header_data(self, header_data)



   .. method:: _batch_set_empty_header_data(self, header_data, get_top_left_id)




.. py:class:: PivotTableSortFilterProxy(parent=None)

   Bases: :class:`PySide2.QtCore.QSortFilterProxyModel`

   Initialize class.

   .. method:: set_filter(self, identifier, filter_value)


      Sets filter for a given index (object class) name.

      :param identifier: index identifier
      :type identifier: int
      :param filter_value: A set of accepted values, or None if no filter (all pass)
      :type filter_value: set, None


   .. method:: clear_filter(self)



   .. method:: accept_index(self, index, index_ids)



   .. method:: filterAcceptsRow(self, source_row, source_parent)


      Returns true if the item in the row indicated by the given source_row
      and source_parent should be included in the model; otherwise returns false.


   .. method:: filterAcceptsColumn(self, source_column, source_parent)


      Returns true if the item in the column indicated by the given source_column
      and source_parent should be included in the model; otherwise returns false.


   .. method:: batch_set_data(self, indexes, values)




