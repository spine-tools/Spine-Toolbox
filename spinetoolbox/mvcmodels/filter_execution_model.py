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
Contains FilterExecutionModel.

:author: M. Marin (KTH)
:date:   26.11.2020
"""

from PySide2.QtCore import Qt, QModelIndex, QAbstractItemModel


class FilterExecutionModel(QAbstractItemModel):

    _item = None

    def reset_model(self, item):
        if item == self._item:
            return
        self.beginResetModel()
        self._item = item
        self.endResetModel()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()):
        if self._item is None:
            return 0
        return len(self._item.filter_log_documents)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if section == 0 and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "Executions"
        return None

    def data(self, index, role=Qt.DisplayRole):
        if self._item is None or not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return list(self._item.filter_log_documents.keys())[index.row()]
        return None

    def get_log_document(self, filter_id):
        return self._item.filter_log_documents[filter_id]

    def get_console(self, filter_id):
        return self._item.filter_consoles.get(filter_id)
