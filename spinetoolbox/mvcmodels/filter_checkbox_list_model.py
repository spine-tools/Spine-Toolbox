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

"""Provides FilterCheckboxListModel for FilterWidget."""
import re
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel, Slot
from spinetoolbox.helpers import bisect_chunks


class SimpleFilterCheckboxListModel(QAbstractListModel):
    _SELECT_ALL_STR = "(Select all)"
    _SELECT_ALL_FILTERED_STR = "(Select all filtered)"
    _EMPTY_STR = "(Empty)"
    _ADD_TO_SELECTION_STR = "Add current selection to filter"

    def __init__(self, parent, show_empty=True):
        """
        Args:
            parent (QWidget): parent widget
            show_empty (bool): if True, adds an empty row to the end of the list
        """
        super().__init__(parent)
        self._data = []
        self._data_set = set()
        self._selected = set()
        self._selected_filtered = set()
        self._is_filtered = False
        self._filter_index = []
        self._filter_expression = re.compile("")
        self._all_selected = True
        self._empty_selected = True
        self._add_to_selection = False
        self._action_rows = [self._SELECT_ALL_STR]
        if show_empty:
            self._action_rows.append(self._EMPTY_STR)

    @property
    def _show_empty(self):
        return self._EMPTY_STR in self._action_rows

    @property
    def _show_add_to_selection(self):
        return self._ADD_TO_SELECTION_STR in self._action_rows

    def reset_selection(self):
        self._selected = self._data_set.copy()
        self._all_selected = True
        self._empty_selected = True

    def _handle_select_all_clicked(self):
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
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), 0), [Qt.ItemDataRole.CheckStateRole])

    def _check_all_selected(self):
        if self._is_filtered:
            return len(self._selected_filtered) == len(self._filter_index)
        return len(self._selected) == len(self._data_set) and self._empty_selected

    def rowCount(self, parent=QModelIndex()):
        if self._is_filtered:
            if self._filter_index:
                return len(self._filter_index) + len(self._action_rows)
            # no filtered values
            return 0
        return len(self._data) + len(self._action_rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        action_state = [self._all_selected]
        if self._show_empty:
            action_state.append(self._empty_selected)
        if self._show_add_to_selection:
            action_state.append(self._add_to_selection)
        if self._is_filtered:
            selected = self._selected_filtered
            if row >= len(self._action_rows):
                data_row = self._filter_index[row - len(self._action_rows)]
        else:
            selected = self._selected
            if row >= len(self._action_rows):
                data_row = row - len(self._action_rows)
        if role == Qt.ItemDataRole.DisplayRole:
            if row >= len(self._action_rows):
                return self._data[data_row]
            return self._action_rows[row]
        if role == Qt.ItemDataRole.CheckStateRole:
            if row >= len(self._action_rows):
                return Qt.CheckState.Checked if self._data[data_row] in selected else Qt.CheckState.Unchecked
            return Qt.CheckState.Checked if action_state[row] else Qt.CheckState.Unchecked

    def _handle_index_clicked(self, index):
        if index.row() == 0:
            self._handle_select_all_clicked()
        else:
            if index.row() == 1 and self._show_add_to_selection:
                self._add_to_selection = not self._add_to_selection
            elif index.row() == 1 and self._show_empty:
                self._empty_selected = not self._empty_selected
            else:
                if self._is_filtered:
                    i = self._filter_index[index.row() - len(self._action_rows)]
                    item = self._data[i]
                    if item in self._selected_filtered:
                        self._selected_filtered.discard(item)
                    else:
                        self._selected_filtered.add(item)
                else:
                    item = self._data[index.row() - len(self._action_rows)]
                    if item in self._selected:
                        self._selected.discard(item)
                    else:
                        self._selected.add(item)
            self._all_selected = self._check_all_selected()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            self.dataChanged.emit(0, 0, [Qt.ItemDataRole.CheckStateRole])

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

    def filter_by_condition(self, condition):
        """Updates selected items by applying a condition.

        Args:
            condition (function): Filter acceptance condition.
        """
        selected = {item for item in self._data if condition(item)}
        self.set_selected(selected)

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

    def set_filter(self, filter_expression):
        filter_expression = filter_expression.strip()
        if filter_expression:
            try:
                self._filter_expression = re.compile(filter_expression)
            except re.error:
                return
            self._action_rows[0] = self._SELECT_ALL_STR
            self._filter_index = [i for i, item in enumerate(self._data) if self.search_filter_expression(item)]
            self._selected_filtered = set(self._data[i] for i in self._filter_index)
            self._add_to_selection = False
            self.beginResetModel()
            self._is_filtered = True
            if not self._show_add_to_selection:
                self._action_rows.append(self._ADD_TO_SELECTION_STR)
            self._all_selected = True
            self.endResetModel()
        else:
            self.remove_filter()

    def search_filter_expression(self, item):
        return self._filter_expression.search(item)

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
                set(item for item in (self._data[i] for i in self._filter_index) if item not in self._selected_filtered)
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
        self._action_rows[0] = self._SELECT_ALL_STR
        self._filter_expression = re.compile("")
        if self._show_add_to_selection:
            self._action_rows.remove(self._ADD_TO_SELECTION_STR)
        self._filter_index = []
        self._is_filtered = False
        self._selected_filtered = set()
        self._all_selected = self._check_all_selected()
        self.endResetModel()

    def _do_add_items(self, data):
        first = len(self._data)
        last = first + len(data) - 1
        self.beginInsertRows(self.index(0, 0), first, last)
        self._data += data
        self.endInsertRows()

    def add_items(self, data, selected=None):
        if selected is None:
            selected = self._all_selected
        data = [x for x in data if x not in self._data_set]
        if not data:
            return
        self._do_add_items(data)
        self._data_set.update(data)
        if selected:
            self._selected.update(data)
            if self._is_filtered:
                self._selected_filtered.update(data)
        if self._is_filtered:
            self._filter_index = [i for i, item in enumerate(self._data) if self.search_filter_expression(item)]
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
            self._filter_index = [i for i, item in enumerate(self._data) if self.search_filter_expression(item)]
            self._selected_filtered.difference_update(data)
        self._all_selected = self._check_all_selected()


class LazyFilterCheckboxListModel(SimpleFilterCheckboxListModel):
    """Extends SimpleFilterCheckboxListModel to allow for lazy loading in synch with another model."""

    def __init__(self, parent, db_mngr, db_maps, fetch_parent, show_empty=True):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_mngr (SpineDBManager): database manager
            db_maps (Sequence of DatabaseMapping): database maps
            fetch_parent (FetchParent): fetch parent
            show_empty (bool): if True, show an empty row at the end of the list
        """
        super().__init__(parent, show_empty=show_empty)
        self._db_mngr = db_mngr
        self._db_maps = db_maps
        self._fetch_parent = fetch_parent

    def canFetchMore(self, _parent):
        result = False
        for db_map in self._db_maps:
            result |= self._db_mngr.can_fetch_more(db_map, self._fetch_parent)
        return result

    def fetchMore(self, _parent):
        for db_map in self._db_maps:
            self._db_mngr.fetch_more(db_map, self._fetch_parent)

    def _do_add_items(self, data):
        """Adds items so the list is always sorted, while assuming that both existing and new items are sorted."""
        for chunk, pos in bisect_chunks(self._data, data):
            self.beginInsertRows(self.index(0, 0), pos, pos + len(chunk) - 1)
            self._data[pos:pos] = chunk
            self.endInsertRows()


class DataToValueFilterCheckboxListModel(SimpleFilterCheckboxListModel):
    """Extends SimpleFilterCheckboxListModel to allow for translating internal data to a value for display role."""

    def __init__(self, parent, data_to_value, show_empty=True):
        """
        Args:
            parent (SpineDBEditor): parent widget
            data_to_value (method): a method to translate item data to a value for display role
            show_empty (bool): if True, add an empty row to the end of the list
        """
        super().__init__(parent, show_empty=show_empty)
        self.data_to_value = data_to_value

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        data = super().data(index, role=role)
        if role == Qt.ItemDataRole.DisplayRole and data not in self._action_rows:
            return self.data_to_value(data)
        return data

    def search_filter_expression(self, item):
        return self._filter_expression.search(self.data_to_value(item))
