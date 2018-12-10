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
        for field in resource.schema.fields:
            # Skip fields in primary key
            if field.name in primary_key:
                continue
            found_in_foreing_key = False
            for foreign_key in foreign_keys:
                if field.name in foreign_key['fields']:
                    found_in_foreing_key = True
                    reference_resource_name = foreign_key['reference']['resource']
                    object_class_name_list = [resource.name, reference_resource_name]
                    if object_class_name_list in object_class_name_lists:
                        continue
                    if reference_resource_name not in object_class_names:
                        object_classes.append(dict(name=reference_resource_name))
                        object_class_names.append(reference_resource_name)
                    relationship_class_name = resource.name + "__" + reference_resource_name
                    pre_relationship_classes.append(
                        object_class_name_list=object_class_name_list,
                        name=relationship_class_name
                    )
                    object_class_name_lists.append(object_class_name_list)
            # If field is not in any foreign keys, use it to create a parameter
            if not found_in_foreing_key and field.name not in parameter_names:
                pre_parameters.append(dict(object_class_name=resource.name, name=field.name))
                parameter_names.append(field.name)
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
    parameter_name_id = {x.name: x.id for x in db_map.parameter_list()}
    object_names = [x.name for x in db_map.object_list()]
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
                parameter_id = parameter_name_id[field_name]
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
    pre_relationships = list()
    return
    # TODO
    for resource in datapackage.resources:
        object_class_id = object_class_name_id[resource.name]
        primary_key = resource.schema.primary_key
        foreign_keys = resource.schema.foreign_keys
        foreign_keys_fields = [x for fk in foreign_keys for x in fk["fields"]]
        for resource in datapackage.resources:
            object_class_name = resource.name
            relationship_class_id_dict = dict()
            child_object_class_id_dict = dict()
            for field in resource.schema.fields:
                # A field whose named starts with the object_class is an index and should be skipped
                if field.name.startswith(parent_object_class_name):
                    continue
                # Fields whose name ends with an object class name are foreign keys
                # and used to create relationships
                child_object_class_name = None
                for x in self.object_class_names:
                    if field.name.endswith(x):
                        child_object_class_name = x
                        break
                if child_object_class_name:
                    relationship_class_name = resource.name + "_" + field.name
                    relationship_class_id_dict[field.name] = self.session.query(self.RelationshipClass.id).\
                        filter_by(name=relationship_class_name).one().id
                    child_object_class_id_dict[field.name] = self.session.query(self.ObjectClass.id).\
                        filter_by(name=child_object_class_name).one().id
            for i, row in enumerate(self.resource_tables[resource.name][1:]):
                row_dict = dict(zip(resource.schema.field_names, row))
                if parent_object_class_name in row_dict:
                    parent_object_name = row_dict[parent_object_class_name]
                else:
                    parent_object_name = parent_object_class_name + str(i)
                parent_object_id = self.session.query(self.Object.id).\
                    filter_by(name=parent_object_name).one().id
                for field_name, value in row_dict.items():
                    if field_name in relationship_class_id_dict:
                        relationship_class_id = relationship_class_id_dict[field_name]
                        child_object_name = None
                        child_object_ref = value
                        child_object_class_id = child_object_class_id_dict[field_name]
                        child_object_class_name = self.session.query(self.ObjectClass.name).\
                            filter_by(id=child_object_class_id).one().name
                        child_resource = self.datapackage.get_resource(child_object_class_name)
                        # Collect index and primary key columns in child resource
                        indices = list()
                        primary_key = None
                        for j, field in enumerate(child_resource.schema.fields):
                            # A field whose named starts with the object_class is an index
                            if field.name.startswith(child_object_class_name):
                                indices.append(j)
                                # A field named exactly as the object_class is the primary key
                                if field.name == child_object_class_name:
                                    primary_key = j
                        # Look up the child object ref. in the child resource table
                        for k, row in enumerate(self.resource_tables[child_resource.name][1:]):
                            if child_object_ref in [row[j] for j in indices]:
                                # Found reference in index values
                                if primary_key is not None:
                                    child_object_name = row[primary_key]
                                else:
                                    child_object_name = child_object_class_name + str(k)
                                break
                        if child_object_name is None:
                            msg = "Couldn't find object ref {} to create relationship for field {}".\
                                format(child_object_ref, field_name)
                            self.ui.statusbar.showMessage(msg, 5000)
                            continue
                        child_object_id = self.session.query(self.Object.id).\
                            filter_by(name=child_object_name, class_id=child_object_class_id).one().id
                        relationship_name = parent_object_name + field_name + child_object_name
                        relationship = self.Relationship(
                            commit_id=1,
                            class_id=relationship_class_id,
                            parent_object_id=parent_object_id,
                            child_object_id=child_object_id,
                            name=relationship_name
                        )
                        try:
                            self.session.add(relationship)
                            self.session.flush()
                            object_id = object_.id
                        except DBAPIError as e:
                            msg = "Failed to insert relationship {0} for object {1} of class {2}: {3}".\
                                format(field_name, parent_object_name, parent_object_class_name, e.orig.args)
                            self.ui.statusbar.showMessage(msg, 5000)
                            self.session.rollback()
                            return False
