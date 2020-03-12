######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
For exporting a database to GAMS .gdx file.

Currently, this module supports databases that are "GAMS-like", that is, they follow the EAV model
but the object classes, objects, relationship classes etc. directly reflect the GAMS data
structures. Conversions e.g. from Spine model to TIMES are not supported at the moment.

This module contains low level functions for reading a database into an intermediate format and
for writing that intermediate format into a .gdx file. A higher lever function
to_gdx_file() that does basically everything needed for exporting is provided for convenience.

:author: A. Soininen (VTT)
:date:   30.8.2019
"""

import enum
import itertools
import os
import os.path
import sys
from gdx2py import GAMSSet, GAMSScalar, GAMSParameter, GdxFile
from spinedb_api import from_database, IndexedValue, Map, ParameterValueFormatError

if sys.platform == 'win32':
    import winreg


class GdxExportException(Exception):
    """An exception raised when something goes wrong within the gdx module."""

    def __init__(self, message):
        """
        Args:
            message (str): a message detailing the cause of the exception
        """
        super().__init__()
        self._message = message

    @property
    def message(self):
        """A message detailing the cause of the exception."""
        return self._message

    def __str__(self):
        """Returns the message detailing the cause of the exception."""
        return self._message


class Set:
    """
    Represents a GAMS domain, set or a subset.

    Attributes:
        description (str): set's explanatory text
        domain_names (list): a list of superset (domain) names, None if the Set is a domain
        name (str): set's name
        records (list): set's elements as a list of Record objects
    """

    def __init__(self, name, description="", domain_names=None):
        """
        Args:
            name (str): set's name
            description (str): set's explanatory text
            domain_names (list): a list of indexing domain names
        """
        self.description = description
        self.domain_names = domain_names if domain_names is not None else [None]
        self.name = name
        self.records = list()

    @property
    def dimensions(self):
        """Number of dimensions of this Set."""
        return len(self.domain_names)

    def is_domain(self):
        """Returns True if this set is a domain set."""
        return self.domain_names[0] is None

    def to_dict(self):
        """Stores Set to a dictionary."""
        set_dict = dict()
        set_dict["name"] = self.name
        set_dict["description"] = self.description
        set_dict["domain_names"] = self.domain_names
        set_dict["records"] = [record.to_dict() for record in self.records]
        return set_dict

    @staticmethod
    def from_dict(set_dict):
        """Restores Set from a dictionary."""
        name = set_dict["name"]
        description = set_dict["description"]
        domain_names = set_dict["domain_names"]
        restored = Set(name, description, domain_names)
        restored.records = [Record.from_dict(record_dict) for record_dict in set_dict["records"]]
        return restored

    @staticmethod
    def from_object_class(object_class):
        """
        Constructs a Set from database's object class row.

        Args:
            object_class (namedtuple): an object class row from the database
        """
        name = object_class.name
        description = object_class.description if object_class.description is not None else ""
        return Set(name, description)

    @staticmethod
    def from_relationship_class(relationship_class):
        """
        Constructs a Set from database's relationship class row.

        Args:
            relationship_class (namedtuple): a relationship class row from the database
        """
        name = relationship_class.name
        domain_names = [name.strip() for name in relationship_class.object_class_name_list.split(',')]
        return Set(name, domain_names=domain_names)


class Record:
    """
    Represents a GAMS set element in a Set.

    Parameters:
        keys (tuple): a tuple of record's keys
    """

    def __init__(self, keys):
        """
        Args:
            keys (tuple): a tuple of record's keys
        """
        self.keys = keys

    def __eq__(self, other):
        """
        Returns True if other is equal to self.

        Args:
            other (Record):  a record to compare to
        """
        if not isinstance(other, Record):
            return NotImplemented
        return other.keys == self.keys

    @property
    def name(self):
        """Record's 'name' as a comma separated list of its keys."""
        return ",".join(self.keys)

    def to_dict(self):
        """Stores Record to a dictionary."""
        record_dict = dict()
        record_dict["keys"] = self.keys
        return record_dict

    @staticmethod
    def from_dict(record_dict):
        """Restores Record from a dictionary."""
        keys = record_dict["keys"]
        restored = Record(tuple(keys))
        return restored

    @staticmethod
    def from_object(object_):
        """
        Constructs a record from database's object row.

        Args:
            object_ (namedtuple): an object or relationship row from the database
        """
        keys = (object_.name,)
        return Record(keys)

    @staticmethod
    def from_relationship(relationship):
        """
        Constructs a record from database's relationship row.

        Args:
            relationship (namedtuple): a relationship row from the database
        """
        keys = tuple(name.strip() for name in relationship.object_name_list.split(','))
        return Record(keys)


class Parameter:
    """
    Represents a GAMS parameter.

    Attributes:
        domain_names (list): indexing domain names (currently Parameters can be indexed by domains only)
        indexes (list): parameter's indexes
        values (list): parameter's values
    """

    def __init__(self, domain_names, indexes, values):
        """
        Args:
            domain_names (list): indexing domain names (currently Parameters can be indexed by domains only)
            indexes (list): parameter's indexes
            values (list): parameter's values
        """
#        if len(domain_names) != len(indexes[0]) and len(indexes[0]) > 0:
#            raise GdxExportException("Different number of parameter indexing domains and index keys.")
        self.domain_names = domain_names
        if len(indexes) != len(values):
            raise GdxExportException("Parameter index and value length mismatch.")
        self.indexes = indexes
        if not all([isinstance(value, type(values[0])) for value in values]):
            raise GdxExportException("Not all values are of the same type.")
        self.values = values

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return NotImplemented
        return other.domain_names == self.domain_names and other.indexes == self.indexes and other.values == self.values

    def append_value(self, index, value):
        """
        Appends a new value.

        Args:
            index (tuple): record keys indexing the value
            value: a value
        """
        self.indexes.append(index)
        self.values.append(value)

    def append_object_parameter(self, object_parameter):
        """
        Appends a value from object parameter.

        Args:
            object_parameter (namedtuple): an object parameter row from the database
        """
        index = (object_parameter.object_name,)
        value = _read_value(object_parameter.value)
        self.append_value(index, value)

    def append_relationship_parameter(self, relationship_parameter):
        """
        Appends a value from relationship parameter.

        Args:
            relationship_parameter (namedtuple): a relationship parameter row from the database
        """
        index = tuple(name.strip() for name in relationship_parameter.object_name_list.split(","))
        value = _read_value(relationship_parameter.value)
        self.append_value(index, value)

    def slurp(self, parameter):
        """
        Appends the indexes and values from another parameter.

        Args:
            parameter (Parameter): a parameter to append from
        """
        self.indexes += parameter.indexes
        self.values += parameter.values

    def is_scalar(self):
        """Returns True if this parameter contains only scalars."""
        return bool(self.values) and isinstance(self.values[0], float)

    def is_indexed(self):
        """Returns True if this parameter contains only indexed values."""
        return bool(self.values) and isinstance(self.values[0], IndexedValue)

    def expand_indexes(self, indexing_setting):
        """
        Expands indexed values to scalars in place by adding a new dimension (index).

        The indexes and values attributes are resized to accommodate all scalars in the indexed values.
        A new indexing domain is inserted to domain_names and the corresponding keys into indexes.
        Effectively, this increases parameter's dimensions by one.

        Args:
            indexing_setting (IndexingSetting): description of how the expansion should be done
        """
        index_position = indexing_setting.index_position
        indexing_domain = indexing_setting.indexing_domain
        self.domain_names.insert(index_position, indexing_domain.name)
        new_values = list()
        new_indexes = list()
        for parameter_index, parameter_value in zip(self.indexes, self.values):
            for new_index in indexing_domain.indexes:
                expanded_index = tuple(parameter_index[:index_position] + new_index + parameter_index[index_position:])
                new_indexes.append(expanded_index)
            new_values += list(parameter_value.values)
        self.indexes = new_indexes
        self.values = new_values

    @staticmethod
    def from_object_parameter(object_parameter):
        """
        Constructs a GAMS parameter from database's object parameter row

        Args:
            object_parameter (namedtuple): a parameter row from the database
        """
        domain_names = [object_parameter.object_class_name]
        index = (object_parameter.object_name,)
        value = _read_value(object_parameter.value)
        return Parameter(domain_names, [index], [value])

    @staticmethod
    def from_relationship_parameter(relationship_parameter):
        """
        Constructs a GAMS parameter from database's relationship parameter row

        Args:
            relationship_parameter (namedtuple): a parameter row from the database
        """
        domain_names = [name.strip() for name in relationship_parameter.object_class_name_list.split(",")]
        index = tuple(name.strip() for name in relationship_parameter.object_name_list.split(","))
        value = _read_value(relationship_parameter.value)
        return Parameter(domain_names, [index], [value])

    @staticmethod
    def from_entity_class_parameter_definition(entity_class):
        """
        Constructs an empty GAMS parameter from database's parameter definition row

        Args:
            entity_class: a parameter definition row from the database
        """
        domain_names = list()
        if hasattr(entity_class, 'object_class_name_list'):
            domain_list = entity_class.object_class_name_list.split(",")
            for dimension in domain_list:
                domain_names.append(dimension)
        else:
            domain_names = [entity_class.name]
        index = None
        value = None
        return Parameter(domain_names, [index], [value])


class IndexingDomain:
    """
    This class holds the indexes that should be used for indexed parameter value expansion.

    Attributes:
        name (str): indexing domain's name
        description (str): domain's description
    """

    def __init__(self, name, description, indexes, pick_list):
        """
        Picks the keys from base_domain for which the corresponding element in pick_list holds True.

        Args:
            name (str): indexing domain's name
            description (str): domain's description
            indexes (list): a list of indexing key tuples
            pick_list (list): a list of booleans
        """
        self.name = name
        self.description = description
        self._picked_indexes = None
        self._all_indexes = indexes
        self._pick_list = pick_list

    @property
    def indexes(self):
        """a list of picked indexing key tuples"""
        if self._picked_indexes is None:
            picked = list()
            for index, pick in zip(self._all_indexes, self._pick_list):
                if pick:
                    picked.append(index)
            self._picked_indexes = picked
        return self._picked_indexes

    @property
    def all_indexes(self):
        """a list of all indexing key tuples"""
        return self._all_indexes

    @property
    def pick_list(self):
        """list of boolean values where True means the corresponding index should be picked"""
        return self._pick_list

    def sort_indexes(self, settings):
        """
        Sorts the indexes according to settings.

        Args:
            settings (Settings): a Settings object
        """
        self._all_indexes = settings.sorted_record_key_lists(self.name)
        self._picked_indexes = None

    def to_dict(self):
        """Stores IndexingDomain to a dictionary."""
        domain_dict = dict()
        domain_dict["name"] = self.name
        domain_dict["description"] = self.description
        domain_dict["indexes"] = self._all_indexes
        domain_dict["pick_list"] = self._pick_list
        return domain_dict

    @staticmethod
    def from_dict(domain_dict):
        """Restores IndexingDomain from a dictionary."""
        indexes = [tuple(index) for index in domain_dict["indexes"]]
        pick_list = domain_dict["pick_list"]
        return IndexingDomain(domain_dict["name"], domain_dict["description"], indexes, pick_list)

    @staticmethod
    def from_base_domain(base_domain, pick_list):
        """
        Builds a new IndexingDomain from an existing Set.

        Args:
            base_domain (Set): a domain set that holds the indexes
            pick_list (list): a list of booleans
        """
        indexes = list()
        for record in base_domain.records:
            indexes.append(record.keys)
        return IndexingDomain(base_domain.name, base_domain.description, indexes, pick_list)


def sort_indexing_domain_indexes(indexing_settings, settings):
    """
    Sorts the index keys of an indexing domain in place.

    Args:
        indexing_settings (dict): a mapping from parameter name to IndexingSetting
        settings (Settings): settings
    """
    for indexing_setting in indexing_settings.values():
        indexing_domain = indexing_setting.indexing_domain
        indexing_domain.sort_indexes(settings)


def _python_interpreter_bitness():
    """Returns 64 for 64bit Python interpreter or 32 for 32bit interpreter."""
    # As recommended in Python's docs:
    # https://docs.python.org/3/library/platform.html#cross-platform
    return 64 if sys.maxsize > 2 ** 32 else 32


def _read_value(value_in_database):
    """Converts a parameter from its database representation to a value object."""
    try:
        value = from_database(value_in_database)
    except ParameterValueFormatError:
        raise GdxExportException("Failed to read parameter value.")
    if value is not None and not isinstance(value, (float, IndexedValue)):
        raise GdxExportException(f"Unsupported parameter value type '{type(value).__name__}'.")
    if isinstance(value, Map):
        if value.is_nested():
            raise GdxExportException("Nested maps are not supported.")
        if not all(isinstance(x, float) for x in value.values):
            raise GdxExportException("Exporting non-numerical values in map is not supported.")
    return value


def _windows_dlls_exist(gams_path):
    """Returns True if required DLL files exist in given GAMS installation path."""
    bitness = _python_interpreter_bitness()
    # This DLL must exist on Windows installation
    dll_name = "gdxdclib{}.dll".format(bitness)
    dll_path = os.path.join(gams_path, dll_name)
    return os.path.isfile(dll_path)


def find_gams_directory():
    """
    Returns GAMS installation directory or None if not found.

    On Windows systems, this function looks for `gams.location` in registry;
    on other systems the `PATH` environment variable is checked.

    Returns:
        a path to GAMS installation directory or None if not found.
    """
    if sys.platform == "win32":
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "gams.location") as gams_location_key:
                gams_path, _ = winreg.QueryValueEx(gams_location_key, None)
                if not _windows_dlls_exist(gams_path):
                    return None
                return gams_path
        except FileNotFoundError:
            return None
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "gams" in path.casefold():
            return path
    return None


def expand_indexed_parameter_values(parameters, indexing_settings):
    """
    Expands the dimensions of indexed parameter values.

    Args:
        parameters (dict): a map from parameter names to Parameters.
        indexing_settings (dict): mapping from parameter name to IndexingSetting
    """
    for parameter_name, parameter in parameters.items():
        try:
            indexing_setting = indexing_settings[parameter_name]
        except KeyError:
            continue
        parameter.expand_indexes(indexing_setting)


class MergingSetting:
    """
    Holds settings needed to merge a single parameter.

    Attributes:
        parameter_names (list): parameters to merge
        new_domain_name (str): name of the additional domain that contains the parameter names
        new_domain_description (str): explanatory text for the additional domain
        previous_set (str): name of the set containing the parameters before merging;
            not needed for the actual merging but included here to make the parameters' origing traceable
    """

    def __init__(self, parameter_names, new_domain_name, new_domain_description, previous_set, previous_domain_names):
        """
        Args:
            parameter_names (list): parameters to merge
            new_domain_name (str): name of the additional domain that contains the parameter names
            new_domain_description (str): explanatory text for the additional domain
            previous_set (str): name of the set containing the parameters before merging
            previous_domain_names (list): list of parameters' original indexing domains
        """
        self.parameter_names = parameter_names
        self.new_domain_name = new_domain_name
        self.new_domain_description = new_domain_description
        self.previous_set = previous_set
        self._previous_domain_names = previous_domain_names
        self.index_position = len(previous_domain_names)

    def domain_names(self):
        """
        Composes a list of merged parameter's indexing domains.

        Returns:
            list: a list of indexing domains including the new domain containing the merged parameters' names
        """
        return (
            self._previous_domain_names[: self.index_position]
            + [self.new_domain_name]
            + self._previous_domain_names[self.index_position :]
        )

    def to_dict(self):
        """Stores the settings to a dictionary."""
        return {
            "parameters": self.parameter_names,
            "new_domain": self.new_domain_name,
            "domain_description": self.new_domain_description,
            "previous_set": self.previous_set,
            "previous_domains": self._previous_domain_names,
            "index_position": self.index_position,
        }

    @staticmethod
    def from_dict(setting_dict):
        """Restores settings from a dictionary."""
        parameters = setting_dict["parameters"]
        new_domain = setting_dict["new_domain"]
        description = setting_dict["domain_description"]
        previous_set = setting_dict["previous_set"]
        previous_domains = setting_dict["previous_domains"]
        index_position = setting_dict["index_position"]
        setting = MergingSetting(parameters, new_domain, description, previous_set, previous_domains)
        setting.index_position = index_position
        return setting


def update_merging_settings(merging_settings, settings, db_map):
    """
    Returns parameter merging settings updated according to new export settings.

    Args:
        merging_settings (dict): old settings to be updated
        settings (Settings): new gdx export settings
        db_map (spinedb_api.DatabaseMapping): a database map
    Returns:
        dict: merged old and new merging settings
    """
    updated = dict()
    for merged_parameter_name, setting in merging_settings.items():
        if setting.previous_set not in itertools.chain(settings.sorted_domain_names, settings.sorted_set_names):
            continue
        entity_class_sq = db_map.entity_class_sq
        entity_class = db_map.query(entity_class_sq).filter(entity_class_sq.c.name == setting.previous_set).first()
        class_id = entity_class.id
        type_id = entity_class.type_id
        type_name = (
            db_map.query(db_map.entity_class_type_sq).filter(db_map.entity_class_type_sq.c.id == type_id).first().name
        )
        if type_name == "object":
            parameters = db_map.parameter_definition_list(object_class_id=class_id)
        elif type_name == "relationship":
            parameters = db_map.parameter_definition_list(relationship_class_id=class_id)
        else:
            raise GdxExportException(f"Unknown entity class type '{type_name}'")
        defined_parameter_names = [parameter.name for parameter in parameters]
        if not defined_parameter_names:
            continue
        setting.parameter_names = defined_parameter_names
        updated[merged_parameter_name] = setting
    return updated


def merging_domain(merging_setting):
    """Constructs the additional indexing domain which contains the merged parameters' names."""
    new_domain = Set(merging_setting.new_domain_name, merging_setting.new_domain_description)
    new_domain.records = [Record((name,)) for name in merging_setting.parameter_names]
    return new_domain


def merge_parameters(parameters, merging_settings):
    """
    Merges multiple parameters into a single parameter.

    Note, that the merged parameters will be removed from the parameters dictionary.

    Args:
        parameters (dict): a mapping from existing parameter name to its Parameter object
        merging_settings (dict): a mapping from the merged parameter name to its merging settings
    Returns:
        dict: a mapping from merged parameter name to its Parameter object
    """
    merged = dict()
    for parameter_name, setting in merging_settings.items():
        indexes = list()
        values = list()
        index_position = setting.index_position
        for name in setting.parameter_names:
            parameter = parameters.pop(name)
            for value, base_index in zip(parameter.values, parameter.indexes):
                expanded_index = base_index[:index_position] + (name,) + base_index[index_position:]
                indexes.append(expanded_index)
                values.append(value)
        merged[parameter_name] = Parameter(setting.domain_names(), indexes, values)
    return merged


def sets_to_gams(gdx_file, sets, omitted_set=None):
    """
    Writes Set objects to .gdx file as GAMS sets.

    Records and Parameters contained within the Sets are written as well.

    Args:
        gdx_file (GdxFile): a target file
        sets (list): a list of Set objects
        omitted_set (Set): prevents writing this set even if it is included in given sets
    """
    for current_set in sets:
        if omitted_set is not None and current_set.name == omitted_set.name:
            continue
        record_keys = list()
        for record in current_set.records:
            record_keys.append(record.keys)
        gams_set = GAMSSet(record_keys, current_set.domain_names, expl_text=current_set.description)
        gdx_file[current_set.name] = gams_set


def parameters_to_gams(gdx_file, parameters):
    """
    Writes parameters to .gdx file as GAMS parameters.

    Args:
        gdx_file (GdxFile): a target file
        parameters (dict): a list of Parameter objects
    """
    for parameter_name, parameter in parameters.items():
        indexed_values = dict()
        for index, value in zip(parameter.indexes, parameter.values):
            if not isinstance(value, float) and not (index == None and value == None):
                if isinstance(value, IndexedValue):
                    raise GdxExportException(
                        f"Cannot write parameter '{parameter_name}':"
                        + " parameter contains indexed values but indexing domain information is missing."
                    )
                raise GdxExportException(
                    f"Cannot write parameter '{parameter_name}':"
                    + f" parameter contains unsupported values of type '{type(value)}'."
                )
            if isinstance(value, float):
                indexed_values[tuple(index)] = value
        gams_parameter = GAMSParameter(indexed_values, domain=parameter.domain_names)
        gdx_file[parameter_name] = gams_parameter


def domain_parameters_to_gams_scalars(gdx_file, parameters, domain_name):
    """
    Adds the parameter from given domain as a scalar to .gdx file.

    The added parameters are erased from parameters.

    Args:
        gdx_file (GdxFile): a target file
        parameters (dict): a map from parameter name to Parameter object
        domain_name (str): name of domain whose parameters to add
    Returns:
        a list of non-scalar parameters
    """
    erase_parameters = list()
    for parameter_name, parameter in parameters.items():
        if parameter.domain_names == [domain_name]:
            if len(parameter.values) != 1 or not parameter.is_scalar():
                raise GdxExportException("Parameter {} is not suitable as GAMS scalar.")
            gams_scalar = GAMSScalar(parameter.values[0])
            gdx_file[parameter_name] = gams_scalar
            erase_parameters.append(parameter_name)
    return erase_parameters


def object_classes_to_domains(db_map):
    """
    Converts object classes, objects and object parameters from a database to the intermediate format.

    Object classes get converted to Set objects
    while objects are stored as Records in corresponding DomainSets.
    Lastly, object parameters are read into Parameter objects.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a tuple containing list of Set objects and a dict of Parameter objects
    """
    class_list = db_map.object_class_list().all()
    domains = list()
    parameters = dict()
    object_parameter_value_query = db_map.object_parameter_value_list()
    for object_class in class_list:
        domain = Set.from_object_class(object_class)
        domains.append(domain)
        object_list = db_map.object_list(class_id=object_class.id)
        for set_object in object_list:
            record = Record.from_object(set_object)
            domain.records.append(record)
            parameter_values = object_parameter_value_query.filter(
                db_map.object_parameter_value_sq.c.object_id == set_object.id
            ).all()
            for object_parameter in parameter_values:
                name = object_parameter.parameter_name
                parameter = parameters.get(name, None)
                if parameter is None:
                    parameters[name] = Parameter.from_object_parameter(object_parameter)
                else:
                    parameter.append_object_parameter(object_parameter)
        parameter_definitions = db_map.parameter_definition_list(object_class_id=object_class.id).all()
        for parameter_definition in parameter_definitions:
            name = parameter_definition.name
            parameter = parameters.get(name, None)
            if parameter is None:
                parameters[name] = Parameter.from_entity_class_parameter_definition(object_class)
    return domains, parameters


def relationship_classes_to_sets(db_map):
    """
    Converts relationship classes, relationships and relationship parameters from a database to the intermediate format.

    Relationship classes get converted to Set objects
    while relationships are stored as SetRecords in corresponding Sets.
    Lastly, relationship parameters are read into Parameter objects.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a tuple containing a list of Set objects and a dict of Parameter objects
    """
    class_list = db_map.wide_relationship_class_list().all()
    sets = list()
    parameters = dict()
    relationship_parameter_value_query = db_map.relationship_parameter_value_list()
    for relationship_class in class_list:
        current_set = Set.from_relationship_class(relationship_class)
        sets.append(current_set)
        relationship_list = db_map.wide_relationship_list(class_id=relationship_class.id).all()
        for relationship in relationship_list:
            record = Record.from_relationship(relationship)
            current_set.records.append(record)
            parameter_values = relationship_parameter_value_query.filter(
                db_map.relationship_parameter_value_sq.c.relationship_id == relationship.id
            ).all()
            for relationship_parameter in parameter_values:
                name = relationship_parameter.parameter_name
                parameter = parameters.get(name, None)
                if parameter is None:
                    parameters[name] = Parameter.from_relationship_parameter(relationship_parameter)
                else:
                    parameter.append_relationship_parameter(relationship_parameter)
        parameter_definitions = db_map.parameter_definition_list(relationship_class_id=relationship_class.id).all()
        for parameter_definition in parameter_definitions:
            name = parameter_definition.name
            parameter = parameters.get(name, None)
            if parameter is None:
                parameters[name] = Parameter.from_entity_class_parameter_definition(relationship_class)
    return sets, parameters


def domain_names_and_records(db_map):
    """
    Returns a list of domain names and a map from a name to list of record keys.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a tuple containing list of domain names and a dict from domain name to its records
    """
    domain_names = list()
    domain_records = dict()
    class_list = db_map.object_class_list().all()
    for object_class in class_list:
        domain_name = object_class.name
        domain_names.append(domain_name)
        object_list = db_map.object_list(class_id=object_class.id).all()
        records = list()
        for set_object in object_list:
            records.append((set_object.name,))
        domain_records[domain_name] = records
    return domain_names, domain_records


def set_names_and_records(db_map):
    """
    Returns a list of set names and a map from a name to list of record keys.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a tuple containing list of set names and a dict from set name to its records
    """
    names = list()
    set_records = dict()
    class_list = db_map.wide_relationship_class_list().all()
    for relationship_class in class_list:
        set_name = relationship_class.name
        names.append(set_name)
        relationship_list = db_map.wide_relationship_list(class_id=relationship_class.id).all()
        records = list()
        for relationship in relationship_list:
            records.append(tuple(name.strip() for name in relationship.object_name_list.split(",")))
        set_records[set_name] = records
    return names, set_records


class IndexingSetting:
    """
    Settings for indexed value expansion for a single Parameter.

    Attributes:
        parameter (Parameter): a parameter containing indexed values
        indexing_domain (IndexingDomain): indexing info
        index_position (int): where to insert the new index when expanding a parameter
    """

    def __init__(self, indexed_parameter):
        """
        Args:
            indexed_parameter (Parameter): a parameter containing indexed values
        """
        self.parameter = indexed_parameter
        self.indexing_domain = None
        self.index_position = len(indexed_parameter.domain_names)

    def append_parameter(self, parameter):
        """Adds indexes and values from another parameter."""
        self.parameter.slurp(parameter)


def make_indexing_settings(db_map):
    """
    Constructs skeleton indexing settings for parameter indexed value expansion.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database mapping
    Returns:
        dict: a mapping from parameter name to IndexingSetting
    """
    settings = dict()
    object_parameter_value_query = db_map.object_parameter_value_list()
    for object_parameter in object_parameter_value_query.all():
        parameter = Parameter.from_object_parameter(object_parameter)
        if not parameter.is_indexed():
            continue
        setting = settings.get(object_parameter.parameter_name, None)
        if setting is not None:
            setting.append_parameter(parameter)
        else:
            settings[object_parameter.parameter_name] = IndexingSetting(parameter)
    relationship_parameter_value_query = db_map.relationship_parameter_value_list()
    for relationship_parameter in relationship_parameter_value_query.all():
        parameter = Parameter.from_relationship_parameter(relationship_parameter)
        if not parameter.is_indexed():
            continue
        setting = settings.get(relationship_parameter.parameter_name, None)
        if setting is not None:
            setting.append_parameter(parameter)
        else:
            settings[relationship_parameter.parameter_name] = IndexingSetting(parameter)
    return settings


def update_indexing_settings(old_indexing_settings, new_indexing_settings, settings):
    """
    Returns new indexing settings merged from old and new ones.

    Entries that do not exist in old settings will be removed.
    If entries exist in both settings the old one will be chosen if both entries are 'equal',
    otherwise the new entry will override the old one.
    Entries existing in new settings only will be added.

    Args:
        old_indexing_settings (dict): settings to be updated
        new_indexing_settings (dict): settings used for updating
        settings (Settings): new gdx export settings
    Returns:
        dict: merged old and new indexing settings
    """
    updated = dict()
    for parameter_name, setting in new_indexing_settings.items():
        old_setting = old_indexing_settings.get(parameter_name, None)
        if old_setting is None:
            updated[parameter_name] = setting
            continue
        if setting.parameter != old_setting.parameter:
            updated[parameter_name] = setting
            continue
        if old_setting.indexing_domain is not None:
            if old_setting.indexing_domain.name in settings.sorted_domain_names:
                new_records = settings.sorted_record_key_lists(old_setting.indexing_domain.name)
                indexes = old_setting.indexing_domain.indexes
                if all(index in new_records for index in indexes):
                    updated[parameter_name] = old_setting
                else:
                    updated[parameter_name] = setting
                continue
        updated[parameter_name] = old_setting
    return updated


def indexing_settings_to_dict(settings):
    """
    Stores indexing settings to a JSON compatible dictionary.

    Args:
        settings (dict): a mapping from parameter name to IndexingSetting.
    Returns:
        a JSON serializable dictionary
    """
    settings_dict = dict()
    for parameter_name, setting in settings.items():
        parameter_dict = dict()
        parameter_dict["indexing_domain"] = (
            setting.indexing_domain.to_dict() if setting.indexing_domain is not None else None
        )
        parameter_dict["index_position"] = setting.index_position
        settings_dict[parameter_name] = parameter_dict
    return settings_dict


def indexing_settings_from_dict(settings_dict, db_map):
    """
    Restores indexing settings from a json compatible dictionary.

    Args:
        settings (dict): a JSON compatible dictionary representing parameter indexing settings.
        db_map (DatabaseMapping): database mapping
    Returns:
        a dictionary mapping parameter name to IndexingSetting.
    """
    settings = dict()
    for parameter_name, setting_dict in settings_dict.items():
        parameter = _find_parameter(parameter_name, db_map)
        setting = IndexingSetting(parameter)
        indexing_domain_dict = setting_dict["indexing_domain"]
        if indexing_domain_dict is not None:
            setting.indexing_domain = IndexingDomain.from_dict(indexing_domain_dict)
        setting.index_position = setting_dict["index_position"]
        settings[parameter_name] = setting
    return settings


def _find_parameter(parameter_name, db_map):
    """Searches for parameter_name in db_map and returns Parameter."""
    parameter = None
    parameter_rows = (
        db_map.object_parameter_value_list()
        .filter(db_map.object_parameter_value_sq.c.parameter_name == parameter_name)
        .all()
    )
    if parameter_rows:
        for row in parameter_rows:
            if parameter is None:
                parameter = Parameter.from_object_parameter(row)
            else:
                parameter.append_object_parameter(row)
    if parameter is None:
        parameter_rows = (
            db_map.relationship_parameter_value_list()
            .filter(db_map.relationship_parameter_value_sq.c.parameter_name == parameter_name)
            .all()
        )
        if parameter_rows:
            for row in parameter_rows:
                if parameter is None:
                    parameter = Parameter.from_relationship_parameter(row)
                else:
                    parameter.append_relationship_parameter(row)
    if parameter is None:
        raise GdxExportException(f"Cannot find parameter '{parameter_name}' in the database.")
    return parameter


def filter_and_sort_sets(sets, sorted_set_names, metadatas):
    """
    Returns a list of sets sorted by `sorted_set_names` and their filter flag set to True

    This function removes the sets that are not supposed to be exported and sorts the rest
    according to the order specified by `sorted_set_names`.

    Args:
        sets (list): a list of sets (DomainSet or Set) to be filtered and sorted
        sorted_set_names (list): a list of set names in the order they should be in the output list,
            including ones to be removed
        metadatas (list): list of SetMetadata objects in the same order as `sorted_set_names`;

    Returns:
        list: a list of sets
    """
    sets = list(sets)
    sorted_exportable_sets = list()
    for name, metadata in zip(sorted_set_names, metadatas):
        if not metadata.is_exportable():
            for current_set in sets:
                if current_set.name == name:
                    sets.remove(current_set)
                    break
            continue
        for current_set in sets:
            if current_set.name != name:
                continue
            sorted_exportable_sets.append(current_set)
            sets.remove(current_set)
            break
    return sorted_exportable_sets


def sort_records_inplace(sets, settings):
    """
    Sorts the record lists of given domains according to the order given in settings.

    Args:
        sets (list): a list of DomainSet or Set objects whose records are to be sorted
        settings (Settings): settings that define the sorting order
    """
    for current_set in sets:
        current_records = list(current_set.records)
        sorting_order = settings.sorted_record_key_lists(current_set.name)
        sorted_records = list()
        for record_keys in sorting_order:
            for record in current_records:
                if record.keys != record_keys:
                    continue
                sorted_records.append(record)
                current_records.remove(record)
                break
        current_set.records = sorted_records


def extract_domain(domains, name_to_extract):
    """
    Extracts the domain with given name from a list of domains.

    Args:
        domains (list): a list of Set objects
        name_to_extract (str): name of the domain to be extracted

    Returns:
        a tuple (list, Set) of the modified domains list and the extracted Set object
    """
    for index, domain in enumerate(domains):
        if domain.name == name_to_extract:
            del domains[index]
            return domains, domain
    return domains, None


def to_gdx_file(
    database_map,
    file_name,
    additional_domains,
    settings,
    indexing_settings,
    merging_settings,
    gams_system_directory=None,
):
    """
    Exports given database map into .gdx file.

    Args:
        database_map (spinedb_api.DatabaseMapping): a database to export
        file_name (str): output file name
        additional_domains (list): a list of extra domains not in the database
        settings (Settings): export settings
        indexing_settings (dict): a dictionary containing settings for indexed parameter expansion
        merging_settings (dict): a list of merging settings for parameter merging
        gams_system_directory (str): path to GAMS system directory or None to let GAMS choose one for you
    """
    domains, domain_parameters = object_classes_to_domains(database_map)
    domains, global_parameters_domain = extract_domain(domains, settings.global_parameters_domain_name)
    domains += additional_domains
    domains = filter_and_sort_sets(domains, settings.sorted_domain_names, settings.domain_metadatas)
    sort_records_inplace(domains, settings)
    sort_indexing_domain_indexes(indexing_settings, settings)
    expand_indexed_parameter_values(domain_parameters, indexing_settings)
    sets, set_parameters = relationship_classes_to_sets(database_map)
    sets = filter_and_sort_sets(sets, settings.sorted_set_names, settings.set_metadatas)
    sort_records_inplace(sets, settings)
    expand_indexed_parameter_values(set_parameters, indexing_settings)
    parameters = {**domain_parameters, **set_parameters}
    merged_parameters = merge_parameters(parameters, merging_settings)
    parameters.update(merged_parameters)
    with GdxFile(file_name, mode='w', gams_dir=gams_system_directory) as output_file:
        sets_to_gams(output_file, domains, global_parameters_domain)
        sets_to_gams(output_file, sets)
        deletable_parameter_names = list()
        if global_parameters_domain is not None:
            deletable_parameter_names = domain_parameters_to_gams_scalars(
                output_file, domain_parameters, global_parameters_domain.name
            )
        for name in deletable_parameter_names:
            del parameters[name]
        parameters_to_gams(output_file, parameters)


def make_settings(database_map):
    """
    Builds a Settings object from given database.

    Args:
        database_map (spinedb_api.DatabaseMapping): a database from which domains, sets, records etc are extracted

    Returns:
        a Settings object useful for exporting the given `database_map`
    """
    domain_names, domain_records = domain_names_and_records(database_map)
    set_names, set_records = set_names_and_records(database_map)
    records = domain_records
    records.update(set_records)
    return Settings(domain_names, set_names, records)


class Settings:
    """
    This class holds some settings needed by `to_gdx_file()` for .gdx export.

    Settings is mostly concerned about the order in which domains, sets and records are exported into the .gdx file.
    This order is paramount for some models, like TIMES.
    """

    def __init__(
        self,
        domain_names,
        set_names,
        records,
        domain_metadatas=None,
        set_metadatas=None,
        global_parameters_domain_name="",
    ):
        """
        Constructs a new Settings object.

        Args:
            domain_names (list): a list of Set names
            set_names (list): a list of Set names
            records (dict): a mapping from Set names to record key tuples
            domain_metadatas (list): a list of SetMetadata objects, one for each domain
            set_metadatas (list): a list of SetMetadata objects, one for each set
            global_parameters_domain_name (str): name of the Set whose parameters to export as GAMS scalars
        """
        self._domain_names = domain_names
        self._set_names = set_names
        self._records = records
        if domain_metadatas is None:
            domain_metadatas = [SetMetadata() for _ in range(len(domain_names))]
        self._domain_metadatas = domain_metadatas
        if set_metadatas is None:
            set_metadatas = [SetMetadata() for _ in range(len(set_names))]
        self._set_metadatas = set_metadatas
        self._global_parameters_domain_name = global_parameters_domain_name

    @property
    def sorted_domain_names(self):
        """this list defines the order in which domains are exported into the .gdx file."""
        return self._domain_names

    @property
    def domain_metadatas(self):
        """this list contains SetMetadata objects for each name in `domain_names`"""
        return self._domain_metadatas

    @property
    def sorted_set_names(self):
        """this list defines the order in which sets are exported into the .gdx file."""
        return self._set_names

    @property
    def set_metadatas(self):
        """this list contains SetMetadata objects for each name in `set_names`"""
        return self._set_metadatas

    @property
    def global_parameters_domain_name(self):
        """the name of the domain, parameters of which should be exported as GAMS scalars"""
        return self._global_parameters_domain_name

    @global_parameters_domain_name.setter
    def global_parameters_domain_name(self, name):
        """Sets the global_parameters_domain_name and declares that domain FORCED_NON_EXPORTABLE."""
        if self._global_parameters_domain_name:
            i = self._domain_names.index(self._global_parameters_domain_name)
            self._domain_metadatas[i].exportable = ExportFlag.EXPORTABLE
        if name:
            i = self._domain_names.index(name)
            self._domain_metadatas[i].exportable = ExportFlag.FORCED_NON_EXPORTABLE
        self._global_parameters_domain_name = name

    def add_or_replace_domain(self, domain, metadata):
        """
        Adds a new domain or replaces an existing domain's records and metadata.

        Args:
            domain (Set): a domain to add/replace
            metadata (SetMetadata): domain's metadata
        Returns:
            True if a new domain was added, False if an existing domain was replaced
        """
        self._records[domain.name] = [record.keys for record in domain.records]
        try:
            i = self._domain_names.index(domain.name)
        except ValueError:
            self._domain_names.append(domain.name)
            self._domain_metadatas.append(metadata)
            return True
        self._domain_metadatas[i] = metadata
        return False

    def domain_index(self, domain):
        """Returns an integral index to the domain's name in sorted domain names."""
        return self._domain_names.index(domain.name)

    def del_domain_at(self, index):
        """Erases domain name at given integral index."""
        domain_name = self._domain_names[index]
        del self._domain_names[index]
        del self._domain_metadatas[index]
        del self._records[domain_name]
        if domain_name == self._global_parameters_domain_name:
            self._global_parameters_domain_name = ""

    def update_domain(self, domain):
        """Updates domain's records."""
        self._records[domain.name] = [record.keys for record in domain.records]

    def sorted_record_key_lists(self, name):
        """
        Returns a list of record keys for given domain or set name.

        The list defines the order in which the records are exported into the .gdx file.

        Args:
            name (str): domain or set name

        Returns:
            an ordered list of record key lists
        """
        return self._records[name]

    def update(self, updating_settings):
        """
        Updates the settings by merging with another one.

        All domains, sets and records that are in both settings (common)
        or in `updating_settings` (new) are retained.
        Common elements are ordered the same way they were ordered in the original settings.
        New elements are appended to the common ones in the order they were in `updating_settings`

        Args:
            updating_settings (Settings): settings to merge with
        """
        self._domain_names, self._domain_metadatas = self._update_names(
            self._domain_names,
            self._domain_metadatas,
            updating_settings._domain_names,
            updating_settings._domain_metadatas,
        )
        self._set_names, self._set_metadatas = self._update_names(
            self._set_names, self._set_metadatas, updating_settings._set_names, updating_settings._set_metadatas
        )
        if self._global_parameters_domain_name not in self._domain_names:
            self._global_parameters_domain_name = ""
        new_records = dict()
        updating_records = dict(updating_settings._records)
        for set_name, record_names in self._records.items():
            updating_record_names = updating_records.get(set_name, None)
            if updating_record_names is None:
                continue
            new_record_names = list()
            for name in record_names:
                try:
                    updating_record_names.remove(name)
                    new_record_names.append(name)
                except ValueError:
                    pass
            new_record_names += updating_record_names
            new_records[set_name] = new_record_names
            del updating_records[set_name]
        new_records.update(updating_records)
        self._records = new_records

    @staticmethod
    def _update_names(names, metadatas, updating_names, updating_metadatas):
        """Updates a list of domain/set names and exportable flags based on reference names and flags."""
        new_names = list()
        new_metadatas = list()
        updating_names = list(updating_names)
        updating_metadatas = list(updating_metadatas)
        for name, metadata in zip(names, metadatas):
            try:
                index = updating_names.index(name)
                del updating_names[index]
                del updating_metadatas[index]
                new_names.append(name)
                new_metadatas.append(metadata)
            except ValueError:
                # name not found in updating_names -- skip it
                continue
        new_names += updating_names
        new_metadatas += updating_metadatas
        return new_names, new_metadatas

    def to_dict(self):
        """Serializes the Settings object to a dict."""
        as_dictionary = {
            "domain_names": self._domain_names,
            "domain_metadatas": [metadata.to_dict() for metadata in self._domain_metadatas],
            "set_names": self._set_names,
            "set_metadatas": [metadata.to_dict() for metadata in self._set_metadatas],
            "records": self._records,
            "global_parameters_domain_name": self._global_parameters_domain_name,
        }
        return as_dictionary

    @staticmethod
    def from_dict(dictionary):
        """Deserializes Settings from a dict."""
        domain_names = dictionary.get("domain_names", list())
        domain_metadatas = dictionary.get("domain_metadatas", None)
        if domain_metadatas is not None:
            domain_metadatas = [SetMetadata.from_dict(metadata_dict) for metadata_dict in domain_metadatas]
        set_names = dictionary.get("set_names", list())
        set_metadatas = dictionary.get("set_metadatas", None)
        if set_metadatas is not None:
            set_metadatas = [SetMetadata.from_dict(metadata_dict) for metadata_dict in set_metadatas]
        records = {
            set_name: [tuple(key) for key in keys] for set_name, keys in dictionary.get("records", dict()).items()
        }
        global_parameters_domain_name = dictionary.get("global_parameters_domain_name", "")
        settings = Settings(
            domain_names, set_names, records, domain_metadatas, set_metadatas, global_parameters_domain_name
        )
        return settings


class ExportFlag(enum.Enum):
    """Options for exporting Set objects."""

    EXPORTABLE = enum.auto()
    """User has declared that the set should be exported."""
    NON_EXPORTABLE = enum.auto()
    """User has declared that the set should not be exported."""
    FORCED_EXPORTABLE = enum.auto()
    """Set must be exported no matter what."""
    FORCED_NON_EXPORTABLE = enum.auto()
    """Set must never be exported."""


class SetMetadata:
    """
    This class holds some additional configuration for Sets.

    Attributes:
        exportable (ExportFlag): set's export flag
        is_additional (bool): True if the domain does not exist in the database but is supplied separately.
    """

    def __init__(self, exportable=ExportFlag.EXPORTABLE, is_additional=False):
        """
        Args:
            exportable (ExportFlag): set's export flag
            is_additional (bool): True if the domain does not exist in the database but is supplied separately.
        """
        self.exportable = exportable
        self.is_additional = is_additional

    def __eq__(self, other):
        """Returns True if other is equal to this metadata."""
        if not isinstance(other, SetMetadata):
            return NotImplemented
        return self.exportable == other.exportable and self.is_additional == other.is_additional

    def is_exportable(self):
        """Returns True if Set should be exported."""
        return self.exportable in [ExportFlag.EXPORTABLE, ExportFlag.FORCED_EXPORTABLE]

    def is_forced(self):
        """Returns True if user's export choices should be overriden."""
        return self.exportable in [ExportFlag.FORCED_EXPORTABLE, ExportFlag.FORCED_NON_EXPORTABLE]

    def to_dict(self):
        """Serializes metadata to a dictionary."""
        metadata_dict = dict()
        metadata_dict["exportable"] = self.exportable.value
        metadata_dict["is_additional"] = self.is_additional
        return metadata_dict

    @staticmethod
    def from_dict(metadata_dict):
        """Deserializes metadata from a dictionary."""
        metadata = SetMetadata()
        metadata.exportable = ExportFlag(metadata_dict["exportable"])
        metadata.is_additional = metadata_dict["is_additional"]
        return metadata
