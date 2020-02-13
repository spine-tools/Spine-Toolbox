:mod:`spinetoolbox.spine_io.importers.excel_reader`
===================================================

.. py:module:: spinetoolbox.spine_io.importers.excel_reader

.. autoapi-nested-parse::

   Contains ExcelConnector class and a help function.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. function:: select_excel_file(parent=None)

   Launches QFileDialog with .xlsx and friends filter


.. py:class:: ExcelConnector

   Bases: :class:`spinetoolbox.spine_io.io_api.SourceConnection`

   Template class to read data from another QThread.

   .. attribute:: DISPLAY_NAME
      :annotation: = Excel

      

   .. attribute:: OPTIONS
      

      

   .. attribute:: SELECT_SOURCE_UI
      

      

   .. method:: connect_to_source(self, source)


      saves filepath

      :param source {str} -- filepath:


   .. method:: disconnect(self)


      Disconnect from connected source.


   .. method:: get_tables(self)


      Method that should return Excel sheets as mappings and their options.

      :returns: Sheets as mappings and options for each sheet or an empty dictionary if no workbook.
      :rtype: dict

      :raises Exception: If something goes wrong.


   .. method:: get_data_iterator(self, table, options, max_rows=-1)


      Return data read from data source table in table. If max_rows is
      specified only that number of rows.


   .. method:: get_mapped_data(self, tables_mappings, options, table_types, table_row_types, max_rows=-1)


      Overrides io_api method to check for some parameter value types.



.. function:: create_mapping_from_sheet(worksheet)

   Checks if sheet is a valid spine excel template, if so creates a
   mapping object for each sheet.


