:mod:`spinetoolbox.spine_io.connection_manager`
===============================================

.. py:module:: spinetoolbox.spine_io.connection_manager

.. autoapi-nested-parse::

   Contains ConnectionManager class.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. py:class:: ConnectionManager(connection, parent=None)

   Bases: :class:`PySide2.QtCore.QObject`

   Class to manage data connections in another thread.

   :param connection: A class derived from `SourceConnection`, e.g. `CSVConnector`
   :type connection: class

   .. attribute:: startTableGet
      

      

   .. attribute:: startDataGet
      

      

   .. attribute:: startMappedDataGet
      

      

   .. attribute:: connectionFailed
      

      

   .. attribute:: connectionReady
      

      

   .. attribute:: closeConnection
      

      

   .. attribute:: error
      

      

   .. attribute:: fetchingData
      

      

   .. attribute:: dataReady
      

      

   .. attribute:: tablesReady
      

      

   .. attribute:: mappedDataReady
      

      

   .. method:: current_table(self)
      :property:



   .. method:: is_connected(self)
      :property:



   .. method:: table_options(self)
      :property:



   .. method:: table_types(self)
      :property:



   .. method:: table_row_types(self)
      :property:



   .. method:: source(self)
      :property:



   .. method:: source_type(self)
      :property:



   .. method:: set_table(self, table)


      Sets the current table of the data source.

      :param table {str} -- str with table name:


   .. method:: request_tables(self)


      Get tables tables from source, emits two singals,
      fetchingData: ConnectionManager is busy waiting for data
      startTableGet: a signal that the worker in another thread is listening
      to know when to run get a list of table names.


   .. method:: request_data(self, table=None, max_rows=-1)


      Request data from emits dataReady to with data

      :keyword table {str} -- which table to get data from (default: {None})
      :keyword max_rows {int} -- how many rows to read (default: {-1})


   .. method:: request_mapped_data(self, table_mappings, max_rows=-1)


      Get mapped data from csv file

      :param table_mappings {dict} -- dict with filename as key and a list of mappings as value:

      :keyword max_rows {int} -- number of rows to read, if -1 read all rows (default: {-1})


   .. method:: connection_ui(self)


      launches a modal ui that prompts the user to select source.

      ex: fileselect if source is a file.


   .. method:: init_connection(self)


      Creates a Worker and a new thread to read source data.
      If there is an existing thread close that one.


   .. method:: _handle_connection_ready(self)



   .. method:: _handle_tables_ready(self, table_options)



   .. method:: _new_options(self)



   .. method:: set_table_options(self, options)


      Sets connection manager options for current connector

      :param options {dict} -- Dict with option settings:


   .. method:: set_table_types(self, types)


      Sets connection manager types for current connector

      :param types {dict} -- Dict with types settings, column:
      :type types {dict} -- Dict with types settings, column: int


   .. method:: set_table_row_types(self, types)


      Sets connection manager types for current connector

      :param types {dict} -- Dict with types settings, row:
      :type types {dict} -- Dict with types settings, row: int


   .. method:: option_widget(self)


      Return a Qwidget with options for reading data from a table in source


   .. method:: close_connection(self)


      Close and delete thread and worker



.. py:class:: ConnectionWorker(source, connection, parent=None)

   Bases: :class:`PySide2.QtCore.QObject`

   A class for delegating SourceConnection operations to another QThread.

   :param source: path of the source file
   :type source: str
   :param connection: A class derived from `SourceConnection` for connecting to the source file
   :type connection: class

   .. attribute:: connectionFailed
      

      

   .. attribute:: error
      

      

   .. attribute:: connectionReady
      

      

   .. attribute:: tablesReady
      

      

   .. attribute:: dataReady
      

      

   .. attribute:: mappedDataReady
      

      

   .. method:: init_connection(self)


      Connect to data source


   .. method:: tables(self)



   .. method:: data(self, table, options, max_rows)



   .. method:: mapped_data(self, table_mappings, options, types, table_row_types, max_rows)



   .. method:: disconnect(self)




