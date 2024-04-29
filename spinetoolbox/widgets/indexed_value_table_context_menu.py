######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Context menus for parameter value editor widgets."""
from operator import itemgetter
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QInputDialog, QMenu
from PySide6.QtGui import QAction
from spinetoolbox.plotting import PlottingError, plot_value_editor_table_selection
from spinetoolbox.widgets.plot_widget import PlotWidget, prepare_plot_in_window_menu
from spinetoolbox.widgets.report_plotting_failure import report_plotting_failure

_INSERT_SINGLE_COLUMN_AFTER = "Insert column after"
_INSERT_SINGLE_ROW_AFTER = "Insert row after"
_INSERT_MULTIPLE_COLUMNS_AFTER = "Insert columns after..."
_INSERT_MULTIPLE_ROWS_AFTER = "Insert rows after..."
_INSERT_SINGLE_COLUMN_BEFORE = "Insert column before"
_INSERT_SINGLE_ROW_BEFORE = "Insert row before"
_INSERT_MULTIPLE_COLUMNS_BEFORE = "Insert columns before..."
_INSERT_MULTIPLE_ROWS_BEFORE = "Insert rows before..."
_OPEN_EDITOR = "Edit..."
_PLOT = "Plot..."
_PLOT_IN_WINDOW = "Plot in window"
_REMOVE_COLUMNS = "Remove columns"
_REMOVE_ROWS = "Remove rows"
_TRIM_COLUMNS = "Trim columns"


class ContextMenuBase(QMenu):
    """Context menu base for parameter value editor tables."""

    def __init__(self, table_view, position):
        """
        Args:
            table_view (QTableView): the view where the menu is invoked
            position (QPoint): menu's position on the table view
        """
        super().__init__(table_view)
        self._table_view = table_view
        self._index = self._table_view.indexAt(position)
        self._in_expanse_row = self._table_view.model().is_expanse_row(self._index.row())

    def _add_default_actions(self):
        """Adds default actions to the menu."""
        self.addAction(self._table_view.copy_action)
        self.addAction(self._table_view.paste_action)
        self.addSeparator()
        self.addAction(_INSERT_SINGLE_ROW_BEFORE, self._insert_single_row_before)
        self.addAction(_INSERT_MULTIPLE_ROWS_BEFORE, self._insert_multiple_rows_before)
        self.addSeparator()
        self.addAction(_INSERT_SINGLE_ROW_AFTER, self._insert_single_row_after).setEnabled(not self._in_expanse_row)
        self.addAction(_INSERT_MULTIPLE_ROWS_AFTER, self._insert_multiple_rows_after).setEnabled(
            not self._in_expanse_row
        )
        self.addSeparator()
        self.addAction(_REMOVE_ROWS, self._remove_rows).setEnabled(not self._in_expanse_row)

    def _first_row(self):
        """
        Returns the first selected row.

        Returns:
            int: index to the first row
        """
        return min(s.top() for s in self._table_view.selectionModel().selection())

    @Slot()
    def _insert_multiple_rows_after(self):
        """Prompts for row count, then inserts new rows below the current selection."""
        row_count = self._prompt_row_count()
        if row_count > 0:
            self._table_view.model().insertRows(self._last_row() + 1, row_count)

    @Slot()
    def _insert_multiple_rows_before(self):
        """Prompts for row count, then inserts new rows above the current selection."""
        row_count = self._prompt_row_count()
        if row_count > 0:
            self._table_view.model().insertRows(self._first_row(), row_count)

    @Slot()
    def _insert_single_row_after(self):
        """Inserts a single row below the current selection."""
        self._table_view.model().insertRow(self._last_row() + 1)

    @Slot()
    def _insert_single_row_before(self):
        """Inserts a single row above the current selection."""
        self._table_view.model().insertRow(self._first_row())

    def _last_row(self):
        """
        Returns the last selected row.

        Returns:
            int: index to the last row
        """
        return max(s.bottom() for s in self._table_view.selectionModel().selection())

    def _prompt_row_count(self):
        """
        Prompts for number of rows to insert.

        Returns:
            int: number of rows
        """
        row_count, accepted = QInputDialog.getInt(
            self._table_view, "Enter number of rows", "Number of rows to insert", minValue=1
        )
        return row_count if accepted else 0

    @Slot()
    def _remove_rows(self):
        """Removes selected rows."""
        ranges = _unique_row_ranges(self._table_view.selectionModel().selection())
        for range_ in ranges:
            self._table_view.model().removeRows(range_[0], range_[1] - range_[0] + 1)


class ArrayTableContextMenu(ContextMenuBase):
    """Context menu for array editor tables."""

    def __init__(self, editor, table_view, position):
        """
        Args:
            editor (ArrayEditor): array editor widget
            table_view (QTableView): the view where the menu is invoked
            position (QPoint): menu's position
        """
        super().__init__(table_view, position)
        self._array_editor = editor
        self.addAction(_OPEN_EDITOR, self._show_value_editor)
        self.addSeparator()
        self._add_default_actions()

    @Slot()
    def _show_value_editor(self):
        """Opens the value element editor."""
        self._array_editor.open_value_editor(self._index)


class IndexedValueTableContextMenu(ContextMenuBase):
    """Context menu for time series and time pattern editor tables."""

    def __init__(self, table_view, position):
        """
        Args:
            table_view (QTableView): the view where the menu is invoked
            position (QPoint): menu's position
        """
        super().__init__(table_view, position)
        self._add_default_actions()


class MapTableContextMenu(ContextMenuBase):
    """Context menu for map editor tables."""

    def __init__(self, editor, table_view, position):
        """
        Args:
            editor (MapEditor): map editor widget
            table_view (QTableView): the view where the menu is invoked
            position (QPoint): table cell index
        """
        super().__init__(table_view, position)
        self._map_editor = editor
        in_expanse_column = table_view.model().is_expanse_column(self._index.column())
        self.addAction(_OPEN_EDITOR, self._show_value_editor)
        self.addAction(_PLOT, self._plot)
        self._plot_in_window_menu = self.addMenu(_PLOT_IN_WINDOW)
        self._plot_in_window_menu.triggered.connect(self._plot_in_window)
        prepare_plot_in_window_menu(self._plot_in_window_menu)
        self.addSeparator()
        self._add_default_actions()
        self.addSeparator()
        self.addAction(_INSERT_SINGLE_COLUMN_BEFORE, self._insert_single_column_before)
        self.addAction(_INSERT_MULTIPLE_COLUMNS_BEFORE, self._insert_multiple_columns_before)
        self.addSeparator()
        self.addAction(_INSERT_SINGLE_COLUMN_AFTER, self._insert_single_column_after).setEnabled(not in_expanse_column)
        self.addAction(_INSERT_MULTIPLE_COLUMNS_AFTER, self._insert_multiple_columns_after).setEnabled(
            not in_expanse_column
        )
        self.addSeparator()
        self.addAction(_REMOVE_COLUMNS, self._remove_columns).setEnabled(not in_expanse_column)
        self.addAction(_TRIM_COLUMNS, self._trim_columns)

    def _first_column(self):
        """
        Returns the first selected column.

        Returns:
            int: index to the first column
        """
        return min(s.left() for s in self._table_view.selectionModel().selection())

    @Slot()
    def _insert_multiple_columns_after(self):
        """Prompts for column count, then inserts new columns right from the current selection."""
        column_count = self._prompt_column_count()
        if column_count > 0:
            self._table_view.model().insertColumns(self._last_column() + 1, column_count)

    @Slot()
    def _insert_multiple_columns_before(self):
        """Prompts for column count, then inserts new columns left from the current selection."""
        column_count = self._prompt_column_count()
        if column_count > 0:
            self._table_view.model().insertColumns(self._first_column(), column_count)

    @Slot()
    def _insert_single_column_before(self):
        """Inserts a single column left from the current selection."""
        self._table_view.model().insertColumn(self._first_column())

    @Slot()
    def _insert_single_column_after(self):
        """Inserts a single column right from the current selection."""
        self._table_view.model().insertColumn(self._last_column() + 1)

    def _last_column(self):
        """
        Returns the last selected column.

        Returns:
            int: index to the last column
        """
        return max(s.right() for s in self._table_view.selectionModel().selection())

    def _prompt_column_count(self):
        """
        Prompts for number of column to insert.

        Returns:
            int: number of columns
        """
        column_count, accepted = QInputDialog.getInt(
            self._table_view, "Enter number of columns", "Number of columns to insert", minValue=1
        )
        return column_count if accepted else 0

    @Slot()
    def _remove_columns(self):
        """Removes selected columns"""
        ranges = _unique_column_ranges(self._table_view.selectionModel().selection())
        for range_ in ranges:
            self._table_view.model().removeColumns(range_[0], range_[1] - range_[0] + 1)

    @Slot()
    def _show_value_editor(self):
        """Opens the value element editor."""
        self._map_editor.open_value_editor(self._index)

    @Slot(bool)
    def _plot(self, checked=False):
        """Plots current indexes."""
        selection = self._table_view.selectedIndexes()
        try:
            plot_widget = plot_value_editor_table_selection(self._table_view.model(), selection)
        except PlottingError as error:
            report_plotting_failure(error, self._table_view)
        else:
            plot_widget.use_as_window(self._table_view.window(), "value")
            plot_widget.show()

    @Slot(QAction)
    def _plot_in_window(self, action):
        """Plots the selected cells in an existing window."""
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self._plot()
            return
        selected_indexes = self._table_view.selectedIndexes()
        try:
            plot_value_editor_table_selection(self._table_view.model(), selected_indexes, plot_window)
            plot_window.raise_()
        except PlottingError as error:
            report_plotting_failure(error, self._table_view)

    @Slot()
    def _trim_columns(self):
        """Removes excessive columns from the table."""
        self._table_view.model().trim_columns()


def _unique_row_ranges(selections):
    """
    Merged ranges in given selections to unique ranges.

    Args:
        selections (list of QItemSelectionRange): selected ranges

    Returns:
        list of list: a list of [first_row, last_row] ranges
    """
    return _merge_intervals([[s.top(), s.bottom()] for s in selections])


def _unique_column_ranges(selections):
    """
    Merged ranges in given selections to unique ranges.

    Args:
        selections (list of QItemSelectionRange): selected ranges

    Returns:
        list of list: a list of [first_row, last_row] ranges
    """
    return _merge_intervals([[s.left(), s.right()] for s in selections])


def _merge_intervals(intervals):
    """
    Merges given intervals if they overlap.

    Args:
        intervals (list of list): a list of intervals in the form [first, last]

    Returns:
        list of list: merged intervals in the form [first, last]
    """
    if not intervals:
        return []
    intervals.sort(key=itemgetter(0))
    merged_intervals = [intervals.pop(0)]
    while intervals:
        interval = intervals.pop(0)
        if interval[0] <= merged_intervals[-1][1]:
            merged_intervals[-1][1] = max(merged_intervals[-1][1], interval[1])
        else:
            merged_intervals.append(interval)
    return merged_intervals
