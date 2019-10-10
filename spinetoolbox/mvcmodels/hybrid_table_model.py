######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a hybrid table model.

:authors: M. Marin (KTH)
:date:   20.5.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from .minimal_table_model import MinimalTableModel
from .empty_row_model import EmptyRowModel


class HybridTableModel(MinimalTableModel):
    """A model that concatenates two models,
    one for existing items and another one for new items.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self._parent = parent
        self.existing_item_model = MinimalTableModel(self)
        self.new_item_model = EmptyRowModel(self)

    def flags(self, index):
        """Return flags for given index.
        Depending on the index's row we will land on one of the two models.
        """
        row = index.row()
        column = index.column()
        if row < self.existing_item_model.rowCount():
            return self.existing_item_model.index(row, column).flags()
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.index(row, column).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Depending on the index's row we will land on one of the two models.
        """
        row = index.row()
        column = index.column()
        if row < self.existing_item_model.rowCount():
            return self.existing_item_model.index(row, column).data(role)
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.index(row, column).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in the two models.
        """
        return self.existing_item_model.rowCount() + self.new_item_model.rowCount()

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        Distribute indexes and data among the two models
        and call batch_set_data on each of them."""
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        existing_model_indexes = []
        existing_model_data = []
        new_model_indexes = []
        new_model_data = []
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            if row < self.existing_item_model.rowCount():
                existing_model_indexes.append(self.existing_item_model.index(row, column))
                existing_model_data.append(data[k])
            else:
                row -= self.existing_item_model.rowCount()
                new_model_indexes.append(self.new_item_model.index(row, column))
                new_model_data.append(data[k])
        self.existing_item_model.batch_set_data(existing_model_indexes, existing_model_data)
        self.new_item_model.batch_set_data(new_model_indexes, new_model_data)
        # Find square envelope of indexes to emit dataChanged
        top = min(ind.row() for ind in indexes)
        bottom = max(ind.row() for ind in indexes)
        left = min(ind.column() for ind in indexes)
        right = max(ind.column() for ind in indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-model (or the empty model) and call insertRows on it."""
        if row < self.existing_item_model.rowCount():
            self.rowsInserted.emit()
            return self.existing_item_model.insertRows(row, count)
        row -= self.existing_item_model.rowCount()
        return self.new_item_model.insertRows(row, count)

    def removeRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-models (or empty model) and call removeRows on them."""
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        if row < self.existing_item_model.rowCount():
            # split count across models
            existing_count = min(count, self.existing_item_model.rowCount() - row)
            self.existing_item_model.removeRows(row, existing_count)
            new_count = count - existing_count
            if new_count > 0:
                self.new_item_model.removeRows(row, new_count)
        else:
            row -= self.existing_item_model.rowCount()
            self.new_item_model.removeRows(row, count)
        self.endRemoveRows()
        return True

    def set_horizontal_header_labels(self, labels):
        super().set_horizontal_header_labels(labels)
        self.new_item_model.set_horizontal_header_labels(labels)

    def reset_model(self, main_data=None):
        """Reset model data."""
        self.beginResetModel()
        self.existing_item_model.reset_model(main_data)
        self.new_item_model.clear()
        self.new_item_model.rowsInserted.connect(self._handle_new_item_model_rows_inserted)
        self.endResetModel()

    @Slot("QModelIndex", "int", "int", name="_handle_new_item_model_rows_inserted")
    def _handle_new_item_model_rows_inserted(self, parent, first, last):
        offset = self.existing_item_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), offset + first, offset + last)
