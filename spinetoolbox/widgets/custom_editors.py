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

import logging
from PySide2.QtCore import Qt, Slot, Signal, QItemSelectionModel, QSortFilterProxyModel, QRegExp, \
    QTimer, QEvent, QCoreApplication, QModelIndex
from PySide2.QtWidgets import QComboBox, QLineEdit, QTableView, QItemDelegate, QFrame
from PySide2.QtGui import QIntValidator, QStandardItemModel, QStandardItem


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


class CustomLineEditDelegate(QItemDelegate):
    """A custom delegate for SearchBarEditor.

    Attributes:
        parent (SearchBarEditor): search bar editor
    """
    text_edited = Signal("QString", name="text_edited")

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.key_list = (Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_Escape)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        editor = CustomLineEditor(parent)
        editor.set_data(index.data())
        editor.textEdited.connect(lambda s: self.text_edited.emit(s))
        return editor

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Escape,):
            self._parent.setFocus()
            return QCoreApplication.sendEvent(self._parent, event)
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab) \
                or event.type() in (QEvent.FocusOut,):
            return QCoreApplication.sendEvent(self._parent, event)
        return super().eventFilter(editor, event)


class SearchBarEditor(QTableView):
    """A widget that implements a Google-like search bar."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._base_size = None
        self._original_text = None
        self.first_index = QModelIndex()
        self.model = QStandardItemModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.filterAcceptsRow = self._proxy_model_filter_accepts_row
        self.setModel(self.proxy_model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setMouseTracking(True)
        self.setTabKeyNavigation(False)
        delegate = CustomLineEditDelegate(self)
        delegate.text_edited.connect(self._handle_delegate_text_edited)
        self.setItemDelegateForRow(0, delegate)

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        if source_row == 0:
            return True
        return QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)

    @Slot("QString", name="_handle_delegate_text_edited")
    def _handle_delegate_text_edited(self, text):
        self._original_text = text
        self.proxy_model.setFilterRegExp("^" + text)
        self.update_geometry()

    def keyPressEvent(self, event):
        previous = self.currentIndex()
        if self.isPersistentEditorOpen(previous):
            self.closePersistentEditor(previous)
        super().keyPressEvent(event)
        current = self.currentIndex()
        if event.key() not in (Qt.Key_Up, Qt.Key_Down):
            return
        if current.row() == 0:
            self.proxy_model.setData(self.first_index, self._original_text)
        else:
            self.proxy_model.setData(self.first_index, current.data())

    def currentChanged(self, current, previous):
        """Edit first index."""
        super().currentChanged(current, previous)
        self.edit_first_index()

    def edit_first_index(self):
        if not self.first_index.isValid():
            return
        if self.isPersistentEditorOpen(self.first_index):
            return
        self.edit(self.first_index)

    def mouseMoveEvent(self, event):
        """Highlight current row."""
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Commit data."""
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.proxy_model.setData(self.first_index, index.data())
        self.data_committed.emit()

    def set_data(self, current, all):
        """Set data."""
        item_list = [QStandardItem(current)]
        for name in all:
            qitem = QStandardItem(name)
            item_list.append(qitem)
            qitem.setFlags(~Qt.ItemIsEditable)
        self.model.invisibleRootItem().appendRows(item_list)
        self.first_index = self.proxy_model.mapFromSource(self.model.index(0, 0))

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Update geometry.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        table_height = self.verticalHeader().length()
        self.resize(self._base_size.width(), table_height + 2)

    def data(self):
        proxy_index = self.proxy_model.index(0, 0)
        return proxy_index.data()


class SearchBarDelegate(QItemDelegate):
    """A custom delegate for MultiSearchBarEditor.

    Attributes:
        parent (MultiSearchBarEditor): multi search bar editor
    """
    data_committed = Signal("QModelIndex", "QVariant", name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        editor = SearchBarEditor(parent)
        editor.set_data(index.data(), self._parent.alls[index.column()])
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        size = option.rect.size()
        editor.set_base_size(size)
        editor.update_geometry()

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def eventFilter(self, editor, event):
        if event.type() in (QEvent.FocusOut,):
            return QCoreApplication.sendEvent(self._parent, event)
        return super().eventFilter(editor, event)

class MultiSearchBarEditor(QTableView):
    """A table view made of several Google-like search bars."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self.alls = None
        self._max_item_count = None
        self._base_size = None
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        delegate = SearchBarDelegate(self)
        self.setItemDelegate(delegate)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        # self.setFrameStyle(QFrame.NoFrame)

    def set_data(self, header, currents, alls):
        self.model.setHorizontalHeaderLabels(header)
        self.alls = alls
        self._max_item_count = max(len(x) for x in alls)
        item_list = []
        for k in range(len(header)):
            try:
                current = currents[k]
            except IndexError:
                current = None
            qitem = QStandardItem(current)
            item_list.append(qitem)
        self.model.invisibleRootItem().appendRow(item_list)
        QTimer.singleShot(0, self.start_editing)

    def data(self):
        return ",".join(self.model.index(0, j).data() for j in range(self.model.columnCount()))

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Update geometry.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width() / self.model.columnCount())
        self.horizontalHeader().setMaximumHeight(self._base_size.height())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        self.resize(self._base_size.width(), self._base_size.height() * (self._max_item_count + 2) + 2)

    def start_editing(self):
        """Start editing first item.
        """
        index = self.model.index(0, 0)
        self.setCurrentIndex(index)
        self.edit(index)


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
