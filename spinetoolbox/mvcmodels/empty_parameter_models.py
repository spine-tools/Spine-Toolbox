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
Empty models for parameter definitions and values.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from helpers import busy_effect
from mvcmodels.empty_row_model import EmptyRowModel


class EmptyParameterModel(EmptyRowModel):
    """An empty parameter model. Implements `batch_set_data` for all `EmptyParameter` models."""

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (ObjectParameterModel or RelationshipParameterModel)
        """
        super().__init__(parent)
        self._parent = parent
        self.error_log = []
        self.added_rows = []

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        Set data in model first, then check if the database needs to be updated as well.
        Extend set of indexes as additional data is set (for emitting dataChanged at the end).
        """
        # TODO: emit dataChanged? Perhaps we need to call `super().batch_set_data` at the end
        self.error_log.clear()
        self.added_rows.clear()
        if not super().batch_set_data(indexes, data):
            return False
        items_to_add = self.items_to_add(indexes)
        self.add_items_to_db(items_to_add)
        return True

    def items_to_add(self, indexes):
        raise NotImplementedError()

    def add_items_to_db(self, items_to_add):
        raise NotImplementedError()


class EmptyParameterValueModel(EmptyParameterModel):
    """An empty parameter value model."""

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (ObjectParameterValueModel or RelationshipParameterValueModel)
        """
        super().__init__(parent)
        self._parent = parent

    def items_to_add(self, indexes):
        raise NotImplementedError()

    @busy_effect
    def add_items_to_db(self, items_to_add):
        """Add parameter values to database.

        Args:
            items_to_add (dict): maps DatabaseMapping instances to another dictionary
                mapping row numbers to parameter value items
        """
        for db_map, row_dict in items_to_add.items():
            rows, items = zip(*row_dict.items())
            parameter_values, error_log = db_map.add_parameter_values(*items)
            id_column = self._parent.horizontal_header_labels().index('id')
            for i, parameter_value in enumerate(parameter_values):
                self._main_data[rows[i]][id_column] = parameter_value.id
            self.error_log.extend(error_log)
            self.added_rows.extend(rows)


class EmptyParameterDefinitionModel(EmptyParameterModel):
    """An empty parameter definition model.
    """

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (ObjectParameterDefinitionModel or RelationshipParameterDefinitionModel)
        """
        super().__init__(parent)
        self._parent = parent

    def items_to_add(self, indexes):
        raise NotImplementedError()

    @busy_effect
    def add_items_to_db(self, items_to_add):
        """Add parameter definitions to database.
        """
        for db_map, row_dict in items_to_add.items():
            rows, items = zip(*row_dict.items())
            # Pop the `parameter_tag_id_list` from `row_dict` into a new dictionary
            row_tag_id_list_dict = {row: item.pop("parameter_tag_id_list", None) for row, item in zip(rows, items)}
            par_defs, error_log = db_map.add_parameter_definitions(*items)
            id_column = self._parent.horizontal_header_labels().index('id')
            # Now we have the parameter definition ids we can build the tag_id_list_dict
            tag_id_list_dict = {}
            for i, par_def in enumerate(par_defs):
                row = rows[i]
                tag_id_list = row_tag_id_list_dict[row]
                if tag_id_list:
                    tag_id_list_dict[par_def.id] = tag_id_list
                self._main_data[rows[i]][id_column] = par_def.id
            _, def_tag_error_log = db_map.set_parameter_definition_tags(tag_id_list_dict)
            self.error_log.extend(error_log + def_tag_error_log)
            self.added_rows.extend(rows)


class EmptyObjectParameterValueModel(EmptyParameterValueModel):
    """An empty object parameter value model.
    Implements `items_to_add`.
    """

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def items_to_add(self, indexes):
        """A dictionary of rows (int) to items (dict) to add to the db.
        Extend set of indexes as additional data is set."""
        items_to_add = dict()
        # Get column numbers
        header_index = self._parent.horizontal_header_labels().index
        db_column = header_index('database')
        object_class_id_column = header_index('object_class_id')
        object_class_name_column = header_index('object_class_name')
        object_id_column = header_index('object_id')
        object_name_column = header_index('object_name')
        parameter_id_column = header_index('parameter_id')
        parameter_name_column = header_index('parameter_name')
        value_column = header_index('value')
        # Lookup dicts (these are filled below as needed with data from the db corresponding to each row)
        object_class_dict = {}
        object_class_name_dict = {}
        object_dict = {}
        parameter_dict = {}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            db_name = self.index(row, db_column).data(Qt.DisplayRole)
            db_map = self._parent.db_name_to_map.get(db_name)
            if not db_map:
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            object_name = self.index(row, object_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            object_class_id = None
            object_ = None
            parameter = None
            if object_class_name:
                d = object_class_dict.setdefault(db_map, {x.name: x.id for x in db_map.object_class_list()})
                try:
                    object_class_id = d[object_class_name]
                    self._main_data[row][object_class_id_column] = object_class_id
                except KeyError:
                    self.error_log.append("Invalid object class '{}'".format(object_class_name))
            if object_name:
                d = object_dict.setdefault(
                    db_map, {x.name: {'id': x.id, 'class_id': x.class_id} for x in db_map.object_list()}
                )
                try:
                    object_ = d[object_name]
                    self._main_data[row][object_id_column] = object_['id']
                except KeyError:
                    self.error_log.append("Invalid object '{}'".format(object_name))
            if parameter_name:
                d = parameter_dict.setdefault(db_map, {})
                for x in db_map.object_parameter_definition_list():
                    d.setdefault(x.parameter_name, {}).update(
                        {x.object_class_id: {'id': x.id, 'object_class_id': x.object_class_id}}
                    )
                try:
                    dup_parameters = d[parameter_name]
                    if len(dup_parameters) == 1:
                        parameter = list(dup_parameters.values())[0]
                    elif object_class_id in dup_parameters:
                        parameter = dup_parameters[object_class_id]
                    if parameter is not None:
                        self._main_data[row][parameter_id_column] = parameter['id']
                except KeyError:
                    self.error_log.append("Invalid parameter '{}'".format(parameter_name))
            if object_class_id is None:
                d = object_class_name_dict.setdefault(db_map, {x.id: x.name for x in db_map.object_class_list()})
                if object_ is not None:
                    object_class_id = object_['class_id']
                    object_class_name = d[object_class_id]
                    self._main_data[row][object_class_id_column] = object_class_id
                    self._main_data[row][object_class_name_column] = object_class_name
                    indexes.append(self.index(row, object_class_name_column))
                elif parameter is not None:
                    object_class_id = parameter['object_class_id']
                    object_class_name = d[object_class_id]
                    self._main_data[row][object_class_id_column] = object_class_id
                    self._main_data[row][object_class_name_column] = object_class_name
                    indexes.append(self.index(row, object_class_name_column))
            if object_ is None or parameter is None:
                continue
            value = self.index(row, value_column).data(Qt.DisplayRole)
            item = {"object_id": object_['id'], "parameter_definition_id": parameter['id'], "value": value}
            items_to_add.setdefault(db_map, {})[row] = item
        return items_to_add


class EmptyRelationshipParameterValueModel(EmptyParameterValueModel):
    """An empty relationship parameter value model.
    Reimplements almost all methods from the super class EmptyParameterModel.
    """

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        A little different from the base class implementation,
        since here we need to support creating relationships on the fly.
        """
        self.error_log = []
        self.added_rows = []
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        for k, index in enumerate(indexes):
            self._main_data[index.row()][index.column()] = data[k]
        relationships_on_the_fly = self.relationships_on_the_fly(indexes)
        items_to_add = self.items_to_add(indexes, relationships_on_the_fly)
        self.add_items_to_db(items_to_add)
        # Find square envelope of indexes to emit dataChanged
        top = min(ind.row() for ind in indexes)
        bottom = max(ind.row() for ind in indexes)
        left = min(ind.column() for ind in indexes)
        right = max(ind.column() for ind in indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return True

    def relationships_on_the_fly(self, indexes):
        """A dict of row (int) to relationship item (KeyedTuple),
        which can be either retrieved or added on the fly.
        Extend set of indexes as additional data is set.
        """
        relationships_on_the_fly = dict()
        relationships_to_add = dict()
        # Get column numbers
        header_index = self._parent.horizontal_header_labels().index
        db_column = header_index('database')
        relationship_class_id_column = header_index('relationship_class_id')
        relationship_class_name_column = header_index('relationship_class_name')
        object_class_id_list_column = header_index('object_class_id_list')
        object_class_name_list_column = header_index('object_class_name_list')
        object_id_list_column = header_index('object_id_list')
        object_name_list_column = header_index('object_name_list')
        parameter_id_column = header_index('parameter_id')
        parameter_name_column = header_index('parameter_name')
        # Lookup dicts (these are filled below as needed with data from the db corresponding to each row)
        relationship_class_dict = {}
        relationship_class_name_dict = {}
        parameter_dict = {}
        relationship_dict = {}
        object_dict = {}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            db_name = self.index(row, db_column).data(Qt.DisplayRole)
            db_map = self._parent.db_name_to_map.get(db_name)
            if not db_map:
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            object_name_list = self.index(row, object_name_list_column).data(Qt.DisplayRole)
            relationship_class_id = None
            object_id_list = None
            parameter = None
            if relationship_class_name:
                d = relationship_class_dict.setdefault(
                    db_map,
                    {
                        x.name: {
                            "id": x.id,
                            "object_class_id_list": x.object_class_id_list,
                            "object_class_name_list": x.object_class_name_list,
                        }
                        for x in db_map.wide_relationship_class_list()
                    },
                )
                try:
                    relationship_class = d[relationship_class_name]
                    relationship_class_id = relationship_class['id']
                    object_class_id_list = relationship_class['object_class_id_list']
                    object_class_name_list = relationship_class['object_class_name_list']
                    self._main_data[row][relationship_class_id_column] = relationship_class_id
                    self._main_data[row][object_class_id_list_column] = object_class_id_list
                    self._main_data[row][object_class_name_list_column] = object_class_name_list
                    indexes.append(self.index(row, object_class_name_list_column))
                except KeyError:
                    self.error_log.append("Invalid relationship class '{}'".format(relationship_class_name))
            if object_name_list:
                d = object_dict.setdefault(db_map, {x.name: x.id for x in db_map.object_list()})
                try:
                    object_id_list = [d[x] for x in object_name_list.split(",")]
                    join_object_id_list = ",".join(str(x) for x in object_id_list)
                    self._main_data[row][object_id_list_column] = join_object_id_list
                except KeyError as e:
                    self.error_log.append("Invalid object '{}'".format(e))
            if parameter_name:
                d = parameter_dict.setdefault(db_map, {})
                for x in db_map.relationship_parameter_definition_list():
                    d.setdefault(x.parameter_name, {}).update(
                        {x.relationship_class_id: {'id': x.id, 'relationship_class_id': x.relationship_class_id}}
                    )
                try:
                    dup_parameters = d[parameter_name]
                    if len(dup_parameters) == 1:
                        parameter = list(dup_parameters.values())[0]
                    elif relationship_class_id in dup_parameters:
                        parameter = dup_parameters[relationship_class_id]
                    if parameter is not None:
                        self._main_data[row][parameter_id_column] = parameter['id']
                except KeyError:
                    self.error_log.append("Invalid parameter '{}'".format(parameter_name))
            if relationship_class_id is None and parameter is not None:
                relationship_class_id = parameter['relationship_class_id']
                d1 = relationship_class_name_dict.setdefault(
                    db_map, {x.id: x.name for x in db_map.wide_relationship_class_list()}
                )
                d2 = relationship_class_dict.setdefault(
                    db_map,
                    {
                        x.name: {
                            "id": x.id,
                            "object_class_id_list": x.object_class_id_list,
                            "object_class_name_list": x.object_class_name_list,
                        }
                        for x in db_map.wide_relationship_class_list()
                    },
                )
                relationship_class_name = d1[relationship_class_id]
                relationship_class = d2[relationship_class_name]
                object_class_id_list = relationship_class['object_class_id_list']
                object_class_name_list = relationship_class['object_class_name_list']
                self._main_data[row][relationship_class_id_column] = relationship_class_id
                self._main_data[row][relationship_class_name_column] = relationship_class_name
                self._main_data[row][object_class_id_list_column] = object_class_id_list
                self._main_data[row][object_class_name_list_column] = object_class_name_list
                indexes.append(self.index(row, relationship_class_name_column))
                indexes.append(self.index(row, object_class_name_list_column))
            if relationship_class_id is None or object_id_list is None:
                continue
            d = relationship_dict.setdefault(
                db_map, {(x.class_id, x.object_id_list): x.id for x in db_map.wide_relationship_list()}
            )
            try:
                relationship_id = d[relationship_class_id, join_object_id_list]
                relationships_on_the_fly[row] = relationship_id
            except KeyError:
                relationship_name = relationship_class_name + "_" + object_name_list.replace(",", "__")
                relationship = {
                    "name": relationship_name,
                    "object_id_list": object_id_list,
                    "class_id": relationship_class_id,
                }
                relationships_to_add.setdefault(db_map, {})[row] = relationship
        added_relationships = self.add_relationships(relationships_to_add)
        if added_relationships:
            relationships_on_the_fly.update(added_relationships)
        return relationships_on_the_fly

    def add_relationships(self, relationships_to_add):
        """Add relationships to database on the fly and return them."""
        added_relationships = {}
        for db_map, row_dict in relationships_to_add.items():
            items = list(row_dict.values())
            rows = list(row_dict.keys())
            added, error_log = db_map.add_wide_relationships(*items)
            self._parent._parent.object_tree_model.add_relationships(db_map, added)
            self._parent._parent.relationship_tree_model.add_relationships(db_map, added)
            added_ids = [x.id for x in added]
            self.error_log.extend(error_log)
            added_relationships.update(dict(zip(rows, added_ids)))
        return added_relationships

    def items_to_add(self, indexes, relationships_on_the_fly):
        """A dictionary of rows (int) to items (dict) to add to the db.
        Extend set of indexes as additional data is set."""
        items_to_add = dict()
        # Get column numbers
        header_index = self._parent.horizontal_header_labels().index
        db_column = header_index('database')
        relationship_id_column = header_index('relationship_id')
        parameter_id_column = header_index('parameter_id')
        value_column = header_index('value')
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            db_name = self.index(row, db_column).data(Qt.DisplayRole)
            db_map = self._parent.db_name_to_map.get(db_name)
            if not db_map:
                continue
            parameter_id = self.index(row, parameter_id_column).data(Qt.DisplayRole)
            if parameter_id is None:
                continue
            relationship_id = relationships_on_the_fly.get(row, None)
            if not relationship_id:
                continue
            self._main_data[row][relationship_id_column] = relationship_id
            value = self.index(row, value_column).data(Qt.DisplayRole)
            item = {"relationship_id": relationship_id, "parameter_definition_id": parameter_id, "value": value}
            items_to_add.setdefault(db_map, {})[row] = item
        return items_to_add


class EmptyObjectParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty object parameter definition model."""

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db."""
        items_to_add = dict()
        # Get column numbers
        header_index = self._parent.horizontal_header_labels().index
        db_column = header_index('database')
        object_class_id_column = header_index('object_class_id')
        object_class_name_column = header_index('object_class_name')
        parameter_name_column = header_index('parameter_name')
        parameter_tag_list_column = header_index('parameter_tag_list')
        parameter_tag_id_list_column = header_index('parameter_tag_id_list')
        value_list_id_column = header_index('value_list_id')
        value_list_name_column = header_index('value_list_name')
        default_value_column = header_index('default_value')
        # Lookup dicts (these are filled below as needed with data from the db corresponding to each row)
        object_class_dict = {}
        parameter_tag_dict = {}
        parameter_value_list_dict = {}
        for row in {ind.row() for ind in indexes}:
            db_name = self.index(row, db_column).data(Qt.DisplayRole)
            db_map = self._parent.db_name_to_map.get(db_name)
            if not db_map:
                continue
            object_class_name = self.index(row, object_class_name_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            parameter_tag_list = self.index(row, parameter_tag_list_column).data(Qt.DisplayRole)
            value_list_name = self.index(row, value_list_name_column).data(Qt.DisplayRole)
            object_class_id = None
            item = {"name": parameter_name}
            if object_class_name:
                d = object_class_dict.setdefault(db_map, {x.name: x.id for x in db_map.object_class_list()})
                try:
                    object_class_id = d[object_class_name]
                    self._main_data[row][object_class_id_column] = object_class_id
                    item["object_class_id"] = object_class_id
                except KeyError:
                    self.error_log.append("Invalid object class '{}'".format(object_class_name))
            if parameter_tag_list:
                d = parameter_tag_dict.setdefault(db_map, {x.tag: x.id for x in db_map.parameter_tag_list()})
                split_parameter_tag_list = parameter_tag_list.split(",")
                try:
                    parameter_tag_id_list = ",".join(str(d[x]) for x in split_parameter_tag_list)
                    self._main_data[row][parameter_tag_id_list_column] = parameter_tag_id_list
                    item["parameter_tag_id_list"] = parameter_tag_id_list
                except KeyError as e:
                    self.error_log.append("Invalid parameter tag '{}'".format(e))
            if value_list_name:
                d = parameter_value_list_dict.setdefault(
                    db_map, {x.name: x.id for x in db_map.wide_parameter_value_list_list()}
                )
                try:
                    value_list_id = d[value_list_name]
                    self._main_data[row][value_list_id_column] = value_list_id
                    item["parameter_value_list_id"] = value_list_id
                except KeyError:
                    self.error_log.append("Invalid value list '{}'".format(value_list_name))
            if not parameter_name or not object_class_id:
                continue
            default_value = self.index(row, default_value_column).data(Qt.DisplayRole)
            item["default_value"] = default_value
            items_to_add.setdefault(db_map, {})[row] = item
        return items_to_add


class EmptyRelationshipParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty relationship parameter definition model."""

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def items_to_add(self, indexes):
        """Return a dictionary of rows (int) to items (dict) to add to the db.
        Extend set of indexes as additional data is set."""
        items_to_add = dict()
        # Get column numbers
        header_index = self._parent.horizontal_header_labels().index
        db_column = header_index('database')
        relationship_class_id_column = header_index('relationship_class_id')
        relationship_class_name_column = header_index('relationship_class_name')
        object_class_id_list_column = header_index('object_class_id_list')
        object_class_name_list_column = header_index('object_class_name_list')
        parameter_name_column = header_index('parameter_name')
        parameter_tag_list_column = header_index('parameter_tag_list')
        parameter_tag_id_list_column = header_index('parameter_tag_id_list')
        value_list_id_column = header_index('value_list_id')
        value_list_name_column = header_index('value_list_name')
        default_value_column = header_index('default_value')
        # Lookup dicts (these are filled below as needed with data from the db corresponding to each row)
        relationship_class_dict = {}
        parameter_tag_dict = {}
        parameter_value_list_dict = {}
        unique_rows = {ind.row() for ind in indexes}
        for row in unique_rows:
            db_name = self.index(row, db_column).data(Qt.DisplayRole)
            db_map = self._parent.db_name_to_map.get(db_name)
            if not db_map:
                continue
            relationship_class_name = self.index(row, relationship_class_name_column).data(Qt.DisplayRole)
            object_class_name_list = self.index(row, object_class_name_list_column).data(Qt.DisplayRole)
            parameter_name = self.index(row, parameter_name_column).data(Qt.DisplayRole)
            parameter_tag_list = self.index(row, parameter_tag_list_column).data(Qt.DisplayRole)
            value_list_name = self.index(row, value_list_name_column).data(Qt.DisplayRole)
            relationship_class_id = None
            item = {"name": parameter_name}
            if relationship_class_name:
                d = relationship_class_dict.setdefault(
                    db_map,
                    {
                        x.name: {
                            'id': x.id,
                            'object_class_id_list': x.object_class_id_list,
                            'object_class_name_list': x.object_class_name_list,
                        }
                        for x in db_map.wide_relationship_class_list()
                    },
                )
                try:
                    relationship_class = d[relationship_class_name]
                    relationship_class_id = relationship_class['id']
                    object_class_id_list = relationship_class['object_class_id_list']
                    object_class_name_list = relationship_class['object_class_name_list']
                    self._main_data[row][relationship_class_id_column] = relationship_class_id
                    self._main_data[row][object_class_id_list_column] = object_class_id_list
                    self._main_data[row][object_class_name_list_column] = object_class_name_list
                    indexes.append(self.index(row, object_class_name_list_column))
                    item["relationship_class_id"] = relationship_class_id
                except KeyError:
                    self.error_log.append("Invalid relationship class '{}'".format(relationship_class_name))
            if parameter_tag_list:
                d = parameter_tag_dict.setdefault(db_map, {x.tag: x.id for x in db_map.parameter_tag_list()})
                split_parameter_tag_list = parameter_tag_list.split(",")
                try:
                    parameter_tag_id_list = ",".join(str(d[x]) for x in split_parameter_tag_list)
                    self._main_data[row][parameter_tag_id_list_column] = parameter_tag_id_list
                    item["parameter_tag_id_list"] = parameter_tag_id_list
                except KeyError as e:
                    self.error_log.append("Invalid tag '{}'".format(e))
            if value_list_name:
                d = parameter_value_list_dict.setdefault(
                    db_map, {x.name: x.id for x in db_map.wide_parameter_value_list_list()}
                )
                try:
                    value_list_id = d[value_list_name]
                    self._main_data[row][value_list_id_column] = value_list_id
                    item["parameter_value_list_id"] = value_list_id
                except KeyError:
                    self.error_log.append("Invalid value list '{}'".format(value_list_name))
            if not parameter_name or not relationship_class_id:
                continue
            default_value = self.index(row, default_value_column).data(Qt.DisplayRole)
            item["default_value"] = default_value
            items_to_add.setdefault(db_map, {})[row] = item
        return items_to_add
