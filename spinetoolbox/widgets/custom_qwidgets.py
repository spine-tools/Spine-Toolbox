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
    QWizardPage,
    QToolButton,
)
from PySide2.QtCore import Qt, QTimer, Signal, Slot, QSize, QEvent
from PySide2.QtGui import QPainter, QFontMetrics, QKeyEvent, QFontDatabase, QFont
from ..mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from .custom_qtextbrowser import MonoSpaceFontTextBrowser
from ..helpers import format_log_message


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
    """A QWidgetAction with custom hovering."""

    def __init__(self, parent=None):
        """Class constructor.

        Args:
            parent (QMenu): the widget's parent
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


class ToolBarWidgetAction(CustomWidgetAction):
    """An action with a tool bar.

    Attributes:
        tool_bar (QToolBar)
    """

    _parent_key_press_event = None

    def __init__(self, text, parent=None, compact=False):
        """Class constructor.

        Args:
            parent (QMenu): the widget's parent
        """
        super().__init__(parent)
        widget = MenuItemToolBarWidget(text, parent=parent, compact=compact)
        self.setDefaultWidget(widget)
        self.tool_bar = widget.tool_bar
        self.tool_bar.enabled_changed.connect(self.setEnabled)
        parent.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.KeyPress:
            self._parent_key_press_event = QKeyEvent(ev.type(), ev.key(), ev.modifiers())
        return super().eventFilter(obj, ev)

    @Slot()
    def _handle_hovered(self):
        super()._handle_hovered()
        if self._parent_key_press_event:
            if self.tool_bar.is_enabled():
                self.tool_bar.keyPressEvent(self._parent_key_press_event)
            else:
                self.parent().keyPressEvent(self._parent_key_press_event)
            self._parent_key_press_event = None


class ToolBarWidgetBase(QWidget):
    """A toolbar on the right, with enough space to print a text beneath.

    Attributes:
        tool_bar (QToolBar)
    """

    def __init__(self, text, parent=None):
        """Class constructor.

        Args:
            text (str)
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        self._text = text
        self._parent = parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.tool_bar = _MenuToolBar(self)
        layout.addStretch()
        layout.addWidget(self.tool_bar)
        icon_extent = qApp.style().pixelMetric(QStyle.PM_SmallIconSize)  # pylint: disable=undefined-variable
        self.tool_bar.setIconSize(QSize(icon_extent, icon_extent))
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)


class ToolBarWidget(ToolBarWidgetBase):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        spacing = qApp.fontMetrics().horizontalAdvance(self._text)  # pylint: disable=undefined-variable
        self.layout().insertSpacing(0, spacing)


class MenuItemToolBarWidget(ToolBarWidgetBase):
    """A menu item with a toolbar on the right.

    Attributes:
        tool_bar (QToolBar)
    """

    def __init__(self, text, parent=None, compact=False):
        """Class constructor.

        Args:
            text (str)
            parent (QWidget): the widget's parent
            compact (bool): if True, the widget uses the minimal space
        """
        super().__init__(text, parent)
        self.option = QStyleOptionMenuItem()
        action = QAction(self._text)
        QMenu(self._parent).initStyleOption(self.option, action)
        if compact:
            self.tool_bar.setFixedHeight(self.option.rect.height())
        text_width = self.option.fontMetrics.horizontalAdvance(self._text)
        icon_widht = qApp.style().pixelMetric(QStyle.PM_ToolBarIconSize)  # pylint: disable=undefined-variable
        spacing = text_width + 3 * icon_widht
        self.layout().insertSpacing(0, spacing)

    def paintEvent(self, event):
        """Draws the menu item, then calls the super() method to draw the tool bar."""
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_MenuItem, self.option, painter)
        super().paintEvent(event)


class _MenuToolBar(QToolBar):
    """A custom tool bar for ``MenuItemToolBarWidget``."""

    enabled_changed = Signal(bool)
    _enabled = True
    _focus_widget = None

    def is_enabled(self):
        return self._enabled

    def addActions(self, actions):
        """Overriden method to customize tool buttons."""
        super().addActions(actions)
        for action in actions:
            self._setup_action_button(action)

    def addAction(self, *args, **kwargs):
        """Overriden method to customize the tool button."""
        result = super().addAction(*args, **kwargs)
        action = result if result is not None else args[0]
        self._setup_action_button(action)
        return result

    def _setup_action_button(self, action):
        """Customizes the QToolButton associated with given action:
            1. Makes sure that the text honores the action's mnemonics.
            2. Installs this as event filter on the button (see ``self.eventFilter()``).

        Must be called everytime an action is added to the tool bar.

        Args:
            QAction
        """
        button = self.widgetForAction(action)
        if not button:
            return
        button.setText(action.text())
        action.changed.connect(lambda action=action: button.setText(action.text()))
        button.installEventFilter(self)

    def actionEvent(self, ev):
        """Updates ``self._enabled``: True if at least one non-separator action is enabled, False otherwise.
        Emits ``self.enabled_changed`` accordingly.
        """
        super().actionEvent(ev)
        new_enabled = any(not a.isSeparator() and a.isEnabled() for a in self.actions())
        if new_enabled != self._enabled:
            self.enabled_changed.emit(new_enabled)
        self._enabled = new_enabled

    def eventFilter(self, obj, ev):
        """Installed on each action's QToolButton.
        Ignores Up and Down key press events, so they are handled by the toolbar for custom navigation.
        """
        if ev.type() == QEvent.KeyPress:
            if ev.key() in (Qt.Key_Left, Qt.Key_Right):
                ev.accept()
                return True
            if ev.key() in (Qt.Key_Up, Qt.Key_Down):
                ev.ignore()
                return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, ev):
        """Navigates over the tool bar buttons."""
        if ev.key() in (Qt.Key_Left, Qt.Key_Right):  # FIXME
            ev.ignore()
            return
        if ev.key() in (Qt.Key_Up, Qt.Key_Down):
            widgets = [self.widgetForAction(a) for a in self.actions() if not a.isSeparator() and a.isEnabled()]
            if self._focus_widget not in widgets:
                self._focus_widget = None
            if self._focus_widget is None:
                next_index = 0 if ev.key() == Qt.Key_Down else len(widgets) - 1
            else:
                index = widgets.index(self._focus_widget)
                next_index = index + 1 if ev.key() == Qt.Key_Down else index - 1
            if 0 <= next_index < len(widgets):
                self._focus_widget = widgets[next_index]
                self._focus_widget.setFocus()
                return
            self._focus_widget = None
            ev.ignore()
        super().keyPressEvent(ev)

    def hideEvent(self, ev):
        super().hideEvent(ev)
        if self._focus_widget is not None:
            self._focus_widget.clearFocus()
            self._focus_widget = None


class TitleWidgetAction(CustomWidgetAction):
    """A titled separator."""

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

    def isSeparator(self):  # pylint: disable=no-self-use
        return True


class WrapLabel(QLabel):
    """A QLabel that always wraps text."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)


class HyperTextLabel(WrapLabel):
    """A QLabel that supports hyperlinks."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setOpenExternalLinks(True)


class QWizardProcessPage(QWizardPage):
    """A QWizards page with a log. Useful for pages that need to capture the output of a process."""

    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)
    msg_success = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self._log = MonoSpaceFontTextBrowser(self)
        self._exec_mngr = None
        self._successful = False
        layout = QVBoxLayout(self)
        layout.addWidget(self._log)
        self._connect_signals()

    def _connect_signals(self):
        self.msg.connect(self._add_msg)
        self.msg_warning.connect(self._add_msg_warning)
        self.msg_error.connect(self._add_msg_error)
        self.msg_success.connect(self._add_msg_succes)
        self.msg_proc.connect(self._add_msg)
        self.msg_proc_error.connect(self._add_msg_error)

    def _add_msg(self, msg):
        self._log.append(format_log_message("msg", msg, show_datetime=False))

    def _add_msg_warning(self, msg):
        self._log.append(format_log_message("msg_warning", msg, show_datetime=False))

    def _add_msg_error(self, msg):
        self._log.append(format_log_message("msg_error", msg, show_datetime=False))

    def _add_msg_succes(self, msg):
        self._log.append(format_log_message("msg_success", msg, show_datetime=False))

    def isComplete(self):
        return self._exec_mngr is None

    def cleanupPage(self):
        super().cleanupPage()
        if self._exec_mngr is not None:
            self._exec_mngr.stop_execution()
        self.msg_error.emit("Aborted by the user")


class LabelWithCopyButton(QWidget):
    """A read only QLabel with a QToolButton that copies the text to clipboard."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        line_edit = QLineEdit(text)
        line_edit.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        line_edit.setFont(font)
        button = QToolButton()
        font = QFont('Font Awesome 5 Free Solid')
        button.setFont(font)
        button.setText("\uf0c5")
        button.setToolTip("Copy text")
        layout.addSpacing(20)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        # pylint: disable=undefined-variable
        button.clicked.connect(lambda _=False, le=line_edit: qApp.clipboard().setText(le.text()))
