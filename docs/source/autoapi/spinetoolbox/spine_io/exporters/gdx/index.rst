:mod:`spinetoolbox.spine_io.exporters.gdx`
==========================================

.. py:module:: spinetoolbox.spine_io.exporters.gdx

.. autoapi-nested-parse::

   For exporting a database to GAMS .gdx file.

   Currently, this module supports databases that are "GAMS-like", that is, they follow the EAV model
   but the object classes, objects, relationship classes etc. directly reflect the GAMS data
   structures. Conversions e.g. from Spine model to TIMES are not supported at the moment.

   This module contains low level functions for reading a database into an intermediate format and
   for writing that intermediate format into a .gdx file. A higher lever function
   to_gdx_file() that does basically everything needed for exporting is provided for convenience.

   :author: A. Soininen (VTT)
   :date:   30.8.2019



Module Contents
---------------

.. py:exception:: GdxExportException(message)

   Bases: :class:`Exception`

   An exception raised when something goes wrong within the gdx module.

   :param message: a message detailing the cause of the exception
   :type message: str

   .. method:: message(self)
      :property:


      A message detailing the cause of the exception.


   .. method:: __str__(self)


      Returns the message detailing the cause of the exception.



.. py:class:: Set(name, description='', domain_names=None)

   Represents a GAMS domain, set or a subset.

   .. attribute:: description

      set's explanatory text

      :type: str

   .. attribute:: domain_names

      a list of superset (domain) names, None if the Set is a domain

      :type: list

   .. attribute:: name

      set's name

      :type: str

   .. attribute:: records

      set's elements as a list of Record objects

      :type: list

   :param name: set's name
   :type name: str
   :param description: set's explanatory text
   :type description: str
   :param domain_names: a list of indexing domain names
   :type domain_names: list

   .. method:: dimensions(self)
      :property:


      Number of dimensions of this Set.


   .. method:: is_domain(self)


      Returns True if this set is a domain set.


   .. method:: to_dict(self)


      Stores Set to a dictionary.


   .. method:: from_dict(set_dict)
      :staticmethod:


      Restores Set from a dictionary.


   .. method:: from_object_class(object_class)
      :staticmethod:


      Constructs a Set from database's object class row.

      :param object_class: an object class row from the database
      :type object_class: namedtuple


   .. method:: from_relationship_class(relationship_class)
      :staticmethod:


      Constructs a Set from database's relationship class row.

      :param relationship_class: a relationship class row from the database
      :type relationship_class: namedtuple



.. py:class:: Record(keys)

   Represents a GAMS set element in a Set.

   :param keys: a tuple of record's keys
   :type keys: tuple

   :param keys: a tuple of record's keys
   :type keys: tuple

   .. method:: name(self)
      :property:


      Record's 'name' as a comma separated list of its keys.


   .. method:: to_dict(self)


      Stores Record to a dictionary.


   .. method:: from_dict(record_dict)
      :staticmethod:


      Restores Record from a dictionary.


   .. method:: from_object(object_)
      :staticmethod:


      Constructs a record from database's object row.

      :param object\_: an object or relationship row from the database
      :type object\_: namedtuple


   .. method:: from_relationship(relationship)
      :staticmethod:


      Constructs a record from database's relationship row.

      :param relationship: a relationship row from the database
      :type relationship: namedtuple



.. py:class:: Parameter(domain_names, indexes, values)

   Represents a GAMS parameter.

   .. attribute:: domain_names

      indexing domain names (currently Parameters can be indexed by domains only)

      :type: list

   .. attribute:: indexes

      parameter's indexes

      :type: list

   .. attribute:: values

      parameter's values

      :type: list

   :param domain_names: indexing domain names (currently Parameters can be indexed by domains only)
   :type domain_names: list
   :param indexes: parameter's indexes
   :type indexes: list
   :param values: parameter's values
   :type values: list

   .. method:: append_value(self, index, value)


      Appends a new value.

      :param index: record keys indexing the value
      :type index: tuple
      :param value: a value


   .. method:: append_object_parameter(self, object_parameter)


      Appends a value from object parameter.

      :param object_parameter: an object parameter row from the database
      :type object_parameter: namedtuple


   .. method:: append_relationship_parameter(self, relationship_parameter)


      Appends a value from relationship parameter.

      :param relationship_parameter: a relationship parameter row from the database
      :type relationship_parameter: namedtuple


   .. method:: slurp(self, parameter)


      Appends the indexes and values from another parameter.

      :param parameter: a parameter to append from
      :type parameter: Parameter


   .. method:: is_scalar(self)


      Returns True if this parameter contains only scalars.


   .. method:: is_indexed(self)


      Returns True if this parameter contains only indexed values.


   .. method:: expand_indexes(self, indexing_setting)


      Expands indexed values to scalars in place by adding a new dimension (index).

      The indexes and values attributes are resized to accommodate all scalars in the indexed values.
      A new indexing domain is inserted to domain_names and the corresponding keys into indexes.
      Effectively, this increases parameter's dimensions by one.

      :param indexing_setting: description of how the expansion should be done
      :type indexing_setting: IndexingSetting


   .. method:: from_object_parameter(object_parameter)
      :staticmethod:


      Constructs a GAMS parameter from database's object parameter row

      :param object_parameter: a parameter row from the database
      :type object_parameter: namedtuple


   .. method:: from_relationship_parameter(relationship_parameter)
      :staticmethod:


      Constructs a GAMS parameter from database's relationship parameter row

      :param relationship_parameter: a parameter row from the database
      :type relationship_parameter: namedtuple



.. py:class:: IndexingDomain(name, description, indexes, pick_list)

   This class holds the indexes that should be used for indexed parameter value expansion.

   .. attribute:: name

      indexing domain's name

      :type: str

   .. attribute:: description

      domain's description

      :type: str

   Picks the keys from base_domain for which the corresponding element in pick_list holds True.

   :param name: indexing domain's name
   :type name: str
   :param description: domain's description
   :type description: str
   :param indexes: a list of indexing key tuples
   :type indexes: list
   :param pick_list: a list of booleans
   :type pick_list: list

   .. method:: indexes(self)
      :property:


      a list of picked indexing key tuples


   .. method:: all_indexes(self)
      :property:


      a list of all indexing key tuples


   .. method:: pick_list(self)
      :property:


      list of boolean values where True means the corresponding index should be picked


   .. method:: sort_indexes(self, settings)


      Sorts the indexes according to settings.

      :param settings: a Settings object
      :type settings: Settings


   .. method:: to_dict(self)


      Stores IndexingDomain to a dictionary.


   .. method:: from_dict(domain_dict)
      :staticmethod:


      Restores IndexingDomain from a dictionary.


   .. method:: from_base_domain(base_domain, pick_list)
      :staticmethod:


      Builds a new IndexingDomain from an existing Set.

      :param base_domain: a domain set that holds the indexes
      :type base_domain: Set
      :param pick_list: a list of booleans
      :type pick_list: list



.. function:: sort_indexing_domain_indexes(indexing_settings, settings)

   Sorts the index keys of an indexing domain in place.

   :param indexing_settings: a mapping from parameter name to IndexingSetting
   :type indexing_settings: dict
   :param settings: settings
   :type settings: Settings


.. function:: _python_interpreter_bitness()

   Returns 64 for 64bit Python interpreter or 32 for 32bit interpreter.


.. function:: _read_value(value_in_database)


.. function:: _windows_dlls_exist(gams_path)

   Returns True if requred DLL files exist in given GAMS installation path.


.. function:: find_gams_directory()

   Returns GAMS installation directory or None if not found.

   On Windows systems, this function looks for `gams.location` in registry;
   on other systems the `PATH` environment variable is checked.

   :returns: a path to GAMS installation directory or None if not found.


.. function:: expand_indexed_parameter_values(parameters, indexing_settings)

   Expands the dimensions of indexed parameter values.

   :param parameters: a map from parameter names to Parameters.
   :type parameters: dict
   :param indexing_settings: mapping from parameter name to IndexingSetting
   :type indexing_settings: dict


.. function:: sets_to_gams(gdx_file, sets, omitted_set=None)

   Writes Set objects to .gdx file as GAMS sets.

   Records and Parameters contained within the Sets are written as well.

   :param gdx_file: a target file
   :type gdx_file: GdxFile
   :param sets: a list of Set objects
   :type sets: list
   :param omitted_set: prevents writing this set even if it is included in given sets
   :type omitted_set: Set


.. function:: parameters_to_gams(gdx_file, parameters)

   Writes parameters to .gdx file as GAMS parameters.

   :param gdx_file: a target file
   :type gdx_file: GdxFile
   :param parameters: a list of Parameter objects
   :type parameters: dict


.. function:: domain_parameters_to_gams_scalars(gdx_file, parameters, domain_name)

   Adds the parameter from given domain as a scalar to .gdx file.

   The added parameters are erased from parameters.

   :param gdx_file: a target file
   :type gdx_file: GdxFile
   :param parameters: a map from parameter name to Parameter object
   :type parameters: dict
   :param domain_name: name of domain whose parameters to add
   :type domain_name: str

   :returns: a list of non-scalar parameters


.. function:: object_classes_to_domains(db_map)

   Converts object classes, objects and object parameters from a database to the intermediate format.

   Object classes get converted to Set objects
   while objects are stored as Records in corresponding DomainSets.
   Lastly, object parameters are read into Parameter objects.

   :param db_map: a database map
   :type db_map: spinedb_api.DatabaseMapping

   :returns: a tuple containing list of Set objects and a dict of Parameter objects


.. function:: relationship_classes_to_sets(db_map)

   Converts relationship classes, relationships and relationship parameters from a database to the intermediate format.

   Relationship classes get converted to Set objects
   while relationships are stored as SetRecords in corresponding Sets.
   Lastly, relationship parameters are read into Parameter objects.

   :param db_map: a database map
   :type db_map: spinedb_api.DatabaseMapping

   :returns: a tuple containing a list of Set objects and a dict of Parameter objects


.. function:: domain_names_and_records(db_map)

   Returns a list of domain names and a map from a name to list of record keys.

   :param db_map: a database map
   :type db_map: spinedb_api.DatabaseMapping

   :returns: a tuple containing list of domain names and a dict from domain name to its records


.. function:: set_names_and_records(db_map)

   Returns a list of set names and a map from a name to list of record keys.

   :param db_map: a database map
   :type db_map: spinedb_api.DatabaseMapping

   :returns: a tuple containing list of set names and a dict from set name to its records


.. py:class:: IndexingSetting(indexed_parameter)

   Settings for indexed value expansion for a single Parameter.

   .. attribute:: parameter

      a parameter containing indexed values

      :type: Parameter

   .. attribute:: indexing_domain

      indexing info

      :type: IndexingDomain

   .. attribute:: index_position

      where to insert the new index when expanding a parameter

      :type: int

   :param indexed_parameter: a parameter containing indexed values
   :type indexed_parameter: Parameter
   :param indexing_domain: indexing info
   :type indexing_domain: IndexingDomain
   :param index_position: where to insert the new index when expanding a parameter
   :type index_position: int

   .. method:: append_parameter(self, parameter)


      Adds indexes and values from another parameter.



.. function:: make_indexing_settings(db_map)

   Constructs skeleton indexing settings for parameter indexed value expansion.

   :param db_map: a database mapping
   :type db_map: spinedb_api.DatabaseMapping

   :returns: a mapping from parameter name to IndexingSetting
   :rtype: dict


.. function:: indexing_settings_to_dict(settings)

   Stores indexing settings to a JSON compatible dictionary.

   :param settings: a mapping from parameter name to IndexingSetting.
   :type settings: dict

   :returns: a JSON serializable dictionary


.. function:: indexing_settings_from_dict(settings_dict, db_map)

   Restores indexing settings from a json compatible dictionary.

   :param settings: a JSON compatible dictionary representing parameter indexing settings.
   :type settings: dict
   :param db_map: database mapping
   :type db_map: DatabaseMapping

   :returns: a dictionary mapping parameter name to IndexingSetting.


.. function:: _find_parameter(parameter_name, db_map)

   Searches for parameter_name in db_map and returns Parameter.


.. function:: filter_and_sort_sets(sets, sorted_set_names, metadatas)

   Returns a list of sets sorted by `sorted_set_names` and their filter flag set to True

   This function removes the sets that are not supposed to be exported and sorts the rest
   according to the order specified by `sorted_set_names`.

   :param sets: a list of sets (DomainSet or Set) to be filtered and sorted
   :type sets: list
   :param sorted_set_names: a list of set names in the order they should be in the output list,
                            including ones to be removed
   :type sorted_set_names: list
   :param metadatas: list of SetMetadata objects in the same order as `sorted_set_names`;
   :type metadatas: list

   :returns: a list of sets
   :rtype: list


.. function:: sort_records_inplace(sets, settings)

   Sorts the record lists of given domains according to the order given in settings.

   :param sets: a list of DomainSet or Set objects whose records are to be sorted
   :type sets: list
   :param settings: settings that define the sorting order
   :type settings: Settings


.. function:: extract_domain(domains, name_to_extract)

   Extracts the domain with given name from a list of domains.

   :param domains: a list of Set objects
   :type domains: list
   :param name_to_extract: name of the domain to be extracted
   :type name_to_extract: str

   :returns: a tuple (list, Set) of the modified domains list and the extracted Set object


.. function:: to_gdx_file(database_map, file_name, additional_domains, settings, indexing_settings, gams_system_directory=None)

   Exports given database map into .gdx file.

   :param database_map: a database to export
   :type database_map: spinedb_api.DatabaseMapping
   :param file_name: output file name
   :type file_name: str
   :param additional_domains: a list of extra domains not in the database
   :type additional_domains: list
   :param settings: export settings
   :type settings: Settings
   :param indexing_settings: a dictionary containing settings for indexed parameter expansion
   :type indexing_settings: dict
   :param gams_system_directory: path to GAMS system directory or None to let GAMS choose one for you
   :type gams_system_directory: str


.. function:: make_settings(database_map)

   Builds a Settings object from given database.

   :param database_map: a database from which domains, sets, records etc are extracted
   :type database_map: spinedb_api.DatabaseMapping

   :returns: a Settings object useful for exporting the given `database_map`


.. py:class:: Settings(domain_names, set_names, records, domain_metadatas=None, set_metadatas=None, global_parameters_domain_name='')

   This class holds some settings needed by `to_gdx_file()` for .gdx export.

   Settings is mostly concerned about the order in which domains, sets and records are exported into the .gdx file.
   This order is paramount for some models, like TIMES.

   Constructs a new Settings object.

   :param domain_names: a list of Set names
   :type domain_names: list
   :param set_names: a list of Set names
   :type set_names: list
   :param records: a mapping from Set names to record key tuples
   :type records: dict
   :param domain_metadatas: a list of SetMetadata objects, one for each domain
   :type domain_metadatas: list
   :param set_metadatas: a list of SetMetadata objects, one for each set
   :type set_metadatas: list
   :param global_parameters_domain_name: name of the Set whose parameters to export as GAMS scalars
   :type global_parameters_domain_name: str

   .. method:: sorted_domain_names(self)
      :property:


      this list defines the order in which domains are exported into the .gdx file.


   .. method:: domain_metadatas(self)
      :property:


      this list contains SetMetadata objects for each name in `domain_names`


   .. method:: sorted_set_names(self)
      :property:


      this list defines the order in which sets are exported into the .gdx file.


   .. method:: set_metadatas(self)
      :property:


      this list contains SetMetadata objects for each name in `set_names`


   .. method:: global_parameters_domain_name(self)
      :property:


      the name of the domain, parameters of which should be exported as GAMS scalars


   .. method:: add_or_replace_domain(self, domain, metadata)


      Adds a new domain or replaces an existing domain's records and metadata.

      :param domain: a domain to add/replace
      :type domain: Set
      :param metadata: domain's metadata
      :type metadata: SetMetadata

      :returns: True if a new domain was added, False if an existing domain was replaced


   .. method:: domain_index(self, domain)


      Returns an integral index to the domain's name in sorted domain names.


   .. method:: del_domain_at(self, index)


      Erases domain name at given integral index.


   .. method:: update_domain(self, domain)


      Updates domain's records.


   .. method:: sorted_record_key_lists(self, name)


      Returns a list of record keys for given domain or set name.

      The list defines the order in which the records are exported into the .gdx file.

      :param name: domain or set name
      :type name: str

      :returns: an ordered list of record key lists


   .. method:: update(self, updating_settings)


      Updates the settings by merging with another one.

      All domains, sets and records that are in both settings (common)
      or in `updating_settings` (new) are retained.
      Common elements are ordered the same way they were ordered in the original settings.
      New elements are appended to the common ones in the order they were in `updating_settings`

      :param updating_settings: settings to merge with
      :type updating_settings: Settings


   .. method:: _update_names(names, metadatas, updating_names, updating_metadatas)
      :staticmethod:


      Updates a list of domain/set names and exportable flags based on reference names and flags.


   .. method:: to_dict(self)


      Serializes the Settings object to a dict.


   .. method:: from_dict(dictionary)
      :staticmethod:


      Deserializes Settings from a dict.



.. py:class:: ExportFlag

   Bases: :class:`enum.Enum`

   Options for exporting Set objects.

   .. attribute:: EXPORTABLE
      

      User has declared that the set should be exported.


   .. attribute:: NON_EXPORTABLE
      

      User has declared that the set should not be exported.


   .. attribute:: FORCED_EXPORTABLE
      

      Set must be exported no matter what.


   .. attribute:: FORCED_NON_EXPORTABLE
      

      Set must never be exported.



.. py:class:: SetMetadata(exportable=ExportFlag.EXPORTABLE, is_additional=False)

   This class holds some additional configuration for Sets.

   .. attribute:: exportable

      set's export flag

      :type: ExportFlag

   .. attribute:: is_additional

      True if the domain does not exist in the database but is supplied separately.

      :type: bool

   :param exportable: set's export flag
   :type exportable: ExportFlag
   :param is_additional: True if the domain does not exist in the database but is supplied separately.
   :type is_additional: bool

   .. method:: __eq__(self, other)


      Returns True if other is equal to this metadata.


   .. method:: is_exportable(self)


      Returns True if Set should be exported.


   .. method:: is_forced(self)


      Returns True if user's export choices should be overriden.


   .. method:: to_dict(self)


      Serializes metadata to a dictionary.


   .. method:: from_dict(metadata_dict)
      :staticmethod:


      Deserializes metadata from a dictionary.



