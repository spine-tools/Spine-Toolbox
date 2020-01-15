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
Models that vertically concatenate two or more table models.

:authors: M. Marin (KTH)
:date:   9.10.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from ..mvcmodels.minimal_table_model import MinimalTableModel


class CompoundTableModel(MinimalTableModel):
    """A model that concatenates several sub table models vertically."""

    def __init__(self, parent, header=None):
        """Initializes model.

        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent, header=header)
        self.sub_models = []
        self._row_map = []  # Maps compound row to tuple (sub_model, sub_row)
        self._inv_row_map = {}  # Maps tuple (sub_model, sub_row) to compound row
        self._fetch_sub_model = None

    def map_to_sub(self, index):
        """Returns an equivalent submodel index.

        Args:
            index (QModelIndex): the compound model index.

        Returns:
            QModelIndex: the equivalent index in one of the submodels
        """
        if not index.isValid():
            return QModelIndex()
        row = index.row()
        column = index.column()
        try:
            sub_model, sub_row = self._row_map[row]
        except IndexError:
            return QModelIndex()
        return sub_model.index(sub_row, column)

    def map_from_sub(self, sub_model, sub_index):
        """Returns an equivalent compound model index.

        Args:
            sub_model (MinimalTableModel): the submodel
            sub_index (QModelIndex): the submodel index.

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

    def refresh(self):
        """Refreshes the layout by computing a new row map."""
        self.layoutAboutToBeChanged.emit()
        self.do_refresh()
        self.layoutChanged.emit()

    def do_refresh(self):
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
            self._inv_row_map[model_row_tup] = self.rowCount()
            self._row_map.append(model_row_tup)

    @staticmethod
    def _row_map_for_model(model):
        """Returns row map for given model.
        The base class implementation just returns all model rows.

        Args:
            model (MinimalTableModel)

        Returns:
            list: tuples (model, row number)
        """
        return [(model, i) for i in range(model.rowCount())]

    def canFetchMore(self, parent=QModelIndex()):
        """Returns True if any of the submodels that haven't been fetched yet can fetch more."""
        for self._fetch_sub_model in self.sub_models:
            if self._fetch_sub_model.canFetchMore(self.map_to_sub(parent)):
                return True
        return False

    def fetchMore(self, parent=QModelIndex()):
        """Fetches the next sub model and increments the fetched counter."""
        self._fetch_sub_model.fetchMore(self.map_to_sub(parent))
        if not self._fetch_sub_model.rowCount():
            self.sub_models.remove(self._fetch_sub_model)
        self.layoutChanged.emit()

    def flags(self, index):
        return self.map_to_sub(index).flags()

    def data(self, index, role=Qt.DisplayRole):
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
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            rows.append(index.row())
            columns.append(index.column())
            sub_model, _ = self._row_map[index.row()]
            sub_index = self.map_to_sub(index)
            d.setdefault(sub_model, list()).append((sub_index, value))
        for model, index_value_tuples in d.items():
            indexes, values = zip(*index_value_tuples)
            model.batch_set_data(list(indexes), list(values))
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Insert count rows after the given row under the given parent.
        Localizes the appropriate submodel and calls insertRows on it.
        """
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        try:
            sub_model, sub_row = self._row_map[row]
        except IndexError:
            sub_model, sub_row = self._row_map[-1]
        return sub_model.insertRows(sub_row, count, self.map_to_sub(parent))


class CompoundWithEmptyTableModel(CompoundTableModel):
    """A compound parameter table model where the last model is an empty row model."""

    @property
    def single_models(self):
        return self.sub_models[:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    def _create_single_models(self):
        """Returns a list of single models."""
        raise NotImplementedError()

    def _create_empty_model(self):
        """Returns an empty model."""
        raise NotImplementedError()

    def init_model(self):
        """Initializes the compound model. Basically populates the sub_models list attribute
        with the result of _create_single_models and _create_empty_model.
        """
        self.clear_model()
        self.sub_models = self._create_single_models()
        self.sub_models.append(self._create_empty_model())
        self.connect_model_signals()

    def connect_model_signals(self):
        """Connects signals so changes in the submodels are acknowledge by the compound."""
        self.empty_model.rowsRemoved.connect(self._handle_empty_rows_removed)
        self.empty_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        for model in self.single_models:
            model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))
        for model in self.sub_models:
            model.dataChanged.connect(
                lambda top_left, bottom_right, roles, model=model: self.dataChanged.emit(
                    self.map_from_sub(model, top_left), self.map_from_sub(model, bottom_right), roles
                )
            )

    def _recompute_empty_row_map(self):
        """Recomputeds the part of the row map corresponding to the empty model."""
        empty_row_map = self._row_map_for_model(self.empty_model)
        try:
            row = self._inv_row_map[self.empty_model, 0]
            self._row_map = self._row_map[:row]
        except KeyError:
            pass
        self._append_row_map(empty_row_map)

    @Slot("QModelIndex", "int", "int")
    def _handle_empty_rows_removed(self, parent, empty_first, empty_last):
        """Runs when rows are removed from the empty model.
        Updates row_map, then emits rowsRemoved so the removed rows are no longer visible.
        """
        first = self._inv_row_map[self.empty_model, empty_first]
        last = self._inv_row_map[self.empty_model, empty_last]
        self._recompute_empty_row_map()
        self.rowsRemoved.emit(QModelIndex(), first, last)

    @Slot("QModelIndex", "int", "int")
    def _handle_empty_rows_inserted(self, parent, empty_first, empty_last):
        """Runs when rows are inserted to the empty model.
        Updates row_map, then emits rowsInserted so the new rows become visible.
        """
        self._recompute_empty_row_map()
        first = self._inv_row_map[self.empty_model, empty_first]
        last = self._inv_row_map[self.empty_model, empty_last]
        self.rowsInserted.emit(QModelIndex(), first, last)

    def _handle_single_model_reset(self, single_model):
        """Runs when one of the single models is reset.
        Updates row_map, then emits rowsInserted so the new rows become visible.
        """
        single_row_map = self._row_map_for_model(single_model)
        self._insert_single_row_map(single_row_map)

    def _insert_single_row_map(self, single_row_map):
        """Inserts given row map just before the empty model's."""
        if not single_row_map:
            return
        try:
            row = self._inv_row_map[self.empty_model, 0]
            self._row_map, empty_row_map = self._row_map[:row], self._row_map[row:]
        except KeyError:
            row = self.rowCount()
            empty_row_map = []
        self._append_row_map(single_row_map)
        self._append_row_map(empty_row_map)
        first = row
        last = row + len(single_row_map) - 1
        self.rowsInserted.emit(QModelIndex(), first, last)

    def clear_model(self):
        """Clears the model."""
        if self._row_map:
            self.beginResetModel()
            self._row_map.clear()
            self.endResetModel()
        for m in self.sub_models:
            m.deleteLater()
        self.sub_models.clear()
        self._inv_row_map.clear()
