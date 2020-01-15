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
Custom editors for model/view programming.


:author: M. Marin (KTH)
:date:   2.9.2018
"""

import sys
from PySide2.QtCore import (
    Qt,
    Slot,
    Signal,
    QItemSelectionModel,
    QSortFilterProxyModel,
    QEvent,
    QCoreApplication,
    QModelIndex,
    QPoint,
    QSize,
)
from PySide2.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QTableView,
    QItemDelegate,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QListView,
    QStyle,
    QLabel,
)
from PySide2.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QColor
from ..helpers import IconListManager, interpret_icon_id, make_icon_id


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models.
    """

    def set_data(self, data):
        if data is not None:
            self.setText(str(data))
        if isinstance(data, int):
            self.setValidator(QIntValidator(self))

    def data(self):
        return self.text()

    def keyPressEvent(self, event):
        """Prevents shift key press to clear the contents."""
        if event.key() != Qt.Key_Shift:
            super().keyPressEvent(event)


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models.
    """

    data_committed = Signal()

    def set_data(self, current_text, items):
        self.addItems(items)
        if current_text and current_text in items:
            self.setCurrentText(current_text)
        else:
            self.setCurrentIndex(-1)
        self.activated.connect(lambda: self.data_committed.emit())  # pylint: disable=unnecessary-lambda
        self.showPopup()

    def data(self):
        return self.currentText()


class CustomLineEditDelegate(QItemDelegate):
    """A delegate for placing a CustomLineEditor on the first row of SearchBarEditor.
    """

    text_edited = Signal("QString")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        """Create editor and 'forward' `textEdited` signal.
        """
        editor = CustomLineEditor(parent)
        editor.set_data(index.data())
        editor.textEdited.connect(lambda s: self.text_edited.emit(s))  # pylint: disable=unnecessary-lambda
        return editor

    def eventFilter(self, editor, event):
        """Handle all sort of special cases.
        """
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            # Bring focus to parent so tab editing works as expected
            self.parent().setFocus()
            return QCoreApplication.sendEvent(self.parent(), event)
        if event.type() == QEvent.FocusOut:
            # Send event to parent so it gets closed when clicking on an empty area of the table
            return QCoreApplication.sendEvent(self.parent(), event)
        if event.type() == QEvent.ShortcutOverride and event.key() == Qt.Key_Escape:
            # Close editor so we don't need to escape twice to close the parent SearchBarEditor
            self.parent().closeEditor(editor, QItemDelegate.NoHint)
            return True
        return super().eventFilter(editor, event)


class SearchBarEditor(QTableView):
    """A Google-like search bar, implemented as a QTableView with a CustomLineEditDelegate in the first row.
    """

    data_committed = Signal()

    def __init__(self, parent, tutor=None):
        """Initializes instance.

        Args:
            parent (QWidget): parent widget
            tutor (QWidget, NoneType): another widget used for positioning.
        """
        super().__init__(parent)
        self._tutor = tutor
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

    def set_data(self, current, items):
        """Populates model.

        Args:
            current (str)
            items (Sequence(str))
        """
        item_list = [QStandardItem(current)]
        for item in items:
            qitem = QStandardItem(item)
            item_list.append(qitem)
            qitem.setFlags(~Qt.ItemIsEditable)
        self.model.invisibleRootItem().appendRows(item_list)
        self.first_index = self.proxy_model.mapFromSource(self.model.index(0, 0))

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Updates geometry.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        self._orig_pos = self.pos()
        if self._tutor:
            self._orig_pos += self._tutor.mapTo(self.parent(), self._tutor.parent().pos())
        self.refit()

    def refit(self):
        self.move(self._orig_pos)
        table_height = self.verticalHeader().length()
        size = QSize(self._base_size.width(), table_height + 2).boundedTo(self.parent().size())
        self.resize(size)
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self.parent().mapToGlobal(self.parent().rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))

    def data(self):
        data = self.first_index.data(Qt.EditRole)
        return data

    @Slot("QString")
    def _handle_delegate_text_edited(self, text):
        """Filters model as the first row is being edited."""
        self._original_text = text
        self.proxy_model.setFilterRegExp("^" + text)
        self.proxy_model.setData(self.first_index, text)
        self.refit()

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        """Always accept first row.
        """
        if source_row == 0:
            return True
        return QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)

    def keyPressEvent(self, event):
        """Sets data from current index into first index as the user navigates
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
        """Edits first index if valid and not already being edited.
        """
        if not self.first_index.isValid():
            return
        if self.isPersistentEditorOpen(self.first_index):
            return
        self.edit(self.first_index)

    def mouseMoveEvent(self, event):
        """Sets the current index to the one hovered by the mouse."""
        if not self.currentIndex().isValid():
            return
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Commits data."""
        index = self.indexAt(event.pos())
        if index.row() == 0:
            return
        self.proxy_model.setData(self.first_index, index.data(Qt.EditRole))
        self.data_committed.emit()


class CheckListEditor(QTableView):
    """A check list editor."""

    def __init__(self, parent, tutor=None):
        """Initialize class."""
        super().__init__(parent)
        self._tutor = tutor
        self._base_size = None
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        """Toggles checked state if the user presses space."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space:
            index = self.currentIndex()
            self.toggle_checked_state(index)

    def toggle_checked_state(self, index):
        """Toggles checked state of given index.

        Args:
            index (QModelIndex)
        """
        item = self.model.itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def mouseMoveEvent(self, event):
        """Sets the current index to the one under mouse."""
        index = self.indexAt(event.pos())
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Toggles checked state of pressed index."""
        index = self.indexAt(event.pos())
        self.toggle_checked_state(index)

    def set_data(self, items, checked_items):
        """Sets data and updates geometry.

        Args:
            items (Sequence(str)): All items.
            checked_items (Sequence(str)): Initially checked items.
        """
        for item in items:
            qitem = QStandardItem(item)
            if item in checked_items:
                qitem.setCheckState(Qt.Checked)
            else:
                qitem.setCheckState(Qt.Unchecked)
            qitem.setFlags(~Qt.ItemIsEditable & ~Qt.ItemIsUserCheckable)
            qitem.setData(qApp.palette().window(), Qt.BackgroundRole)  # pylint: disable=undefined-variable
            self.model.appendRow(qitem)
        self.selectionModel().select(self.model.index(0, 0), QItemSelectionModel.Select)

    def data(self):
        """Returns a comma separated list of checked items.

        Returns
            str
        """
        data = []
        for q in self.model.findItems('*', Qt.MatchWildcard):
            if q.checkState() == Qt.Checked:
                data.append(q.text())
        return ",".join(data)

    def set_base_size(self, size):
        self._base_size = size

    def update_geometry(self):
        """Updates geometry.
        """
        self.horizontalHeader().setDefaultSectionSize(self._base_size.width())
        self.verticalHeader().setDefaultSectionSize(self._base_size.height())
        total_height = self.verticalHeader().length() + 2
        size = QSize(self._base_size.width(), total_height).boundedTo(self.parent().size())
        self.resize(size)
        if self._tutor:
            self.move(self.pos() + self._tutor.mapTo(self.parent(), self._tutor.parent().pos()))
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self.parent().mapToGlobal(self.parent().rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))


class IconPainterDelegate(QItemDelegate):
    """A delegate to highlight decorations in a QListWidget."""

    def paint(self, painter, option, index):
        """Paints selected items using the highlight brush."""
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, qApp.palette().highlight())  # pylint: disable=undefined-variable
        super().paint(painter, option, index)


class IconColorEditor(QDialog):
    """An editor to let the user select an icon and a color for an object class.
    """

    def __init__(self, parent):
        """Init class."""
        super().__init__(parent)  # , Qt.Popup)
        icon_size = QSize(32, 32)
        self.icon_mngr = IconListManager(icon_size)
        self.setWindowTitle("Select icon and color")
        self.icon_widget = QWidget(self)
        self.icon_list = QListView(self.icon_widget)
        self.icon_list.setViewMode(QListView.IconMode)
        self.icon_list.setIconSize(icon_size)
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
        top_widget = QWidget(self)
        top_layout = QHBoxLayout(top_widget)
        top_layout.addWidget(self.icon_widget)
        top_layout.addWidget(self.color_dialog)
        layout = QVBoxLayout(self)
        layout.addWidget(top_widget)
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
        icon_code, color_code = interpret_icon_id(data)
        self.icon_mngr.init_model()
        for i in range(self.proxy_model.rowCount()):
            index = self.proxy_model.index(i, 0)
            if index.data(Qt.UserRole) == icon_code:
                self.icon_list.setCurrentIndex(index)
                break
        self.color_dialog.setCurrentColor(QColor(color_code))

    def data(self):
        icon_code = self.icon_list.currentIndex().data(Qt.UserRole)
        color_code = self.color_dialog.currentColor().rgb()
        return make_icon_id(icon_code, color_code)


class NumberParameterInlineEditor(QDoubleSpinBox):
    """
    An editor widget for numeric (datatype double) parameter values.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setRange(-sys.float_info.max, sys.float_info.max)
        self.setDecimals(sys.float_info.mant_dig)

    def set_data(self, data):
        if data is not None:
            self.setValue(float(data))

    def data(self):
        return self.value()
