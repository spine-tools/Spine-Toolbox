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
Provides FilterCheckboxListModel for FilterWidget.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from PySide2.QtCore import Qt, QModelIndex, QAbstractListModel


class FilterCheckboxListModelBase(QAbstractListModel):
    def __init__(self, parent, show_empty=True):
        """Init class.

        Args:
            parent (QWidget)
        """
        super().__init__(parent)
        self._data = []
        self._data_set = set()
        self._all_selected = True
        self._empty_selected = True
        self._selected = set()
        self._selected_filtered = set()
        self._list_filter = None
        self._index_offset = 2
        self._is_filtered = False
        self._filter_index = []
        self._select_all_str = '(Select All)'
        self._show_empty = show_empty
        self._empty_str = '(Empty)'
        self._add_to_selection_str = 'Add current selection to filter'
        self._add_to_selection = False

        if self._show_empty:
            self._index_offset = 2
        else:
            self._index_offset = 1

    def reset_selection(self):
        self._selected = self._data_set.copy()
        self._all_selected = True
        self._empty_selected = True

    def _select_all_clicked(self):
        if self._all_selected:
            if self._is_filtered:
                self._selected_filtered = set()
            else:
                self._selected = set()
        else:
            if self._is_filtered:
                self._selected_filtered = set(self._data[i] for i in self._filter_index)
            else:
                self._selected = self._data_set.copy()
        self._all_selected = not self._all_selected
        if self._show_empty:
            self._empty_selected = self._all_selected
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0), [Qt.CheckStateRole])

    def _check_all_selected(self):
        if self._is_filtered:
            return len(self._selected_filtered) == len(self._filter_index)
        return len(self._selected) == len(self._data_set) and self._empty_selected

    def rowCount(self, parent=QModelIndex()):
        if self._is_filtered:
            if self._filter_index:
                return len(self._filter_index) + self._index_offset
            # no filtered values
            return 0
        return len(self._data) + self._index_offset

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        row = index.row()
        action_state = [self._all_selected]
        if self._is_filtered:
            i = 0
            if row > 1:
                i = self._filter_index[row - self._index_offset]
            action_rows = [self._select_all_str, self._add_to_selection_str]
            action_state.append(self._add_to_selection)
            selected = self._selected_filtered
        else:
            i = row - self._index_offset
            action_rows = [self._select_all_str]
            if self._show_empty:
                action_rows.append(self._empty_str)
                action_state.append(self._empty_selected)
            selected = self._selected
        if role == Qt.DisplayRole:
            if row >= len(action_rows):
                return self._item_name(self._data[i])
            return action_rows[row]
        if role == Qt.CheckStateRole:
            if row < len(action_state):
                return Qt.Checked if action_state[row] else Qt.Unchecked
            return Qt.Checked if self._data[i] in selected else Qt.Unchecked

    def _item_name(self, item):
        raise NotImplementedError()

    def click_index(self, index):
        if index.row() == 0:
            self._select_all_clicked()
        else:
            if index.row() == 1 and self._is_filtered:
                self._add_to_selection = not self._add_to_selection
            elif index.row() == 1 and self._show_empty:
                self._empty_selected = not self._empty_selected
            else:
                if self._is_filtered:
                    i = self._filter_index[index.row() - self._index_offset]
                    item = self._data[i]
                    if item in self._selected_filtered:
                        self._selected_filtered.discard(item)
                    else:
                        self._selected_filtered.add(item)
                else:
                    item = self._data[index.row() - self._index_offset]
                    if item in self._selected:
                        self._selected.discard(item)
                    else:
                        self._selected.add(item)
            self._all_selected = self._check_all_selected()
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            self.dataChanged.emit(0, 0, [Qt.CheckStateRole])

    def set_list(self, data, all_selected=True):
        self.beginResetModel()
        self._data_set = set(data)
        self._data = list(data)
        if all_selected:
            self._selected = self._data_set.copy()
            self._all_selected = True
            self._empty_selected = True
        else:
            self._selected = set()
            self._all_selected = False
            self._empty_selected = False
        self.remove_filter()
        self.endResetModel()

    def set_selected(self, selected, select_empty=None):
        self.beginResetModel()
        self._selected = self._data_set.intersection(selected)
        if select_empty is not None:
            self._empty_selected = select_empty
        self._all_selected = self._check_all_selected()
        self.endResetModel()

    def get_selected(self):
        return self._selected.copy()

    def get_not_selected(self):
        if self._all_selected:
            return set()
        return self._data_set.difference(self._selected)

    def set_filter(self, search_for):
        if search_for and (isinstance(search_for, str) and not search_for.isspace()):
            self._select_all_str = '(Select all filtered)'
            self._list_filter = search_for
            self._filter_index = [i for i, id_ in enumerate(self._data) if self._list_filter in self._item_name(id_)]
            self._selected_filtered = set(self._data[i] for i in self._filter_index)
            self._add_to_selection = False
            self.beginResetModel()
            self._is_filtered = True
            self._all_selected = True
            self.endResetModel()
        else:
            self.remove_filter()

    def apply_filter(self):
        if not self._is_filtered:
            return
        if self._add_to_selection:
            self._remove_and_add_filtered()
        else:
            self._remove_and_replace_filtered()

    def _remove_and_add_filtered(self):
        if not self._selected:
            # no previous selected, just replace
            self._selected = set(self._selected_filtered)
        else:
            # add selected
            self._selected.update(self._selected_filtered)
            # remove unselected
            self._selected.difference_update(
                set(self._data[i] for i in self._filter_index if self._data[i] not in self._selected_filtered)
            )
        self.remove_filter()

    def _remove_and_replace_filtered(self):
        self._selected = set(self._selected_filtered)
        self._empty_selected = False
        self.remove_filter()

    def remove_filter(self):
        if not self._is_filtered:
            return
        self.beginResetModel()
        self._select_all_str = '(Select all)'
        self._list_filter = None
        self._is_filtered = False
        self._filter_index = []
        self._selected_filtered = set()
        self._all_selected = self._check_all_selected()
        self.endResetModel()

    def add_items(self, data, selected=None):
        if selected is None:
            selected = self._all_selected
        data = [x for x in data if x not in self._data_set]
        if not data:
            return
        first = len(self._data)
        last = first + len(data) - 1
        self.beginInsertRows(self.index(0, 0), first, last)
        self._data += data
        self._data_set.update(data)
        if selected:
            self._selected.update(data)
            if self._is_filtered:
                self._selected_filtered.update(data)
        self.endInsertRows()
        if self._is_filtered:
            self._filter_index = [i for i, item in enumerate(self._data) if self._list_filter in self._item_name(item)]
        self._all_selected = self._check_all_selected()

    def remove_items(self, data):
        data = set(data)
        if not data.intersection(self._data_set):
            return
        for k, item in reversed(list(enumerate(self._data))):
            if item in data:
                self.beginRemoveRows(self.index(0, 0), k, k)
                self._data.pop(k)
                self.endRemoveRows()
        self._data_set.difference_update(data)
        self._selected.difference_update(data)
        if self._is_filtered:
            self._filter_index = [i for i, item in enumerate(self._data) if self._list_filter in self._item_name(item)]
            self._selected_filtered.difference_update(data)
        self._all_selected = self._check_all_selected()


class SimpleFilterCheckboxListModel(FilterCheckboxListModelBase):
    def _item_name(self, item):
        return item


class DBItemFilterCheckboxListModel(FilterCheckboxListModelBase):
    def __init__(self, parent, query_method, source_model=None, show_empty=True):
        """Init class.

        Args:
            parent (DataStoreForm)
            query_method (method): the method to query data
            source_model (CompoundParameterModel, optional): a model to lazily get data from
        """
        super().__init__(parent, show_empty=show_empty)
        self.query_method = query_method
        self.source_model = source_model

    def _item_name(self, item):
        if item is None:
            return None
        db_map, db_id = item
        return self.query_method(db_map, db_id)

    def canFetchMore(self, parent=QModelIndex()):
        if self.source_model is None:
            return False
        return self.source_model.canFetchMore()

    def fetchMore(self, parent=QModelIndex()):
        row_count = self.rowCount()
        self.source_model.fetchMore()
        # If the source model didn't bring any new data, emit layoutChanged to trigger fetching again.
        if row_count == self.rowCount():
            self.layoutChanged.emit()
