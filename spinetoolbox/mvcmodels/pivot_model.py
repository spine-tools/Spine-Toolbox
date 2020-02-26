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
Provides PivotModel.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

import operator
from ..helpers import tuple_itemgetter


class PivotModel:
    def __init__(self):
        self._data = {}  # dictionary of unpivoted data
        self.index_values = {}  # Maps index id to a sorted set of values for that index
        self.index_ids = ()  # ids of the indexes in _data, cannot contain duplicates
        self.pivot_rows = ()  # current selected rows indexes
        self.pivot_columns = ()  # current selected columns indexes
        self.pivot_frozen = ()  # current filtered frozen indexes
        self.frozen_value = ()  # current selected value of index_frozen
        self._key_getter = None  # operator.itemgetter placeholder used to translate pivot to keys in _data
        self._row_data_header = []  # header values for row data
        self._column_data_header = []  # header values for column data

    def reset_model(self, data, index_ids=(), rows=(), columns=(), frozen=(), frozen_value=()):
        """Resets the model.
        """
        if not rows + columns + frozen:
            # no pivot given, set default
            rows = tuple(index_ids)
            columns = ()
            frozen = ()
            frozen_value = ()
        self.pivot_rows = None
        self.pivot_columns = None
        self.pivot_frozen = None
        self.frozen_value = None
        # create data dict with keys as long as index_ids
        self._data = data
        self.index_values = dict(zip(index_ids, zip(*data.keys())))
        self.index_ids = tuple(index_ids)
        self.set_pivot(rows, columns, frozen, frozen_value)

    def clear_model(self):
        self._data = {}
        self.index_values = {}
        self.index_ids = ()
        self.pivot_rows = ()
        self.pivot_columns = ()
        self.pivot_frozen = ()
        self.frozen_value = ()
        self._key_getter = None
        self._row_data_header = []
        self._column_data_header = []

    def update_model(self, data):
        self._data.update(data)

    def add_to_model(self, data):
        self._data.update(data)
        self.index_values = dict(zip(self.index_ids, zip(*self._data.keys())))
        old_row_count = len(self._row_data_header)
        old_column_count = len(self._column_data_header)
        self._row_data_header = self._get_unique_index_values(self.pivot_rows)
        self._column_data_header = self._get_unique_index_values(self.pivot_columns)
        added_row_count = len(self._row_data_header) - old_row_count
        added_column_count = len(self._column_data_header) - old_column_count
        return added_row_count, added_column_count

    def remove_from_model(self, data):
        self._data = {key: self._data[key] for key in set(self._data) - set(data)}
        self.index_values = dict(zip(self.index_ids, zip(*self._data.keys())))
        old_row_count = len(self._row_data_header)
        old_column_count = len(self._column_data_header)
        self._row_data_header = self._get_unique_index_values(self.pivot_rows)
        self._column_data_header = self._get_unique_index_values(self.pivot_columns)
        removed_row_count = old_row_count - len(self._row_data_header)
        removed_column_count = old_column_count - len(self._column_data_header)
        return removed_row_count, removed_column_count

    def _check_pivot(self, rows, columns, frozen, frozen_value):
        """Checks if given pivot is valid.

        Returns:
            str, NoneType: error message or None if no error
        """
        if not len(set(self.index_ids)) == len(self.index_ids):
            err_msg = "index ids must be unique"
        elif not all(i in self.index_ids for i in frozen):
            err_msg = "'frozen' contains wrong ids"
        elif not all(i in self.index_ids for i in rows):
            err_msg = "'rows' contains wrong ids"
        elif not all(c in self.index_ids for c in columns):
            err_msg = "'columns' contains wrong ids"
        elif len(set(rows + columns + frozen)) != len(self.index_ids):
            err_msg = "ids in 'rows', 'columns' and 'frozen' are not unique"
        elif len(frozen) != len(frozen_value):
            err_msg = "'frozen_value' must be same length as 'frozen'"
        else:
            return
        raise ValueError(err_msg)

    def _index_key_getter(self, indexes):
        """Returns an itemgetter that always returns tuples from list of indexes"""
        keys = tuple(self.index_ids.index(i) for i in indexes if i in self.index_ids)
        return tuple_itemgetter(operator.itemgetter(*keys), len(keys))

    def _get_unique_index_values(self, indexes):
        """Returns unique indexes that match the frozen condition.

        Args:
            indexes (list)

        Returns
            list
        """
        if not indexes:
            return []
        index_getter = self._index_key_getter(indexes)
        if self.pivot_frozen:
            frozen_getter = self._index_key_getter(self.pivot_frozen)
            result = {index_getter(k): None for k in self._data if frozen_getter(k) == self.frozen_value}
        else:
            result = {index_getter(k): None for k in self._data}
        return [x for x in result if None not in x]

    def set_pivot(self, rows, columns, frozen, frozen_value):
        """Sets pivot."""
        self._check_pivot(rows, columns, frozen, frozen_value)
        if (
            self.pivot_rows == rows
            and self.pivot_columns == columns
            and self.pivot_frozen == frozen
            and self.frozen_value == frozen_value
        ):
            # Nothing changed
            return
        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        order = tuple(self.index_ids.index(i) for i in self.pivot_rows + self.pivot_columns + self.pivot_frozen)
        order = tuple(sorted(range(len(order)), key=order.__getitem__))
        self._key_getter = tuple_itemgetter(operator.itemgetter(*order), len(order))
        self._row_data_header = self._get_unique_index_values(self.pivot_rows)
        self._column_data_header = self._get_unique_index_values(self.pivot_columns)

    def set_frozen_value(self, value):
        """Sets values for the frozen indexes."""
        if len(value) != len(self.pivot_frozen):
            raise ValueError("'value' must have same length as 'self.pivot_frozen'")
        if value == self.frozen_value:
            return
        self.set_pivot(self.pivot_rows, self.pivot_columns, self.pivot_frozen, value)

    def get_pivoted_data(self, row_mask, column_mask):
        """Returns data for indexes in row_mask and column_mask.

        Args:
            row_mask (list)
            column_mask (list)
        Returns:
            list(list)
        """
        if not self.rows and not self.columns:
            if self.pivot_frozen and len(self.pivot_frozen) == len(self.index_ids):
                # special case when all indexes are in pivot frozen
                return [[self._data.get(self._key_getter(self.frozen_value), None)]]
            # no data
            return []
        if self.pivot_rows and any(r >= len(self.rows) or r < 0 for r in row_mask):
            raise ValueError("row_mask contains invalid indexes for current row pivot")
        if self.pivot_columns and any(c >= len(self.columns) or c < 0 for c in column_mask):
            raise ValueError("column_mask contains invalid indexes for current column pivot")
        data = []
        for row in row_mask:
            data_row = []
            row_key = self.row_key(row)
            for column in column_mask:
                column_key = self.column_key(column)
                key = self._key_getter(row_key + column_key + self.frozen_value)
                data_row.append(self._data.get(key, None))
            data.append(data_row)
        return data

    def row_key(self, row):
        if self.pivot_rows:
            if self._row_data_header:
                return self._row_data_header[row]
            return tuple(None for _ in self.pivot_rows)
        if row == 0:
            return ()
        raise IndexError('index out of range for current row pivot')

    def column_key(self, column):
        if self.pivot_columns:
            if self._column_data_header:
                return self._column_data_header[column]
            return tuple(None for _ in self.pivot_columns)
        if column == 0:
            return ()
        raise IndexError('index out of range for current column pivot')

    @property
    def rows(self):
        return self._row_data_header

    @property
    def columns(self):
        return self._column_data_header
