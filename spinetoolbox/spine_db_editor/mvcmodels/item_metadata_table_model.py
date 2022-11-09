######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains :class:`ItemMetadataTableModel` and associated functionality.

:author: A. Soininen (VTT)
:date:   25.3.2022
"""
from enum import auto, Enum, IntEnum, unique

from PySide2.QtCore import QModelIndex

from spinetoolbox.helpers import rows_to_row_count_tuples, FlexibleFetchParent
from .metadata_table_model_base import Column, FLAGS_EDITABLE, FLAGS_FIXED, MetadataTableModelBase


@unique
class ExtraColumn(IntEnum):
    """Identifiers for hidden table columns."""

    ITEM_METADATA_ID = Column.max() + 1
    METADATA_ID = Column.max() + 2


@unique
class ItemType(Enum):
    """Allowed item types."""

    ENTITY = auto()
    VALUE = auto()


class ItemMetadataTableModel(MetadataTableModelBase):
    """Model for entity and parameter value metadata."""

    _ITEM_NAME_KEY = "metadata_name"
    _ITEM_VALUE_KEY = "metadata_value"

    def __init__(self, db_mngr, db_maps, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_maps (Iterable of DatabaseMappingBase): database maps
            parent (QObject): parent object
        """
        super().__init__(db_mngr, db_maps, parent)
        self._item_type = None
        self._item_ids = {}
        self._entity_metadata_fetch_parent = FlexibleFetchParent(
            "entity_metadata",
            handle_items_added=self.add_item_metadata,
            handle_items_removed=self.remove_item_metadata,
            handle_items_updated=self.update_item_metadata,
        )
        self._parameter_value_metadata_fetch_parent = FlexibleFetchParent(
            "parameter_value_metadata",
            handle_items_added=self.add_item_metadata,
            handle_items_removed=self.remove_item_metadata,
            handle_items_updated=self.update_item_metadata,
        )

    def _fetch_parents(self):
        yield self._entity_metadata_fetch_parent
        yield self._parameter_value_metadata_fetch_parent

    def clear(self):
        """Clears the model."""
        self.beginResetModel()
        self._item_ids = {}
        self._data = []
        self._adder_row = self._make_adder_row(None)
        self.endResetModel()

    @staticmethod
    def _make_hidden_adder_columns():
        """See base class."""
        return [None, None]

    def set_entity_ids(self, db_map_ids):
        """Sets the model to show metadata from given entity.

        Args:
            db_map_ids (dict): mapping from database mapping to entity's id in that database
        """
        metadata = {
            db_map: self._db_mngr.get_entity_metadata(db_map, entity_id) for db_map, entity_id in db_map_ids.items()
        }
        self._reset_metadata(ItemType.ENTITY, db_map_ids, metadata)

    def set_parameter_value_ids(self, db_map_ids):
        """Sets the model to show metadata from given parameter value.

        Args:
            db_map_ids (dict): mapping from database mapping to value's id in that database
        """
        metadata = {
            db_map: self._db_mngr.get_parameter_value_metadata(db_map, id_) for db_map, id_ in db_map_ids.items()
        }
        self._reset_metadata(ItemType.VALUE, db_map_ids, metadata)

    def _reset_metadata(self, item_type, db_map_ids, metadata):
        """Resets model.

        Args:
            item_type (ItemType): current item type
            db_map_ids (dict): mapping from database mapping to value's id in that database
            metadata (dict): mapping from database mapping to metadata records
        """
        self.beginResetModel()
        self._item_type = item_type
        self._item_ids = dict(db_map_ids)
        self._db_maps = set(db_map_ids.keys())
        default_db_map = next(iter(self._db_maps)) if self._db_maps else None
        self._adder_row = self._make_adder_row(default_db_map)
        self._data = [
            [record.metadata_name, record.metadata_value, db_map, record.id, record.metadata_id]
            for db_map, records in metadata.items()
            for record in records
        ]
        if db_map_ids:
            db_map = next(iter(db_map_ids))
        elif self._db_maps:
            db_map = next(iter(self._db_maps))
        else:
            db_map = None
        self._adder_row = self._make_adder_row(db_map)
        self.endResetModel()

    def _add_data_to_db_mngr(self, name, value, db_map):
        """See base class."""
        item_id = self._item_ids[db_map]
        if self._item_type == ItemType.ENTITY:
            self._db_mngr.add_entity_metadata(
                {db_map: [{"entity_id": item_id, "metadata_name": name, "metadata_value": value}]}
            )
        else:
            self._db_mngr.add_parameter_value_metadata(
                {db_map: [{"parameter_value_id": item_id, "metadata_name": name, "metadata_value": value}]}
            )

    def _update_data_in_db_mngr(self, id_, name, value, db_map):
        """See base class"""
        if self._item_type == ItemType.ENTITY:
            self._db_mngr.update_entity_metadata(
                {db_map: [{"id": id_, "metadata_name": name, "metadata_value": value}]}
            )
        else:
            self._db_mngr.update_parameter_value_metadata(
                {db_map: [{"id": id_, "metadata_name": name, "metadata_value": value}]}
            )

    def rollback(self, db_maps):
        """Rolls back changes in database.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): database mappings that have been rolled back
        """
        spans = rows_to_row_count_tuples(
            i for db_map in db_maps for i, row in enumerate(self._data) if row[Column.DB_MAP] == db_map
        )
        for span in spans:
            first = span[0]
            last = span[0] + span[1] - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            self._data = self._data[:first] + self._data[last + 1 :]
            self.endRemoveRows()
        if self._item_type == ItemType.ENTITY:
            get_item_metadata = self._db_mngr.get_entity_metadata
        else:
            get_item_metadata = self._db_mngr.get_parameter_value_metadata
        metadata = {}
        for db_map in db_maps:
            id_ = self._item_ids.get(db_map)
            if id_ is None:
                continue
            metadata.update({db_map: get_item_metadata(db_map, id_)})
        if not metadata:
            return
        rolled_back_data = [
            [record.metadata_name, record.metadata_value, db_map, record.id, record.metadata_id]
            for db_map, records in metadata.items()
            for record in records
        ]
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data) + len(rolled_back_data) - 1)
        self._data += rolled_back_data
        self.endInsertRows()

    def flags(self, index):
        row = index.row()
        column = index.column()
        if column == Column.DB_MAP and row < len(self._data):
            data_row = self._data[row]
            if data_row[ExtraColumn.ITEM_METADATA_ID] is not None and data_row[ExtraColumn.METADATA_ID] is not None:
                return FLAGS_FIXED
        return FLAGS_EDITABLE

    @staticmethod
    def _ids_from_added_item(item):
        """See base class."""
        return item["id"], item["metadata_id"]

    @staticmethod
    def _extra_cells_from_added_item(item):
        """See base class."""
        return [item["id"], item["metadata_id"]]

    def _set_extra_columns(self, row, ids):
        """See base class."""
        row[ExtraColumn.ITEM_METADATA_ID] = ids[0]
        row[ExtraColumn.METADATA_ID] = ids[1]

    def _database_table_name(self):
        """See base class"""
        return "entity_metadata" if self._item_type == ItemType.ENTITY else "parameter_value_metadata"

    def _row_id(self, row):
        """See base class."""
        return row[ExtraColumn.ITEM_METADATA_ID]

    def add_item_metadata(self, db_map_data):
        """Adds new item metadata from database manager to the model.

        Args:
            db_map_data (dict): added items keyed by database mapping
        """
        self._add_data(db_map_data)

    def update_item_metadata(self, db_map_data):
        """Updates item metadata in model after it has been updated in databases.

        Args:
            db_map_data (dict): updated metadata records
        """
        for db_map, items in db_map_data.items():
            for item in items:
                for row in self._data:
                    if db_map != row[Column.DB_MAP] or item["id"] != row[ExtraColumn.ITEM_METADATA_ID]:
                        continue
                    row[ExtraColumn.METADATA_ID] = item["metadata_id"]
                    break

    def remove_item_metadata(self, db_map_data):
        """Removes item metadata from model after it has been removed from databases.

        Args:
            db_map_data (dict): removed items keyed by database mapping
        """
        self._remove_data(db_map_data, ExtraColumn.ITEM_METADATA_ID)
