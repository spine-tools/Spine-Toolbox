:mod:`spinetoolbox.spine_io.importers.csv_reader`
=================================================

.. py:module:: spinetoolbox.spine_io.importers.csv_reader

.. autoapi-nested-parse::

   Contains CSVConnector class and a help function.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. function:: select_csv_file(parent=None)

   Launches QFileDialog with no filter


.. py:class:: CSVConnector

   Bases: :class:`spinetoolbox.spine_io.io_api.SourceConnection`

   Template class to read data from another QThread.

   .. attribute:: DISPLAY_NAME
      :annotation: = Text/CSV

      "Text/CSV

      :type: name of data source, ex


   .. attribute:: _ENCODINGS
      :annotation: = ['utf-8', 'utf-16', 'utf-32', 'ascii', 'iso-8859-1', 'iso-8859-2']

      List of available text encodings


   .. attribute:: OPTIONS
      

      dict with option specification for source.


   .. attribute:: SELECT_SOURCE_UI
      

      Modal widget that returns source object and action (OK, CANCEL)


   .. method:: connect_to_source(self, source)


      saves filepath

      :param source: filepath
      :type source: str


   .. method:: disconnect(self)


      Disconnect from connected source.


   .. method:: get_tables(self)


      Returns a mapping from file name to options.

      :returns: dict


   .. method:: parse_options(options)
      :staticmethod:


      Parses options dict to dialect and quotechar options for csv.reader

      :param options: dict with options:
                      "encoding": file text encoding
                      "delimiter": file delimiter
                      "quotechar": file quotechar
                      "has_header": if first row should be treated as a header
                      "skip": how many rows should be skipped
      :type options: dict

      :returns:

                tuple dialect for csv.reader,
                                            quotechar for csv.reader and
                                            number of rows to skip
      :rtype: tuple(dict, bool, integer)


   .. method:: file_iterator(self, options, max_rows)


      creates an iterator that reads max_rows number of rows from text file

      :param options: dict with options:
      :type options: dict
      :param max_rows: max number of rows to read, if -1 then read all rows
      :type max_rows: integer

      :returns: iterator of csv file
      :rtype: iterator


   .. method:: get_data_iterator(self, table, options, max_rows=-1)


      Creates an iterator for the file in self.filename

      :param table: ignored, used in abstract IOWorker class
      :type table: string
      :param options: dict with options
      :type options: dict

      :keyword max_rows: how many rows of data to read, if -1 read all rows (default: {-1})
      :kwtype max_rows: int

      :returns:
      :rtype: tuple



