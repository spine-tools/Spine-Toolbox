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

"""Custom QTableView classes that support copy-paste and the like."""
from contextlib import contextmanager, suppress
import csv
import ctypes
import io
from itertools import cycle
import locale
from numbers import Number
from operator import methodcaller
import re
from typing import Any, Optional
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, QPoint, Qt, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QApplication, QTableView, QWidget
from spinedb_api import (
    DateTime,
    Duration,
    IndexedValue,
    ParameterValueFormatError,
    SpineDBAPIError,
    from_database,
    to_database,
)
from spinedb_api.parameter_value import FLOAT_VALUE_TYPE, join_value_and_type, split_value_and_type
from ..mvcmodels.empty_row_model import EmptyRowModel
from ..mvcmodels.minimal_table_model import MinimalTableModel
from .paste_excel import EXCEL_CLIPBOARD_MIME_TYPE, clipboard_excel_as_table

_ = csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))


class CopyPasteTableView(QTableView):
    """Custom QTableView class with copy and paste methods."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._copy_action = None
        self._paste_action = None
        self._delete_action = QAction("Delete", self)
        self._delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.addAction(self._delete_action)
        self._delete_action.triggered.connect(self.delete_content)

    def moveCursor(self, cursor_action, modifiers):
        """Inserts an extra row to the table if moving down from the last row and the model supports it."""
        if cursor_action == QAbstractItemView.CursorAction.MoveDown and modifiers == Qt.KeyboardModifier.NoModifier:
            model = self.model()
            if isinstance(model, EmptyRowModel):
                current_index = self.currentIndex()
                row_count = model.rowCount()
                if current_index.row() == row_count - 1:
                    model.insertRows(row_count, 1, QModelIndex())
        return super().moveCursor(cursor_action, modifiers)

    def init_copy_and_paste_actions(self):
        """Initializes copy and paste actions and connects relevant signals."""
        if self._copy_action is not None or self._paste_action is not None:
            raise RuntimeError("Copy and paste actions have already been set.")
        copy_icon = QIcon(":/icons/menu_icons/copy.svg")
        self._copy_action = QAction(copy_icon, "Copy", self)
        self._copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.addAction(self._copy_action)
        self._copy_action.triggered.connect(self.copy)
        paste_icon = QIcon(":/icons/menu_icons/paste.svg")
        self._paste_action = QAction(paste_icon, "Paste", self)
        self._paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.addAction(self._paste_action)
        self._paste_action.triggered.connect(self.paste)

    def set_external_copy_and_paste_actions(self, copy_action, paste_action):
        """Sets the view to use external copy and paste actions.

        Note that this doesn't connect the actions' trigger signals;
        the owner of the actions is responsible for handling them.

        Args:
            copy_action (QAction): copy action
            paste_action (QAction): paste action
        """
        if self._copy_action is not None or self._paste_action is not None:
            raise RuntimeError("Copy and paste actions have already been set.")
        self._copy_action = copy_action
        self._paste_action = paste_action

    @property
    def copy_action(self) -> QAction:
        return self._copy_action

    @property
    def paste_action(self) -> QAction:
        return self._paste_action

    @Slot(bool)
    def delete_content(self, _=False):
        """Deletes content from editable indexes in current selection."""
        if not hasattr(self.model(), "batch_set_data"):
            return False
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = [ind for ind in selection.indexes() if ind.flags() & Qt.ItemIsEditable]
        return self.model().batch_set_data(indexes, len(indexes) * [None])

    def can_copy(self):
        return not self.selectionModel().selection().isEmpty()

    @Slot(bool)
    def copy(self, _=False):
        """Copies current selection to clipboard in Excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        v_header = self.verticalHeader()
        h_header = self.horizontalHeader()
        row_dict = {}
        with system_lc_numeric():
            model = self.model()
            for rng in sorted(selection, key=lambda x: h_header.visualIndex(x.left())):
                for i in range(rng.top(), rng.bottom() + 1):
                    if v_header.isSectionHidden(i):
                        continue
                    row = row_dict.setdefault(i, [])
                    for j in range(rng.left(), rng.right() + 1):
                        if h_header.isSectionHidden(j):
                            continue
                        data = self.model().index(i, j).data(Qt.ItemDataRole.EditRole)
                        row.append(self._convert_copied(i, j, data, model))
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter="\t", quotechar="'")
            for key in sorted(row_dict):
                writer.writerow(row_dict[key])
            QApplication.clipboard().setText(output.getvalue())
        return True

    def can_paste(self):
        return QApplication.clipboard().text() and (
            not self.selectionModel().selection().isEmpty() or self.currentIndex().isValid()
        )

    def _convert_copied(self, row: int, column: int, value: Any, model: MinimalTableModel) -> Optional[str]:
        return value if value is not None else ""

    @Slot(bool)
    def paste(self, _=False):
        """Paste data from clipboard."""
        selection = self.selectionModel().selection()
        if len(selection.indexes()) > 1:
            return self.paste_on_selection()
        return self.paste_normal()

    @staticmethod
    def _get_data_from_clipboard() -> list[list[Any]]:
        """Gets data from clipboard converting it to Python table.

        Returns:
            data table
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data = None
        data_formats = mime_data.formats()
        if EXCEL_CLIPBOARD_MIME_TYPE in data_formats:
            with suppress(Exception):
                data = clipboard_excel_as_table(bytes(mime_data.data(EXCEL_CLIPBOARD_MIME_TYPE)))
        if data is None and "text/plain" in data_formats:
            text = clipboard.text()
            if text:
                with suppress(ValueError):
                    with io.StringIO(text) as input_stream:
                        reader = csv.reader(input_stream, delimiter="\t", quotechar="'")
                        data = list(reader)
        return data

    def paste_on_selection(self):
        """Pastes clipboard data on selection, but not beyond.
        If data is smaller than selection, repeat data to fit selection."""
        data = self._get_data_from_clipboard()
        if not data:
            return False
        selection = self.selectionModel().selection()
        if selection.isEmpty():
            return False
        indexes = []
        values = []
        is_row_hidden = self.verticalHeader().isSectionHidden
        rows = [x for r in selection for x in range(r.top(), r.bottom() + 1) if not is_row_hidden(x)]
        is_column_hidden = self.horizontalHeader().isSectionHidden
        columns = [x for r in selection for x in range(r.left(), r.right() + 1) if not is_column_hidden(x)]
        model = self.model()
        model_index = model.index
        with system_lc_numeric():
            for row in rows:
                for column in columns:
                    index = model_index(row, column)
                    if index.flags() & Qt.ItemFlag.ItemIsEditable:
                        i = (row - rows[0]) % len(data)
                        j = (column - columns[0]) % len(data[i])
                        value = data[i][j]
                        indexes.append(index)
                        values.append(self._convert_pasted(row, column, value, model))
        model.batch_set_data(indexes, values)
        return True

    def paste_normal(self):
        """Pastes clipboard data, overwriting cells if needed."""

        def is_visual_column_hidden(x):
            return h.isSectionHidden(h.logicalIndex(x))

        data = self._get_data_from_clipboard()
        if not data:
            return False
        current = self.currentIndex()
        if not current.isValid():
            return False
        indexes = []
        values = []
        row = current.row()
        rows = []
        rows_append = rows.append
        is_row_hidden = self.verticalHeader().isSectionHidden
        for _ in range(len(data)):
            while is_row_hidden(row):
                row += 1
            rows_append(row)
            row += 1
        column = current.column()
        visual_column = self.horizontalHeader().visualIndex(column)
        columns = []
        columns_append = columns.append
        h = self.horizontalHeader()
        for _ in range(len(data[0])):
            while is_visual_column_hidden(visual_column):
                visual_column += 1
            columns_append(h.logicalIndex(visual_column))
            visual_column += 1
        # Insert extra rows if needed:
        last_row = rows[-1]
        model = self.model()
        row_count = model.rowCount()
        if last_row >= row_count:
            if not model.insertRows(row_count, last_row - row_count + 1):
                rows, data = self._cull_rows(row_count, rows, data)
        # Insert extra columns if needed:
        last_column = max(columns)
        column_count = model.columnCount()
        if last_column >= column_count:
            model.insertColumns(column_count, last_column - column_count + 1)
        model_index = model.index
        with system_lc_numeric():
            for i, row in enumerate(rows):
                try:
                    line = data[i]
                except IndexError:
                    break
                for j, column in enumerate(columns):
                    try:
                        value = line[j]
                    except IndexError:
                        break
                    index = model_index(row, column)
                    if index.flags() & Qt.ItemFlag.ItemIsEditable:
                        indexes.append(index)
                        values.append(self._convert_pasted(row, column, value, model))
        model.begin_paste()
        model.batch_set_data(indexes, values)
        model.end_paste()
        return True

    def _convert_pasted(self, row: int, column: int, str_value: Optional[str], model: MinimalTableModel) -> Any:
        return str_value

    @staticmethod
    def _cull_rows(model_row_count: int, rows: list[int], data: list) -> tuple[list[int], list]:
        culled_rows = []
        culled_data = []
        for i, row in enumerate(rows):
            if row >= model_row_count:
                continue
            culled_rows.append(row)
            culled_data.append(data[i])
        return culled_rows, culled_data


class AutoFilterCopyPasteTableView(CopyPasteTableView):
    """Custom QTableView class with autofilter functionality."""

    def __init__(self, parent: Optional[QWidget]):
        super().__init__(parent=parent)
        self._show_filter_menu_action = QAction(self)
        self._show_filter_menu_action.setShortcut(QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_Down.value))
        self._show_filter_menu_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        self._show_filter_menu_action.triggered.connect(self._trigger_filter_menu)
        self.addAction(self._show_filter_menu_action)
        self.horizontalHeader().sectionClicked.connect(self.show_auto_filter_menu)

    def setModel(self, model):
        """Disconnects the sectionPressed signal which seems to be connected by the super method.
        Otherwise pressing the header just selects the column.

        Args:
            model (QAbstractItemModel)
        """
        super().setModel(model)
        self.horizontalHeader().sectionPressed.disconnect()

    @Slot(bool)
    def _trigger_filter_menu(self, _):
        """Shows current column's auto filter menu."""
        self.show_auto_filter_menu(self.currentIndex().column())

    @Slot(int)
    def show_auto_filter_menu(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Shows/hides the auto filter widget.

        Args:
            logical_index (int): header section index
        """
        menu = self.model().get_auto_filter_menu(logical_index)
        if menu is None:
            return
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(logical_index)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        menu.popup(QPoint(pos_x, pos_y))


class IndexedParameterValueTableViewBase(CopyPasteTableView):
    """Custom QTableView base class with copy and paste methods for indexed parameter values."""

    @Slot(bool)
    def copy(self, _=False):
        """Copies current selection to clipboard in CSV format.

        Returns:
            bool: True if data was copied on the clipboard, False otherwise
        """
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        data_model = self.model()
        selected_indexes = sorted(
            (index for index in selection_model.selectedIndexes() if not data_model.is_expanse_row(index.row())),
            key=lambda i: 2 * i.row() + i.column(),
        )
        row_first = selected_indexes[0].row()
        row_last = selected_indexes[-1].row()
        row_count = row_last - row_first + 1
        data_indexes = row_count * [None]
        data_values = row_count * [None]
        for selected_index in selected_indexes:
            data = data_model.data(selected_index, Qt.ItemDataRole.EditRole)
            row = selected_index.row()
            if selected_index.column() == 0:
                data_indexes[row - row_first] = data
            else:
                data_values[row - row_first] = data
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter="\t")
            with system_lc_numeric():
                if all(stamp is None for stamp in data_indexes):
                    for value in data_values:
                        writer.writerow([locale.str(value) if value is not None else ""])
                elif all(value is None for value in data_values):
                    for index in data_indexes:
                        writer.writerow([index if index is not None else ""])
                else:
                    for index, value in zip(data_indexes, data_values):
                        index = index if index is not None else ""
                        value = locale.str(value) if value is not None else ""
                        writer.writerow([index, value])
            QApplication.clipboard().setText(output.getvalue())
        return True

    @Slot(bool)
    def paste(self, _=False):
        """Pastes data from clipboard to selection."""
        raise NotImplementedError()


class TimeSeriesFixedResolutionTableView(IndexedParameterValueTableViewBase):
    """A QTableView for fixed resolution time series table."""

    @Slot(bool)
    def paste(self, _=True):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        data = self._get_data_from_clipboard()
        if not data:
            return False
        pasted_table = [row[0] for row in data]
        first_row, last_row, _, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        indexes_to_set, values_to_set = self._convert_pasted_data(
            pasted_table, first_row, selection_length if selection_length > 1 else len(pasted_table)
        )
        if not indexes_to_set:
            return False
        paste_length = len(indexes_to_set)
        model = self.model()
        model_row_count = model.rowCount() - 1
        if selection_length == 1:
            # If a single row is selected, we paste everything.
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            indexes_to_set = indexes_to_set[:selection_length]
            values_to_set = values_to_set[:selection_length]
        create_index = model.index
        model.batch_set_data([create_index(*i) for i in indexes_to_set], values_to_set)
        pasted_selection = QItemSelection(model.index(first_row, 1), model.index(first_row + paste_length - 1, 1))
        self.selectionModel().select(pasted_selection, QItemSelectionModel.ClearAndSelect)
        return True

    @staticmethod
    def _convert_pasted_data(values, first_row, paste_length):
        """Converts pasted data.

        Args:
            values (list): a list of float values to paste
            first_row (int): index of the first row where to paste
            paste_length (int): length of the paste selection (can be different from len(values))

        Returns:
            tuple: A tuple (list((row, column)), list(pasted values))
        """
        values_to_set = []
        indexes_to_set = []
        # Always paste to the Values column.
        with system_lc_numeric():
            for row, value in enumerate(cycle(values)):
                if row == paste_length:
                    break
                if isinstance(value, bytes):
                    try:
                        value = from_database(value, FLOAT_VALUE_TYPE)
                    except ParameterValueFormatError:
                        continue
                elif isinstance(value, str):
                    try:
                        value = locale.atof(value)
                    except ValueError:
                        continue
                if isinstance(value, float):
                    values_to_set.append(value)
                    indexes_to_set.append((first_row + len(values_to_set) - 1, 1))
        return indexes_to_set, values_to_set


class IndexedValueTableView(IndexedParameterValueTableViewBase):
    """A QTableView class with for variable resolution time series and time patterns."""

    @Slot(bool)
    def paste(self, _=False):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        data = self._get_data_from_clipboard()
        if not data:
            return False
        paste_single_column = True
        pasted_table = []
        for row in data:
            if len(row) > 1:
                paste_single_column = False
                break
            pasted_table.append(row[0])
        if not paste_single_column:
            index_column = []
            value_column = []
            for row in data:
                index_column.append(row[0])
                try:
                    value_column.append(row[1])
                except IndexError:
                    value_column.append(None)
            pasted_table = [index_column, value_column]
            paste_length = len(index_column)
        else:
            paste_length = len(pasted_table)
        first_row, last_row, first_column, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        model = self.model()
        if selection_length == 1 or model.is_expanse_row(last_row):
            # If a single row or the expanse row is selected, we paste everything.
            model_last_row = model.rowCount() - 1
            if model_last_row <= first_row + paste_length:
                model.insertRows(model_last_row, paste_length - (model_last_row - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            if paste_single_column:
                pasted_table = pasted_table[0:selection_length]
            else:
                pasted_table = pasted_table[0][0:selection_length], pasted_table[1][0:selection_length]
        if paste_single_column:
            indexes_to_set, values_to_set = self._paste_single_column(
                pasted_table, first_row, first_column, selection_length if selection_length > 1 else len(pasted_table)
            )
            paste_selection = QItemSelection(
                model.index(first_row, first_column), model.index(first_row + paste_length - 1, first_column)
            )
        else:
            indexes_to_set, values_to_set = self._paste_two_columns(
                pasted_table[0],
                pasted_table[1],
                first_row,
                selection_length if selection_length > 1 else len(pasted_table[0]),
            )
            paste_selection = QItemSelection(model.index(first_row, 0), model.index(first_row + paste_length - 1, 1))
        model.batch_set_data(indexes_to_set, values_to_set)
        self.selectionModel().select(paste_selection, QItemSelectionModel.ClearAndSelect)
        return True

    def _paste_two_columns(self, data_indexes, data_values, first_row, paste_length):
        """Pastes data indexes and values.

        Args:
            data_indexes (list): a list of data indexes (time stamps/durations)
            data_values (list): a list of data values
            first_row (int): first row index
            paste_length (int): selection length for pasting

        Returns:
            tuple: a tuple (modified model indexes, modified model values)
        """
        values_to_set = []
        indexes_to_set = []
        index_type = self.model().column_type(0)
        create_model_index = self.model().index
        with system_lc_numeric():
            for i, (stamp, value) in enumerate(cycle(zip(data_indexes, data_values))):
                if i == paste_length:
                    break
                try:
                    stamp = index_type(stamp)
                except ValueError:
                    continue
                if isinstance(value, str):
                    try:
                        value = locale.atof(value)
                    except ValueError:
                        continue
                row = first_row + i
                values_to_set.append(stamp)
                indexes_to_set.append(create_model_index(row, 0))
                values_to_set.append(value)
                indexes_to_set.append(create_model_index(row, 1))
        return indexes_to_set, values_to_set

    def _paste_single_column(self, values, first_row, first_column, paste_length):
        """Pastes a single column of data.

        Args:
            values (list): a list of data to paste (data indexes or values)
            first_row (int): first row index
            paste_length (int): selection length for pasting

        Returns:
            tuple: a tuple (modified model indexes, modified model values)
        """
        values_to_set = []
        indexes_to_set = []
        create_model_index = self.model().index
        # Always paste numbers to the Values column.
        target_column = first_column if not isinstance(values[0], float) else 1
        column_type = self.model().column_type(target_column)
        with system_lc_numeric():
            for i, value in enumerate(cycle(values)):
                if i == paste_length:
                    break
                try:
                    value = column_type(value)
                except ValueError:
                    continue
                row = first_row + i
                values_to_set.append(value)
                indexes_to_set.append(create_model_index(row, target_column))
        return indexes_to_set, values_to_set


class ArrayTableView(IndexedParameterValueTableViewBase):
    """Custom QTableView with copy and paste methods for single column tables."""

    @Slot(bool)
    def copy(self, _=False):
        """Copies current selection to clipboard in CSV format.

        Returns:
            bool: True if data was copied on the clipboard, False otherwise
        """
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        model = self.model()
        selected_indexes = [i for i in selection_model.selectedIndexes() if not model.is_expanse_row(i.row())]
        selected_indexes.sort(key=methodcaller("row"))
        first_column = selected_indexes[0].column()
        if any(index.column() != first_column for index in selected_indexes):
            values = {}
            for index in selected_indexes:
                row = index.row()
                row_values = values.setdefault(row, {})
                row_values["x" if index.column() == 0 else "y"] = index.data(Qt.ItemDataRole.EditRole)
            with system_lc_numeric():
                with io.StringIO() as output:
                    writer = csv.writer(output, delimiter="\t")
                    for row_values in values.values():
                        x = row_values.get("x", "")
                        y = row_values.get("y", "")
                        y = locale.str(y) if isinstance(y, Number) else y
                        writer.writerow([x, y])
                    QApplication.clipboard().setText(output.getvalue())
        else:
            with system_lc_numeric():
                with io.StringIO() as output:
                    writer = csv.writer(output, delimiter="\t")
                    for index in selected_indexes:
                        y = index.data(Qt.ItemDataRole.EditRole)
                        writer.writerow([locale.str(y) if isinstance(y, Number) else y])
                    QApplication.clipboard().setText(output.getvalue())
        return True

    @Slot(bool)
    def paste(self, _=False):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        data = self._get_data_from_clipboard()
        pasted_table = [row[0] for row in data]
        first_row, last_row, _, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        model = self.model()
        indexes_to_set, values_to_set = self._convert_pasted_data(
            pasted_table, first_row, selection_length if selection_length > 1 else len(pasted_table)
        )
        paste_length = len(values_to_set)
        if paste_length == 0:
            return False
        model_row_count = model.rowCount() - 1
        if selection_length == 1:
            # If a single row is selected, we paste everything.
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            values_to_set = values_to_set[:selection_length]
            indexes_to_set = indexes_to_set[:selection_length]
        create_model_index = self.model().index
        model.batch_set_data([create_model_index(*i) for i in indexes_to_set], values_to_set)
        paste_selection = QItemSelection(model.index(first_row, 1), model.index(first_row + paste_length - 1, 1))
        self.selectionModel().select(paste_selection, QItemSelectionModel.ClearAndSelect)
        return True

    def _convert_pasted_data(self, values, first_row, paste_length):
        """Converts pasted data.

        Args:
            values (list): a list of float values to paste
            first_row (int): index of the first row where to paste
            paste_length (int): length of the paste selection (can be different from len(values))

        Returns:
            tuple: A tuple (list((row, column)), list(pasted values))
        """
        values_to_set = []
        indexes_to_set = []
        model = self.model()
        with system_lc_numeric():
            for row, value in enumerate(cycle(values)):
                if row == paste_length:
                    break
                if isinstance(value, bytes):
                    try:
                        value = from_database(value, FLOAT_VALUE_TYPE)
                    except ParameterValueFormatError:
                        continue
                elif isinstance(value, str) and model.data_type == float:
                    try:
                        value = locale.atof(value)
                    except ValueError:
                        continue
                if isinstance(value, model.data_type):
                    values_to_set.append(value)
                    indexes_to_set.append((first_row + len(values_to_set) - 1, 1))
        return indexes_to_set, values_to_set


class MapTableView(CopyPasteTableView):
    """Custom QTableView with copy and paste methods for map tables."""

    @Slot(bool)
    def copy(self, _=False):
        """Copies current selection to clipboard in Excel compatible CSV format.

        Returns:
            bool: True if data was copied on the clipboard, False otherwise
        """
        selection = self.selectionModel().selection()
        if not selection:
            return False
        top, bottom, left, right = _range(selection)
        model = self.model()
        if model.is_expanse_column(right):
            right -= 1
        if model.is_expanse_row(bottom):
            bottom -= 1
        if left > right or top > bottom:
            QApplication.clipboard().setText("")
            return True
        out_table = []
        with system_lc_numeric():
            for y in range(top, bottom + 1):
                row = (right - left + 1) * [None]
                for x in range(left, right + 1):
                    index = model.index(y, x)
                    if not selection.contains(index):
                        continue
                    data = index.data(Qt.ItemDataRole.EditRole)
                    try:
                        number = float(data)
                        str_data = locale.str(number)
                    except ValueError:
                        str_data = str(data)
                    except TypeError:
                        if isinstance(data, IndexedValue):
                            str_data = join_value_and_type(*to_database(data))
                        else:
                            str_data = str(data)
                    row[x - left] = str_data
                out_table.append(row)
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter="\t", quotechar="'")
            writer.writerows(out_table)
            QApplication.clipboard().setText(output.getvalue())
        return True

    @Slot(bool)
    def delete_content(self, _=False):
        """Deletes content in current selection."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        self.model().clear(selection.indexes())

    @Slot(bool)
    def paste(self, _=False):
        """Pastes data from clipboard.

        Returns:
            bool: True if data was pasted successfully, False otherwise
        """
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        data = self._get_data_from_clipboard()
        if not data:
            return False
        first_row, last_row, first_column, last_column = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        pasted_table = self._convert_pasted_data(data, selection_length if selection_length > 1 else len(data))
        if not pasted_table:
            return False
        paste_length = len(pasted_table)
        paste_width = len(pasted_table[0])
        selection_width = last_column - first_column + 1
        model = self.model()
        if (
            (selection_length == 1 and selection_width == 1)
            or model.is_expanse_row(last_row)
            or model.is_expanse_column(last_column)
        ):
            # If a single cell or expanse is selected, we paste everything.
            model_row_count = model.rowCount()
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - 1 - first_row))
            model_column_count = model.columnCount()
            if model_column_count <= first_column + paste_width:
                model.insertColumns(model_column_count, paste_width - (model_column_count - 1 - first_column))
            capped_length = paste_length
            capped_width = paste_width
        else:
            capped_length = min(paste_length, selection_length)
            capped_width = min(paste_length, selection_width)
        top_left = model.index(first_row, first_column)
        bottom_right = model.index(first_row + capped_length - 1, first_column + capped_width - 1)
        model.set_box(top_left, bottom_right, pasted_table)
        selection = QItemSelection(top_left, bottom_right)
        self.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)
        return True

    @staticmethod
    def _convert_pasted_data(data, length):
        """Convert pasted data to what the model expects.

        Args:
            data (list of list): pasted data
            length (int): paste length

        Returns:
            list of list: converted data
        """
        pasted_table = []
        with system_lc_numeric():
            for i, row in enumerate(cycle(data)):
                if i == length:
                    break
                table_row = []
                for cell in row:
                    if isinstance(cell, bytes):
                        cell = str(cell, encoding="utf-8")
                    elif isinstance(cell, (float, bool)):
                        table_row.append(cell)
                        continue
                    try:
                        table_row.append(locale.atof(cell))
                        continue
                    except ValueError:
                        pass
                    try:
                        # Try parsing Duration before DateTime
                        # because DateTime will happily accept strings like '1h'
                        value = Duration(cell)
                        table_row.append(value)
                        continue
                    except SpineDBAPIError:
                        pass
                    if _could_be_time_stamp(cell):
                        try:
                            value = DateTime(cell)
                            table_row.append(value)
                            continue
                        except SpineDBAPIError:
                            pass
                    try:
                        value = from_database(*split_value_and_type(cell))
                        table_row.append(value)
                        continue
                    except ParameterValueFormatError:
                        pass
                    table_row.append(cell)
                pasted_table.append(table_row)
        return pasted_table


def _range(selection):
    """Returns the top left and bottom right corners of selection.

    Args:
        selection (QItemSelection): a list of selected QItemSelection objects

    Returns:
        tuple of ints: a tuple (top row, bottom row, left column, right column)
    """
    left = selection[0].left()
    top = selection[0].top()
    right = selection[0].right()
    bottom = selection[0].bottom()
    for i in range(1, len(selection)):
        range_ = selection[i]
        left = min(left, range_.left())
        top = min(top, range_.top())
        right = max(right, range_.right())
        bottom = max(bottom, range_.bottom())
    return top, bottom, left, right


_NOT_TIME_STAMP = re.compile(r"^[a-zA-z][0-9]")


def _could_be_time_stamp(s):
    """Evaluates if given string could be a time stamp.

    This is to deal with special cases that are not intended as time stamps but
    could end up as one by the very greedy ``DateTime`` constructor.

    Args:
        s (str): string to evaluate

    Returns:
        bool: True if s could be a time stamp, False otherwise
    """
    return _NOT_TIME_STAMP.match(s) is None


@contextmanager
def system_lc_numeric():
    toolbox_lc_numeric = locale.getlocale(locale.LC_NUMERIC)
    locale.setlocale(locale.LC_NUMERIC, "")
    try:
        yield None
    finally:
        locale.setlocale(locale.LC_NUMERIC, toolbox_lc_numeric)
