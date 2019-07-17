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
Class for a custom QTableView that allows copy-paste, and maybe some other feature we may think of.

:author: M. Marin (KTH)
:date:   18.5.2018
"""

from PySide2.QtWidgets import QTableView, QApplication, QAbstractItemView, QMenu, QLineEdit, QWidgetAction
from PySide2.QtCore import Qt, Signal, Slot, QItemSelectionModel, QPoint, QSortFilterProxyModel
from PySide2.QtGui import QKeySequence
from models import TableModel, MinimalTableModel


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
                    str_data = str(data) if data is not None else ""
                    row.append(str_data)
        rows = list()
        for key in sorted(row_dict):
            row = row_dict[key]
            rows.append("\t".join(row))
        content = "\n".join(rows)
        QApplication.clipboard().setText(content)
        return True

    def canPaste(self):  # pylint: disable=no-self-use
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


class AutoFilterMenu(QMenu):
    """A widget to show the auto filter 'menu'.

    Attributes:
        parent (QTableView): the parent widget.
    """

    asc_sort_triggered = Signal(name="asc_sort_triggered")
    desc_sort_triggered = Signal(name="desc_sort_triggered")
    filter_triggered = Signal(name="filter_triggered")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self.row_is_accepted = []
        self.unchecked_values = dict()
        self.model = MinimalTableModel(self)
        self.model.data = self._model_data
        self.model.flags = self._model_flags
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setFilterKeyColumn(1)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.filterAcceptsRow = self._proxy_model_filter_accepts_row
        self.text_filter = QLineEdit(self)
        self.text_filter.setPlaceholderText("Search...")
        self.text_filter.setClearButtonEnabled(True)
        self.view = QTableView(self)
        self.view.setModel(self.proxy_model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        self.view.setMouseTracking(True)
        self.view.entered.connect(self._handle_view_entered)
        self.view.clicked.connect(self._handle_view_clicked)
        self.view.leaveEvent = self._view_leave_event
        self.view.keyPressEvent = self._view_key_press_event
        text_filter_action = QWidgetAction(self)
        text_filter_action.setDefaultWidget(self.text_filter)
        view_action = QWidgetAction(self)
        view_action.setDefaultWidget(self.view)
        self.addAction(text_filter_action)
        self.addAction(view_action)
        ok_action = self.addAction("Ok")
        # pylint: disable=unnecessary-lambda
        self.text_filter.textEdited.connect(lambda x: self.proxy_model.setFilterRegExp(x))
        ok_action.triggered.connect(self._handle_ok_action_triggered)

    def _model_flags(self, index):  # pylint: disable=no-self-use
        """Return no item flags."""
        return ~Qt.ItemIsEditable

    def _model_data(self, index, role=Qt.DisplayRole):
        """Read checked state from first column."""
        if role == Qt.CheckStateRole:
            checked = self.model._main_data[index.row()][0]
            if checked is None:
                return Qt.PartiallyChecked
            if checked is True:
                return Qt.Checked
            return Qt.Unchecked
        return MinimalTableModel.data(self.model, index, role)

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        """Overridden method to always accept first row.
        """
        if source_row == 0:
            return True
        result = QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)
        self.row_is_accepted[source_row] = result
        return result

    @Slot("QModelIndex", name="_handle_view_entered")
    def _handle_view_entered(self, index):
        """Highlight current row."""
        self.view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    def _view_key_press_event(self, event):
        QTableView.keyPressEvent(self.view, event)
        if event.key() == Qt.Key_Space:
            index = self.view.currentIndex()
            self.toggle_checked_state(index)

    @Slot("QModelIndex", name="_handle_view_clicked")
    def _handle_view_clicked(self, index):
        self.toggle_checked_state(index)

    def toggle_checked_state(self, checked_index):
        """Toggle checked state."""
        index = self.proxy_model.index(checked_index.row(), 0)
        checked = index.data(Qt.EditRole)
        row_count = self.proxy_model.rowCount()
        if index.row() == 0:
            # All row
            all_checked = checked in (None, False)
            for row in range(0, row_count):
                self.proxy_model.setData(self.proxy_model.index(row, 0), all_checked)
            self.proxy_model.dataChanged.emit(self.proxy_model.index(0, 1), self.proxy_model.index(row_count - 1, 1))
        else:
            # Data row
            self.proxy_model.setData(index, not checked)
            self.proxy_model.dataChanged.emit(checked_index, checked_index)
            self.set_data_for_all_index()

    def _view_leave_event(self, event):
        """Clear selection."""
        self.view.selectionModel().clearSelection()
        event.accept()

    def set_data_for_all_index(self):
        """Set data for 'all' index based on data from all other indexes."""
        all_index = self.proxy_model.index(0, 0)
        true_count = 0
        row_count = self.proxy_model.rowCount()
        for row in range(1, row_count):
            if self.proxy_model.index(row, 0).data():
                true_count += 1
        if true_count == row_count - 1:
            self.proxy_model.setData(all_index, True)
        elif true_count == 0:
            self.proxy_model.setData(all_index, False)
        else:
            self.proxy_model.setData(all_index, None)
        index = self.proxy_model.index(0, 1)
        self.proxy_model.dataChanged.emit(index, index)

    @Slot("bool", name="_handle_ok_action_triggered")
    def _handle_ok_action_triggered(self, checked=False):
        """Called when user presses Ok."""
        self.unchecked_values = dict()
        for row in range(1, self.model.rowCount()):
            checked, value, object_class_id_set = self.model._main_data[row]
            if not self.row_is_accepted[row] or not checked:
                for object_class_id in object_class_id_set:
                    self.unchecked_values.setdefault(object_class_id, set()).add(value)
        self.filter_triggered.emit()

    def set_values(self, values):
        """Set values to show in the 'menu'."""
        self.row_is_accepted = [True for _ in range(len(values) + 1)]
        self.model.reset_model([[None, "(Select All)", ""]] + values)
        self.set_data_for_all_index()
        self.view.horizontalHeader().hideSection(0)  # Column 0 holds the checked state
        self.view.horizontalHeader().hideSection(2)  # Column 2 holds the (cls_id_set)
        self.proxy_model.setFilterRegExp("")

    def popup(self, pos, width=0, at_action=None):
        super().popup(pos, at_action)
        self.text_filter.clear()
        self.text_filter.setFocus()
        self.view.horizontalHeader().setMinimumSectionSize(0)
        self.view.resizeColumnToContents(1)
        table_width = self.view.horizontalHeader().sectionSize(1) + 2
        width = max(table_width, width)
        self.view.horizontalHeader().setMinimumSectionSize(width)
        parent_section_height = self.parent().verticalHeader().defaultSectionSize()
        self.view.verticalHeader().setDefaultSectionSize(parent_section_height)
        # if self.view.verticalScrollBar().isVisible():
        #    width += qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        self.setFixedWidth(width)


class AutoFilterCopyPasteTableView(CopyPasteTableView):
    """Custom QTableView class with autofilter functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    filter_changed = Signal("QObject", "int", "QStringList", name="filter_changed")

    def __init__(self, parent):
        """Initialize the class."""
        super().__init__(parent=parent)
        self.auto_filter_column = None
        self.auto_filter_menu = AutoFilterMenu(self)
        self.auto_filter_menu.asc_sort_triggered.connect(self.sort_model_ascending)
        self.auto_filter_menu.desc_sort_triggered.connect(self.sort_model_descending)
        self.auto_filter_menu.filter_triggered.connect(self.update_auto_filter)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_Down:
            column = self.currentIndex().column()
            self.toggle_auto_filter(column)
            event.accept()
        else:
            super().keyPressEvent(event)

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
        self.auto_filter_column = logical_index
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(self.auto_filter_column)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        width = self.horizontalHeader().sectionSize(logical_index)
        values = self.model().auto_filter_values(logical_index)
        self.auto_filter_menu.set_values(values)
        self.auto_filter_menu.popup(QPoint(pos_x, pos_y), width)

    @Slot(name="update_auto_filter")
    def update_auto_filter(self):
        """Called when the user selects Ok in the auto filter menu.
        Set 'filtered out values' in auto filter model."""
        self.model().set_filtered_out_values(self.auto_filter_column, self.auto_filter_menu.unchecked_values)

    @Slot(name="sort_model_ascending")
    def sort_model_ascending(self):
        """Called when the user selects sort ascending in the auto filter widget."""
        self.model().sort(self.auto_filter_column, Qt.AscendingOrder)

    @Slot(name="sort_model_descending")
    def sort_model_descending(self):
        """Called when the user selects sort descending in the auto filter widget."""
        self.model().sort(self.auto_filter_column, Qt.DescendingOrder)


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
        index = self.selectedIndexes()[0]
        return self.model.row(index)

    def set_data(self, headers, values):
        self.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
        self.model.set_data(values, headers)
        self.selectRow(0)
        self.selectionModel().blockSignals(False)


class SimpleCopyPasteTableView(QTableView):
    """Custom QTableView class that copies and paste data in response to key press events.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent=None):
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
            for i in range(first.top(), first.bottom() + 1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right() + 1):
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
