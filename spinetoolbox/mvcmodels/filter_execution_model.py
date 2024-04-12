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

"""Contains FilterExecutionModel."""
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel


class FilterExecutionModel(QAbstractListModel):
    _filter_consoles = dict()

    def reset_model(self, filter_consoles):
        self.beginResetModel()
        self._filter_consoles = filter_consoles
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._filter_consoles)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if section == 0 and orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Executions"
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not self._filter_consoles or not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return list(self._filter_consoles.keys())[index.row()]
        return None

    def find_index(self, console_key):
        for row, key in enumerate(self._filter_consoles.keys()):
            if key == console_key:
                return self.index(row, 0)
        return QModelIndex()

    def get_console(self, filter_id):
        return self._filter_consoles.get(filter_id)
