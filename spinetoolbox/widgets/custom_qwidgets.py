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
    QLabel,
    QFrame,
)
from PySide2.QtCore import QTimer, Signal, Slot
from PySide2.QtGui import QPainter, QFontMetrics
from ..mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel


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
        self._ui_list.clicked.connect(self._filter_model._handle_index_clicked)
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
        self._filter_model = SimpleFilterCheckboxListModel(self, show_empty=show_empty)
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)
        self.connect_signals()


class CustomWidgetAction(QWidgetAction):
    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        self.hovered.connect(self._handle_hovered)

    @Slot()
    def _handle_hovered(self):
        """Hides other menus that might be shown in the parent widget and repaints it.
        This is to emulate the behavior of QAction."""
        for menu in self.parentWidget().findChildren(QMenu):
            if menu.isVisible():
                menu.hide()
        self.parentWidget().update(self.parentWidget().geometry())


class TitleWidgetAction(CustomWidgetAction):
    """
    A widget action for adding titled sections to menus.
    """

    # NOTE: I'm aware of QMenu.addSection(), but it doesn't seem to work on all platforms?

    H_MARGIN = 6
    V_MARGIN = 2

    def __init__(self, title, parent=None):
        super().__init__(parent)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(self.H_MARGIN, self.V_MARGIN, self.H_MARGIN, self.V_MARGIN)
        layout.setSpacing(self.V_MARGIN)
        label = QLabel(title, widget)
        fm = QFontMetrics(label.font())
        label.setFixedWidth(fm.width(title))
        lines = QFrame(widget), QFrame(widget)
        for line in lines:
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)
        layout.insertWidget(1, label)
        self.setDefaultWidget(widget)


class ZoomWidgetAction(CustomWidgetAction):
    """A widget action with plus, minus, and reset buttons.
    Used to create zoom actions for menus.
    """

    minus_pressed = Signal()
    plus_pressed = Signal()
    reset_pressed = Signal()

    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        actions = {"-": "Zoom out", "Reset": "Reset zoom", "+": "Zoom in"}
        widget = ActionToolbarWidget("Zoom", actions, parent)
        self.setDefaultWidget(widget)
        widget.action_triggered.connect(self._handle_action_triggered)

    @Slot(str)
    def _handle_action_triggered(self, name):
        {"+": self.plus_pressed, "-": self.minus_pressed, "Reset": self.reset_pressed}[name].emit()


class RotateWidgetAction(CustomWidgetAction):
    """A widget action with rotate left and right buttons.
    Used to create rotate actions for menus.
    """

    clockwise_pressed = Signal()
    anticlockwise_pressed = Signal()

    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        actions = {"\u2b6f": "Rotate counter-clockwise", "\u2b6e": "Rotate clockwise"}
        widget = ActionToolbarWidget("Rotate", actions, parent)
        self.setDefaultWidget(widget)
        widget.action_triggered.connect(self._handle_action_triggered)

    @Slot(str)
    def _handle_action_triggered(self, name):
        {"\u2b6f": self.anticlockwise_pressed, "\u2b6e": self.clockwise_pressed}[name].emit()


class ActionToolbarWidget(QWidget):

    action_triggered = Signal(str)

    def __init__(self, text, actions, parent=None):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        self.option = QStyleOptionMenuItem()
        action = QAction(text)
        QMenu(parent).initStyleOption(self.option, action)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        tool_bar = QToolBar(self)
        tool_bar.setFixedHeight(self.option.rect.height())
        layout.addSpacing(self.option.rect.width())
        layout.addStretch()
        layout.addWidget(tool_bar)
        for name, tool_tip in actions.items():
            action = tool_bar.addAction(name)
            action.setToolTip(tool_tip)
            action.triggered.connect(lambda x=False, name=name: self.action_triggered.emit(name))

    def paintEvent(self, event):
        """Overridden method."""
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_MenuItem, self.option, painter)
        super().paintEvent(event)
