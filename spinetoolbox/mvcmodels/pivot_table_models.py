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
from PySide2.QtGui import QColor, QFont
from .pivot_model import PivotModel
from ..config import PIVOT_TABLE_HEADER_COLOR


class PivotTableModel(QAbstractTableModel):

    _V_HEADER_WIDTH = 5

    def __init__(self, parent):
        """
        Args:
            parent (TabularViewForm)
        """
        super().__init__()
        self._parent = parent
        self.db_mngr = parent.db_mngr
        self.db_map = parent.db_map
        self.model = PivotModel()
        self._plot_x_column = None

    def reset_model(self, data, index_ids, rows=(), columns=(), frozen=(), frozen_value=()):
        self.beginResetModel()
        self.model.reset_model(data, index_ids, rows, columns, frozen, frozen_value)
        self._plot_x_column = None
        self.endResetModel()

    def set_pivot(self, rows, columns, frozen, frozen_value):
        self.beginResetModel()
        self.model.set_pivot(rows, columns, frozen, frozen_value)
        self.endResetModel()

    def set_frozen_value(self, frozen_value):
        self.beginResetModel()
        self.model.set_frozen_value(frozen_value)
        self.endResetModel()

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

    def get_key(self, index):
        row = self.model.row(max(0, index.row() - self._num_headers_row))
        col = self.model.column(max(0, index.column() - self._num_headers_column))
        return self.model._key_getter(row + col + self.model.frozen_value)

    def get_col_key(self, column):
        return self.model.column(max(0, column - self._num_headers_column))

    def first_data_row(self):
        """Returns the row index to the first data row."""
        # Last row is an empty row, exclude it.
        return self.rowCount() - self.dataRowCount() - 1

    def dataRowCount(self):
        """number of rows that contains actual data"""
        return max(1, len(self.model.rows))

    def dataColumnCount(self):
        """number of columns that contains actual data"""
        return max(1, len(self.model.columns))

    def headerRowCount(self):
        """Returns number of rows occupied by header."""
        return len(self.model.pivot_columns) + bool(self.model.pivot_rows)

    def headerColumnCount(self):
        """Returns number of columns occupied by header."""
        if not self.model.pivot_rows:
            if self.model.pivot_columns:
                return 1
            return 0
        return len(self.model.pivot_rows)

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in table, number of header rows + datarows + 1 empty row"""
        return self.headerRowCount() + self.dataRowCount() + 1

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in table, number of header columns + datacolumns + 1 empty columns"""
        return self.headerColumnCount() + self.dataColumnCount() + 1

    def flags(self, index):
        """Roles for data"""
        if self.index_in_top_left(index):
            return ~Qt.ItemIsEnabled
        if self.model.pivot_rows and index.row() == len(self.model.pivot_columns):
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

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

    def index_in_top(self, index):
        return index.row() == len(self.model.pivot_columns) and index.column() < len(self.model.pivot_rows)

    def index_in_left(self, index):
        last_top_column = max(0, len(self.model.pivot_rows) - 1)
        return index.column() == last_top_column and index.row() < len(self.model.pivot_columns)

    def index_in_top_left(self, index):
        """Returns whether or not the given index is in top left corner, where pivot names are displayed"""
        return self.index_in_top(index) or self.index_in_left(index)

    def index_in_column_headers(self, index):
        """Returns whether or not the given index is in column headers (horizontal) area"""
        return (
            index.row() < len(self.model.pivot_columns)
            and len(self.model.pivot_rows) <= index.column() < self.columnCount() - 1
        )

    def index_in_row_headers(self, index):
        """Returns whether or not the given index is in row headers (vertical) area"""
        return (
            index.column() < len(self.model.pivot_rows)
            and len(self.model.pivot_columns) < index.row() < self.rowCount() - 1
        )

    def index_in_empty_column_headers(self, index):
        """Returns whether or not the given index is in empty column headers (vertical) area"""
        return index.row() < len(self.model.pivot_columns) and index.column() == self.columnCount() - 1

    def index_in_empty_row_headers(self, index):
        """Returns whether or not the given index is in empty row headers (vertical) area"""
        return index.column() < len(self.model.pivot_rows) and index.row() == self.rowCount() - 1

    def index_in_data(self, index):
        """Returns whether or not the given index is in data area"""
        return (
            self.headerRowCount() <= index.row() < self.rowCount() - 1
            and self.headerColumnCount() <= index.column() < self.columnCount() - 1
        )

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self._plot_x_column:
                return "(X)"
            return None
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return self._V_HEADER_WIDTH * " "
        return None

    def _header_data(self, header_key, header_id):
        if header_key == -1:
            return self.db_mngr.get_item(self.db_map, "parameter definition", header_id)["parameter_name"]
        return self.db_mngr.get_item(self.db_map, "object", header_id)["name"]

    def map_to_pivot(self, index):
        return index.row() - self.headerRowCount(), index.column() - self.headerColumnCount()

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            if self.index_in_top(index):
                return self.model.pivot_rows[index.column()]
            if self.index_in_left(index):
                return self.model.pivot_columns[index.row()]
            if self.index_in_row_headers(index):
                row, _ = self.map_to_pivot(index)
                header_id = self.model._row_data_header[row][index.column()]
                header_key = self.model.pivot_rows[index.column()]
                return self._header_data(header_key, header_id)
            if self.index_in_column_headers(index):
                _, column = self.map_to_pivot(index)
                header_id = self.model._column_data_header[column][index.row()]
                header_key = self.model.pivot_columns[index.row()]
                return self._header_data(header_key, header_id)
            if self.index_in_data(index):
                row, column = self.map_to_pivot(index)
                data = self.model.get_pivoted_data([row], [column])
                if not data or data[0][0] is None:
                    return ''
                if not self._parent.is_value_input_type():
                    return data[0][0]
                return self.db_mngr.get_value(self.db_map, "parameter value", data[0][0], "value", role)
            return None
        if role == Qt.FontRole and self.index_in_top_left(index):
            font = QFont()
            font.setBold(True)
            return font
        if role == Qt.BackgroundColorRole:
            return self.data_color(index)
        if (
            role == Qt.TextAlignmentRole
            and self.index_in_data(index)
            and not self._parent.is_value_input_type()
            # or self.index_in_column_headers(index)
        ):
            return Qt.AlignHCenter
        return None

    def _set_header_data(self, header, header_id, value):
        item = dict(id=header_id, name=value)
        if header == 0:
            self.db_mngr.update_parameter_definitions({self.db_map: [item]})
        else:
            self.db_mngr.update_objects({self.db_map: [item]})

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        if self.index_in_data(index):
            # edit existing data
            row, column = self.map_to_pivot(index)
            data = self.model.get_pivoted_data([row], [column])
            if not data or data[0][0] is None:
                # Add
                index_tuple = self.get_key(index)
                self._parent.add_parameter_value(index_tuple, value)
            else:
                self._parent.update_parameter_value(data[0][0], value)
            self.dataChanged.emit(index, index)
            return True
        if self.index_in_row_headers(index):
            header_id = self.model._row_data_header[index.row() - len(self.model.pivot_columns) - 1][index.column()]
            header = self.model.pivot_rows[index.column()]
            self._set_header_data(header, header_id, value)
            return True
        if self.index_in_column_headers(index):
            header_id = self.model._column_data_header[index.column() - len(self.model.pivot_rows) - 1][index.row()]
            header = self.model.pivot_columns[index.row()]
            self._set_header_data(header, header_id, value)
            return True
        if self.index_in_empty_row_headers(index):
            header = self.model.pivot_rows[index.column()]
            return True
        if self.index_in_empty_column_headers(index):
            return True
        return False
        if (
            index.row() < self._num_headers_row - min(1, self.dataRowCount())
            and index.column() >= self._num_headers_column
            and index.column() < self.columnCount() - 1
        ):  # TODO: try to use `if self.index_in_column_headers(index):`
            # edit column key
            return self.set_index_key(index, value, "column")
        if self.index_in_row_headers(index):
            # edit row key
            return self.set_index_key(index, value, "row")
        if index.row() == self.rowCount() - 1 and index.column() < self._num_headers_column:
            # add new row if there are any indexes on the row
            if self.model.pivot_rows:
                return self.set_index_key(index, value, "row")
        elif index.column() == self.columnCount() - 1 and index.row() < self._num_headers_row:
            # add new column if there are any columns on the pivot
            if self.model.pivot_columns:
                return self.set_index_key(index, value, "column")

    def data_color(self, index):
        return None
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
            return QColor(PIVOT_TABLE_HEADER_COLOR)


class PivotTableSortFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.index_filters = {}

    def set_filter(self, identifier, filter_value):
        """Sets filter for a given index (object class) name.

        Args:
            identifier (int): index identifier
            filter_value (set, None): A set of accepted values, or None if no filter (all pass)
        """
        self.index_filters[identifier] = filter_value
        self.invalidateFilter()  # trigger filter update

    def clear_filter(self):
        self.index_filters = {}
        self.invalidateFilter()  # trigger filter update

    def accept_index(self, index, index_ids):
        for i, identifier in zip(index, index_ids):
            valid = self.index_filters.get(identifier)
            if valid is not None and i not in valid:
                return False
        return True

    def delete_values(self, delete_indexes):
        delete_indexes = [self.mapToSource(index) for index in delete_indexes]
        self.sourceModel().delete_values(delete_indexes)

    def restore_values(self, indexes):
        indexes = [self.mapToSource(index) for index in indexes]
        self.sourceModel().restore_values(indexes)

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """

        if source_row < self.sourceModel().headerRowCount() or source_row == self.sourceModel().rowCount() - 1:
            return True
        if source_row in self.sourceModel().model._invalid_row:
            return True
        if self.sourceModel().model.pivot_rows:
            index = self.sourceModel().model._row_data_header[source_row - self.sourceModel().headerRowCount()]
            return self.accept_index(index, self.sourceModel().model.pivot_rows)
        return True

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if (
            source_column < self.sourceModel().headerColumnCount()
            or source_column == self.sourceModel().columnCount() - 1
        ):
            return True
        if source_column in self.sourceModel().model._invalid_column:
            return True
        if self.sourceModel().model.pivot_columns:
            index = self.sourceModel().model._column_data_header[source_column - self.sourceModel().headerColumnCount()]
            return self.accept_index(index, self.sourceModel().model.pivot_columns)
        return True
