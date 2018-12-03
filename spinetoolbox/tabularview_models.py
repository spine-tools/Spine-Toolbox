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
    #_data_frozen_index_values = set() # valid frozen_value values for current pivot_frozen
    _index_types = () # type of the indexes in _data
    index_names = () # names of the indexes in _data, can not contain duplicates
    index_real_names = () # real names of indexes, can contain duplicates
    pivot_rows = () # current selected rows indexes
    pivot_columns = () # current selected columns indexes
    pivot_frozen = () # current filtered frozen indexes
    frozen_value = () # current selected value of index_frozen
    _key_getter = lambda *x: () # operator.itemgetter placeholder used translate pivot to keys in _data
    _row_data_header = [] # header values for row data 
    _column_data_header = [] # header valus for column data
    _row_data_header_set = set() # set of _row_data_header
    _column_data_header_set = set() # set of _column_data_header
    _invalid_row = {} # set of rows that have invalid indexes
    _invalid_column = {} # set of columns that have invalid indexes
    _invalid_data = {} # dictionary of invalid data
    _added_index_entries = {} # added index entries
    _added_tuple_index_entries = {} # added tuple index entries
    _deleted_tuple_index_entries = {} # deleted tuple index entries
    _deleted_index_entries = {} # deleted index_entries
    _used_index_values = {}
    _unique_name_2_name = {}

    # dict with index name as key and set/range of valid values for that index
    # if set/range is empty or index doesn't exist in valid_index_values
    # then all values are valid
    _valid_index_values = {}
    
    def clear_track_data(self):
        """clears data that is tracked"""
        self._edit_data = {}
        self._deleted_data = {}
        self._added_index_entries = {}
        self._added_tuple_index_entries = {}
        self._deleted_tuple_index_entries = {}
        self._deleted_index_entries = {}
    
    def set_new_data(self, data, index_names, index_type, rows=(), columns=(),
                     frozen=(), frozen_value=() , index_entries={}, valid_index_values={}, 
                     tuple_index_entries={}, used_index_values={}, index_real_names = []):
        """set the data of the model, index names and any additional indexes that don't have data, valid index values.
        """
        if not index_real_names:
            index_real_names = index_names
        elif len(index_real_names) != len(index_names):
            raise ValueError('index_real_name and index_names must have same length')
        if len(index_names) != len(index_type):
            raise ValueError('index_names and index_type must have same length')
        if data and any(len(d) < len(index_names) + 1 for d in data):
            raise ValueError('data inner lists be of len >= len(index_names) + 1')
        if not all(t in [str, int] for t in index_type):
            raise ValueError('index_type can only contain str or int type')
        if len(set(index_real_names)) != len(index_names):
            # index_real_names contains duplicates, make sure the type is the same
            un_2_n = {unique: name for unique, name in zip(index_names, index_real_names)}
            real_type = {n: set() for n in index_real_names}
            for name, name_type in zip(index_names, index_type):
                real_name = un_2_n[name]
                real_type[real_name].add(name_type)
            # should only have one type per unique name in index_real_names
            if any(len(types) != 1 for types in real_type.values()):
                raise ValueError('inconsistent types for "index_real_names" and "index_types"')

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
        
        self._unique_name_2_name = {unique: name for unique, name in zip(index_names, index_real_names)}

        self._valid_index_values = valid_index_values
        self._index_ind = {index: ind for ind, index in enumerate(index_names)}
        
        self.index_names = tuple(index_names)
        self.index_real_names = tuple(index_real_names)
        self._index_type = {self._unique_name_2_name[index_names[i]]: it for i, it in enumerate(index_type)}
        # create data dict with keys as long as index_names
        self._data = {tuple(d[:len(index_names)]):d[len(index_names)] for d in data}
        # item getter so that you can call _key_getter(row_header + column_header + frozen_value)
        # and get a key to use on _data
        key = tuple(self.index_names.index(i) for i in index_names)
        self._key_getter = tuple_itemgetter(operator.itemgetter(*key), len(key))
        
        self.index_entries = {}
        self.tuple_index_entries = {}
        self.clear_track_data()
        self.pivot_rows = tuple(rows)
        self.pivot_columns = tuple(columns)
        self.pivot_frozen = tuple(frozen)
        self.frozen_value = tuple(frozen_value)
        self._used_index_values = used_index_values
        
        # get all index values from data
        for i, c in enumerate(self.index_names):
            name = self._unique_name_2_name[c]
            if name in self.index_entries:
                self.index_entries[name].update(set(d[i] for d in self._data.keys()))
            else:
                self.index_entries[name] = set(d[i] for d in self._data.keys())
            self._added_index_entries[name] = set()
            self._deleted_index_entries[name] = set()
        for k, v in index_entries.items():
            name = self._unique_name_2_name[k]
            if name in self.index_entries:
                self.index_entries[name].update(set(v))
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
        if not len(set(index_names)) == len(index_names):
            error = "'index_names' must contain only unique strings"
        if not all(i in index_names for i in frozen):
            error = "'frozen' contains strings that doesn't match with current 'index_names'"
        if not all(i in index_names for i in rows):
            error = "'rows' contains strings that doesn't match with current 'index_names'"
        if not all(c in index_names for c in columns):
            error = "'columns' contains strings that doesn't match with current 'index_names'"
        if len(set(rows + columns + frozen)) != len(index_names):
            error = "'rows', 'columns' and 'forzen' must contain all unqiue strings in 'index_names' without duplicates"
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
            name = self._unique_name_2_name[name]
            self.index_entries[name].update(value)
        # columns
        new_column_keys, new_column_none_keys, new_entries = self._index_entries_without_data(
            self.pivot_columns, self._column_data_header_set,
            self.pivot_frozen, self.frozen_value, self.tuple_index_entries)
        for name, value in new_entries.items():
            name = self._unique_name_2_name[name]
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

        #self._change_index_frozen()
        
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
        #self.frozen_value = tuple(value)
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
            return []
        if self.pivot_rows and any(r >= len(self._row_data_header) or r < 0 for r in row_mask):
            raise ValueError("row_mask contains invalid indexes to current row pivot")
        if self.pivot_columns and any(c >= len(self._column_data_header) or c < 0 for c in col_mask):
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
        if not data:
            return
        elif len(data) == 1 and not data[0]:
            return
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
    
    def _add_index_value(self, value, name):
        name = self._unique_name_2_name[name]
        if value in self.index_entries[name]:
            # value for index already exists, no need to add.
            return True
        # check if value for index 'name' is already in use.
        for k, v in self._used_index_values.items():
            if name in k and value in v:
                # value is already in use
                return False
        #check if new value is valid for index.
        if not self.is_valid_index(value, name):
            return False
        # add to existing entries.
        self.index_entries[name].add(value)
        # add new value to used names
        for k, v in self._used_index_values.items():
            if name in k:
                v.add(value)
        # reomve from deleted values
        if name in self._deleted_index_entries and value in self._deleted_index_entries[name]:
            # value was deleted, now readded, don't add to _added_index_entries
            self._deleted_index_entries[name].discard(value)
        else:
            # add to added values
            if name not in self._added_index_entries:
                self._added_index_entries[name] = set()
            self._added_index_entries[name].add(value)
        return True

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
        if key in self._deleted_data:
            # data was deleted, add deleted data
            self._add_data(key, self._deleted_data[key])
        elif key in self._edit_data:
            # data was edited
            value = self._edit_data[key]
            if value == None:
                # no previous data, delete
                self._delete_data(key)
            else:
                # readd previous data
                self._add_data(key, value)
    
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
    
    def restore_pivoted_values(self, indexes):
        """Restores all values for given indexes"""
        if not all(i[0] <= len(self.rows) or i[0] < 0 
                   or i[1] <= len(self.columns) or i[1] < 0 for i in indexes):
            raise ValueError('indexes must be list of valid index for row pivot')
        for i in indexes:
            key = self._key_getter(self.row(i[0]) + self.column(i[1]) + self.frozen_value)
            self._restore_data(key)
    
    def delete_pivoted_values(self, indexes):
        """Deletes values for given indexes"""
        if not all(i[0] <= len(self.rows) or i[0] < 0 
                   or i[1] <= len(self.columns) or i[1] < 0 for i in indexes):
            raise ValueError('indexes must be list of valid index for row pivot')
        # delete values
        for i in indexes:
            if i[0] in self._invalid_row or i[1] in self._invalid_column:
                # delete invalid data
                self._invalid_data.pop(tuple(i), None)
            else:
                # delete data if exists
                key = self._key_getter(self.row(i[0]) + self.column(i[1]) + self.frozen_value)
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
            if k not in self.index_real_names or not indexes:
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
            # remove any entries in used values
            for u_name, v in self._used_index_values.items():
                if k in u_name:
                    v.difference_update(dv)
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
            num_new = min(len(index_names) - start_index, len(data[0]))
            data = [row[:num_new] for row in data]
        else:
            num_new = min(len(index_names) - start_index, len(data))
            data = [[data[row][col] for row in range(num_new)] for col in range(len(data[0]))]
        
        # get header indexes that are going to be updated
        edit_index = [index_values[i] for i in mask if i < len(index_values)]

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
            new_index = [before + tuple(data[row][col] for col in new_indexes) + after 
                         for row in range(len(edit_index), len(data))]
        return edit_index, new_index

    def paste_data(self, row_start=0, row_header_data=[], col_start=0,
                   col_header_data=[], data=[], row_mask=[], col_mask=[]):
        """Paste a list of list into current view of AbstractTable"""
        if row_header_data:
            edit_rows, add_rows = self._data_to_header(row_header_data,
                                                       row_start,
                                                       self._row_data_header,
                                                       self.pivot_rows,
                                                       row_mask, "row")
            self.edit_index(edit_rows + add_rows, row_mask, "row")
        if col_header_data and col_header_data[0]:
            edit_columns, add_columns = self._data_to_header(col_header_data, 
                                                             col_start, 
                                                             self._column_data_header,
                                                             self.pivot_columns,
                                                             col_mask, "column")
            self.edit_index(edit_columns + add_columns, col_mask, "column")
        # paste data
        if data:
            self.set_pivoted_data(data, row_mask, col_mask)

    def edit_index(self, new_index, index_mask, direction):
        if len(new_index) != len(index_mask):
            raise ValueError('index_mask must be same length as new_index')
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
            order = tuple(self.index_names.index(i) for i in self.pivot_columns + self.pivot_rows + self.pivot_frozen)
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
                self._add_index_value(r[i], name)
        
        # update tuple entities
        for k in self.tuple_index_entries.keys():
            if (set(k).issubset(index_name + self.pivot_frozen) 
                and not set(self.pivot_frozen).issuperset(k)):
                names = [n for n in index_name + self.pivot_frozen]
                valid = [(i, names.index(kn)) for i, kn in enumerate(k) if kn in names]
                keys = tuple(v[1] for v in valid)
                names = tuple(k[v[0]] for v in valid)
                getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
                for line in new_index:
                    new_tuple = getter(tuple(line) + self.frozen_value)
                    if all(i in self.index_entries[self._unique_name_2_name[n]] 
                           for i, n in zip(new_tuple, names)):
                        # all indexes are valid
                        if new_tuple not in self.tuple_index_entries[k]:
                            # new tuple, save
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
        real_names = [self._unique_name_2_name[name] for name in key_names]
        if not all(index in self.index_entries[index_name] for index, index_name in zip(key, real_names)):
            return False
        if key in existing_keys:
            # key cannot be a duplicate of existing keys in index.
            return False
        return True


class PivotTableModel(QAbstractTableModel):
    def __init__(self, parent = None):
        super(PivotTableModel, self).__init__(parent)
        self.model = PivotModel()
        self._data_header = [[]]
        self._num_headers_row = 0
        self._num_headers_column = 0
    
    def set_data(self, data, index_names, index_type, rows=(), columns=(), frozen=(), frozen_value=(), index_entries={} , valid_index_values={}, tuple_index_entries={}, used_index_values={}, index_real_names=[]):
        self.beginResetModel()
        self.model.set_new_data(data, index_names, index_type, rows, columns, frozen, frozen_value, index_entries, valid_index_values, tuple_index_entries, used_index_values, index_real_names)
        self._update_header_data()
        self.endResetModel()
    
    def set_pivot(self, rows, columns, frozen, frozen_value):
        self.beginResetModel()
        self.model.set_pivot(rows, columns, frozen, frozen_value)
        self._update_header_data()
        self.endResetModel()
    
    def set_frozen_value(self, frozen_value):
        self.beginResetModel()
        self.model.set_frozen_value(frozen_value)
        self._update_header_data()
        self.endResetModel()

    def delete_values(self, indexes):
        # transform to PivotModel index
        indexes = self._indexes_to_pivot_index(indexes)
        self.beginResetModel()
        self.model.delete_pivoted_values(indexes)
        self.endResetModel()
    
    def delete_index_values(self, keys_dict):
        self.beginResetModel()
        self.model.delete_index_values(keys_dict)
        self.endResetModel()
    
    def delete_tuple_index_values(self, tuple_key_dict):
        self.beginResetModel()
        self.model.delete_tuple_index_values(tuple_key_dict)
        self.endResetModel()
    
    def restore_values(self, indexes):
        indexes = self._indexes_to_pivot_index(indexes)
        self.beginResetModel()
        self.model.restore_pivoted_values(indexes)
        self.endResetModel()
    
    def get_key(self, index):
        row = self.model.row(max(0, index.row() - self._num_headers_row))
        col = self.model.column(max(0, index.column() - self._num_headers_column))
        return self.model._key_getter(row + col + self.model.frozen_value)
    
    def paste_data(self, index, data, row_mask, col_mask):
        """paste data into pivot model"""
        row_header_data = []
        col_header_data = [[]]
        skip_cols = max(0, self._num_headers_column - index.column())
        skip_rows = max(0, self._num_headers_row - index.row())
        
        if self.model.pivot_columns and index.row() < self._num_headers_row:
            # extract data for column headers
            if not self.model.pivot_rows or not index.row() == self._num_headers_row - 1:
                col_header_data = [line[skip_cols:] for line in data[:skip_rows]]
        if self.model.pivot_rows and index.column() < self._num_headers_column:
            # extract data for row headers
            row_header_data = [data[r][:skip_cols] for r in range(skip_rows, len(data))]
        
        # extract data for pasting in values
        value_data = [line[skip_cols:] for line in data[skip_rows:]]
        if not value_data:
            value_data = [[]]
        # translate mask into pivot index
        row_mask = [r - self._num_headers_row for r in row_mask if r >= self._num_headers_row]
        col_mask = [c - self._num_headers_column for c in col_mask if c >= self._num_headers_column]
        new_rows = max(len(value_data), len(row_header_data)) - len(row_mask)
        new_cols = max(len(value_data[0]), len(col_header_data[0])) - len(col_mask)
        
        # extend mask if new values are given
        if  new_rows > 0:
            row_mask.extend(list(range(len(self.model.rows), len(self.model.rows) + new_rows)))
        if new_cols > 0:
            col_mask.extend(list(range(len(self.model.columns), len(self.model.columns) + new_cols)))
        
        self.beginResetModel()
        self.model.paste_data(index.column(), row_header_data, index.row(), col_header_data, value_data, row_mask, col_mask)
        self.endResetModel()
    
    def _indexes_to_pivot_index(self, indexes):
        max_row = len(self.model.rows)
        max_col = len(self.model.columns)
        if len(self.model.pivot_rows) == 0:
            max_row = 1
        if len(self.model.pivot_columns) == 0:
            max_col = 1
        indexes = [(i.row() - self._num_headers_row, i.column() - self._num_headers_column) 
                   for i in indexes 
                   if (i.row() >= self._num_headers_row and i.row() - self._num_headers_row < max_row)
                   and (i.column() >= self._num_headers_column and i.column() - self._num_headers_column < max_col)]
        return indexes
    
    def _update_header_data(self):
        """updates the top left corner 'header' data"""
        self._num_headers_row = len(self.model.pivot_columns) + min(1,len(self.model.pivot_rows))
        self._num_headers_column = max(len(self.model.pivot_rows),1)
        if self.model.pivot_columns:
            headers = [[None for _ in range(self._num_headers_column-1)] + [c] for c in self.model.pivot_columns]
            if self.model.pivot_rows:
                headers.append(self.model.pivot_rows)
        else:
            headers = [self.model.pivot_rows]
        self._data_header = headers
    
    def dataRowCount(self):
        """number of rows that contains actual data"""
        return len(self.model.rows)
        
    def dataColumnCount(self):
        """number of columns that contains actual data"""
        return len(self.model.columns)

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in table, number of header rows + datarows + 1 empty row"""
        return self._num_headers_row + self.dataRowCount() + 1

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in table, number of header columns + datacolumns + 1 empty columns"""
        return self._num_headers_column + self.dataColumnCount() + 1
    
    def flags(self, index):
        """Roles for data"""
        if index.row() < self._num_headers_row and index.column() < self._num_headers_column:
            return super(PivotTableModel, self).flags(index)
        elif self.model.pivot_rows and self.model.pivot_columns and index.row() == self._num_headers_row - 1 and index.column() >= self._num_headers_column:
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super(PivotTableModel, self).flags(index)
    
    def index_in_top_left(self, index):
        """check if index is in top left corner, where pivot names are displayed"""
        return index.row() < self._num_headers_row and index.column() < self._num_headers_column
    
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
        return (self.model.pivot_rows
                and index.row() >= self._num_headers_row
                and index.column() < self._num_headers_column
                and index.row() < self.rowCount() - 1)
    
    def set_index_key(self, index, value, direction):
        """edits/sets a index value in a index in row/column"""
        # TODO: change this to insertRow/Column instead when creating new rows
        self.beginResetModel()
        if not value or value.isspace():
            # empty do nothing
            return False
        if direction == "column":
            header_ind = index.row()
            index_ind = index.column() - self._num_headers_column
            index_name = self.model.pivot_columns[header_ind]
            if len(self.model.columns) <= index_ind:
                # edited index outside, add new column
                old_key = [None for _ in range(len(self.model.pivot_columns))]
            else:
                old_key = self.model.column(index_ind)
        elif direction == "row":
            header_ind = index.column()
            index_ind = index.row() - self._num_headers_row
            index_name = self.model.pivot_rows[header_ind]
            if len(self.model.rows) <= index_ind:
                # edited index outside, add new column
                old_key = [None for _ in range(len(self.model.pivot_rows))]
            else:
                old_key = self.model.row(index_ind)
        else:
            raise ValueError('parameter direction must be "row" or "column"')
        # check if value should be int
        if (index_name in self.model._index_type 
            and self.model._index_type[index_name] == int 
            and value.isdigit()):
                value = int(value)
        # update value
        new_key = list(old_key)
        new_key[header_ind] = value
        new_key = tuple(new_key)
        # change index values
        self.model.edit_index([new_key], [index_ind], direction)
        self.endResetModel()
        self.dataChanged.emit(index, index)
        #self.update_index_entries(new_key_entries)
        return True
    
    def setData(self, index, value, role = Qt.EditRole):
        if role == Qt.EditRole:
            if self.index_in_data(index):
                #edit existing data
                self.model.set_pivoted_data([[value]],
                                            [index.row() - self._num_headers_row],
                                            [index.column() - self._num_headers_column])
                return True
            elif index.row() == self.rowCount() - 1 and index.column() < self._num_headers_column:
                # add new row if there are any indexes on the row
                if self.model.pivot_rows:
                    return self.set_index_key(index, value, "row")
            elif index.column() == self.columnCount() - 1 and index.row() < self._num_headers_row:
                # add new column if there are any columns on the pivot
                if self.model.pivot_columns:
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
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self.index_in_data(index):
                # get values
                data = self.model.get_pivoted_data([index.row() - self._num_headers_row],[index.column() - self._num_headers_column])
                if not data:
                    return ''
                else:
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
        elif role == Qt.ToolTipRole:
            # display tooltip for edited data
            if self.index_in_data(index):
                key = self.get_key(index)
                if key in self.model._edit_data:
                    value = self.model._edit_data[key]
                    if value:
                        return 'Original data: {}'.format(value)
                    else:
                        return 'New data'
                elif key in self.model._deleted_data:
                    return 'Deleted data: {}'.format(self.model._deleted_data[key])
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
            r = index.row() - self._num_headers_row
            c = index.column() - self._num_headers_column
            if r in self.model._invalid_row or c in self.model._invalid_column:
                # invalid data, color grey
                return QColor(Qt.lightGray)
            row = self.model.row(index.row() - self._num_headers_row)
            col = self.model.column(index.column() - self._num_headers_column)
            key = self.model._key_getter(row + col + self.model.frozen_value)
            if key in self.model._deleted_data:
                # deleted data, color red
                return QColor(Qt.red)
            if key in self.model._edit_data:
                if self.model._edit_data[key] == None:
                    # new data color green
                    return QColor(Qt.green)
                else:
                    # edited data color yellow
                    return QColor(Qt.yellow)
                    
        elif self.index_in_column_headers(index):
            # color new indexes or invalid indexes "columns"
            if index.row() >= len(self.model.pivot_columns):
                return
            index_name = self.model._unique_name_2_name[self.model.pivot_columns[index.row()]]
            key = self.model.column(index.column() - self._num_headers_column)
            index_entry = key[index.row()]
            if (index.column() - self._num_headers_column in self.model._invalid_column
                and (not index_entry in self.model.index_entries[index_name]
                     or key in self.model._column_data_header_set)):
                # color invalid columns
                return QColor(Qt.red)
            elif index_entry in self.model._added_index_entries[index_name]:
                # color added indexes
                return QColor(Qt.green)
        elif self.index_in_row_headers(index):
            # color new indexes or invalid indexes "rows"
            index_name = self.model._unique_name_2_name[self.model.pivot_rows[index.column()]]
            key = self.model.row(index.row() - self._num_headers_row)
            index_entry = key[index.column()]
            if (index.row() - self._num_headers_row in self.model._invalid_row
                and (not index_entry in self.model.index_entries[index_name]
                     or key in self.model._row_data_header_set)):
                # invalid index or duplicate key
                return QColor(Qt.red)
            elif index_entry in self.model._added_index_entries[index_name]:
                # color added indexes
                return QColor(Qt.green)
            


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
    
    def delete_values(self, delete_indexes):
        delete_indexes = [self.mapToSource(index) for index in delete_indexes]
        self.sourceModel().delete_values(delete_indexes)
    
    def restore_values(self, indexes):
        indexes = [self.mapToSource(index) for index in indexes]
        self.sourceModel().restore_values(indexes)
        
    def paste_data(self, index, data):
        model_index = self.mapToSource(index)
        row_mask = []
        # get indexes of filtered rows
        # TODO: this might be cached somewhere?
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
        elif source_row in self.sourceModel().model._invalid_row:
            return True
        else:
            if self.sourceModel().model.pivot_rows:
                index = self.sourceModel().model._row_data_header[source_row - self.sourceModel()._num_headers_row]
                return self.accept_index(index, self.sourceModel().model.pivot_rows)
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
        elif source_column in self.sourceModel().model._invalid_column:
            return True
        else:
            if self.sourceModel().model.pivot_columns:
                index = self.sourceModel().model._column_data_header[source_column - self.sourceModel()._num_headers_column]
                return self.accept_index(index, self.sourceModel().model.pivot_columns)
            else:
                return True

