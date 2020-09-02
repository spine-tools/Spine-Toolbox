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
Contains :class:`RecordListModel`

:author: A. Soininen (VTT)
:date:   25.8.2020
"""
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt
from spinetoolbox.spine_io.exporters import gdx
from ..list_utils import move_list_elements


class RecordListModel(QAbstractListModel):
    """A model to manage record ordering within domains and sets."""

    def __init__(self):
        super().__init__()
        self._records = gdx.LiteralRecords([])
        self._set_name = ""

    def data(self, index, role=Qt.DisplayRole):
        """With `role == Qt.DisplayRole` returns the record's keys as comma separated string."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            keys = self._records.records[index.row()]
            return ", ".join(keys)
        return None

    def flags(self, index):
        if self._records.is_shufflable():
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.NoItemFlags

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns row and column header data."""
        if orientation == Qt.Horizontal:
            return ''
        return section + 1

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        """
        Moves the records around.

        Args:
            sourceParent (QModelIndex): parent from which the rows are moved
            sourceRow (int): index of the first row to be moved
            count (int): number of rows to move
            destinationParent (QModelIndex): parent to which the rows are moved
            destinationChild (int): index where to insert the moved rows

        Returns:
            True if the operation was successful, False otherwise
        """
        if not self._records.is_shufflable():
            return False
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        self._records.shuffle(move_list_elements(self._records.records, sourceRow, last_source_row, destinationChild))
        self.endMoveRows()
        return True

    def reset(self, records, set_name):
        """Resets the model's record data."""
        self._set_name = set_name
        self.beginResetModel()
        self._records = records
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of records in the model."""
        return len(self._records)

    def sort_alphabetically(self):
        """Sorts the record alphabetically"""
        if not self._records.is_shufflable():
            return
        self._records.shuffle(sorted(self._records.records))
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._records) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
