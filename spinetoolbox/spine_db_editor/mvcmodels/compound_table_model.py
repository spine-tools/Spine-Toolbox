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

"""Models that vertically concatenate two or more table models."""
from typing import Optional
from PySide6.QtCore import QModelIndex, QObject, Qt, QTimer, Slot
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel
from .single_models import SingleModelBase


class CompoundTableModel(MinimalTableModel):
    """A model that concatenates several sub table models vertically."""

    def __init__(self, parent: Optional[QObject] = None, header: Optional[list[str]] = None):
        """
        Args:
            parent: the parent object
            header: header labels
        """
        super().__init__(parent=parent, header=header)
        self.sub_models: list[SingleModelBase] = []
        self._row_map: list[tuple[SingleModelBase, int]] = []  # Maps compound row to tuple (sub_model, sub_row)
        self._inv_row_map: dict[tuple[SingleModelBase, int], int] = (
            {}
        )  # Maps tuple (sub_model, sub_row) to compound row
        self._next_sub_model: Optional[SingleModelBase] = None

    def map_to_sub(self, index):
        """Returns an equivalent submodel index.

        Args:
            index (QModelIndex): the compound model index.

        Returns:
            QModelIndex: the equivalent index in one of the submodels
        """
        if not index.isValid():
            return QModelIndex()
        try:
            sub_model, sub_row = self._row_map[index.row()]
        except IndexError:
            return QModelIndex()
        return sub_model.index(sub_row, index.column())

    def map_from_sub(self, sub_model: SingleModelBase, sub_index: QModelIndex) -> QModelIndex:
        """Returns an equivalent compound model index.

        Args:
            sub_model: the submodel
            sub_index: the submodel index.

        Returns:
            QModelIndex: the equivalent index in the compound model
        """
        try:
            row = self._inv_row_map[sub_model, sub_index.row()]
        except KeyError:
            return QModelIndex()
        return self.index(row, sub_index.column())

    def item_at_row(self, row):
        """Returns the item at given row.

        Args:
            row (int)

        Returns:
            object
        """
        sub_model, sub_row = self._row_map[row]
        return sub_model._main_data[sub_row]

    def sub_model_at_row(self, row):
        """Returns the submodel corresponding to the given row in the compound model.

        Args:
            row (int):

        Returns:
            MinimalTableModel
        """
        sub_model, _ = self._row_map[row]
        return sub_model

    def sub_model_row(self, row):
        """Calculates sub model row.

        Args:
            row (int): row in compound model

        Returns:
            int: row in sub model
        """
        _, sub_row = self._row_map[row]
        return sub_row

    @Slot()
    def refresh(self):
        """Refreshes the layout by computing a new row map."""
        self.layoutAboutToBeChanged.emit()
        self._do_refresh()
        self.layoutChanged.emit()
        if self.canFetchMore(QModelIndex()):
            self.fetchMore(QModelIndex())

    def _do_refresh(self):
        """Recomputes the row and inverse row maps."""
        self._row_map.clear()
        self._inv_row_map.clear()
        for model in self.sub_models:
            row_map = self._row_map_for_model(model)
            self._append_row_map(row_map)

    def _append_row_map(self, row_map):
        """Appends given row map to the tail of the model.

        Args:
            row_map (list): tuples (model, row number)
        """
        for model_row_tup in row_map:
            self._inv_row_map[model_row_tup] = len(self._row_map)
            self._row_map.append(model_row_tup)

    def _row_map_iterator_for_model(self, model):
        """Yields row map for given model.
        The base class implementation just yields all model rows.

        Args:
            model (MinimalTableModel)

        Yields:
            tuple: (model, row number)
        """
        for i in range(model.rowCount()):
            yield (model, i)

    def _row_map_for_model(self, model):
        """Returns row map for given model.
        The base class implementation just returns all model rows.

        Args:
            model (MinimalTableModel)

        Returns:
            list: tuples (model, row number)
        """
        return list(self._row_map_iterator_for_model(model))

    def canFetchMore(self, parent):
        """Returns True if any of the submodels that haven't been fetched yet can fetch more."""
        for self._next_sub_model in self.sub_models:
            if self._next_sub_model.canFetchMore(self.map_to_sub(parent)):
                return True
        return False

    def fetchMore(self, parent):
        """Fetches the next sub model and increments the fetched counter."""
        self._next_sub_model.fetchMore(self.map_to_sub(parent))
        if not self._next_sub_model.rowCount():
            self.sub_models.remove(self._next_sub_model)
        self.layoutChanged.emit()

    def flags(self, index):
        return self.map_to_sub(index).flags()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        return self.map_to_sub(index).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Returns the sum of rows in all models."""
        return len(self._row_map)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Distributes indexes and values among the different submodels
        and calls batch_set_data on each of them."""
        if not indexes or not data:
            return False
        d = {}  # Maps models to (index, value) tuples
        rows = []
        columns = []
        successful = True
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            rows.append(index.row())
            columns.append(index.column())
            sub_model, _ = self._row_map[index.row()]
            sub_index = self.map_to_sub(index)
            d.setdefault(sub_model, []).append((sub_index, value))
        for model, index_value_tuples in d.items():
            indexes, values = zip(*index_value_tuples)
            if not model.batch_set_data(list(indexes), list(values)):
                successful = False
                break
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return successful

    def insertRows(self, row, count, parent=QModelIndex()):
        """Does not insert any rows as single models do not support such operation."""
        return False

    def removeRows(self, row, count, parent=QModelIndex()):
        """Removes count rows starting with the given row under parent.
        Localizes the appropriate submodels and calls removeRows on it.
        """
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        first = row
        last = row + count - 1
        self.beginRemoveRows(parent, first, last)
        while first <= last:
            try:
                sub_model, sub_row = self._row_map[first]
                sub_count = min(sub_model.rowCount(), count)
                first += sub_count
                count -= sub_count
            except IndexError:
                sub_model, sub_row = self._row_map[-1]
                sub_count = min(sub_model.rowCount(), count)
                break
            finally:
                # pylint: disable=used-before-assignment
                sub_model.removeRows(sub_row, sub_count, self.map_to_sub(parent))
        self.endRemoveRows()
        self.refresh()
        return True
