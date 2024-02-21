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
import bisect
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QTimer
from ..mvcmodels.minimal_table_model import MinimalTableModel


class CompoundTableModel(MinimalTableModel):
    """A model that concatenates several sub table models vertically."""

    refreshed = Signal()

    def __init__(self, parent=None, header=None):
        """Initializes model.

        Args:
            parent (QObject, optional): the parent object
            header (list of str, optional): header labels
        """
        super().__init__(parent=parent, header=header)
        self.sub_models = []
        self._row_map = []  # Maps compound row to tuple (sub_model, sub_row)
        self._inv_row_map = {}  # Maps tuple (sub_model, sub_row) to compound row
        self._next_sub_model = None

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
        self.refreshed.emit()

    def _append_row_map(self, row_map):
        """Appends given row map to the tail of the model.

        Args:
            row_map (list): tuples (model, row number)
        """
        for model_row_tup in row_map:
            self._inv_row_map[model_row_tup] = self.rowCount()
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
            d.setdefault(sub_model, list()).append((sub_index, value))
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
        """Inserts count rows after the given row under the given parent.
        Localizes the appropriate submodel and calls insertRows on it.
        """
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        if row < self.rowCount():
            sub_model, sub_row = self._row_map[row]
        else:
            sub_model, sub_row = self._row_map[-1]
            sub_row += 1
        self.beginInsertRows(parent, row, row + count - 1)
        sub_model.insertRows(sub_row, count, self.map_to_sub(parent))
        self.endInsertRows()
        self.refresh()
        return True

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
                sub_model.removeRows(sub_row, sub_count, self.map_to_sub(parent))
        self.endRemoveRows()
        self.refresh()
        return True


class CompoundWithEmptyTableModel(CompoundTableModel):
    """A compound parameter table model where the last model is an empty row model."""

    @property
    def single_models(self):
        return self.sub_models[:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    def _create_empty_model(self):
        """Creates and returns an empty model.

        Returns:
            EmptyRowModel: model
        """
        raise NotImplementedError()

    def init_model(self):
        """Initializes the compound model.

        Basically populates the sub_models list attribute with the result of _create_empty_model.
        """
        self.clear_model()
        self.sub_models.append(self._create_empty_model())
        self.empty_model.rowsRemoved.connect(self._handle_empty_rows_removed)
        self.empty_model.rowsInserted.connect(self._handle_empty_rows_inserted)

    def _connect_single_model(self, model):
        """Connects signals so changes in the submodels are acknowledged by the compound."""
        model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))
        model.modelAboutToBeReset.connect(lambda model=model: self._handle_single_model_about_to_be_reset(model))
        model.dataChanged.connect(
            lambda top_left, bottom_right, roles, model=model: self.dataChanged.emit(
                self.map_from_sub(model, top_left), self.map_from_sub(model, bottom_right), roles
            )
        )

    def _recompute_empty_row_map(self):
        """Recomputes the part of the row map corresponding to the empty model."""
        empty_row_map = self._row_map_for_model(self.empty_model)
        try:
            row = self._inv_row_map[self.empty_model, 0]
            self._row_map = self._row_map[:row]
        except KeyError:
            pass
        self._append_row_map(empty_row_map)

    @Slot(QModelIndex, int, int)
    def _handle_empty_rows_removed(self, parent, empty_first, empty_last):
        """Updates row_map when rows are removed from the empty model."""
        first = self._inv_row_map[self.empty_model, empty_first]
        last = self._inv_row_map[self.empty_model, empty_last]
        self.beginRemoveRows(QModelIndex(), first, last)
        self._recompute_empty_row_map()
        self.endRemoveRows()

    @Slot(QModelIndex, int, int)
    def _handle_empty_rows_inserted(self, parent, empty_first, empty_last):
        """Runs when rows are inserted to the empty model.
        Updates row_map, then emits rowsInserted so the new rows become visible.
        """
        self._recompute_empty_row_map()
        first = self._inv_row_map[self.empty_model, empty_first]
        last = self._inv_row_map[self.empty_model, empty_last]
        self.rowsInserted.emit(QModelIndex(), first, last)

    def _handle_single_model_about_to_be_reset(self, model):
        """Runs when given model is about to reset."""
        if model not in self.single_models:
            return
        row_map = self._row_map_for_model(model)
        if not row_map:
            return
        try:
            first = self._inv_row_map[row_map[0]]
        except KeyError:
            # Sometimes the submodel may get reset before it has been added to the inverted row map.
            # In this case there are no rows to remove, so we can bail out here.
            return
        last = first + len(row_map) - 1
        tail_row_map = self._row_map[last + 1 :]
        self.beginRemoveRows(QModelIndex(), first, last)
        for key in self._row_map[first:]:
            del self._inv_row_map[key]
        self._row_map[first:] = []
        self._append_row_map(tail_row_map)
        self.endRemoveRows()

    def _handle_single_model_reset(self, model):
        """Runs when given model is reset."""
        if model in self.single_models:
            self._refresh_single_model(model)
        else:
            self._insert_single_model(model)

    def _refresh_single_model(self, model):
        single_row_map = self._row_map_for_model(model)
        pos = self.single_models.index(model) + 1
        self._insert_row_map(pos, single_row_map)

    def _get_insert_position(self, model):
        return bisect.bisect_left(self.single_models, model)

    def _insert_single_model(self, model):
        single_row_map = self._row_map_for_model(model)
        pos = self._get_insert_position(model)
        self._insert_row_map(pos, single_row_map)
        self.sub_models.insert(pos, model)

    def _get_row_for_insertion(self, pos):
        for model in self.sub_models[pos:]:
            first_row_map_item = next(self._row_map_iterator_for_model(model), None)
            if first_row_map_item is not None:
                try:
                    return self._inv_row_map[first_row_map_item]
                except KeyError:
                    # Sometimes the submodel is not yet in the inverted row map.
                    # In this case we just skip it and try another insertion point.
                    pass
        return self.rowCount()

    def _insert_row_map(self, pos, single_row_map):
        if not single_row_map:
            # Emit layoutChanged to trigger fetching.
            # The QTimer is to avoid funny situations where the user enters new data via the empty row model,
            # and those rows need to be removed at the same time as we fetch the added data.
            # Doing it in the same loop cycle was causing bugs.
            QTimer.singleShot(0, self.layoutChanged.emit)
            return
        row = self._get_row_for_insertion(pos)
        last = row + len(single_row_map) - 1
        self.beginInsertRows(QModelIndex(), row, last)
        self._row_map, tail_row_map = self._row_map[:row], self._row_map[row:]
        self._append_row_map(single_row_map)
        self._append_row_map(tail_row_map)
        self.endInsertRows()

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
