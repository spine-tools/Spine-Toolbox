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
Contains :class:`MetadataTableModel` and associated functionality.
"""
from enum import IntEnum, unique
from PySide6.QtCore import QModelIndex, Qt
from spinetoolbox.helpers import rows_to_row_count_tuples
from spinetoolbox.fetch_parent import FlexibleFetchParent
from .metadata_table_model_base import Column, FLAGS_FIXED, FLAGS_EDITABLE, MetadataTableModelBase


@unique
class ExtraColumn(IntEnum):
    """Identifiers for hidden table columns."""

    ID = Column.max() + 1


class MetadataTableModel(MetadataTableModelBase):
    """Model for metadata."""

    _ITEM_NAME_KEY = "name"
    _ITEM_VALUE_KEY = "value"

    def __init__(self, db_mngr, db_maps, db_editor):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_maps (Iterable of DatabaseMappingBase): database maps
            db_editor (SpineDBEditor): DB editor
        """
        super().__init__(db_mngr, db_maps, db_editor)
        self._metadata_fetch_parent = FlexibleFetchParent(
            "metadata",
            handle_items_added=self.add_metadata,
            handle_items_removed=self.remove_metadata,
            handle_items_updated=self.update_metadata,
            owner=self,
        )

    @staticmethod
    def _make_hidden_adder_columns():
        """See base class."""
        return [None]

    def _add_data_to_db_mngr(self, name, value, db_map):
        """See base class."""
        self._db_mngr.add_metadata({db_map: [{"name": name, "value": value}]})

    def _update_data_in_db_mngr(self, id_, name, value, db_map):
        """See base class"""
        self._db_mngr.update_metadata({db_map: [{"id": id_, "name": name, "value": value}]})

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
        if self.canFetchMore(QModelIndex()):
            self.fetchMore(QModelIndex())

    def _database_table_name(self):
        """See base class"""
        return "metadata"

    def _row_id(self, row):
        """See base class."""
        return row[ExtraColumn.ID]

    def flags(self, index):
        row = index.row()
        column = index.column()
        if column == Column.DB_MAP and row < len(self._data) and self._data[row][ExtraColumn.ID] is not None:
            return FLAGS_FIXED
        return FLAGS_EDITABLE

    def _fetch_parents(self):
        yield self._metadata_fetch_parent

    @staticmethod
    def _ids_from_added_item(item):
        """See base class."""
        return item["id"]

    @staticmethod
    def _extra_cells_from_added_item(item):
        """See base class."""
        return [item["id"]]

    def _set_extra_columns(self, row, ids):
        """See base class."""
        row[ExtraColumn.ID] = ids

    def add_metadata(self, db_map_data):
        """Adds new metadata from database manager to the model.

        Args:
            db_map_data (dict): added metadata items keyed by database mapping
        """
        self._add_data(db_map_data)

    def update_metadata(self, db_map_data):
        """Updates model according to data received from database manager.

        Args:
            db_map_data (dict): updated metadata items keyed by database mapping
        """
        for items in db_map_data.values():
            items_by_id = {item["id"]: item for item in items}
            updated_rows = []
            for row_index, row in enumerate(self._data):
                if row[ExtraColumn.ID] is None:
                    continue
                db_item = items_by_id.get(row[ExtraColumn.ID])
                if db_item is None:
                    continue
                if row[Column.NAME] != db_item["name"]:
                    row[Column.NAME] = db_item["name"]
                    updated_rows.append(row_index)
                if row[Column.VALUE] != db_item["value"]:
                    row[Column.VALUE] = db_item["value"]
                    updated_rows.append(row_index)
            if updated_rows:
                top_left = self.index(updated_rows[0], 0)
                bottom_right = self.index(updated_rows[-1], Column.DB_MAP - 1)
                self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def remove_metadata(self, db_map_data):
        """Removes metadata from model after it has been removed from databases.

        Args:
            db_map_data (dict): removed items keyed by database mapping
        """
        self._remove_data(db_map_data, ExtraColumn.ID)
