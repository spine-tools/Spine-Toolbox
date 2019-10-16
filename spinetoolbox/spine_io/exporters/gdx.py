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

Currently, this module supports databases that are "GAMS-like", that is, they follow the EAV model
but the object classes, objects, relationship classes etc. directly reflect the GAMS data
structures. Conversions e.g. from Spine model to TIMES are not supported at the moment.

This module contains low level functions for reading a database into an intermediate format and
for writing that intermediate format into a .gdx file. A higher lever function
to_gdx_file() that does basically everything needed for exporting is provided for convenience.

:author: A. Soininen (VTT)
:date:   30.8.2019
"""

import os
import sys
from gdx2py import GAMSSet, GAMSScalar, GAMSParameter, GdxFile
from spinedb_api import from_database, ParameterValueFormatError


class GdxExportException(Exception):
    """
    An exception raised when something goes wrong within the gdx module.

    Attributes:
        message (str): a message detailing the cause of the exception
    """

    def __init__(self, message):
        super().__init__()
        self._message = message

    @property
    def message(self):
        return self._message

    def __str__(self):
        return self._message


class DomainSet:
    """
    Represents a one-dimensional universal GAMS set.

    Attributes:
        description (str): explanatory text describing the domain
        name (str): domain's name
        records (list): domain's elements as a list of DomainRecord objects
    """

    def __init__(self, object_class):
        """
        Args:
            object_class (namedtuple): an object class row from the database
        """
        self.description = object_class.description if object_class.description is not None else ""
        self.name = object_class.name
        self.records = list()

    @property
    def dimensions(self):
        """The dimensions of this DomainSet which is always 1"""
        return 1


class Set:
    """
    Represents a (non-domain) GAMS set or a subset.

    Attributes:
        domain_names (list): a list of superset (DomainSet) names
        dimensions (int): number of set's dimensions
        name (str): set's name
        records (list): set's elements as a list of SetRecord objects
    """

    def __init__(self, relationship_class):
        """
        Args:
            relationship_class (namedtuple): a relationship class row from the database
        """
        self.domain_names = [name.strip() for name in relationship_class.object_class_name_list.split(',')]
        self.dimensions = len(self.domain_names)
        self.name = relationship_class.name
        self.records = list()


class Record:
    """
    Represents a GAMS set element in a DomainSet.

    Parameters:
        keys (list): a list  of record's keys
        parameters: record's parameters as a list of Parameter objects
    """

    def __init__(self, object_or_relationship):
        """
        Args:
            object_or_relationship (namedtuple): an object or relationship row from the database
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

    Attributes:
        name (str): parameter's name
        value (float or None): parameter's value
    """

    def __init__(self, object_parameter):
        """
        Args:
            object_parameter (namedtuple): a parameter row from the database
        """
        self.name = object_parameter.parameter_name
        try:
            value = from_database(object_parameter.value)
        except ParameterValueFormatError:
            value = None
        self.value = float(value) if isinstance(value, (int, float)) else None


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
            import winreg

            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "gams.location") as gams_location_key:
                gams_path, _ = winreg.QueryValueEx(gams_location_key, None)
                return gams_path
        except FileNotFoundError:
            return None
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "gams" in path.casefold():
            return path
    return None


def domains_to_gams(gdx_file, domains):
    """
    Writes DomainSet objects to .gdx file as universal (index '*') one-dimensional sets.

    Records and Parameters contained within the DomainSets will be written as well.

    Args:
        gdx_file (GdxFile): a target file
        domains (list): a list of DomainSet objects
     """
    for domain in domains:
        domain_parameters = dict()
        record_keys = list()
        for record in domain.records:
            record_key = record.keys[0]
            record_keys.append((record_key,))
            for parameter in record.parameters:
                index_and_value = domain_parameters.setdefault(parameter.name, (list(), list()))
                index_and_value[0].append((record_key,))
                index_and_value[1].append(parameter.value)
        gams_set = GAMSSet(record_keys, expl_text=domain.description)
        gdx_file[domain.name] = gams_set
        for parameter_name, parameter_data in domain_parameters.items():
            parameter_dict = dict()
            for parameter_key, parameter_value in zip(parameter_data[0], parameter_data[1]):
                parameter_dict[parameter_key] = parameter_value
            gams_parameter = GAMSParameter(parameter_dict, domain=[domain.name])
            gdx_file[parameter_name] = gams_parameter


def sets_to_gams(gdx_file, sets):
    """
    Writes Set objects to .gdx file as GAMS sets.

    Records and Parameters contained within the Sets are written as well.

    Args:
        gdx_file (GdxFile): a target file
        sets (list): a list of Set objects
    """
    for current_set in sets:
        set_parameters = dict()
        record_keys = list()
        for record in current_set.records:
            record_key = tuple(record.keys)
            record_keys.append(record_key)
            for parameter in record.parameters:
                index_and_value = set_parameters.setdefault(parameter.name, (list(), list()))
                index_and_value[0].append(record_key)
                index_and_value[1].append(parameter.value)
        gams_set = GAMSSet(record_keys, current_set.domain_names)
        gdx_file[current_set.name] = gams_set
        for parameter_name, parameter_data in set_parameters.items():
            parameter_dict = dict()
            for parameter_key, parameter_value in zip(parameter_data[0], parameter_data[1]):
                parameter_dict[parameter_key] = parameter_value
            gams_parameter = GAMSParameter(parameter_dict, domain=current_set.domain_names)
            gdx_file[parameter_name] = gams_parameter


def domain_parameters_to_gams(gdx_file, domain):
    """
    Adds the parameters from given domain as scalars to .gdx file.

    Args:
        gdx_file (GdxFile): a target file
        domain (DomainSet): a domain that holds the parameters
    """
    for record in domain.records:
        for parameter in record.parameters:
            gams_scalar = GAMSScalar(parameter.value)
            gdx_file[parameter.name] = gams_scalar


def object_classes_to_domains(db_map):
    """
    Converts object classes, objects and object parameters from a database to the intermediate format.

    Object classes get converted to DomainSet objects
    while objects are stored as Records in corresponding DomainSets.
    Lastly, object parameters are read into Records as Parameter objects.

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


def to_gdx_file(database_map, file_name, settings, gams_system_directory=None):
    """
    Exports given database map into .gdx file.

    Args:
        database_map (spinedb_api.DatabaseMapping): a database to export
        settings (Settings): export settings
        gams_system_directory (str): path to GAMS system directory or None to let GAMS choose one for you
    """
    domains = object_classes_to_domains(database_map)
    domains, global_parameters_domain = extract_domain(domains, settings.global_parameters_domain_name)
    domains = filter_and_sort_sets(domains, settings.sorted_domain_names, settings.domain_exportable_flags)
    sort_records_inplace(domains, settings)
    sets = relationship_classes_to_sets(database_map)
    sets = filter_and_sort_sets(sets, settings.sorted_set_names, settings.set_exportable_flags)
    sort_records_inplace(sets, settings)
    with GdxFile(file_name, mode='w', gams_dir=gams_system_directory) as output_file:
        domains_to_gams(output_file, domains)
        sets_to_gams(output_file, sets)
        if global_parameters_domain is not None:
            domain_parameters_to_gams(output_file, global_parameters_domain)


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

    def update(self, updating_settings):
        """
        Updates the settings by merging with another one.

        All domains, sets and records (elements) that are in both settings (common)
        or in `updating_settings` (new) are retained.
        Common elements are ordered the same way they were ordered in the original settings.
        New elements are appended to the common ones in the order they were in `updating_settings`

        Args:
            updating_settings (Settings): settings to merge with
        """
        self._domain_names, self._domain_exportable_flags = self._update_names(
            self._domain_names,
            self._domain_exportable_flags,
            updating_settings._domain_names,
            updating_settings._domain_exportable_flags,
        )
        self._set_names, self._set_exportable_flags = self._update_names(
            self._set_names,
            self._set_exportable_flags,
            updating_settings._set_names,
            updating_settings._set_exportable_flags,
        )
        if self._global_parameters_domain_name not in self._domain_names:
            self._global_parameters_domain_name = ''
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
    def _update_names(names, exportable_flags, updating_names, updating_flags):
        """Updates a list of domain/set names and exportable flags based on reference names and flags."""
        new_names = list()
        new_flags = list()
        updating_names = list(updating_names)
        updating_flags = list(updating_flags)
        for name, exportable in zip(names, exportable_flags):
            try:
                index = updating_names.index(name)
                del updating_names[index]
                del updating_flags[index]
                new_names.append(name)
                new_flags.append(exportable)
            except ValueError:
                # name not found in updating_names -- skip it
                continue
        new_names += updating_names
        new_flags += updating_flags
        return new_names, new_flags

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
