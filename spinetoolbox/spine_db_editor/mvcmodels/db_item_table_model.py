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
from dataclasses import dataclass
from typing import Any, ClassVar
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from spinedb_api import DatabaseMapping
from spinedb_api.helpers import ItemType
from spinedb_api.temp_id import TempId
from spinetoolbox.fetch_parent import DBMapMixedItems, FlexibleFetchParent
from spinetoolbox.helpers import rows_to_row_count_tuples
from spinetoolbox.spine_db_manager import SpineDBManager


@dataclass
class RowData:
    id: TempId
    db_map: DatabaseMapping


class DBItemTableModel(QAbstractTableModel):
    ITEM_TYPE: ClassVar[ItemType] = NotImplemented
    HEADER: ClassVar[list[str]] = NotImplemented
    HEADER_TO_FIELD: ClassVar[dict[str, str]] = NotImplemented

    def __init__(self, db_mngr: SpineDBManager, parent: QObject | None = None):
        super().__init__(parent)
        self._db_mngr = db_mngr
        self._db_maps: list[DatabaseMapping] = []
        self._data: list[RowData] = []
        self._fetch_parent = FlexibleFetchParent(
            self.ITEM_TYPE,
            self._append_rows_for_added_items,
            self._remove_rows_of_removed_items,
            self._update_rows_of_updated_items,
            owner=self,
        )

    def reset_db_maps(self, db_maps: list[DatabaseMapping]) -> None:
        self.beginResetModel()
        self._unregister_fetch_parents()
        self._data.clear()
        self._db_maps = db_maps.copy()
        for db_map in db_maps:
            self._db_mngr.register_fetch_parent(db_map, self._fetch_parent)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADER)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.column() != len(self.HEADER) - 1:
            return flags | Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADER[section]
        return None

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            row_data = self._data[index.row()]
            column = index.column()
            if column == len(self.HEADER) - 1:
                return self._db_mngr.name_registry.display_name(row_data.db_map.db_url)
            header = self.HEADER[column]
            mapped_table = row_data.db_map.mapped_table(self.ITEM_TYPE)
            return mapped_table[row_data.id][self.HEADER_TO_FIELD[header]]
        return None

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False
        row_data = self._data[index.row()]
        field = self.HEADER_TO_FIELD[self.HEADER[index.column()]]
        self._db_mngr.update_items(self.ITEM_TYPE, {row_data.db_map: [{"id": row_data.id, field: value}]})
        return True

    def begin_paste(self) -> None:
        pass

    def batch_set_data(self, indexes: list[QModelIndex], values: list[Any]) -> None:
        update_items = {}
        for index, value in zip(indexes, values):
            row_data = self._data[index.row()]
            field = self.HEADER_TO_FIELD[self.HEADER[index.column()]]
            update_items.setdefault(row_data.db_map, {}).setdefault(row_data.id, {})[field] = value
        db_map_data = {}
        for db_map, items in update_items.items():
            db_map_data[db_map] = data = []
            for item_id, item in items.items():
                data.append({"id": item_id, **item})
        self._db_mngr.update_items(self.ITEM_TYPE, db_map_data)

    def end_paste(self) -> None:
        pass

    def removeRows(self, row, count, parent=QModelIndex()) -> bool:
        ids_to_remove = {}
        for row in range(row, row + count):
            row_data = self._data[row]
            ids_to_remove.setdefault(row_data.db_map, {}).setdefault(self.ITEM_TYPE, set()).add(row_data.id)
        self._db_mngr.remove_items(ids_to_remove)
        return True

    def canFetchMore(self, parent: QModelIndex) -> bool:
        return bool(self._db_maps) and any(not self._fetch_parent.is_fetched(db_map) for db_map in self._db_maps)

    def fetchMore(self, parent: QModelIndex) -> None:
        for db_map in self._db_maps:
            self._db_mngr.fetch_more(db_map, self._fetch_parent)

    def _append_rows_for_added_items(self, db_map_items: DBMapMixedItems) -> None:
        for db_map, items in db_map_items.items():
            if db_map not in self._db_maps:
                continue
            first = len(self._data)
            self.beginInsertRows(QModelIndex(), first, first + len(items) - 1)
            for item in items:
                self._data.append(RowData(item["id"], db_map))
            self.endInsertRows()

    def _remove_rows_of_removed_items(self, db_map_items: DBMapMixedItems) -> None:
        for db_map, items in db_map_items.items():
            if db_map not in self._db_maps:
                continue
            row_by_id = {row_data.id: row for row, row_data in enumerate(self._data)}
            rows_to_remove = [row_by_id[item["id"]] for item in items]
            for first, count in sorted(rows_to_row_count_tuples(rows_to_remove), reverse=True):
                self.beginRemoveRows(QModelIndex(), first, first + count - 1)
                self._data = self._data[:first] + self._data[first + count :]
                self.endRemoveRows()

    def _update_rows_of_updated_items(self, db_map_items: DBMapMixedItems) -> None:
        row_by_id = None
        updated_rows = []
        for db_map, items in db_map_items.items():
            if db_map not in self._db_maps:
                continue
            if row_by_id is None:
                row_by_id = {row_data.id: row for row, row_data in enumerate(self._data)}
            updated_rows += [row_by_id[item["id"]] for item in items]
        if updated_rows:
            top_left = self.index(min(updated_rows), 0)
            bottom_right = self.index(max(updated_rows), len(self.HEADER) - 2)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])

    def tear_down(self):
        self._unregister_fetch_parents()

    def _unregister_fetch_parents(self) -> None:
        for db_map in self._db_maps:
            self._db_mngr.unregister_fetch_parent(db_map, self._fetch_parent)
