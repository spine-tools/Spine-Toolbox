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
Mixins for parameter definition models

:authors: M. Marin (KTH)
:date:   4.10.2019
"""
from PySide2.QtCore import Qt, QModelIndex


class ParameterAutocompleteMixin:
    """Provides basic autocomplete methods for all parameter models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def item_at_row(self, row):
        """Returns the item associated with the given row number.

        Args:
            row (int)
        """
        return self._main_data[row]

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.
        Reimplement in subclasses to automatically set additional data
        from the current data in the items (e.g., id from names, class from entity).

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """

    @staticmethod
    def _attr_set(items, attr, func=lambda a: {a}):
        """Returns a dictionary mapping databases to a set of attribute values from the given items.

        Args:
            items: an iterable of items to process
            attr (str): the attribute to collect for each item
            func: a function that returns an iterable from the attribute value, in case we want to decouple it
        """
        d = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            value = item.__getattribute__(attr)
            if value:
                d.setdefault(database, set()).update(func(value))
        return d

    def _attr_dict(self, attr_set, subqry_name, map_func, filter_func):
        """Takes a dictionary mapping databases to a set of attribute values,
        and returns another dictionary mapping the same databases to
        a custom dictionary for those values.

        Args:
            attr_set: a dict mapping databases to a set of attribute values, e.g., as returned by _attr_set(...)
            subqry_name (str): a DiffDatabaseMapping subquery attribute
            map_func: a function to produce pairs for each query result
            filter_func: a function to produce a filter for the subquery from the attribute value set
        """
        d = dict()
        for database, attrs in attr_set.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            subqry = db_map.__getattribute__(subqry_name)
            d[database] = dict([map_func(x) for x in db_map.query(subqry).filter(filter_func(subqry, attrs))])
        return d

    def _attr_dict_v2(self, attr_set, subqry_name, map_func, filter_func):
        """Takes a dictionary mapping databases to a set of attribute values,
        and returns another dictionary mapping the same databases to
        a custom dictionary for those values.

        Args:
            attr_set: a dict mapping databases to an attribute set, as returned by _attr_set(...)
            subqry_name (str): a DiffDatabaseMapping subquery attribute
            map_func: a function to produce pairs for each query result
            filter_func: a function to produce a filter for the subquery from the attribute set
        """
        d = dict()
        for database, attrs in attr_set.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            subqry = db_map.__getattribute__(subqry_name)
            d[database] = {
                attr: dict([map_func(x) for x in db_map.query(subqry).filter(filter_func(subqry, attr))])
                for attr in attrs
            }
        return d


class ParameterDefinitionAutocompleteMixin:
    """Provides autocomplete methods for parameter definition models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def batch_set_tag_id_lists(self, rows):
        """Sets parameter tag id lists in accordance with name lists.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        parameter_tags = self._attr_set(rows.values(), "parameter_tag_list", func=lambda a: a.split(","))
        map_func = lambda x: (x.tag, x.id)
        filter_func = lambda sq, tags: sq.c.tag.in_(tags)
        parameter_tag_dict = self._attr_dict(parameter_tags, "parameter_tag_sq", map_func, filter_func)
        for item in rows.values():
            db_parameter_tag_dict = parameter_tag_dict.get(item.database)
            if db_parameter_tag_dict and item.parameter_tag_list:
                tags = item.parameter_tag_list.split(",")
                tag_ids = [db_parameter_tag_dict.get(tag) for tag in tags]
                if None in tag_ids:
                    item.parameter_tag_id_list = None
                else:
                    item.parameter_tag_id_list = ",".join([str(id_) for id_ in tag_ids])

    def batch_set_value_list_ids(self, rows):
        """Sets value list ids in accordance with the names.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        value_list_names = self._attr_set(rows.values(), "value_list_name")
        map_func = lambda x: (x.name, x.id)
        filter_func = lambda sq, names: sq.c.name.in_(names)
        value_list_dict = self._attr_dict(value_list_names, "wide_parameter_value_list_sq", map_func, filter_func)
        for item in rows.values():
            db_value_list_dict = value_list_dict.get(item.database)
            if db_value_list_dict:
                item.value_list_id = db_value_list_dict.get(item.value_list_name)

    def set_parameter_definition_tags_in_db(self, rows):
        """Set parameter definition tags in the db.

        Args:
            rows (dict): A dict mapping row numbers to items whose tags should be set
        """
        tag_specs_dict = dict()
        for item in rows.values():
            tag_spec = item.tag_spec()
            if tag_spec:
                tag_specs_dict.setdefault(db_map, dict()).update(tag_spec)
        for db_map, tag_specs in tag_specs_dict.items():
            _, error_log = db_map.set_parameter_definition_tags(tag_specs)
            self.error_log.extend(error_log)


class ParameterValueAutocompleteMixin:
    """Provides autocomplete methods for parameter value models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def batch_set_possible_parameter_ids(self, rows):
        """Sets possible parameter definition ids in accordance with the names.

        Args:
            rows (list): A list of items that need treatment
        """
        parameter_names = self._attr_set(rows.values(), "parameter_name")
        map_func = lambda x: (x.object_class_id or x.relationship_class_id, x.id)
        filter_func = lambda sq, name: sq.c.name == name
        parameter_dict = self._attr_dict_v2(parameter_names, "parameter_definition_sq", map_func, filter_func)
        for item in rows.values():
            db_parameter_dict = parameter_dict.get(item.database)
            if db_parameter_dict:
                item._parameter_dict = db_parameter_dict.get(item.parameter_name, {})


class ObjectParameterAutocompleteMixin:
    """Provides autocomplete methods for object parameter models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def batch_set_object_class_ids(self, rows):
        """Sets object class ids in accordance with the object class names.

        Args:
            rows (list): A list of items that need treatment
        """
        object_class_names = self._attr_set(rows.values(), "object_class_name")
        map_func = lambda x: (x.name, x.id)
        filter_func = lambda sq, names: sq.c.name.in_(names)
        object_class_dict = self._attr_dict(object_class_names, "object_class_sq", map_func, filter_func)
        for item in rows.values():
            db_object_class_dict = object_class_dict.get(item.database)
            if db_object_class_dict:
                item.object_class_id = db_object_class_dict.get(item.object_class_name)


class RelationshipParameterAutocompleteMixin:
    """Provides autocomplete methods for relationship parameter models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def batch_set_relationship_class_ids(self, rows):
        """Sets relationship class ids in accordance with the relationship class names.

        Args:
            rows (list): A list of items that need treatment
        """
        relationship_class_names = self._attr_set(rows.values(), "relationship_class_name")
        map_func = lambda x: (x.name, x)
        filter_func = lambda sq, names: sq.c.name.in_(names)
        relationship_class_dict = self._attr_dict(
            relationship_class_names, "wide_relationship_class_sq", map_func, filter_func
        )
        for item in rows.values():
            db_relationship_class_dict = relationship_class_dict.get(item.database)
            if db_relationship_class_dict:
                relationship_class = db_relationship_class_dict.get(item.relationship_class_name)
                if not relationship_class:
                    item.relationship_class_id = None
                    item.object_class_id_list = None
                    item.object_class_name_list = None
                else:
                    item.relationship_class_id = relationship_class.id
                    item.object_class_id_list = relationship_class.object_class_id_list
                    item.object_class_name_list = relationship_class.object_class_name_list
        # TODO: emit dataChanged after changing `object_class_name_list`


class ObjectParameterDecorateMixin:
    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role."""
        if role == Qt.DecorationRole and self.header[index.column()] == "object_class_name":
            object_class_name = self.item_at_row(index.row()).object_class_name
            return self._parent._parent.icon_mngr.object_icon(object_class_name)
        return super().data(index, role)


class RelationshipParameterDecorateMixin:
    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role."""
        if role == Qt.DecorationRole and self.header[index.column()] == "relationship_class_name":
            object_class_name_list = self.item_at_row(index.row()).object_class_name_list
            return self._parent._parent.icon_mngr.relationship_icon(object_class_name_list)
        return super().data(index, role)


class SingleObjectParameterMixin:
    """An object parameter mixin for a single object class."""

    def __init__(self, parent, database, object_class_id):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent model
            database (str): the database where the object class associated with this model lives.
            object_class_id (int): the id of the object class
        """
        super().__init__(parent, database)
        self.object_class_id = object_class_id
        self.json_fields = ["value"]

    def selected_param_def_ids(self):
        return self._grand_parent.selected_obj_parameter_definition_ids.get((self.db_map, self.object_class_id), set())

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model or zero if the
        object class is not selected in the grand parent."""
        selected_object_class_ids = self._grand_parent.all_selected_object_class_ids
        if selected_object_class_ids and self.object_class_id not in selected_object_class_ids.get(self.db_map, set()):
            return 0
        return super().rowCount(parent)


class SingleRelationshipParameterMixin:
    """A relationship parameter mixin for a single relationship class."""

    def __init__(self, parent, database, relationship_class_id, object_class_id_list):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent model
            database (str): the database where the relationship class associated with this model lives.
            relationship_class_id (int): the id of the relationship class
            object_class_id_list (str): comma separated string of member object class ids
        """
        super().__init__(parent, database)
        self.relationship_class_id = relationship_class_id
        self.object_class_id_list = [int(id_) for id_ in object_class_id_list.split(",")]
        self.json_fields = ["default_value"]

    def selected_param_def_ids(self):
        return self._grand_parent.selected_rel_parameter_definition_ids.get(
            (self.db_map, self.relationship_class_id), set()
        )

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows in the model or zero if nor the
        relationship class nor any of its object classes is selected in the grand parent."""
        selected_object_class_ids = self._grand_parent.selected_object_class_ids
        selected_relationship_class_ids = self._grand_parent.all_selected_relationship_class_ids
        if selected_object_class_ids:
            if not selected_object_class_ids.get(self.db_map, set()).intersection(self.object_class_id_list):
                return 0
        if selected_relationship_class_ids:
            if self.relationship_class_id not in selected_relationship_class_ids.get(self.db_map, set()):
                return 0
        return super().rowCount(parent)
