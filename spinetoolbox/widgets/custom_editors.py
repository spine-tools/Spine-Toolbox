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
Custom editors for model/view programming.


:author: M. Marin (KTH)
:date:   2.9.2018
"""
from PySide2.QtCore import Qt, Slot, Signal, QItemSelectionModel, QSortFilterProxyModel, QRegExp, \
    QEvent, QSize
from PySide2.QtWidgets import QComboBox, QLineEdit, QWidget, QVBoxLayout, QTableView, QSplitter, \
    QApplication
from PySide2.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QFocusEvent


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, data):
        if data is not None:
            self.setText(str(data))
        if type(data) is int:
            self.setValidator(QIntValidator(self))

    def data(self):
        return self.text()


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, current_text, items):
        self.addItems(items)
        if current_text and current_text in items:
            self.setCurrentText(current_text)
        else:
            self.setCurrentIndex(-1)
        self.activated.connect(lambda: self.data_committed.emit())
        self.showPopup()

    def data(self):
        return self.currentText()


class SearchBarEditor(QWidget):
    """A widget that implements a Google-like search bar."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._base_size = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.line_edit = QLineEdit(self)
        self.line_edit.setFocusPolicy(Qt.NoFocus)
        self.line_edit.keyPressEvent = self._line_edit_key_press_event
        self.old_text = None
        self.model = QStandardItemModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.view = QTableView(self)
        self.view.setModel(self.proxy_model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        self.view.setFocusPolicy(Qt.NoFocus)
        self.view.setMouseTracking(True)
        self.view.mouseMoveEvent = self._view_mouse_move_event
        layout.addWidget(self.line_edit)
        layout.addWidget(self.view)
        self.connect_signals()

    def connect_signals(self):
        self.line_edit.textEdited.connect(self._handle_line_edit_text_edited)
        self.view.clicked.connect(self._handle_view_clicked)

    def keyPressEvent(self, event):
        """Call event handler on line edit.
        """
        self._line_edit_key_press_event(event)

    def focusInEvent(self, event):
        """Call event handler on line edit.
        """
        self.line_edit.focusInEvent(event)
        # self.line_edit.selectAll()

    def focusOutEvent(self, event):
        """Call event handler on line edit.
        """
        self.line_edit.focusOutEvent(event)

    def _line_edit_key_press_event(self, event):
        """Navigate through view when pressing up and down arrows.
        """
        if event.key() == Qt.Key_Down:
            next_row = self.view.currentIndex().row() + 1
            next_index = self.proxy_model.index(next_row, 0)
            self.view.setCurrentIndex(next_index)
            if next_row == 0:
                self.old_text = self.line_edit.text()
            if not next_index.isValid():
                self.line_edit.setText(self.old_text)
            else:
                self.line_edit.setText(next_index.data())
        elif event.key() == Qt.Key_Up:
            next_row = self.view.currentIndex().row() - 1
            if next_row == -2:
                next_row = self.proxy_model.rowCount() - 1
            next_index = self.proxy_model.index(next_row, 0)
            self.view.setCurrentIndex(next_index)
            if next_row == self.proxy_model.rowCount() - 1:
                self.old_text = self.line_edit.text()
            if not next_index.isValid():
                self.line_edit.setText(self.old_text)
            else:
                self.line_edit.setText(next_index.data())
        else:
            QLineEdit.keyPressEvent(self.line_edit, event)

    @Slot("QString", name="_handle_line_edit_text_edited")
    def _handle_line_edit_text_edited(self, text):
        """Filter model.
        """
        self.proxy_model.setFilterRegExp("^" + text)
        self.update_geometry()

    def _view_mouse_move_event(self, event):
        """Highlight current row."""
        index = self.view.indexAt(event.pos())
        self.view.setCurrentIndex(index)

    @Slot("QModelIndex", name="_handle_view_clicked")
    def _handle_view_clicked(self, index):
        """Commit data."""
        self.line_edit.setText(index.data())
        self.data_committed.emit()

    def set_data(self, current, all):
        """Set data."""
        item_list = []
        for name in all:
            qitem = QStandardItem(name)
            item_list.append(qitem)
            qitem.setFlags(~Qt.ItemIsEditable)
        self.model.invisibleRootItem().appendRows(item_list)
        self.line_edit.setText(current)

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Update geometry.
        """
        self.line_edit.setFixedHeight(self._base_size.height())
        self.view.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.view.verticalHeader().setDefaultSectionSize(self._base_size.height())
        table_height = self.view.verticalHeader().length()
        if not table_height:
            table_height = 16  # FIXME
        total_height = table_height + self._base_size.height() + 2
        self.resize(self._base_size.width(), total_height)

    def data(self):
        return self.line_edit.text()


class MultiSearchBarEditor(QSplitter):
    """A widget that splits out several Google-like search bars."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent, Qt.Horizontal)
        self.active_index = 0
        self.setHandleWidth(0)
        self.splitterMoved.connect(self._handle_splitter_moved)
        self.setMouseTracking(True)

    @Slot("int", "int", name="_handle_splitter_moved")
    def _handle_splitter_moved(self, pos, index):
        for k, width in enumerate(self.sizes()):
            search_bar = self.widget(k)
            size = QSize(width, search_bar._base_size.height())
            search_bar.set_base_size(size)
            search_bar.update_geometry()

    def set_active_index(self, index):
        """Set active index. The widget at the given index gains focus.
        """
        event = QFocusEvent(QEvent.FocusOut)
        self.widget(self.active_index).focusOutEvent(event)
        self.active_index = index
        event = QFocusEvent(QEvent.FocusIn)
        self.widget(self.active_index).focusInEvent(event)

    def keyPressEvent(self, event):
        """Call event handler on the active widget.
        """
        self.widget(self.active_index).keyPressEvent(event)

    def focusInEvent(self, event):
        """Set the active index.
        """
        self.set_active_index(0)

    def set_data(self, currents, alls):
        height = 0
        width = 0
        for k, all_ in enumerate(alls):
            search_bar = SearchBarEditor(self)
            try:
                current = currents[k]
            except IndexError:
                current = None
            search_bar.set_data(current, all_)
            search_bar.line_edit.setMouseTracking(True)
            search_bar.line_edit.installEventFilter(self)
            search_bar.view.clicked.connect(lambda i, k=k: self.set_active_index(k))
            self.addWidget(search_bar)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            index = self.indexOf(watched.parent())
            self.set_active_index(index)
        return False

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        total_width = 0
        max_height = 0
        size = self._base_size
        size.setWidth(size.width() / self.count())
        for k in range(self.count()):
            search_bar = self.widget(k)
            search_bar.set_base_size(size)
            search_bar.update_geometry()
            total_width += search_bar.width()
            max_height = max(max_height, search_bar.height())
        self.resize(self.width(), max_height)

    def data(self):
        return ",".join(self.widget(k).data() for k in range(self.count()))


class CheckListEditor(QTableView):
    """A widget that implements a check list."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._base_size = None
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        """Toggle checked state."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space:
            index = self.currentIndex()
            self.toggle_checked_state(index)

    def toggle_checked_state(self, index):
        item = self.model.itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def mouseMoveEvent(self, event):
        """Highlight current row."""
        index = self.indexAt(event.pos())
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Toggle checked state."""
        index = self.indexAt(event.pos())
        self.toggle_checked_state(index)

    def set_data(self, item_names, current_item_names):
        """Set data and update geometry."""
        for name in item_names:
            qitem = QStandardItem(name)
            if name in current_item_names:
                qitem.setCheckState(Qt.Checked)
            else:
                qitem.setCheckState(Qt.Unchecked)
            qitem.setFlags(~Qt.ItemIsEditable & ~Qt.ItemIsUserCheckable)
            self.model.appendRow(qitem)
        self.selectionModel().select(self.model.index(0, 0), QItemSelectionModel.Select)

    def data(self):
        data = []
        for q in self.model.findItems('*', Qt.MatchWildcard):
            if q.checkState() == Qt.Checked:
                data.append(q.text())
        return ",".join(data)

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Update geometry.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        total_height = self.verticalHeader().length() + 2
        self.resize(self._base_size.width(), total_height)


class ObjectNameListEditor(QWidget):
    """A custom QWidget to edit object name lists.
    NOTE: obsolete
    """

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self.missing_dimensions = set()
        self.combos = list()
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_data(self, object_icons, object_class_names, object_names, object_names_dict):
        for i, object_class_name in enumerate(object_class_names):
            combo = QComboBox(self)
            model = QStandardItemModel()
            icon = object_icons[i]
            qitem = QStandardItem(icon, object_class_name)
            qitem.setFlags(~Qt.ItemIsSelectable)
            model.appendRow(qitem)
            all_object_names = object_names_dict[object_class_name]
            for object_name in all_object_names:
                qitem = QStandardItem(object_name)
                model.appendRow(qitem)
            combo.setModel(model)
            combo.insertSeparator(1)
            combo.activated.connect(lambda index, i=i: self.remove_missing_dimension(i))
            self.layout().addWidget(combo)
            self.combos.append(combo)
            try:
                object_name = object_names[i]
            except IndexError:
                self.missing_dimensions.add(i)
                continue
            if object_name:
                combo.setCurrentText(object_name)
            else:
                self.missing_dimensions.add(i)

    def remove_missing_dimension(self, dim):
        combo = self.combos[dim]
        try:
            self.missing_dimensions.remove(dim)
        except KeyError:
            pass
        if not self.missing_dimensions:
            self.data_committed.emit()

    def data(self):
        object_name_list = list()
        for combo in self.combos:
            if combo.currentIndex() == 0:
                object_name = ''
            else:
                object_name = combo.currentText()
            object_name_list.append(object_name)
        return ','.join(object_name_list)
