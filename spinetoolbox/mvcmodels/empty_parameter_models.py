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
from PySide2.QtCore import Qt, Slot
from ..mvcmodels.empty_row_model import EmptyRowModel
from ..mvcmodels.parameter_mixins import (
    FillInParameterNameMixin,
    FillInValueListIdMixin,
    MakeParameterTagMixin,
    ConvertToDBMixin,
)
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

    @property
    def entity_class_type(self):
        """Either 'object class' or 'relationship class'."""
        raise NotImplementedError()

    @property
    def entity_class_id_key(self):
        return {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.entity_class_type
        ]

    @property
    def entity_class_name_key(self):
        return {"object class": "object_class_name", "relationship class": "relationship_class_name"}[
            self.entity_class_type
        ]

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (item.get(self.entity_class_name_key), item.get("parameter_name"))

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object or relationship parameter definitions or values.
        Must be reimplemented in subclasses according to the entity type and to whether
        it's a definition or value model. Used by receive_parameter_data_added."""
        raise NotImplementedError()

    @Slot("QVariant", name="receive_parameter_data_added")
    def receive_parameter_data_added(self, db_map_data):
        """Runs when parameter definitions or values are added.
        Finds and removes model items that were successfully added to the db."""
        added_ids = []
        for db_map, items in db_map_data.items():
            ids = {x["id"] for x in items}
            for item in self.get_entity_parameter_data(db_map, ids=ids):
                database = db_map.codename
                unique_id = (database, *self._make_unique_id(item))
                added_ids.append(unique_id)
        removed_rows = []
        for row, data in enumerate(self._main_data):
            item = dict(zip(self.header, data))
            database = item.get("database")
            unique_id = (database, *self._make_unique_id(item))
            if unique_id in added_ids:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.removeRows(row, count)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch. If successful, add items to db."""
        if not super().batch_set_data(indexes, data):
            return False
        unique_rows = {ind.row() for ind in indexes}
        items = [dict(zip(self.header, self._main_data[row]), row=row) for row in unique_rows]
        self.add_items_to_db(items)
        return True

    def add_items_to_db(self, items):
        """Groups items by database and calls _do_add_items_to_db.

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
        """Adds database grouped items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of items to add
        """
        raise NotImplementedError()

    def _take_db_map(self, item):
        """Takes the database key from the given item and returns the corresponding DiffDatabaseMapping instance.
        Returns None if no match.
        """
        database = item.pop("database")
        return next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)


class FillInEntityClassIdMixin(ConvertToDBMixin):
    """Fills in entity class ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_ent_cls_lookup = dict()

    def begin_convert_to_db(self, db_map_data):
        """Begins an operation to convert items. Populate lookup dict.
        """
        super().begin_convert_to_db(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                entity_class_name = item.get(self.entity_class_name_key)
                db_map_names.setdefault(db_map, set()).add(entity_class_name)
        # Build lookup dicts
        self._db_map_ent_cls_lookup.clear()
        for db_map, names in db_map_names.items():
            for name in names:
                item = self.db_mngr.get_item_by_field(db_map, self.entity_class_type, "name", name)
                if item:
                    self._db_map_ent_cls_lookup.setdefault(db_map, {})[name] = item

    def _fill_in_entity_class_id(self, item, db_map):
        """Fills in the entity class id."""
        entity_class_name = item.pop(self.entity_class_name_key, None)
        entity_class = self._db_map_ent_cls_lookup.get(db_map, {}).get(entity_class_name)
        if not entity_class:
            return
        item[self.entity_class_id_key] = entity_class.get("id")

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._fill_in_entity_class_id(item, db_map)
        return item

    def end_convert_to_db(self):
        """Ends an operation to convert items."""
        super().end_convert_to_db()
        self._db_map_ent_cls_lookup.clear()


class EmptyParameterDefinitionModel(
    FillInValueListIdMixin, MakeParameterTagMixin, FillInParameterNameMixin, EmptyParameterModel
):
    """An empty parameter definition model."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_data_added)

    def _do_add_items_to_db(self, db_map_data):
        """Adds database grouped items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of model items
        """
        self.begin_convert_to_db(db_map_data)
        db_map_param_def = dict()
        db_map_param_tag = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item = self._convert_to_db(item, db_map)
                tag_item = self._make_parameter_definition_tag(item, db_map)
                if self._check_item(def_item):
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if tag_item:
                    db_map_param_tag.setdefault(db_map, []).append(tag_item)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if any(db_map_param_tag.values()):
            self.db_mngr.set_parameter_definition_tags(db_map_param_tag)
        self.end_convert_to_db()

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and "name" in item


class EmptyObjectParameterDefinitionModel(FillInEntityClassIdMixin, EmptyParameterDefinitionModel):
    """An empty object parameter definition model."""

    @property
    def entity_class_type(self):
        return "object class"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_definitions(db_map, ids=ids)


class EmptyRelationshipParameterDefinitionModel(FillInEntityClassIdMixin, EmptyParameterDefinitionModel):
    """An empty relationship parameter definition model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_definitions(db_map, ids=ids)

    def flags(self, index):
        """Additional hack to make the object_class_name_list column non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] == "object_class_name_list":
            flags &= ~Qt.ItemIsEditable
        return flags


class FillInObjectIdsMixin(ConvertToDBMixin):
    """Fills in object ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_obj_lookup = dict()

    def begin_convert_to_db(self, db_map_data):
        """Begins an operation to convert items. Populate lookup dict.
        """
        super().begin_convert_to_db(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                name = item.get("object_name")
                db_map_names.setdefault(db_map, set()).add(name)
        # Build lookup dicts
        self._db_map_obj_lookup.clear()
        for db_map, names in db_map_names.items():
            for name in names:
                items = self.db_mngr.get_items_by_field(db_map, "object", "name", name)
                if items:
                    self._db_map_obj_lookup.setdefault(db_map, {})[name] = items

    def _fill_in_object_ids(self, item, db_map):
        """Fills in all possible object ids (as there can be more than one for the same name)
        keyed by object class id."""
        name = item.pop("object_name", None)
        items = self._db_map_obj_lookup.get(db_map, {}).get(name)
        if not items:
            return
        item["object_ids"] = {x["class_id"]: x["id"] for x in items}

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._fill_in_object_ids(item, db_map)
        return item

    def end_convert_to_db(self):
        """Ends an operation to convert items."""
        super().end_convert_to_db()
        self._db_map_obj_lookup.clear()


class FillInParameterDefinitionIdsMixin(ConvertToDBMixin):
    """Fills in parameter definition ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_param_lookup = dict()

    def begin_convert_to_db(self, db_map_data):
        """Begins an operation to convert items. Populate lookup dict.
        """
        super().begin_convert_to_db(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                name = item.get("parameter_name")
                db_map_names.setdefault(db_map, set()).add(name)
        # Build lookup dicts
        self._db_map_param_lookup.clear()
        for db_map, names in db_map_names.items():
            for name in names:
                items = self.db_mngr.get_items_by_field(db_map, "parameter definition", "parameter_name", name)
                if items:
                    self._db_map_param_lookup.setdefault(db_map, {})[name] = items

    def _fill_in_parameter_ids(self, item, db_map):
        """Fills in all possible parameter definition ids
        (as there can be more than one for the same name) keyed by entity class id."""
        name = item.pop("parameter_name", None)
        items = self._db_map_param_lookup.get(db_map, {}).get(name)
        if not items:
            return
        item["parameter_ids"] = {x.get("object_class_id") or x.get("relationship_class_id"): x["id"] for x in items}

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._fill_in_parameter_ids(item, db_map)
        return item

    def end_convert_to_db(self):
        """Ends an operation to convert items."""
        super().end_convert_to_db()
        self._db_map_param_lookup.clear()


class InferObjectClassIdMixin(ConvertToDBMixin):
    """Infers object class ids."""

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._infer_and_fill_in_object_class_id(item, db_map)
        return item

    def _infer_and_fill_in_object_class_id(self, item, db_map):
        """Try and infer the object class id by intersecting object ids and parameter ids previously computed.
        Then pick the correct object id and parameter definition id based on that, and fill everything in.
        Also set the inferred object class name in the model.
        """
        row = item.pop("row")
        object_ids = item.pop("object_ids", {})
        parameter_ids = item.pop("parameter_ids", {})
        if "object_class_id" not in item:
            object_class_ids = {*object_ids.keys(), *parameter_ids.keys()}
            if len(object_class_ids) != 1:
                return
            object_class_id = object_class_ids.pop()
            item["object_class_id"] = object_class_id
            object_class_name = self.db_mngr.get_item(db_map, "object class", object_class_id)["name"]
            # TODO: Check if this is the right place to do it
            self._main_data[row][self.header.index("object_class_name")] = object_class_name
        object_class_id = item["object_class_id"]
        object_id = object_ids.get(object_class_id)
        parameter_definition_id = parameter_ids.get(object_class_id)
        if not object_id or not parameter_definition_id:
            return
        item["object_id"] = object_id
        item["parameter_definition_id"] = parameter_definition_id


class EmptyParameterValueModel(FillInParameterDefinitionIdsMixin, EmptyParameterModel):
    """An empty parameter value model."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_data_added)

    def _do_add_items_to_db(self, db_map_data):
        """Add database grouped items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of model items
        """
        self.begin_convert_to_db(db_map_data)
        db_map_param_val = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                val_item = self._convert_to_db(item, db_map)
                if self._check_item(val_item):
                    db_map_param_val.setdefault(db_map, []).append(val_item)
        if any(db_map_param_val.values()):
            self.db_mngr.add_parameter_values(db_map_param_val)
        self.end_convert_to_db()


class EmptyObjectParameterValueModel(
    InferObjectClassIdMixin, FillInObjectIdsMixin, FillInEntityClassIdMixin, EmptyParameterValueModel
):
    """An empty object parameter value model."""

    @property
    def entity_class_type(self):
        return "object class"

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (*super()._make_unique_id(item), item.get("object_name"))

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_values(db_map, ids=ids)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and "object_id" in item and "parameter_definition_id" in item


class EmptyRelationshipParameterValueModel(FillInEntityClassIdMixin, EmptyParameterValueModel):
    """An empty relationship parameter value model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (*super()._make_unique_id(item), item.get("object_name_list"))

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_values(db_map, ids=ids)

    def _add_items_to_db(self, rows):
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
