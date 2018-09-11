#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Functions to import/export between spine database and frictionless data's datapackage.

:author: M. Marin (KTH)
:date:   28.8.2018
"""

from PySide2.QtCore import Qt
from datapackage import Package
from spinedatabase_api import SpineDBAPIError
from helpers import busy_effect
import logging

@busy_effect
def import_datapackage(data_store_form, datapackage_path):
    """Import datapackage from `datapackage_path` into `data_store_form`."""
    data_store_form.msg.emit("Importing datapackage... ")
    mapping = data_store_form.mapping
    object_class_name_list = [x.name for x in mapping.object_class_list()]
    datapackage = Package(datapackage_path)
    for resource in datapackage.resources:
        if resource.name not in object_class_name_list:
            logging.debug("Ignoring resource '{}'.".format(resource.name))
            continue
        logging.debug("Importing resource '{}'.".format(resource.name))
        object_class_name = resource.name
        object_class = mapping.single_object_class(name=object_class_name).one_or_none()
        if not object_class:
            continue
        object_class_id = object_class.id
        primary_key = resource.schema.primary_key
        foreign_keys = resource.schema.foreign_keys
        for field in resource.schema.fields:
            logging.debug("Checking field '{}'.".format(field.name))
            # Skip fields in primary key
            if field.name in primary_key:
                continue
            # Find field in foreign keys, and prepare list of child object classes
            child_object_class_name_list = list()
            for foreign_key in foreign_keys:
                if field.name in foreign_key['fields']:
                    child_object_class_name = foreign_key['reference']['resource']
                    if child_object_class_name not in object_class_name_list:
                        continue
                    child_object_class_name_list.append(child_object_class_name)
            # If field is not in any foreign keys, use it to create a parameter
            if not child_object_class_name_list:
                try:
                    parameter = mapping.add_parameter(object_class_id=object_class_id, name=field.name)
                except SpineDBAPIError as e:
                    logging.debug(e.msg)
                continue
            # Create relationship classes
            for child_object_class_name in child_object_class_name_list:
                child_object_class = mapping.single_object_class(name=child_object_class_name).\
                    one_or_none()
                if not child_object_class:
                    continue
                relationship_class_name = object_class_name + "_" + child_object_class.name
                try:
                    wide_relationship_class = mapping.add_wide_relationship_class(
                        object_class_id_list=[object_class_id, child_object_class.id],
                        name=relationship_class_name
                    )
                    data_store_form.object_tree_model.add_relationship_class(wide_relationship_class._asdict())
                except SpineDBAPIError as e:
                    logging.debug(e.msg)
        # Iterate over resource rows to create objects and parameter values
        for i, row in enumerate(resource.read(cast=False)):  # TODO: try and get field keys from read method too
            row_dict = dict(zip(resource.schema.field_names, row))
            # Create object
            if primary_key:
                object_name = "_".join(row_dict[field] for field in primary_key)
            else:
                object_name = object_class_name + str(i)
            try:
                object_ = mapping.add_object(class_id=object_class_id, name=object_name)
                data_store_form.object_tree_model.add_object(object_.__dict__)
            except SpineDBAPIError as e:
                logging.debug(e.msg)
                continue
            # Create parameters
            object_id = object_.id
            for field_name, value in row_dict.items():
                if field_name in primary_key:
                    continue
                if field_name in [x for a in foreign_keys for x in a["fields"]]:  # TODO: compute this outside the loop
                    continue
                parameter = mapping.single_parameter(name=field_name).one_or_none()
                if not parameter:
                    continue
                try:
                    parameter_value = mapping.add_parameter_value(
                        object_id=object_id,
                        parameter_id=parameter.id,
                        value=value
                    )
                except SpineDBAPIError as e:
                    logging.debug(e.msg)


        # TODO: Import relationships from foreign keys
        # Iterate over resources (again) to create relationships
        #for resource in self.datapackage.resources:
        #    parent_object_class_name = resource.name
        #    if parent_object_class_name not in self.object_class_name_list:
        #        continue
        #    relationship_class_id_dict = dict()
        #    child_object_class_id_dict = dict()
        #    for field in resource.schema.fields:
        #        # A field whose named starts with the object_class is an index and should be skipped
        #        if field.name.startswith(parent_object_class_name):
        #            continue
        #        # Fields whose name ends with an object class name are foreign keys
        #        # and used to create relationships
        #        child_object_class_name = None
        #        for x in self.object_class_name_list:
        #            if field.name.endswith(x):
        #                child_object_class_name = x
        #                break
        #        if child_object_class_name:
        #            relationship_class_name = resource.name + "_" + field.name
        #            relationship_class_id_dict[field.name] = self.session.query(self.RelationshipClass.id).\
        #                filter_by(name=relationship_class_name).one().id
        #            child_object_class_id_dict[field.name] = self.session.query(self.ObjectClass.id).\
        #                filter_by(name=child_object_class_name).one().id
        #    for i, row in enumerate(self.resource_tables[resource.name][1:]):
        #        row_dict = dict(zip(resource.schema.field_names, row))
        #        if parent_object_class_name in row_dict:
        #            parent_object_name = row_dict[parent_object_class_name]
        #        else:
        #            parent_object_name = parent_object_class_name + str(i)
        #        parent_object_id = self.session.query(self.Object.id).\
        #            filter_by(name=parent_object_name).one().id
        #        for field_name, value in row_dict.items():
        #            if field_name in relationship_class_id_dict:
        #                relationship_class_id = relationship_class_id_dict[field_name]
        #                child_object_name = None
        #                child_object_ref = value
        #                child_object_class_id = child_object_class_id_dict[field_name]
        #                child_object_class_name = self.session.query(self.ObjectClass.name).\
        #                    filter_by(id=child_object_class_id).one().name
        #                child_resource = self.datapackage.get_resource(child_object_class_name)
        #                # Collect index and primary key columns in child resource
        #                indices = list()
        #                primary_key = None
        #                for j, field in enumerate(child_resource.schema.fields):
        #                    # A field whose named starts with the object_class is an index
        #                    if field.name.startswith(child_object_class_name):
        #                        indices.append(j)
        #                        # A field named exactly as the object_class is the primary key
        #                        if field.name == child_object_class_name:
        #                            primary_key = j
        #                # Look up the child object ref. in the child resource table
        #                for k, row in enumerate(self.resource_tables[child_resource.name][1:]):
        #                    if child_object_ref in [row[j] for j in indices]:
        #                        # Found reference in index values
        #                        if primary_key is not None:
        #                            child_object_name = row[primary_key]
        #                        else:
        #                            child_object_name = child_object_class_name + str(k)
        #                        break
        #                if child_object_name is None:
        #                    msg = "Couldn't find object ref {} to create relationship for field {}".\
        #                        format(child_object_ref, field_name)
        #                    self.ui.statusbar.showMessage(msg, 5000)
        #                    continue
        #                child_object_id = self.session.query(self.Object.id).\
        #                    filter_by(name=child_object_name, class_id=child_object_class_id).one().id
        #                relationship_name = parent_object_name + field_name + child_object_name
        #                relationship = self.Relationship(
        #                    commit_id=1,
        #                    class_id=relationship_class_id,
        #                    parent_object_id=parent_object_id,
        #                    child_object_id=child_object_id,
        #                    name=relationship_name
        #                )
        #                try:
        #                    self.session.add(relationship)
        #                    self.session.flush()
        #                    object_id = object_.id
        #                except DBAPIError as e:
        #                    msg = "Failed to insert relationship {0} for object {1} of class {2}: {3}".\
        #                        format(field_name, parent_object_name, parent_object_class_name, e.orig.args)
        #                    self.ui.statusbar.showMessage(msg, 5000)
        #                    self.session.rollback()
        #                    return False
