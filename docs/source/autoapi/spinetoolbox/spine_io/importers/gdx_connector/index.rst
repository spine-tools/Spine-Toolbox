:mod:`spinetoolbox.spine_io.importers.gdx_connector`
====================================================

.. py:module:: spinetoolbox.spine_io.importers.gdx_connector

.. autoapi-nested-parse::

   Contains GDXConnector class and a help function.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. function:: select_gdx_file(parent=None)

   Launches QFileDialog with .gdx filter


.. py:class:: GdxConnector

   Bases: :class:`spinetoolbox.spine_io.io_api.SourceConnection`

   Template class to read data from another QThread.

   .. attribute:: DISPLAY_NAME
      :annotation: = Gdx

      name of data source


   .. attribute:: OPTIONS
      

      dict with option specification for source


   .. attribute:: SELECT_SOURCE_UI
      

      Modal widget that returns source object and action (OK, CANCEL).


   .. method:: __exit__(self, exc_type, exc_value, traceback)



   .. method:: __del__(self)



   .. method:: connect_to_source(self, source)


      Connects to given .gdx file.

      :param source: path to .gdx file.
      :type source: str


   .. method:: disconnect(self)


      Disconnects from connected source.


   .. method:: get_tables(self)


      Returns a list of table names.

      GAMS scalars are also regarded as tables.

      :returns: Table names in list
      :rtype: list(str)


   .. method:: get_data_iterator(self, table, options, max_rows=-1)


      Creates an iterator for the data source

      :param table: table name
      :type table: string
      :param options: dict with options
      :type options: dict

      :keyword max_rows: ignored
      :kwtype max_rows: int

      :returns: data iterator, list of column names, number of columns
      :rtype: tuple



