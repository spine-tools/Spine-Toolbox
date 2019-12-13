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

from PySide2.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
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

    def first_data_row(self):
        """Returns the row index to the first data row."""
        # Last row is an empty row, exclude it.
        return self.headerRowCount()

    def headerRowCount(self):
        """Returns number of rows occupied by header."""
        return len(self.model.pivot_columns) + bool(self.model.pivot_rows)

    def headerColumnCount(self):
        """Returns number of columns occupied by header."""
        return max(1, len(self.model.pivot_rows))

    def dataRowCount(self):
        """Returns number of rows that contain actual data."""
        if not self.model.pivot_rows:
            return 1
        return len(self.model.rows)

    def dataColumnCount(self):
        """Returns number of columns that contain actual data."""
        if not self.model.pivot_columns:
            return 1
        return len(self.model.columns)

    def emptyRowCount(self):
        return 1 if self.model.pivot_rows else 0

    def emptyColumnCount(self):
        return 1 if self.model.pivot_columns else 0

    def rowCount(self, parent=QModelIndex()):
        """Number of rows in table, number of header rows + datarows + 1 empty row"""
        return self.headerRowCount() + self.dataRowCount() + self.emptyRowCount()

    def columnCount(self, parent=QModelIndex()):
        """Number of columns in table, number of header columns + datacolumns + 1 empty columns"""
        return self.headerColumnCount() + self.dataColumnCount() + self.emptyColumnCount()

    def flags(self, index):
        """Roles for data"""
        if index.row() < self.headerRowCount() and index.column() < self.headerColumnCount():
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
        return index.column() == self.headerColumnCount() - 1 and index.row() < len(self.model.pivot_columns)

    def index_in_top_left(self, index):
        """Returns whether or not the given index is in top left corner, where pivot names are displayed"""
        return self.index_in_top(index) or self.index_in_left(index)

    def index_in_column_headers(self, index):
        """Returns whether or not the given index is in column headers (horizontal) area"""
        return (
            index.row() < len(self.model.pivot_columns)
            and self.headerColumnCount() <= index.column() < self.headerColumnCount() + self.dataColumnCount()
        )

    def index_in_row_headers(self, index):
        """Returns whether or not the given index is in row headers (vertical) area"""
        return (
            index.column() < len(self.model.pivot_rows)
            and self.headerRowCount() <= index.row() < self.headerRowCount() + self.dataRowCount()
        )

    def index_in_headers(self, index):
        return self.index_in_column_headers(index) or self.index_in_row_headers(index)

    def index_in_empty_column_headers(self, index):
        """Returns whether or not the given index is in empty column headers (vertical) area"""
        return index.row() < len(self.model.pivot_columns) and index.column() == self.columnCount() - 1

    def index_in_empty_row_headers(self, index):
        """Returns whether or not the given index is in empty row headers (vertical) area"""
        return index.column() < len(self.model.pivot_rows) and index.row() == self.rowCount() - 1

    def index_in_data(self, index):
        """Returns whether or not the given index is in data area"""
        return (
            self.headerRowCount() <= index.row() < self.rowCount() - self.emptyRowCount()
            and self.headerColumnCount() <= index.column() < self.columnCount() - self.emptyColumnCount()
        )

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == self._plot_x_column:
                return "(X)"
            return None
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return self._V_HEADER_WIDTH * " "
        return None

    def map_to_pivot(self, index):
        """Returns a tuple of row and column in the pivot model that corresponds to the given model index.

        Args:
            index (QModelIndex)

        Returns:
            int: row
            int: column
        """
        return index.row() - self.headerRowCount(), index.column() - self.headerColumnCount()

    def _top_left_id(self, index):
        """Returns the id of the top left header corresponding to the given header index.

        Args:
            index (QModelIndex)
        Returns:
            int, NoneType
        """
        if self.index_in_row_headers(index):
            return self.model.pivot_rows[index.column()]
        if self.index_in_column_headers(index):
            return self.model.pivot_columns[index.row()]
        return None

    def _header_id(self, index):
        """Returns the id of the given row or column header index.

        Args:
            index (QModelIndex)
        Returns:
            int, NoneType
        """
        if self.index_in_row_headers(index):
            row, _ = self.map_to_pivot(index)
            return self.model._row_data_header[row][index.column()]
        if self.index_in_column_headers(index):
            _, column = self.map_to_pivot(index)
            return self.model._column_data_header[column][index.row()]
        return None

    def _header_ids(self, index):
        """Returns the ids of the row *and* column headers corresponding to the given header or data index.

        Args:
            index (QModelIndex)

        Returns:
            tuple(int)
        """
        row, column = self.map_to_pivot(index)
        row_key = self.model.row_key(max(0, row))
        column_key = self.model.column_key(max(0, column))
        return self.model._key_getter(row_key + column_key + self.model.frozen_value)

    def _header_name(self, top_left_id, header_id):
        """Returns the name of the header given by top_left_id and header_id.

        Args:
            top_left_id (int): The id of the top left header
            header_id (int): The header id

        Returns
            str
        """
        if top_left_id == -1:
            return self.db_mngr.get_item(self.db_map, "parameter definition", header_id).get("parameter_name")
        return self.db_mngr.get_item(self.db_map, "object", header_id)["name"]

    def header_name(self, index):
        """Returns the name corresponding to the given header index.

        Args:
            index (QModelIndex)

        Returns:
            str
        """
        header_id = self._header_id(index)
        top_left_id = self._top_left_id(index)
        return self._header_name(top_left_id, header_id)

    def header_names(self, index):
        """Returns the header names corresponding to the given data index.

        Args:
            index (QModelIndex)

        Returns:
            list(str): object names
            str: parameter name
        """
        header_ids = self._header_ids(index)
        objects_ids, parameter_id = header_ids[:-1], header_ids[-1]
        object_names = [self.db_mngr.get_item(self.db_map, "object", id_)["name"] for id_ in objects_ids]
        parameter_name = self.db_mngr.get_item(self.db_map, "parameter definition", parameter_id)["parameter_name"]
        return object_names, parameter_name

    def value_name(self, index):
        """Returns a string that concatenates the header names corresponding to the given data index.

        Args:
            index (QModelIndex)

        Returns:
            str
        """
        if not self.index_in_data(index):
            return ""
        object_names, parameter_name = self.header_names(index)
        return self.db_mngr._GROUP_SEP.join(object_names) + " - " + parameter_name

    def column_name(self, column):
        """Returns a string that concatenates the header names corresponding to the given column.

        Args:
            column (int)

        Returns:
            str
        """
        header_names = []
        column -= self.headerColumnCount()
        for row, top_left_id in enumerate(self.model.pivot_columns):
            header_id = self.model._column_data_header[column][row]
            header_names.append(self._header_name(top_left_id, header_id))
        return self.db_mngr._GROUP_SEP.join(header_names)

    def _color_data(self, index):
        if index.row() < self.headerRowCount() and index.column() < self.headerColumnCount():
            return QColor(PIVOT_TABLE_HEADER_COLOR)

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            if self.index_in_top(index):
                return self.model.pivot_rows[index.column()]
            if self.index_in_left(index):
                return self.model.pivot_columns[index.row()]
            if self.index_in_headers(index):
                return self.header_name(index)
            if self.index_in_data(index):
                row, column = self.map_to_pivot(index)
                data = self.model.get_pivoted_data([row], [column])
                if not data:
                    return None
                if self._parent.is_value_input_type():
                    if data[0][0] is None:
                        return None
                    return self.db_mngr.get_value(self.db_map, "parameter value", data[0][0], "value", role)
                return bool(data[0][0])
            return None
        if role == Qt.FontRole and self.index_in_top_left(index):
            font = QFont()
            font.setBold(True)
            return font
        if role == Qt.BackgroundColorRole:
            return self._color_data(index)
        if (
            role == Qt.TextAlignmentRole
            and self.index_in_data(index)
            and not self._parent.is_value_input_type()
            # or self.index_in_column_headers(index)
        ):
            return Qt.AlignHCenter
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        if self.index_in_data(index):
            # edit existing data
            row, column = self.map_to_pivot(index)
            data = self.model.get_pivoted_data([row], [column])
            if not data:
                return False
            if self._parent.is_value_input_type():
                if data[0][0] is None:
                    self.add_parameter_value(index, value)
                else:
                    self.update_parameter_value(data[0][0], value)
            else:
                if data[0][0] is None:
                    self.add_relationship(index)
                else:
                    self.remove_relationship(data[0][0])
            return True
        if self.index_in_headers(index):
            header_id = self._header_id(index)
            top_left_id = self._top_left_id(index)
            self._set_header_name(top_left_id, header_id, value)
            return True
        if self.index_in_empty_row_headers(index):
            top_left_id = self.model.pivot_rows[index.column()]
            self._set_empty_header_name(top_left_id, value)
            return True
        if self.index_in_empty_column_headers(index):
            top_left_id = self.model.pivot_columns[index.row()]
            self._set_empty_header_name(top_left_id, value)
            return True
        return False

    def _set_header_name(self, top_left_id, header_id, value):
        item = dict(id=header_id, name=value)
        if top_left_id == -1:
            self.db_mngr.update_parameter_definitions({self.db_map: [item]})
        else:
            self.db_mngr.update_objects({self.db_map: [item]})

    def _set_empty_header_name(self, top_left_id, value):
        item = dict(name=value)
        if top_left_id == -1:
            class_key = (
                "object_class_id"
                if self._parent.current_class_type == self._parent._OBJECT_CLASS
                else "relationship_class_id"
            )
            item[class_key] = self._parent.current_class_id
            self.db_mngr.add_parameter_definitions({self.db_map: [item]})
        else:
            item["class_id"] = self._parent.current_object_class_id_list()[top_left_id]
            self.db_mngr.add_objects({self.db_map: [item]})

    def _get_relationship(self, object_ids):
        """
        Returns a relationship dictionary item associated with given object ids.

        Args:
            object_ids (tuple(int)):

        Returns:
            dict, NoneType
        """
        object_id_list = ",".join([str(id_) for id_ in object_ids])
        relationships = self.db_mngr.get_items(self.db_map, "relationship")
        return next(
            iter(
                rel
                for rel in relationships
                if rel["class_id"] == self._parent.current_class_id and rel["object_id_list"] == object_id_list
            )
        )

    def _new_relationship_parameter_value(self, object_ids, value):
        """Returns a new parameter value item to insert to the db.

        Args:
            object_ids (tuple(int)):
            value
        Returns:
            dict
        """
        relationship = self._get_relationship(object_ids)
        return dict(relationship_id=relationship["id"], value=value)

    def add_parameter_value(self, index, value):
        """
        Args:
            index (QModelIndex)
            value
        """
        header_ids = self._header_ids(index)
        if self._parent.current_class_type == self._parent._RELATIONSHIP_CLASS:
            item = self._new_relationship_parameter_value(header_ids[:-1], value)
        else:
            object_id = header_ids[0]
            item = dict(object_id=object_id, value=value)
        parameter_id = header_ids[-1]
        item["parameter_definition_id"] = parameter_id
        self.db_mngr.add_parameter_values({self.db_map: [item]})

    def update_parameter_value(self, id_, value):
        """
        Args:
            id_ (int)
            value
        """
        db_map_data = {self.db_map: [dict(id=id_, value=value)]}
        self.db_mngr.update_parameter_values(db_map_data)

    def add_relationship(self, index):
        """
        Args:
            index (QModelIndex)
        """
        objects_id_list = list(self._header_ids(index))
        class_id = self._parent.current_class_id
        rel_cls_name = self.db_mngr.get_item(self.db_map, "relationship class", self._parent.current_class_id)["name"]
        object_names = [self.db_mngr.get_item(self.db_map, "object", id_)["name"] for id_ in objects_id_list]
        name = rel_cls_name + "_" + "__".join(object_names)
        relationship = dict(object_id_list=objects_id_list, class_id=class_id, name=name)
        db_map_data = {self.db_map: [relationship]}
        self.db_mngr.add_relationships(db_map_data)

    def remove_relationship(self, id_):
        """
        Args:
            id_ (int)
        """
        relationship = self.db_mngr.get_item(self.db_map, "relationship", id_)
        db_map_typed_data = {self.db_map: {"relationship": [relationship]}}
        self.db_mngr.remove_items(db_map_typed_data)


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

    def filterAcceptsRow(self, source_row, source_parent):
        """Returns true if the item in the row indicated by the given source_row
        and source_parent should be included in the model; otherwise returns false.
        """

        if source_row < self.sourceModel().headerRowCount() or source_row == self.sourceModel().rowCount() - 1:
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
        if self.sourceModel().model.pivot_columns:
            index = self.sourceModel().model._column_data_header[source_column - self.sourceModel().headerColumnCount()]
            return self.accept_index(index, self.sourceModel().model.pivot_columns)
        return True
