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
from spinedb_api import DatabaseMapping, from_database, ParameterValueFormatError


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
        self.parameters = list()


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


def available():
    return gams is not None
