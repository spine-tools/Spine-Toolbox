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
Functions to export a Spine model database to GAMS .gdx file in TIMES format.

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
from helpers import get_db_map


class DomainSet:
    def __init__(self, object_class):
        self.description = object_class.description if object_class.description is not None else ""
        self.dimensions = 1
        self.name = object_class.name
        self.records = list()


class Set:
    def __init__(self, relationship_class):
        self.domain_names = [name.strip() for name in relationship_class.object_class_name_list.split(',')]
        self.dimensions = len(self.domain_names)
        self.name = relationship_class.name
        self.records = list()


class DomainRecord:
    def __init__(self, object_instance):
        self.name = object_instance.name
        self.parameters = list()


class SetRecord:
    def __init__(self, relationship):
        self.domain_records = [name.strip() for name in relationship.object_name_list.split(',')]
        self._name = None
        self.parameters = list()

    @property
    def name(self):
        if self._name is None:
            self._name = ', '.join(self.domain_records)
        return self._name


class Parameter:
    def __init__(self, object_parameter):
        self.name = object_parameter.parameter_name
        try:
            value = from_database(object_parameter.value)
        except ParameterValueFormatError:
            value = None
        self.value = value if isinstance(value, (int, float)) else None


def domains_to_gams(gams_database, domains):
    gams_domains = dict()
    for domain in domains:
        gams_domain = gams_database.add_set(domain.name, domain.dimensions, domain.description)
        gams_domains[domain.name] = gams_domain
        for record in domain.records:
            gams_domain.add_record(record.name)
            for parameter in record.parameters:
                try:
                    gams_parameter = gams_database.get_parameter(parameter.name)
                except gams.workspace.GamsException:
                    gams_parameter = gams_database.add_parameter_dc(parameter.name, [gams_domain])
                gams_parameter.add_record(record.name).value = parameter.value
    return gams_domains


def sets_to_gams(gams_database, sets, gams_domains):
    for current_set in sets:
        required_domains = list()
        for domain_name in current_set.domain_names:
            required_domains.append(gams_domains[domain_name])
        gams_set = gams_database.add_set_dc(current_set.name, required_domains)
        for record in current_set.records:
            gams_set.add_record(record.domain_records)
            for parameter in record.parameters:
                try:
                    gams_parameter = gams_database.get_parameter(parameter.name)
                except gams.workspace.GamsException:
                    gams_parameter = gams_database.add_parameter_dc(parameter.name, required_domains)
                gams_parameter.add_record(record.domain_records).value = parameter.value


def domain_parameters_to_gams(gams_database, domain):
    """
    Adds the parameters from given domain as scalars to GAMS database.

    Args:
        gams_database (GamsDatabase): a GAMS database to which the scalars are added
        domain (DomainSet): a domain that holds the parameters
    """
    for record in domain.records:
        for parameter in record.parameters:
            try:
                gams_parameter = gams_database.get_parameter(parameter.name)
            except gams.workspace.GamsException:
                gams_parameter = gams_database.add_parameter(parameter.name, dimension=0)
            gams_parameter.add_record().value = parameter.value


def object_classes_to_domains(db_map):
    class_list = db_map.object_class_list().all()
    domains = list()
    object_parameter_value_query = db_map.object_parameter_value_list()
    for object_class in class_list:
        domain = DomainSet(object_class)
        domains.append(domain)
        object_list = db_map.object_list(class_id=object_class.id)
        for set_object in object_list:
            record = DomainRecord(set_object)
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
    class_list = db_map.wide_relationship_class_list().all()
    sets = list()
    relationship_parameter_value_query = db_map.relationship_parameter_value_list()
    for relationship_class in class_list:
        current_set = Set(relationship_class)
        sets.append(current_set)
        relationship_list = db_map.wide_relationship_list(class_id=relationship_class.id).all()
        for relationship in relationship_list:
            record = SetRecord(relationship)
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
    gams_database.export(file_name)


def make_gams_workspace():
    return gams.GamsWorkspace()


def make_gams_database(gams_workspace):
    return gams_workspace.add_database()


def filter_and_sort_sets(sets, set_names, set_exportable_flags):
    sets = list(sets)
    sorted_exportable_sets = list()
    for name, exportable in zip(set_names, set_exportable_flags):
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


def sort_records_inplace(domains, settings):
    for domain in domains:
        current_records = list(domain.records)
        records = settings.records(domain.name)
        sorted_records = list()
        for record in records:
            for domain_record in current_records:
                if domain_record.name != record:
                    continue
                sorted_records.append(domain_record)
                current_records.remove(domain_record)
                break
        domain.records = sorted_records


def extract_domain(domains, name_to_extract):
    for index, domain in enumerate(domains):
        if domain.name == name_to_extract:
            del domains[index]
            return domains, domain
    return domains, None


def to_gams_workspace(database_map, settings):
    domains = object_classes_to_domains(database_map)
    domains, global_parameters_domain = extract_domain(domains, settings.global_parameters_domain_name)
    domains = filter_and_sort_sets(domains, settings.domain_names, settings.domain_exportable_flags)
    sort_records_inplace(domains, settings)
    sets = relationship_classes_to_sets(database_map)
    sets = filter_and_sort_sets(sets, settings.set_names, settings.set_exportable_flags)
    sort_records_inplace(sets, settings)
    gams_workspace = make_gams_workspace()
    gams_database = make_gams_database(gams_workspace)
    gams_domains = domains_to_gams(gams_database, domains)
    sets_to_gams(gams_database, sets, gams_domains)
    if global_parameters_domain is not None:
        domain_parameters_to_gams(gams_database, global_parameters_domain)
    return gams_workspace, gams_database


def names(sets):
    return [element.name for element in sets]


def set_records(sets):
    records = dict()
    for set_item in sets:
        records[set_item.name] = [record.name for record in set_item.records]
    return records


def make_settings(database_map):
    domains = object_classes_to_domains(database_map)
    sets = relationship_classes_to_sets(database_map)
    domain_names = names(domains)
    set_names = names(sets)
    records = set_records(domains)
    records.update(set_records(sets))
    return Settings(domain_names, set_names, records)


class Settings:
    def __init__(self, domain_names, set_names, records, domain_exportable_flags=None, set_exportable_flags=None, global_parameters_domain_name=''):
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
    def domain_names(self):
        return self._domain_names

    @property
    def domain_exportable_flags(self):
        return self._domain_exportable_flags

    @property
    def set_names(self):
        return self._set_names

    @property
    def set_exportable_flags(self):
        return self._set_exportable_flags

    def records(self, name):
        return self._records[name]

    @property
    def global_parameters_domain_name(self):
        return self._global_parameters_domain_name

    @global_parameters_domain_name.setter
    def global_parameters_domain_name(self, name):
        self._global_parameters_domain_name = name


def available():
    return gams is not None
