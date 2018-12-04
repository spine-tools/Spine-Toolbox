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

from PySide2.QtWidgets import QTableView, QApplication, QAction, QWidget, QVBoxLayout, QPushButton
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
            if not self.paste(self.clipboard_text):
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

    def paste(self, text):
        """Paste data from clipboard."""
        selection = self.selectionModel().selection()
        if len(selection.indexes()) > 1:
            self.paste_on_selection(text)
        else:
            self.paste_normal(text)

    def paste_on_selection(self, text):
        """Paste clipboard data on selection, but not beyond.
        If data is smaller than selection, repeat data to fit selection."""
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

    def paste_normal(self, text):
        """Paste clipboard data, overwritting cells if needed"""
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
        model_index = self.model().index
        for i, row in enumerate(rows):
            line = data[i]
            if not line:
                continue
            for j, column in enumerate(columns):
                value = line[j]
                if not value:
                    continue
                index = model_index(row, column)
                if index.flags() & Qt.ItemIsEditable:
                    indexes.append(index)
                    values.append(value)
        self.model().batch_set_data(indexes, values)
        return True


class FilterWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.model = MinimalTableModel(self)
        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        check_box_delegate = CheckBoxDelegate(self)
        self.view.setItemDelegateForColumn(0, check_box_delegate)
        check_box_delegate.commit_data.connect(self._handle_check_box_commit_data)
        self.button = QPushButton("Ok", self)
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.hide)
        self.hide()

    @Slot("QModelIndex", name="_handle_check_box_commit_data")
    def _handle_check_box_commit_data(self, index):
        data = index.data(Qt.EditRole)
        index.model().setData(index, not data)

    def set_values(self, values):
        self.model.reset_model(values)
        self.view.resizeColumnsToContents()
        width = self.view.horizontalHeader().length()
        # self.setFixedWidth(width + 2)
        height = self.view.verticalHeader().length() + self.button.height()
        parent_height = self.parent().height()
        self.setFixedHeight(min(height, parent_height / 2) + 2)

    def set_section_height(self, height):
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

    @Slot("bool", name="update_auto_filter")
    def update_auto_filter(self, checked=False):
        """Called when the user clicks the Ok button in the auto filter widget.
        Add 'filtered out values' to auto filter."""
        data = self.filter_widget.model._main_data
        values = dict()
        for checked, value, object_class_id_set in data:
            if checked:
                continue
            for object_class_id in object_class_id_set:
                values.setdefault(object_class_id, set()).add(value)
        self.model().set_filtered_out_values(self.filter_column, values)

    def _handle_vertical_section_resized(self, logical_index, old_size, new_size):
        """Pass vertical section size on to the filter widget."""
        if logical_index == 0:
            self.filter_widget.set_section_height(new_size)

    def setModel(self, model):
        """Disconnect sectionPressed signal, only connect it to show_filter_menu slot.
        Otherwise the column is selected when pressing on the header."""
        super().setModel(model)
        self.horizontalHeader().sectionPressed.disconnect()
        self.horizontalHeader().sectionPressed.connect(self.toggle_auto_filter)

    @Slot(int, name="show_filter_menu")
    def toggle_auto_filter(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Show/hide the autofilter widget."""
        if self.filter_widget.isVisible() and self.filter_column == logical_index:
            self.filter_widget.hide()
            return
        self.filter_column = logical_index
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = self.horizontalHeader().sectionViewportPosition(logical_index)
        pos_y = self.horizontalHeader().height()
        values = self.model().auto_filter_values(logical_index)
        self.filter_widget.set_values(values)
        width = self.horizontalHeader().sectionSize(logical_index)
        self.filter_widget.move(pos_x, pos_y)
        self.filter_widget.show()

    @Slot(int, name="show_filter_menu")
    def show_filter_menu(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Show the menu to select a filter."""
        self.filter_column = logical_index
        model = self.model()
        filter_menu = QOkMenu(self)
        self.filter_action_list = list()
        # Add 'All' action
        self.action_all = QAction("All", self)
        self.action_all.setCheckable(True)
        self.action_all.triggered.connect(self.action_all_triggered)
        filter_menu.addAction(self.action_all)
        filter_menu.addSeparator()
        values, filtered_values = model.autofilter_values(self.filter_column)
        # Add filter actions
        self.filter_action_list = list()
        for i, value in enumerate(sorted(list(values))):
            action = QAction(str(value), self)
            action.setCheckable(True)
            action.triggered.connect(self.update_action_all_checked)
            filter_menu.addAction(action)
            self.filter_action_list.append(action)
            if value in filtered_values:
                action.setChecked(True)
            action.trigger()  # Note: this toggles the checked property
        # 'Ok' action
        action_ok = QAction("Ok", self)
        action_ok.triggered.connect(self.update_and_apply_filter)
        filter_menu.addSeparator()
        filter_menu.addAction(action_ok)
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(self.filter_column)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        filter_menu.exec_(QPoint(pos_x, pos_y))

    @Slot("bool", name="update_action_all_checked")
    def update_action_all_checked(self, checked=False):
        """Called when one filter action is triggered.
        In case they are all checked, check to 'All' action too.
        """
        self.action_all.setChecked(all([a.isChecked() for a in self.filter_action_list]))

    @Slot("bool", name="action_all_triggered")
    def action_all_triggered(self, checked=False):
        """Check or uncheck all filter actions."""
        checked = self.action_all.isChecked()
        for action in self.filter_action_list:
            action.setChecked(checked)

    @Slot(name="update_and_apply_filter")
    def update_and_apply_filter(self):
        """Called when user clicks Ok in a filter. Emit `filter_changed` signal."""
        filter_text_list = list()
        for action in self.filter_action_list:
            if not action.isChecked():
                filter_text_list.append(action.text())
        self.filter_changed.emit(self.model(), self.filter_column, filter_text_list)
