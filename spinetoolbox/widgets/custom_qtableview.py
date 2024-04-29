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
import csv
import ctypes
import io
import locale
from contextlib import contextmanager
from numbers import Number
import re
from operator import methodcaller
from PySide6.QtWidgets import QTableView, QApplication
from PySide6.QtCore import Qt, Slot, QItemSelection, QItemSelectionModel, QPoint
from PySide6.QtGui import QKeySequence, QIcon, QAction
from spinedb_api import (
    DateTime,
    Duration,
    from_database,
    IndexedValue,
    ParameterValueFormatError,
    SpineDBAPIError,
    to_database,
)
from spinedb_api.parameter_value import join_value_and_type, split_value_and_type
from ..helpers import busy_effect


_ = csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))


class CopyPasteTableView(QTableView):
    """Custom QTableView class with copy and paste methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._copy_action = None
        self._paste_action = None
        self._delete_action = QAction("Delete", self)
        self._delete_action.setShortcut(QKeySequence.Delete)
        self.addAction(self._delete_action)
        self._pasted_data_converters = {}
        self._delete_action.triggered.connect(self.delete_content)

    def init_copy_and_paste_actions(self):
        """Initializes copy and paste actions and connects relevant signals."""
        if self._copy_action is not None or self._paste_action is not None:
            raise RuntimeError("Copy and paste actions have already been set.")
        copy_icon = QIcon(":/icons/menu_icons/copy.svg")
        self._copy_action = QAction(copy_icon, "Copy", self)
        self._copy_action.setShortcut(QKeySequence.Copy)
        self.addAction(self._copy_action)
        self._copy_action.triggered.connect(self.copy)
        paste_icon = QIcon(":/icons/menu_icons/paste.svg")
        self._paste_action = QAction(paste_icon, "Paste", self)
        self._paste_action.setShortcut(QKeySequence.Paste)
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
    def copy_action(self):
        return self._copy_action

    @property
    def paste_action(self):
        return self._paste_action

    @Slot(bool)
    def delete_content(self, _=False):
        """Deletes content from editable indexes in current selection."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = [ind for ind in selection.indexes() if ind.flags() & Qt.ItemIsEditable]
        return self.model().batch_set_data(indexes, len(indexes) * [None])

    def can_copy(self):
        return not self.selectionModel().selection().isEmpty()

    @busy_effect
    @Slot(bool)
    def copy(self, _=False):
        """Copies current selection to clipboard in excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        v_header = self.verticalHeader()
        h_header = self.horizontalHeader()
        row_dict = {}
        with system_lc_numeric():
            for rng in sorted(selection, key=lambda x: h_header.visualIndex(x.left())):
                for i in range(rng.top(), rng.bottom() + 1):
                    if v_header.isSectionHidden(i):
                        continue
                    row = row_dict.setdefault(i, [])
                    for j in range(rng.left(), rng.right() + 1):
                        if h_header.isSectionHidden(j):
                            continue
                        data = self.model().index(i, j).data(Qt.ItemDataRole.EditRole)
                        if data is not None:
                            if isinstance(data, bool):
                                str_data = "true" if data else "false"
                            else:
                                if isinstance(data, int):
                                    str_data = str(data)
                                else:
                                    try:
                                        number = float(data)
                                        str_data = locale.str(number)
                                    except ValueError:
                                        str_data = str(data)
                        else:
                            str_data = ""
                        row.append(str_data)
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

    @busy_effect
    @Slot(bool)
    def paste(self, _=False):
        """Paste data from clipboard."""
        selection = self.selectionModel().selection()
        if len(selection.indexes()) > 1:
            return self.paste_on_selection()
        return self.paste_normal()

    @staticmethod
    def _read_pasted_text(text):
        """Parses a tab separated CSV text table.

        Args:
            text (str): a CSV formatted table

        Returns:
            list: a list of rows
        """

        def _process_value(value):
            """Delocalizes value, except when it's one of our 'complex' value types.
            We need this exception because our complex values are json strings, so they have commas,
            and ``locale.delocalize`` might remove those commas.

            We identify our complex values by checking if the word "type" is in them.
            See ``spinedb_api.helpers.join_value_and_type`` for the reason why this works.
            """
            new_value = locale.delocalize(value)
            try:
                float(new_value)
                return new_value
            except ValueError:
                # The new delocalized value is not even a number, so ignore it
                # This prevents comma separated strings to become dot separated strings
                return value

        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter="\t", quotechar="'")
            with system_lc_numeric():
                return [[_process_value(element) for element in row] for row in reader]

    def paste_on_selection(self):
        """Pastes clipboard data on selection, but not beyond.
        If data is smaller than selection, repeat data to fit selection."""
        text = QApplication.clipboard().text()
        if not text:
            return False
        data = self._read_pasted_text(text)
        if not data:
            return False
        selection = self.selectionModel().selection()
        if selection.isEmpty():
            return False
        indexes = list()
        values = list()
        is_row_hidden = self.verticalHeader().isSectionHidden
        rows = [x for r in selection for x in range(r.top(), r.bottom() + 1) if not is_row_hidden(x)]
        is_column_hidden = self.horizontalHeader().isSectionHidden
        columns = [x for r in selection for x in range(r.left(), r.right() + 1) if not is_column_hidden(x)]
        converters = self._converters() if self._pasted_data_converters else {}
        model_index = self.model().index
        for row in rows:
            for column in columns:
                index = model_index(row, column)
                if index.flags() & Qt.ItemIsEditable:
                    i = (row - rows[0]) % len(data)
                    j = (column - columns[0]) % len(data[i])
                    value = data[i][j]
                    indexes.append(index)
                    if converters:
                        convert = converters.get(column)
                        if convert is not None:
                            values.append(convert(value))
                            continue
                    values.append(value)
        self.model().batch_set_data(indexes, values)
        return True

    def paste_normal(self):
        """Pastes clipboard data, overwriting cells if needed."""
        text = QApplication.clipboard().text().strip()
        if not text:
            return False
        data = self._read_pasted_text(text)
        if not data:
            return False
        current = self.currentIndex()
        if not current.isValid():
            return False
        indexes = list()
        values = list()
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
        is_visual_column_hidden = lambda x: h.isSectionHidden(h.logicalIndex(x))
        for _ in range(len(data[0])):
            while is_visual_column_hidden(visual_column):
                visual_column += 1
            columns_append(h.logicalIndex(visual_column))
            visual_column += 1
        # Insert extra rows if needed:
        last_row = max(rows)
        model = self.model()
        row_count = model.rowCount()
        if last_row >= row_count:
            model.insertRows(row_count, last_row - row_count + 1)
        # Insert extra columns if needed:
        last_column = max(columns)
        column_count = model.columnCount()
        if last_column >= column_count:
            model.insertColumns(column_count, last_column - column_count + 1)
        converters = self._converters() if self._pasted_data_converters else {}
        model_index = model.index
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
                if index.flags() & Qt.ItemIsEditable:
                    indexes.append(index)
                    if converters:
                        convert = converters.get(column)
                        if convert is not None:
                            values.append(convert(value))
                            continue
                    values.append(value)
        model.batch_set_data(indexes, values)
        return True

    def set_column_converter_for_pasting(self, header, converter):
        self._pasted_data_converters[header] = converter

    def _converters(self):
        converters = {}
        model = self.model()
        for column in range(model.columnCount()):
            label = model.headerData(column, Qt.Orientation.Horizontal)
            converter = self._pasted_data_converters.get(label)
            if converter is not None:
                converters[column] = converter
        return converters


class AutoFilterCopyPasteTableView(CopyPasteTableView):
    """Custom QTableView class with autofilter functionality."""

    def __init__(self, parent):
        """
        Args:
            parent (QObject)
        """
        super().__init__(parent=parent)
        self._show_filter_menu_action = QAction(self)
        self._show_filter_menu_action.setShortcut(QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_Down.value))
        self._show_filter_menu_action.setShortcutContext(Qt.WidgetShortcut)
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

    @staticmethod
    def _read_pasted_text(text):
        """Reads CSV formatted table."""
        raise NotImplementedError()

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
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if "text/plain" not in data_formats:
            return False
        try:
            pasted_table = self._read_pasted_text(clipboard.text())
        except ValueError:
            return False
        if isinstance(pasted_table, tuple):
            # Always use the first column
            pasted_table = pasted_table[0]
        paste_length = len(pasted_table)
        first_row, last_row, _, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        model = self.model()
        model_row_count = model.rowCount() - 1
        if selection_length == 1:
            # If a single row is selected, we paste everything.
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            pasted_table = pasted_table[0:selection_length]
        indexes_to_set, values_to_set = self._paste_to_values_column(pasted_table, first_row, paste_length)
        model.batch_set_data(indexes_to_set, values_to_set)
        pasted_selection = QItemSelection(model.index(first_row, 1), model.index(first_row + paste_length - 1, 1))
        self.selectionModel().select(pasted_selection, QItemSelectionModel.ClearAndSelect)
        return True

    @staticmethod
    def _read_pasted_text(text):
        """Parses the given CSV table.
        Parsing is locale aware.

        Args:
            text (str): a CSV table containing numbers

        Returns:
            list of float: A list of floats
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter="\t")
            with system_lc_numeric():
                return [locale.atof(row[0]) for row in reader if row]

    def _paste_to_values_column(self, values, first_row, paste_length):
        """Pastes data to the Values column.

        Args:
            values (list): a list of float values to paste
            first_row (int): index of the first row where to paste
            paste_length (int): length of the paste selection (can be different from len(values))

        Returns:
            tuple: A tuple (list(pasted indexes), list(pasted values))
        """
        values_to_set = list()
        indexes_to_set = list()
        create_model_index = self.model().index
        # Always paste to the Values column.
        for row in range(first_row, first_row + paste_length):
            values_to_set.append(values[row - first_row])
            indexes_to_set.append(create_model_index(row, 1))
        return indexes_to_set, values_to_set


class IndexedValueTableView(IndexedParameterValueTableViewBase):
    """A QTableView class with for variable resolution time series and time patterns."""

    @Slot(bool)
    def paste(self, _=False):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if "text/plain" not in data_formats:
            return False
        try:
            pasted_table = self._read_pasted_text(clipboard.text())
        except ValueError:
            return False
        paste_single_column = isinstance(pasted_table, list)
        paste_length = len(pasted_table) if paste_single_column else len(pasted_table[0])
        first_row, last_row, first_column, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        model = self.model()
        model_row_count = model.rowCount() - 1
        if selection_length == 1 or model.is_expanse_row(last_row):
            # If a single row or the expanse row is selected, we paste everything.
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            if paste_single_column:
                pasted_table = pasted_table[0:selection_length]
            else:
                pasted_table = pasted_table[0][0:selection_length], pasted_table[1][0:selection_length]
        if paste_single_column:
            indexes_to_set, values_to_set = self._paste_single_column(
                pasted_table, first_row, first_column, paste_length
            )
            paste_selection = QItemSelection(
                model.index(first_row, first_column), model.index(first_row + paste_length - 1, first_column)
            )
        else:
            indexes_to_set, values_to_set = self._paste_two_columns(
                pasted_table[0], pasted_table[1], first_row, paste_length
            )
            paste_selection = QItemSelection(model.index(first_row, 0), model.index(first_row + paste_length - 1, 1))
        try:
            model.batch_set_data(indexes_to_set, values_to_set)
        except ValueError:
            return False
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
        values_to_set = list()
        indexes_to_set = list()
        create_model_index = self.model().index
        for row in range(first_row, first_row + paste_length):
            i = row - first_row
            values_to_set.append(data_indexes[i])
            indexes_to_set.append(create_model_index(row, 0))
            values_to_set.append(data_values[i])
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
        values_to_set = list()
        indexes_to_set = list()
        create_model_index = self.model().index
        # Always paste numbers to the Values column.
        target_column = first_column if not isinstance(values[0], float) else 1
        for row in range(first_row, first_row + paste_length):
            values_to_set.append(values[row - first_row])
            indexes_to_set.append(create_model_index(row, target_column))
        return indexes_to_set, values_to_set

    @staticmethod
    def _read_pasted_text(text):
        """Parses a given CSV table.

        Args:
            text (str): a CSV table

        Returns:
            tuple: a tuple (data indexes, data values)
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter="\t")
            single_column = list()
            data_indexes = list()
            data_values = list()
            with system_lc_numeric():
                for row in reader:
                    column_count = len(row)
                    if column_count == 1:
                        try:
                            number = locale.atof(row[0])
                            single_column.append(number)
                        except ValueError:
                            single_column.append(row[0])
                    elif column_count > 1:
                        data_indexes.append(row[0])
                        data_values.append(locale.atof(row[1]))
        if single_column:
            if data_indexes:
                # Don't know how to handle a mixture of single and multiple columns.
                raise ValueError()
            return single_column
        return data_indexes, data_values


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
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if "text/plain" not in data_formats:
            return False
        try:
            pasted_table = self._read_pasted_text(clipboard.text())
        except ValueError:
            return False
        if isinstance(pasted_table, tuple):
            # Always use the first column
            pasted_table = pasted_table[0]
        paste_length = len(pasted_table)
        first_row, last_row, _, _ = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
        model = self.model()
        model_row_count = model.rowCount() - 1
        if selection_length == 1:
            # If a single row is selected, we paste everything.
            if model_row_count <= first_row + paste_length:
                model.insertRows(model_row_count, paste_length - (model_row_count - first_row))
        elif paste_length > selection_length:
            # If multiple row are selected, we paste what fits the selection.
            paste_length = selection_length
            pasted_table = pasted_table[0:selection_length]
        values_to_set = list()
        indexes_to_set = list()
        create_model_index = self.model().index
        for row in range(first_row, first_row + paste_length):
            values_to_set.append(pasted_table[row - first_row])
            indexes_to_set.append(create_model_index(row, 0))
        with system_lc_numeric():
            model.batch_set_data(indexes_to_set, values_to_set)
        paste_selection = QItemSelection(model.index(first_row, 0), model.index(first_row + paste_length - 1, 0))
        self.selectionModel().select(paste_selection, QItemSelectionModel.ClearAndSelect)
        return True

    @staticmethod
    def _read_pasted_text(text):
        """Reads the first column of given CSV table.

        Args:
            text (str): a CSV table

        Returns:
            list of str: data column
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter="\t")
            column = [row[0] for row in reader if row]
        return column


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
        out_table = list()
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
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if "text/plain" not in data_formats:
            return False
        pasted_table = self._read_pasted_text(clipboard.text())
        paste_length = len(pasted_table)
        paste_width = len(pasted_table[0]) if pasted_table else 0
        first_row, last_row, first_column, last_column = _range(selection_model.selection())
        selection_length = last_row - first_row + 1
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
    def _read_pasted_text(text):
        """Parses a given CSV table.

        Args:
            text (str): a CSV table

        Returns:
            list of list: a list of table rows
        """
        data = list()
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter="\t")
            with system_lc_numeric():
                for row in reader:
                    data_row = list()
                    for cell in row:
                        try:
                            number = locale.atof(cell)
                            data_row.append(number)
                            continue
                        except ValueError:
                            pass
                        try:
                            # Try parsing Duration before DateTime
                            # because DateTime will happily accept strings like '1h'
                            value = Duration(cell)
                            data_row.append(value)
                            continue
                        except SpineDBAPIError:
                            pass
                        if _could_be_time_stamp(cell):
                            try:
                                value = DateTime(cell)
                                data_row.append(value)
                                continue
                            except SpineDBAPIError:
                                pass
                        try:
                            value = from_database(*split_value_and_type(cell))
                            data_row.append(value)
                            continue
                        except ParameterValueFormatError:
                            pass
                        data_row.append(cell)
                    data.append(data_row)
        return data


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
