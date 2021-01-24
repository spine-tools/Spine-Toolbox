######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from PySide2.QtCore import Qt, QTimer, Signal, Slot, QSize
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


class ToolbarWidgetAction(CustomWidgetAction):
    def __init__(self, text, parent=None, compact=False):
        """Class constructor.

        Args:
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        widget = ActionToolbarWidget(text, parent=parent, compact=compact)
        self.setDefaultWidget(widget)
        self.tool_bar = widget.tool_bar


class _MnemonicsToolBar(QToolBar):
    """Fixes action texts to respect mnemonics (e.g., &Edit), by explicitly re-setting the text to the button.

    Ideally we'd watch for ``self.actionEvent()`` sent with ``QEvent.ActionChanged``, but

        AttributeError: 'PySide2.QtGui.QActionEvent' object has no attribute 'action'
    """

    def addActions(self, actions):
        super().addActions(actions)
        for action in actions:
            self._fix_action_text(action)

    def addAction(self, *args, **kwargs):
        result = super().addAction(*args, **kwargs)
        action = result if result is not None else args[0]
        self._fix_action_text(action)
        return result

    def _fix_action_text(self, action):
        button = self.widgetForAction(action)
        button.setText(action.text())
        action.changed.connect(lambda action=action: button.setText(action.text()))


class ActionToolbarWidget(QWidget):
    def __init__(self, text, parent=None, compact=False):
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
        self.tool_bar = _MnemonicsToolBar(self)
        if compact:
            self.tool_bar.setFixedHeight(self.option.rect.height())
        extent = qApp.style().pixelMetric(QStyle.PM_SmallIconSize)  # pylint: disable=undefined-variable
        self.tool_bar.setIconSize(QSize(extent, extent))
        layout.addSpacing(self.option.rect.width())
        layout.addStretch()
        layout.addWidget(self.tool_bar)
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

    def paintEvent(self, event):
        """Overridden method."""
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_MenuItem, self.option, painter)
        super().paintEvent(event)


class TitleWidgetAction(CustomWidgetAction):
    """
    A widget action for adding titled sections to menus.
    """

    # NOTE: I'm aware of QMenu.addSection(), but it doesn't seem to work on all platforms?

    H_MARGIN = 5
    V_MARGIN = 2

    def __init__(self, title, parent=None):
        super().__init__(parent)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(self.H_MARGIN, self.V_MARGIN, self.H_MARGIN, self.V_MARGIN)
        layout.setSpacing(self.V_MARGIN)
        label = QLabel(title, widget)
        fm = QFontMetrics(label.font())
        label.setFixedWidth(fm.horizontalAdvance(title))
        self._add_line(widget, layout)
        layout.addWidget(label)
        self._add_line(widget, layout)
        self.setDefaultWidget(widget)

    @staticmethod
    def _add_line(widget, layout):
        line = QFrame(widget)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
