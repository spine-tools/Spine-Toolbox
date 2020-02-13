:mod:`spinetoolbox.spine_io.exporters.excel`
============================================

.. py:module:: spinetoolbox.spine_io.exporters.excel

.. autoapi-nested-parse::

   Framework for exporting a database to Excel file.

   :author: P. Vennström (VTT), A. Soininen (VTT)
   :date:   31.1.2020



Module Contents
---------------

.. function:: _get_objects_and_parameters(db)

   Exports all object data from spine database into unstacked list of lists

   :param db: database mapping for database
   :type db: spinedb_api.DatabaseMapping

   :returns: (List, List) First list contains parameter data, second one json data


.. function:: _get_relationships_and_parameters(db)

   Exports all relationship data from spine database into unstacked list of lists

   :param db: database mapping for database
   :type db: spinedb_api.DatabaseMapping

   :returns: (List, List) First list contains parameter data, second one json data


.. function:: _unstack_list_of_tuples(data, headers, key_cols, value_name_col, value_col)

   Unstacks list of lists or list of tuples and creates a list of namedtuples
   whit unstacked data (pivoted data)

   :param data: List of lists with data to unstack
   :type data: List[List]
   :param headers: List of header names for data
   :type headers: List[str]
   :param key_cols: List of index for column that are keys, columns to not unstack
   :type key_cols: List[Int]
   :param value_name_col: index to column containing name of data to unstack
   :type value_name_col: Int
   :param value_col: index to column containing value to value_name_col
   :type value_col: Int

   :returns: List of list with headers in headers list
             (List): List of header names for each item in inner list
   :rtype: (List[List])


.. function:: _get_unstacked_relationships(db)

   Gets all data for relationships in a unstacked list of list

   :param db: database mapping for database
   :type db: spinedb_api.DatabaseMapping

   :returns: stacked relationships, stacked JSON, stacked time series and stacked time patterns
   :rtype: (list, list, list, list)


.. function:: _get_unstacked_objects(db)

   Gets all data for objects in a unstacked list of list

   :param db: database mapping for database
   :type db: spinedb_api.DatabaseMapping

   :returns: stacked objects, parsed JSON, parsed time series and parsed time patterns
   :rtype: (list, list, list, list)


.. function:: _write_relationships_to_xlsx(wb, relationship_data)

   Writes Classes, parameter and parameter values for relationships.
   Writes one sheet per relationship class.

   :param wb: excel workbook to write too.
   :type wb: openpyxl.Workbook
   :param relationship_data: List of lists containing relationship
   :type relationship_data: List[List]
   :param data give by function get_unstacked_relationships:


.. function:: _write_json_array_to_xlsx(wb, data, sheet_type)

   Writes json array data for object classes and relationship classes.
   Writes one sheet per relationship/object class.

   :param wb: excel workbook to write too.
   :type wb: openpyxl.Workbook
   :param data: List of lists containing json data give by function
   :type data: List[List]
   :param get_unstacked_objects and get_unstacked_relationships:
   :param sheet_type: str with value "relationship" or "object" telling if data is for a relationship or object
   :type sheet_type: str


.. function:: _write_TimeSeries_to_xlsx(wb, data, sheet_type, data_type)

   Writes spinedb_api TimeSeries data for object classes and relationship classes.
   Writes one sheet per relationship/object class.

   :param wb: excel workbook to write too.
   :type wb: openpyxl.Workbook
   :param data: List of lists containing json data give by function
   :type data: List[List]
   :param get_unstacked_objects and get_unstacked_relationships:
   :param sheet_type: str with value "relationship" or "object" telling if data is for a relationship or object
   :type sheet_type: str


.. function:: _write_objects_to_xlsx(wb, object_data)

   Writes Classes, parameter and parameter values for objects.
   Writes one sheet per relationship/object class.

   :param wb: excel workbook to write too.
   :type wb: openpyxl.Workbook
   :param object_data: List of lists containing relationship data give by function get_unstacked_objects
   :type object_data: List[List]


.. function:: export_spine_database_to_xlsx(db, filepath)

   Writes all data in a spine database into an excel file.

   :param db: database mapping for database.
   :type db: spinedb_api.DatabaseMapping
   :param filepath: str with filepath to save excel file to.
   :type filepath: str


