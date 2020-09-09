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
Contains :class:`IndexingTableModel`.

:author: A. Soininen (VTT)
:date:   25.8.2020
"""
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from spinetoolbox.spine_io.exporters import gdx


class IndexingTableModel(QAbstractTableModel):
    """
    A table model for parameter_value indexing.

    First column contains the proposed new index keys.
    The rest of the columns contain the parameter values for each set of existing index keys.
    Only selected new index keys are used for indexing.
    Unselected rows are left empty.
    """

    selection_changed = Signal()
    """Emitted after the values have been spread over the selected indexes."""
    manual_selection = Signal()
    """Emitted when the selection has been changed by setData()."""

    def __init__(self, parameter):
        """
        Args:
            parameter (Parameter): a parameter to model
        """
        super().__init__()
        self._records = gdx.LiteralRecords([])
        self._index_name = ""
        self._parameter_values = list(parameter.values)
        self._parameter_nonexpanded_indexes = list(parameter.indexes)
        self._selected = list()
        self._rows_shown = 0
        self._values = [list() for _ in range(len(self._parameter_values))]
        self.records_operational = True

    def get_picking(self):
        """
        Turns the checked record into picking.

        Returns:
            FixedPicking: picked records
        """
        return gdx.FixedPicking(list(self._selected))

    def canFetchMore(self, parent):
        """Returns True if more rows are available to show."""
        return self._rows_shown < len(self._records)

    def clear(self):
        """Clears the model."""
        self.beginResetModel()
        self._records = gdx.LiteralRecords([])
        self._selected = list()
        self._values = [list() for _ in range(len(self._parameter_values))]
        self._rows_shown = 0
        self.endResetModel()
        self.selection_changed.emit()

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns."""
        return len(self._parameter_values) + 1

    def data(self, index, role=Qt.DisplayRole):
        """Returns data associated with given model index and role."""
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            row = index.row()
            column = index.column()
            if column == 0:
                try:
                    value = self._records.records[row][0]
                except gdx.GdxExportException:
                    self.records_operational = False
                    return None
                else:
                    self.records_operational = True
                    return value
            return self._values[column - 1][row]
        if index.column() == 0 and role == Qt.CheckStateRole:
            return Qt.Checked if self._selected[index.row()] else Qt.Unchecked
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns header data."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        if section == 0:
            return self._index_name
        return ", ".join(self._parameter_nonexpanded_indexes[section - 1])

    def fetchMore(self, parent):
        """Inserts a number of new rows to the table."""
        remainder = len(self._records) - self._rows_shown
        fetch_size = min(remainder, 100)
        end = self._rows_shown + fetch_size
        self.beginInsertRows(parent, self._rows_shown, end - 1)
        for column in self._values:
            column += fetch_size * [None]
        start = self._rows_shown
        self._rows_shown = end
        self._spread_values_over_selected_rows(start)
        self.endInsertRows()

    def flags(self, index):
        """Returns flags for given index."""
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == 0:
            flags = flags | Qt.ItemIsUserCheckable
        return flags

    def mapped_values_balance(self):
        """
        Returns the balance between available indexes and parameter values.

        Zero means that there is as many indexes available as there are values,
        i.e. the parameter is 'perfectly' indexed.
        A positive value means there are more indexes than values
        while a negative value means there are not enough indexes for all values.

        Returns:
            int: mapped values' balance
        """
        count = sum(1 for selected in self._selected if selected)
        return count - len(self._parameter_values[0].values) if self._parameter_values else 0

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows."""
        return self._rows_shown

    def select_all(self):
        """Selects all indexes."""
        self._selected = len(self._records) * [True]
        top_left = self.index(0, 0)
        bottom_right = self.index(self._rows_shown - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])
        self._spread_values_over_selected_rows(0)
        self.selection_changed.emit()

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the checked state for given index."""
        if role != Qt.CheckStateRole:
            return False
        row = index.row()
        self._selected[row] = value == Qt.Checked
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])
        self._spread_values_over_selected_rows(row)
        self.selection_changed.emit()
        self.manual_selection.emit()
        return True

    def set_index_name(self, name):
        """Sets the indexing domain name."""
        self._index_name = name
        self.headerDataChanged.emit(Qt.Horizontal, 0, 0)

    def set_records(self, records, pick_list=None):
        """Overwrites all new indexes."""
        self.beginResetModel()
        self._records = records
        self._selected = pick_list if pick_list is not None else len(records) * [True]
        self._values = [list() for _ in range(len(self._parameter_values))]
        self._rows_shown = 0
        self.selection_changed.emit()
        self.endResetModel()

    def set_picking(self, picking):
        """
        Selects the indexes specified by picking.

        Args:
            picking (Picking): picking
        """
        if picking is None:
            picking = gdx.FixedPicking(len(self._records) * [True])
        pick = picking.pick
        try:
            self._selected = [pick(i) for i in range(len(self._records))]
        except gdx.GdxExportException:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(self._rows_shown - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])
        self._spread_values_over_selected_rows(0)
        self.selection_changed.emit()

    def _spread_values_over_selected_rows(self, first_row):
        """Repopulates the table according to selected indexes."""
        value_start = sum(1 for is_selected in self._selected[:first_row] if is_selected)
        for i, parameter_value in enumerate(self._parameter_values):
            value_index = value_start
            value_length = len(parameter_value)
            values = list(parameter_value.values)
            column = self._values[i]
            for j in range(first_row, self._rows_shown):
                is_selected = self._selected[j]
                if is_selected and value_index < value_length:
                    column[j] = str(values[value_index])
                    value_index += 1
                else:
                    column[j] = None
        top_left = self.index(first_row, 1)
        bottom_right = self.index(self._rows_shown - 1, len(self._values))
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.ToolTipRole])
