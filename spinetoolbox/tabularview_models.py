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

    def  edit_index(self, new_index, index_mask, direction):
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