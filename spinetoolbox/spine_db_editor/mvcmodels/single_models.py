######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Single models for parameter definitions and values (as 'for a single entity')."""
from PySide6.QtCore import Qt
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, plain_to_rich
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ..mvcmodels.single_and_empty_model_mixins import SplitValueAndTypeMixin, MakeEntityOnTheFlyMixin
from ...mvcmodels.shared import PARSED_ROLE, DB_MAP_ROLE
from .colors import FIXED_FIELD_COLOR


class HalfSortedTableModel(MinimalTableModel):
    def reset_model(self, main_data=None):
        """Reset model."""
        if main_data is None:
            main_data = []
        self.beginResetModel()
        self._main_data = sorted(main_data, key=self._sort_key)
        self.endResetModel()

    def add_rows(self, data):
        data = [item for item in data if item not in self._main_data]
        if not data:
            return
        self.beginResetModel()
        self._main_data += data
        self._main_data.sort(key=self._sort_key)
        self.endResetModel()

    def _sort_key(self, element):
        return element


class SingleModelBase(HalfSortedTableModel):
    """Base class for all single models that go in a CompoundModelBase subclass."""

    def __init__(self, parent, db_map, entity_class_id, committed, lazy=False):
        """Init class.

        Args:
            parent (CompoundModelBase): the parent model
            db_map (DatabaseMapping)
            entity_class_id (int)
            committed (bool)
        """
        super().__init__(parent=parent, header=parent.header, lazy=lazy)
        self.db_mngr = parent.db_mngr
        self.db_map = db_map
        self.entity_class_id = entity_class_id
        self._auto_filter = {}  # Maps field to accepted ids for that field
        self.committed = committed

    def __lt__(self, other):
        if self.entity_class_name == other.entity_class_name:
            return self.db_map.codename < other.db_map.codename
        return self.entity_class_name < other.entity_class_name

    @property
    def item_type(self):
        """The DB item type, required by the data method."""
        raise NotImplementedError()

    @property
    def field_map(self):
        return self._parent.field_map

    def update_items_in_db(self, items):
        """Update items in db. Required by batch_set_data"""
        items_to_upd = []
        error_log = []
        for item in items:
            item_to_upd, errors = self._convert_to_db(item)
            if tuple(item_to_upd.keys()) != ("id",):
                items_to_upd.append(item_to_upd)
            if errors:
                error_log += errors
        if items_to_upd:
            self._do_update_items_in_db({self.db_map: items_to_upd})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})

    @property
    def _references(self):
        raise NotImplementedError()

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, "entity_class", self.entity_class_id)["name"]

    @property
    def dimension_id_list(self):
        return self.db_mngr.get_item(self.db_map, "entity_class", self.entity_class_id)["dimension_id_list"]

    @property
    def fixed_fields(self):
        return ["entity_class_name", "database"]

    @property
    def group_fields(self):
        return ["entity_byname"]

    @property
    def can_be_filtered(self):
        return True

    def _mapped_field(self, field):
        return self.field_map.get(field, field)

    def item_id(self, row):
        """Returns parameter id for row.

        Args:
            row (int): row index

        Returns:
            int: parameter id
        """
        return self._main_data[row]

    def item_ids(self):
        """Returns model's parameter ids.

        Returns:
            set of int: ids
        """
        return set(self._main_data)

    def db_item(self, index):
        return self._db_item(index.row())

    def _db_item(self, row):
        id_ = self._main_data[row]
        return self.db_item_from_id(id_)

    def db_item_from_id(self, id_):
        return self.db_mngr.get_item(self.db_map, self.item_type, id_)

    def db_items(self):
        return [self._db_item(row) for row in range(self.rowCount())]

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] in self.fixed_fields:
            return flags & ~Qt.ItemIsEditable
        return flags

    def _filter_accepts_row(self, row):
        item = self.db_mngr.get_item(self.db_map, self.item_type, self._main_data[row])
        return self.filter_accepts_item(item)

    def filter_accepts_item(self, item):
        return self._auto_filter_accepts_item(item)

    def set_auto_filter(self, field, values):
        if values == self._auto_filter.get(field, set()):
            return False
        self._auto_filter[field] = values
        return True

    def _auto_filter_accepts_item(self, item):
        """Returns the result of the auto filter."""
        if self._auto_filter is None:
            return False
        for field, values in self._auto_filter.items():
            if values and item.get(field) not in values:
                return False
        return True

    def accepted_rows(self):
        """Yields accepted rows, for convenience."""
        for row in range(self.rowCount()):
            if self._filter_accepts_row(row):
                yield row

    def _get_ref(self, db_item, field):
        """Returns the item referred by the given field."""
        ref = self._references.get(field)
        if ref is None:
            return {}
        src_id_key, ref_type = ref
        ref_if = db_item.get(src_id_key)
        return self.db_mngr.get_item(self.db_map, ref_type, ref_if)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        field = self.header[index.column()]
        if role == Qt.ItemDataRole.BackgroundRole and field in self.fixed_fields:
            return FIXED_FIELD_COLOR
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole):
            if field == "database":
                return self.db_map.codename
            id_ = self._main_data[index.row()]
            item = self.db_mngr.get_item(self.db_map, self.item_type, id_)
            if role == Qt.ItemDataRole.ToolTipRole:
                description = self._get_ref(item, field).get("description")
                if description:
                    return plain_to_rich(description)
            mapped_field = self._mapped_field(field)
            data = item.get(mapped_field)
            if data and field in self.group_fields:
                data = DB_ITEM_SEPARATOR.join(data)
            return data
        if role == Qt.ItemDataRole.DecorationRole and field == "entity_class_name":
            return self.db_mngr.entity_class_icon(self.db_map, self.entity_class_id)
        if role == DB_MAP_ROLE:
            return self.db_map
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Sets data directly in database using db mngr. If successful, updated data will be
        automatically seen by the data method.
        """

        def split_value(value, column):
            if self.header[column] in self.group_fields:
                return tuple(value.split(DB_ITEM_SEPARATOR))
            return value

        if not indexes or not data:
            return False
        row_data = {}
        for index, value in zip(indexes, data):
            row_data.setdefault(index.row(), {})[self.header[index.column()]] = split_value(value, index.column())
        items = [dict(id=self._main_data[row], **data) for row, data in row_data.items()]
        self.update_items_in_db(items)
        return True


class FilterEntityAlternativeMixin:
    """Provides the interface to filter by entity and alternative."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_alternative_ids = set()
        self._filter_entity_ids = set()

    def set_filter_entity_ids(self, db_map_class_entity_ids):
        # Don't accept entity id filters from entities that don't belong in this model
        filter_entity_ids = set().union(
            *(
                ent_ids
                for (db_map, class_id), ent_ids in db_map_class_entity_ids.items()
                if db_map == self.db_map and (class_id == self.entity_class_id or class_id in self.dimension_id_list)
            )
        )
        if self._filter_entity_ids == filter_entity_ids:
            return False
        self._filter_entity_ids = filter_entity_ids
        return True

    def set_filter_alternative_ids(self, db_map_alternative_ids):
        alternative_ids = db_map_alternative_ids.get(self.db_map, set())
        if self._filter_alternative_ids == alternative_ids:
            return False
        self._filter_alternative_ids = alternative_ids
        return True

    def filter_accepts_item(self, item):
        """Reimplemented to also account for the entity and alternative filter."""
        return (
            super().filter_accepts_item(item)
            and self._entity_filter_accepts_item(item)
            and self._alternative_filter_accepts_item(item)
        )

    def _entity_filter_accepts_item(self, item):
        """Returns the result of the entity filter."""
        if not self._filter_entity_ids:  # If no entities are selected, only entity classes
            return True
        entity_id = item[self._mapped_field("entity_id")]
        return entity_id in self._filter_entity_ids or bool(set(item["element_id_list"]) & self._filter_entity_ids)

    def _alternative_filter_accepts_item(self, item):
        """Returns the result of the alternative filter."""
        if not self._filter_alternative_ids:
            return True
        alternative_id = item.get("alternative_id")
        return alternative_id is None or alternative_id in self._filter_alternative_ids


class ParameterMixin:
    """Provides the data method for parameter values and definitions."""

    @property
    def value_field(self):
        return {"parameter_definition": "default_value", "parameter_value": "value"}[self.item_type]

    @property
    def parameter_definition_id_key(self):
        return {"parameter_definition": "id", "parameter_value": "parameter_id"}[self.item_type]

    @property
    def _references(self):
        return {
            "entity_class_name": ("entity_class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "parameter_name": (self.parameter_definition_id_key, "parameter_definition"),
            "value_list_name": ("value_list_id", "parameter_value_list"),
            "description": ("id", "parameter_definition"),
            "value": ("id", "parameter_value"),
            "default_value": ("id", "parameter_definition"),
            "database": ("database", None),
            "alternative_name": ("alternative_id", "alternative"),
        }

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Gets the id and database for the row, and reads data from the db manager
        using the item_type property.
        Paint the object_class icon next to the name.
        Also paint background of fixed indexes gray and apply custom format to JSON fields."""
        field = self.header[index.column()]
        # Display, edit, tool tip, alignment role of 'value fields'
        if field == self.value_field and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.ToolTipRole,
            Qt.TextAlignmentRole,
            PARSED_ROLE,
        ):
            id_ = self._main_data[index.row()]
            return self.db_mngr.get_value(self.db_map, self.item_type, id_, role)
        return super().data(index, role)


class EntityMixin:
    def update_items_in_db(self, items):
        """Overriden to create entities on the fly first."""
        for item in items:
            item["entity_class_name"] = self.entity_class_name
        entities = []
        error_log = []
        for item in items:
            entity, errors = self._make_entity_on_the_fly(item, self.db_map)
            if entity:
                entities.append(entity)
            if errors:
                error_log.extend(errors)
        if entities:
            self.db_mngr.add_entities({self.db_map: entities})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})
        super().update_items_in_db(items)

    def _do_update_items_in_db(self, db_map_data):
        raise NotImplementedError()


class SingleParameterDefinitionModel(SplitValueAndTypeMixin, ParameterMixin, SingleModelBase):
    """A parameter_definition model for a single entity_class."""

    @property
    def item_type(self):
        return "parameter_definition"

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        return item.get("name", "")

    def _do_update_items_in_db(self, db_map_data):
        self.db_mngr.update_parameter_definitions(db_map_data)


class SingleParameterValueModel(
    MakeEntityOnTheFlyMixin,
    SplitValueAndTypeMixin,
    ParameterMixin,
    EntityMixin,
    FilterEntityAlternativeMixin,
    SingleModelBase,
):
    """A parameter_value model for a single entity_class."""

    @property
    def item_type(self):
        return "parameter_value"

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        return (item.get("entity_byname", ()), item.get("parameter_name", ""), item.get("alternative_name", ""))

    def _do_update_items_in_db(self, db_map_data):
        self.db_mngr.update_parameter_values(db_map_data)


class SingleEntityAlternativeModel(MakeEntityOnTheFlyMixin, EntityMixin, FilterEntityAlternativeMixin, SingleModelBase):
    """An entity_alternative model for a single entity_class."""

    @property
    def item_type(self):
        return "entity_alternative"

    def _sort_key(self, element):
        item = self.db_item_from_id(element)
        return (item.get("entity_byname", ()), item.get("alternative_name", ""))

    @property
    def _references(self):
        return {
            "entity_class_name": ("entity_class_id", "entity_class"),
            "entity_byname": ("entity_id", "entity"),
            "alternative_name": ("alternative_id", "alternative"),
            "database": ("database", None),
        }

    def _do_update_items_in_db(self, db_map_data):
        self.db_mngr.update_entity_alternatives(db_map_data)
