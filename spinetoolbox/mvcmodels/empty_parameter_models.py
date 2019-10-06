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

from sqlalchemy.sql import and_, or_
from PySide2.QtCore import Qt, QModelIndex
from mvcmodels.empty_row_model import EmptyRowModel
from mvcmodels.parameter_mixins import (
    ParameterAutocompleteMixin,
    ParameterDefinitionAutocompleteMixin,
    ParameterValueAutocompleteMixin,
    ObjectParameterAutocompleteMixin,
    RelationshipParameterAutocompleteMixin,
    ObjectParameterDecorateMixin,
    RelationshipParameterDecorateMixin,
)
from mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class EmptyParameterModel(ParameterAutocompleteMixin, EmptyRowModel):
    """An empty parameter model."""

    def __init__(self, parent):
        """Initialize class.

        Args:
            parent (ParameterModel): the parent object
        """
        super().__init__(parent)
        self.header = parent.header
        self.db_name_to_map = parent.db_name_to_map
        self.error_log = []
        self.added_rows = []

    def create_item(self):
        """Returns an item to put in the model rows.
        Reimplement in subclasses to return something meaningful.
        """
        raise NotImplementedError()

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database.
        Reimplement in subclasses.
        """
        raise NotImplementedError()

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.

        Args:
            row (int): Row number where new rows are inserted
            count (int): Number of inserted rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were inserted successfully, False otherwise
        """
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            # Create the new row using the `create_item` attribute
            new_main_row = self.create_item()
            # Notice if insert index > rowCount(), new object is inserted to end
            self._main_data.insert(row + i, new_main_row)
        self.endInsertRows()
        return True

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Set data in model first, then set internal data for modified items.
        Finally add successfully modified items to the db.
        """
        self.error_log.clear()
        self.added_rows.clear()
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row(): self._main_data[ind.row()] for ind in indexes}
        self.batch_autocomplete_data(rows)
        self.add_items_to_db(rows)
        return True

    def add_items_to_db(self, rows):
        """Adds items to database.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        for row, item in rows.items():
            item = self._main_data[row]
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            item_for_insert = item.for_insert()
            if not item_for_insert:
                continue
            new_items, error_log = self.do_add_items_to_db(db_map, item_for_insert)
            self.error_log.extend(error_log)
            if not error_log:
                new_item = new_items.first()
                item.id = new_item.id
                item.clear_cache()
            self.added_rows.append(row)


class EmptyParameterDefinitionModel(ParameterDefinitionAutocompleteMixin, EmptyParameterModel):
    """An empty parameter definition model.
    Handles all parameter definitions regardless of the entity class.
    """

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database."""
        return db_map.add_parameter_definitions(*items)

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_tag_id_lists(rows)
        self.batch_set_value_list_ids(rows)

    def add_items_to_db(self, rows):
        """Adds items to database.
        Call the super method to add parameter definitions, then the method to set tags.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        super().add_items_to_db(rows)
        self.set_parameter_definition_tags_in_db(rows)


class EmptyObjectParameterDefinitionModel(
    ObjectParameterDecorateMixin, ObjectParameterAutocompleteMixin, EmptyParameterDefinitionModel
):
    """An empty object parameter definition model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return ObjectParameterDefinitionItem(self.header)

    def batch_autocomplete_data(self, rows):
        """Sets more data for model items in batch.

        Args:
            rows (list): A list of items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_object_class_ids(rows)


class EmptyRelationshipParameterDefinitionModel(
    RelationshipParameterDecorateMixin, RelationshipParameterAutocompleteMixin, EmptyParameterDefinitionModel
):
    """An empty relationship parameter definition model."""

    def create_item(self):
        return RelationshipParameterDefinitionItem(self.header)

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_relationship_class_ids(rows)


class EmptyParameterValueModel(ParameterValueAutocompleteMixin, EmptyParameterModel):
    """An empty parameter value model.
    Handles all parameter values regardless of the entity.
    """

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database."""
        return db_map.add_parameter_values(*items)

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_possible_parameter_ids(rows)


class EmptyObjectParameterValueModel(
    ObjectParameterDecorateMixin, ObjectParameterAutocompleteMixin, EmptyParameterValueModel
):
    """An empty object parameter value model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return ObjectParameterValueItem(self.header)

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_object_class_ids(rows)
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


class EmptyRelationshipParameterValueModel(
    RelationshipParameterDecorateMixin, RelationshipParameterAutocompleteMixin, EmptyParameterValueModel
):
    """An empty relationship parameter value model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return RelationshipParameterValueItem(self.header)

    def batch_autocomplete_data(self, rows):
        """Autocompletes data for indexes in batch.

        Args:
            rows (dict): A dict mapping row numbers to items that need treatment
        """
        super().batch_autocomplete_data(rows)
        self.batch_set_relationship_class_ids(rows)
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

    def add_items_to_db(self, rows):
        """Adds items to database. Add relationships on the fly first,
        then proceed to add parameter values by calling the super() method.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        for row, item in rows.items():
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship_for_insert = item.relationship_for_insert()
            if not relationship_for_insert:
                continue
            new_relationships, error_log = db_map.add_wide_relationships(relationship_for_insert)
            if error_log:
                self.error_log.extend(error_log)
                continue
            new_relationship = new_relationships.first()
            item.relationship_id = new_relationship.id
        # TODO: try and do this with signals and slots
        # self._parent._parent.object_tree_model.add_relationships(db_map, new_relationships)
        # self._parent._parent.relationship_tree_model.add_relationships(db_map, new_relationships)
        super().add_items_to_db(rows)
