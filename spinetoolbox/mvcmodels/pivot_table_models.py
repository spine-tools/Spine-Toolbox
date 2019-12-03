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
Provides pivot table models for the Tabular View.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from PySide2.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, QSortFilterProxyModel
from PySide2.QtGui import QColor, QFont, QPalette
from .parameter_value_formatting import format_for_DisplayRole, format_for_EditRole, format_for_ToolTipRole
from .pivot_model import PivotModel


class PivotTableModel(QAbstractTableModel):
    index_entries_changed = Signal(dict, dict)

    def __init__(self, parent=None):
        super(PivotTableModel, self).__init__(parent)
        self.model = PivotModel()
        self._data_header = [[]]
        self._num_headers_row = 0
        self._num_headers_column = 0
        self._plot_x_column = None

    def set_data(
        self,
        data,
        index_names,
        index_type,
        rows=(),
        columns=(),
        frozen=(),
        frozen_value=(),
        index_entries=None,
        valid_index_values=None,
        tuple_index_entries=None,
        used_index_values=None,
        index_real_names=None,
    ):
        if index_entries is None:
            index_entries = dict()
        if valid_index_values is None:
            valid_index_values = dict()
        if tuple_index_entries is None:
            tuple_index_entries = dict()
        if used_index_values is None:
            used_index_values = dict()
        if index_real_names is None:
            index_real_names = list()
        self.beginResetModel()
        self.model.set_new_data(
            data,
            index_names,
            index_type,
            rows,
            columns,
            frozen,
            frozen_value,
            index_entries,
            valid_index_values,
            tuple_index_entries,
            used_index_values,
            index_real_names,
        )
        self._plot_x_column = None
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
        add_index = {k: len(v) for k, v in self.model._added_index_entries.items()}
        del_index = {k: len(v) for k, v in self.model._deleted_index_entries.items()}

        self.beginResetModel()
        self.model.delete_index_values(keys_dict)
        self.endResetModel()

        new_indexes = {}
        deleted_indexes = {}
        for k, v in self.model._added_index_entries.items():
            if k in add_index and not len(v) == add_index[k]:
                new_indexes[k] = set(v)
        for k, v in self.model._deleted_index_entries.items():
            if k in add_index and not len(v) == del_index[k]:
                deleted_indexes[k] = set(v)
        if new_indexes or deleted_indexes:
            self.index_entries_changed.emit(new_indexes, deleted_indexes)

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

    def get_col_key(self, column):
        return self.model.column(max(0, column - self._num_headers_column))

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
        if new_rows > 0:
            row_mask.extend(list(range(len(self.model.rows), len(self.model.rows) + new_rows)))
        if new_cols > 0:
            col_mask.extend(list(range(len(self.model.columns), len(self.model.columns) + new_cols)))

        add_index = {k: len(v) for k, v in self.model._added_index_entries.items()}
        del_index = {k: len(v) for k, v in self.model._deleted_index_entries.items()}
        self.beginResetModel()
        self.model.paste_data(
            index.column(), row_header_data, index.row(), col_header_data, value_data, row_mask, col_mask
        )
        self.endResetModel()
        new_indexes = {}
        deleted_indexes = {}
        for k, v in self.model._added_index_entries.items():
            if k in add_index and not len(v) == add_index[k]:
                new_indexes[k] = set(v)
        for k, v in self.model._deleted_index_entries.items():
            if k in add_index and not len(v) == del_index[k]:
                deleted_indexes[k] = set(v)
        if new_indexes or deleted_indexes:
            self.index_entries_changed.emit(new_indexes, deleted_indexes)

    def _indexes_to_pivot_index(self, indexes):
        max_row = len(self.model.rows)
        max_col = len(self.model.columns)
        if not self.model.pivot_rows:
            max_row = 1
        if not self.model.pivot_columns:
            max_col = 1
        indexes = [
            (i.row() - self._num_headers_row, i.column() - self._num_headers_column)
            for i in indexes
            if (i.row() >= self._num_headers_row and i.row() - self._num_headers_row < max_row)
            and (i.column() >= self._num_headers_column and i.column() - self._num_headers_column < max_col)
        ]
        return indexes

    def _update_header_data(self):
        """updates the top left corner 'header' data"""
        self._num_headers_row = len(self.model.pivot_columns) + min(1, len(self.model.pivot_rows))
        self._num_headers_column = max(len(self.model.pivot_rows), 1)
        if self.model.pivot_columns:
            headers = [[None for _ in range(self._num_headers_column - 1)] + [c] for c in self.model.pivot_columns]
            if self.model.pivot_rows:
                headers.append(self.model.pivot_rows)
        else:
            headers = [self.model.pivot_rows]
        self._data_header = headers

    def first_data_row(self):
        """Returns the row index to the first data row."""
        # Last row is an empty row, exclude it.
        return self.rowCount() - self.dataRowCount() - 1

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
        if self.index_in_top_left(index):
            return ~Qt.ItemIsEnabled
        if (
            self.model.pivot_rows
            and self.model.pivot_columns
            and index.row() == self._num_headers_row - 1
            and index.column() >= self._num_headers_column
        ):
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def index_in_top_left(self, index):
        """check if index is in top left corner, where pivot names are displayed"""
        return index.row() < self._num_headers_row and index.column() < self._num_headers_column

    def top_left_indexes(self):
        """Returns indexes in the top left area.

        Returns
            list(QModelIndex): top indexes (horizontal headers, associated to rows)
            list(QModelIndex): left indexes (vertical headers, associated to columns)
        """
        pivot_column_count = len(self.model.pivot_columns)
        pivot_row_count = len(self.model.pivot_rows)
        top_indexes = []
        left_indexes = []
        for column in range(pivot_row_count):
            index = self.index(pivot_column_count, column)
            top_indexes.append(index)
        column = max(pivot_row_count - 1, 0)
        for row in range(pivot_column_count):
            index = self.index(row, column)
            left_indexes.append(index)
        return top_indexes, left_indexes

    def index_in_data(self, index):
        """check if index is in data area"""
        if (
            self.dataRowCount() == 0
            and self.model.pivot_rows
            or self.dataColumnCount() == 0
            and self.model.pivot_columns
        ):
            # no data
            return False
        return (
            index.row() >= self._num_headers_row
            and index.column() >= self._num_headers_column
            and index.row() < self._num_headers_row + max(1, self.dataRowCount())
            and index.column() < self._num_headers_column + max(1, self.dataColumnCount())
        )

    def index_in_column_headers(self, index):
        """check if index is in column headers (horizontal) area"""
        return (
            index.row() < self._num_headers_row
            and index.column() >= self._num_headers_column
            and index.column() < self.columnCount() - 1
        )

    def index_in_row_headers(self, index):
        """check if index is in row headers (vertical) area"""
        return (
            self.model.pivot_rows
            and index.column() < self._num_headers_column
            and index.row() >= self._num_headers_row
            and index.row() < self.rowCount() - 1
        )

    def set_plot_x_column(self, column, is_x):
        """Sets or clears the Y flag on a column"""
        if is_x:
            self._plot_x_column = column
        elif column == self._plot_x_column:
            self._plot_x_column = None
        self.headerDataChanged.emit(Qt.Horizontal, column, column)

    @property
    def plot_x_column(self):
        """Returns the index of the column designated as Y values for plotting or None."""
        return self._plot_x_column

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
        if index_name in self.model._index_type and self.model._index_type[index_name] == int and value.isdigit():
            value = int(value)
        # update value
        new_key = list(old_key)
        new_key[header_ind] = value
        new_key = tuple(new_key)
        # change index values
        add_index = {k: len(v) for k, v in self.model._added_index_entries.items()}
        del_index = {k: len(v) for k, v in self.model._deleted_index_entries.items()}
        self.model.edit_index([new_key], [index_ind], direction)
        self.endResetModel()
        self.dataChanged.emit(index, index)
        # self.update_index_entries(new_key_entries)
        # check if any index has been updated
        new_indexes = {}
        deleted_indexes = {}
        for k, v in self.model._added_index_entries.items():
            if k in add_index and not len(v) == add_index[k]:
                new_indexes[k] = set(v)
        for k, v in self.model._deleted_index_entries.items():
            if k in add_index and not len(v) == del_index[k]:
                deleted_indexes[k] = set(v)
        if new_indexes or deleted_indexes:
            self.index_entries_changed.emit(new_indexes, deleted_indexes)

        return True

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if self.index_in_data(index):
                # edit existing data
                self.model.set_pivoted_data(
                    [[value]], [index.row() - self._num_headers_row], [index.column() - self._num_headers_column]
                )
                return True
            if index.row() == self.rowCount() - 1 and index.column() < self._num_headers_column:
                # add new row if there are any indexes on the row
                if self.model.pivot_rows:
                    return self.set_index_key(index, value, "row")
            elif index.column() == self.columnCount() - 1 and index.row() < self._num_headers_row:
                # add new column if there are any columns on the pivot
                if self.model.pivot_columns:
                    return self.set_index_key(index, value, "column")
            elif (
                index.row() < self._num_headers_row - min(1, self.dataRowCount())
                and index.column() >= self._num_headers_column
                and index.column() < self.columnCount() - 1
            ):
                # edit column key
                return self.set_index_key(index, value, "column")
            elif self.index_in_row_headers(index):
                # edit row key
                return self.set_index_key(index, value, "row")
        return False

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if self.index_in_data(index):
                # get values
                data = self.model.get_pivoted_data(
                    [index.row() - self._num_headers_row], [index.column() - self._num_headers_column]
                )
                if not data or data[0][0] is None:
                    return ''
                data = data[0][0]
                if role == Qt.EditRole:
                    return format_for_EditRole(data)
                return format_for_DisplayRole(data)
            if self.index_in_column_headers(index):
                # draw column header values
                if not self.model.pivot_rows:
                    # when special case when no pivot_index, no empty line padding
                    return self.model._column_data_header[index.column() - self._num_headers_column][index.row()]
                if index.row() < self._num_headers_row - 1:
                    return self.model._column_data_header[index.column() - self._num_headers_column][index.row()]
            elif self.index_in_row_headers(index):
                # draw index values
                return self.model._row_data_header[index.row() - self._num_headers_row][index.column()]
            elif index.row() < self._num_headers_row and index.column() < self._num_headers_column:
                # draw header values
                return self._data_header[index.row()][index.column()]
            else:
                return None
        elif role == Qt.FontRole:
            if self.index_in_top_left(index):
                font = QFont()
                font.setBold(True)
                return font
        elif role == Qt.BackgroundColorRole:
            return self.data_color(index)
        elif role == Qt.ToolTipRole:
            if self.index_in_data(index):
                data = self.model.get_pivoted_data(
                    [index.row() - self._num_headers_row], [index.column() - self._num_headers_column]
                )
                if not data or data[0][0] is None:
                    return None
                data = data[0][0]
                return format_for_ToolTipRole(data)
        else:
            return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self._plot_x_column:
                return "(X)"
            return None
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return 8 * " "
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
                if self.model._edit_data[key] is None:
                    # new data color green
                    return QColor(Qt.green)
                # edited data color yellow
                return QColor(Qt.yellow)

        elif self.index_in_column_headers(index):
            # color new indexes or invalid indexes "columns"
            if index.row() >= len(self.model.pivot_columns):
                return
            index_name = self.model._unique_name_2_name[self.model.pivot_columns[index.row()]]
            key = self.model.column(index.column() - self._num_headers_column)
            index_entry = key[index.row()]
            if index.column() - self._num_headers_column in self.model._invalid_column and (
                not index_entry in self.model.index_entries[index_name] or key in self.model._column_data_header_set
            ):
                # color invalid columns
                return QColor(Qt.red)
            if index_entry in self.model._added_index_entries[index_name]:
                # color added indexes
                return QColor(Qt.green)
        elif self.index_in_row_headers(index):
            # color new indexes or invalid indexes "rows"
            index_name = self.model._unique_name_2_name[self.model.pivot_rows[index.column()]]
            key = self.model.row(index.row() - self._num_headers_row)
            index_entry = key[index.column()]
            if index.row() - self._num_headers_row in self.model._invalid_row and (
                not index_entry in self.model.index_entries[index_name] or key in self.model._row_data_header_set
            ):
                # invalid index or duplicate key
                return QColor(Qt.red)
            if index_entry in self.model._added_index_entries[index_name]:
                # color added indexes
                return QColor(Qt.green)
        elif self.index_in_top_left(index):
            return qApp.palette().color(QPalette.Button)


class PivotTableSortFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.index_filters = {}

    def set_filter(self, index_name, filter_value):
        self.index_filters[index_name] = filter_value
        self.invalidateFilter()  # trigger filter update

    def clear_filter(self):
        self.index_filters = {}
        self.invalidateFilter()  # trigger filter update

    def accept_index(self, index, index_names):
        for i, n in zip(index, index_names):
            if n in self.index_filters and i not in self.index_filters[n]:
                return False
        return True

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
        for c in range(
            model_index.column(), self.sourceModel().dataColumnCount() + self.sourceModel()._num_headers_column
        ):
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
        if source_row in self.sourceModel().model._invalid_row:
            return True
        if self.sourceModel().model.pivot_rows:
            index = self.sourceModel().model._row_data_header[source_row - self.sourceModel()._num_headers_row]
            return self.accept_index(index, self.sourceModel().model.pivot_rows)
        return True

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if (
            source_column < self.sourceModel()._num_headers_column
            or source_column == self.sourceModel().columnCount() - 1
        ):
            # always display headers
            return True
        if source_column in self.sourceModel().model._invalid_column:
            return True
        if self.sourceModel().model.pivot_columns:
            index = self.sourceModel().model._column_data_header[source_column - self.sourceModel()._num_headers_column]
            return self.accept_index(index, self.sourceModel().model.pivot_columns)
        return True
