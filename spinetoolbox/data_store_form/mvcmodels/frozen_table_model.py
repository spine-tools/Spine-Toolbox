######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains FrozenTableModel class.

:author: P. Vennström (VTT)
:date:   24.9.2019
"""

from PySide2.QtCore import Qt, QModelIndex, QAbstractItemModel


class FrozenTableModel(QAbstractItemModel):
    """Used by custom_qtableview.FrozenTableView"""

    def __init__(self, parent, headers=None, data=None):
        """
        Args:
            parent (TabularViewMixin)
        """
        super().__init__()
        self._parent = parent
        self.db_mngr = parent.db_mngr
        self.db_map = parent.db_map
        if headers is None:
            headers = list()
        if data is None:
            data = list()
        self._data = data
        self._headers = headers

    def parent(self, child=None):
        return QModelIndex()

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column, parent)

    def reset_model(self, data, headers):
        if data and len(data[0]) != len(headers):
            raise ValueError("'data[0]' must be same length as 'headers'")
        self._headers = list(headers)
        data = [self._headers] + data
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def clear_model(self):
        self._headers = []
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._headers)

    def row(self, index):
        if index.isValid():
            return self._data[index.row()]

    def data(self, index, role):
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            id_ = self._data[index.row()][index.column()]
            if index.row() == 0:
                return id_
            index_id = self._data[0][index.column()]
            if index_id == -1:
                item = self.db_mngr.get_item(self.db_map, "parameter definition", id_)
                name = item.get("parameter_name")
            else:
                item = self.db_mngr.get_item(self.db_map, "object", id_)
                name = item.get("name")
            if role == Qt.DisplayRole:
                return name
            description = item.get("description")
            if description in (None, ""):
                description = name
            return description

    @property
    def headers(self):
        return self._headers
