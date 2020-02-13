:mod:`spinetoolbox.spine_io.importers.sqlalchemy_connector`
===========================================================

.. py:module:: spinetoolbox.spine_io.importers.sqlalchemy_connector

.. autoapi-nested-parse::

   Contains SqlAlchemyConnector class and a help function.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. function:: select_sa_conn_string(parent=None)

   Launches QInputDialog for entering connection string


.. py:class:: SqlAlchemyConnector

   Bases: :class:`spinetoolbox.spine_io.io_api.SourceConnection`

   Template class to read data from another QThread.

   .. attribute:: DISPLAY_NAME
      :annotation: = SqlAlchemy

      

   .. attribute:: OPTIONS
      

      

   .. attribute:: SELECT_SOURCE_UI
      

      

   .. method:: connect_to_source(self, source)


      saves filepath

      :param source {str} -- filepath:


   .. method:: disconnect(self)


      Disconnect from connected source.


   .. method:: get_tables(self)


      Method that should return a list of table names, list(str)

      :returns: Table names in list
      :rtype: list(str)


   .. method:: get_data_iterator(self, table, options, max_rows=-1)


      Creates a iterator for the file in self.filename

      :param table {string} -- table name:
      :param options {dict} -- dict with options, not used:

      :keyword max_rows {int} -- how many rows of data to read, if -1 read all rows (default: {-1})

      :returns: [type] -- [description]



