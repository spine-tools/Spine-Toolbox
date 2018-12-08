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

from PySide2.QtWidgets import QTableView, QApplication, QAction, QWidget, QVBoxLayout, QPushButton, \
    QStyle
from PySide2.QtCore import Qt, Signal, Slot, QItemSelectionModel, QPoint, QModelIndex
from PySide2.QtGui import QKeySequence, QFont, QFontMetrics
from widgets.custom_delegates import CheckBoxDelegate
from models import MinimalTableModel


class CopyPasteTableView(QTableView):
    """Custom QTableView class with copy-paste functionality.

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
        text = self.clipboard_text
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


class FilterWidget(QWidget):
    """A widget to show the auto filter 'menu'."""
    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.model = MinimalTableModel(self)
        self.model.flags = self.model_flags
        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        check_box_delegate = CheckBoxDelegate(self)
        self.view.setItemDelegateForColumn(0, check_box_delegate)
        check_box_delegate.commit_data.connect(self._handle_check_box_commit_data)
        self.button = QPushButton("Ok", self)
        self.button.setFlat(True)
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.hide)
        self.hide()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

    def model_flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 1:
            return ~Qt.ItemIsEditable
        return Qt.ItemIsEditable

    @Slot("QModelIndex", name="_handle_check_box_commit_data")
    def _handle_check_box_commit_data(self, index):
        """Called when checkbox delegate wants to edit data. Toggle the index's value."""
        data = index.data(Qt.EditRole)
        model_data = self.model._main_data
        row_count = self.model.rowCount()
        if index.row() == 0:
            # Ok row
            value = data in (None, False)
            for row in range(row_count):
                model_data[row][0] = value
            self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(row_count - 1, 0))
        else:
            # Data row
            self.model.setData(index, not data)
            self.set_ok_index_data()

    def set_ok_index_data(self):
        """Set data for ok index based on data from all other indexes."""
        ok_index = self.model.index(0, 0)
        true_count = 0
        for row_data in self.model._main_data[1:]:
            if row_data[0] == True:
                true_count += 1
        if true_count == len(self.model._main_data) - 1:
            self.model.setData(ok_index, True)
        elif true_count == 0:
            self.model.setData(ok_index, False)
        else:
            self.model.setData(ok_index, None)

    def set_values(self, values):
        """Set values to show in the 'menu'. Reset model using those values and update geometry."""
        self.model.reset_model([[None, "All"]] + values)
        self.set_ok_index_data()
        self.view.horizontalHeader().hideSection(2)  # Column 2 holds internal data (cls_id_set)
        self.view.resizeColumnsToContents()
        width = self.view.horizontalHeader().length() + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        self.setFixedWidth(width + 2)
        height = self.view.verticalHeader().length() + self.button.height()
        parent_height = self.parent().height()
        self.setFixedHeight(min(height, parent_height / 2) + 2)

    def set_section_height(self, height):
        """Set vertical header default section size as well as button height."""
        self.view.verticalHeader().setDefaultSectionSize(height)
        self.button.setFixedHeight(height)


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
        self.filter_widget = FilterWidget(self)
        self.filter_widget.button.clicked.connect(self.update_auto_filter)
        self.verticalHeader().sectionResized.connect(self._handle_vertical_section_resized)

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
        self.filter_column = logical_index
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(self.filter_column)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        values = self.model().auto_filter_values(logical_index)
        self.filter_widget.set_values(values)
        width = self.horizontalHeader().sectionSize(logical_index)
        self.filter_widget.move(pos_x, pos_y)
        self.filter_widget.show()

    def _handle_vertical_section_resized(self, logical_index, old_size, new_size):
        """Pass vertical section size on to the filter widget."""
        if logical_index == 0:
            self.filter_widget.set_section_height(new_size)

    @Slot("bool", name="update_auto_filter")
    def update_auto_filter(self, checked=False):
        """Called when the user clicks the Ok button in the auto filter widget.
        Set 'filtered out values' in auto filter model."""
        data = self.filter_widget.model._main_data
        values = dict()
        for checked, value, object_class_id_set in data[1:]:
            if checked:
                continue
            for object_class_id in object_class_id_set:
                values.setdefault(object_class_id, set()).add(value)
        self.model().set_filtered_out_values(self.filter_column, values)
