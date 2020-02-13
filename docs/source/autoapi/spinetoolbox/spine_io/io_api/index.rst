:mod:`spinetoolbox.spine_io.io_api`
===================================

.. py:module:: spinetoolbox.spine_io.io_api

.. autoapi-nested-parse::

   Contains a class template for a data source connector used in import ui.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. data:: TYPE_STRING_TO_CLASS
   

   

.. data:: TYPE_CLASS_TO_STRING
   

   

.. py:class:: SourceConnection

   Template class to read data from another QThread.

   .. attribute:: DISPLAY_NAME
      :annotation: = unnamed source

      

   .. attribute:: OPTIONS
      

      

   .. attribute:: SELECT_SOURCE_UI
      

      

   .. method:: connect_to_source(self, source)
      :abstractmethod:


      Connects to source, ex: connecting to a database where source is a connection string.

      :param source {} -- object with information on source to be connected to, ex: filepath string for a csv connection


   .. method:: disconnect(self)
      :abstractmethod:


      Disconnect from connected source.


   .. method:: get_tables(self)
      :abstractmethod:


      Method that should return a list of table names, list(str)

      :raises NotImplementedError: [description]


   .. method:: get_data_iterator(self, table, options, max_rows=-1)
      :abstractmethod:


      Function that should return a data iterator, data header and number of
      columns.


   .. method:: get_data(self, table, options, max_rows=-1)


      Return data read from data source table in table. If max_rows is
      specified only that number of rows.


   .. method:: get_mapped_data(self, tables_mappings, options, table_types, table_row_types, max_rows=-1)


      Reads all mappings in dict tables_mappings, where key is name of table
      and value is the mappings for that table.
      emits mapped data when ready.



