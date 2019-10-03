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
from helpers import busy_effect
from mvcmodels.empty_row_model import EmptyRowModel
from mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class EmptyParameterModel(EmptyRowModel):
    """An empty parameter model."""

    def __init__(self, parent, item_maker):
        """Initialize class.

        Args:
            parent (ParameterModel): the parent object
            item_maker (function): a function to create items to put in the model rows
        """
        super().__init__(parent)
        self._parent = parent
        self.db_name_to_map = parent.db_name_to_map
        self.item_maker = item_maker
        self.error_log = []
        self.added_rows = []

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
            # Create the new row using the `item_maker` attribute
            new_main_row = self.item_maker(self.horizontal_header_labels())
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
        unique_rows = {ind.row() for ind in indexes}
        items = [self._main_data[row] for row in unique_rows]
        self.batch_set_internal_data(items)
        self.batch_set_entity_data(items)
        self.add_items_to_db(unique_rows)
        return True

    def batch_set_internal_data(self, items):
        """Sets internal data for indexes in batch.
        Reimplement in subclasses to set id from names etc.

        Args:
            items (list): A list of items that need treatment
        """
        raise NotImplementedError

    def batch_set_entity_data(self, items):
        """Sets entity data for indexes in batch.
        Reimplement in subclasses to set data related to the entity.

        Args:
            items (list): A list of items that need treatment
        """
        raise NotImplementedError

    def add_items_to_db(self, rows):
        """Adds items to database. Reimplement in subclasses.

        Args:
            rows (list): A list of model rows whose items should be added to the db
        """
        raise NotImplementedError


class EmptyParameterDefinitionModel(EmptyParameterModel):
    """An empty parameter definition model.
    Provides methods common to all parameter definitions regardless of the entity class.
    """

    def batch_set_internal_data(self, items):
        """Sets internal data for model items in batch.
        Set parameter tag ids and value list ids in accordance with the names.

        Args:
            items (list): A list of items that need treatment
        """
        # Collect value list names and parameter tags for which we need to query the id
        value_list_names = dict()
        parameter_tags = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            value_list_names.setdefault(database, set()).add(item.value_list_name)
            if item.parameter_tag_list:
                tags = item.parameter_tag_list.split(",")
                parameter_tags.setdefault(database, set()).update(tags)
        # Do the queries
        value_list_dict = dict()
        parameter_tag_dict = dict()
        for database, names in value_list_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            parameter_value_list = db_map.wide_parameter_value_list_sq
            value_list_dict[database] = {
                x.name: x.id for x in db_map.query(parameter_value_list).filter(parameter_value_list.c.name.in_(names))
            }
        for database, tags in parameter_tags.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            parameter_tag = db_map.parameter_tag_sq
            parameter_tag_dict[database] = {
                x.tag: x.id for x in db_map.query(parameter_tag).filter(parameter_tag.c.tag.in_(tags))
            }
        # Update the items
        for item in items:
            database = item.database
            db_value_list_dict = value_list_dict.get(database)
            if db_value_list_dict:
                item.value_list_id = db_value_list_dict.get(item.value_list_name)
            db_parameter_tag_dict = parameter_tag_dict.get(database)
            if db_parameter_tag_dict and item.parameter_tag_list:
                tags = item.parameter_tag_list.split(",")
                tag_ids = [db_parameter_tag_dict.get(tag) for tag in tags]
                if None in tag_ids:
                    item.parameter_tag_id_list = None
                else:
                    item.parameter_tag_id_list = ",".join([str(id_) for id_ in tag_ids])

    def add_items_to_db(self, rows):
        """Adds items to database.

        Args:
            rows (list): A list of model rows whose items should be added to the db
        """
        self.error_log.clear()
        self.added_rows.clear()
        tags_dict = dict()
        for row in rows:
            item = self._main_data[row]
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            item_for_insert = item.for_insert()
            if not item_for_insert:
                continue
            new_items, error_log = db_map.add_parameter_definitions(item_for_insert)
            if error_log:
                self.error_log.extend(error_log)
                continue
            new_item = new_items.first()
            item.id = new_item.id
            # Populate tags dict
            if item.parameter_tag_id_list:
                tags_dict.setdefault(db_map, dict())[item.id] = item.parameter_tag_id_list
            self.added_rows.append(row)
        # Set tags
        for db_map, tags in tags_dict.items():
            _, error_log = db_map.set_parameter_definition_tags(tags)
            self.error_log.extend(error_log)


class EmptyObjectParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty object parameter definition model."""

    def __init__(self, parent):
        super().__init__(parent, item_maker=ObjectParameterDefinitionItem)

    def batch_set_entity_data(self, items):
        """Sets entity data for model items in batch.
        Set object class ids in accordance with the object class names.

        Args:
            items (list): A list of items that need treatment
        """
        # Collect object class names for which we need to query the id
        object_class_names = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            object_class_names.setdefault(database, set()).add(item.object_class_name)
        # Do the queries
        object_class_dict = dict()
        for database, names in object_class_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            object_class = db_map.object_class_sq
            object_class_dict[database] = {
                x.name: x.id for x in db_map.query(object_class).filter(object_class.c.name.in_(names))
            }
        # Update the items
        for item in items:
            database = item.database
            db_object_class_dict = object_class_dict.get(database)
            if db_object_class_dict:
                item.object_class_id = db_object_class_dict.get(item.object_class_name)


class EmptyRelationshipParameterDefinitionModel(EmptyParameterDefinitionModel):
    """An empty relationship parameter definition model."""

    def __init__(self, parent):
        super().__init__(parent, item_maker=RelationshipParameterDefinitionItem)

    def batch_set_entity_data(self, items):
        """Sets entity data for model items in batch.
        Set relationship class ids and object class id and name lists
        in accordance with the relationship class names.

        Args:
            items (list): A list of items that need treatment
        """
        super().batch_set_internal_data(items)
        # Collect object class names for which we need to query the data
        relationship_class_names = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            relationship_class_names.setdefault(database, set()).add(item.relationship_class_name)
        # Do the queries
        relationship_class_dict = dict()
        for database, names in relationship_class_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship_class = db_map.wide_relationship_class_sq
            relationship_class_dict[database] = {
                x.name: x for x in db_map.query(relationship_class).filter(relationship_class.c.name.in_(names))
            }
        # Update the items
        for item in items:
            database = item.database
            db_relationship_class_dict = relationship_class_dict.get(database)
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


class EmptyParameterValueModel(EmptyParameterModel):
    """An empty parameter value model."""

    def batch_set_internal_data(self, items):
        """Sets internal data for model items in batch.
        Set possible parameter definition ids in accordance with the names.

        Args:
            items (list): A list of items that need treatment
        """
        # Collect definition names for which we need to query the id
        definition_names = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            definition_names.setdefault(database, set()).add(item.parameter_name)
        # Do the queries
        definition_dict = dict()
        for database, names in definition_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            parameter_definition = db_map.parameter_definition_sq
            definition_dict[database] = {
                name: {
                    x.object_class_id or x.relationship_class_id: x.id
                    for x in db_map.query(parameter_definition).filter(parameter_definition.c.name == name)
                }
                for name in names
            }
        # Update the items
        for item in items:
            database = item.database
            db_definition_dict = definition_dict.get(database)
            if db_definition_dict:
                item._definition_dict = db_definition_dict.get(item.parameter_name, {})

    def add_items_to_db(self, rows):
        """Adds items to database.

        Args:
            rows (list): A list of model rows whose items should be added to the db
        """
        for row in rows:
            item = self._main_data[row]
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            item_for_insert = item.for_insert()
            if not item_for_insert:
                continue
            new_items, error_log = db_map.add_parameter_values(item_for_insert)
            if error_log:
                self.error_log.extend(error_log)
                continue
            new_item = new_items.first()
            item.id = new_item.id
            self.added_rows.append(row)


class EmptyObjectParameterValueModel(EmptyParameterValueModel):
    """An empty object parameter value model."""

    def __init__(self, parent):
        super().__init__(parent, item_maker=ObjectParameterValueItem)

    def batch_set_entity_data(self, items):
        """Sets entity data for model items in batch.

        Args:
            items (list): A list of items that need treatment
        """
        self.batch_set_entity_data_phase_1(items)
        self.batch_set_entity_data_phase_2(items)

    def batch_set_entity_data_phase_1(self, items):
        """Set possible object ids and object class ids in accordance with names."""
        # Collect object and object class names for which we need to query the data
        object_names = dict()
        object_class_names = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            object_names.setdefault(database, set()).add(item.object_name)
            object_class_names.setdefault(database, set()).add(item.object_class_name)
        # Do the queries
        object_dict = dict()
        object_class_dict = dict()
        for database, names in object_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            object_ = db_map.object_sq
            object_dict[database] = {
                name: {x.class_id: x.id for x in db_map.query(object_).filter(object_.c.name == name)} for name in names
            }
        for database, names in object_class_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            object_class = db_map.object_class_sq
            object_class_dict[database] = {
                x.name: x.id for x in db_map.query(object_class).filter(object_class.c.name.in_(names))
            }
        # Update the items
        for item in items:
            database = item.database
            db_object_dict = object_dict.get(database)
            if db_object_dict:
                item._object_dict = db_object_dict.get(item.object_name, {})
            db_object_class_dict = object_class_dict.get(database)
            if db_object_class_dict:
                item.object_class_id = db_object_class_dict.get(item.object_class_name)

    def batch_set_entity_data_phase_2(self, items):
        """Try and figure out object class id automatically, and then the name.
        Also pick the right object_id and parameter_id according to object class id.
        """
        object_class_ids = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            if item.object_class_id is None:
                # Try and see if we can figure out the object class id
                if item._object_dict and item._definition_dict:
                    object_class_id = item._object_dict.keys() & item._definition_dict.keys()
                elif item._object_dict:
                    object_class_id = set(item._object_dict.keys())
                elif item._definition_dict:
                    object_class_id = set(item._definition_dict.keys())
                else:
                    object_class_id = {}
                if len(object_class_id) != 1:
                    continue
                item.object_class_id = object_class_id.pop()
                item.object_class_name = True  # Mark the item somehow
                object_class_ids.setdefault(database, set()).add(item.object_class_id)
            # Pick the right object_id and parameter_id
            item.object_id = item._object_dict.get(item.object_class_id)
            item.parameter_id = item._definition_dict.get(item.object_class_id)
        # Do the queries
        object_class_dict = dict()
        for database, ids in object_class_ids.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            object_class = db_map.object_class_sq
            object_class_dict[database] = {
                x.id: x.name for x in db_map.query(object_class).filter(object_class.c.id.in_(ids))
            }
        # Update the items
        for item in items:
            database = item.database
            db_object_class_dict = object_class_dict.get(database)
            if db_object_class_dict and item.object_class_name is True:
                item.object_class_name = db_object_class_dict.get(item.object_class_id)


class EmptyRelationshipParameterValueModel(EmptyParameterValueModel):
    """An empty relationship parameter value model.
    """

    def __init__(self, parent):
        super().__init__(parent, item_maker=RelationshipParameterValueItem)

    def batch_set_entity_data(self, items):
        """Sets entity data for model items in batch.
        Set object ids in accordance with names.
        Then set object class names in accordance with ids set in the previous step.

        Args:
            items (list): A list of items that need treatment
        """
        self.batch_set_entity_data_phase_1(items)
        self.batch_set_entity_data_phase_2(items)
        self.batch_set_entity_data_phase_3(items)

    def batch_set_entity_data_phase_1(self, items):
        """Set possible relationship ids and relationship class ids in accordance with names."""
        # Collect object name lists and relationship class names for which we need to query the data
        object_name_lists = dict()
        relationship_class_names = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            object_name_lists.setdefault(database, set()).add(item.object_name_list)
            relationship_class_names.setdefault(database, set()).add(item.relationship_class_name)
        # Do the queries
        relationship_dict = dict()
        relationship_class_dict = dict()
        for database, name_lists in object_name_lists.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship = db_map.wide_relationship_sq
            relationship_dict[database] = {
                name_list: {
                    x.class_id: x
                    for x in db_map.query(relationship).filter(relationship.c.object_name_list == name_list)
                }
                for name_list in name_lists
            }
        for database, names in relationship_class_names.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship_class = db_map.wide_relationship_class_sq
            relationship_class_dict[database] = {
                x.name: x for x in db_map.query(relationship_class).filter(relationship_class.c.name.in_(names))
            }
        # Update the items
        for item in items:
            database = item.database
            db_relationship_dict = relationship_dict.get(database)
            if db_relationship_dict:
                item._relationship_dict = db_relationship_dict.get(item.object_name_list, {})
                relationship_class = db_relationship_dict.get(item.relationship_class_name)
                if relationship_class:
                    item.relationship_class_id = relationship_class.id
                    item.object_class_id_list = relationship_class.object_class_id_list
                    item.object_class_name_list = relationship_class.object_class_name_list
                else:
                    item.relationship_class_id = None
                    item.object_class_id_list = None
                    item.object_class_name_list = None

    def batch_set_entity_data_phase_2(self, items):
        """Try and figure out relationship class id automatically, and then the name.
        Also pick the right relationship_id and parameter_id according to relationship class id.
        """
        relationship_class_ids = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            if item.relationship_class_id is None:
                # Try and see if we can figure out the object class id
                if item._relationship_dict and item._definition_dict:
                    relationship_class_id = item._relationship_dict.keys() & item._definition_dict.keys()
                elif item._relationship_dict:
                    relationship_class_id = set(item._relationship_dict.keys())
                elif item._definition_dict:
                    relationship_class_id = set(item._definition_dict.keys())
                else:
                    relationship_class_id = {}
                if len(relationship_class_id) != 1:
                    continue
                item.relationship_class_id = relationship_class_id.pop()
                item.relationship_class_name = True  # Mark the item somehow
                relationship_class_ids.setdefault(database, set()).add(item.relationship_class_id)
            # Pick the right object_id and parameter_id
            relationship = item._relationship_dict.get(item.relationship_class_id)
            if relationship:
                item.relationship_id = relationship.id
                item.object_id_list = relationship.object_id_list
            item.parameter_id = item._definition_dict.get(item.relationship_class_id)
        # Do the queries
        relationship_class_dict = dict()
        for database, ids in relationship_class_ids.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship_class = db_map.wide_relationship_class_sq
            relationship_class_dict[database] = {
                x.id: x for x in db_map.query(relationship_class).filter(relationship_class.c.id.in_(ids))
            }
        # Update the items
        for item in items:
            database = item.database
            db_relationship_class_dict = relationship_class_dict.get(database)
            if db_relationship_class_dict and item.relationship_class_name is True:
                relationship_class = db_relationship_class_dict.get(item.relationship_class_id)
                if relationship_class:
                    item.relationship_class_name = relationship_class.name
                    item.object_class_id_list = relationship_class.object_class_id_list
                    item.object_class_name_list = relationship_class.object_class_name_list
                else:
                    item.relationship_class_id = None
                    item.object_class_id_list = None
                    item.object_class_name_list = None

    def batch_set_entity_data_phase_3(self, items):
        """Set object_id_list if not set and possible.
        """
        # Collect tuples (class_id, name) of objects for which we need to query the data
        object_name_class_id_tuples = dict()
        for item in items:
            database = item.database
            if not database:
                continue
            if not item.object_id_list and item.object_name_list and item.object_class_id_list:
                # We must set the object_id_list
                object_names = item.object_name_list.split(",")
                object_class_ids = [int(x) for x in item.object_class_id_list.split(",")]
                item._object_name_class_id_tups = set(zip(object_names, object_class_ids))
                object_name_class_id_tuples.setdefault(database, set()).update(item._object_name_class_id_tups)
            else:
                item._object_name_class_id_tups = None
        # Do the queries
        object_dict = dict()
        for database, tups in object_name_class_id_tuples.items():
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            object_ = db_map.object_sq
            object_dict[database] = {
                (x.name, x.class_id): x.id
                for x in db_map.query(object_).filter(
                    or_(*(and_(object_.c.name == name, object_.c.class_id == class_id) for (name, class_id) in tups))
                )
            }
        # Update the items
        for item in items:
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
            rows (list): A list of model rows whose items should be added to the db
        """
        for row in rows:
            item = self._main_data[row]
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
        # TODO:
        # self._parent._parent.object_tree_model.add_relationships(db_map, new_relationships)
        # self._parent._parent.relationship_tree_model.add_relationships(db_map, new_relationships)
        super().add_items_to_db(rows)
