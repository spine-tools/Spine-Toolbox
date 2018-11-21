#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Spine Toolbox grid view

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from PySide2.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, QSortFilterProxyModel
from PySide2.QtGui import QColor
import operator

class PivotModel():
    _model_is_updating = False # flag if model is being reset/updated
    _data = {} # dictionary of unpivoted data
    _edit_data = {} # dictionary of edited data, values are original data
    _deleted_data = {} # dictionary of deleted data, values are original data
    _data_frozen = {} # data filtered with frozen_value
    _data_frozen_index_values = set() # valid frozen_value values for current pivot_frozen
    _index_types = () # type of the indexes in _data
    index_names = () # names of the indexes in _data
    pivot_rows = () # current selected rows indexes
    pivot_columns = () # current selected columns indexes
    pivot_frozen = () # current filtered frozen indexes
    frozen_value = () # current selected value of index_frozen
    _key_getter = lambda *x: () # operator.itemgetter placeholder used translate pivot to keys in _data
    _row_data_header = [] # header values for row data 
    _column_data_header = [] # header valus for column data
    _row_data_header_set = set() # set of _row_data_header
    _column_data_header_set = set() # set of _column_data_header
    _invalid_row = {}
    _invalid_column = {}
    _invalid_data = {}
    _added_index_entries = {}
    _added_tuple_index_entries = {}
    _deleted_tuple_index_entries = {}
    _deleted_index_entries = {}

    # dict with index name as key and set/range of valid values for that index
    # if set/range is empty or index doesn't exist in valid_index_values
    # then all values are valid
    _valid_index_values = {} 
    def set_new_data(self, data, index_names, index_type, rows=(), columns=(), frozen=(), frozen_value=() , valid_index_values={}, tuple_index_entries={}):
        """set the data of the model, index names and any additional indexes that don't have data, valid index values.
        """
        if len(index_names) != len(index_type):
            raise ValueError('index_names and index_type must have same length')
        if data and any(len(d) < len(index_names) + 1 for d in data):
            raise ValueError('data inner lists be of len >= len(index_names) + 1')
        if not all(t in [str, int] for t in index_type):
            raise ValueError('index_type can only contain str or int type')

        if not rows + columns + frozen:
            # no pivot given, set default pivot
            rows = tuple(index_names)
            columns = ()
            frozen = ()
            frozen_value = ()
        else:
            # check given pivot
            pivot_error = self._is_invalid_pivot(rows, columns, frozen, frozen_value, index_names)
            if pivot_error:
                raise ValueError(pivot_error)
        
        self._model_is_updating = True

        self._valid_index_values = valid_index_values
        self._edit_data = {}
        self._deleted_data = {}
        self._index_ind = {index: ind for ind, index in enumerate(index_names)}
        
        self.index_names = tuple(index_names)
        self._index_type = {index_names[i]: it for i, it in enumerate(index_type)}
        # create data dict with keys as long as index_names
        self._data = {tuple(d[:len(index_names)]):d[len(index_names)] for d in data}
        # item getter so that you can call _key_getter(row_header + column_header + frozen_value)
        # and get a key to use on _data
        key = tuple(self.index_names.index(i) for i in index_names)
        self._key_getter = tuple_itemgetter(operator.itemgetter(*key), len(key))
        
        self.index_entries = {}
        self.tuple_index_entries = {}
        self._added_index_entries = {}
        self._added_tuple_index_entries = {}
        self._deleted_tuple_index_entries = {}
        self._deleted_index_entries = {}
        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        
        # get all index values from data
        for i, c in enumerate(self.index_names):
            self.index_entries[c] = set(d[i] for d in self._data.keys())
            self._added_index_entries[c] = set()
            self._deleted_index_entries[c] = set()
        # add tuple entries
        for k, v in tuple_index_entries.items():
            keys = tuple(self._index_ind[i] for i in k)
            getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
            self.tuple_index_entries[k] = set(getter(key) for key in self._data.keys())
            self.tuple_index_entries[k].update(v)

        self.set_pivot(rows, columns, frozen, frozen_value)
        self._model_is_updating = False
    
    def _is_invalid_pivot(self, rows, columns, frozen, frozen_value, index_names):
        """checks if given pivot is valid for index_names,
        returns str with error message if invalid else None"""
        error = None
        if not all(i in index_names for i in frozen):
            error = "'frozen' contains values that doesn't match with current 'index_names'"
        if not all(i in index_names for i in rows):
            error = "'rows' contains values that doesn't match with current 'index_names'"
        if not all(c in index_names for c in columns):
            error = "'columns' contains values that doesn't match with current 'index_names'"
        if len(set(rows + columns + frozen)) != len(index_names):
            error = "'rows', 'columns' and 'forzen' must contain all unqiue variables in 'index_names' without duplicates"
        if len(frozen) != len(frozen_value):
            error = "'frozen_value' must be same length as 'frozen'"
        return error
    
    def _change_index_frozen(self):
        """Filters out data with index values in index_frozen"""
        if self.pivot_frozen:
            key_getter = self._index_key_getter(self.pivot_frozen)
            self._data_frozen_index_values = set(key_getter(k) for k in self._data.keys())
        else:
            self._data_frozen_index_values = set()
    
    def _index_key_getter(self, names_of_index):
        """creates a itemgetter that always returns tuples from list of index names"""
        keys = tuple(self.index_names.index(i) for i in names_of_index if i in self.index_names)
        return tuple_itemgetter(operator.itemgetter(*keys), len(keys))
    
    def _get_unique_index_values(self, index, filter_index, filter_value):
        """Finds unique index values for index names in index 
        filtered by index names in filter_index with values in filter_value"""
        if len(index) > 0:
            index_getter = self._index_key_getter(index)
            if filter_index:
                frozen_getter = self._index_key_getter(filter_index)
                index_header_values = set(index_getter(k) for k in self._data.keys() if frozen_getter(k) == filter_value)
            else:
                index_header_values = set(index_getter(k) for k in self._data.keys())
        else:
            index_header_values = set()
        return index_header_values

    def set_pivot(self, rows, columns, frozen, frozen_value):
        """Sets pivot for current data"""
        pivot_error = self._is_invalid_pivot(rows, columns, frozen, frozen_value, self.index_names)
        if pivot_error:
            raise ValueError(pivot_error)
        if not self._model_is_updating:
            # check if pivot has changed
            if self.pivot_rows == rows and self.pivot_columns == columns and self.pivot_frozen == frozen:
                if frozen_value == self.frozen_value:
                    # nothing has changed
                    return

        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        # set key_getter so that you will get a correct key for _data when doing
        # _key_getter(row_key + col_key + frozen_value)
        order = tuple(self.index_names.index(i) for i in self.pivot_rows + self.pivot_columns + self.pivot_frozen)
        order = tuple(sorted(range(len(order)),key=order.__getitem__))
        self._key_getter = tuple_itemgetter(operator.itemgetter(*order), len(order))
        
        # find unique set of tuples for row and column headers from data with given pivot
        # row indexes
        self._row_data_header_set = self._get_unique_index_values(self.pivot_rows, self.pivot_frozen, self.frozen_value)
        # column indexes
        self._column_data_header_set = self._get_unique_index_values(self.pivot_columns, self.pivot_frozen, self.frozen_value)
        
        # add tuple index entries to rows and column
        # rows
        new_row_keys, new_row_none_keys, new_entries = self._index_entries_without_data(
            self.pivot_rows, self._row_data_header_set,
            self.pivot_frozen, self.frozen_value, self.tuple_index_entries)
        for name, value in new_entries.items():
            self.index_entries[name].update(value)
        # columns
        new_column_keys, new_column_none_keys, new_entries = self._index_entries_without_data(
            self.pivot_columns, self._column_data_header_set,
            self.pivot_frozen, self.frozen_value, self.tuple_index_entries)
        for name, value in new_entries.items():
            self.index_entries[name].update(value)

        # add values
        self._row_data_header_set.update(new_row_keys)
        self._column_data_header_set.update(new_column_keys)
        self._row_data_header = sorted(self._row_data_header_set)
        self._column_data_header = sorted(self._column_data_header_set)
        len_valid_rows = len(self._row_data_header)
        len_valid_columns = len(self._column_data_header)

        # values with None keys
        none_rows = sorted(new_row_none_keys, key=lambda x:tuple((i is None, i) for i in x))
        none_columns = sorted(new_column_none_keys, key=lambda x:tuple((i is None, i) for i in x))

        # add to header data
        self._row_data_header.extend(none_rows)
        self._column_data_header.extend(none_columns)

        self._change_index_frozen()
        
        # set invalid data to indexes with none in them.
        self._invalid_row = set(i + len_valid_rows for i, key in enumerate(none_rows))
        self._invalid_column = set(i + len_valid_columns for i, key in enumerate(none_columns))
        self._invalid_data = {}
    
    def set_frozen_value(self, value):
        """Sets the value of the frozen indexes"""
        if len(value) != len(self.pivot_frozen):
            raise ValueError("'value' must have same lenght as 'self.pivot_frozen'")
        if value == self.frozen_value:
            #same as previous do nothing
            return
        self.frozen_value = tuple(value)
        self.set_pivot(self.pivot_rows, self.pivot_columns, self.pivot_frozen, value)

    def _index_entries_without_data(self, pivot_index, pivot_set, filter_index, filter_value, tuple_index_entries):
        """find values in tuple_index_entries that are not present in pivot_set for index in pivot index
        filtered by filter_index and filter_value"""
        # new unique values for pivot_index
        new_keys = set()
        new_none_keys = set() # can contain None
        # keep track of new individual index entries
        new_entries = {name: set() for name in pivot_index}
        for k in tuple_index_entries.keys():
            if set(k).issubset(filter_index + pivot_index) and not set(filter_index).issuperset(k):
                # tuple_index_entries names are all in given index, i.e. don't add indexes that are split
                position = [i for i, name in enumerate(k) if name in pivot_index]
                position_current = [pivot_index.index(name) for name in k if name in pivot_index]
                position_current_frozen = [filter_index.index(name) for name in k if name in filter_index]
                getter_current = tuple_itemgetter(operator.itemgetter(*tuple(position_current)), len(position_current))
                getter = operator.itemgetter(*tuple(position))
                v = set(tuple_index_entries[k])
                if filter_index and position_current_frozen:
                    # one or more of the index entries are in the filter column, 
                    # keep only those with same value as filter_value
                    position_frozen = [i for i, name in enumerate(k) if name in filter_index]
                    getter_frozen_current = tuple_itemgetter(operator.itemgetter(*tuple(position_current_frozen)), len(position_current_frozen))
                    getter_frozen = tuple_itemgetter(operator.itemgetter(*tuple(position_frozen)), len(position_frozen))
                    v = set(getter(i) for i in v if getter_frozen(i) == getter_frozen_current(filter_value))
                    k = tuple(i for i in k if i not in filter_index)
                # find unique values for with subset in tuple_index_entries
                current_set = set(getter_current(d) for d in pivot_set)
                v = v.difference(current_set)
                # create new values that are the same length and order as pivot_index
                none_key = [None for _ in pivot_index]
                for key in v:
                    if not isinstance(key, tuple):
                        key = (key,)
                    new_key = none_key
                    for i, ki in enumerate(position_current):
                        new_key[ki] = key[i]
                        new_entries[k[i]].add(key[i])
                    if len(key) == len(pivot_index):
                        new_keys.add(tuple(new_key))
                    else:
                        new_none_keys.add(tuple(new_key))
        return new_keys, new_none_keys, new_entries

    def get_pivoted_data(self, row_mask, col_mask):
        """gets data from current pivot with indexes in row_mask and col_mask"""
        if not self._row_data_header and not self._column_data_header:
            if self.pivot_frozen and len(self.pivot_frozen) == len(self.index_names):
                #special case when all indexes are in pivot forzen
                return [[self._data.get(self._key_getter(self.frozen_value), None)]]
            # no data
            return [[]]
        if any(r >= len(self._row_data_header) or r < 0 for r in row_mask):
            raise ValueError("row_mask contains invalid indexes to current row pivot")
        if any(c >= len(self._column_data_header) or c < 0 for c in col_mask):
            raise ValueError("col_mask contains invalid indexes to current row pivot")
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

    def set_pivoted_data(self, data, row_mask, col_mask):
        """paste list of lists into current pivot, no change of indexes,
        row_mask list of indexes where to paste data rows in current pivot
        col_mask list of indexes where to paste data columns in current pivot"""
        if len(data) != len(row_mask):
            raise ValueError('row_mask must be same length as data')
        if not all(len(row) == len(col_mask) for row in data):
            raise ValueError('col_mask must be same length as each sublist in data')
        
        # keep only valid indexes
        if self.pivot_rows and self.pivot_columns:
            data = [[col for c, col in zip(col_mask, row) if c < len(self._column_data_header)] 
                    for r, row in zip(row_mask, data) if r < len(self._row_data_header)]
            row_mask = [r for r in row_mask if r < len(self._row_data_header)]
            col_mask = [r for r in col_mask if r < len(self._column_data_header)]
        elif self.pivot_rows and not self.pivot_columns:
            # only row data
            data = [[col for c, col in zip(col_mask, row) if c == 0] 
                    for r, row in zip(row_mask, data) if r < len(self._row_data_header)]
            row_mask = [r for r in row_mask if r < len(self._row_data_header)]
            col_mask = [r for r in col_mask if r == 0]
        elif self.pivot_columns and not self.pivot_rows:
            # only col data
            data = [[col for c, col in zip(col_mask, row) if c < len(self._column_data_header)] 
                    for r, row in zip(row_mask, data) if r == 0]
            row_mask = [r for r in row_mask if r == 0]
            col_mask = [r for r in col_mask if r < len(self._column_data_header)]
                

        for row, row_value in zip(row_mask, data):
            invalid_row = row in self._invalid_row
            row_key = self.row(row)
            for col, paste_value in zip(col_mask, row_value):
                col_key = self.column(col)
                if invalid_row or col in self._invalid_column:
                    # row or col invalid, put data in invald data dict
                    invalid_index = (row, col)
                    if not paste_value or paste_value.isspace():
                        # value is None or whitspace remove any existing data
                        self._invalid_data.pop(invalid_index, None)
                    else:
                        # update invalid data
                        self._invalid_data[invalid_index] = paste_value
                else:
                    # valid index, insert data into dict
                    key = self._key_getter(row_key + col_key + self.frozen_value)
                    if not paste_value or paste_value.isspace():
                        # value is None or whitspace remove any existing data
                        self._delete_data(key)
                    else:
                        # update data
                        self._add_data(key, paste_value)

    def _delete_data(self, key):
        # value is None or whitspace remove any existing data
        if key in self._edit_data:
            # data was edited, track original value
            if self._edit_data[key] and key not in self._deleted_data:
                # there was data in _edit_data, store original value
                self._deleted_data[key] = self._edit_data.pop(key)
        else:
            # data was not edited, track existing data
            if key in self._data and key not in self._deleted_data:
                self._deleted_data[key] = self._data.pop(key)
        self._edit_data.pop(key, None)
        self._data.pop(key, None)
        

    def _add_data(self, key, value):
        old_value = None
        if key in self._deleted_data:
            # data was deleted before
            old_value = self._deleted_data.pop(key)
            if not old_value == value:
                # new value, set edit data to old value
                self._edit_data[key] = old_value
        else:
            # data new or edit data
            if key in self._edit_data:
                # data has been edited before
                if self._edit_data[key] == value:
                    # same value as original, delete from edit
                    self._edit_data.pop(key)
            else:
                if value != self._data.get(key, None):
                    # new value is not same as previous
                    self._edit_data[key] = self._data.get(key, None)
        self._data[key] = value
    
    def _restore_data(self, key):
        # TODO: function to restore data to original value
        pass
    
    def row(self, row):
        if self.pivot_rows:
            return self._row_data_header[row]
        else:
            if row == 0:
                return ()
            else:
                raise IndexError('index out of range for current row pivot')
    
    def column(self, col):
        if self.pivot_columns:
            return self._column_data_header[col]
        else:
            if col == 0:
                return ()
            else:
                raise IndexError('index out of range for current column pivot')
    
    @property
    def rows(self):
        return self._row_data_header
    
    @property
    def columns(self):
        return self._column_data_header
    
    def delete_row_col_values(self, index, mask_other_index = [], direction = 'row'):
        """Deletes values for given index and mask of other index"""
        if direction not in ['row','column']:
            raise ValueError('direction must be a str with value "row" or "column"')
        if direction == 'row':
            if not all(m <= len(self._row_data_header) or m < 0 for m in index):
                raise ValueError('index must be valid index for row pivot')
            if not all(m <= len(self._column_data_header) or m < 0 for m in mask_other_index):
                raise ValueError('mask_other_index must be valid index for column pivot')
            key_getter = self._key_getter
            invalid_first = self._invalid_row
            invalid_other = self._invalid_column
            other_index_name = self.pivot_columns
            other_index_headers = self._column_data_header
            first_key_getter = self.row
            other_key_getter = self.column
        elif direction == 'column':
            if not all(m <= len(self._column_data_header) or m < 0 for m in index):
                raise ValueError('index must be valid index for column pivot')
            if not all(m <= len(self._row_data_header) or m < 0 for m in mask_other_index):
                raise ValueError('mask_other_index must be valid index for row pivot')
            # keygetter with column as first index
            order = tuple(self.index_names.index(i) for i in self.pivot_columns + self.pivot_rows + self.pivot_frozen)
            order = tuple(sorted(range(len(order)),key=order.__getitem__))
            key_getter = operator.itemgetter(*order)
            invalid_first = self._invalid_column
            invalid_other = self._invalid_row
            other_index_name = self.pivot_rows
            other_index_headers = self._row_data_header
            first_key_getter = self.column
            other_key_getter = self.row
        if not mask_other_index:
            # no mask given, delete all indexes of other index
            if not other_index_name:
                mask_other_index = [0]
            else:
                mask_other_index = range(len(other_index_headers))
        else:
            # check that mask is valid
            if not other_index_name:
                if not len(mask_other_index) == 1 and mask_other_index[0] == 0:
                    raise ValueError('mask_other_index contains invalid index values, no dimension in other pivot, only [0] is allowed')
            elif not all(i >= 0 and i < len(other_index_headers) for i in mask_other_index):
                raise ValueError('mask_other_index contains invalid index values for other pivot header')
        # delete values
        for i in index:
            i_invalid = i in invalid_first
            key_first = first_key_getter(i)
            for i_other in mask_other_index:
                if i_other in invalid_other or i_invalid:
                    # delete invalid data
                    self._invalid_data.pop((i, i_other), None)
                else:
                    key_other = other_key_getter(i_other)
                    key = key_getter(key_first + key_other + self.frozen_value)
                    self._delete_data(key)

    def delete_tuple_index_values(self, delete_tuples):
        """deletes values from keys with combination of indexes given that match tuple_index_entries"""
        # delete from tuple indexes
        delete_values = set()
        delete_values_row = set()
        delete_values_column = set()
        for tk in self.tuple_index_entries.keys():
            for names, indexes in delete_tuples.items():
                if set(names) == set(tk):
                    # reorder to same index order
                    pos = [tk.index(n) for n in names]
                    getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                    indexes = set(getter(i) for i in indexes)
                    remove_set = set(row for row in self.tuple_index_entries[tk] if row in indexes)
                    self.tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self._added_tuple_index_entries:
                        self._added_tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self._deleted_tuple_index_entries:
                        self._deleted_tuple_index_entries[tk].update(remove_set)
                    else:
                        self._deleted_tuple_index_entries[tk] = remove_set
                    # delete values from _data
                    pos = [tk.index(n) for n in self.index_names if n in tk]
                    getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                    delete_values.update(set(k for k in self._data if getter(k) in indexes))
                    # delete values from headers
                    if all(n in self.pivot_rows for n in tk):
                        # tuple exists over rows
                        pos = [tk.index(n) for n in self.pivot_rows if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        row_indexes = set(getter(i) for i in indexes)
                        pos = [self.pivot_rows.index(n) for n in self.pivot_rows if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        delete_values_row.update(set(n for n in self._row_data_header if getter(n) in row_indexes))
                    # delete values from column headers
                    if all(n in self.pivot_columns for n in tk):
                        # tuple exists over columns
                        pos = [tk.index(n) for n in self.pivot_columns if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        column_indexes = set(getter(i) for i in indexes)
                        pos = [self.pivot_columns.index(n) for n in self.pivot_columns if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        delete_values_column.update(set(n for n in self._column_data_header if getter(n) in column_indexes))
        if delete_values:
            # delete values from data dict
            for k in delete_values:
                self._delete_data(k)
        # delete from index headers
        if delete_values_row:
            for i, key in reversed(list(enumerate(self._row_data_header))):
                if key in delete_values_row:
                    del_key = self._row_data_header.pop(i)
                    self._row_data_header_set.discard(del_key)
        if delete_values_column:
            for i, key in reversed(list(enumerate(self._column_data_header))):
                if key in delete_values_column:
                    del_key = self._column_data_header.pop(i)
                    self._column_data_header_set.discard(del_key)
    
    def delete_index_values(self, delete_indexes):
        """delete one ore more index value from data"""
        delete_values = {}
        delete_values_row = {}
        delete_values_column = {}
        for k, indexes in delete_indexes.items():
            if k not in self._index_ind or not indexes:
                continue
            dv = set(indexes)
            if k in self.pivot_rows:
                delete_values_row[self.pivot_rows.index(k)] = dv
            if k in self.pivot_columns:
                delete_values_column[self.pivot_columns.index(k)] = dv
            # add existing entries to deleted entries
            self._deleted_index_entries[k].update(self.index_entries[k].intersection(dv))
            # uppdate existing entries
            self.index_entries[k].difference_update(dv)
            # remove any entries in added indexes
            self._added_index_entries[k].difference_update(dv)
            delete_values[self.index_names.index(k)] = dv
        # delete from tuple indexes
        for tk in self.tuple_index_entries.keys():
            for k, indexes in delete_indexes.items():
                if k in tk:
                    pos = tk.index(k)
                    remove_set = set(row for row in self.tuple_index_entries[tk] if row[pos] in indexes)
                    self.tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self._added_tuple_index_entries:
                        self._added_tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self._deleted_tuple_index_entries:
                        self._deleted_tuple_index_entries[tk].update(remove_set)
                    else:
                        self._deleted_tuple_index_entries[tk] = remove_set
        if delete_values:
            # delete values from data dict
            delete_keys = []
            for key in self._data.keys():
                for ind, values in delete_values.items():
                    if key[ind] in values:
                        delete_keys.append(key)
            for key in delete_keys:
                self._delete_data(key)
        # delete from index headers
        if delete_values_row:
            for i, key in reversed(list(enumerate(self._row_data_header))):
                for ind, values in delete_values_row.items():
                    if key[ind] in values:
                        del_key = self._row_data_header.pop(i)
                        self._row_data_header_set.discard(del_key)
        if delete_values_column:
            for i, key in reversed(list(enumerate(self._column_data_header))):
                for ind, values in delete_values_column.items():
                    if key[ind] in values:
                        del_key = self._column_data_header.pop(i)
                        self._column_data_header_set.discard(del_key)

    def _data_to_header(self, data, start_index, index_values, index_names, mask, direction):
        edit_index = []
        new_index = []
        if not data:
            return edit_index, new_index
        if not all(len(data[0]) == len(d) for d in data):
            raise ValueError('data must be a rectangular list of list')
        if direction not in ["row", "column"]:
            raise ValueError('direction must be a str with value "row" or "column"')
        if any(m < 0 for m in mask):
            raise ValueError('invalid index in mask')
        if start_index >= len(index_names):
            return edit_index, new_index

        # find data that fits into index
        if direction == 'row':
            end_index = min(len(index_names) - start_index, len(data[0]))
            data = [row[:end_index] for row in data]
        else:
            end_index = min(len(index_names) - start_index, len(data))
            data = [[data[row][col] for row in range(end_index - start_index + 1)] for col in range(len(data[0]))]
        
        # get header indexes that are going to be updated
        edit_index = [index_values[i] for i in mask if i < len(index_values)]
        
        num_new = end_index - start_index + 1
        replace_from = start_index
        replace_to = replace_from + num_new
        # convert indexes with int type to int
        for c in range(num_new):
            if (index_names[replace_from + c] in self._index_type
                and self._index_type[index_names[replace_from + c]] == int):
                for r in range(len(data)):
                    if isinstance(data[r][c],str) and data[r][c].isdigit():
                        data[r][c] = int(data[r][c])

        # replace old values with pasted values
        new_indexes = range(replace_to - replace_from)
        edit_index = [old[0:replace_from] + tuple(data[row][col] for col in new_indexes) + old[replace_to:] 
                        for row, old in enumerate(edit_index)]
                
        # new header values
        new_index = []
        if len(data) > len(edit_index):
            none_tuple = tuple(None for _ in range(len(index_names)))
            before = none_tuple[0:replace_from]
            after = none_tuple[replace_to:]
            new_index = [before + tuple(data[row][col] for col in new_indexes) + after for row in range(len(edit_index), len(data))]
        return edit_index, new_index

    def paste_data(self, row_start = 0, row_header_data = [], col_start = 0, col_header_data = [], data = [], row_mask = [], col_mask = []):
        """Paste a list of list into current view of AbstractTable"""
        if row_header_data:
            edit_rows, add_rows = self._data_to_header(row_header_data, row_start, self._row_data_header, self.pivot_rows, row_mask, "row")
            self.edit_index(edit_rows + add_rows, row_mask, "row")
        if col_header_data:
            edit_columns, add_columns = self._data_to_header(col_header_data, col_start, self._column_data_header, self.pivot_columns, col_mask, "column")
            self.edit_index(edit_columns + add_columns, col_mask, "column")
        # paste data
        if data:
            self.set_pivoted_data(data, row_mask, col_mask)

    def edit_index(self, new_index, index_mask, direction):
        """Edits the index of either row or column"""
        if direction == "row":
            index_name = self.pivot_rows
            other_index_name = self.pivot_columns
            edit_index = self._row_data_header
            edit_index_set = self._row_data_header_set
            invalid_set = self._invalid_row
            other_index = self._column_data_header
            other_invalid_set = self._invalid_column
            order_getter = operator.itemgetter(*(0,1))
            key_getter = self._key_getter
        elif direction == "column":
            index_name = self.pivot_columns
            other_index_name = self.pivot_rows
            edit_index = self._column_data_header
            edit_index_set = self._column_data_header_set
            invalid_set = self._invalid_column
            other_index = self._row_data_header
            other_invalid_set = self._invalid_row
            order_getter = operator.itemgetter(*(1,0))
            order = tuple(self._index_ind[i] for i in self.pivot_columns + self.pivot_rows + self.pivot_frozen)
            order = tuple(sorted(range(len(order)),key=order.__getitem__))
            key_getter = operator.itemgetter(*order)
        else:
            raise ValueError('parameter direction must be "row" or "column"')
        
        if not other_index_name:
            other_index = [()]
        
        # insert new index entites
        new_indexes = {}
        for i, name in enumerate(index_name):
            for r in new_index:
                index = r[i]
                if self.is_valid_index(index, name) and index not in self.index_entries[name]:
                    self.index_entries[name].add(index)
                    if name in new_indexes:
                        new_indexes[name].add(index)
                    else:
                        new_indexes[name] = set([index])
        
        # update tuple entities
        for k in self.tuple_index_entries.keys():
            if set(k).issubset(index_name + self.pivot_frozen) and not set(self.pivot_frozen).issuperset(k):
                names = [n for n in index_name + self.pivot_frozen]
                valid = [(i, names.index(kn)) for i, kn in enumerate(k) if kn in names]
                keys = tuple(v[1] for v in valid)
                names = tuple(k[v[0]] for v in valid)
                getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
                for line in new_index:
                    new_tuple = getter(tuple(line) + self.frozen_value)
                    if all(self.is_valid_index(i, n) for i, n in zip(new_tuple, names)):
                        if new_tuple not in self.tuple_index_entries[k]:
                            self.tuple_index_entries[k].add(new_tuple)
                            if k in self._added_tuple_index_entries:
                                self._added_tuple_index_entries[k].add(new_tuple)
                            else:
                                self._added_tuple_index_entries[k] = set([new_tuple])
        
        # change data values since their index is changed
        for i, new_key in zip(index_mask, new_index):
            if i < len(edit_index) and edit_index[i] == new_key:
                # same as old key, do nothing
                continue
            if self.is_valid_key(new_key, edit_index_set, index_name):
                # key is valid
                edit_index_set.add(new_key)
                if i >= len(edit_index):
                    # outside old data do nothing
                    continue
                if i in invalid_set:
                    # previous key was invalid move data from invalid to valid
                    invalid_set.discard(i)
                    for c, other_key in enumerate(other_index):
                        row_col_index = order_getter((i, c))
                        if c not in other_invalid_set and row_col_index in self._invalid_data:
                            key = key_getter(new_key + other_key + self.frozen_value)
                            value = self._invalid_data.pop(row_col_index)
                            self._add_data(key, value)
                else:
                    # previous key vas valid, move data to new key
                    old_index_key = edit_index[i]
                    edit_index_set.remove(old_index_key)
                    for c, other_key in enumerate(other_index):
                        old_key = key_getter(old_index_key + other_key + self.frozen_value)
                        if c not in other_invalid_set and old_key in self._data:
                            key = key_getter(new_key + other_key + self.frozen_value)
                            old_val = self._data[old_key]
                            self._delete_data(old_key)
                            self._add_data(key, old_val)
            else:
                # key is invalid
                if i < len(edit_index):
                    old_index_key = edit_index[i]
                    if old_index_key in edit_index_set and i not in invalid_set:
                        # previous key was valid, remove from set
                        edit_index_set.remove(old_index_key)
                    if i not in invalid_set:
                        # move data to invalid data
                        old_index_key = edit_index[i]
                        for c, other_key in enumerate(other_index):
                            old_key = key_getter(old_index_key + other_key + self.frozen_value)
                            if c not in other_invalid_set and old_key in self._data:
                                row_col_index = order_getter((i, c ))
                                self._invalid_data[row_col_index] = self._data[old_key]
                                self._delete_data(old_key)
                invalid_set.add(i)

        # add new values
        for i, new_key in zip(index_mask, new_index):
            if i < len(edit_index):
                edit_index[i] = new_key
            else:
                edit_index.append(new_key)

        # update header arrays
        if direction == "row":
            self._row_data_header = edit_index
            self._row_data_header_set = edit_index_set
            self._invalid_row = invalid_set
        elif direction == "column":
            self._column_data_header = edit_index
            self._column_data_header_set = edit_index_set
            self._invalid_column = invalid_set
        return new_indexes

    def is_valid_index(self, index, index_name):
        """checks if if given index value is a valid value for given index"""
        if not index:
            # index value cannot be empty/None
            return False
        if not isinstance(index, self._index_type[index_name]):
            # index is not correct type
            return False
        if index_name in self._valid_index_values and self._valid_index_values[index_name]:
            # check if there is any valid values for index
            if index not in self._valid_index_values[index_name]:
                # index is not in valid values
                return False
        return True
    
    def is_valid_key(self, key, existing_keys, key_names):
        """Checks if given key (combination of indexes) is valid"""
        if not all(self.is_valid_index(index, index_name) for index, index_name in zip(key, key_names)):
            return False
        if key in existing_keys:
            # key cannot be a duplicate of existing keys in index.
            return False
        return True


class QPivotTableModel(QAbstractTableModel):
    def __init__(self, parent = None):
        super(QPivotTableModel, self).__init__(parent)
        self.model = PivotModel()
        self._data_header = [[]]
        self._num_headers_row = 0
        self._num_headers_column = 0
    
    def _update_header_data(self):
        """updates the top left corner 'header' data"""
        self._num_headers_row = len(self.model.pivot_columns) + min(1,len(self.model.pivot_rows))
        self._num_headers_column = max(len(self.model.pivot_rows),1)
        if self.model.pivot_columns:
            headers = [[None for _ in range(self._num_headers_column-1)] + [c] for c in self.model.pivot_columns]
            if self.pivot_index:
                headers.append(self.model.pivot_rows)
        else:
            headers = [self.model.pivot_rows]
        self._data_header = headers
    
    def dataRowCount(self):
        """number of rows that contains actual data"""
        return len(self.model._row_data_header)
        
    def dataColumnCount(self):
        """number of columns that contains actual data"""
        return len(self.model._column_data_header)

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in table, number of header rows + datarows + 1 empty row"""
        return self._num_headers_row + self.dataRowCount() + 1

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in table, number of header columns + datacolumns + 1 empty columns"""
        return self._num_headers_column + self.dataColumnCount() + 1
    
    def flags(self, index):
        """Roles for data"""
        if index.row() < self._num_headers_row and index.column() < self._num_headers_column:
            return super(QPivotTableModel, self).flags(index)
        elif self.pivot_index and self.pivot_columns and index.row() == self._num_headers_row - 1 and index.column() >= self._num_headers_column:
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super(QPivotTableModel, self).flags(index)
    
    def index_in_data(self,index):
        """check if index is in data area"""
        if (self.dataRowCount() == 0 and self.model.pivot_rows or
            self.dataColumnCount() == 0 and self.model.pivot_columns):
            # no data
            return False
        return (index.row() >= self._num_headers_row
                and index.column() >= self._num_headers_column
                and index.row() < self._num_headers_row + max(1,self.dataRowCount())
                and index.column() < self._num_headers_column + max(1,self.dataColumnCount()))
    
    def index_in_column_headers(self, index):
        """check if index is in column headers (horizontal) area"""
        return (index.row() < self._num_headers_row 
                and index.column() >= self._num_headers_column
                and index.column() < self.columnCount() - 1)
    
    def index_in_row_headers(self, index):
        """check if index is in row headers (vertical) area"""
        return (self.pivot_index
                and index.row() >= self._num_headers_row
                and index.column() < self._num_headers_column
                and index.row() < self.rowCount() - 1)
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self.index_in_data(index):
                # get values
                data = self.model.get_pivoted_data([index.row() - self._num_headers_row],[index.column() - self._num_headers_column])
                data = data[0][0]
                return '' if data is None else str(data)
            elif self.index_in_column_headers(index):
                # draw column header values
                if not self.model.pivot_rows:
                    # when special case when no pivot_index, no empty line padding
                    return self.model._column_data_header[index.column() - self._num_headers_column][index.row()]
                elif index.row() < self._num_headers_row - 1:
                    return self.model._column_data_header[index.column() - self._num_headers_column][index.row()]
            elif self.index_in_row_headers(index):
                # draw index values
                return self.model._row_data_header[index.row() - self._num_headers_row][index.column()]
            elif (index.row() < self._num_headers_row
                  and index.column() < self._num_headers_column):
                # draw header values
                return self._data_header[index.row()][index.column()]
            else:
                return None
        elif role == Qt.BackgroundColorRole:
            return self.data_color(index)
        else:
            return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return None
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return None
    
    def data_color(self, index):
        if self.index_in_data(index):
            # color edited values
            pass
        elif self.index_in_column_headers(index) and index.column() in self.model._invalid_column:
            # color invalid columns
            pass
        elif self.index_in_row_headers(index) and index.row() in self.model._invalid_row:
            # color invalid rows
            pass
        


def tuple_itemgetter(itemgetter_func, num_indexes):
    """Change output of itemgetter to always be a tuple even for one index"""
    if num_indexes == 1:
        def g(item):
            return (itemgetter_func(item),)
        return g
    else:
        return itemgetter_func

class PivotTableSortFilterProxy(QSortFilterProxyModel):
    
    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.index_filters = {}

    def setSourceModel(self, source_model):
        super().setSourceModel(source_model)
    
    def set_filter(self, index_name, filter_value):
        self.index_filters[index_name] = filter_value
        self.invalidateFilter() # trigger filter update
    
    def clear_filter(self):
        self.index_filters = {}
        self.invalidateFilter() # trigger filter update
    
    def accept_index(self, index, index_names):
        accept = True
        for i, n in zip(index, index_names):
            if self.index_filters.get(n) and i not in self.index_filters[n]:
                accept = False
                break
        return accept
    
    def delete_row_col(self, delete_indexes, direction):
        delete_indexes = [self.mapToSource(index) for index in delete_indexes]
        self.sourceModel().delete_row_col(delete_indexes, direction)
        
    def paste_data(self, index, data):
        model_index = self.mapToSource(index)
        row_mask = []
        for r in range(model_index.row(), self.sourceModel().dataRowCount() + self.sourceModel()._num_headers_row):
            if self.filterAcceptsRow(r, None):
                row_mask.append(r)
                if len(row_mask) == len(data):
                    break
        col_mask = []
        for c in range(model_index.column(), self.sourceModel().dataColumnCount() + self.sourceModel()._num_headers_column):
            if self.filterAcceptsColumn(c, None):
                col_mask.append(c)
                if len(col_mask) == len(data[0]):
                    break
        self.sourceModel().paste_data(model_index, data, row_mask, col_mask)
    
    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        All the rules and subrules need to pass.
        """
        
        if source_row < self.sourceModel()._num_headers_row or source_row == self.sourceModel().rowCount() - 1:
            # always display headers
            return True
        elif source_row in self.sourceModel()._invalid_row:
            return True
        else:
            if self.sourceModel().pivot_index:
                index = self.sourceModel()._data_index[source_row - self.sourceModel()._num_headers_row]
                return self.accept_index(index, self.sourceModel().pivot_index)
            else:
                return True

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if (source_column < self.sourceModel()._num_headers_column
            or source_column == self.sourceModel().columnCount() - 1):
            # always display headers
            return True
        elif source_column in self.sourceModel()._invalid_column:
            return True
        else:
            if self.sourceModel().pivot_columns:
                index = self.sourceModel()._data_columns[source_column - self.sourceModel()._num_headers_column]
                return self.accept_index(index, self.sourceModel().pivot_columns)
            else:
                return True

class PivotTableModel(QAbstractTableModel):
    """A class that models dict data as a pivotable table without aggregation.
    """
    indexEntriesChanged = Signal(object, dict, dict) #signals when enteties in each index has changed
    def __init__(self, data, index_names, index_type, parent = None):
        super(PivotTableModel, self).__init__(parent)
        
        # stores edited and deleted data
        self._edit_data = {}
        self._data_deleted = set()
        # operator.itemgetter placeholder
        self._key_getter = lambda *x: () 
        # actual data as a dict
        self._data = {}
        # row and column indexes of current pivot
        self._data_index = []
        self._data_columns = []
        # sets of column and row indexes of current pivot for comparisions
        self._data_index_set = set()
        self._data_columns_set = set()
        # dictionary wiht index name to index in self.index_names
        self._index_ind = {}
        
        # number of rows and columns of top left corner where index names are displayed
        self._num_headers_row = 0
        self._num_headers_column = 0
        # list of list that stores the top left corner data
        self._data_header = []
        
        # name and type of indexes
        self.index_names = ()
        self.index_type = {}
        
        # the pivot of the model
        self.frozen_index = ()
        self.pivot_index = ()
        self.pivot_columns = ()
        self.pivot_frozen = ()
        
        # index values for each index and for a tuple of indexes
        self.index_entries = {}
        self.tuple_index_entries = {}

        # stores rows and columns where the index is invalid
        # and data inserted into those rows/columns
        self._invalid_row = {}
        self._invalid_column = {}
        self._invalid_data = {}
        
        # dictionary to store set or range of valid values for each index.
        self.valid_index_values = {}
        
        # keeps track of added and deleted index entries
        self.added_index_entries = {}
        self.deleted_index_entries = {}
        self.added_tuple_index_entries = {}
        self.deleted_tuple_index_entries = {}
        
        self.set_new_data(data, index_names, index_type)

    def set_new_data(self, data, index_names, index_type, index=(), columns=(), frozen=(), frozen_value=() , valid_index_values={}, tuple_index_entries={}):
        """set the data of the model, index names and any additional indexes that don't have data, valid index values.
        """
        if len(index_names) != len(index_type):
            raise ValueError('index_names and index_type must have same length')
        if data and any(len(d) < len(index_names) + 1 for d in data):
            raise ValueError('data inner lists be of length >= len(index_names) + 1')
        if not all(t in [str, int] for t in index_type):
            raise ValueError('index_type can only contain str or int type')

        if not index + columns + frozen:
            # no pivot given, set default pivot
            index = tuple(index_names)
            columns = ()
            frozen = ()
            frozen_value = ()
        else:
            #check given pivot
            pivot_error = self.is_invalid_pivot(index, columns, frozen, frozen_value, index_names)
            if pivot_error:
                raise pivot_error
            
        #self.beginResetModel()
        self.valid_index_values = valid_index_values
        self._edit_data = {}
        self._index_ind = {index: ind for ind, index in enumerate(index_names)}
        # create data dict with keys as long as index_names
        self._data = {tuple(d[:len(index_names)]):d[len(index_names)] for d in data}
        key = tuple(self._index_ind[i] for i in index_names)
        self._key_getter = tuple_itemgetter(operator.itemgetter(*key), len(key))
        self.index_names = tuple(index_names)
        self.index_type = {index_names[i]: it for i, it in enumerate(index_type)}
        self.index_entries = {}
        self.tuple_index_entries = {}
        self.added_index_entries = {}
        self.added_tuple_index_entries = {}
        self.deleted_tuple_index_entries = {}
        self.deleted_index_entries = {}
        self.pivot_index = tuple(index)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        
        # get all index values from data
        for i, c in enumerate(self.index_names):
            self.index_entries[c] = set(d[i] for d in self._data.keys())
            self.added_index_entries[c] = set()
            self.deleted_index_entries[c] = set()
        # add tuple entries
        for k, v in tuple_index_entries.items():
            keys = tuple(self._index_ind[i] for i in k)
            getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
            self.tuple_index_entries[k] = set(getter(key) for key in self._data.keys())
            self.tuple_index_entries[k].update(v)

        self.setPivot(index, columns, frozen, frozen_value)

    def set_frozen_value(self, value):
        """Sets the value of the frozen indexes"""
        if len(value) != len(self.pivot_frozen):
            raise ValueError("'value' must have same lenght as 'self.pivot_frozen'")
        if value == self.frozen_value:
            #same as previous do nothing
            return
        self.frozen_value = tuple(value)
        self.setPivot(self.pivot_index, self.pivot_columns, self.pivot_frozen, value)
    
    def is_invalid_pivot(self, index, columns, frozen, frozen_value, index_names):
        error = None
        if not all(i in index_names for i in frozen):
            error = ValueError("'frozen' contains values that doesn't match with current 'index_names'")
        if not all(i in index_names for i in index):
            error = ValueError("'index' contains values that doesn't match with current 'index_names'")
        if not all(c in index_names for c in columns):
            error = ValueError("'columns' contains values that doesn't match with current 'index_names'")
        if len(set(index + columns + frozen)) != len(index_names):
            error = ValueError("'index', 'columns' and 'forzen' must contain all unqiue variables in 'index_names' without duplicates")
        if len(frozen) != len(frozen_value):
            error = ValueError("'frozen_value' must be same length as 'frozen'")
        return error

    def setPivot(self, index, columns, frozen, frozen_value):
        """Sets pivot for current data"""
        pivot_error = self.is_invalid_pivot(index, columns, frozen, frozen_value, self.index_names)
        if pivot_error:
            raise pivot_error

        self.beginResetModel()
        self.pivot_index = index
        self.pivot_columns = columns
        self.pivot_frozen = frozen
        self.frozen_value = tuple(frozen_value)
        # set key_getter so that you will get a correct key for _data when doing
        # _key_getter(row_key + col_key + frozen_value)
        order = tuple(self._index_ind[i] for i in self.pivot_index + self.pivot_columns + self.pivot_frozen)
        order = tuple(sorted(range(len(order)),key=order.__getitem__))
        self._key_getter = tuple_itemgetter(operator.itemgetter(*order), len(order))
        
        # find unique set of tuples for row and column headers from data with given pivot
        # row indexes
        if len(self.pivot_index) > 0:
            keys = tuple(self._index_ind[i] for i in self.pivot_index)
            ind_getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
            if self.pivot_frozen:
                keys = tuple(self._index_ind[i] for i in self.pivot_frozen)
                frozen_getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
                index_values = set(ind_getter(k) for k in self._data.keys() if all(ind_getter(k)) and frozen_getter(k) == self.frozen_value)
            else:
                index_values = set(ind_getter(k) for k in self._data.keys() if all(ind_getter(k)))
        else:
            index_values = [()]
        # column indexes
        if len(self.pivot_columns) > 0:
            keys = tuple(self._index_ind[i] for i in self.pivot_columns)
            col_getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
            if self.pivot_frozen:
                keys = tuple(self._index_ind[i] for i in self.pivot_frozen)
                frozen_getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
                column_values = set(col_getter(k) for k in self._data.keys() if all(col_getter(k)) and frozen_getter(k) == self.frozen_value)
            else:
                column_values = set(col_getter(k) for k in self._data.keys() if all(col_getter(k)))
        else:
            column_values = [()]

        # keep unique values
        self._data_index_set = set(index_values)
        self._data_columns_set = set(column_values)

        # add tuple entries to row and column indexes if given
        # only add tuples where all indexes are found in pivot + frozen_value
        for k in self.tuple_index_entries.keys():
            # row items
            if set(k).issubset(self.pivot_frozen + self.pivot_index) and not set(self.pivot_frozen).issuperset(k):
                position = [i for i, name in enumerate(k) if name in self.pivot_index]
                position_current = [self.pivot_index.index(name) for name in k if name in self.pivot_index]
                position_current_frozen = [self.pivot_frozen.index(name) for name in k if name in self.pivot_frozen]
                getter_current = tuple_itemgetter(operator.itemgetter(*tuple(position_current)), len(position_current))
                getter = operator.itemgetter(*tuple(position))
                v = self.tuple_index_entries[k]
                if self.pivot_frozen and position_current_frozen:
                    position_frozen = [i for i, name in enumerate(k) if name in self.pivot_frozen]
                    getter_frozen_current = tuple_itemgetter(operator.itemgetter(*tuple(position_current_frozen)), len(position_current_frozen))
                    getter_frozen = tuple_itemgetter(operator.itemgetter(*tuple(position_frozen)), len(position_frozen))
                    v = set(getter(i) for i in v if getter_frozen(i) == getter_frozen_current(self.frozen_value))
                
                current_set = set(getter_current(d) for d in self._data_index_set)
                v = v.difference(current_set)
                none_key = [None for _ in self.pivot_index]
                add_keys = set()
                new_entries = {name: set() for name in k}
                for key in v:
                    if not isinstance(key, tuple):
                        key = (key,)
                    new_key = none_key
                    for i, ki in enumerate(position_current):
                        new_key[ki] = key[i]
                        new_entries[k[i]].add(key[i])
                    add_keys.add(tuple(new_key))
                self._data_index_set.update(add_keys)
                for name in k:
                    self.index_entries[name].update(new_entries[name])
            # column items
            if set(k).issubset(self.pivot_frozen + self.pivot_columns) and not set(self.pivot_frozen).issuperset(k):
                position = [i for i, name in enumerate(k) if name in self.pivot_columns]
                position_current = [self.pivot_columns.index(name) for name in k if name in self.pivot_columns]
                position_current_frozen = [self.pivot_frozen.index(name) for name in k if name in self.pivot_frozen]
                getter_current = operator.itemgetter(*tuple(position_current))
                getter = operator.itemgetter(*tuple(position))
                v = self.tuple_index_entries[k]
                if self.pivot_frozen and position_current_frozen:
                    position_frozen = [i for i, name in enumerate(k) if name in self.pivot_frozen]
                    getter_frozen_current = operator.itemgetter(*tuple(position_current_frozen))
                    getter_frozen = operator.itemgetter(*tuple(position_frozen))
                    v = set(getter(i) for i in v if getter_frozen(i) == getter_frozen_current(self.frozen_value))
                
                current_set = set(getter_current(d) for d in self._data_columns_set)
                v = v.difference(current_set)
                none_key = [None for _ in self.pivot_columns]
                add_keys = set()
                new_entries = {name: set() for name in k}
                for key in v:
                    if not isinstance(key, tuple):
                        key = (key,)
                    new_key = none_key
                    for i, ki in enumerate(position_current):
                        new_key[ki] = key[i]
                        new_entries[k[i]].add(key[i])
                    add_keys.add(tuple(new_key))
                self._data_columns_set.update(add_keys)
                for name in k:
                    self.index_entries[name].update(new_entries[name])
        
        # remove duplicates with none type
        # row indexes
        tuples_with_none = [t for t in self._data_columns_set if not all(t)]
        # find set of indices which contain all not none elements
        index_without_none = set(tuple(i for i, item in enumerate(index_tuple) if item != None) for index_tuple in tuples_with_none)
        for ind in index_without_none:
            getter = tuple_itemgetter(operator.itemgetter(*ind), len(ind))
            existing_index = set(getter(t) for t in self._data_columns_set if all(t))
            none_index = set(t for t in tuples_with_none if all(getter(t)))
            remove_index = set(t for t in none_index if getter(t) in existing_index)
            self._data_columns_set.difference_update(remove_index)
            
        # remove duplicates with none type
        # column indexes
        tuples_with_none = [t for t in self._data_index_set if not all(t)]
        # find which index that is not None
        index_without_none = set(tuple(i for i, item in enumerate(index_tuple) if item != None) for index_tuple in tuples_with_none)
        for ind in index_without_none:
            getter = tuple_itemgetter(operator.itemgetter(*ind), len(ind))
            existing_index = set(getter(t) for t in self._data_index_set if all(t))
            none_index = set(t for t in tuples_with_none if all(getter(t)))
            remove_index = set(t for t in none_index if getter(t) in existing_index)
            self._data_index_set.difference_update(remove_index)
            
        
        _data_columns_none_set = set(t for t in self._data_columns_set if not all(t))
        _data_index_none_set = set(t for t in self._data_index_set if not all(t))
        self._data_columns_set = set(t for t in self._data_columns_set if all(t))
        self._data_index_set = set(t for t in self._data_index_set if all(t))
        # sort indexes without Nones
        self._data_index = sorted(self._data_index_set)
        self._data_columns = sorted(self._data_columns_set)
        # add indexes where tuple values can be None
        self._data_index.extend(sorted(_data_index_none_set, key=lambda x:tuple((i is None, i) for i in x)))
        self._data_columns.extend(sorted(_data_columns_none_set, key=lambda x:tuple((i is None, i) for i in x)))
        
        # update top left corner data
        self._update_header_data()
        
        # set invalid data to indexes with none in them.
        self._invalid_row = {i + self._num_headers_row: key for i, key in enumerate(self._data_index) if not all(key)}
        self._invalid_column = {i + self._num_headers_column: key for i, key in enumerate(self._data_columns) if not all(key)}
        self._invalid_data = {}
        
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)
    
    def _update_header_data(self):
        """updates the top left corner 'header' data"""
        self._num_headers_row = len(self.pivot_columns) + min(1,len(self.pivot_index))
        self._num_headers_column = max(len(self.pivot_index),1)
        if self.pivot_columns:
            headers = [[None for _ in range(self._num_headers_column-1)] + [c] for c in self.pivot_columns]
            if self.pivot_index:
                headers.append(self.pivot_index)
        else:
            headers = [self.pivot_index]
        self._data_header = headers
        
    def paste_data_in_values(self, index, data, row_mask = [], col_mask = []):
        """paste list of lists into current view of the data"""
        if not data:
            # no data
            return
        top_left_row = index.row() - self._num_headers_row
        top_left_col = index.column() - self._num_headers_column
        num_rows = min(self.dataRowCount() - top_left_row, len(data))
        num_cols = min(self.dataColumnCount() - top_left_col, len(data[0]))
        
        if self.pivot_index:
            if row_mask:
                row_indexes = [r for r in row_mask if r >= 0 and r < self.dataRowCount()]
                if len(row_indexes) > len(data):
                    row_indexes = row_indexes[:len(data)]
            else:
                row_indexes = range(top_left_row, num_rows + top_left_row)
        else:
            row_indexes = [len(self.pivot_index)]
        if self.pivot_columns:
            if col_mask:
                col_indexes = [c for c in col_mask if c >= 0 and c < self.dataColumnCount()]
                if len(col_indexes) > len(data[0]):
                    col_indexes = col_indexes[:len(data[0])]
            else:
                col_indexes = range(top_left_col, num_cols + top_left_col)
        else:
            col_indexes = [len(self.pivot_columns)]
        
        for paste_row, row in enumerate(row_indexes):
            r = self._data_index[row]
            invalid_row = row + self._num_headers_row in self._invalid_row
            for paste_col, col in enumerate(col_indexes):
                if invalid_row or col + self._num_headers_column in self._invalid_column:
                    invalid_index = (row + self._num_headers_row, col + self._num_headers_column)
                    # row or col invalid, put data in invald data dict
                    if not data[paste_row][paste_col] or data[paste_row][paste_col].isspace():
                        # value is None or whitspace remove any existing data
                        self._invalid_data.pop(invalid_index, None)
                    else:
                        # update invalid data
                        self._invalid_data[invalid_index] = data[paste_row][paste_col]
                else:
                    # insert data into dict
                    c = self._data_columns[col]
                    key = self._key_getter(r + c + self.frozen_value)
                    if not data[paste_row][paste_col] or data[paste_row][paste_col].isspace():
                        # value is None or whitspace remove any existing data
                        if key in self._data:
                            self._data_deleted.add(key)
                        self._data.pop(key, None)
                        self._edit_data.pop(key, None)
                    else:
                        # update data
                        self._data[key] = data[paste_row][paste_col]
                        self._edit_data[key] = 1

    def delete_tuple_index_values(self, delete_tuples):
        """deletes values from keys with combination of indexes given that match tuple_index_entries"""
        # delete from tuple indexes
        delete_values = set()
        delete_values_index = set()
        delete_values_column = set()
        self.beginResetModel()
        for tk in self.tuple_index_entries.keys():
            for names, indexes in delete_tuples.items():
                if set(names) == set(tk):
                    # reorder to same index order
                    pos = [tk.index(n) for n in names]
                    getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                    indexes = set(getter(i) for i in indexes)
                    remove_set = set(row for row in self.tuple_index_entries[tk] if row in indexes)
                    self.tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self.added_tuple_index_entries:
                        self.added_tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self.deleted_tuple_index_entries:
                        self.deleted_tuple_index_entries[tk].update(remove_set)
                    else:
                        self.deleted_tuple_index_entries[tk] = remove_set
                    # delete values from _data
                    pos = [tk.index(n) for n in self.index_names if n in tk]
                    getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                    delete_values.update(set(k for k in self._data if getter(k) in indexes))
                    # delete values from row headers
                    if any(n in self.pivot_index for n in tk):
                        pos = [tk.index(n) for n in self.pivot_index if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        row_indexes = set(getter(i) for i in indexes)
                        pos = [self.pivot_index.index(n) for n in self.pivot_index if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        delete_values_index.update(set(n for n in self._data_index if getter(n) in row_indexes))
                    # delete values from column headers
                    if any(n in self.pivot_columns for n in tk):
                        pos = [tk.index(n) for n in self.pivot_columns if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        column_indexes = set(getter(i) for i in indexes)
                        pos = [self.pivot_columns.index(n) for n in self.pivot_columns if n in tk]
                        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                        delete_values_column.update(set(n for n in self._data_columns if getter(n) in column_indexes))
        if delete_values:
            # delete values from data dict
            for k in delete_values:
                self._data.pop(k, None)
                self._edit_data.pop(k, None)
        # delete from index headers
        if delete_values_index:
            for i, key in reversed(list(enumerate(self._data_index))):
                if key in delete_values_index:
                    del_key = self._data_index.pop(i)
                    self._data_index_set.discard(del_key)
        if delete_values_column:
            for i, key in reversed(list(enumerate(self._data_columns))):
                if key in delete_values_column:
                    del_key = self._data_columns.pop(i)
                    self._data_columns_set.discard(del_key)
        self.endResetModel()
    
    def delete_index_values(self, delete_indexes):
        """delete one ore more index value from data"""
        delete_values = {}
        delete_values_index = {}
        delete_values_column = {}
        self.beginResetModel()
        for k, indexes in delete_indexes.items():
            if k not in self._index_ind or not indexes:
                continue
            dv = set(indexes)
            index_ind = [i for i, v in enumerate(self.pivot_index) if v == k]
            if index_ind:
                delete_values_index[index_ind[0]] = dv
            column_ind = [i for i, v in enumerate(self.pivot_columns) if v == k]
            if column_ind:
                delete_values_column[column_ind[0]] = dv
            # add existing entries to deleted entries
            self.deleted_index_entries[k].update(self.index_entries[k].intersection(dv))
            # uppdate existing entries
            self.index_entries[k].difference_update(dv)
            # remove any entries in added indexes
            self.added_index_entries[k].difference_update(dv)
            delete_values[self._index_ind[k]] = dv
        # delete from tuple indexes
        for tk in self.tuple_index_entries.keys():
            for k, indexes in delete_indexes.items():
                if k in tk:
                    pos = tk.index(k)
                    remove_set = set(row for row in self.tuple_index_entries[tk] if row[pos] in indexes)
                    self.tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self.added_tuple_index_entries:
                        self.added_tuple_index_entries[tk].difference_update(remove_set)
                    if tk in self.deleted_tuple_index_entries:
                        self.deleted_tuple_index_entries[tk].update(remove_set)
                    else:
                        self.deleted_tuple_index_entries[tk] = remove_set
        if delete_values:
            # delete values from data dict
            delete_keys = []
            for key in self._data.keys():
                for ind, values in delete_values.items():
                    if key[ind] in values:
                        delete_keys.append(key)
            for k in delete_keys:
                self._data.pop(k)
                self._edit_data.pop(k, None)
        # delete from index headers
        if delete_values_index:
            for i, key in reversed(list(enumerate(self._data_index))):
                for ind, values in delete_values_index.items():
                    if key[ind] in values:
                        del_key = self._data_index.pop(i)
                        self._data_index_set.discard(del_key)
        if delete_values_column:
            for i, key in reversed(list(enumerate(self._data_columns))):
                for ind, values in delete_values_column.items():
                    if key[ind] in values:
                        del_key = self._data_columns.pop(i)
                        self._data_columns_set.discard(del_key)
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)
        if delete_values:
            self.update_index_entries({}, delete_values)

    def delete_row_col(self, delete_indexes, direction):
        """Delete one ore more rows/columns from current view"""
        # TODO: this currently removes all data for selected row or col even if
        #       those are hidden. Change so only visible values are removed
        if not delete_indexes:
            return
        if direction == "row":
            self.beginResetModel()
            deleted_keys = []
            delete_indexes = sorted(set(d.row() for d in delete_indexes if d.row() >= self._num_headers_row and d.row() < self._num_headers_row + len(self._data_index)))
            for r in delete_indexes:
                ind = r - self._num_headers_row
                row_key = self._data_index[ind]
                self._data_index_set.discard(row_key)
                if r in self._invalid_row:
                    # delete invalid column
                    self._invalid_row.pop(r, None)
                    for c, col_key in enumerate(self._data_columns):
                        self._invalid_data.pop((r, c + self._num_headers_column), None)
                else:
                    self._invalid_row.pop(r, None)
                    #check if there exists an invalid index with same value
                    new_valid_row = None
                    for k,v in self._invalid_row.items():
                        if v == row_key:
                            new_valid_row = k
                            self._invalid_row.pop(new_valid_row, None)
                            break
                    if not new_valid_row:
                        deleted_keys.append(row_key)
                    # delete or replace old data
                    for c, col_key in enumerate(self._data_columns):
                        key = self._key_getter(row_key + col_key + self.frozen_value)
                        if key in self._data:
                            self._data_deleted.add(key)
                        self._data.pop(key, None)
                        self._edit_data.pop(key, None)
                        invalid_key = (new_valid_row, c + self._num_headers_column)
                        if new_valid_row and invalid_key in self._invalid_data:
                            # move invalid data from the previous invalid column to data.
                            self._data[key] = self._invalid_data.pop(invalid_key)
                            self._edit_data[key] = 1
                            self._data_deleted.discard(key)
                for invalid_row in sorted(self._invalid_row):
                    # shift invalid rows up.
                    if invalid_row > r:
                        self._invalid_row[invalid_row - 1] = self._invalid_row.pop(invalid_row)
                for invalid_index in sorted(self._invalid_data):
                    # shift invalid data one up.
                    if invalid_index[0] > r:
                        new_index = list(invalid_index)
                        new_index[0] = invalid_index[0] - 1
                        self._invalid_data[tuple(new_index)] = self._invalid_data.pop(invalid_index)
            for ind in sorted(delete_indexes, reverse=True):
                del self._data_index[ind - self._num_headers_row]
            self.endResetModel()
            #self.update_index_entries(self.pivot_index, [], deleted_keys)
        elif direction == "column":
            self.beginResetModel()
            deleted_keys = []
            delete_indexes = sorted(set(d.column() for d in delete_indexes if d.column() >= self._num_headers_column and d.column() < self._num_headers_column + len(self._data_columns)))
            for c in delete_indexes:
                ind = c - self._num_headers_column
                col_key = self._data_columns[ind]
                self._data_columns_set.discard(col_key)
                if c in self._invalid_column:
                    # delete invalid column
                    self._invalid_column.pop(c, None)
                    for r, row_key in enumerate(self._data_index):
                        self._invalid_data.pop((r + self._num_headers_row, c), None)
                else:
                    self._invalid_column.pop(c, None)
                    #check if there exists an invalid index with same value
                    new_valid_col = None
                    for k,v in self._invalid_column.items():
                        if v == col_key:
                            new_valid_col = k
                            self._invalid_column.pop(new_valid_col, None)
                            break
                    if not new_valid_col:
                        deleted_keys.append(col_key)
                    # delete or replace old data
                    for r, row_key in enumerate(self._data_index):
                        key = self._key_getter(row_key + col_key + self.frozen_value)
                        if key in self._data:
                            self._data_deleted.add(key)
                        self._data.pop(key, None)
                        self._edit_data.pop(key, None)
                        invalid_key = (r + self._num_headers_row, new_valid_col)
                        if new_valid_col and invalid_key in self._invalid_data:
                            # move invalid data from the previous invalid column to data.
                            self._data[key] = self._invalid_data.pop(invalid_key)
                            self._edit_data[key] = 1
                            self._data_deleted.discard(key)
                for invalid_col in sorted(self._invalid_column):
                    # shift invalid columns left.
                    if invalid_col > c:
                        self._invalid_column[invalid_col - 1] = self._invalid_column.pop(invalid_col)
                for invalid_index in sorted(self._invalid_data):
                    # shift invalid data one to the left.
                    if invalid_index[1] > c:
                        new_index = list(invalid_index)
                        new_index[1] = invalid_index[1] - 1
                        self._invalid_data[tuple(new_index)] = self._invalid_data.pop(invalid_index)
            for ind in sorted(delete_indexes, reverse=True):
                del self._data_columns[ind - self._num_headers_column]
            self.endResetModel()
            #self.update_index_entries(self.pivot_columns, [], deleted_keys)
        else:
            raise ValueError('parameter direction must be "row" or "column"')
    
    def paste_data(self, index, data, row_mask = [], col_mask = []):
        """Paste a list of list into current view of AbstractTable"""
        if not data:
            return
        self.beginResetModel()
        new_col_entities = {}
        new_row_entities = {}

        top_left_data_row = max(index.row(), self._num_headers_row) - self._num_headers_row
        top_left_data_col = max(index.column(), self._num_headers_column) - self._num_headers_column
        
        if self.pivot_index:
            # filter row mask to only contain data rows with data index
            if row_mask:
                row_mask = [r - self._num_headers_row for r in row_mask 
                            if r >= self._num_headers_row 
                            and r < self._num_headers_row + self.dataRowCount()]
            else:
                row_mask = range(top_left_data_row, self.dataRowCount())
        else:
            row_mask = [len(self.pivot_index)]
        if self.pivot_columns:
            # filter column mask to only contain data columns with data index
            if col_mask:
                col_mask = [c - self._num_headers_column for c in col_mask 
                            if c >= self._num_headers_column 
                            and c < self._num_headers_column + self.dataColumnCount()]
            else:
                col_mask = range(top_left_data_col, self.dataColumnCount())
        else:
            col_mask = [len(self.pivot_columns)]
        
        if self.index_in_data(index):
            # paste data only in data, ignore data outside table size
            self.paste_data_in_values(index, data, row_mask, col_mask)
        elif index.row() < self._num_headers_row or index.column() < self._num_headers_column:
            # paste in index or new row/column

            skip_row = 0
            skip_col = 0
            start_row = index.row()
            start_col = index.column()
            if index.column() >= self._num_headers_column:
                # pasted in column headers make no new rows alowed
                num_new_cols = max(0, len(data[0]) - len(col_mask))
                num_new_rows = 0
                # keep only paste data that fits in current rows.
                if row_mask:
                    start_row = row_mask[0] + self._num_headers_row
                data_row = index.row() - self._num_headers_row
                if len(data) + data_row > len(row_mask):
                    new_len = len(row_mask) - data_row
                    data = data[0:new_len]
                # data with only values
                data_values = data[self._num_headers_row - index.row():]
            elif index.row() >= self._num_headers_row:
                # pasted in row headers no new cols alowed
                num_new_rows = max(0, len(data) - len(row_mask))
                num_new_cols = 0
                if col_mask:
                    start_col = col_mask[0] - self._num_headers_column
                data_col = index.column() - self._num_headers_column
                if len(data[0]) + data_col > len(col_mask):
                    new_len = len(col_mask) - data_col
                    data = [d[0:new_len] for d in data]
                # data with only values
                data_values = [d[self._num_headers_column - index.column():] for d in data]
            else:
                # pasted in topleft corner, both new rows and columns allowed.
                skip_row = self._num_headers_row - index.row()
                skip_col = self._num_headers_column - index.column()
                start_row = self._num_headers_row
                start_col = self._num_headers_column
                if not row_mask:
                    num_new_rows = max(0, self.dataRowCount() + len(data) - self.dataRowCount())
                else:
                    num_new_rows = max(0, row_mask[0] + len(data) - self.dataRowCount())
                if not col_mask:
                    num_new_cols = max(0, self.dataColumnCount() + len(data[0]) - self.dataColumnCount())
                else:
                    num_new_cols = max(0, col_mask[0] + len(data[0]) - self.dataColumnCount())
                
                
                # data with only values
                data_values = [d[skip_col:] for d in data[skip_row:]]

            if index.row() < self._num_headers_row:
                # update column indexes
                col_data = [data[row][skip_col:] for row in range(min(len(self.pivot_columns) - index.row(), len(data)))]
                updated_col_index = [self._data_columns[i] for i in col_mask]
                replace_from = index.row()
                replace_to = replace_from + len(col_data)
                
                # convert indexes with int type to int
                for i, line in enumerate(col_data):
                    if (self.pivot_columns[replace_from + i] in self.index_type
                        and self.index_type[self.pivot_columns[replace_from + i]] == int):
                        for k, value in enumerate(line):
                            if value.isdigit():
                                line[k] = int(value)

                # replace old values with pasted values
                new_indexes = range(replace_to - replace_from)
                updated_col_index = [old[0:replace_from] + tuple(col_data[row][col] for row in new_indexes) + old[replace_to:] for col, old in enumerate(updated_col_index)]
                
                # new header values
                new_col_index = []
                new_cols = []
                if num_new_cols > 0:
                    none_tuple = tuple(None for _ in range(len(self.pivot_columns)))
                    before = none_tuple[0:replace_from]
                    after = none_tuple[replace_to:]
                    new_col_index = [before + tuple(col_data[row][col] for row in new_indexes) + after for col in range(len(updated_col_index), len(col_data[0]))]
                    new_cols = list(range(self.dataColumnCount(), self.dataColumnCount() + num_new_cols))

                # edit column indexes
                col_mask = list(col_mask) + new_cols
                new_col_entities = self.edit_index(updated_col_index + new_col_index, col_mask, "column")

            if index.column() < self._num_headers_column:
                # update row indexes
                num_indexes = range(min(len(self.pivot_index) - index.column(),len(data[0])))
                row_data = [[d[col] for col in num_indexes] for d in data[skip_row:]]
                updated_row_index = [self._data_index[i] for i in row_mask]
                replace_from = index.column()
                replace_to = replace_from + len(row_data[0])
                
                # convert indexes with int type to int
                for c in range(len(row_data[0])):
                    if (self.pivot_index[replace_from + c] in self.index_type
                        and self.index_type[self.pivot_index[replace_from + c]] == int):
                        for r in range(len(row_data)):
                            if row_data[r][c].isdigit():
                                row_data[r][c] = int(row_data[r][c])

                # replace old values with pasted values
                new_indexes = range(replace_to - replace_from)
                updated_row_index = [old[0:replace_from] + tuple(row_data[row][col] for col in new_indexes) + old[replace_to:] for row, old in enumerate(updated_row_index)]
                
                # new header values
                new_row_index = []
                new_rows = []
                if num_new_rows > 0:
                    none_tuple = tuple(None for _ in range(len(self.pivot_index)))
                    before = none_tuple[0:replace_from]
                    after = none_tuple[replace_to:]
                    new_row_index = [before + tuple(row_data[row][col] for col in new_indexes) + after for row in range(len(updated_row_index), len(row_data))]
                    new_rows = list(range(self.dataRowCount(), self.dataRowCount() + num_new_rows))
                
                #edit row indexes
                row_mask = list(row_mask) + new_rows
                new_row_entities = self.edit_index(updated_row_index + new_row_index, row_mask, "row")
            
            # paste data
            if data_values and data_values[0]:
                paste_index = self.index(start_row, start_col)
                self.paste_data_in_values(paste_index, data_values, row_mask, col_mask)

        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)
        self.update_index_entries({**new_row_entities, **new_col_entities})

    def edit_index(self, new_index, index_mask, direction):
        """Edits the index of either row or column"""
        if direction == "row":
            index_name = self.pivot_index
            edit_index = self._data_index
            edit_index_set = self._data_index_set
            invalid_set = self._invalid_row
            other_index = self._data_columns
            other_invalid_set = self._invalid_column
            order_getter = operator.itemgetter(*(0,1))
            key_getter = self._key_getter
            index_offset = self._num_headers_row
            other_index_offset = self._num_headers_column
        elif direction == "column":
            index_name = self.pivot_columns
            edit_index = self._data_columns
            edit_index_set = self._data_columns_set
            invalid_set = self._invalid_column
            other_index = self._data_index
            other_invalid_set = self._invalid_row
            order_getter = operator.itemgetter(*(1,0))
            order = tuple(self._index_ind[i] for i in self.pivot_columns + self.pivot_index + self.pivot_frozen)
            order = tuple(sorted(range(len(order)),key=order.__getitem__))
            key_getter = operator.itemgetter(*order)
            index_offset = self._num_headers_column
            other_index_offset = self._num_headers_row
        else:
            raise ValueError('parameter direction must be "row" or "column"')
        
        # insert new index entites
        new_indexes = {}
        for i, name in enumerate(index_name):
            for r in new_index:
                index = r[i]
                if self.is_valid_index(index, name) and index not in self.index_entries[name]:
                    self.index_entries[name].add(index)
                    if name in new_indexes:
                        new_indexes[name].add(index)
                    else:
                        new_indexes[name] = set([index])
                    #self.added_index_entries[name].add(index)
        
        # update tuple entities
        for k in self.tuple_index_entries.keys():
            if set(k).issubset(index_name + self.pivot_frozen) and not set(self.pivot_frozen).issuperset(k):
                names = [n for n in index_name + self.pivot_frozen]
                valid = [(i, names.index(kn)) for i, kn in enumerate(k) if kn in names]
                keys = tuple(v[1] for v in valid)
                names = tuple(k[v[0]] for v in valid)
                getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
                for line in new_index:
                    new_tuple = getter(tuple(line) + self.frozen_value)
                    if all(self.is_valid_index(i, n) for i, n in zip(new_tuple, names)):
                        if new_tuple not in self.tuple_index_entries[k]:
                            self.tuple_index_entries[k].add(new_tuple)
                            if k in self.added_tuple_index_entries:
                                self.added_tuple_index_entries[k].add(new_tuple)
                            else:
                                self.added_tuple_index_entries[k] = set([new_tuple])
        
        for i, new_key in zip(index_mask, new_index):
            if i < len(edit_index) and edit_index[i] == new_key:
                # same as old key, do nothing
                continue
            if self.is_valid_key(new_key, edit_index_set, index_name):
                # key is valid
                edit_index_set.add(new_key)
                if i >= len(edit_index):
                    # outside old data do nothing
                    continue
                if i + index_offset in invalid_set:
                    # previous key was invalid move data from invalid to
                    # valid if not in paste area
                    invalid_set.pop(i + index_offset, None)
                    for c, other_key in enumerate(other_index):
                        row_col_index = order_getter((i + index_offset, c + other_index_offset))
                        if c + other_index_offset not in other_invalid_set and row_col_index in self._invalid_data:
                            key = key_getter(new_key + other_key + self.frozen_value)
                            self._data[key] = self._invalid_data.pop(row_col_index)
                            self._edit_data[key] = 1
                else:
                    # previous key vas valid, move data to new key
                    old_index_key = edit_index[i]
                    edit_index_set.remove(old_index_key)
                    for c, other_key in enumerate(other_index):
                        old_key = key_getter(old_index_key + other_key + self.frozen_value)
                        if c + other_index_offset not in other_invalid_set and old_key in self._data:
                            key = key_getter(new_key + other_key + self.frozen_value)
                            self._data[key] = self._data.pop(old_key)
                            self._edit_data[key] = 1
                            self._edit_data.pop(old_key, None)
                            self._data_deleted.add(old_key)
            else:
                # key is invalid
                if i < len(edit_index):
                    old_index_key = edit_index[i]
                    if old_index_key in edit_index_set and i + index_offset not in invalid_set:
                        # previous key was valid, remove from set
                        edit_index_set.remove(old_index_key)
                    if i + index_offset not in invalid_set:
                        # move data to invalid data
                        old_index_key = edit_index[i]
                        for c, other_key in enumerate(other_index):
                            old_key = key_getter(old_index_key + other_key + self.frozen_value)
                            if c + other_index_offset not in other_invalid_set and old_key in self._data:
                                row_col_index = order_getter((i + index_offset, c + other_index_offset))
                                self._invalid_data[row_col_index] = self._data.pop(old_key)
                                self._edit_data.pop(old_key, None)
                                self._data_deleted.add(old_key)
                invalid_set[i + index_offset] = new_key

        for i, new_key in zip(index_mask, new_index):
            if i < len(edit_index):
                edit_index[i] = new_key
            else:
                edit_index.append(new_key)

        if direction == "row":
            self._data_index = edit_index
            self._data_index_set = edit_index_set
            self._invalid_row = invalid_set
        elif direction == "column":
            self._data_columns = edit_index
            self._data_columns_set = edit_index_set
            self._invalid_column = invalid_set
        return new_indexes

    def dataRowCount(self):
        """number of rows that contains actual data"""
        if self._data_index and self._data_index[0]:
            return len(self._data_index)
        else:
            return 0
        
    def dataColumnCount(self):
        """number of columns that contains actual data"""
        if self._data_columns and self._data_columns[0]:
            return len(self._data_columns)
        else:
            return 0

    def rowCount(self, parent=QModelIndex()):
        return self._num_headers_row + self.dataRowCount() + 1

    def columnCount(self, parent=QModelIndex()):
        return self._num_headers_column + self.dataColumnCount() + 1
    
    def is_valid_index(self, index, index_name):
        """checks if if given index value is a valid value for given index"""
        if not index:
            # index value cannot be empty/None
            return False
        if not isinstance(index, self.index_type[index_name]):
            # index is not correct type
            return False
        if index_name in self.valid_index_values and self.valid_index_values[index_name]:
            # check if there is any valid values for index
            if index not in self.valid_index_values[index_name]:
                # index is not in valid values
                return False
        return True
    
    def is_valid_key(self, key, existing_keys, key_names):
        """Checks if given key (combination of indexes) is valid"""
        if not all(self.is_valid_index(index, index_name) for index, index_name in zip(key, key_names)):
            return False
        if key in existing_keys:
            # key cannot be a duplicate of existing keys in index.
            return False
        return True
    
    def update_index_entries(self, new_entries = {}, deleted_entries = {}):
        if new_entries or deleted_entries:
            self.indexEntriesChanged.emit(self, deleted_entries, new_entries)

    def set_index_key(self, index, value, direction):
        """edits/sets a index value in a index in row/column"""
        self.beginResetModel()
        if not value or value.isspace():
            # empty do nothing
            return False
        if direction == "column":
            header_ind = index.row()
            index_ind = index.column() - self._num_headers_column
            index_name = self.pivot_columns[header_ind]
            if len(self._data_columns) <= index_ind:
                # edited index outside, add new column
                old_key = [None for _ in range(len(self.pivot_columns))]
            else:
                old_key = self._data_columns[index_ind]
        elif direction == "row":
            header_ind = index.column()
            index_ind = index.row() - self._num_headers_row
            index_name = self.pivot_index[header_ind]
            if len(self._data_index) <= index_ind:
                # edited index outside, add new column
                old_key = [None for _ in range(len(self.pivot_index))]
            else:
                old_key = self._data_index[index_ind]
        else:
            raise ValueError('parameter direction must be "row" or "column"')
        # check if value should be int
        if index_name in self.index_type and self.index_type[index_name] == int and value.isdigit():
                value = int(value)
        # update value
        new_key = list(old_key)
        new_key[header_ind] = value
        new_key = tuple(new_key)
        # change index values
        new_key_entries = self.edit_index([new_key], [index_ind], direction)
        self.endResetModel()
        self.dataChanged.emit(index, index)
        self.update_index_entries(new_key_entries)
        return True

    def setData(self, index, value, role = Qt.EditRole):
        if role == Qt.EditRole:
            if self.index_in_data(index):
                #edit existing data
                self.paste_data_in_values(index, [[value]])
                return True
            elif index.row() == self.rowCount() - 1 and index.column() < self._num_headers_column:
                # add new row if there are any indexes on the row
                if self.pivot_index:
                    return self.set_index_key(index, value, "row")
            elif index.column() == self.columnCount() - 1 and index.row() < self._num_headers_row:
                # add new column if there are any columns on the pivot
                if self.pivot_columns:
                    return self.set_index_key(index, value, "column")
            elif (index.row() < self._num_headers_row - min(1, self.dataRowCount())
                  and index.column() >= self._num_headers_column
                  and index.column() < self.columnCount() - 1):
                # edit column key
                return self.set_index_key(index, value, "column")
            elif self.index_in_row_headers(index):
                # edit row key
                return self.set_index_key(index, value, "row")
        return False
    
    def flags(self, index):
        if index.row() < self._num_headers_row and index.column() < self._num_headers_column:
            return super(PivotTableModel, self).flags(index)
        elif self.pivot_index and self.pivot_columns and index.row() == self._num_headers_row - 1 and index.column() >= self._num_headers_column:
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super(PivotTableModel, self).flags(index)
    
    def index_in_data(self,index):
        """check if index is in data area"""
        if (self.dataRowCount() == 0 and self.pivot_index or
            self.dataColumnCount() == 0 and self.pivot_columns):
            # no data
            return False
        return (index.row() >= self._num_headers_row
                and index.column() >= self._num_headers_column
                and index.row() < self._num_headers_row + max(1,self.dataRowCount())
                and index.column() < self._num_headers_column + max(1,self.dataColumnCount()))
    
    def index_in_column_headers(self, index):
        """check if index is in column headers (horizontal) area"""
        return (index.row() < self._num_headers_row 
                and index.column() >= self._num_headers_column
                and index.column() < self.columnCount() - 1)
    
    def index_in_row_headers(self, index):
        """check if index is in row headers (vertical) area"""
        return (self.pivot_index
                and index.row() >= self._num_headers_row
                and index.column() < self._num_headers_column
                and index.row() < self.rowCount() - 1)
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self.index_in_data(index):
                # get values
                value = None
                if index.row() in self._invalid_row or index.column() in self._invalid_column:
                    # see if invalid value exits
                    value = self._invalid_data.get((index.row(), index.column()))
                else:
                    if self._data:
                        r = self._data_index[index.row() - self._num_headers_row]
                        c = self._data_columns[index.column() - self._num_headers_column]
                        value = self._data.get(self._key_getter(r + c + self.frozen_value))
                return '' if value is None else str(value)
            elif self.index_in_column_headers(index):
                # draw column header values
                if not self.pivot_index:
                    # when special case when no pivot_index, no empty line padding
                    return self._data_columns[index.column() - self._num_headers_column][index.row()]
                elif index.row() < self._num_headers_row - 1:
                    return self._data_columns[index.column() - self._num_headers_column][index.row()]
            elif self.index_in_row_headers(index):
                # draw index values
                return self._data_index[index.row() - self._num_headers_row][index.column()]
            elif (index.row() < self._num_headers_row
                  and index.column() < self._num_headers_column):
                # draw header values
                return self._data_header[index.row()][index.column()]
            else:
                return None
        elif role == Qt.BackgroundColorRole:
            return self.data_color(index)
        else:
            return None
        
    def get_key(self, index):
        r = tuple(None for _ in self.pivot_index)
        c = tuple(None for _ in self.pivot_columns)
        if self._data_index and self._data_index[0]:
            r = self._data_index[index.row() - self._num_headers_row]
        if self._data_columns and self._data_columns[0]:
            c = self._data_columns[index.column() - self._num_headers_column]
        return self._key_getter(r + c + self.frozen_value)
    
    def data_color(self, index):
        if self.index_in_data(index):
            # color edited values
            if index.row() in self._invalid_row or index.column() in self._invalid_column:
                return QColor(Qt.lightGray)
            if self._data:
                r = self._data_index[index.row() - self._num_headers_row]
                c = self._data_columns[index.column() - self._num_headers_column]
                key = self._key_getter(r + c + self.frozen_value)
                if key in self._edit_data.keys():
                    return QColor(Qt.yellow)
        elif self.index_in_column_headers(index) and index.column() in self._invalid_column:
            # color invalid columns
            if index.row() >= len(self.pivot_columns):
                return
            index_name = self.pivot_columns[index.row()]
            key = self._data_columns[index.column() - self._num_headers_column]
            index = key[index.row()]
            if not self.is_valid_index(index, index_name) or key in self._data_columns_set:
                # invalid index or duplicate key
                return QColor(Qt.red)
        elif self.index_in_row_headers(index) and index.row() in self._invalid_row:
            # color invalid indexes
            index_name = self.pivot_index[index.column()]
            key = self._data_index[index.row() - self._num_headers_row]
            index = key[index.column()]
            if not self.is_valid_index(index, index_name) or key in self._data_index_set:
                # invalid index or duplicate key
                return QColor(Qt.red)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return None
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return None
