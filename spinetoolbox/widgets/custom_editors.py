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
Custom editors for model/view programming.


:author: M. Marin (KTH)
:date:   2.9.2018
"""

import json
from PySide2.QtCore import (
    Qt,
    Slot,
    Signal,
    QItemSelectionModel,
    QSortFilterProxyModel,
    QTimer,
    QEvent,
    QCoreApplication,
    QModelIndex,
    QPoint,
    QSize,
)
from PySide2.QtWidgets import (
    QComboBox,
    QLineEdit,
    QTableView,
    QItemDelegate,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QListView,
    QStyle,
    QLabel,
)
from PySide2.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QColor
from treeview_models import LazyLoadingArrayModel
from widgets.custom_qtableview import CopyPasteTableView


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

    def keyPressEvent(self, event):
        """Don't allow shift key to clear the contents."""
        if event.key() != Qt.Key_Shift:
            super().keyPressEvent(event)


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
    """A delegate for placing a CustomLineEditor on the first row of SearchBarEditor.

    Attributes:
        parent (SearchBarEditor): search bar editor
    """

    text_edited = Signal("QString", name="text_edited")

    def __init__(self, parent):
        """Init class."""
        super().__init__(parent)
        self._parent = parent

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        """Create editor and 'forward' `textEdited` signal.
        """
        editor = CustomLineEditor(parent)
        editor.set_data(index.data())
        editor.textEdited.connect(lambda s: self.text_edited.emit(s))
        return editor

    def eventFilter(self, editor, event):
        """Handle all sort of special cases.
        """
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            # Bring focus to parent so tab editing works as expected
            self._parent.setFocus()
            return QCoreApplication.sendEvent(self._parent, event)
        if event.type() == QEvent.FocusOut:
            # Send event to parent so it gets closed when clicking on an empty area of the table
            return QCoreApplication.sendEvent(self._parent, event)
        if event.type() == QEvent.ShortcutOverride and event.key() == Qt.Key_Escape:
            # Close editor so we don't need to escape twice to close the parent SearchBarEditor
            self._parent.closeEditor(editor, QItemDelegate.NoHint)
            return True
        return super().eventFilter(editor, event)


class SearchBarEditor(QTableView):
    """A Google-like search bar, implemented as a QTableView with a CustomLineEditDelegate in the first row.

    Attributes:
        parent (QWidget): the parent for this widget
        elder_sibling (QWidget or NoneType): another widget which is used to find this widget's position.
    """

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, elder_sibling=None, is_json=False):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self._elder_sibling = elder_sibling
        self._is_json = is_json
        self._base_size = None
        self._original_text = None
        self._orig_pos = None
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

    def set_data(self, current, all):
        """Populate model and initialize first index."""
        if self._is_json:
            all = [json.loads(x) for x in all]
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
        """Update geometry. Resize the widget to optimal size, then adjust its position.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        self._orig_pos = self.pos()
        if self._elder_sibling:
            self._orig_pos += self._elder_sibling.mapTo(self._parent, self._elder_sibling.parent().pos())
        self.refit()

    def refit(self):
        """Resize to optimal size.
        """
        self.move(self._orig_pos)
        table_height = self.verticalHeader().length()
        size = QSize(self._base_size.width(), table_height + 2).boundedTo(self._parent.size())
        self.resize(size)
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self._parent.mapToGlobal(self._parent.rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))

    def data(self):
        data = self.first_index.data(Qt.EditRole)
        if self._is_json:
            data = json.dumps(data)
        return data

    @Slot("QString", name="_handle_delegate_text_edited")
    def _handle_delegate_text_edited(self, text):
        """Filter model as the first row is being edited."""
        self._original_text = text
        self.proxy_model.setFilterRegExp("^" + text)
        self.proxy_model.setData(self.first_index, text)
        self.refit()

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        """Overridden method to always accept first row.
        """
        if source_row == 0:
            return True
        return QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)

    def keyPressEvent(self, event):
        """Set data from current index into first index as the user navigates
        through the table using the up and down keys.
        """
        super().keyPressEvent(event)
        event.accept()  # Important to avoid unhandled behavior when trying to navigate outside view limits
        # Initialize original text. TODO: Is there a better place for this?
        if self._original_text is None:
            self.proxy_model.setData(self.first_index, event.text())
            self._handle_delegate_text_edited(event.text())
        # Set data from current index in model
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current = self.currentIndex()
            if current.row() == 0:
                self.proxy_model.setData(self.first_index, self._original_text)
            else:
                self.proxy_model.setData(self.first_index, current.data())

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        self.edit_first_index()

    def edit_first_index(self):
        """Edit first index if valid and not already being edited.
        """
        if not self.first_index.isValid():
            return
        if self.isPersistentEditorOpen(self.first_index):
            return
        self.edit(self.first_index)

    def mouseMoveEvent(self, event):
        """Make hovered index the current index."""
        if not self.currentIndex().isValid():
            return
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Commit data."""
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.proxy_model.setData(self.first_index, index.data(Qt.EditRole))
        self.data_committed.emit()


class SearchBarDelegate(QItemDelegate):
    """A custom delegate to place a SearchBarEditor on each cell of a MultiSearchBarEditor.

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
        if event.type() == QEvent.FocusOut:
            super().eventFilter(editor, event)
            return QCoreApplication.sendEvent(self._parent, event)
        return super().eventFilter(editor, event)


class MultiSearchBarEditor(QTableView):
    """A table view made of several Google-like search bars."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, elder_sibling=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self._elder_sibling = elder_sibling
        self.alls = None
        self._max_item_count = None
        self._base_size = None
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        delegate = SearchBarDelegate(self)
        self.setItemDelegate(delegate)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

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
        size = QSize(self._base_size.width(), self._base_size.height() * (self._max_item_count + 2) + 2).boundedTo(
            self._parent.size()
        )
        self.resize(size)
        if self._elder_sibling:
            self.move(self.pos() + self._elder_sibling.mapTo(self._parent, self._elder_sibling.parent().pos()))
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self._parent.mapToGlobal(self._parent.rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))

    def start_editing(self):
        """Start editing first item.
        """
        index = self.model.index(0, 0)
        self.setCurrentIndex(index)
        self.edit(index)


class CheckListEditor(QTableView):
    """A check list editor."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, elder_sibling=None):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self._elder_sibling = elder_sibling
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
            qitem.setData(qApp.palette().window(), Qt.BackgroundRole)
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
        size = QSize(self._base_size.width(), total_height).boundedTo(self._parent.size())
        self.resize(size)
        if self._elder_sibling:
            self.move(self.pos() + self._elder_sibling.mapTo(self._parent, self._elder_sibling.parent().pos()))
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self._parent.mapToGlobal(self._parent.rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))


class JSONEditor(QTabWidget):
    """A double JSON editor, featuring:
    - A QTextEdit for editing arbitrary json.
    - A QTableView for editing json array.
    """

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, elder_sibling, popup=False):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent
        self._elder_sibling = elder_sibling
        self._popup = popup
        self.setTabPosition(QTabWidget.South)
        self.tab_raw = QWidget()
        vertical_layout = QVBoxLayout(self.tab_raw)
        vertical_layout.setSpacing(0)
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.text_edit = QTextEdit(self.tab_raw)
        self.text_edit.setTabChangesFocus(True)
        vertical_layout.addWidget(self.text_edit)
        self.addTab(self.tab_raw, "Raw")
        self.tab_table = QWidget()
        vertical_layout = QVBoxLayout(self.tab_table)
        vertical_layout.setSpacing(0)
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.table_view = CopyPasteTableView(self.tab_table)
        self.table_view.horizontalHeader().hide()
        self.table_view.setTabKeyNavigation(False)
        vertical_layout.addWidget(self.table_view)
        self.addTab(self.tab_table, "Table")
        self.setCurrentIndex(0)
        self._base_size = None
        self.model = LazyLoadingArrayModel(self)
        self.table_view.setModel(self.model)
        self.text_edit.installEventFilter(self)
        self.table_view.installEventFilter(self)
        self.table_view.keyPressEvent = self._view_key_press_event
        if popup:
            self.text_edit.setReadOnly(True)
            self.table_view.setEditTriggers(QTableView.NoEditTriggers)
            self.setFocusPolicy(Qt.NoFocus)

    def _view_key_press_event(self, event):
        """Accept key events on the view to avoid weird behaviour, when trying to navigate
        outside of its limits.
        """
        QTableView.keyPressEvent(self.table_view, event)
        event.accept()

    def eventFilter(self, widget, event):
        """Intercept events to text_edit and table_view to enable consistent behavior.
        """
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if widget == self.text_edit:
                    self.setCurrentIndex(1)
                    return True
                if widget == self.table_view:
                    return QCoreApplication.sendEvent(self, event)
            if event.key() == Qt.Key_Backtab:
                if widget == self.table_view:
                    self.setCurrentIndex(0)
                    return True
                if widget == self.text_edit:
                    return QCoreApplication.sendEvent(self, event)
            if event.key() == Qt.Key_Escape:
                self.setFocus()
                return QCoreApplication.sendEvent(self, event)
            if event.key() in (Qt.Key_Enter, Qt.Key_Return):
                if widget == self.table_view:
                    if self.table_view.isPersistentEditorOpen(self.table_view.currentIndex()):
                        return True
                    self.setFocus()
                    return QCoreApplication.sendEvent(self, event)
                return False
        if event.type() == QEvent.FocusOut:
            QTimer.singleShot(0, self.check_focus)
        return False

    def check_focus(self):
        """Called when either the text edit or the table view lose focus.
        Check if the focus is still on this widget (which would mean it was a tab change)
        otherwise emit signal so this is closed.
        """
        if qApp.focusWidget() != self.focusWidget():
            self.data_committed.emit()

    @Slot("int", name="_handle_current_changed")
    def _handle_current_changed(self, index):
        """Update json data on text edit or table view, and set focus.
        """
        if index == 0:
            data = self.model.all_data()
            if data is not None:
                formatted_data = json.dumps(data, indent=4)
                self.text_edit.setText(formatted_data)
            self.text_edit.setFocus()
        elif index == 1:
            text = self.text_edit.toPlainText()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            self.model.reset_model(data)
            self.table_view.setFocus()
            self.table_view.setCurrentIndex(self.model.index(0, 0))
            self.table_view.selectionModel().clearSelection()

    def set_data(self, data, current_index):
        """Set data on text edit or table view (model) depending on current index.
        """
        self.setCurrentIndex(current_index)
        self.currentChanged.connect(self._handle_current_changed)
        try:
            loaded_data = json.loads(data)
        except (TypeError, json.JSONDecodeError):
            # NOTE: TypeError happens when data is None
            loaded_data = None
        if current_index == 0:
            if loaded_data is not None:
                formatted_data = json.dumps(loaded_data, indent=4)
                self.text_edit.setText(formatted_data)
        elif current_index == 1:
            self.model.reset_model(loaded_data)
        QTimer.singleShot(0, self.start_editing)

    def start_editing(self):
        """Start editing.
        """
        current_index = self.currentIndex()
        if current_index == 0:
            self.text_edit.setFocus()
        elif current_index == 1:
            self.table_view.setFocus()

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Update geometry.
        """
        self.table_view.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.table_view.verticalHeader().setDefaultSectionSize(self._base_size.height())
        if self._popup:
            base_width = 0.6 * self._base_size.width()
            offset = QPoint(0.4 * self._base_size.width(), 0)
            min_size = QSize(0, 0)
        else:
            base_width = self._base_size.width()
            offset = QPoint(0, 0)
            min_size = QSize(200, 0)
        size = QSize(base_width, self._base_size.height() * 16)  # TODO: Try and get rid of the 16 here
        size = size.boundedTo(self._parent.size())
        size = size.expandedTo(min_size)
        self.resize(size)
        self.move(offset + self.pos() + self._elder_sibling.mapTo(self._parent, self._elder_sibling.parent().pos()))
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self._parent.mapToGlobal(self._parent.rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))

    def data(self):
        index = self.currentIndex()
        if index == 0:
            text = self.text_edit.toPlainText()
            if not text:  # empty string is not valid JSON
                text = 'null'
            return text
        elif index == 1:
            return json.dumps(self.model.all_data())


class IconPainterDelegate(QItemDelegate):
    """A delegate to highlight decorations in a QListWidget."""

    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, index):
        """Highlight selected items."""
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, qApp.palette().highlight())
        super().paint(painter, option, index)


class IconColorEditor(QDialog):
    """An editor to let the user select an icon and a color for an object class.
    """

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, icon_mngr):
        """Init class."""
        super().__init__(parent)  # , Qt.Popup)
        self.icon_mngr = icon_mngr
        self.setWindowTitle("Select icon and color")
        self.icon_widget = QWidget(self)
        self.icon_list = QListView(self.icon_widget)
        self.icon_list.setViewMode(QListView.IconMode)
        self.icon_list.setIconSize(QSize(32, 32))
        self.icon_list.setResizeMode(QListView.Adjust)
        self.icon_list.setItemDelegate(IconPainterDelegate(self))
        self.icon_list.setMovement(QListView.Static)
        self.icon_list.setMinimumHeight(400)
        icon_widget_layout = QVBoxLayout(self.icon_widget)
        icon_widget_layout.addWidget(QLabel("Font Awesome icons"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Search icons for...")
        icon_widget_layout.addWidget(self.line_edit)
        icon_widget_layout.addWidget(self.icon_list)
        self.color_dialog = QColorDialog(self)
        self.color_dialog.setWindowFlags(Qt.Widget)
        self.color_dialog.setOption(QColorDialog.NoButtons, True)
        self.color_dialog.setOption(QColorDialog.DontUseNativeDialog, True)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QVBoxLayout(self)
        layout.addWidget(self.icon_widget)
        layout.addWidget(self.color_dialog)
        layout.addWidget(self.button_box)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.icon_mngr.model)
        self.proxy_model.filterAcceptsRow = self._proxy_model_filter_accepts_row
        self.icon_list.setModel(self.proxy_model)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.connect_signals()

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        """Overridden method to filter icons according to search terms.
        """
        text = self.line_edit.text()
        if not text:
            return QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)
        searchterms = self.icon_mngr.model.index(source_row, 0, source_parent).data(Qt.UserRole + 1)
        return any([text in term for term in searchterms])

    def connect_signals(self):
        """Connect signals to slots."""
        self.line_edit.textEdited.connect(self.proxy_model.invalidateFilter)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def set_data(self, data):
        icon_code, color_code = self.icon_mngr.icon_color_code(data)
        self.icon_mngr.init_model()
        for i in range(self.proxy_model.rowCount()):
            index = self.proxy_model.index(i, 0)
            if index.data(Qt.UserRole) == icon_code:
                self.icon_list.setCurrentIndex(index)
                break
        self.color_dialog.setCurrentColor(QColor(color_code))

    def data(self):
        if not self.result():
            return None
        icon_code = self.icon_list.currentIndex().data(Qt.UserRole)
        color_code = self.color_dialog.currentColor().rgb()
        return self.icon_mngr.display_icon(icon_code, color_code)
