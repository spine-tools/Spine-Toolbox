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
from collections.abc import Iterable
from typing import Optional
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from PySide6.QtGui import QFont
from spinedb_api import DatabaseMapping
from spinedb_api.temp_id import TempId
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_manager import SpineDBManager

_HEADERS = ("entity_class_name", "entity_byname", "parameter_name", "alternative_name", "value", "database")
_HEADER_TO_FIELD = {"parameter_name": "parameter_definition_name"}
_GROUP_NAME_FONT = QFont()
_GROUP_NAME_FONT.setItalic(True)


class GroupedParameterValueModel(QAbstractItemModel):
    """A tree model that has parameter value groups as root items and value tables as leafs."""

    def __init__(self, db_mngr: SpineDBManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._groups: dict[tuple[Optional[str], Optional[str]], list[tuple[DatabaseMapping, TempId]]] = {}
        self._db_mngr = db_mngr

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            return self.createIndex(row, column)
        group_row = parent.row()
        group_key = next(filter(lambda i: i[0] == group_row, enumerate(self._groups)))[1]
        return self.createIndex(row, column, group_key)

    def parent(self, index):
        group_key = index.internalPointer()
        if group_key is None:
            return QModelIndex()
        row = next(filter(lambda i: i[1] == group_key, enumerate(self._groups)))[0]
        return self.createIndex(row, 0)

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._groups)
        group_key = parent.internalPointer()
        if group_key is None:
            if parent.column() != 0:
                return 0
            row = parent.row()
            group = next(filter(lambda i: i[0] == row, enumerate(self._groups.values())))[1]
            return len(group)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return len(_HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            group_key = index.internalPointer()
            if group_key is None:
                if index.column() != 0:
                    return None
                row = index.row()
                group_key = next(filter(lambda i: i[0] == row, enumerate(self._groups)))[1]
                group_name = group_key[1]
                return group_name
            group = self._groups[group_key]
            db_map, value_id = group[index.row()]
            with self._db_mngr.get_lock(db_map):
                value_item = db_map.mapped_table("parameter_value")[value_id]
                header = _HEADERS[index.column()]
                if header == "entity_byname":
                    return DB_ITEM_SEPARATOR.join(value_item[header])
                if header == "value":
                    return self._db_mngr.get_value(db_map, value_item, role)
                if header == "database":
                    return self._db_mngr.name_registry.display_name(db_map.sa_url)
                field = _HEADER_TO_FIELD.get(header, header)
                if group_key[1] is not None and field == "parameter_definition_name":
                    _, _, parameter_name = value_item[field].partition("/")
                    return parameter_name
                return value_item[field]
        if role == Qt.ItemDataRole.FontRole and index.internalPointer() is None:
            return _GROUP_NAME_FONT
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _HEADERS[section]
        return None

    def load_data(self, entity_class_ids: dict[DatabaseMapping, Iterable[TempId]]) -> None:
        self.beginResetModel()
        self._groups.clear()
        for db_map, ids in entity_class_ids.items():
            with self._db_mngr.get_lock(db_map):
                class_table = db_map.mapped_table("entity_class")
                for class_id in ids:
                    class_name = class_table[class_id]["name"]
                    for value_item in db_map.find_parameter_values(entity_class_id=class_id):
                        group_name, _, parameter_name = value_item["parameter_definition_name"].partition("/")
                        key = (class_name, group_name) if parameter_name else (None, None)
                        self._groups.setdefault(key, []).append((db_map, value_item["id"]))
        self.endResetModel()

    def ungrouped_row(self) -> Optional[int]:
        try:
            return next(filter(lambda i: i[1][0] is None, enumerate(self._groups)))[0]
        except StopIteration:
            return None
