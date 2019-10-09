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
Mixins for autocompleting data in parameter models

:authors: M. Marin (KTH)
:date:   4.10.2019
"""


class ParameterAutocompleteMixin:
    """Provides basic autocomplete methods for all parameter models."""

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        If succesful, autocomplete data
        """
        if super().batch_set_data(indexes, data):
            rows = {ind.row(): self._main_data[ind.row()] for ind in indexes}
            self.batch_autocomplete_data(rows)
            return True
        return False

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


class ParameterDefinitionAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for parameter definition models."""

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_tag_id_lists(rows)
        self.batch_set_value_list_ids(rows)

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


class ParameterValueAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for parameter value models."""

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_possible_parameter_ids(rows)

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


class ObjectParameterAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for object parameter models."""

    def batch_autocomplete_data(self, rows):
        """Sets more data for model items in batch.

        Args:
            rows (list): A list of items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_object_class_ids(rows)

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


class RelationshipParameterAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for relationship parameter models."""

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_relationship_class_ids(rows)

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


class ObjectParameterValueAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for object parameter value models."""

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_possible_object_ids(rows)
        self.batch_consolidate_data(rows)

    def batch_set_possible_object_ids(self, rows):
        """Set possible object ids in accordance with names."""
        object_names = self._attr_set(rows.values(), "object_name")
        map_func = lambda x: (x.class_id, x.id)
        filter_func = lambda sq, name: sq.c.name == name
        object_dict = self._attr_dict_v2(object_names, "object_sq", map_func, filter_func)
        for item in rows.values():
            db_object_dict = object_dict.get(item.database)
            if db_object_dict:
                item._object_dict = db_object_dict.get(item.object_name, {})

    def batch_consolidate_data(self, rows):
        """If object class id is not set, then try and figure it out from possible ones.
        Then pick the right object_id and parameter_id according to object class id.
        """
        object_class_ids = dict()
        for item in rows.values():
            database = item.database
            if not database:
                continue
            if item.object_class_id is None:
                # Try and see if we can figure out the object class id
                if item._object_dict and item._parameter_dict:
                    object_class_id = item._object_dict.keys() & item._parameter_dict.keys()
                elif item._object_dict:
                    object_class_id = set(item._object_dict.keys())
                elif item._parameter_dict:
                    object_class_id = set(item._parameter_dict.keys())
                else:
                    object_class_id = {}
                if len(object_class_id) != 1:
                    continue
                item.object_class_id = object_class_id.pop()
                item.object_class_name = True  # Mark the item somehow
                object_class_ids.setdefault(database, set()).add(item.object_class_id)
            # Pick the right object_id and parameter_id
            item.object_id = item._object_dict.get(item.object_class_id)
            item.parameter_id = item._parameter_dict.get(item.object_class_id)
        map_func = lambda x: (x.id, x.name)
        filter_func = lambda sq, ids: sq.c.id.in_(ids)
        object_class_dict = self._attr_dict(object_class_ids, "object_class_sq", map_func, filter_func)
        for item in rows.values():
            db_object_class_dict = object_class_dict.get(item.database)
            if db_object_class_dict and item.object_class_name is True:
                item.object_class_name = db_object_class_dict.get(item.object_class_id)
        # TODO: emit dataChanged after changing `object_class_name`


class RelationshipParameterValueAutocompleteMixin(ParameterAutocompleteMixin):
    """Provides autocomplete methods for relationship parameter value models."""

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_possible_relationship_ids(rows)
        self.batch_consolidate_data(rows)
        self.batch_set_object_id_lists(rows)

    def batch_set_possible_relationship_ids(self, rows):
        """Set possible relationship ids in accordance with names."""
        object_name_lists = self._attr_set(rows.values(), "object_name_list")
        map_func = lambda x: (x.class_id, x)
        filter_func = lambda sq, name_list: sq.c.object_name_list == name_list
        relationship_dict = self._attr_dict_v2(object_name_lists, "wide_relationship_sq", map_func, filter_func)
        for item in rows.values():
            db_relationship_dict = relationship_dict.get(item.database)
            if db_relationship_dict:
                item._relationship_dict = db_relationship_dict.get(item.object_name_list, {})

    def batch_consolidate_data(self, rows):
        """If relationship class id is not set, then try and figure it out from possible ones.
        Then pick the right relationship_id and parameter_id according to relationship class id.
        """
        relationship_class_ids = dict()
        for item in rows.values():
            database = item.database
            if not database:
                continue
            if item.relationship_class_id is None:
                # Try and see if we can figure out the object class id
                if item._relationship_dict and item._parameter_dict:
                    relationship_class_id = item._relationship_dict.keys() & item._parameter_dict.keys()
                elif item._relationship_dict:
                    relationship_class_id = set(item._relationship_dict.keys())
                elif item._parameter_dict:
                    relationship_class_id = set(item._parameter_dict.keys())
                else:
                    relationship_class_id = {}
                if len(relationship_class_id) != 1:
                    continue
                item.relationship_class_id = relationship_class_id.pop()
                item.relationship_class_name = True  # Mark the item somehow
                relationship_class_ids.setdefault(database, set()).add(item.relationship_class_id)
            # Pick the right relationship_id and parameter_id
            relationship = item._relationship_dict.get(item.relationship_class_id)
            if relationship:
                item.relationship_id = relationship.id
                item.object_id_list = relationship.object_id_list
            item.parameter_id = item._parameter_dict.get(item.relationship_class_id)
        map_func = lambda x: (x.id, x)
        filter_func = lambda sq, ids: sq.c.id.in_(ids)
        relationship_class_dict = self._attr_dict(
            relationship_class_ids, "wide_relationship_class_sq", map_func, filter_func
        )
        # Update the items
        for item in rows.values():
            database = item.database
            db_relationship_class_dict = relationship_class_dict.get(database)
            if db_relationship_class_dict and item.relationship_class_name is True:
                relationship_class = db_relationship_class_dict.get(item.relationship_class_id)
                if relationship_class:
                    item.relationship_class_name = relationship_class.name
                    item.object_class_id_list = relationship_class.object_class_id_list
                    item.object_class_name_list = relationship_class.object_class_name_list
                else:
                    item.relationship_class_name = None
                    item.object_class_id_list = None
                    item.object_class_name_list = None
        # TODO: emit dataChanged after changing `relationship_class_name` and `object_class_name_list`

    def batch_set_object_id_lists(self, rows):
        """Set object_id_list if not set and possible.
        This is needed to add relationships 'on the fly'.
        """
        object_name_class_id_tuples = dict()
        for item in rows.values():
            database = item.database
            if not database:
                continue
            if not item.object_id_list and item.object_name_list and item.object_class_id_list:
                # object_id_list is not and can be figured out, so let's do it
                object_names = item.object_name_list.split(",")
                object_class_ids = [int(x) for x in item.object_class_id_list.split(",")]
                item._object_name_class_id_tups = set(zip(object_names, object_class_ids))
                object_name_class_id_tuples.setdefault(database, set()).update(item._object_name_class_id_tups)
            else:
                item._object_name_class_id_tups = None
        map_func = lambda x: ((x.name, x.class_id), x.id)
        filter_func = lambda sq, tups: or_(
            *(and_(sq.c.name == name, sq.c.class_id == class_id) for (name, class_id) in tups)
        )
        object_dict = self._attr_dict(object_name_class_id_tuples, "object_sq", map_func, filter_func)
        # Update the items
        for item in rows.values():
            database = item.database
            db_object_dict = object_dict.get(database)
            tups = item._object_name_class_id_tups
            if db_object_dict and tups:
                object_id_list = [db_object_dict.get((name, class_id)) for (name, class_id) in tups]
                if None in object_id_list:
                    item.object_id_list = None
                else:
                    item.object_id_list = ",".join([str(id_) for id_ in object_id_list])
