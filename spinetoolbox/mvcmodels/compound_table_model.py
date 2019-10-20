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
Models that vertically concatenate two or more table models.

:authors: M. Marin (KTH)
:date:   9.10.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..helpers import rows_to_row_count_tuples


class CompoundTableModel(MinimalTableModel):
    """A model that vertically concatenates several sub table models together."""

    def __init__(self, parent, header=None):
        """Init class.

        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent, header=header)
        self.sub_models = []
        self._row_map = []  # Maps compound row to tuple (sub_model, sub_row)
        self._inv_row_map = {}  # Maps tuple (sub_model, sub_row) to compound row
        self._fetched_count = 0

    def map_to_sub(self, index):
        """Translate the index into the corresponding submodel."""
        if not index.isValid():
            return QModelIndex()
        row = index.row()
        column = index.column()
        sub_model, sub_row = self._row_map[row]
        return sub_model.index(sub_row, column)

    def map_from_sub(self, sub_model, sub_index):
        """Translate the index from the given submodel into this."""
        try:
            row = self._inv_row_map[sub_model, sub_index.row()]
        except KeyError:
            return QModelIndex()
        return self.index(row, sub_index.column())

    def refresh(self):
        """Recomputes the row map."""
        self.layoutAboutToBeChanged.emit()
        self.do_refresh()
        self.layoutChanged.emit()

    def _row_map_for_model(self, model):
        """Returns row map for given model.
        The base class implementation just returns all rows.
        """
        return [(model, i) for i in range(model.rowCount())]

    def do_refresh(self):
        """Recomputes the row map."""
        self._row_map.clear()
        self._inv_row_map.clear()
        for model in self.sub_models:
            row_map = self._row_map_for_model(model)
            self._append_row_map(row_map)

    def _append_row_map(self, row_map):
        """Appends given row map."""
        row_count = self.rowCount()
        self._row_map += row_map
        for model, row in row_map:
            self._inv_row_map[model, row] = row_count + row

    def item_at_row(self, row):
        """Returns the item at given row."""
        sub_model, sub_row = self._row_map[row]
        return sub_model._main_data[sub_row]

    def sub_model_at_row(self, row):
        """Returns the item at given row."""
        sub_model, _ = self._row_map[row]
        return sub_model

    def canFetchMore(self, parent):
        """Returns True if any of the unfetched single models can fetch more."""
        for model in self.sub_models[self._fetched_count :]:
            if model.canFetchMore(self.map_to_sub(parent)):
                return True
        return False

    def fetchMore(self, parent):
        """Fetches the next single model and increments the fetched counter."""
        model = self.sub_models[self._fetched_count]
        row_count_before = model.rowCount()
        model.fetchMore(self.map_to_sub(parent))
        # Increment counter or just pop model if empty
        if model.rowCount():
            self._fetched_count += 1
        else:
            self.sub_models.pop(self._fetched_count)
        if model.rowCount() == row_count_before:
            # fetching submodel didn't add any rows. Emit layoutChanged so we make sure we fetch the next submodel
            self.layoutChanged.emit()

    def flags(self, index):
        """Translate the index into the corresponding submodel and return its flags."""
        return self.map_to_sub(index).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Maps the index into a submodel and return its data."""
        return self.map_to_sub(index).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in all models."""
        return len(self._row_map)

    def remove_sub_model_rows(self, model, first, last):
        """Remove rows from given submodel."""
        compound_first = self._inv_row_map[model, first]
        compound_last = self._inv_row_map[model, last]
        self.beginRemoveRows(QModelIndex(), compound_first, compound_last)
        del model._main_data[first : last + 1]
        self.endRemoveRows()
        # Redo the map for the affected model entirely
        removed_count = last - first + 1
        previous_row_count = model.rowCount() + removed_count
        compound_first = self._inv_row_map[model, 0]
        compound_last = self._inv_row_map[model, previous_row_count - 1]
        self._row_map, tail_row_map = self._row_map[:compound_first], self._row_map[compound_last:]
        row_map = self._row_map_for_model(model)
        self._append_row_map(row_map)
        self._append_row_map(tail_row_map)

    def batch_set_data(self, indexes, data):
        """Set data for indexes in batch.
        Distribute indexes and values among the different submodels
        and call batch_set_data on each of them."""
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
            model.batch_set_data(indexes, values)
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        return True


class CompoundWithEmptyTableModel(CompoundTableModel):
    """A compound parameter table model where the last model is an empty row model."""

    @property
    def single_models(self):
        return self.sub_models[0:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_removed")
    def _handle_empty_rows_removed(self, parent, first, last):
        """Runs when rows are removed from the empty model.
        Update row_map, then emit rowsRemoved so the removed rows are no longer visible.
        """
        compound_first = self._inv_row_map[self.empty_model, first]
        compound_last = self._inv_row_map[self.empty_model, last]
        self.rowsRemoved.emit(QModelIndex(), compound_first, compound_last)
        # Redo the map for the empty model entirely
        tip = self._inv_row_map[self.empty_model, 0]
        self._row_map = self._row_map[:tip]
        empty_row_map = self._row_map_for_model(self.empty_model)
        self._append_row_map(empty_row_map)

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_inserted")
    def _handle_empty_rows_inserted(self, parent, first, last):
        """Runs when rows are inserted to the empty model.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        # Append row map, knowing rows are always inserted at the end
        tail_empty_row_map = [(self.empty_model, row) for row in range(first, last + 1)]
        self._append_row_map(tail_empty_row_map)
        compound_first = self._inv_row_map[self.empty_model, first]
        compound_last = self._inv_row_map[self.empty_model, last]
        self.rowsInserted.emit(QModelIndex(), compound_first, compound_last)

    def _handle_single_model_reset(self, single_model):
        """Runs when one of the single models is reset.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        compound_first = self.rowCount() - self.empty_model.rowCount()
        compound_last = compound_first + single_model.rowCount() - 1
        self.rowsInserted.emit(QModelIndex(), compound_first, compound_last)
        # Take the empty row map, append the new one, and then append the empty
        self._row_map, empty_row_map = self._row_map[:compound_first], self._row_map[compound_first:]
        single_row_map = self._row_map_for_model(single_model)
        self._append_row_map(single_row_map)
        self._append_row_map(empty_row_map)

    def connect_model_signals(self):
        """Connect model signals."""
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

    def clear_model(self):
        """Clear the model."""
        if self._row_map:
            self.beginResetModel()
            self._row_map.clear()
            self.endResetModel()
        self._fetched_count = 0
        for m in self.sub_models:
            m.deleteLater()
        self.sub_models.clear()
        self._inv_row_map.clear()

    def init_model(self):
        """Initialize model."""
        self.clear_model()
        self.sub_models = self._create_single_models()
        self.sub_models.append(self._create_empty_model())
        self.connect_model_signals()

    def _create_single_models(self):
        """Returns a list of single models."""
        raise NotImplementedError()

    def _create_empty_model(self):
        """Returns an empty model."""
        raise NotImplementedError()
