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

"""Custom editors for model/view programming."""
from PySide6.QtCore import (
    Qt,
    Slot,
    Signal,
    QSortFilterProxyModel,
    QEvent,
    QCoreApplication,
    QModelIndex,
    QPoint,
    QSize,
    QObject,
)
from PySide6.QtWidgets import (
    QLineEdit,
    QTableView,
    QStyledItemDelegate,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QListView,
    QStyle,
    QLabel,
    QComboBox,
)
from PySide6.QtGui import QPalette, QStandardItemModel, QStandardItem, QColor
from spinetoolbox.helpers import IconListManager, interpret_icon_id, make_icon_id, try_number_from_string
from spinetoolbox.spine_db_editor.helpers import FALSE_STRING, TRUE_STRING


class EventFilterForCatchingRollbackShortcut(QObject):
    def eventFilter(self, obj, event):
        """Catches Rollback action shortcut (Ctrl+backspace) while editing is in progress."""
        if (
            event.type() == QEvent.ShortcutOverride
            and event.keyCombination().key() == Qt.Key.Key_Backspace
            and event.keyCombination().keyboardModifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            event.accept()
            return True
        return QObject.eventFilter(self, obj, event)  # Pass event further


class CustomComboBoxEditor(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.event_filter = EventFilterForCatchingRollbackShortcut()
        self.installEventFilter(self.event_filter)


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models."""

    def __init__(self, parent):
        super().__init__(parent)
        self.event_filter = EventFilterForCatchingRollbackShortcut()
        self.installEventFilter(self.event_filter)

    def set_data(self, data):
        """Sets editor's text.

        Args:
            data (Any): anything convertible to string
        """
        if data is not None:
            self.setText(str(data))

    def data(self):
        """Returns editor's text.

        Returns:
            str: editor's text
        """
        return self.text()

    def keyPressEvent(self, event):
        """Prevents shift key press to clear the contents."""
        if event.key() != Qt.Key_Shift:
            super().keyPressEvent(event)


class ParameterValueLineEditor(CustomLineEditor):
    def set_data(self, data):
        """See base class."""
        if data is not None and not isinstance(data, str):
            self.setAlignment(Qt.AlignRight)
        super().set_data(data)

    def data(self):
        """See base class."""
        return try_number_from_string(super().data())


class PivotHeaderTableLineEditor(CustomLineEditor):
    """Line editor that is visible on Pivot view's header tables due to a clever hack."""

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        # For unknown reason editors opened on the header tables of Pivot view are invisible but still usable.
        # This may be somehow connected to the header tables having WA_TransparentForMouseEvents attribute set.
        # In any case, we can reparent the editor here and fix its position later in the delegate.
        super().__init__(parent.parent())
        self._map_to_parent = parent.mapToParent

    def fix_geometry(self):
        """Fixes editor's position after reparenting."""
        geometry = self.geometry()
        geometry.setTopLeft(self._map_to_parent(geometry.topLeft()))
        geometry.setBottomRight(self._map_to_parent(geometry.bottomRight()))
        self.setGeometry(geometry)


class _CustomLineEditDelegate(QStyledItemDelegate):
    """A delegate for placing a CustomLineEditor on the first row of SearchBarEditor."""

    text_edited = Signal(str)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        """Create editor and 'forward' `textEdited` signal."""
        editor = CustomLineEditor(parent)
        editor.set_data(index.data())
        editor.textEdited.connect(lambda s: self.text_edited.emit(s))  # pylint: disable=unnecessary-lambda
        return editor

    def eventFilter(self, editor, event):
        """Handle all sort of special cases."""
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            # Bring focus to parent so tab editing works as expected
            self.parent().setFocus()
            return QCoreApplication.sendEvent(self.parent(), event)
        if event.type() == QEvent.FocusOut:
            # Send event to parent so it gets closed when clicking on an empty area of the table
            return QCoreApplication.sendEvent(self.parent(), event)
        if event.type() == QEvent.ShortcutOverride and event.key() == Qt.Key_Escape:
            # Close editor so we don't need to escape twice to close the parent SearchBarEditor
            self.parent().closeEditor(editor, QStyledItemDelegate.NoHint)
            return True
        return super().eventFilter(editor, event)


class SearchBarEditor(QTableView):
    """A Google-like search bar, implemented as a QTableView with a _CustomLineEditDelegate in the first row."""

    data_committed = Signal()

    def __init__(self, parent, tutor=None):
        """
        Args:
            parent (QWidget, optional): parent widget
            tutor (QWidget, optional): another widget used for positioning.
        """
        super().__init__(parent)
        self._tutor = tutor
        self._base_offset = QPoint()
        self._original_text = None
        self._orig_pos = None
        self.first_index = QModelIndex()
        self._model = QStandardItemModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setSourceModel(self._model)
        self.proxy_model.filterAcceptsRow = self._proxy_model_filter_accepts_row
        self.setModel(self.proxy_model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setTabKeyNavigation(False)
        delegate = _CustomLineEditDelegate(self)
        delegate.text_edited.connect(self._handle_delegate_text_edited)
        self.setItemDelegateForRow(0, delegate)
        hover_color = self.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight).lighter(220)
        self.setStyleSheet(f"QTableView::item:hover {{background: {hover_color.name()};}}")

    def set_data(self, current, items):
        """Populates model.

        Args:
            current (str): item that is currently selected from given items
            items (Sequence of str): items to show in the list
        """
        item_list = [QStandardItem(current)]
        for item in sorted(items, key=lambda x: x.casefold()):
            qitem = QStandardItem(item)
            item_list.append(qitem)
            qitem.setFlags(~Qt.ItemIsEditable)
        self._model.invisibleRootItem().appendRows(item_list)
        self.first_index = self.proxy_model.mapFromSource(self._model.index(0, 0))

    def set_base_offset(self, offset):
        """Changes the base offset that is applied to the editor's position.

        Args:
            offset (QPoint): new offset
        """
        self._base_offset = offset

    def update_geometry(self, option):
        """Updates geometry.

        Args:
            option (QStyleOptionViewItem): style information
        """
        self.resizeColumnsToContents()
        self.verticalHeader().setDefaultSectionSize(option.rect.height())
        self._orig_pos = self.pos() + self._base_offset
        if self._tutor:
            self._orig_pos += self._tutor.mapTo(self.parent(), self._tutor.rect().topLeft())
        self.refit()

    def refit(self):
        """Changes the position and size of the editor to fit the window."""
        self.move(self._orig_pos)
        margins = self.contentsMargins()
        table_height = self.verticalHeader().length() + margins.top() + margins.bottom()
        table_width = self.horizontalHeader().length() + margins.left() + margins.right()
        if table_height > self.parent().size().height():
            table_width += self.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        size = QSize(table_width, table_height).boundedTo(self.parent().size())
        self.resize(size)
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self.parent().mapToGlobal(self.parent().rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))

    def data(self):
        """Returns editor's final data.

        Returns:
            str: editor data
        """
        first_data = self.first_index.data(Qt.ItemDataRole.EditRole)
        if not first_data:
            return None
        model = self.model()
        rows = model.rowCount()
        if any(model.index(row, 0).data(Qt.ItemDataRole.EditRole) == first_data for row in range(1, rows)):
            return first_data
        return model.index(1, 0).data(Qt.ItemDataRole.EditRole)

    @Slot(str)
    def _handle_delegate_text_edited(self, text):
        """Filters model as the first row is being edited.

        Args:
            text (str): text the user has entered on the first row
        """
        self._original_text = text
        self.proxy_model.setFilterRegularExpression("^" + text)
        self.proxy_model.setData(self.first_index, text)
        self.refit()

    def _proxy_model_filter_accepts_row(self, source_row, source_parent):
        """Always accept first row while filtering the rest.

        Args:
            source_row (int): source row index
            source_parent (QModelIndex): parent index for source row

        Returns:
            bool: True if row is accepted, False otherwise
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
        """Edits first index if valid and not already being edited."""
        if not self.first_index.isValid():
            return
        if self.isPersistentEditorOpen(self.first_index):
            return
        self.edit(self.first_index)

    def mousePressEvent(self, event):
        """Commits data."""
        index = self.indexAt(event.position().toPoint())
        if index.row() == 0:
            return
        self.proxy_model.setData(self.first_index, index.data(Qt.ItemDataRole.EditRole))
        self.data_committed.emit()


class BooleanSearchBarEditor(SearchBarEditor):
    def data(self):
        data = super().data()
        return {TRUE_STRING: True, FALSE_STRING: False}.get(data, False)

    def set_data(self, current, items):
        current = {True: TRUE_STRING, False: FALSE_STRING}[bool(current)]
        super().set_data(current, [TRUE_STRING, FALSE_STRING])


class CheckListEditor(QTableView):
    """A check list editor."""

    def __init__(self, parent, tutor=None):
        """
        Args:
            parent (QWidget): parent widget
            tutor (QWidget, optional): a widget that helps in positioning
        """
        super().__init__(parent)
        self._tutor = tutor
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.setShowGrid(False)
        self.setMouseTracking(True)
        self._icons = []
        self._selected = []
        self._items = {}

    def keyPressEvent(self, event):
        """Toggles checked state if the user presses space."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space:
            index = self.currentIndex()
            self.toggle_selected(index)

    def toggle_selected(self, index):
        """Adds or removes given index from selected items.

        Args:
            index (QModelIndex): index to toggle
        """
        item = self._model.itemFromIndex(index).text()
        qitem = self._items[item]
        if item not in self._selected:
            rank = len(self._selected)
            qitem.setCheckState(Qt.CheckState.Checked)
            self._selected.append(item)
        else:
            self._selected.remove(item)
            qitem.setCheckState(Qt.CheckState.Unchecked)

    def mouseMoveEvent(self, event):
        """Sets the current index to the one under mouse."""
        index = self.indexAt(event.position().toPoint())
        self.setCurrentIndex(index)

    def mousePressEvent(self, event):
        """Toggles checked state of pressed index."""
        index = self.indexAt(event.position().toPoint())
        self.toggle_selected(index)

    def set_data(self, items, checked_items):
        """Sets data and updates geometry.

        Args:
            items (Sequence(str)): All items.
            checked_items (Sequence(str)): Initially checked items.
        """
        for item in items:
            qitem = QStandardItem(item)
            qitem.setFlags(~Qt.ItemIsEditable)
            qitem.setData(qApp.palette().window(), Qt.ItemDataRole.BackgroundRole)  # pylint: disable=undefined-variable
            qitem.setCheckState(Qt.CheckState.Unchecked)
            self._items[item] = qitem
            self._model.appendRow(qitem)
        self._selected = [item for item in checked_items if item in items]
        for item in self._selected:
            qitem = self._items[item]
            qitem.setCheckState(Qt.CheckState.Checked)

    def data(self):
        """Returns a comma separated list of checked items.

        Returns
            str
        """
        return ",".join(self._selected)

    def update_geometry(self, option):
        """Updates geometry.

        Args:
            option (QStyleOptionViewItem): style information
        """
        self.resizeColumnsToContents()
        self.verticalHeader().setDefaultSectionSize(option.rect.height())
        margins = self.contentsMargins()
        table_height = self.verticalHeader().length() + margins.top() + margins.bottom()
        table_width = self.horizontalHeader().length() + margins.left() + margins.right()
        if table_height > self.parent().size().height():
            table_width += self.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        size = QSize(table_width, table_height).boundedTo(self.parent().size())
        self.resize(size)
        if self._tutor:
            self.move(self.pos() + self._tutor.mapTo(self.parent(), self._tutor.rect().topLeft()))
        # Adjust position if widget is outside parent's limits
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        parent_bottom_right = self.parent().mapToGlobal(self.parent().rect().bottomRight())
        x_offset = max(0, bottom_right.x() - parent_bottom_right.x())
        y_offset = max(0, bottom_right.y() - parent_bottom_right.y())
        self.move(self.pos() - QPoint(x_offset, y_offset))


class _IconPainterDelegate(QStyledItemDelegate):
    """A delegate to highlight decorations in a QListWidget."""

    def paint(self, painter, option, index):
        """Paints selected items using the highlight brush."""
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, qApp.palette().highlight())  # pylint: disable=undefined-variable
        super().paint(painter, option, index)


class IconColorEditor(QDialog):
    """An editor to let the user select an icon and a color for an object_class."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent)
        icon_size = QSize(32, 32)
        self.icon_mngr = IconListManager(icon_size)
        self.setWindowTitle("Select icon and color")
        self.icon_widget = QWidget(self)
        self.icon_list = QListView(self.icon_widget)
        self.icon_list.setViewMode(QListView.IconMode)
        self.icon_list.setIconSize(icon_size)
        self.icon_list.setResizeMode(QListView.Adjust)
        self.icon_list.setItemDelegate(_IconPainterDelegate(self))
        self.icon_list.setMovement(QListView.Static)
        self.icon_list.setMinimumHeight(400)
        icon_widget_layout = QVBoxLayout(self.icon_widget)
        icon_widget_layout.addWidget(QLabel("Font Awesome icons"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Search icons for...")
        icon_widget_layout.addWidget(self.line_edit)
        icon_widget_layout.addWidget(self.icon_list)
        self.color_dialog = QColorDialog(self)
        self.color_dialog.setWindowFlags(Qt.WindowType.Widget)
        self.color_dialog.setOption(QColorDialog.NoButtons, True)
        self.color_dialog.setOption(QColorDialog.DontUseNativeDialog, True)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
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
        """Filters icons according to search terms.

        Args:
            source_row (int): source row index
            source_parent (QModelIndex): parent index for source row

        Returns:
            bool: True if row is accepted, False otherwise
        """
        text = self.line_edit.text()
        if not text:
            return QSortFilterProxyModel.filterAcceptsRow(self.proxy_model, source_row, source_parent)
        searchterms = self.icon_mngr.model.index(source_row, 0, source_parent).data(Qt.ItemDataRole.UserRole + 1)
        return any(text in term for term in searchterms)

    def connect_signals(self):
        """Connects signals to slots."""
        self.line_edit.textEdited.connect(self.proxy_model.invalidateFilter)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def set_data(self, data):
        """Sets current icon data.

        Args:
            data (int): database icon data
        """
        icon_code, color_code = interpret_icon_id(data)
        self.icon_mngr.init_model()
        for i in range(self.proxy_model.rowCount()):
            index = self.proxy_model.index(i, 0)
            if index.data(Qt.ItemDataRole.UserRole) == icon_code:
                self.icon_list.setCurrentIndex(index)
                break
        self.color_dialog.setCurrentColor(QColor(color_code))

    def data(self):
        """Gets current icon data.

        Returns:
            int: database icon data
        """
        icon_code = self.icon_list.currentIndex().data(Qt.ItemDataRole.UserRole)
        color_code = self.color_dialog.currentColor().rgb()
        return make_icon_id(icon_code, color_code)
