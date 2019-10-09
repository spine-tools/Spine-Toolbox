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
A models that concatenate several table models vertically.

:authors: M. Marin (KTH)
:date:   9.10.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..helpers import rows_to_row_count_tuples


class CompoundTableModel(MinimalTableModel):
    """A model that concatenates several table models together."""

    def __init__(self, parent, header=None):
        """Init class.

        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent, header=header)
        self._parent = parent
        self.sub_models = []
        self._row_map = []
        self._fetched_count = 0  # Index of the last submodel that's already been fetched

    def canFetchMore(self, parent):
        """Returns True if any of the unfetched single models can fetch more."""
        for model in self.sub_models[self._fetched_count :]:
            if model.canFetchMore(self.map_to_sub(parent)):
                return True
        return False

    def fetchMore(self, parent):
        """Fetches the next single model and increments the fetched index."""
        model = self.sub_models[self._fetched_count]
        sub_parent = self.map_to_sub(parent)
        layout_changed_emitted = False

        def _handle_layout_changed():
            layout_changed_emitted = True

        model.layoutChanged.connect(_handle_layout_changed)
        model.fetchMore(sub_parent)
        # Increment counter or just pop model if empty
        if model.rowCount():
            self._fetched_count += 1
        else:
            self.sub_models.pop(self._fetched_count)
        if not layout_changed_emitted:
            # layoutChanged not emitted by the , emit layoutChanged so we move to the next submodel
            self.layoutChanged.emit()

    def map_to_sub(self, index):
        """Returns a submodel index corresponding to given one."""
        if not index.isValid():
            return QModelIndex()
        row = index.row()
        column = index.column()
        sub_model, sub_row = self._row_map[row]
        return sub_model.index(sub_row, column)

    def flags(self, index):
        """Translate the index into the corresponding submodel and return its flags."""
        return self.map_to_sub(index).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Maps the index into a submodel and return its data."""
        return self.map_to_sub(index).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in all models."""
        return len(self._row_map)

    def removeRows(self, row, count, parent=QModelIndex()):
        """Distribute the rows among the different submodels
        and call removeRows on each of them.
        """
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        d = dict()
        for sub_model, sub_row in self._row_map[row, row + count]:
            d.setdefault(sub_model, list()).append(sub_row)
        for sub_model, sub_rows in d.items():
            for sub_row, sub_count in rows_to_row_count_tuples(sub_rows):
                sub_model.removeRows(sub_row, sub_count)
        self.endRemoveRows()
        return True

    def item_at_row(self, row):
        """Returns the item at given row."""
        sub_model, sub_row = self._row_map[row]
        return sub_model._main_data[sub_row]

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

    def clear_model(self):
        """Clears model. Runs after rollback or refresh."""
        for model in self.sub_models:
            model.clear_model()


class CompoundWithEmptyTableModel(CompoundTableModel):
    """A compound parameter table model where the last model is an empty row model."""

    def __init__(self, parent, header=None):
        """Init class.

        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent, header=header)
        self._parent = parent

    @property
    def single_models(self):
        return self.sub_models[0:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_inserted")
    def _handle_empty_rows_inserted(self, parent, first, last):
        """Runs when rows are inserted to the empty model.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        self._row_map += [(self.empty_model, i) for i in range(first, last + 1)]
        tip = self.rowCount() - self.empty_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), tip + first, tip + last)

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_removed")
    def _handle_empty_rows_removed(self, parent, first, last):
        """Runs when rows are removed from the empty model.
        Update row_map, then emit rowsRemoved so the removed rows are no longer visible.
        """
        removed_count = last - first + 1
        tip = self.rowCount() - (self.empty_model.rowCount() + removed_count)
        self._row_map = self._row_map[:tip] + [(self.empty_model, i) for i in range(self.empty_model.rowCount())]
        self.rowsRemoved.emit(QModelIndex(), tip + first, tip + last)

    def _handle_single_model_reset(self, model):
        """Runs when one of the single models is reset.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        tip = self.rowCount() - self.empty_model.rowCount()
        self._row_map, empty_row_map = self._row_map[:tip], self._row_map[tip:]
        self._row_map += self._row_map_for_model(model) + empty_row_map
        first = self.rowCount() + 1
        last = first + model.rowCount() - 1
        self.rowsInserted.emit(QModelIndex(), first, last)

    def connect_model_signals(self):
        """Connect model signals."""
        self.empty_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        self.empty_model.rowsRemoved.connect(self._handle_empty_rows_removed)
        for model in self.single_models:
            model.layoutChanged.connect(self.layoutChanged)
            model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))

    def _row_map_for_model(self, model):
        """Returns row map for given model.
        Reimplement in subclasses to do e.g. filtering."""
        print("this one")
        return [(model, i) for i in range(model.rowCount())]
