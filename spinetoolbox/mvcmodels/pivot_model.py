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
Provides PivotModel.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

import operator
from ..helpers import tuple_itemgetter


class PivotModel:
    def __init__(self):
        self._model_is_updating = False  # flag if model is being reset/updated
        self._data = {}  # dictionary of unpivoted data
        self.index_ids = ()  # ids of the indexes in _data, cannot contain duplicates
        self.pivot_rows = ()  # current selected rows indexes
        self.pivot_columns = ()  # current selected columns indexes
        self.pivot_frozen = ()  # current filtered frozen indexes
        self.frozen_value = ()  # current selected value of index_frozen
        self._key_getter = lambda *x: ()  # operator.itemgetter placeholder used to translate pivot to keys in _data
        self._row_data_header = []  # header values for row data
        self._column_data_header = []  # header values for column data
        self._invalid_row = {}  # set of rows that have invalid indexes
        self._invalid_column = {}  # set of columns that have invalid indexes
        self._invalid_data = {}  # dictionary of invalid data

    def set_new_data(self, data, index_ids=(), rows=(), columns=(), frozen=(), frozen_value=()):
        """Sets new data for the model.
        """
        if not rows + columns + frozen:
            # no pivot given, set default pivot
            rows = tuple(index_ids)
            columns = ()
            frozen = ()
            frozen_value = ()
        else:
            # check given pivot
            pivot_error = self._is_invalid_pivot(rows, columns, frozen, frozen_value, index_ids)
            if pivot_error:
                raise ValueError(pivot_error)
        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        self._model_is_updating = True
        self.index_ids = tuple(index_ids)
        # create data dict with keys as long as index_ids
        self._data = data
        # item getter so that you can call _key_getter(row_header + column_header + frozen_value)
        # and get a key to use on _data
        key = tuple(self.index_ids.index(i) for i in index_ids)
        self._key_getter = tuple_itemgetter(operator.itemgetter(*key), len(key))
        self.set_pivot(rows, columns, frozen, frozen_value)
        self._model_is_updating = False

    @staticmethod
    def _is_invalid_pivot(rows, columns, frozen, frozen_value, index_ids):
        """checks if given pivot is valid for index_ids,
        returns str with error message if invalid else None"""
        error = None
        if not len(set(index_ids)) == len(index_ids):
            error = "'index_ids' must contain only unique integers"
        if not all(i in index_ids for i in frozen):
            error = "'frozen' contains ids that don't belong in 'index_ids'"
        if not all(i in index_ids for i in rows):
            error = "'rows' contains ids that don't belong in 'index_ids'"
        if not all(c in index_ids for c in columns):
            error = "'columns' contains ids that don't belong in 'index_ids'"
        if len(set(rows + columns + frozen)) != len(index_ids):
            error = "'rows', 'columns' and 'frozen' must contain only unique ids in 'index_ids' without duplicates"
        if len(frozen) != len(frozen_value):
            error = "'frozen_value' must be same length as 'frozen'"
        return error

    def _index_key_getter(self, names_of_index):
        """Returns an itemgetter that always returns tuples from list of index names"""
        keys = tuple(self.index_ids.index(i) for i in names_of_index if i in self.index_ids)
        return tuple_itemgetter(operator.itemgetter(*keys), len(keys))

    def _get_unique_index_values(self, index, filter_index, filter_value):
        """Finds unique index values for index names in index
        filtered by index names in filter_index with values in filter_value"""
        if index:
            index_getter = self._index_key_getter(index)
            if filter_index:
                frozen_getter = self._index_key_getter(filter_index)
                index_header_values = set(
                    index_getter(k) for k in self._data.keys() if frozen_getter(k) == filter_value
                )
            else:
                index_header_values = set(index_getter(k) for k in self._data.keys())
        else:
            index_header_values = set()
        return index_header_values

    def set_pivot(self, rows, columns, frozen, frozen_value):
        """Sets pivot for current data"""
        pivot_error = self._is_invalid_pivot(rows, columns, frozen, frozen_value, self.index_ids)
        print(rows, columns, frozen, frozen_value, self.index_ids)
        if pivot_error:
            raise ValueError(pivot_error)
        if not self._model_is_updating and (
            self.pivot_rows == rows
            and self.pivot_columns == columns
            and self.pivot_frozen == frozen
            and frozen_value == self.frozen_value
        ):
            # nothing has changed
            return
        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        # set key_getter so that you will get a correct key for _data when doing
        # _key_getter(row_key + col_key + frozen_value)
        order = tuple(self.index_ids.index(i) for i in self.pivot_rows + self.pivot_columns + self.pivot_frozen)
        order = tuple(sorted(range(len(order)), key=order.__getitem__))
        self._key_getter = tuple_itemgetter(operator.itemgetter(*order), len(order))
        # find unique set of tuples for row and column headers from data with given pivot
        row_data_header_set = self._get_unique_index_values(self.pivot_rows, self.pivot_frozen, self.frozen_value)
        column_data_header_set = self._get_unique_index_values(self.pivot_columns, self.pivot_frozen, self.frozen_value)
        self._row_data_header = sorted(row_data_header_set)
        self._column_data_header = sorted(column_data_header_set)
        # TODO: handle invalid data
        # len_valid_rows = len(self._row_data_header)
        # len_valid_columns = len(self._column_data_header)
        # set invalid data to indexes with none in them.
        # self._invalid_row = set(i + len_valid_rows for i, key in enumerate(none_rows))
        # self._invalid_column = set(i + len_valid_columns for i, key in enumerate(none_columns))
        self._invalid_data = {}

    def set_frozen_value(self, value):
        """Sets the value of the frozen indexes"""
        if len(value) != len(self.pivot_frozen):
            raise ValueError("'value' must have same length as 'self.pivot_frozen'")
        if value == self.frozen_value:
            # same as previous do nothing
            return
        # self.frozen_value = tuple(value)
        self.set_pivot(self.pivot_rows, self.pivot_columns, self.pivot_frozen, value)

    def get_pivoted_data(self, row_mask, col_mask):
        """gets data from current pivot with indexes in row_mask and col_mask"""
        if not self._row_data_header and not self._column_data_header:
            if self.pivot_frozen and len(self.pivot_frozen) == len(self.index_ids):
                # special case when all indexes are in pivot frozen
                return [[self._data.get(self._key_getter(self.frozen_value), None)]]
            # no data
            return []
        if self.pivot_rows and any(r >= len(self._row_data_header) or r < 0 for r in row_mask):
            raise ValueError("row_mask contains invalid indexes for current row pivot")
        if self.pivot_columns and any(c >= len(self._column_data_header) or c < 0 for c in col_mask):
            raise ValueError("col_mask contains invalid indexes for current column pivot")
        data = []
        for row in row_mask:
            data_row = []
            invalid_row = row in self._invalid_row
            row_key = self.row(row)
            for col in col_mask:
                if invalid_row or col in self._invalid_column:
                    # get invalid data
                    data_row.append(self._invalid_data.get((row, col), None))
                else:
                    # get dict data
                    col_key = self.column(col)
                    key = self._key_getter(row_key + col_key + self.frozen_value)
                    data_row.append(self._data.get(key, None))
            data.append(data_row)
        return data

    def row(self, row):
        if self.pivot_rows:
            if self._row_data_header:
                return self._row_data_header[row]
            return tuple(None for _ in self.pivot_rows)
        if row == 0:
            return ()
        raise IndexError('index out of range for current row pivot')

    def column(self, col):
        if self.pivot_columns:
            if self._column_data_header:
                return self._column_data_header[col]
            return tuple(None for _ in self.pivot_columns)
        if col == 0:
            return ()
        raise IndexError('index out of range for current column pivot')

    @property
    def rows(self):
        return self._row_data_header

    @property
    def columns(self):
        return self._column_data_header
