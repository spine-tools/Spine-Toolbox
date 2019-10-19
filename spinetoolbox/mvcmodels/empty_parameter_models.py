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
from ..mvcmodels.parameter_mixins import ParameterDefinitionFillInMixin, ParameterFillInBase
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

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object or relationship parameter definitions or values.
        Must be reimplemented in subclasses according to the entity type and parameter type.
        Used by receive_parameter_data_added."""
        raise NotImplementedError()

    def _make_parameter_data_id(self, item):
        """Returns a unique id from parameter data. Used by receive_parameter_data_added."""
        raise NotImplementedError()

    @Slot("QVariant", name="receive_parameter_data_added")
    def receive_parameter_data_added(self, db_map_data):
        """Runs when parameter definitions or values are added. Find matches and removes them,
        they have nothing to do in this model anymore."""
        added_ids = []
        for db_map, items in db_map_data.items():
            ids = {x["id"] for x in items}
            for item in self.get_entity_parameter_data(db_map, ids=ids):
                database = db_map.codename
                unique_id = (database, *self._make_parameter_data_id(item))
                added_ids.append(unique_id)
        removed_rows = []
        for row, data in enumerate(self._main_data):
            item = dict(zip(self.header, data))
            database = item.get("database")
            unique_id = (database, *self._make_parameter_data_id(item))
            if unique_id in added_ids:
                removed_rows.append(row)
        for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
            self.removeRows(row, count)

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


class EntityClassFillInMixin(ParameterFillInBase):
    """Provides methods to fill in entity class ids for parameter definition or value items
    edited by the user, so they can be entered in the database.
    """

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_ent_cls_lookup = dict()

    @property
    def entity_class_id_key(self):
        raise NotImplementedError()

    @property
    def entity_class_name_key(self):
        raise NotImplementedError()

    @property
    def entity_class_type(self):
        raise NotImplementedError()

    def _make_parameter_data_id(self, item):
        """Returns a unique id from parameter data. Used by receive_parameter_data_added."""
        return (item.get("parameter_name"), item.get(self.entity_class_name_key))

    def begin_modify_db(self, db_map_data):
        """Begins an operation to add or update database items.
        Populate the lookup dicts with necessary data needed by the _fill_in methods to work.
        """
        super().begin_modify_db(db_map_data)
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
        entity_class_name = item.pop(self.entity_class_name_key, None)
        entity_class = self._db_map_ent_cls_lookup.get(db_map, {}).get(entity_class_name)
        if not entity_class:
            return
        item[self.entity_class_id_key] = entity_class.get("id")

    def _make_parameter_item(self, item, db_map):
        """Returns a parameter item for adding to the database."""
        item = super()._make_parameter_item(item, db_map)
        self._fill_in_entity_class_id(item, db_map)
        return item

    def end_modify_db(self):
        """Ends an operation to add or update database items."""
        super().end_modify_db()
        self._db_map_ent_cls_lookup.clear()


class ObjectClassFillInMixin(EntityClassFillInMixin):
    """Specialization of EntityClassFillInMixin for object class."""

    @property
    def entity_class_id_key(self):
        return "object_class_id"

    @property
    def entity_class_name_key(self):
        return "object_class_name"

    @property
    def entity_class_type(self):
        return "object class"


class RelationshipClassFillInMixin(EntityClassFillInMixin):
    """Specialization of EntityClassFillInMixin for relationship class."""

    @property
    def entity_class_id_key(self):
        return "relationship_class_id"

    @property
    def entity_class_name_key(self):
        return "relationship_class_name"

    @property
    def entity_class_type(self):
        return "relationship class"


class EmptyParameterDefinitionMixin(ParameterDefinitionFillInMixin):
    """Handles parameter definitions added."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_data_added)

    def _do_add_items_to_db(self, db_map_data):
        """Add items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of model items
        """
        self.begin_modify_db(db_map_data)
        db_map_param_def = dict()
        db_map_param_tag = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item = self._make_parameter_item(item, db_map)
                tag_item = self._make_param_tag_item(item, db_map)
                if def_item:
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if tag_item:
                    db_map_param_tag.setdefault(db_map, []).append(tag_item)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if any(db_map_param_tag.values()):
            self.db_mngr.set_parameter_definition_tags(db_map_param_tag)
        self.end_modify_db()

    def _make_parameter_item(self, item, db_map):
        """Returns a parameter definition item that can be inserted into the db or None if
        mandatory keys are missing."""
        item = super()._make_parameter_item(item, db_map)
        # TODO: Try and use _make_parameter_data_id here, the problem seems to be `name` vs `parameter_name`
        if self.entity_class_id_key not in item or "name" not in item:
            return None
        return item


class EmptyObjectParameterDefinitionModel(EmptyParameterDefinitionMixin, ObjectClassFillInMixin, EmptyParameterModel):
    """An empty object parameter definition model."""

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_definitions(db_map, ids=ids)


class EmptyRelationshipParameterDefinitionModel(
    EmptyParameterDefinitionMixin, RelationshipClassFillInMixin, EmptyParameterModel
):
    """An empty relationship parameter definition model."""

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter definitions. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_definitions(db_map, ids=ids)

    def flags(self, index):
        """Small hack so the object_class_name_list is non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] == "object_class_name_list":
            flags &= ~Qt.ItemIsEditable
        return flags


class ObjectFillInMixin(ParameterFillInBase):
    """Provides methods to fill in objects for parameter value items
    edited by the user, so they can be entered in the database.
    """

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_obj_lookup = dict()

    def _make_parameter_data_id(self, item):
        """Returns a unique id from parameter data. Used by receive_parameter_data_added."""
        return (item.get("object_name"), *super()._make_parameter_data_id(item))

    def begin_modify_db(self, db_map_data):
        """Begins an operation to add or update database items.
        Populate the lookup dicts with necessary data needed by the _fill_in methods to work.
        """
        super().begin_modify_db(db_map_data)
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

    def _fill_in_objects(self, item, db_map):
        name = item.pop("object_name", None)
        items = self._db_map_obj_lookup.get(db_map, {}).get(name)
        if not items:
            return
        item["object_ids"] = {x["class_id"]: x["id"] for x in items}

    def _make_parameter_item(self, item, db_map):
        """Returns a parameter item for adding to the database."""
        item = super()._make_parameter_item(item, db_map)
        self._fill_in_objects(item, db_map)
        return item

    def end_modify_db(self):
        """Ends an operation to add or update database items."""
        super().end_modify_db()
        self._db_map_obj_lookup.clear()


class ParameterFillInMixin(ParameterFillInBase):
    """Provides methods to fill in parameters for parameter value items
    edited by the user, so they can be entered in the database."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_param_lookup = dict()

    def begin_modify_db(self, db_map_data):
        """Begins an operation to add or update database items.
        Populate the lookup dicts with necessary data needed by the _fill_in methods to work.
        """
        super().begin_modify_db(db_map_data)
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

    def _fill_in_parameters(self, item, db_map):
        name = item.pop("parameter_name", None)
        items = self._db_map_param_lookup.get(db_map, {}).get(name)
        if not items:
            return
        item["parameter_ids"] = {x["object_class_id"]: x["id"] for x in items}

    def _make_parameter_item(self, item, db_map):
        """Returns a parameter item for adding to the database."""
        item = super()._make_parameter_item(item, db_map)
        self._fill_in_parameters(item, db_map)
        return item

    def end_modify_db(self):
        """Ends an operation to add or update database items."""
        super().end_modify_db()
        self._db_map_param_lookup.clear()


class EmptyParameterValueMixin:
    """Handles parameter values added."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_data_added)

    def _do_add_items_to_db(self, db_map_data):
        """Add items to the database.

        Args:
            db_map_data (dict): maps DiffDatabaseMapping instances to list of model items
        """
        self.begin_modify_db(db_map_data)
        db_map_param_val = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                val_item = self._make_parameter_item(item, db_map)
                if val_item:
                    db_map_param_val.setdefault(db_map, []).append(val_item)
        if any(db_map_param_val.values()):
            self.db_mngr.add_parameter_values(db_map_param_val)
        self.end_modify_db()


class EmptyObjectParameterValueModel(
    EmptyParameterValueMixin, ObjectFillInMixin, ParameterFillInMixin, ObjectClassFillInMixin, EmptyParameterModel
):
    """An empty object parameter value model."""

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_values(db_map, ids=ids)

    def _make_parameter_item(self, item, db_map):
        """Returns a parameter value item for adding to the database or None if mandatory keys are missing."""
        item = super()._make_parameter_item(item, db_map)
        # Here we consolidate
        object_ids = item.pop("object_ids", {})
        parameter_ids = item.pop("parameter_ids", {})
        if "object_class_id" not in item:
            object_class_id = self._infer_object_class_id(set(object_ids.keys()), set(parameter_ids.keys()))
            if not object_class_id:
                return None
            item["object_class_id"] = object_class_id
            object_class_name = self.db_mngr.get_item(db_map, "object class", object_class_id)["name"]
            # TODO: put object class name in model, we need the row or something
        object_class_id = item["object_class_id"]
        object_id = object_ids.get(object_class_id)
        parameter_definition_id = parameter_ids.get(object_class_id)
        if not object_id or not parameter_definition_id:
            return None
        item["object_id"] = object_id
        item["parameter_definition_id"] = parameter_definition_id
        return item

    @staticmethod
    def _infer_object_class_id(object_class_ids_1, object_class_ids_2):
        if not object_class_ids_1:
            object_class_ids = object_class_ids_2
        elif not object_class_ids_2:
            object_class_ids = object_class_ids_1
        else:
            object_class_ids = object_class_ids_1 & object_class_ids_2
        if len(object_class_ids) == 1:
            return object_class_ids.pop()


class EmptyRelationshipParameterValueModel(
    EmptyParameterValueMixin, ParameterFillInMixin, RelationshipClassFillInMixin, EmptyParameterModel
):
    """An empty relationship parameter value model."""

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
