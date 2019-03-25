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
Custom QWidgets for Filtering and Zooming.

:author: P. Vennström (VTT)
:date:   4.12.2018
"""

from PySide2.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, \
    QMenu, QPushButton, QAction, QTableView, QStyle, QToolBar, QStyleOptionMenuItem, \
    QListView, QLineEdit, QDialogButtonBox, QToolButton
from PySide2.QtCore import Qt, QTimer, Signal, Slot, QItemSelectionModel
from PySide2.QtGui import QPixmap, QPainter, QStandardItem, QStandardItemModel
from models import MinimalTableModel
from tabularview_models import FilterCheckboxListModel


class AutoFilterWidget(QWidget):
    """A widget to show the auto filter 'menu'."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.model = MinimalTableModel(self)
        self.model.data = self._model_data
        self.model.flags = self._model_flags
        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        self.view.setMouseTracking(True)
        self.view.entered.connect(self._handle_view_entered)
        self.view.clicked.connect(self._handle_view_clicked)
        self.view.leaveEvent = self._view_leave_event
        self.button = QToolButton(self)
        self.button.setText("Ok")
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.button.clicked.connect(self._handle_ok_button_clicked)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.checked_values = dict()
        self.hide()

    def _model_flags(self, index):
        """Return no item flags."""
        return ~Qt.ItemIsEditable

    def _model_data(self, index, role=Qt.DisplayRole):
        """Read checked state from first column."""
        if role == Qt.CheckStateRole:
            checked = self.model._main_data[index.row()][0]
            if checked is None:
                return Qt.PartiallyChecked
            elif checked is True:
                return Qt.Checked
            else:
                return Qt.Unchecked
        return MinimalTableModel.data(self.model, index, role)

    @Slot("QModelIndex", name="_handle_view_entered")
    def _handle_view_entered(self, index):
        """Highlight current row."""
        self.view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    @Slot("QModelIndex", name="_handle_view_clicked")
    def _handle_view_clicked(self, clicked_index):
        """Toggle checked state."""
        index = self.model.index(clicked_index.row(), 0)
        checked = index.data(Qt.EditRole)
        model_data = self.model._main_data
        row_count = self.model.rowCount()
        if index.row() == 0:
            # All row
            all_checked = checked in (None, False)
            for row in range(row_count):
                model_data[row][0] = all_checked
            self.model.dataChanged.emit(self.model.index(0, 1), self.model.index(row_count - 1, 1))
        else:
            # Data row
            self.model.setData(index, not checked)
            self.model.dataChanged.emit(clicked_index, clicked_index)
            self.set_data_for_all_index()

    def _view_leave_event(self, event):
        """Clear selection."""
        self.view.selectionModel().clearSelection()
        event.accept()

    def set_data_for_all_index(self):
        """Set data for 'all' index based on data from all other indexes."""
        all_index = self.model.index(0, 0)
        true_count = 0
        for row_data in self.model._main_data[1:]:
            if row_data[0] == True:
                true_count += 1
        if true_count == len(self.model._main_data) - 1:
            self.model.setData(all_index, True)
        elif true_count == 0:
            self.model.setData(all_index, False)
        else:
            self.model.setData(all_index, None)
        index = self.model.index(0, 1)
        self.model.dataChanged.emit(index, index)

    @Slot("bool", name="_handle_ok_button_clicked")
    def _handle_ok_button_clicked(self, checked=False):
        """Called when user pressed Ok."""
        self.checked_values = dict()
        data = self.model._main_data
        for checked, value, object_class_id_set in data[1:]:
            if checked:
                continue
            for object_class_id in object_class_id_set:
                self.checked_values.setdefault(object_class_id, set()).add(value)
        self.hide()
        self.data_committed.emit()

    def set_values(self, values):
        """Set values to show in the 'menu'."""
        self.model.reset_model([[None, "All", ""]] + values)
        self.set_data_for_all_index()
        self.view.horizontalHeader().hideSection(0)  # Column 0 holds the checked state
        self.view.horizontalHeader().hideSection(2)  # Column 2 holds the (cls_id_set)

    def show(self, min_width=0):
        super().show()
        self.view.horizontalHeader().setMinimumSectionSize(0)
        self.view.resizeColumnToContents(1)
        table_width = self.view.horizontalHeader().sectionSize(1) + 2
        width = max(table_width, min_width)
        self.view.horizontalHeader().setMinimumSectionSize(width)
        height = self.view.verticalHeader().length() + self.button.height()
        parent_height = self.parent().height()
        self.setFixedHeight(min(height, parent_height / 2) + 2)
        if self.view.verticalScrollBar().isVisible():
            width += qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        self.setFixedWidth(width)
        self.button.setFixedWidth(width)


class FilterWidget(QWidget):
    """Filter widget class."""
    okPressed = Signal()
    cancelPressed = Signal()

    def __init__(self, parent=None, show_empty=True):
        """Init class."""
        super().__init__(parent)
        # parameters
        self._filter_state = set()
        self._filter_empty_state = False
        self._search_text = ''
        self.search_delay = 200

        # create ui elements
        self._ui_vertical_layout = QVBoxLayout(self)
        self._ui_list = QListView()
        self._ui_edit = QLineEdit()
        self._ui_edit.setPlaceholderText('Search')
        self._ui_edit.setClearButtonEnabled(True)
        self._ui_buttons = QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self._ui_vertical_layout.addWidget(self._ui_edit)
        self._ui_vertical_layout.addWidget(self._ui_list)
        self._ui_vertical_layout.addWidget(self._ui_buttons)

        # add models
        self._search_timer = QTimer()  # Used to limit search so it doesn't search when typing
        self._search_timer.setSingleShot(True)

        self._filter_model = FilterCheckboxListModel(show_empty=show_empty)
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)

        # connect signals
        self._ui_list.clicked.connect(self._filter_model.click_index)
        self._search_timer.timeout.connect(self._filter_list)
        self._ui_edit.textChanged.connect(self._text_edited)
        self._ui_buttons.button(QDialogButtonBox.Ok).clicked.connect(self._apply_filter)
        self._ui_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self._cancel_filter)

    def save_state(self):
        """Saves the state of the FilterCheckboxListModel."""
        self._filter_state = self._filter_model.get_selected()
        if self._filter_model._show_empty:
            self._filter_empty_state = self._filter_model._empty_selected
        else:
            self._filter_empty_state = False

    def reset_state(self):
        """Sets the state of the FilterCheckboxListModel to saved state."""
        self._filter_model.set_selected(self._filter_state, self._filter_empty_state)

    def clear_filter(self):
        """Selects all items in FilterCheckBoxListModel."""
        self._filter_model.reset_selection()
        self.save_state()

    def has_filter(self):
        """Returns true if any item is filtered in FilterCheckboxListModel false otherwise."""
        return not self._filter_model._all_selected

    def set_filter_list(self, data):
        """Sets the list of items to filter."""
        self._filter_state = set(data)
        if self._filter_model._show_empty:
            self._filter_empty_state = True
        else:
            self._filter_empty_state = False
        self._filter_model.set_list(self._filter_state)

    def _apply_filter(self):
        """Apply current filter and save state."""
        self._filter_model.apply_filter()
        self.save_state()
        self._ui_edit.setText('')
        self.okPressed.emit()

    def _cancel_filter(self):
        """Cancel current edit of filter and set the state to the stored state."""
        self._filter_model.remove_filter()
        self.reset_state()
        self._ui_edit.setText('')
        self.cancelPressed.emit()

    def _filter_list(self):
        """Filter list with current text."""
        self._filter_model.set_filter(self._search_text)

    def _text_edited(self, new_text):
        """Callback for edit text, starts/restarts timer.
        Start timer after text is edited, restart timer if text
        is edited before last time out.
        """
        self._search_text = new_text
        self._search_timer.start(self.search_delay)


class ZoomWidget(QWidget):
    """A widget for a QWidgetAction providing zoom actions for a graph view.

    Attributes
        parent (QWidget): the widget's parent
    """
    minus_pressed = Signal(name="minus_pressed")
    plus_pressed = Signal(name="plus_pressed")
    reset_pressed = Signal(name="reset_pressed")

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.option = QStyleOptionMenuItem()
        zoom_action = QAction("Zoom")
        QMenu(parent).initStyleOption(self.option, zoom_action)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        tool_bar = QToolBar(self)
        tool_bar.setFixedHeight(self.option.rect.height())
        minus_action = tool_bar.addAction("-")
        reset_action = tool_bar.addAction("Reset")
        plus_action = tool_bar.addAction("+")
        layout.addSpacing(self.option.rect.width())
        layout.addWidget(tool_bar)
        minus_action.setToolTip("Zoom out")
        reset_action.setToolTip("Reset zoom")
        plus_action.setToolTip("Zoom in")
        minus_action.triggered.connect(lambda x: self.minus_pressed.emit())
        plus_action.triggered.connect(lambda x: self.plus_pressed.emit())
        reset_action.triggered.connect(lambda x: self.reset_pressed.emit())

    def paintEvent(self, event):
        """Overridden method."""
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_MenuItem, self.option, painter)
        super().paintEvent(event)
