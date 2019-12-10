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
Provides FilterCheckboxListModel for FilterWidget.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

import bisect
from PySide2.QtCore import Qt, QModelIndex, QAbstractListModel


class FilterCheckboxListModel(QAbstractListModel):
    def __init__(self, parent, item_type, show_empty=True):
        """Init class.

        Args:
            parent (TabularViewMixin)
            item_type (str): either "object" or "parameter definition"
        """
        super().__init__(parent)
        self.db_mngr = parent.db_mngr
        self.db_map = parent.db_map
        self.item_type = item_type
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
        self._selected = set(self._data_set)
        self._all_selected = True
        self._empty_selected = True

    def _select_all_clicked(self):
        if self._all_selected:
            if self._is_filtered:
                self._selected_filtered = set()
            else:
                self._selected = set()
            self._empty_selected = False
        else:
            if self._is_filtered:
                self._selected_filtered = set(self._data[i] for i in self._filter_index)
            else:
                self._selected = set(self._data_set)
            self._empty_selected = True
        self._all_selected = not self._all_selected
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0), [Qt.CheckStateRole])

    def _is_all_selected(self):
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
                name_key = {"object": "name", "parameter definition": "parameter_name"}[self.item_type]
                return self.db_mngr.get_item(self.db_map, self.item_type, self._data[i])[name_key]
            return action_rows[row]
        if role == Qt.CheckStateRole:
            if row < len(action_state):
                return Qt.Checked if action_state[row] else Qt.Unchecked
            return Qt.Checked if self._data[i] in selected else Qt.Unchecked

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
                    f_i = self._filter_index[index.row() - self._index_offset]
                    item = self._data[f_i]
                    if item in self._selected_filtered:
                        self._selected_filtered.discard(item)
                        self._all_selected = False
                    else:
                        self._selected_filtered.add(item)
                else:
                    item = self._data[index.row() - self._index_offset]
                    if item in self._selected:
                        self._selected.discard(item)
                        self._all_selected = False
                    else:
                        self._selected.add(item)
            self._all_selected = self._is_all_selected()
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            self.dataChanged.emit(0, 0, [Qt.CheckStateRole])

    def set_list(self, data, all_selected=True):
        self.beginResetModel()
        self._data_set = set(data)
        self._data = sorted(data)
        if all_selected:
            self._selected = set(self._data_set)
            self._all_selected = True
            self._empty_selected = True
        else:
            self._selected = set()
            self._all_selected = False
            self._empty_selected = False
        self.remove_filter()
        self.endResetModel()

    def add_items(self, items, selected=True):
        for item in items:
            if item not in self._data_set:
                pos = bisect.bisect_left(self._data, item)
                self.beginInsertRows(self.index(0, 0), pos, pos)
                if self._is_filtered and pos is not None:
                    start_pos = bisect.bisect_left(self._filter_index, pos)
                    for i in range(start_pos, len(self._filter_index)):
                        self._filter_index[i] = self._filter_index[i] + 1
                    if self._list_filter in item:
                        self._filter_index.insert(start_pos, pos)
                self._data.insert(pos, item)
                self._data_set.add(item)
                if selected:
                    self._selected.add(item)
                    if self._is_filtered:
                        self._selected_filtered.add(item)
                self._all_selected = self._is_all_selected()
                self.endInsertRows()

    def set_selected(self, selected, select_empty=None):
        self.beginResetModel()
        self._selected = self._data_set.intersection(selected)
        if select_empty is not None:
            self._empty_selected = select_empty
        self._all_selected = self._is_all_selected()
        self.endResetModel()

    def get_selected(self):
        return set(self._selected)

    def get_not_selected(self):
        if self._all_selected:
            return set()
        return self._data_set.difference(self._selected)

    def set_filter(self, search_for):
        if search_for and (isinstance(search_for, str) and not search_for.isspace()):
            self._select_all_str = '(Select all filtered)'
            self._list_filter = search_for
            self._filter_index = [i for i in range(len(self._data)) if search_for in str(self._data[i])]
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
        self._all_selected = self._is_all_selected()
        self.endResetModel()

    def remove_items(self, items):
        if self._is_filtered:
            self._selected_filtered.difference_update(items)
            remove_index = []
            subtract_index = 0
            for i, row in enumerate(self._filter_index):
                if self._data[row] in items:
                    # indexes to remove
                    remove_index.append(i)
                    subtract_index = subtract_index + 1
                else:
                    # update row index
                    self._filter_index[i] = self._filter_index[i] - subtract_index
            for i in reversed(remove_index):
                self._filter_index.pop(i)
        self._data_set.difference_update(items)
        self._data = [d for d in self._data if d not in items]
        self._selected.difference_update(items)

        self._all_selected = self._is_all_selected()
