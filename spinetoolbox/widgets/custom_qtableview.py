######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Class for a custom QTableView that allows copy-paste, and maybe some other feature we may think of.

:author: M. Marin (KTH)
:date:   18.5.2018
"""

import time
import logging
from PySide2.QtWidgets import QTableView, QApplication, QAbstractItemView
from PySide2.QtCore import Qt, Signal, Slot, QItemSelectionModel
from PySide2.QtGui import QKeySequence, QFont, QFontMetrics
from widgets.custom_delegates import CheckBoxDelegate
from widgets.custom_qwidgets import AutoFilterWidget
from models import TableModel


class CopyPasteTableView(QTableView):
    """Custom QTableView class with copy and paste methods.

    Attributes:
        parent (QWidget): The parent of this view
    """
    def __init__(self, parent):
        """Initialize the class."""
        super().__init__(parent=parent)
        QApplication.clipboard().dataChanged.connect(self.clipboard_data_changed)
        self.clipboard_text = QApplication.clipboard().text()

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = QApplication.clipboard().text()

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            if not self.copy():
                super().keyPressEvent(event)
        elif event.matches(QKeySequence.Paste):
            if not self.paste():
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def copy(self):
        """Copy current selection to clipboard in excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        # Take only the first selection in case of multiple selection.
        first = selection.first()
        rows = list()
        v_header = self.verticalHeader()
        h_header = self.horizontalHeader()
        for i in range(first.top(), first.bottom()+1):
            if v_header.isSectionHidden(i):
                continue
            row = list()
            for j in range(first.left(), first.right()+1):
                if h_header.isSectionHidden(j):
                    continue
                data = self.model().index(i, j).data(Qt.DisplayRole)
                str_data = str(data) if data is not None else ""
                row.append(str_data)
            rows.append("\t".join(row))
        content = "\n".join(rows)
        QApplication.clipboard().setText(content)
        return True

    def canPaste(self):
        return True

    def paste(self):
        """Paste data from clipboard."""
        selection = self.selectionModel().selection()
        if len(selection.indexes()) > 1:
            self.paste_on_selection()
        else:
            self.paste_normal()

    def paste_on_selection(self):
        """Paste clipboard data on selection, but not beyond.
        If data is smaller than selection, repeat data to fit selection."""
        text = self.clipboard_text
        if not text:
            return False
        data = [line.split('\t') for line in text.split('\n')]
        if not data:
            return False
        selection = self.selectionModel().selection()
        if selection.isEmpty():
            return False
        first = selection.first()
        indexes = list()
        values = list()
        is_row_hidden = self.verticalHeader().isSectionHidden
        rows = [x for x in range(first.top(), first.bottom() + 1) if not is_row_hidden(x)]
        is_column_hidden = self.horizontalHeader().isSectionHidden
        columns = [x for x in range(first.left(), first.right() + 1) if not is_column_hidden(x)]
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
        """Paste clipboard data, overwritting cells if needed"""
        text = self.clipboard_text.strip()
        if not text:
            return False
        data = [line.split('\t') for line in text.split('\n')]
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
        for x in range(len(data)):
            while is_row_hidden(row):
                row += 1
            rows_append(row)
            row += 1
        column = current.column()
        columns = []
        columns_append = columns.append
        is_column_hidden = self.horizontalHeader().isSectionHidden
        for x in range(len(data[0])):
            while is_column_hidden(column):
                column += 1
            columns_append(column)
            column += 1
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


class AutoFilterCopyPasteTableView(CopyPasteTableView):
    """Custom QTableView class with autofilter functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    filter_changed = Signal("QObject", "int", "QStringList", name="filter_changed")

    def __init__(self, parent):
        """Initialize the class."""
        super().__init__(parent=parent)
        self.filter_action_list = list()
        self.action_all = None
        self.filter_text = None
        self.filter_column = None
        self.auto_filter_widget = AutoFilterWidget(self)
        self.auto_filter_widget.data_committed.connect(self.update_auto_filter)

    def setModel(self, model):
        """Disconnect sectionPressed signal, only connect it to show_filter_menu slot.
        Otherwise the column is selected when pressing on the header."""
        super().setModel(model)
        self.horizontalHeader().sectionPressed.disconnect()
        self.horizontalHeader().sectionClicked.connect(self.toggle_auto_filter)

    @Slot(int, name="show_filter_menu")
    def toggle_auto_filter(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Show/hide the auto filter widget."""
        tic = time.clock()
        self.filter_column = logical_index
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(self.filter_column)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        width = self.horizontalHeader().sectionSize(logical_index)
        values = self.model().auto_filter_values(logical_index)
        self.auto_filter_widget.set_values(values)
        self.auto_filter_widget.move(pos_x, pos_y)
        self.auto_filter_widget.show(min_width=width)
        toc = time.clock()
        # logging.debug("Filter populated in {} seconds".format(toc - tic))

    @Slot(name="update_auto_filter")
    def update_auto_filter(self):
        """Called when the user clicks the Ok button in the auto filter widget.
        Set 'filtered out values' in auto filter model."""
        self.model().set_filtered_out_values(self.filter_column, self.auto_filter_widget.checked_values)


class FrozenTableView(QTableView):
    def __init__(self, parent=None):
        super(FrozenTableView, self).__init__(parent)
        self.model = TableModel()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(self.model)
        self.is_updating = False

    def clear(self):
        self.model.set_data([], [])

    def get_selected_row(self):
        if self.model.columnCount() == 0:
            return ()
        if self.model.rowCount() == 0:
            return tuple(None for _ in range(self.model.columnCount()))
        index = self.selectedIndexes()
        if not index:
            return tuple(None for _ in range(self.model.columnCount()))
        else:
            index = self.selectedIndexes()[0]
            return self.model.row(index)

    def set_data(self, headers, values):
        self.selectionModel().blockSignals(True) #prevent selectionChanged signal when updating
        self.model.set_data(values, headers)
        self.selectRow(0)
        self.selectionModel().blockSignals(False)


class SimpleCopyPasteTableView(QTableView):
    """Custom QTableView class that copies and paste data in response to key press events.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent = None):
        """Initialize the class."""
        super().__init__(parent)
        # self.editing = False
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = self.clipboard.text()

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            selection = self.selectionModel().selection()
            if not selection:
                super().keyPressEvent(event)
                return
            # Take only the first selection in case of multiple selection.
            first = selection.first()
            content = ""
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            for i in range(first.top(), first.bottom()+1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right()+1):
                    if h_header.isSectionHidden(j):
                        continue
                    row.append(str(self.model().index(i, j).data(Qt.DisplayRole)))
                content += "\t".join(row)
                content += "\n"
            self.clipboard.setText(content)
        elif event.matches(QKeySequence.Paste):
            if not self.clipboard_text:
                super().keyPressEvent(event)
                return
            top_left_index = self.currentIndex()
            if not top_left_index.isValid():
                super().keyPressEvent(event)
                return
            data = [line.split('\t') for line in self.clipboard_text.split('\n')[0:-1]]
            self.selectionModel().select(top_left_index, QItemSelectionModel.Select)
            self.model().paste_data(top_left_index, data)
        else:
            super().keyPressEvent(event)
