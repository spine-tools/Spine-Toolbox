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
Custom QWidgets for Filtering and Zooming.

:author: P. Vennström (VTT)
:date:   4.12.2018
"""

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
    QAction,
    QStyle,
    QToolBar,
    QStyleOptionMenuItem,
    QListView,
    QLineEdit,
    QDialogButtonBox,
    QWidgetAction,
)
from PySide2.QtCore import QTimer, Signal, Slot
from PySide2.QtGui import QPainter
from ..mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel, DBItemFilterCheckboxListModel


class FilterWidgetBase(QWidget):
    """Filter widget class."""

    okPressed = Signal()
    cancelPressed = Signal()

    def __init__(self, parent):
        """Init class.

        Args:
            parent (QWidget)
        """
        super().__init__(parent)
        # parameters
        self._filter_state = set()
        self._filter_empty_state = None
        self._search_text = ''
        self.search_delay = 200

        # create ui elements
        self._ui_vertical_layout = QVBoxLayout(self)
        self._ui_list = QListView()
        self._ui_edit = QLineEdit()
        self._ui_edit.setPlaceholderText('Search')
        self._ui_edit.setClearButtonEnabled(True)
        self._ui_buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._ui_vertical_layout.addWidget(self._ui_edit)
        self._ui_vertical_layout.addWidget(self._ui_list)
        self._ui_vertical_layout.addWidget(self._ui_buttons)

        # add models
        self._search_timer = QTimer()  # Used to limit search so it doesn't search when typing
        self._search_timer.setSingleShot(True)

        self._filter_model = None

    def connect_signals(self):
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
        self._filter_state = list(data)
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


class SimpleFilterWidget(FilterWidgetBase):
    def __init__(self, parent, show_empty=True):
        """Init class.

        Args:
            parent (QWidget)
        """
        super().__init__(parent)
        self._filter_model = SimpleFilterCheckboxListModel(parent, show_empty=show_empty)
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)
        self.connect_signals()


class DBItemFilterWidget(FilterWidgetBase):
    def __init__(self, parent, query_method, source_model=None, show_empty=True):
        """Init class.

        Args:
            parent (DataStoreForm)
            query_method (method): the method to query data
            source_model (CompoundParameterModel, optional): a model to lazily get data from
        """
        super().__init__(parent)
        self._filter_model = DBItemFilterCheckboxListModel(
            self, query_method, source_model=source_model, show_empty=show_empty
        )
        self._filter_model.set_list(self._filter_state)
        self.connect_signals()

    def set_model(self):
        self._ui_list.setModel(self._filter_model)


class ZoomWidgetAction(QWidgetAction):
    """A zoom widget action."""

    minus_pressed = Signal()
    plus_pressed = Signal()
    reset_pressed = Signal()

    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        zoom_widget = ZoomWidget(parent)
        self.setDefaultWidget(zoom_widget)
        zoom_widget.minus_pressed.connect(self.minus_pressed)
        zoom_widget.plus_pressed.connect(self.plus_pressed)
        zoom_widget.reset_pressed.connect(self.reset_pressed)
        self.hovered.connect(self._handle_hovered)

    @Slot()
    def _handle_hovered(self):
        """Runs when the zoom widget action is hovered. Hides other menus under the parent widget
        which are being shown. This is the default behavior for hovering QAction,
        but for some reason it's not the case for hovering QWidgetAction."""
        for menu in self.parentWidget().findChildren(QMenu):
            if menu.isVisible():
                menu.hide()


class ZoomWidget(QWidget):

    minus_pressed = Signal()
    plus_pressed = Signal()
    reset_pressed = Signal()

    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
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
