######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

:author: A. Soininen (VTT)
:date:   7.2.2022
"""
from enum import IntEnum, unique
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from spinetoolbox.helpers import rows_to_row_count_tuples, FetchParent
from .colors import FIXED_FIELD_COLOR


@unique
class Column(IntEnum):
    """Identifiers for table columns."""

    NAME = 0
    VALUE = 1
    DB_MAP = 2
    ID = 3


HEADER = "name", "value", "db_map"
FLAGS_FIXED = Qt.ItemIsEnabled | Qt.ItemIsSelectable
FLAGS_EDITABLE = FLAGS_FIXED | Qt.ItemIsEditable


class MetadataTableModel(QAbstractTableModel, FetchParent):
    """Model for metadata."""

    msg_error = Signal(str)

    def __init__(self, db_mngr, db_maps, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_maps (Iterable of DatabaseMappingBase): database maps
            parent (QObject): parent object
        """
        super().__init__(parent)
        self._db_mngr = db_mngr
        self._data = []
        self._db_maps = db_maps
        default_db_map = next(iter(db_maps)) if db_maps else None
        self._adder_row = self._make_adder_row(default_db_map)

    @staticmethod
    def _make_adder_row(default_db_map):
        return ["", "", default_db_map, None]

    def set_db_maps(self, db_maps):
        self.beginResetModel()
        self._db_maps = db_maps
        new_data = [row for row in self._data if row[Column.DB_MAP] in db_maps]
        self._data = new_data
        default_db_map = next(iter(db_maps)) if db_maps else None
        self._adder_row = self._make_adder_row(default_db_map)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data) + 1

    def columnCount(self, parent=QModelIndex()):
        return 3

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column == Column.DB_MAP:
                db_map = self._data[row][column] if row < len(self._data) else self._adder_row[column]
                return db_map.codename if db_map is not None else ""
            return self._data[row][column] if row < len(self._data) else self._adder_row[column]
        if (
            role == Qt.BackgroundRole
            and column == Column.DB_MAP
            and row < len(self._data)
            and self._data[row][Column.ID] is not None
        ):
            return FIXED_FIELD_COLOR
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        return HEADER[section]

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        column = index.column()
        row = index.row()
        data_length = len(self._data)
        target_row = self._data[row] if row < data_length else self._adder_row
        if column == Column.DB_MAP:
            match = None
            for db_map in self._db_maps:
                if value == db_map.codename:
                    match = db_map
                    break
            value = match
        if value == target_row[column]:
            return False
        reserved = self._reserved_metadata()
        previous_value = target_row[column]
        target_row[column] = value
        name = target_row[Column.NAME]
        value = target_row[Column.VALUE]
        db_map = target_row[Column.DB_MAP]
        if not name or not value or db_map is None:
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        if reserved.get(db_map, {}).get(name) == value:
            target_row[column] = previous_value
            self.msg_error.emit("Duplicate metadata name and value.")
            return False
        id_ = target_row[Column.ID]
        if id_ is not None:
            self._db_mngr.update_metadata({db_map: [{"id": id_, "name": name, "value": value}]})
            return True
        self._db_mngr.add_metadata({db_map: [{"name": name, "value": value}]})
        if row == data_length:
            if db_map is None:
                db_map = next(iter(self._db_maps)) if self._db_maps else None
            self._adder_row = self._make_adder_row(db_map)
            top_left = self.index(data_length, 0)
            bottom_right = self.index(data_length, Column.DB_MAP)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
        return True

    def batch_set_data(self, indexes, values):
        rows = []
        columns = []
        previous_values = []
        data_length = len(self._data)
        available_codenames = {db_map.codename for db_map in self._db_maps}
        reserved = self._reserved_metadata()
        for index, value in zip(indexes, values):
            column = index.column()
            if column == Column.DB_MAP and value not in available_codenames:
                continue
            row = index.row()
            data_row = self._data[row] if row < data_length else self._adder_row
            previous_values.append(data_row[column])
            data_row[column] = value
            rows.append(row)
            columns.append(column)
        metadata_to_add = {}
        metadata_to_update = {}
        duplicates_found = False
        for i, row in enumerate(rows):
            data_row = self._data[row] if row < data_length else self._adder_row
            name = data_row[Column.NAME]
            if not name:
                continue
            value = data_row[Column.VALUE]
            if not value:
                continue
            db_map = data_row[Column.DB_MAP]
            if db_map is None:
                continue
            if reserved.get(db_map, {}).get(name) == value:
                data_row[columns[i]] = previous_values[i]
                duplicates_found = True
                continue
            if row == data_length:
                self._adder_row = self._make_adder_row(db_map)
            id_ = data_row[Column.ID]
            if id_ is not None:
                metadata_to_update.setdefault(db_map, []).append({"name": name, "value": value, "id": id_})
            else:
                metadata_to_add.setdefault(db_map, []).append({"name": name, "value": value})
        if metadata_to_add:
            self._db_mngr.add_metadata(metadata_to_add)
        if metadata_to_update:
            self._db_mngr.update_metadata(metadata_to_update)
        if rows:
            top_left = self.index(min(rows), min(columns))
            bottom_right = self.index(max(rows), max(columns))
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
        if duplicates_found:
            self.msg_error.emit("Duplicate metadata names and values.")

    def roll_back(self, db_maps):
        spans = rows_to_row_count_tuples(
            i for db_map in db_maps for i, row in enumerate(self._data) if row[Column.DB_MAP] == db_map
        )
        for span in spans:
            first = span[0]
            last = span[0] + span[1] - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            self._data = self._data[:first] + self._data[last + 1 :]
            self.endRemoveRows()
        self.fetchMore(QModelIndex())

    def insertRows(self, row, count, parent=QModelIndex()):
        row = min(row, len(self._data))
        if self._data:
            db_map_row = row - 1 if row > 0 else 0
            db_map = self._data[db_map_row][Column.DB_MAP]
        else:
            db_map = next(iter(self._db_maps)) if self._db_maps else None
        added = [["", "", db_map, None] for _ in range(count)]
        self.beginInsertRows(parent, row, row + count - 1)
        self._data = self._data[:row] + added + self._data[row:]
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if row == len(self._data):
            return False
        count = min(count, len(self._data) - row)
        ids_to_remove = {}
        for i, row in enumerate(self._data[row : row + count]):
            if row[Column.ID] is not None:
                ids_to_remove.setdefault(row[Column.DB_MAP], {}).setdefault("metadata", set()).add(row[Column.ID])
            else:
                self.beginRemoveRows(parent, i, i + count - 1)
                del self._data[i]
                self.endRemoveRows()
        if ids_to_remove:
            self._db_mngr.remove_items(ids_to_remove)
        return True

    def flags(self, index):
        row = index.row()
        column = index.column()
        if column == Column.DB_MAP and row < len(self._data) and self._data[row][Column.ID] is not None:
            return FLAGS_FIXED
        return FLAGS_EDITABLE

    @property
    def fetch_item_type(self):
        return "metadata"

    def canFetchMore(self, _):
        return any(self._db_mngr.can_fetch_more(db_map, self) for db_map in self._db_maps)

    def fetchMore(self, _):
        for db_map in self._db_maps:
            self._db_mngr.fetch_more(db_map, self)

    def add_metadata(self, db_map_data):
        """Adds new metadata from database manager to the model."""
        id_update_rows = set()
        for db_map, items in db_map_data.items():
            ids = {}
            for item in items:
                ids.setdefault(item["name"], {})[item["value"]] = item["id"]
            for i, row in enumerate(self._data):
                if row[Column.DB_MAP] != db_map:
                    continue
                id_ = ids.get(row[Column.NAME], {}).pop(row[Column.VALUE], None)
                if id_ is None:
                    continue
                row[Column.ID] = id_
                id_update_rows.add(i)
            ids_to_insert = {id_ for ids_by_name in ids.values() for id_ in ids_by_name.values()}
            if ids_to_insert:
                added = [[i["name"], i["value"], db_map, i["id"]] for i in items if i["id"] in ids_to_insert]
                first = len(self._data)
                self.beginInsertRows(QModelIndex(), first, first + len(added) - 1)
                self._data += added
                self.endInsertRows()
        if id_update_rows:
            top_left = self.index(min(id_update_rows), Column.DB_MAP)
            bottom_right = self.index(max(id_update_rows), Column.DB_MAP)
            self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

    def update_metadata(self, db_map_data):
        for db_map, items in db_map_data.items():
            items_by_id = {item["id"]: item for item in items}
            updated_rows = []
            for row_index, row in enumerate(self._data):
                if row[Column.ID] is None:
                    continue
                db_item = items_by_id.get(row[Column.ID])
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
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    def remove_metadata(self, db_map_data):
        for db_map, items in db_map_data.items():
            ids_to_remove = {item["id"] for item in items}
            removed_rows = []
            for row_index, row in enumerate(self._data):
                if row[Column.ID] is None:
                    continue
                if row[Column.ID] not in ids_to_remove:
                    continue
                removed_rows.append(row_index)
            if removed_rows:
                spans = rows_to_row_count_tuples(removed_rows)
                for row, count in spans:
                    self.beginRemoveRows(QModelIndex(), row, row + count - 1)
                    self._data = self._data[:row] + self._data[row + count :]
                    self.endRemoveRows()

    def sort(self, column, order=Qt.AscendingOrder):
        if not self._data or column < 0:
            return
        self._data.sort(key=lambda row: row[column], reverse=order == Qt.DescendingOrder)
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._data) - 1, Column.DB_MAP)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    def _reserved_metadata(self):
        reserved = {}
        for row in self._data:
            db_map = row[Column.DB_MAP]
            if db_map is None:
                continue
            name = row[Column.NAME]
            if not name:
                continue
            value = row[Column.VALUE]
            if not value:
                continue
            reserved.setdefault(db_map, {})[name] = value
        return reserved
