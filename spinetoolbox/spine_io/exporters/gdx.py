######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

GAMS Python bindings need to be installed before most functionality in this module can be used.
The function available() can be used to check if the bindings have been successfully found.

Currently, this module supports databases that are "GAMS-like", that is, they follow the EAV model
but the object classes, objects, relationship classes etc. directly reflect the GAMS data
structures. Conversions e.g. from Spine model to TIMES are not supported.

This module contains low level functions for reading a database into an intermediate format and
for modifying and writing that intermediate format into a .gdx file. A higher lever function
to_gams_workspace() does basically everything that is needed for exporting.

:author: A. Soininen (VTT)
:date:   30.8.2019
"""

import logging

try:
    import gams
except ImportError:
    logging.info('No GAMS Python bindings installed. GDX support is unavailable.')
    gams = None
from spinedb_api import from_database, ParameterValueFormatError


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
        return self._message

    def __str__(self):
        return self._message


class DomainSet:
    """Represents a one-dimensional universal GAMS set."""

    def __init__(self, object_class):
        """Constructs a DomainSet from an object class.

        Args:
            description (str): explanatory text describing the domain
            name (str): domain's name
            records (list): domain's elements as a list of DomainRecord objects
        """
        self.description = object_class.description if object_class.description is not None else ""
        self.name = object_class.name
        self.records = list()

    @property
    def dimensions(self):
        """The dimensions of this DomainSet which is always 1"""
        return 1


class Set:
    """Represents a (non-domain) GAMS set or a subset."""

    def __init__(self, relationship_class):
        """Constructs a new Set from a relationship class.

        Args:
            domain_names (list): a list of superset (DomainSet) names
            dimensions (int): number of set's dimensions
            name (str): set's name
            records (list): set's elements as a list of SetRecord objects
        """
        self.domain_names = [name.strip() for name in relationship_class.object_class_name_list.split(',')]
        self.dimensions = len(self.domain_names)
        self.name = relationship_class.name
        self.records = list()


class Record:
    """Represents a GAMS set element in a DomainSet."""

    def __init__(self, object_or_relationship):
        """Constructs a DomainRecord from a database object.

        Args:
            keys (list): a list  of record's keys
            parameters: record's parameters as a list of Parameter objects
        """
        if hasattr(object_or_relationship, "object_name_list"):
            self.keys = [name.strip() for name in object_or_relationship.object_name_list.split(',')]
        else:
            self.keys = [object_or_relationship.name]
        self.parameters = list()


class Parameter:
    """
    Represents a GAMS parameter.

    Supports only plain values. Does not support time series, time patterns etc.
    """

    def __init__(self, object_parameter):
        """Constructs a parameter from object or relationship parameter.

        Args:
            name (str): parameter's name
            value (float, int or None): parameter's value
        """
        self.name = object_parameter.parameter_name
        try:
            value = from_database(object_parameter.value)
        except ParameterValueFormatError:
            value = None
        self.value = value if isinstance(value, (int, float)) else None


def domains_to_gams(gams_database, domains):
    """
    Writes DomainSet objects to GAMS database as universal one-dimensional sets.

    DomainRecords and Parameters contained within the DomainSets will be written as well.

    Args:
        gams_database (GamsDatabase): a target GAMS database
        domains (list): a list of DomainSet objects

    Returns:
        the list of the GamsSet objects that were written to the database
     """
    try:
        gams_domains = dict()
        for domain in domains:
            gams_domain = gams_database.add_set(domain.name, domain.dimensions, domain.description)
            gams_domains[domain.name] = gams_domain
            for record in domain.records:
                record_key = record.keys[0]
                gams_domain.add_record(record_key)
                for parameter in record.parameters:
                    try:
                        gams_parameter = gams_database.get_parameter(parameter.name)
                    except gams.workspace.GamsException:
                        gams_parameter = gams_database.add_parameter_dc(parameter.name, [gams_domain])
                    gams_parameter.add_record(record_key).value = parameter.value
        return gams_domains
    except gams.GamsException as gams_exception:
        raise GdxExportException(str(gams_exception)) from gams_exception


def sets_to_gams(gams_database, sets, gams_domains):
    """
    Writes Set objects to GAMS database as GAMS sets.

    SetRecords and Parameters contained within the Sets are written as well.

    The database should already contain all DomainSets since the Sets use the DomainRecords as their index.

    Args:
        gams_database (GamsDatabase): a target GAMS database
        sets (list): a list of Set objects
        gams_domains (dict): a list of GamsSet objects corresponding to DomainSets already written to the database
    """
    try:
        for current_set in sets:
            required_domains = list()
            for domain_name in current_set.domain_names:
                required_domains.append(gams_domains[domain_name])
            gams_set = gams_database.add_set_dc(current_set.name, required_domains)
            for record in current_set.records:
                gams_set.add_record(record.keys)
                for parameter in record.parameters:
                    try:
                        gams_parameter = gams_database.get_parameter(parameter.name)
                    except gams.workspace.GamsException:
                        gams_parameter = gams_database.add_parameter_dc(parameter.name, required_domains)
                    gams_parameter.add_record(record.keys).value = parameter.value
    except gams.GamsException as gams_exception:
        raise GdxExportException(str(gams_exception)) from gams_exception


def domain_parameters_to_gams(gams_database, domain):
    """
    Adds the parameters from given domain as scalars to GAMS database.

    Args:
        gams_database (GamsDatabase): a GAMS database to which the scalars are added
        domain (DomainSet): a domain that holds the parameters
    """
    try:
        for record in domain.records:
            for parameter in record.parameters:
                try:
                    gams_parameter = gams_database.get_parameter(parameter.name)
                except gams.workspace.GamsException:
                    gams_parameter = gams_database.add_parameter(parameter.name, dimension=0)
                gams_parameter.add_record().value = parameter.value
    except gams.GamsException as gams_exception:
        raise GdxExportException(str(gams_exception)) from gams_exception


def object_classes_to_domains(db_map):
    """
    Converts object classes, objects and object parameters from a database to the intermediate format.

    Object classes get converted to DomainSet objects
    while objects are stored as DomainRecords in corresponding DomainSets.
    Lastly, object parameters are read into DomainRecords as Parameter objects.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a list of DomainSet objects
    """
    class_list = db_map.object_class_list().all()
    domains = list()
    object_parameter_value_query = db_map.object_parameter_value_list()
    for object_class in class_list:
        domain = DomainSet(object_class)
        domains.append(domain)
        object_list = db_map.object_list(class_id=object_class.id)
        for set_object in object_list:
            record = Record(set_object)
            domain.records.append(record)
            parameter_values = object_parameter_value_query.filter(
                db_map.object_parameter_value_sq.c.object_id == set_object.id
            ).all()
            for parameter in parameter_values:
                parameter = Parameter(parameter)
                if parameter.value is not None:
                    record.parameters.append(parameter)
    return domains


def relationship_classes_to_sets(db_map):
    """
    Converts relationship classes, relationships and relationship parameters from a database to the intermediate format.

    Relationship classes get converted to Set objects
    while relationships are stored as SetRecords in corresponding Sets.
    Lastly, relationship parameters are read into SetRecords as Parameter objects.

    Args:
        db_map (spinedb_api.DatabaseMapping): a database map

    Returns:
         a list of Set objects
    """
    class_list = db_map.wide_relationship_class_list().all()
    sets = list()
    relationship_parameter_value_query = db_map.relationship_parameter_value_list()
    for relationship_class in class_list:
        current_set = Set(relationship_class)
        sets.append(current_set)
        relationship_list = db_map.wide_relationship_list(class_id=relationship_class.id).all()
        for relationship in relationship_list:
            record = Record(relationship)
            current_set.records.append(record)
            parameter_values = relationship_parameter_value_query.filter(
                db_map.relationship_parameter_value_sq.c.relationship_id == relationship.id
            ).all()
            for parameter in parameter_values:
                parameter = Parameter(parameter)
                if parameter.value is not None:
                    record.parameters.append(parameter)
    return sets


def export_to_gdx(gams_database, file_name):
    """Writes a GamsDatabase object to given file."""
    gams_database.export(file_name)


def make_gams_workspace(gams_system_directory=None):
    """
    Returns a freshly created GamsWorkspace object.

    Args:
        gams_system_directory (str): path to GAMS system directory or None to let GAMS choose one for you

    Returns:
        a GAMS workspace
    """
    # This may emit a ResourceWarning (unclosed file).
    # It is harmless but don't know how to suppress it.
    return gams.GamsWorkspace(system_directory=gams_system_directory)


def make_gams_database(gams_workspace):
    """Adds a database to GAMS workspace and returns the database"""
    return gams_workspace.add_database()


def filter_and_sort_sets(sets, sorted_set_names, filter_flags):
    """
    Returns a list of sets sorted by `sorted_set_names` and their filter flag set to True

    This function removes the sets that are not supposed to be exported and sorts the rest
    according to the order specified by `sorted_set_names`.

    Args:
        sets (list): a list of sets (DomainSet or Set) to be filtered and sorted
        sorted_set_names (list): a list of set names in the order they should be in the output list,
            including ones to be removed
        filter_flags (list): list of booleans in the same order as `sorted_set_names`;
            if True the corresponding set will be included in the output

    Returns:
        a list of sets
    """
    sets = list(sets)
    sorted_exportable_sets = list()
    for name, exportable in zip(sorted_set_names, filter_flags):
        if not exportable:
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
        domains (list): a list of DomainSet objects
        name_to_extract (str): name of the domain to be extracted

    Returns:
        a tuple (list, DomainSet) of the modified domains list and the extracted DomainSet object
    """
    for index, domain in enumerate(domains):
        if domain.name == name_to_extract:
            del domains[index]
            return domains, domain
    return domains, None


def to_gams_workspace(database_map, settings, gams_system_directory=None):
    """
    Exports given database map into GAMS database.

    This high-level function reads the data from `database_map` and writes it to a GAMS database
     returning the database and corresponding GAMS workspace.

    Args:
        database_map (spinedb_api.DatabaseMapping): a database to export
        settings (Settings): export settings
        gams_system_directory (str): path to GAMS system directory or None to let GAMS choose one for you

    Returns:
        a tuple of (GamsWorkspace, GamsDatabase)
    """
    domains = object_classes_to_domains(database_map)
    domains, global_parameters_domain = extract_domain(domains, settings.global_parameters_domain_name)
    domains = filter_and_sort_sets(domains, settings.sorted_domain_names, settings.domain_exportable_flags)
    sort_records_inplace(domains, settings)
    sets = relationship_classes_to_sets(database_map)
    sets = filter_and_sort_sets(sets, settings.sorted_set_names, settings.set_exportable_flags)
    sort_records_inplace(sets, settings)
    try:
        gams_workspace = make_gams_workspace(gams_system_directory)
    except gams.workspace.GamsException as gams_exc:
        raise RuntimeError(gams_exc)
    gams_database = make_gams_database(gams_workspace)
    gams_domains = domains_to_gams(gams_database, domains)
    sets_to_gams(gams_database, sets, gams_domains)
    if global_parameters_domain is not None:
        domain_parameters_to_gams(gams_database, global_parameters_domain)
    return gams_workspace, gams_database


def names(sets):
    """Returns the names of given sets as a list."""
    return [element.name for element in sets]


def set_records(sets):
    """Returns a dictionary mapping set name to its records' keys."""
    records = dict()
    for set_item in sets:
        records[set_item.name] = [record.keys for record in set_item.records]
    return records


def make_settings(database_map):
    """
    Builds a Settings object from given database.

    Args:
        database_map (spinedb_api.DatabaseMapping): a database from which domains, sets, records etc are extracted

    Returns:
        a Settings object useful for exporting the given `database_map`
    """
    domains = object_classes_to_domains(database_map)
    sets = relationship_classes_to_sets(database_map)
    domain_names = names(domains)
    set_names = names(sets)
    records = set_records(domains)
    records.update(set_records(sets))
    return Settings(domain_names, set_names, records)


class Settings:
    """
    This class holds some settings needed by `to_gams_workspace()` for .gdx export.

    Settings is mostly concerned about the order in which domains, sets and records are exported into the .gdx file.
    This order is paramount for some models, like TIMES.
    """

    def __init__(
        self,
        domain_names,
        set_names,
        records,
        domain_exportable_flags=None,
        set_exportable_flags=None,
        global_parameters_domain_name='',
    ):
        """
        Constructs a new Settings object.

        Args:
            domain_names (list): a list of DomainSet names
            set_names (list): a list of Set names
            records (dict): a mapping from DomainSet or Set names to record names
            domain_exportable_flags (list): a boolean for each name in domain_names indicating if it should be exported
            set_exportable_flags (list): a boolean for each name in set_names indicating if it should be exported
            global_parameters_domain_name (str): name of the DomainSet whose parameters to export as GAMS scalars
        """
        self._domain_names = domain_names
        self._set_names = set_names
        self._records = records
        if domain_exportable_flags is None:
            domain_exportable_flags = len(domain_names) * [True]
        self._domain_exportable_flags = domain_exportable_flags
        if set_exportable_flags is None:
            set_exportable_flags = len(set_names) * [True]
        self._set_exportable_flags = set_exportable_flags
        self._global_parameters_domain_name = global_parameters_domain_name

    @property
    def sorted_domain_names(self):
        """this list defines the order in which domains are exported into the .gdx file."""
        return self._domain_names

    @property
    def domain_exportable_flags(self):
        """
        this list contains booleans for each name in `domain_names`
        which when True, mark the domain to be exported.
        """
        return self._domain_exportable_flags

    @property
    def sorted_set_names(self):
        """this list defines the order in which sets are exported into the .gdx file."""
        return self._set_names

    @property
    def set_exportable_flags(self):
        """
        this list contains booleans for each name in `set_names`
        which when True, mark the domain to be exported.
        """
        return self._set_exportable_flags

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

    @property
    def global_parameters_domain_name(self):
        """the name of the domain, parameters of which should be exported as GAMS scalars"""
        return self._global_parameters_domain_name

    @global_parameters_domain_name.setter
    def global_parameters_domain_name(self, name):
        """Sets the global parameters domain name to given name."""
        self._global_parameters_domain_name = name

    def to_dict(self):
        """Serializes the Settings object to a dict."""
        as_dictionary = {
            "domain names": self._domain_names,
            "domain exportable flags": self._domain_exportable_flags,
            "set names": self._set_names,
            "set exportable flags": self._set_exportable_flags,
            "records": self._records,
            "global parameters domain name": self._global_parameters_domain_name,
        }
        return as_dictionary

    @staticmethod
    def from_dict(dictionary):
        """Deserializes Settings from a dict."""
        domain_names = dictionary.get("domain names", list())
        domain_exportable_flags = dictionary.get("domain exportable flags", None)
        set_names = dictionary.get("set names", list())
        set_exportable_flags = dictionary.get("set exportable flags", None)
        records = dictionary.get("records", list())
        global_parameters_domain_name = dictionary.get("global parameters domain name", "")
        settings = Settings(
            domain_names,
            set_names,
            records,
            domain_exportable_flags,
            set_exportable_flags,
            global_parameters_domain_name,
        )
        return settings


def gams_import_error():
    """
    Checks if sufficiently recent GAMS Python binding have been installed.

    Returns:
         an empty string if usable bindings are found, otherwise the string contains an error message
    """
    if gams is None:
        return "Could not load the `gams` package. No GAMS Python bindings found."
    if not hasattr(gams, "GamsWorkspace"):
        return "Could not find `GamsWorkspace` in `gams` package. GAMS Python bindings seem to be broken."
    if gams.GamsWorkspace.api_major_rel_number < 24 and gams.GamsWorkspace.api_gold_rel_number < 1:
        return "GAMS version {} is too old. Minimum version required 24.0.1.".format(gams.GamsWorkspace.api_version)
    return ""
