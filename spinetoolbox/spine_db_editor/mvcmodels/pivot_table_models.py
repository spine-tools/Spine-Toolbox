######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""
from collections import defaultdict
from contextlib import suppress
from functools import partial

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont

from spinedb_api import DatabaseMapping
from spinedb_api.parameter_value import join_value_and_type, split_value_and_type
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, parameter_identifier
from spinetoolbox.fetch_parent import FlexibleFetchParent
from .colors import FIXED_FIELD_COLOR, PIVOT_TABLE_HEADER_COLOR
from .pivot_model import PivotModel
from ...mvcmodels.shared import PARSED_ROLE
from ..widgets.custom_delegates import (
    RelationshipPivotTableDelegate,
    ParameterPivotTableDelegate,
    ScenarioAlternativeTableDelegate,
)


class TopLeftHeaderItem:
    """Base class for all 'top left pivot headers'.
    Represents a header located in the top left area of the pivot table."""

    def __init__(self, model):
        """
        Args:
            model (PivotTableModelBase)
        """
        self._model = model

    @property
    def model(self):
        return self._model

    @property
    def db_mngr(self):
        return self._model.db_mngr

    def _get_header_data_from_db(self, item_type, header_id, field_name, role):
        db_map, id_ = header_id
        item = self.db_mngr.get_item(db_map, item_type, id_)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return item.get(field_name)
        if role == Qt.ItemDataRole.ToolTipRole:
            return item.get("description", "No description")

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):
        """Returns header data for given id.

        Args:
            header_id (Any): header id
            role (Qt.ItemDataRole): data role

        Returns:
            Any: data corresponding to role
        """
        raise NotImplementedError()

    def update_data(self, db_map_data):
        """Updates database data.

        Args:
            db_map_data (dict): update data

        Returns:
            bool: True if data was successfully updated, False otherwise
        """
        raise NotImplementedError()

    def add_data(self, names, db_map):
        """Adds more data to database.

        Args:
            names (set of str): header names
            db_map (DatabaseMapping): database to add the data to

        Returns:
            bool: True if data was added successfully, False otherwise
        """
        raise NotImplementedError()


class TopLeftObjectHeaderItem(TopLeftHeaderItem):
    """A top left header for object_class."""

    def __init__(self, model, rank, class_name, class_id):
        super().__init__(model)
        self.rank = rank
        self._name = class_name
        self._class_id = class_id

    @property
    def header_type(self):
        return "object"

    @property
    def name(self):
        return self._name

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):
        """See base class."""
        return self._get_header_data_from_db("object", header_id, "name", role)

    def update_data(self, db_map_data):
        """See base class."""
        if not db_map_data:
            return False
        self.db_mngr.update_objects(db_map_data)
        return True

    def add_data(self, names, db_map):
        """See base class."""
        if not names:
            return False
        class_id = self._class_id[db_map]
        db_map_data = {db_map: [{"name": name, "class_id": class_id} for name in names]}
        self.db_mngr.add_objects(db_map_data)
        return True


class TopLeftParameterHeaderItem(TopLeftHeaderItem):
    """A top left header for parameter_definition."""

    @property
    def header_type(self):
        return "parameter"

    @property
    def name(self):
        return "parameter"

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):
        """See base class."""
        return self._get_header_data_from_db("parameter_definition", header_id, "parameter_name", role)

    def update_data(self, db_map_data):
        """See base class."""
        if not db_map_data:
            return False
        self.db_mngr.update_parameter_definitions(db_map_data)
        return True

    def add_data(self, names, db_map):
        """See base class."""
        if not names:
            return False
        class_id = self.model._parent.current_class_id[db_map]
        db_map_data = {db_map: [{"name": name, "entity_class_id": class_id} for name in names]}
        self.db_mngr.add_parameter_definitions(db_map_data)
        return True


class TopLeftParameterIndexHeaderItem(TopLeftHeaderItem):
    """A top left header for parameter index."""

    @property
    def header_type(self):
        return "index"

    @property
    def name(self):
        return "index"

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):  # pylint: disable=no-self-use
        """See base class."""
        _, index = header_id
        if role == PARSED_ROLE:
            return index
        return str(index)

    def update_data(self, db_map_data):  # pylint: disable=no-self-use
        """See base class."""
        return False

    def add_data(self, names, db_map):  # pylint: disable=no-self-use
        """See base class."""
        return False


class TopLeftAlternativeHeaderItem(TopLeftHeaderItem):
    """A top left header for alternative."""

    @property
    def header_type(self):
        return "alternative"

    @property
    def name(self):
        return "alternative"

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):  # pylint: disable=no-self-use
        """See base class."""
        return self._get_header_data_from_db("alternative", header_id, "name", role)

    def update_data(self, db_map_data):
        """See base class."""
        if not db_map_data:
            return False
        self.db_mngr.update_alternatives(db_map_data)
        return True

    def add_data(self, names, db_map):
        """See base class."""
        if not names:
            return False
        db_map_data = {db_map: [{"name": name} for name in names]}
        self.db_mngr.add_alternatives(db_map_data)
        return True


class TopLeftScenarioHeaderItem(TopLeftHeaderItem):
    """A top left header for scenario."""

    @property
    def header_type(self):
        return "scenario"

    @property
    def name(self):
        return "scenario"

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):  # pylint: disable=no-self-use
        """See base class."""
        return self._get_header_data_from_db("scenario", header_id, "name", role)

    def update_data(self, db_map_data):
        """See base class."""
        if not db_map_data:
            return False
        self.db_mngr.update_scenarios(db_map_data)
        return True

    def add_data(self, names, db_map):
        """See base class."""
        if not names:
            return False
        db_map_data = {db_map: [{"name": name} for name in names]}
        self.db_mngr.add_scenarios(db_map_data)
        return True


class TopLeftDatabaseHeaderItem(TopLeftHeaderItem):
    """A top left header for database."""

    def __init__(self, model):
        super().__init__(model)
        self._suggested_codename = None

    @property
    def header_type(self):
        return "database"

    @property
    def name(self):
        return "database"

    def header_data(self, header_id, role=Qt.ItemDataRole.DisplayRole):  # pylint: disable=no-self-use
        """See base class."""
        return header_id.codename

    def update_data(self, db_map_data):
        """See base class."""
        return False

    def add_data(self, names, db_map):
        """See base class."""
        return False

    def set_data(self, codename):
        """Sets database mapping's codename.

        Args:
            codename (str): database codename

        Returns:
            bool: True if codename was acceptable, False otherwise
        """
        if any(db_map.codename == codename for db_map in self.model.db_maps):
            self._suggested_codename = codename
            return True
        return False

    def take_suggested_db_map(self):
        """Suggests database mapping resetting the suggestion afterwards.

        Returns:
            DatabaseMapping: database mapping
        """
        if self._suggested_codename is not None:
            for db_map in self.model.db_maps:
                if db_map.codename == self._suggested_codename:
                    self._suggested_codename = None
                    return db_map
            raise RuntimeError(f"Logic error: no such database mapping `{self._suggested_codename}`")
        return next(iter(self.model.db_maps))

    def suggest_db_map_codename(self):
        """Suggests a database mapping codename.

        Returns:
            str: codename
        """
        if self._suggested_codename is not None:
            return self._suggested_codename
        return next(iter(self.model.db_maps)).codename


class PivotTableModelBase(QAbstractTableModel):
    _CHUNK_SIZE = 1000
    model_data_changed = Signal()
    frozen_values_added = Signal(set)
    frozen_values_removed = Signal(set)

    def __init__(self, db_editor):
        """
        Args:
            db_editor (SpineDBEditor)
        """
        super().__init__(db_editor)
        self._parent = db_editor
        self.db_mngr = db_editor.db_mngr
        self.model = PivotModel()
        self.top_left_headers = {}
        self._active = False
        self._plot_x_column = None
        self._data_row_count = 0
        self._data_column_count = 0
        self.modelAboutToBeReset.connect(self._reset_data_count)
        self.modelReset.connect(lambda *args: QTimer.singleShot(0, self._collect_more_data))
        self.rowsInserted.connect(lambda *args: QTimer.singleShot(0, self._collect_more_rows))
        self.columnsInserted.connect(lambda *args: QTimer.singleShot(0, self._collect_more_columns))

    @property
    def db_maps(self):
        return self._parent.db_maps

    def reset_fetch_parents(self):
        for parent in self._fetch_parents():
            parent.reset_fetching(None)

    def _fetch_parents(self):
        """Yields fetch parents for this model.

        Yields:
            FetchParent
        """
        raise NotImplementedError()

    def canFetchMore(self, _):
        if not self._active:
            return False
        result = False
        for fetch_parent in self._fetch_parents():
            for db_map in self._parent.db_maps:
                result |= self.db_mngr.can_fetch_more(db_map, fetch_parent)
        return result

    def fetchMore(self, _):
        if not self._active:
            return
        for parent in self._fetch_parents():
            for db_map in self._parent.db_maps:
                self.db_mngr.fetch_more(db_map, parent)

    @property
    def item_type(self):
        """Returns the item type."""
        raise NotImplementedError()

    @Slot()
    def _reset_data_count(self):
        self._data_row_count = 0
        self._data_column_count = 0

    @Slot()
    def _collect_more_data(self):
        self._collect_more_rows()
        self._collect_more_columns()

    @Slot()
    def _collect_more_rows(self):
        count = min(self._CHUNK_SIZE, len(self.model.rows) - self._data_row_count)
        if not count:
            return
        first = self.headerRowCount() + self.dataRowCount()
        self.beginInsertRows(QModelIndex(), first, first + count - 1)
        self._data_row_count += count
        self.endInsertRows()

    @Slot()
    def _collect_more_columns(self):
        count = min(self._CHUNK_SIZE, len(self.model.columns) - self._data_column_count)
        if not count:
            return
        first = self.headerColumnCount() + self.dataColumnCount()
        self.beginInsertColumns(QModelIndex(), first, first + count - 1)
        self._data_column_count += count
        self.endInsertColumns()

    def call_reset_model(self, pivot=None):
        """

        Args:
            pivot (tuple, optional): list of rows, list of columns, list of frozen indexes, frozen value
        """
        raise NotImplementedError()

    @staticmethod
    def make_delegate(parent):
        raise NotImplementedError()

    def reset_model(self, data, index_ids, rows=(), columns=(), frozen=(), frozen_value=()):
        self.beginResetModel()
        self.model.reset_model(data, index_ids, rows, columns, frozen, frozen_value)
        self._active = True
        self.endResetModel()
        self._plot_x_column = None
        self.reset_fetch_parents()

    def clear_model(self):
        self.beginResetModel()
        self.model.clear_model()
        self._active = False
        self.endResetModel()
        self._plot_x_column = None
        self.reset_fetch_parents()

    def update_model(self, data):
        """Update model with new data, but doesn't grow the model.

        Args:
            data (dict)
        """
        if not data:
            return
        self.model.update_model(data)
        self._emit_all_data_changed()

    def add_to_model(self, db_map_data):
        if not db_map_data:
            return
        frozen_values = self.model.frozen_values(db_map_data)
        if frozen_values:
            self.frozen_values_added.emit(frozen_values)
        row_count, column_count = self.model.add_to_model(db_map_data)
        if row_count > 0:
            first = self.headerRowCount() + self.dataRowCount()
            self.beginInsertRows(QModelIndex(), first, first + row_count - 1)
            self._data_row_count += row_count
            self.endInsertRows()
        if column_count > 0:
            first = self.headerColumnCount() + self.dataColumnCount()
            self.beginInsertColumns(QModelIndex(), first, first + column_count - 1)
            self._data_column_count += column_count
            self.endInsertColumns()
        self._emit_all_data_changed()

    def remove_from_model(self, data):
        if not data:
            return
        row_count, column_count = self.model.remove_from_model(data)
        frozen_values = self.model.frozen_values(data)
        if frozen_values:
            self.frozen_values_removed.emit(frozen_values)
        if row_count > 0:
            first = self.headerRowCount()
            self.beginRemoveRows(QModelIndex(), first, first + row_count - 1)
            self._data_row_count -= row_count
            self.endRemoveRows()
        if column_count > 0:
            first = self.headerColumnCount()
            self.beginRemoveColumns(QModelIndex(), first, first + column_count - 1)
            self._data_column_count -= column_count
            self.endRemoveColumns()
        self._emit_all_data_changed()

    def _emit_all_data_changed(self):
        top_left = self.index(self.headerRowCount(), self.headerColumnCount())
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)
        self.model_data_changed.emit()

    def set_pivot(self, rows, columns, frozen, frozen_value):
        self.beginResetModel()
        self.model.set_pivot(rows, columns, frozen, frozen_value)
        self.endResetModel()

    def set_frozen(self, frozen):
        """Sets the order of frozen headers without changing model data.

        Args:
            frozen (list of str): new frozen
        """
        self.model.set_frozen(frozen)

    def set_frozen_value(self, frozen_value):
        """Sets frozen value resetting the model.

        Args:
            frozen_value (tuple): frozen value

        Returns:
            bool: True if value was set, False otherwise
        """
        if frozen_value == self.model.frozen_value:
            return False
        self.beginResetModel()
        self.model.set_frozen_value(frozen_value)
        self.endResetModel()
        return True

    def set_plot_x_column(self, column, is_x):
        """Sets or clears the X flag on a column"""
        if is_x:
            self._plot_x_column = column
        elif column == self._plot_x_column:
            self._plot_x_column = None
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, column, column)

    @property
    def plot_x_column(self):
        """Returns the index of the column designated as Y values for plotting or None."""
        return self._plot_x_column

    def x_value(self, index):
        """Returns x value for given model index.

        Args:
            index (QModelIndex): model index

        Returns:
            Any: x value
        """
        x_index = self.index(index.row(), self._plot_x_column)
        return self.data(x_index, PARSED_ROLE)

    def x_parameter_name(self):
        """Returns x column's parameter name.

        Returns:
            str: parameter name
        """
        pivot_column = self._plot_x_column - self.headerColumnCount()
        header_ids = self._header_ids(0, pivot_column)
        _, parameter_id = header_ids[-3]
        db_map = header_ids[-1]
        parameter_name = self.db_mngr.get_item(db_map, "parameter_definition", parameter_id).get("parameter_name", "")
        return parameter_name

    def headerRowCount(self):
        """Returns number of rows occupied by header."""
        return len(self.model.pivot_columns) + int(bool(self.model.pivot_rows))

    def headerColumnCount(self):
        """Returns number of columns occupied by header."""
        return max(int(bool(self.model.pivot_columns)), len(self.model.pivot_rows))

    def dataRowCount(self):
        """Returns number of rows that contain actual data."""
        if self.model.pivot_columns and not self.model.pivot_rows:
            return 1
        return self._data_row_count

    def dataColumnCount(self):
        """Returns number of columns that contain actual data."""
        if self.model.pivot_rows and not self.model.pivot_columns:
            return 1
        return self._data_column_count

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
        row = index.row()
        is_top = row < self.headerRowCount()
        is_left = index.column() < self.headerColumnCount()
        if is_top and is_left:
            return ~Qt.ItemIsEnabled
        if self.model.pivot_rows and row == len(self.model.pivot_columns):
            # empty line between column headers and data
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if is_top or is_left:
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            id_ = self.top_left_id(index)
            if id_ is None or not isinstance(self.top_left_headers[id_], TopLeftDatabaseHeaderItem):
                flags |= Qt.ItemIsEditable
            return flags
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

    def index_within_top_left(self, index):
        return index.row() < self.headerRowCount() and index.column() < self.headerColumnCount()

    def index_in_top(self, index):
        return index.row() == self.headerRowCount() - 1 and index.column() < len(self.model.pivot_rows)

    def index_in_left(self, index):
        return index.column() == self.headerColumnCount() - 1 and index.row() < len(self.model.pivot_columns)

    def index_in_top_left(self, index):
        """Returns whether the given index is in top left corner, where pivot names are displayed."""
        return self.index_in_top(index) or self.index_in_left(index)

    def index_in_column_headers(self, index):
        """Returns whether the given index is in column headers (horizontal) area."""
        return (
            index.row() < len(self.model.pivot_columns)
            and self.headerColumnCount() <= index.column() < self.headerColumnCount() + self.dataColumnCount()
        )

    def index_in_row_headers(self, index):
        """Returns whether the given index is in row headers (vertical) area."""
        return (
            index.column() < len(self.model.pivot_rows)
            and self.headerRowCount() <= index.row() < self.headerRowCount() + self.dataRowCount()
        )

    def index_in_headers(self, index):
        return self.index_in_column_headers(index) or self.index_in_row_headers(index)

    def index_in_empty_column_headers(self, index):
        """Returns whether the given index is in empty column headers (vertical) area."""
        return index.row() < len(self.model.pivot_columns) and index.column() == self.columnCount() - 1

    def index_in_empty_row_headers(self, index):
        """Returns whether the given index is in empty row headers (vertical) area."""
        return index.column() < len(self.model.pivot_rows) and index.row() == self.rowCount() - 1

    def index_in_data(self, index):
        """Returns whether the given index is in data area."""
        return (
            self.headerRowCount() <= index.row() < self.rowCount() - self.emptyRowCount()
            and self.headerColumnCount() <= index.column() < self.columnCount() - self.emptyColumnCount()
        )

    def column_is_index_column(self, column):  # pylint: disable=no-self-use
        """Returns True if column is the column containing expanded parameter_value indexes."""
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and section == self._plot_x_column:
                return "(X)"
            if orientation == Qt.Orientation.Vertical:
                return 5 * " "
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

    def top_left_id(self, index):
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
            tuple or DatabaseMapping or NoneType
        """
        if self.index_in_row_headers(index):
            row, _ = self.map_to_pivot(index)
            return self.model._row_data_header[row][index.column()]
        if self.index_in_column_headers(index):
            _, column = self.map_to_pivot(index)
            return self.model._column_data_header[column][index.row()]
        return None

    def _header_ids(self, row, column):
        """Returns the ids for the headers at given row *and* column.

        Args:
            row (int)
            column (int)

        Returns:
            tuple(int)
        """
        row_key = self.model.row_key(max(0, row))
        column_key = self.model.column_key(max(0, column))
        return self.model._key_getter(row_key + column_key + self.model.frozen_value)

    def header_name(self, index):
        """Returns the name corresponding to the given header index.
        Used by PivotTableView.

        Args:
            index (QModelIndex)

        Returns:
            str
        """
        header_id = self._header_id(index)
        top_left_id = self.top_left_id(index)
        return self._header_name(top_left_id, header_id)

    def _color_data(self, index):
        is_top = index.row() < self.headerRowCount()
        is_left = index.column() < self.headerColumnCount()
        if is_top and is_left:
            return PIVOT_TABLE_HEADER_COLOR
        if is_top or is_left:
            id_ = self.top_left_id(index)
            if id_ is not None and isinstance(self.top_left_headers[id_], TopLeftDatabaseHeaderItem):
                return FIXED_FIELD_COLOR
        return None

    def _text_alignment_data(self, index):  # pylint: disable=no-self-use
        return None

    def _header_data(self, index, role=Qt.ItemDataRole.DisplayRole):
        header_id = self._header_id(index)
        top_left_id = self.top_left_id(index)
        return self._header_name(top_left_id, header_id)

    def _header_name(self, top_left_id, header_id):
        return self.top_left_headers[top_left_id].header_data(header_id)

    def _data(self, index, role):
        raise NotImplementedError()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, Qt.ItemDataRole.ToolTipRole, PARSED_ROLE):
            if self.index_in_top(index):
                return self.model.pivot_rows[index.column()]
            if self.index_in_left(index):
                return self.model.pivot_columns[index.row()]
            if self.index_in_headers(index):
                return self._header_data(index, role)
            if self.index_in_data(index):
                return self._data(index, role)
            if "database" not in self.model.pivot_frozen:
                if self.emptyRowCount() > 0 and index.row() == self.headerRowCount() + self.dataRowCount():
                    with suppress(ValueError):
                        database_header_column = self.model.pivot_rows.index("database")
                        if index.column() == database_header_column:
                            return self.top_left_headers["database"].suggest_db_map_codename()
                elif (
                    self.emptyColumnCount() > 0 and index.column() == self.headerColumnCount() + self.dataColumnCount()
                ):
                    with suppress(ValueError):
                        database_header_row = self.model.pivot_columns.index("database")
                        if index.row() == database_header_row:
                            return self.top_left_headers["database"].suggest_db_map_codename()
            return None
        if role == Qt.ItemDataRole.FontRole and self.index_in_top_left(index):
            font = QFont()
            font.setBold(True)
            return font
        if role == Qt.ItemDataRole.BackgroundRole:
            return self._color_data(index)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._text_alignment_data(index)
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return False
        return self.batch_set_data([index], [value])

    def batch_set_data(self, indexes, values):
        inner_data = []
        header_data = []
        empty_row_header_data = []
        empty_column_header_data = []
        for index, value in zip(indexes, values):
            if self.index_in_data(index):
                inner_data.append((index, value))
            elif self.index_in_headers(index):
                header_data.append((index, value))
            elif self.index_in_empty_row_headers(index):
                empty_row_header_data.append((index, value))
            elif self.index_in_empty_column_headers(index):
                empty_column_header_data.append((index, value))
        result = self._batch_set_inner_data(inner_data)
        result |= self._batch_set_header_data(header_data)
        result |= self._batch_set_empty_header_data(empty_row_header_data, lambda i: self.model.pivot_rows[i.column()])
        result |= self._batch_set_empty_header_data(
            empty_column_header_data, lambda i: self.model.pivot_columns[i.row()]
        )
        return result

    def _batch_set_inner_data(self, inner_data):
        row_map = set()
        column_map = set()
        values = {}
        for index, value in inner_data:
            row, column = self.map_to_pivot(index)
            row_map.add(row)
            column_map.add(column)
            values[row, column] = value
        row_map = list(row_map)
        column_map = list(column_map)
        data = self.model.get_pivoted_data(row_map, column_map)
        if not data:
            return False
        return self._do_batch_set_inner_data(row_map, column_map, data, values)

    def _do_batch_set_inner_data(self, row_map, column_map, data, values):
        raise NotImplementedError()

    def _batch_set_header_data(self, header_data):
        """Sets header data for multiple indexes at once.

        Args:
            header_data (list of tuple): mapping from index to data

        Returns:
            bool: True if data was set successfully, False otherwise
        """
        list_dict = partial(defaultdict, list)
        data_by_top_left_id = defaultdict(list_dict)
        for index, value in header_data:
            header_id = self._header_id(index)
            if isinstance(header_id, tuple):
                top_left_id = self.top_left_id(index)
                item = dict(id=header_id[1], name=value)
                data_by_top_left_id[top_left_id][header_id[0]].append(item)
        success = False
        for id_, data in data_by_top_left_id.items():
            success = success or self.top_left_headers[id_].update_data(data)
        return success

    def _batch_set_empty_header_data(self, header_data, get_top_left_id):
        names_by_top_left_id = defaultdict(set)
        db_map = None
        for value in self.model.frozen_value:
            if isinstance(value, DatabaseMapping):
                db_map = value
                break
        for index, value in header_data:
            top_left_id = get_top_left_id(index)
            names_by_top_left_id[top_left_id].add(value)
        success = False
        for id_, names in names_by_top_left_id.items():
            header_item = self.top_left_headers[id_]
            if db_map is None:
                db_map = self.top_left_headers["database"].take_suggested_db_map()
            if isinstance(header_item, TopLeftDatabaseHeaderItem):
                header_item.set_data(next(iter(names)))
            else:
                success = success or header_item.add_data(names, db_map)
        return success


class ParameterValuePivotTableModel(PivotTableModelBase):
    """A model for the pivot table in parameter_value input type."""

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._entity_fetch_parent = FlexibleFetchParent(
            None,
            handle_items_added=self._handle_entities_added,
            handle_items_removed=self._handle_entities_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            accepts_item=self._parent.accepts_entity_item,
            owner=self,
        )
        self._parameter_definition_fetch_parent = FlexibleFetchParent(
            "parameter_definition",
            handle_items_added=self._handle_parameter_definitions_added,
            handle_items_removed=self._handle_parameter_definitions_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            accepts_item=self._parent.accepts_parameter_item,
            owner=self,
        )
        self._parameter_value_fetch_parent = FlexibleFetchParent(
            "parameter_value",
            handle_items_added=self._handle_parameter_values_added,
            handle_items_removed=self._handle_parameter_values_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            accepts_item=self._parent.accepts_parameter_item,
            owner=self,
            chunk_size=None,
        )
        self._alternative_fetch_parent = FlexibleFetchParent(
            "alternative",
            handle_items_added=self._handle_alternatives_added,
            handle_items_removed=self._handle_alternatives_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            owner=self,
        )

    def _handle_entities_added(self, db_map_data):
        data = self._load_empty_parameter_value_data(db_map_entities=db_map_data)
        self.add_to_model(data)

    def _handle_entities_removed(self, db_map_data):
        data = self._load_empty_parameter_value_data(db_map_entities=db_map_data)
        self.remove_from_model(data)

    def _handle_parameter_definitions_added(self, db_map_data):
        db_map_parameter_ids = {
            db_map: {(db_map, x["id"]) for x in parameters} for db_map, parameters in db_map_data.items()
        }
        data = self._load_empty_parameter_value_data(db_map_parameter_ids=db_map_parameter_ids)
        self.add_to_model(data)

    def _handle_parameter_definitions_removed(self, db_map_data):
        db_map_parameter_ids = {
            db_map: {(db_map, x["id"]) for x in parameters} for db_map, parameters in db_map_data.items()
        }
        data = self._load_empty_parameter_value_data(db_map_parameter_ids=db_map_parameter_ids)
        self.remove_from_model(data)

    def _handle_parameter_values_added(self, db_map_data):
        data = self._load_full_parameter_value_data(db_map_parameter_values=db_map_data, action="add")
        self.add_to_model(data)

    def _handle_parameter_values_removed(self, db_map_data):
        data = self._load_full_parameter_value_data(db_map_parameter_values=db_map_data, action="remove")
        self.remove_from_model(data)

    def _handle_alternatives_added(self, db_map_data):
        db_map_alternative_ids = {db_map: [(db_map, a["id"]) for a in items] for db_map, items in db_map_data.items()}
        data = self._load_empty_parameter_value_data(db_map_alternative_ids=db_map_alternative_ids)
        self.add_to_model(data)

    def _handle_alternatives_removed(self, db_map_data):
        db_map_alternative_ids = {db_map: [(db_map, a["id"]) for a in items] for db_map, items in db_map_data.items()}
        data = self._load_empty_parameter_value_data(db_map_alternative_ids=db_map_alternative_ids)
        self.remove_from_model(data)

    def _load_empty_parameter_value_data(self, *args, **kwargs):
        return self._parent.load_empty_parameter_value_data(*args, **kwargs)

    def _load_full_parameter_value_data(self, *args, **kwargs):
        return self._parent.load_full_parameter_value_data(*args, **kwargs)

    @property
    def item_type(self):
        return "parameter_value"

    def _fetch_parents(self):
        yield self._parameter_value_fetch_parent
        yield self._alternative_fetch_parent
        yield self._parameter_definition_fetch_parent
        yield self._entity_fetch_parent

    def reset_fetch_parents(self):
        super().reset_fetch_parents()
        if self._parent.current_class_type == "object_class":
            self._entity_fetch_parent.fetch_item_type = "object"
        elif self._parent.current_class_type == "relationship_class":
            self._entity_fetch_parent.fetch_item_type = "relationship"

    def db_map_object_ids(self, index):
        """
        Returns db_map and object ids for given index. Used by PivotTableView.

        Returns:
            DatabaseMapping, list
        """
        row, column = self.map_to_pivot(index)
        header_ids = self._header_ids(row, column)
        return self._db_map_object_ids(header_ids)

    def _db_map_object_ids(self, header_ids):
        object_indexes = [
            k for k, h in enumerate(self.top_left_headers.values()) if isinstance(h, TopLeftObjectHeaderItem)
        ]
        return header_ids[-1], [header_ids[k][1] for k in object_indexes]

    def all_header_names(self, index):
        """Returns the object, parameter, alternative, and db names corresponding to the given data index.

        Args:
            index (QModelIndex)

        Returns:
            list(str): object names
            str: parameter name
            str: alternative name
            str: db name
        """
        row, column = self.map_to_pivot(index)
        header_ids = self._header_ids(row, column)
        _, objects_ids = self._db_map_object_ids(header_ids)
        _, parameter_id = header_ids[-3]
        _, alternative_id = header_ids[-2]
        db_map = header_ids[-1]
        object_names = [self.db_mngr.get_item(db_map, "object", id_)["name"] for id_ in objects_ids]
        parameter_name = self.db_mngr.get_item(db_map, "parameter_definition", parameter_id).get("parameter_name", "")
        alternative_name = self.db_mngr.get_item(db_map, "alternative", alternative_id).get("name", "")
        return object_names, parameter_name, alternative_name, db_map.codename

    def index_name(self, index):
        """Returns a string that concatenates the object and parameter names corresponding to the given data index.
        Used by plotting and ParameterValueEditor.

        Args:
            index (QModelIndex)

        Returns:
            str
        """
        if not self.index_in_data(index):
            return ""
        object_names, parameter_name, alternative_name, db_name = self.all_header_names(index)
        return parameter_identifier(db_name, parameter_name, object_names, alternative_name)

    def column_name(self, column):
        """Returns a string that concatenates the object and parameter names corresponding to the given column.
        Used by plotting.

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
        return DB_ITEM_SEPARATOR.join(header_names)

    def call_reset_model(self, pivot=None):
        """See base class."""
        object_class_ids = self._parent.current_object_class_ids
        data = {}
        top_left_headers = [
            TopLeftObjectHeaderItem(self, k, name, id_) for k, (name, id_) in enumerate(object_class_ids.items())
        ]
        top_left_headers += [TopLeftParameterHeaderItem(self)]
        top_left_headers += [TopLeftAlternativeHeaderItem(self)]
        top_left_headers += [TopLeftDatabaseHeaderItem(self)]
        self.top_left_headers = {h.name: h for h in top_left_headers}
        if pivot is None:
            pivot = self._default_pivot(data)
        self.reset_model(data, self.top_left_headers, *pivot)

    @staticmethod
    def make_delegate(parent):
        return ParameterPivotTableDelegate(parent)

    def _default_pivot(self, data):
        header_names = list(self.top_left_headers)
        rows = header_names[:-3]
        columns = [header_names[-3]]
        frozen = header_names[-2:]
        key = next(iter(data), [None, None])
        frozen_value = key[-2:]
        return rows, columns, frozen, frozen_value

    def _data(self, index, role):
        row, column = self.map_to_pivot(index)
        data = self.model.get_pivoted_data([row], [column])
        if not data:
            return None
        if data[0][0] is None:
            return None
        db_map, id_ = data[0][0]
        return self.db_mngr.get_value(db_map, "parameter_value", id_, role)

    def _do_batch_set_inner_data(self, row_map, column_map, data, values):
        return self._batch_set_parameter_value_data(row_map, column_map, data, values)

    def _object_parameter_value_to_add(self, db_map, header_ids, value_and_type):
        value, value_type = split_value_and_type(value_and_type)
        return dict(
            object_class_id=self._parent.current_class_id[db_map],
            object_id=header_ids[0],
            parameter_definition_id=header_ids[-2],
            value=value,
            type=value_type,
            alternative_id=header_ids[-1],
        )

    def _relationship_parameter_value_to_add(self, db_map, header_ids, value_and_type, rel_id_lookup):
        object_id_list = tuple(id_ for id_ in header_ids[:-2])
        value, value_type = split_value_and_type(value_and_type)
        return dict(
            relationship_class_id=self._parent.current_class_id[db_map],
            relationship_id=rel_id_lookup[db_map, object_id_list],
            parameter_definition_id=header_ids[-2],
            value=value,
            type=value_type,
            alternative_id=header_ids[-1],
        )

    def _make_parameter_value_to_add(self):
        if self._parent.current_class_type == "object_class":
            return self._object_parameter_value_to_add
        if self._parent.current_class_type == "relationship_class":
            db_map_relationships = {
                db_map: self.db_mngr.get_items_by_field(db_map, "relationship", "class_id", class_id)
                for db_map, class_id in self._parent.current_class_id.items()
            }
            rel_id_lookup = {
                (db_map, x["object_id_list"]): x["id"]
                for db_map, relationships in db_map_relationships.items()
                for x in relationships
            }
            return lambda db_map, header_ids, value, rel_id_lookup=rel_id_lookup: self._relationship_parameter_value_to_add(
                db_map, header_ids, value, rel_id_lookup
            )

    @staticmethod
    def _parameter_value_to_update(id_, header_ids, value_and_type):
        value, value_type = split_value_and_type(value_and_type)
        return {
            "id": id_,
            "value": value,
            "type": value_type,
            "parameter_definition_id": header_ids[-2],
            "alternative_id": header_ids[-1],
        }

    def _batch_set_parameter_value_data(self, row_map, column_map, data, values):
        """Sets parameter values in batch."""
        to_add = {}
        to_update = {}
        parameter_value_to_add = self._make_parameter_value_to_add()
        for i, row in enumerate(row_map):
            for j, column in enumerate(column_map):
                if (row, column) not in values:
                    continue
                header_ids = list(self._header_ids(row, column))
                db_map = header_ids.pop()
                header_ids = [id_ for _db_map, id_ in header_ids]
                if data[i][j] is None:
                    item = parameter_value_to_add(db_map, header_ids, values[row, column])
                    to_add.setdefault(db_map, []).append(item)
                else:
                    _db_map, id_ = data[i][j]
                    item = self._parameter_value_to_update(id_, header_ids, values[row, column])
                    to_update.setdefault(db_map, []).append(item)
        if not to_add and not to_update:
            return False
        if to_add:
            self._add_parameter_values(to_add)
        if to_update:
            self._update_parameter_values(to_update)
        return True

    def _add_parameter_values(self, db_map_data):
        self.db_mngr.add_parameter_values(db_map_data)

    def _update_parameter_values(self, db_map_data):
        self.db_mngr.update_parameter_values(db_map_data)

    def get_set_data_delayed(self, index):
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.

        Args:
            index (QModelIndex)

        Returns:
            function
        """
        row, column = self.map_to_pivot(index)
        data = self.model.get_pivoted_data([row], [column])
        header_ids = list(self._header_ids(row, column))
        db_map = header_ids.pop()
        header_ids = [id_ for _db_map, id_ in header_ids]
        if data[0][0] is None:
            func = self._make_parameter_value_to_add()
            return lambda value_type_tup, func=func, db_map=db_map, header_ids=header_ids: self._add_parameter_values(
                {db_map: [func(db_map, header_ids, join_value_and_type(*value_type_tup))]}
            )
        _db_map, id_ = data[0][0]
        return lambda value_type_tup, id_=id_, header_ids=header_ids: self._update_parameter_values(
            {db_map: [self._parameter_value_to_update(id_, header_ids, join_value_and_type(*value_type_tup))]}
        )


class IndexExpansionPivotTableModel(ParameterValuePivotTableModel):
    """A model for the pivot table in parameter index expansion input type."""

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._index_top_left_header = None

    def call_reset_model(self, pivot=None):
        """See base class."""
        object_class_ids = self._parent.current_object_class_ids
        data = {}
        top_left_headers = [
            TopLeftObjectHeaderItem(self, k, name, id_) for k, (name, id_) in enumerate(object_class_ids.items())
        ]
        self._index_top_left_header = TopLeftParameterIndexHeaderItem(self)
        top_left_headers += [
            self._index_top_left_header,
            TopLeftParameterHeaderItem(self),
            TopLeftAlternativeHeaderItem(self),
            TopLeftDatabaseHeaderItem(self),
        ]
        self.top_left_headers = {h.name: h for h in top_left_headers}
        if pivot is None:
            pivot = self._default_pivot(data)
        self.reset_model(data, self.top_left_headers, *pivot)
        pivot_rows = pivot[0]
        try:
            x_column = pivot_rows.index(self._index_top_left_header.name)
            self.set_plot_x_column(x_column, is_x=True)
        except ValueError:
            # The parameter index is not a column (it's either a row or frozen)
            pass

    def flags(self, index):
        """Roles for data"""
        if self.index_in_data(index):
            row, column = self.map_to_pivot(index)
            data = self.model.get_pivoted_data([row], [column])
            if not data or data[0][0] is None:
                # Don't add parameter values in index expansion mode
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.top_left_id(index) == self._index_top_left_header.name:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return super().flags(index)

    def column_is_index_column(self, column):
        """Returns True if column is the column containing expanded parameter_value indexes."""
        try:
            index_column = self.model.pivot_rows.index(self._index_top_left_header.name)
            return column == index_column
        except ValueError:
            # The parameter index is not a column (it's either a row or frozen)
            return False

    def _load_empty_parameter_value_data(self, *args, **kwargs):
        return self._parent.load_empty_expanded_parameter_value_data(*args, **kwargs)

    def _load_full_parameter_value_data(self, *args, **kwargs):
        return self._parent.load_full_expanded_parameter_value_data(*args, **kwargs)

    def _data(self, index, role):
        row, column = self.map_to_pivot(index)
        data = self.model.get_pivoted_data([row], [column])
        if not data:
            return None
        if data[0][0] is None:
            return None
        _, parameter_index = self._header_ids(row, column)[-4]
        db_map, id_ = data[0][0]
        return self.db_mngr.get_value_index(db_map, "parameter_value", id_, parameter_index, role)

    @staticmethod
    def _parameter_value_to_update(id_, header_ids, value_and_type):
        value, value_type = split_value_and_type(value_and_type)
        return {"id": id_, "value": value, "type": value_type, "index": header_ids[-3]}

    def _update_parameter_values(self, db_map_data):
        self.db_mngr.update_expanded_parameter_values(db_map_data)


class RelationshipPivotTableModel(PivotTableModelBase):
    """A model for the pivot table in relationship input type."""

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._relationship_fetch_parent = FlexibleFetchParent(
            "relationship",
            handle_items_added=self._handle_relationships_added,
            handle_items_removed=self._handle_relationships_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            accepts_item=self._parent.accepts_entity_item,
            owner=self,
            chunk_size=None,
        )
        self._object_fetch_parent = FlexibleFetchParent(
            "object",
            handle_items_added=self._handle_objects_added,
            handle_items_removed=self._handle_objects_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            accepts_item=self._parent.accepts_member_object_item,
            owner=self,
        )

    def _handle_relationships_added(self, db_map_data):
        data = self._parent.load_full_relationship_data(db_map_relationships=db_map_data, action="add")
        self.update_model(data)

    def _handle_relationships_removed(self, db_map_data):
        data = self._parent.load_full_relationship_data(db_map_relationships=db_map_data, action="remove")
        self.update_model(data)

    def _load_empty_relationship_data(self, db_map_data):
        db_map_class_objects = dict()
        for db_map, items in db_map_data.items():
            class_objects = db_map_class_objects[db_map] = dict()
            for item in items:
                class_objects.setdefault(item["class_id"], []).append(item)
        return self._parent.load_empty_relationship_data(db_map_class_objects=db_map_class_objects)

    def _handle_objects_added(self, db_map_data):
        data = self._load_empty_relationship_data(db_map_data)
        self.add_to_model(data)

    def _handle_objects_removed(self, db_map_data):
        data = self._load_empty_relationship_data(db_map_data)
        self.remove_from_model(data)

    @property
    def item_type(self):
        return "relationship"

    def _fetch_parents(self):
        yield self._object_fetch_parent
        yield self._relationship_fetch_parent

    def call_reset_model(self, pivot=None):
        """See base class."""
        object_class_ids = self._parent.current_object_class_ids
        data = {}
        top_left_headers = [
            TopLeftObjectHeaderItem(self, k, name, id_) for k, (name, id_) in enumerate(object_class_ids.items())
        ]
        top_left_headers += [TopLeftDatabaseHeaderItem(self)]
        self.top_left_headers = {h.name: h for h in top_left_headers}
        if pivot is None:
            pivot = self._default_pivot(data)
        self.reset_model(data, self.top_left_headers, *pivot)

    @staticmethod
    def make_delegate(parent):
        return RelationshipPivotTableDelegate(parent)

    def _default_pivot(self, data):
        header_names = list(self.top_left_headers)
        rows = header_names[:-1]
        columns = []
        frozen = [header_names[-1]]
        key = next(iter(data), [None])
        frozen_value = [key[-1]]
        return rows, columns, frozen, frozen_value

    def _data(self, index, role):
        row, column = self.map_to_pivot(index)
        data = self.model.get_pivoted_data([row], [column])
        if not data:
            return None
        return bool(data[0][0])

    def _do_batch_set_inner_data(self, row_map, column_map, data, values):
        return self._batch_set_relationship_data(row_map, column_map, data, values)

    def _batch_set_relationship_data(self, row_map, column_map, data, values):
        def relationship_to_add(db_map, header_ids):
            rel_cls_name = self.db_mngr.get_item(
                db_map, "relationship_class", self._parent.current_class_id.get(db_map)
            )["name"]
            object_names = [self.db_mngr.get_item(db_map, "object", id_)["name"] for id_ in header_ids]
            name = rel_cls_name + "_" + "__".join(object_names)
            return dict(object_id_list=list(header_ids), class_id=self._parent.current_class_id.get(db_map), name=name)

        to_add = {}
        to_remove = {}
        for i, row in enumerate(row_map):
            for j, column in enumerate(column_map):
                header_ids = list(self._header_ids(row, column))
                db_map = header_ids.pop()
                header_ids = [id_ for _, id_ in header_ids]
                if data[i][j] is None and values[row, column]:
                    item = relationship_to_add(db_map, header_ids)
                    to_add.setdefault(db_map, []).append(item)
                elif data[i][j] is not None and not values[row, column]:
                    _, id_ = data[i][j]
                    to_remove.setdefault(db_map, {}).setdefault("relationship", []).append(id_)
        if not to_add and not to_remove:
            return False
        if to_add:
            self.db_mngr.add_relationships(to_add)
        if to_remove:
            self.db_mngr.remove_items(to_remove)
        return True


class ScenarioAlternativePivotTableModel(PivotTableModelBase):
    """A model for the pivot table in scenario alternative input type."""

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._scenario_fetch_parent = FlexibleFetchParent(
            "scenario",
            handle_items_added=self._handle_scenarios_added,
            handle_items_removed=self._handle_scenarios_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            owner=self,
        )
        self._alternative_fetch_parent = FlexibleFetchParent(
            "alternative",
            handle_items_added=self._handle_alternatives_added,
            handle_items_removed=self._handle_alternatives_removed,
            handle_items_updated=lambda _: self._parent.refresh_views(),
            owner=self,
        )
        self._scenario_alternative_fetch_parent = FlexibleFetchParent(
            "scenario_alternative",
            handle_items_added=self._handle_scenario_alternatives_changed,
            handle_items_removed=self._handle_scenario_alternatives_changed,
            owner=self,
            chunk_size=None,
        )

    def _handle_scenarios_added(self, db_map_data):
        data = self._parent.load_scenario_alternative_data(db_map_scenarios=db_map_data)
        self.add_to_model(data)

    def _handle_scenarios_removed(self, db_map_data):
        data = self._parent.load_scenario_alternative_data(db_map_scenarios=db_map_data)
        self.remove_from_model(data)

    def _handle_alternatives_added(self, db_map_data):
        data = self._parent.load_scenario_alternative_data(db_map_alternatives=db_map_data)
        self.add_to_model(data)

    def _handle_alternatives_removed(self, db_map_data):
        data = self._parent.load_scenario_alternative_data(db_map_alternatives=db_map_data)
        self.remove_from_model(data)

    def _handle_scenario_alternatives_changed(self, db_map_data):
        db_map_scenarios = {
            db_map: [self.db_mngr.get_item(db_map, "scenario", x["scenario_id"]) for x in items]
            for db_map, items in db_map_data.items()
        }
        data = self._parent.load_scenario_alternative_data(db_map_scenarios=db_map_scenarios)
        self.update_model(data)

    @property
    def item_type(self):
        return "scenario_alternative"

    def _fetch_parents(self):
        yield self._scenario_fetch_parent
        yield self._alternative_fetch_parent
        yield self._scenario_alternative_fetch_parent

    def call_reset_model(self, pivot=None):
        """See base class."""
        data = {}
        top_left_headers = [
            TopLeftScenarioHeaderItem(self),
            TopLeftAlternativeHeaderItem(self),
            TopLeftDatabaseHeaderItem(self),
        ]
        self.top_left_headers = {h.name: h for h in top_left_headers}
        if pivot is None:
            pivot = self._default_pivot(data)
        self.reset_model(data, self.top_left_headers, *pivot)

    @staticmethod
    def make_delegate(parent):
        return ScenarioAlternativeTableDelegate(parent)

    def _default_pivot(self, data):
        header_names = list(self.top_left_headers)
        rows = [header_names[0]]
        columns = [header_names[1]]
        frozen = [header_names[-1]]
        key = next(iter(data), [None])
        frozen_value = [key[-1]]
        return rows, columns, frozen, frozen_value

    def _data(self, index, role):
        row, column = self.map_to_pivot(index)
        data = self.model.get_pivoted_data([row], [column])
        if not data:
            return None
        if data[0][0] is None:
            return False
        return data[0][0]

    def _do_batch_set_inner_data(self, row_map, column_map, data, values):
        return self._batch_set_scenario_alternative_data(row_map, column_map, data, values)

    def _batch_set_scenario_alternative_data(self, row_map, column_map, data, values):
        to_add = {}
        to_remove = {}
        for i, row in enumerate(row_map):
            for j, column in enumerate(column_map):
                header_ids = list(self._header_ids(row, column))
                db_map = header_ids.pop()
                scen_id, alt_id = [id_ for _, id_ in header_ids]
                if data[i][j] is None and values[row, column]:
                    to_add.setdefault((db_map, scen_id), []).append(alt_id)
                elif data[i][j] is not None and not values[row, column]:
                    to_remove.setdefault((db_map, scen_id), []).append(alt_id)
        if not to_add and not to_remove:
            return False
        db_map_items = {}
        for (db_map, scen_id), alt_ids_to_add in to_add.items():
            alt_ids_to_remove = to_remove.pop((db_map, scen_id), [])
            alternative_id_list = [
                id_
                for id_ in list(self.db_mngr.get_scenario_alternative_id_list(db_map, scen_id)) + alt_ids_to_add
                if id_ not in alt_ids_to_remove
            ]
            db_item = {"id": scen_id, "alternative_id_list": alternative_id_list}
            db_map_items.setdefault(db_map, []).append(db_item)
        for (db_map, scen_id), alt_ids_to_remove in to_remove.items():
            alternative_id_list = [
                id_
                for id_ in self.db_mngr.get_scenario_alternative_id_list(db_map, scen_id)
                if id_ not in alt_ids_to_remove
            ]
            db_item = {"id": scen_id, "alternative_id_list": alternative_id_list}
            db_map_items.setdefault(db_map, []).append(db_item)
        self.db_mngr.set_scenario_alternatives(db_map_items)
        return True


class PivotTableSortFilterProxy(QSortFilterProxyModel):
    model_data_changed = Signal()

    def __init__(self, parent=None):
        """Initialize class."""
        super().__init__(parent)
        self.setDynamicSortFilter(False)  # Important so we can edit parameters in the view
        self.index_filters = {}

    def setSourceModel(self, model):
        old_model = self.sourceModel()
        if old_model:
            old_model.model_data_changed.disconnect(self.model_data_changed)
        super().setSourceModel(model)
        model.model_data_changed.connect(self.model_data_changed)

    def set_filter(self, identifier, filter_value):
        """Sets filter for a given index (object_class) name.

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
        if not self.sourceModel().model.pivot_rows:
            return True
        index = self.sourceModel().model._row_data_header[source_row - self.sourceModel().headerRowCount()]
        return self.accept_index(index, self.sourceModel().model.pivot_rows)

    def filterAcceptsColumn(self, source_column, source_parent):
        """Returns true if the item in the column indicated by the given source_column
        and source_parent should be included in the model; otherwise returns false.
        """
        if (
            source_column < self.sourceModel().headerColumnCount()
            or source_column == self.sourceModel().columnCount() - 1
        ):
            return True
        if not self.sourceModel().model.pivot_columns:
            return True
        index = self.sourceModel().model._column_data_header[source_column - self.sourceModel().headerColumnCount()]
        return self.accept_index(index, self.sourceModel().model.pivot_columns)

    def batch_set_data(self, indexes, values):
        indexes = [self.mapToSource(index) for index in indexes]
        return self.sourceModel().batch_set_data(indexes, values)
