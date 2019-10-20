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

    @property
    def can_be_filtered(self):
        return False

    def accepted_rows(self):
        return list(range(self.rowCount()))

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
        added_ids = set()
        for db_map, items in db_map_data.items():
            ids = {x["id"] for x in items}
            for item in self.get_entity_parameter_data(db_map, ids=ids):
                database = db_map.codename
                unique_id = (database, *self._make_unique_id(item))
                added_ids.add(unique_id)
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
        rows = {ind.row() for ind in indexes}
        self.add_items_to_db(rows)
        return True

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        raise NotImplementedError()

    def _make_db_map_data(self, rows):
        """
        Returns model data grouped by database map.

        Args:
            rows (set): group data from these rows
        """
        items = [dict(zip(self.header, self._main_data[row]), row=row) for row in rows]
        db_map_data = dict()
        for item in items:
            database = item.pop("database")
            db_map = next(iter(x for x in self.db_mngr.db_maps if x.codename == database), None)
            if not db_map:
                continue
            db_map_data.setdefault(db_map, []).append(item)
        return db_map_data


class FillInEntityClassIdMixin(ConvertToDBMixin):
    """Fills in entity class ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_ent_cls_lookup = dict()

    def build_lookup_dictionary(self, db_map_data):
        """Build lookup dictionary."""
        super().build_lookup_dictionary(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                entity_class_name = item.get(self.entity_class_name_key)
                db_map_names.setdefault(db_map, set()).add(entity_class_name)
        # Build lookup dict
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


class EmptyParameterDefinitionModel(
    FillInValueListIdMixin, MakeParameterTagMixin, FillInParameterNameMixin, EmptyParameterModel
):
    """An empty parameter definition model."""

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_data_added)

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        db_map_data = self._make_db_map_data(rows)
        self.build_lookup_dictionary(db_map_data)
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


class FillInEntityIdsMixin(ConvertToDBMixin):
    """Fills in entity ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_ent_lookup = dict()

    def build_lookup_dictionary(self, db_map_data):
        """Build lookup dictionary."""
        super().build_lookup_dictionary(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                name = item.get(self.entity_name_key)
                db_map_names.setdefault(db_map, set()).add(name)
        # Build lookup dict
        self._db_map_ent_lookup.clear()
        for db_map, names in db_map_names.items():
            for name in names:
                items = self.db_mngr.get_items_by_field(db_map, self.entity_type, self.entity_name_key_in_cache, name)
                if items:
                    self._db_map_ent_lookup.setdefault(db_map, {})[name] = items

    def _fill_in_entity_ids(self, item, db_map):
        """Fills in all possible entity ids (as there can be more than one for the same name)
        keyed by entity class id."""
        name = item.pop(self.entity_name_key, None)
        items = self._db_map_ent_lookup.get(db_map, {}).get(name)
        if not items:
            return
        item["entity_ids"] = {x["class_id"]: x["id"] for x in items}

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._fill_in_entity_ids(item, db_map)
        return item


class FillInParameterDefinitionIdsMixin(ConvertToDBMixin):
    """Fills in parameter definition ids."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_param_lookup = dict()

    def build_lookup_dictionary(self, db_map_data):
        """Build lookup dictionary."""
        super().build_lookup_dictionary(db_map_data)
        # Group data by name
        db_map_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                name = item.get("parameter_name")
                db_map_names.setdefault(db_map, set()).add(name)
        # Build lookup dict
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
        item["parameter_ids"] = {x[self.entity_class_id_key]: x["id"] for x in items}

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._fill_in_parameter_ids(item, db_map)
        return item


class InferEntityClassIdMixin(ConvertToDBMixin):
    """Infers object class ids."""

    def _convert_to_db(self, item, db_map):
        """Converts a model item (name-based) into a database item (id-based)."""
        item = super()._convert_to_db(item, db_map)
        self._infer_and_fill_in_entity_class_id(item, db_map)
        return item

    def _infer_and_fill_in_entity_class_id(self, item, db_map):
        """Try and infer the object class id by intersecting object ids and parameter ids previously computed.
        Then pick the correct object id and parameter definition id based on that, and fill everything in.
        Also set the inferred object class name in the model.
        """
        row = item.pop("row")
        entity_ids = item.pop("entity_ids", {})
        parameter_ids = item.pop("parameter_ids", {})
        if self.entity_class_id_key not in item:
            entity_class_ids = {*entity_ids.keys(), *parameter_ids.keys()}
            if len(entity_class_ids) != 1:
                # entity class id not in the item and not inferrable, good bye
                return
            entity_class_id = entity_class_ids.pop()
            item[self.entity_class_id_key] = entity_class_id
            entity_class_name = self.db_mngr.get_item(db_map, self.entity_class_type, entity_class_id)["name"]
            # TODO: Try to find a better place for this, and emit dataChanged
            self._main_data[row][self.header.index(self.entity_class_name_key)] = entity_class_name
        # At this point we're sure the entity_class_id is there
        entity_class_id = item[self.entity_class_id_key]
        entity_id = entity_ids.get(entity_class_id)
        parameter_definition_id = parameter_ids.get(entity_class_id)
        if entity_id:
            item[self.entity_id_key] = entity_id
        if parameter_definition_id:
            item["parameter_definition_id"] = parameter_definition_id


class EmptyParameterValueModel(
    InferEntityClassIdMixin,
    FillInParameterDefinitionIdsMixin,
    FillInEntityIdsMixin,
    FillInEntityClassIdMixin,
    EmptyParameterModel,
):
    """An empty parameter value model."""

    @property
    def entity_type(self):
        """Either 'object' or "relationship'."""
        raise NotImplementedError()

    @property
    def entity_id_key(self):
        return {"object": "object_id", "relationship": "relationship_id"}[self.entity_type]

    @property
    def entity_name_key(self):
        return {"object": "object_name", "relationship": "object_name_list"}[self.entity_type]

    @property
    def entity_name_key_in_cache(self):
        return {"object": "name", "relationship": "object_name_list"}[self.entity_type]

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_data_added)

    def _make_unique_id(self, item):
        """Returns a unique id for the given model item (name-based). Used by receive_parameter_data_added."""
        return (*super()._make_unique_id(item), item.get(self.entity_name_key))

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        db_map_data = self._make_db_map_data(rows)
        self.build_lookup_dictionary(db_map_data)
        db_map_param_val = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                param_val = self._convert_to_db(item, db_map)
                if self._check_item(param_val):
                    db_map_param_val.setdefault(db_map, []).append(param_val)
        if any(db_map_param_val.values()):
            self.db_mngr.add_parameter_values(db_map_param_val)

    def _check_item(self, item):
        """Checks if a db item is ready to be inserted."""
        return self.entity_class_id_key in item and self.entity_id_key in item and "parameter_definition_id" in item


class EmptyObjectParameterValueModel(EmptyParameterValueModel):
    """An empty object parameter value model."""

    @property
    def entity_class_type(self):
        return "object class"

    @property
    def entity_type(self):
        return "object"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns object parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_object_parameter_values(db_map, ids=ids)


class MakeRelationshipOnTheFlyMixin:
    """Makes relationships on the fly."""

    def __init__(self, *args, **kwargs):
        """Init class, create lookup dicts."""
        super().__init__(*args, **kwargs)
        self._db_map_obj_lookup = dict()
        self._db_map_rel_cls_lookup = dict()

    def build_lookup_dictionaries(self, db_map_data):
        """Build object lookup dictionary."""
        # Group data by name
        db_map_object_names = dict()
        db_map_rel_cls_names = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                object_name_list = item.get("object_name_list")
                object_name_list = self._parse_object_name_list(object_name_list)
                if object_name_list:
                    db_map_object_names.setdefault(db_map, set()).update(object_name_list)
                relationship_class_name = item.get("relationship_class_name")
                db_map_rel_cls_names.setdefault(db_map, set()).add(relationship_class_name)
        # Build lookup dicts
        self._db_map_obj_lookup.clear()
        for db_map, names in db_map_object_names.items():
            for name in names:
                item = self.db_mngr.get_item_by_field(db_map, "object", "name", name)
                if item:
                    self._db_map_obj_lookup.setdefault(db_map, {})[name] = item
        self._db_map_rel_cls_lookup.clear()
        for db_map, names in db_map_rel_cls_names.items():
            for name in names:
                item = self.db_mngr.get_item_by_field(db_map, "relationship class", "name", name)
                if item:
                    self._db_map_rel_cls_lookup.setdefault(db_map, {})[name] = item

    def _make_relationship_on_the_fly(self, item, db_map):
        """Gets entity info from model item (name-based) into a relationship database item (id-based)."""
        relationship_class_name = item.get("relationship_class_name")
        relationship_class = self._db_map_rel_cls_lookup.get(db_map, {}).get(relationship_class_name)
        if not relationship_class:
            return None
        object_name_list = item.get("object_name_list")
        object_name_list = self._parse_object_name_list(object_name_list)
        if not object_name_list:
            return None
        object_id_list = []
        for name in object_name_list:
            object_ = self._db_map_obj_lookup.get(db_map, {}).get(name)
            if not object_:
                return None
            object_id_list.append(object_["id"])
        relationship_name = relationship_class_name + "__" + "_".join(object_name_list)
        return {"class_id": relationship_class["id"], "object_id_list": object_id_list, "name": relationship_name}

    @staticmethod
    def _parse_object_name_list(object_name_list):
        try:
            return object_name_list.split(",")
        except AttributeError:
            return None


class EmptyRelationshipParameterValueModel(MakeRelationshipOnTheFlyMixin, EmptyParameterValueModel):
    """An empty relationship parameter value model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    @property
    def entity_type(self):
        return "relationship"

    def get_entity_parameter_data(self, db_map, ids=None):
        """Returns relationship parameter values. Used by receive_parameter_data_added."""
        return self.db_mngr.get_relationship_parameter_values(db_map, ids=ids)

    def connect_db_mngr_signals(self):
        """Connect db mngr signals."""
        super().connect_db_mngr_signals()
        self.db_mngr.relationships_added.connect(self.receive_relationships_added)

    @Slot("QVariant", name="receive_relationships_added")
    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added.
        Finds affected rows and call add_items_to_db."""
        added_ids = set()
        for db_map, items in db_map_data.items():
            for item in items:
                database = db_map.codename
                unique_id = (database, item["class_name"], item["object_name_list"])
                added_ids.add(unique_id)
        affected_rows = set()
        for row, data in enumerate(self._main_data):
            item = dict(zip(self.header, data))
            database = item.get("database")
            unique_id = (database, item["relationship_class_name"], item["object_name_list"])
            if unique_id in added_ids:
                affected_rows.add(row)
        self.add_items_to_db(affected_rows)

    def add_items_to_db(self, rows):
        """Add items to db.

        Args:
            rows (set): add data from these rows
        """
        super().add_items_to_db(rows)  # This will also complete the relationship class name
        # Now we try to add relationships
        db_map_data = self._make_db_map_data(rows)
        self.build_lookup_dictionaries(db_map_data)
        db_map_relationships = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                relationship = self._make_relationship_on_the_fly(item, db_map)
                if relationship:
                    db_map_relationships.setdefault(db_map, []).append(relationship)
        if any(db_map_relationships.values()):
            self.db_mngr.add_relationships(db_map_relationships)
