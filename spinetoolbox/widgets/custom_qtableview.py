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
Custom QTableView classes that support copy-paste and the like.

:author: M. Marin (KTH)
:date:   18.5.2018
"""

import csv
import io
import locale
import numpy as np
from PySide2.QtWidgets import QTableView, QApplication
from PySide2.QtCore import Qt, Slot, QItemSelectionModel, QPoint
from PySide2.QtGui import QKeySequence
from ..widgets.pivot_table_header_view import PivotTableHeaderView
from ..helpers import busy_effect


class CopyPasteTableView(QTableView):
    """Custom QTableView class with copy and paste methods."""

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            if not self.copy():
                super().keyPressEvent(event)
        elif event.matches(QKeySequence.Paste):
            if not self.paste():
                super().keyPressEvent(event)
        elif event.matches(QKeySequence.Delete):
            if not self.delete_content():
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def delete_content(self):
        """Delete content from editable indexes in current selection."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = [ind for ind in selection.indexes() if ind.flags() & Qt.ItemIsEditable]
        return self.model().batch_set_data(indexes, [None for _ in indexes])

    @busy_effect
    def copy(self):
        """Copy current selection to clipboard in excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        v_header = self.verticalHeader()
        h_header = self.horizontalHeader()
        row_dict = {}
        for rng in sorted(selection, key=lambda x: h_header.visualIndex(x.left())):
            for i in range(rng.top(), rng.bottom() + 1):
                if v_header.isSectionHidden(i):
                    continue
                row = row_dict.setdefault(i, [])
                for j in range(rng.left(), rng.right() + 1):
                    if h_header.isSectionHidden(j):
                        continue
                    data = self.model().index(i, j).data(Qt.EditRole)
                    if data is not None:
                        try:
                            number = float(data)
                            str_data = locale.str(number)
                        except ValueError:
                            str_data = str(data)
                    else:
                        str_data = ""
                    row.append(str_data)
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter='\t')
            for key in sorted(row_dict):
                writer.writerow(row_dict[key])
            QApplication.clipboard().setText(output.getvalue())
        return True

    def canPaste(self):  # pylint: disable=no-self-use
        return True

    @busy_effect
    def paste(self):
        """Paste data from clipboard."""
        selection = self.selectionModel().selection()
        if len(selection.indexes()) > 1:
            return self.paste_on_selection()
        return self.paste_normal()

    @staticmethod
    def _read_pasted_text(text):
        """
        Parses a tab separated CSV text table.

        Args:
            text (str): a CSV formatted table
        Returns:
            a list of rows
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter='\t')
            rows = list()
            for row in reader:
                rows.append([locale.delocalize(element) for element in row])
            return rows

    def paste_on_selection(self):
        """Paste clipboard data on selection, but not beyond.
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
        model_index = self.model().index
        for row in rows:
            for column in columns:
                index = model_index(row, column)
                if index.flags() & Qt.ItemIsEditable:
                    i = (row - rows[0]) % len(data)
                    j = (column - columns[0]) % len(data[i])
                    value = data[i][j]
                    indexes.append(index)
                    values.append(value)
        self.model().batch_set_data(indexes, values)
        return True

    def paste_normal(self):
        """Paste clipboard data, overwriting cells if needed"""
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
        row_count = self.model().rowCount()
        if last_row >= row_count:
            self.model().insertRows(row_count, last_row - row_count + 1)
        # Insert extra columns if needed:
        last_column = max(columns)
        column_count = self.model().columnCount()
        if last_column >= column_count:
            self.model().insertColumns(column_count, last_column - column_count + 1)
        model_index = self.model().index
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
                    values.append(value)
        self.model().batch_set_data(indexes, values)
        return True


class PivotTableView(CopyPasteTableView):
    """Custom QTableView class with pivot capabilities.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent=None):
        """Initialize the class."""
        super().__init__(parent)
        h_header = PivotTableHeaderView(Qt.Horizontal, "columns", self)
        v_header = PivotTableHeaderView(Qt.Vertical, "rows", self)
        self.setHorizontalHeader(h_header)
        self.setVerticalHeader(v_header)
        h_header.setContextMenuPolicy(Qt.CustomContextMenu)


class AutoFilterCopyPasteTableView(CopyPasteTableView):
    """Custom QTableView class with autofilter functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initializes the view.

        Args:
            parent (QObject)
        """
        super().__init__(parent=parent)
        self.horizontalHeader().sectionClicked.connect(self.show_auto_filter_menu)

    def keyPressEvent(self, event):
        """Shows the autofilter menu if the user presses Alt + Down.

        Args:
            event (QEvent)
        """
        if event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_Down:
            column = self.currentIndex().column()
            self.show_auto_filter_menu(column)
            event.accept()
        else:
            super().keyPressEvent(event)

    def setModel(self, model):
        """Disconnects the sectionPressed signal which seems to be connected by the super method.
        Otherwise pressing the header just selects the column.

        Args:
            model (QAbstractItemModel)
        """
        super().setModel(model)
        self.horizontalHeader().sectionPressed.disconnect()

    @Slot(int)
    def show_auto_filter_menu(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Shows/hides the auto filter widget.

        Args:
            logical_index (int)
        """
        menu = self.model().get_auto_filter_menu(logical_index)
        if menu is None:
            return
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(logical_index)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        menu.popup(QPoint(pos_x, pos_y))


class IndexedParameterValueTableViewBase(CopyPasteTableView):
    """
    Custom QTableView base class with copy and paste methods for indexed parameter values.
    """

    def copy(self):
        """Copy current selection to clipboard in CSV format."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        selected_indexes = sorted(selection_model.selectedIndexes(), key=lambda index: 2 * index.row() + index.column())
        row_first = selected_indexes[0].row()
        row_last = selected_indexes[-1].row()
        row_count = row_last - row_first + 1
        data_indexes = row_count * [None]
        data_values = row_count * [None]
        data_model = self.model()
        for selected_index in selected_indexes:
            data = data_model.data(selected_index)
            row = selected_index.row()
            if selected_index.column() == 0:
                data_indexes[row - row_first] = data
            else:
                data_values[row - row_first] = data
        with io.StringIO() as output:
            writer = csv.writer(output, delimiter='\t')
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

    def paste(self):
        """Pastes data from clipboard to selection."""
        raise NotImplementedError()

    @staticmethod
    def _range(indexes):
        """
        Returns the top left and bottom right corners of selected model indexes.

        Args:
            indexes (list): a list of selected QModelIndex objects
        Returns:
            a tuple (top row, bottom row, left column, right column)
        """
        rows = np.empty(len(indexes), dtype=int)
        columns = np.empty(len(indexes), dtype=int)
        for i, index in enumerate(indexes):
            rows[i] = index.row()
            columns[i] = index.column()
        return np.amin(rows), np.amax(rows), np.amin(columns), np.amax(columns)

    def _select_pasted(self, indexes):
        """Selects the given model indexes."""
        selection_model = self.selectionModel()
        selection_model.clear()
        for index in indexes:
            selection_model.select(index, QItemSelectionModel.Select)


class TimeSeriesFixedResolutionTableView(IndexedParameterValueTableViewBase):
    """A QTableView for fixed resolution time series table."""

    def paste(self):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if not 'text/plain' in data_formats:
            return False
        try:
            pasted_table = self._read_pasted_text(QApplication.clipboard().text())
        except ValueError:
            return False
        selected_indexes = selection_model.selectedIndexes()
        if isinstance(pasted_table, tuple):
            # Always use the first column
            pasted_table = pasted_table[0]
        paste_length = len(pasted_table)
        first_row, last_row, _, _ = self._range(selected_indexes)
        selection_length = last_row - first_row + 1
        model = self.model()
        model_row_count = model.rowCount()
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
        self._select_pasted(indexes_to_set)

    @staticmethod
    def _read_pasted_text(text):
        """
        Parses the given CSV table.

        Parsing is locale aware.

        Args:
            text (str): a CSV table containing numbers
        Returns:
            A list of floats
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter='\t')
            single_column = list()
            for row in reader:
                number = locale.atof(row[0])
                single_column.append(number)
        return single_column

    def _paste_to_values_column(self, values, first_row, paste_length):
        """
        Pastes data to the Values column.

        Args:
            values (list): a list of float values to paste
            first_row (int): index of the first row where to paste
            paste_length (int): length of the paste selection (can be different from len(values))
        Returns:
            A tuple (list(pasted indexes), list(pasted values))
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

    def paste(self):
        """Pastes data from clipboard."""
        selection_model = self.selectionModel()
        if not selection_model.hasSelection():
            return False
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        data_formats = mime_data.formats()
        if not 'text/plain' in data_formats:
            return False
        try:
            pasted_table = self._read_pasted_text(QApplication.clipboard().text())
        except ValueError:
            return False
        selected_indexes = selection_model.selectedIndexes()
        paste_single_column = isinstance(pasted_table, list)
        paste_length = len(pasted_table) if paste_single_column else len(pasted_table[0])
        first_row, last_row, first_column, _ = self._range(selected_indexes)
        selection_length = last_row - first_row + 1
        model = self.model()
        model_row_count = model.rowCount()
        if selection_length == 1:
            # If a single row is selected, we paste everything.
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
        else:
            indexes_to_set, values_to_set = self._paste_two_columns(
                pasted_table[0], pasted_table[1], first_row, paste_length
            )
        model.batch_set_data(indexes_to_set, values_to_set)
        self._select_pasted(indexes_to_set)

    def _paste_two_columns(self, data_indexes, data_values, first_row, paste_length):
        """
        Pastes data indexes and values.

        Args:
            data_indexes (list): a list of data indexes (time stamps/durations)
            data_values (list): a list of data values
            first_row (int): first row index
            paste_length (int): selection length for pasting
        Returns:
            a tuple (modified model indexes, modified model values)
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
        """
        Pastes a single column of data

        Args:
            values (list): a list of data to paste (data indexes or values)
            first_row (int): first row index
            paste_length (int): selection length for pasting
        Returns:
            a tuple (modified model indexes, modified model values)
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
        """
        Parses a given CSV table

        Args:
            text (str): a CSV table
        Returns:
            a tuple (data indexes, data values)
        """
        with io.StringIO(text) as input_stream:
            reader = csv.reader(input_stream, delimiter='\t')
            single_column = list()
            data_indexes = list()
            data_values = list()
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
