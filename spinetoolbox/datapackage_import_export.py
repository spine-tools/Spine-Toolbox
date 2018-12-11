######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Functions to import/export between spine database and frictionless data's datapackage.

:author: M. Marin (KTH)
:date:   28.8.2018
"""

from datapackage import Package
from spinedatabase_api import SpineDBAPIError
from helpers import busy_effect
import logging


@busy_effect
def datapackage_to_spine(db_map, datapackage_file_path):
    """Convert datapackage from `datapackage_file_path` into Spine `db_map`."""
    insert_log = []
    error_log = []
    datapackage = Package(datapackage_file_path)
    object_class_names = [x.name for x in db_map.object_class_list()]
    parameter_names = [x.name for x in db_map.parameter_list()]
    object_class_name_lists = [x.object_class_name_list.split(",") for x in db_map.wide_relationship_class_list()]
    object_classes = list()
    pre_relationship_classes = list()
    pre_parameters = list()
    for resource in datapackage.resources:
        if resource.name not in object_class_names:
            object_classes.append(dict(name=resource.name))
            object_class_names.append(resource.name)
        primary_key = resource.schema.primary_key
        foreign_keys = resource.schema.foreign_keys
        reference_resource_names = [fk["reference"]["resource"] for fk in foreign_keys]
        for reference_resource_name in reference_resource_names:
            if reference_resource_name not in object_class_names:
                object_classes.append(dict(name=reference_resource_name))
                object_class_names.append(reference_resource_name)
        if reference_resource_names:
            object_class_name_list = [resource.name] + reference_resource_names
            relationship_class_name = "__".join(object_class_name_list)
            pre_relationship_classes.append(dict(
                object_class_name_list=object_class_name_list,
                name=relationship_class_name
            ))
            object_class_name_lists.append(object_class_name_list)
        for field in resource.schema.fields:
            # Skip fields in primary key
            if field.name in primary_key:
                continue
            # Skip fields in any foreign key
            if field in [x for fk in foreign_keys for x in fk["fields"]]:
                continue
            parameter_name = resource.name + "_" + field.name
            if parameter_name not in parameter_names:
                pre_parameters.append(dict(object_class_name=resource.name, name=parameter_name))
                parameter_names.append(parameter_name)
    db_map.add_object_classes(*object_classes)
    object_class_name_id = {x.name: x.id for x in db_map.object_class_list()}
    relationship_classes = [
        dict(
            object_class_id_list=[object_class_name_id[n] for n in r['object_class_name_list']],
            name=r['name']
        ) for r in pre_relationship_classes
    ]
    db_map.add_wide_relationship_classes(*relationship_classes)
    parameters = [
        dict(
            object_class_id=object_class_name_id[p['object_class_name']],
            name=p['name']
        ) for p in pre_parameters
    ]
    db_map.add_parameters(*parameters)
    relationship_class_name_id = {x.name: x.id for x in db_map.wide_relationship_class_list()}
    parameter_name_id = {x.name: x.id for x in db_map.parameter_list()}
    object_names = [x.name for x in db_map.object_list()]
    # Create list of object and preliminary parameter value dicts.
    objects = list()
    pre_parameter_values = list()
    for resource in datapackage.resources:
        object_class_id = object_class_name_id[resource.name]
        primary_key = resource.schema.primary_key
        foreign_keys = resource.schema.foreign_keys
        foreign_keys_fields = [x for fk in foreign_keys for x in fk["fields"]]
        for i, row in enumerate(resource.read(cast=False)):  # TODO: try and get row_dict directly from read method
            row_dict = dict(zip(resource.schema.field_names, row))
            if primary_key:
                object_name = "_".join(row_dict[field] for field in primary_key)
            else:
                object_name = resource.name + str(i)
            if not object_name in object_names:
                objects.append(dict(class_id=object_class_id, name=object_name))
                object_names.append(object_name)
            for field_name, value in row_dict.items():
                if field_name in primary_key:
                    continue
                if field_name in foreign_keys_fields:
                    continue
                parameter_name = resource.name + "_" + field_name
                parameter_id = parameter_name_id[parameter_name]
                pre_parameter_values.append(dict(
                    object_name=object_name,
                    parameter_id=parameter_id,
                    value=value
                ))
    db_map.add_objects(*objects)
    object_name_id = {x.name: x.id for x in db_map.object_list()}
    parameter_values = [
        dict(
            object_id=object_name_id[p['object_name']],
            parameter_id=p['parameter_id'],
            value=p['value']
        ) for p in pre_parameter_values
    ]
    db_map.add_parameter_values(*parameter_values)
    # Create dictionary of reference resource names => list of reference fields names
    reference_resource_dict = dict()
    for resource in datapackage.resources:
        foreign_keys = resource.schema.foreign_keys
        for foreign_key in foreign_keys:
            reference_resource_name = foreign_key["reference"]["resource"]
            reference_fields_names = foreign_key["reference"]["fields"]
            reference_resource_dict.setdefault(reference_resource_name, list()).\
                append(reference_fields_names)
    # Create dictionary of reference resource name => reference fields names
    # => reference key => object id
    reference_object_id_dict = dict()
    for reference_resource_name, reference_fields_names_list in reference_resource_dict.items():
        reference_resource = datapackage.get_resource(reference_resource_name)
        reference_primary_key = reference_resource.schema.primary_key
        reference_object_id_dict[reference_resource_name] = d1 = dict()
        for reference_fields_names in reference_fields_names_list:
            d1[",".join(reference_fields_names)] = d2 = dict()
            for i, row in enumerate(reference_resource.read(cast=False)):
                row_dict = dict(zip(reference_resource.schema.field_names, row))
                # Find object id
                if reference_primary_key:
                    reference_object_name = "_".join(row_dict[field] for field in reference_primary_key)
                else:
                    reference_object_name = reference_resource_name + str(i)
                reference_object_id = object_name_id[reference_object_name]
                key = ",".join([row_dict[x] for x in reference_fields_names])
                d2[key] = (reference_object_id, reference_object_name)
    # Create list of relationships
    relationships = list()
    for resource in datapackage.resources:
        primary_key = resource.schema.primary_key
        foreign_keys = resource.schema.foreign_keys
        reference_resource_names = [fk['reference']['resource'] for fk in foreign_keys]
        if not reference_resource_names:
            continue
        object_class_name_list = [resource.name] + reference_resource_names
        relationship_class_name = "__".join(object_class_name_list)
        relationship_class_id = relationship_class_name_id[relationship_class_name]
        for i, row in enumerate(resource.read(cast=False)):
            row_dict = dict(zip(resource.schema.field_names, row))
            if primary_key:
                object_name = "_".join(row_dict[field] for field in primary_key)
            else:
                object_name = resource.name + str(i)
            object_id = object_name_id[object_name]
            object_id_list = [object_id]
            object_name_list = [object_name]
            for fk in foreign_keys:
                fields_names = fk['fields']
                reference_resource_name = fk['reference']['resource']
                reference_fields_names = fk['reference']['fields']
                key = ",".join([row_dict[x] for x in fields_names])
                d1 = reference_object_id_dict[reference_resource_name]
                d2 = d1[",".join(reference_fields_names)]
                reference_object_id, reference_object_name = d2[key]
                object_id_list.append(reference_object_id)
                object_name_list.append(reference_object_name)
            relationship_name = relationship_class_name + "_" + "__".join(object_name_list)
            relationships.append(dict(
                class_id=relationship_class_id,
                object_id_list=object_id_list,
                name=relationship_name
            ))
    db_map.add_wide_relationships(*relationships)
