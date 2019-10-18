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
from PySide2.QtCore import Slot
from ..mvcmodels.empty_row_model import EmptyRowModel
from ..mvcmodels.parameter_mixins import ParameterDefinitionFillInMixin
from ..helpers import rows_to_row_count_tuples


class EmptyParameterModel(EmptyRowModel):
    """An empty parameter model."""

    def __init__(self, parent, header, db_mngr):
        """Initialize class.

        Args:
            parent (Object): the parent object, typically a CompoundParameterModel
            header (list): list of field names for the header
            db_mngr (SpineDBManager)
        """
        super().__init__(parent, header)
        self.db_mngr = db_mngr
        self.connect_db_mngr_signals()

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""

    @property
    def insert_method_name(self):
        raise NotImplementedError()

    @property
    def item_type(self):
        raise NotImplementedError()

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        If successful, add items to db.
        """
        if not super().batch_set_data(indexes, data):
            return False
        unique_rows = {ind.row() for ind in indexes}
        items = [dict(zip(self.header, self._main_data[row])) for row in unique_rows]
        self.add_items_to_db(items)
        return True

    def add_items_to_db(self, items):
        """Adds items to database.

        Args:
            items (list): list of dict items
        """
        db_map_data = dict()
        for item in items:
            db_map = self._take_db_map(item)
            if not db_map:
                continue
            db_map_data.setdefault(db_map, []).append(item)
        self._do_add_items_to_db(db_map_data)

    def _do_add_items_to_db(self, db_map_data):
        """Add items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items to add
        """
        raise NotImplementedError()

    def _take_db_map(self, item):
        database = item.pop("database")
        return next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)


class EmptyParameterDefinitionMixin:
    """Handles parameter definitions added."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_definitions_added)

    @Slot("QVariant", name="receive_parameter_definitions_added")
    def receive_parameter_definitions_added(self, db_map_data):
        """Runs when parameter definitions are added. Find matches and removes them,
        they have nothing to do in this model anymore."""
        signatures = []
        for db_map, items in db_map_data.items():
            ids = {x["id"] for x in items}
            for item in self.db_mngr.get_object_parameter_definitions(db_map, ids=ids):
                database = db_map.codename
                parameter_name = item.get("parameter_name")
                entity_class_name = item.get("object_class_name") or item.get("relationship_class_name")
                signatures.append((database, parameter_name, entity_class_name))
        removed_rows = []
        for row, data in enumerate(self._main_data):
            item = dict(zip(self.header, data))
            database = item.get("database")
            parameter_name = item.get("parameter_name")
            entity_class_name = item.get("object_class_name") or item.get("relationship_class_name")
            if (database, parameter_name, entity_class_name) in signatures:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.removeRows(row, count)

    def _do_add_items_to_db(self, db_map_data):
        """Add items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of model items
        """
        db_map_param_def = dict()
        db_map_param_tag = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item = self._make_param_def_item(item, db_map)
                tag_item = self._make_param_tag_item(item, db_map)
                if def_item:
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if tag_item:
                    db_map_param_tag.setdefault(db_map, []).append(tag_item)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if any(db_map_param_tag.values()):
            self.db_mngr.set_parameter_definition_tags(db_map_param_tag)

    def _make_param_def_item(self, item, db_map):
        """Returns a parameter definition item for adding to the database."""
        item = item.copy()
        self._fill_in_parameter_name(item)
        self._fill_in_entity_class_id(item, db_map)
        self._fill_in_parameter_tag_id_list(item, db_map)
        if not self._entity_class_id_key in item or not "name" in item:
            return None
        return item

    @property
    def _entity_class_id_key(self):
        raise NotImplementedError()


class EmptyObjectParameterDefinitionModel(
    ParameterDefinitionFillInMixin, EmptyParameterDefinitionMixin, EmptyParameterModel
):
    """An empty object parameter definition model."""

    @property
    def _entity_class_id_key(self):
        return "object_class_id"

    def _fill_in_entity_class_id(self, item, db_map):
        entity_class_name = item.pop("object_class_name", None)
        if not entity_class_name:
            return
        entity_class = self.db_mngr.get_item_by_field(db_map, "object class", "name", entity_class_name)
        if not entity_class:
            return
        item["object_class_id"] = entity_class.get("id")


class EmptyRelationshipParameterDefinitionModel(
    ParameterDefinitionFillInMixin, EmptyParameterDefinitionMixin, EmptyParameterModel
):
    """An empty relationship parameter definition model."""

    @property
    def _entity_class_id_key(self):
        return "relationship_class_id"

    def _fill_in_entity_class_id(self, item, db_map):
        entity_class_name = item.pop("relationship_class_name", None)
        if not entity_class_name:
            return
        entity_class = self.db_mngr.get_item_by_field(db_map, "relationship class", "name", entity_class_name)
        if not entity_class:
            return
        item["relationship_class_id"] = entity_class.get("id")


class EmptyObjectParameterValueModel(EmptyParameterModel):
    """An empty object parameter value model."""


class EmptyRelationshipParameterValueModel(EmptyParameterModel):
    """An empty relationship parameter value model."""

    def add_items_to_db(self, rows):
        """Adds items to database. Add relationships on the fly first,
        then proceed to add parameter values by calling the super() method.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        db_map_data = dict()
        for row, item in rows.items():
            db_map = item.db_map
            if not db_map:
                continue
            relationship_for_insert = item.relationship_for_insert()
            if not relationship_for_insert:
                continue
            db_map_data.setdefault(db_map, []).append(relationship_for_insert)
        self.db_mng.add_relationships(db_map_data)
        super().add_items_to_db(rows)
