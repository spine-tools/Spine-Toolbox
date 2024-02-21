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

"""Contains base class for metadata table models associated functionality."""
from enum import IntEnum, unique
from operator import itemgetter
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from spinetoolbox.helpers import rows_to_row_count_tuples
from .colors import FIXED_FIELD_COLOR


@unique
class Column(IntEnum):
    """Identifiers for visible table columns."""

    NAME = 0
    VALUE = 1
    DB_MAP = 2

    @staticmethod
    def max():
        return max(c for c in Column)


FLAGS_FIXED = Qt.ItemIsEnabled | Qt.ItemIsSelectable
FLAGS_EDITABLE = FLAGS_FIXED | Qt.ItemIsEditable


class MetadataTableModelBase(QAbstractTableModel):
    """Base for metadata table models"""

    msg_error = Signal(str)
    """Emitted when an error occurs."""

    _HEADER = "name", "value", "database"
    _ITEM_NAME_KEY = None
    _ITEM_VALUE_KEY = None

    def __init__(self, db_mngr, db_maps, db_editor):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_maps (Iterable of DatabaseMapping): database maps
            db_editor (SpineDBEditor): DB editor
        """
        super().__init__(db_editor)
        self._db_editor = db_editor
        self._db_mngr = db_mngr
        self._data = []
        self._db_maps = db_maps
        default_db_map = next(iter(db_maps)) if db_maps else None
        self._adder_row = self._make_adder_row(default_db_map)

    @classmethod
    def _make_adder_row(cls, default_db_map):
        """Generates a new empty last row.

        Args:
            default_db_map (DiffDatabaseMapping): initial database mapping

        Returns:
            list: empty row
        """
        return (len(cls._HEADER) - 1) * [""] + [default_db_map] + cls._make_hidden_adder_columns()

    @staticmethod
    def _make_hidden_adder_columns():
        """Creates hidden extra columns for adder row.

        Returns:
            list: extra columns
        """
        raise NotImplementedError()

    def set_db_maps(self, db_maps):
        """Changes current database mappings.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): database mappings
        """
        self.beginResetModel()
        self._db_maps = db_maps
        new_data = [row for row in self._data if row[Column.DB_MAP] in db_maps]
        self._data = new_data
        default_db_map = next(iter(db_maps)) if db_maps else None
        self._adder_row = self._make_adder_row(default_db_map)
        self.endResetModel()

    def _fetch_parents(self):
        """Yields fetch parents for this model.

        Yields:
            FetchParent
        """
        raise NotImplementedError()

    def canFetchMore(self, _):
        result = False
        for fetch_parent in self._fetch_parents():
            for db_map in self._db_maps:
                result |= self._db_mngr.can_fetch_more(db_map, fetch_parent)
        return result

    def fetchMore(self, _):
        for parent in self._fetch_parents():
            for db_map in self._db_maps:
                self._db_mngr.fetch_more(db_map, parent)

    def rowCount(self, parent=QModelIndex()):
        return len(self._data) + 1

    def columnCount(self, parent=QModelIndex()):
        return len(self._HEADER)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.ItemDataRole.DisplayRole:
            if column == Column.DB_MAP:
                db_map = self._data[row][column] if row < len(self._data) else self._adder_row[column]
                return db_map.codename if db_map is not None else ""
            return self._data[row][column] if row < len(self._data) else self._adder_row[column]
        if (
            role == Qt.ItemDataRole.BackgroundRole
            and column == Column.DB_MAP
            and row < len(self._data)
            and self._row_id(self._data[row]) is not None
        ):
            return FIXED_FIELD_COLOR
        return None

    def _add_data_to_db_mngr(self, name, value, db_map):
        """Tells database manager to start adding data.

        Args:
            name (str): metadata name
            value (str): metadata value
            db_map (DiffDatabaseMapping): database mapping
        """
        raise NotImplementedError()

    def _update_data_in_db_mngr(self, id_, name, value, db_map):
        """Tells database manager to start updating data.

        Args:
            id_ (int): database id
            name (str): metadata name
            value (str): metadata value
            db_map (DiffDatabaseMapping): database mapping
        """
        raise NotImplementedError()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return False
        column = index.column()
        row = index.row()
        data_length = len(self._data)
        target_row = self._data[row] if row < data_length else self._adder_row
        if column == Column.DB_MAP:
            value = self._find_db_map(value)
        if value == target_row[column]:
            return False
        previous_value = target_row[column]
        reserved = self._reserved_metadata()
        target_row[column] = value
        name = target_row[Column.NAME]
        metadata_value = target_row[Column.VALUE]
        db_map = target_row[Column.DB_MAP]
        if not name or not metadata_value or db_map is None:
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        if reserved.get(db_map, {}).get(name) == metadata_value:
            target_row[column] = previous_value
            self.msg_error.emit("Duplicate metadata name and value.")
            return False
        id_ = self._row_id(target_row)
        if id_ is not None:
            self._update_data_in_db_mngr(id_, name, metadata_value, db_map)
            return True
        self._add_data_to_db_mngr(name, metadata_value, db_map)
        if row == data_length:
            if db_map is None:
                db_map = next(iter(self._db_maps)) if self._db_maps else None
            self._adder_row = self._make_adder_row(db_map)
            top_left = self.index(data_length, 0)
            bottom_right = self.index(data_length, Column.DB_MAP)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
        return True

    def batch_set_data(self, indexes, values):
        """Sets data in multiple indexes simultaneously.

        Args:
            indexes (Iterable of QModelIndex): indexes to set
            values (Iterable of str): values corresponding to indexes
        """
        rows = []
        columns = []
        previous_values = []
        data_length = len(self._data)
        available_codenames = {db_map.codename: db_map for db_map in self._db_maps}
        reserved = self._reserved_metadata()
        for index, value in zip(indexes, values):
            if not self.flags(index) & Qt.ItemIsEditable:
                continue
            if value is None:
                value = ""
            column = index.column()
            if column == Column.DB_MAP:
                db_map = available_codenames.get(value)
                if db_map is None:
                    continue
                value = db_map
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
            id_ = self._row_id(data_row)
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
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
        if duplicates_found:
            self.msg_error.emit("Duplicate metadata names and values.")

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._HEADER[section]

    def insertRows(self, row, count, parent=QModelIndex()):
        row = min(row, len(self._data))
        if self._data:
            db_map_row = row - 1 if row > 0 else 0
            db_map = self._data[db_map_row][Column.DB_MAP]
        else:
            db_map = next(iter(self._db_maps)) if self._db_maps else None
        added = [self._make_adder_row(db_map) for _ in range(count)]
        self.beginInsertRows(parent, row, row + count - 1)
        self._data = self._data[:row] + added + self._data[row:]
        self.endInsertRows()
        return True

    def _database_table_name(self):
        """Returns primary database table name.

        Returns:
            str: table name
        """
        raise NotImplementedError()

    def _row_id(self, row):
        """Returns a unique row id.

        Args:
            row (list): data table row

        Returns:
            int: id or None
        """
        raise NotImplementedError()

    def removeRows(self, first, count, parent=QModelIndex()):
        if first == len(self._data):
            return False
        count = min(count, len(self._data) - first)
        ids_to_remove = {}
        table_name = self._database_table_name()
        for i, row in enumerate(self._data[first : first + count]):
            id_to_remove = self._row_id(row)
            if id_to_remove is not None:
                ids_to_remove.setdefault(row[Column.DB_MAP], {}).setdefault(table_name, set()).add(id_to_remove)
            else:
                self.beginRemoveRows(parent, i, i + count - 1)
                del self._data[i]
                self.endRemoveRows()
        if ids_to_remove:
            self._db_mngr.remove_items(ids_to_remove)
        return True

    @staticmethod
    def _ids_from_added_item(item):
        """Returns ids that uniquely identify an added database item.

        Args:
            item (dict): added item

        Returns:
            Any: unique identifier
        """
        raise NotImplementedError()

    @staticmethod
    def _extra_cells_from_added_item(item):
        """Constructs extra cells for data row from added database item.

        Args:
            item (dict): added item

        Returns:
            list: extra cells
        """
        raise NotImplementedError()

    def _set_extra_columns(self, row, ids):
        """Sets extra columns for data row.

        Args:
            row (list): data row
            ids (Any):
        """
        raise NotImplementedError()

    def _add_data(self, db_map_data):
        """Adds new data from database manager to the model.

        Args:
            db_map_data (dict): added items keyed by database mapping
        """
        id_update_rows = set()
        for db_map, items in db_map_data.items():
            unique_identifiers = {}
            for item in items:
                unique_identifiers.setdefault(item[self._ITEM_NAME_KEY], {})[
                    item[self._ITEM_VALUE_KEY]
                ] = self._ids_from_added_item(item)
            for i, row in enumerate(self._data):
                if row[Column.DB_MAP] != db_map:
                    continue
                id_ = unique_identifiers.get(row[Column.NAME], {}).pop(row[Column.VALUE], None)
                if id_ is None:
                    continue
                self._set_extra_columns(row, id_)
                id_update_rows.add(i)
            ids_to_insert = {id_ for ids_by_name in unique_identifiers.values() for id_ in ids_by_name.values()}
            if ids_to_insert:
                added = [
                    [i[self._ITEM_NAME_KEY], i[self._ITEM_VALUE_KEY], db_map] + self._extra_cells_from_added_item(i)
                    for i in items
                    if self._ids_from_added_item(i) in ids_to_insert
                ]
                first = len(self._data)
                self.beginInsertRows(QModelIndex(), first, first + len(added) - 1)
                self._data += added
                self.endInsertRows()
        if id_update_rows:
            top_left = self.index(min(id_update_rows), Column.DB_MAP)
            bottom_right = self.index(max(id_update_rows), Column.DB_MAP)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.BackgroundRole])

    def _update_data(self, db_map_data, id_column):
        """Update data table after database update.

        Args:
            db_map_data (dict): updated items keyed by database mapping
            id_column (int): column that contains item ids
        """
        for items in db_map_data.values():
            items_by_id = {item["id"]: item for item in items}
            updated_rows = []
            for row_index, row in enumerate(self._data):
                id_ = row[id_column]
                if id_ is None:
                    continue
                db_item = items_by_id.get(id_)
                if db_item is None:
                    continue
                name = db_item[self._ITEM_NAME_KEY]
                if row[Column.NAME] != name:
                    row[Column.NAME] = name
                    updated_rows.append(row_index)
                value = db_item[self._ITEM_VALUE_KEY]
                if row[Column.VALUE] != value:
                    row[Column.VALUE] = value
                    updated_rows.append(row_index)
            if updated_rows:
                top_left = self.index(updated_rows[0], 0)
                bottom_right = self.index(updated_rows[-1], Column.DB_MAP - 1)
                self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def _remove_data(self, db_map_data, id_column):
        """Removes data from model after it has been removed from databases.

        Args:
            db_map_data (dict): removed items keyed by database mapping
            id_column (int): column that contains item ids
        """
        for items in db_map_data.values():
            ids_to_remove = {item["id"] for item in items}
            removed_rows = []
            for row_index, row in enumerate(self._data):
                row_id = row[id_column]
                if row_id is None or row_id not in ids_to_remove:
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

        def db_map_sort_key(row):
            db_map = row[Column.DB_MAP]
            return db_map.codename if db_map is not None else ""

        sort_key = itemgetter(column) if column != Column.DB_MAP else db_map_sort_key
        self._data.sort(key=sort_key, reverse=order == Qt.DescendingOrder)
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._data) - 1, Column.DB_MAP)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole])

    def _find_db_map(self, codename):
        """Finds database mapping with given codename.

        Args:
            codename (str): database mapping's code name

        Returns:
            DiffDatabaseMapping: database mapping or None if not found
        """
        match = None
        for db_map in self._db_maps:
            if codename == db_map.codename:
                match = db_map
                break
        return match

    def _reserved_metadata(self):
        """Collects metadata names and values that are already in database.

        Returns:
            dict: mapping from database mapping to metadata name and value
        """
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
