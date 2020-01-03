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


class FilterCheckboxListModelBase(QAbstractListModel):
    def __init__(self, parent, show_empty=True):
        """Init class.

        Args:
            parent (QWidget)
        """
        super().__init__(parent)
        self._id_data = []
        self._id_data_set = set()
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
        self._selected = self._id_data_set.copy()
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
                self._selected_filtered = set(self._id_data[i] for i in self._filter_index)
            else:
                self._selected = self._id_data_set.copy()
            self._empty_selected = True
        self._all_selected = not self._all_selected
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0), [Qt.CheckStateRole])

    def _is_all_selected(self):
        if self._is_filtered:
            return len(self._selected_filtered) == len(self._filter_index)
        return len(self._selected) == len(self._id_data_set) and self._empty_selected

    def rowCount(self, parent=QModelIndex()):
        if self._is_filtered:
            if self._filter_index:
                return len(self._filter_index) + self._index_offset
            # no filtered values
            return 0
        return len(self._id_data) + self._index_offset

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
                return self._item_name(self._id_data[i])
            return action_rows[row]
        if role == Qt.CheckStateRole:
            if row < len(action_state):
                return Qt.Checked if action_state[row] else Qt.Unchecked
            return Qt.Checked if self._id_data[i] in selected else Qt.Unchecked

    def _item_name(self, id_):
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
                    item = self._id_data[i]
                    if item in self._selected_filtered:
                        self._selected_filtered.discard(item)
                    else:
                        self._selected_filtered.add(item)
                else:
                    item = self._id_data[index.row() - self._index_offset]
                    if item in self._selected:
                        self._selected.discard(item)
                    else:
                        self._selected.add(item)
            self._all_selected = self._is_all_selected()
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            self.dataChanged.emit(0, 0, [Qt.CheckStateRole])

    def set_list(self, id_data, all_selected=True):
        self.beginResetModel()
        self._id_data_set = set(id_data)
        self._id_data = sorted(self._id_data_set)
        if all_selected:
            self._selected = self._id_data_set.copy()
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
        self._selected = self._id_data_set.intersection(selected)
        if select_empty is not None:
            self._empty_selected = select_empty
        self._all_selected = self._is_all_selected()
        self.endResetModel()

    def get_selected(self):
        return self._selected.copy()

    def get_not_selected(self):
        if self._all_selected:
            return set()
        return self._id_data_set.difference(self._selected)

    def set_filter(self, search_for):
        if search_for and (isinstance(search_for, str) and not search_for.isspace()):
            self._select_all_str = '(Select all filtered)'
            self._list_filter = search_for
            self._filter_index = [i for i, id_ in enumerate(self._id_data) if self._list_filter in self._item_name(id_)]
            self._selected_filtered = set(self._id_data[i] for i in self._filter_index)
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
                set(self._id_data[i] for i in self._filter_index if self._id_data[i] not in self._selected_filtered)
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

    def add_items(self, ids, selected=True):
        ids = set(ids) - self._id_data_set
        if not ids:
            return
        for id_ in ids:
            k = bisect.bisect_left(self._id_data, id_)
            self.beginInsertRows(self.index(0, 0), k, k)
            self._id_data.insert(k, id_)
            self._id_data_set.update(ids)
            if selected:
                self._selected.update(ids)
                if self._is_filtered:
                    self._selected_filtered.update(ids)
            self.endInsertRows()
        if self._is_filtered:
            self._filter_index = [i for i, id_ in enumerate(self._id_data) if self._list_filter in self._item_name(id_)]
        self._all_selected = self._is_all_selected()

    def remove_items(self, ids):
        ids = set(ids)
        if not ids.intersection(self._id_data_set):
            return
        for k, id_ in reversed(list(enumerate(self._id_data))):
            if id_ in ids:
                self.beginRemoveRows(self.index(0, 0), k, k)
                self._id_data.pop(k)
                self.endRemoveRows()
        self._id_data_set.difference_update(ids)
        self._selected.difference_update(ids)
        if self._is_filtered:
            self._filter_index = [i for i, id_ in enumerate(self._id_data) if self._list_filter in self._item_name(id_)]
            self._selected_filtered.difference_update(ids)
        self._all_selected = self._is_all_selected()


class SimpleFilterCheckboxListModel(FilterCheckboxListModelBase):
    def _item_name(self, id_):
        return id_


class TabularViewFilterCheckboxListModel(FilterCheckboxListModelBase):
    def __init__(self, parent, item_type, show_empty=True):
        """Init class.

        Args:
            parent (TabularViewMixin)
            item_type (str, NoneType): either "object" or "parameter definition"
        """
        super().__init__(parent, show_empty=show_empty)
        self.item_type = item_type
        self.db_mngr = parent.db_mngr
        self.db_map = parent.db_map

    def _item_name(self, id_):
        name_key = {"object": "name", "parameter definition": "parameter_name"}[self.item_type]
        return self.db_mngr.get_item(self.db_map, self.item_type, id_)[name_key]
