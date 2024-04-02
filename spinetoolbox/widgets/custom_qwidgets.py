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

"""Custom QWidgets for Filtering and Zooming."""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
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
    QPushButton,
    QSpinBox,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QEvent, QRect
from PySide6.QtGui import (
    QPainter,
    QFontMetrics,
    QKeyEvent,
    QFontDatabase,
    QFont,
    QIntValidator,
    QKeySequence,
    QAction,
    QUndoStack,
)
from .custom_qtextbrowser import MonoSpaceFontTextBrowser
from .select_database_items import SelectDatabaseItems
from ..helpers import format_log_message


class ElidedTextMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_text = ""
        self.elided_mode = Qt.ElideLeft

    def setText(self, text):
        self._update_text(text)

    def _update_text(self, text):
        self._full_text = text
        self._set_text_elided()

    def _set_text_elided(self, width=None):
        if width is None:
            width = self.rect().width()
        text_width = width - self._elided_offset() - self.fontMetrics().averageCharWidth()
        elided_text = self.fontMetrics().elidedText(self._full_text, self.elided_mode, text_width)
        super().setText(elided_text)

    def _elided_offset(self):
        return 0

    def text(self):
        return self._full_text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_text_elided(event.size().width())


class UndoRedoMixin:
    def keyPressEvent(self, e):
        """Overridden to catch and pass on the Undo and Redo commands when this line edit has the focus.

        Args:
            e (QKeyEvent): Event
        """
        undo_stack = self.nativeParentWidget().findChild(QUndoStack)
        if undo_stack is None:
            super().keyPressEvent(e)
            return
        if e.matches(QKeySequence.Undo):
            undo_stack.undo()
        elif e.matches(QKeySequence.Redo):
            undo_stack.redo()
        else:
            super().keyPressEvent(e)


class FilterWidget(QWidget):
    """Filter widget class."""

    okPressed = Signal()
    cancelPressed = Signal()

    def __init__(self, parent, make_filter_model, *args, **kwargs):
        """Init class.

        Args:
            parent (QWidget, optional): parent widget
            make_filter_model (Callable): callable that constructs the filter model
            *args: arguments forwarded to ``make_filter_model``
            **kwargs: keyword arguments forwarded to ``make_filter_model``
        """
        super().__init__(parent)
        # parameters
        self._filter_state = set()
        self._filter_empty_state = None
        self._search_text = ""
        self.search_delay = 200
        # create ui elements
        self._ui_vertical_layout = QVBoxLayout(self)
        self._ui_list = QListView()
        self._ui_edit = QLineEdit()
        self._ui_edit.setPlaceholderText("Search")
        self._ui_edit.setClearButtonEnabled(True)
        self._ui_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self._ui_vertical_layout.addWidget(self._ui_edit)
        self._ui_vertical_layout.addWidget(self._ui_list)
        self._ui_vertical_layout.addWidget(self._ui_buttons)
        self._search_timer = QTimer()  # Used to limit search so it doesn't search when typing
        self._search_timer.setSingleShot(True)
        self._filter_model = make_filter_model(*args, **kwargs)
        self._filter_model.setParent(self)
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)
        self.connect_signals()

    # For tests
    def set_filter_list(self, items):
        self._filter_state = items
        self._filter_model.set_list(self._filter_state)

    def connect_signals(self):
        self._ui_list.clicked.connect(self._filter_model._handle_index_clicked)
        self._search_timer.timeout.connect(self._filter_list)
        self._ui_edit.textChanged.connect(self._text_edited)
        self._ui_buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._apply_filter)
        self._ui_buttons.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self._cancel_filter)

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

    def _apply_filter(self):
        """Apply current filter and save state."""
        self._filter_model.apply_filter()
        self.save_state()
        self._ui_edit.setText("")
        self.okPressed.emit()

    def _cancel_filter(self):
        """Cancel current edit of filter and set the state to the stored state."""
        self._filter_model.remove_filter()
        self.reset_state()
        self._ui_edit.setText("")
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
        for menu in self.parent().findChildren(QMenu):
            if menu.isVisible():
                menu.hide()
        self.parent().update(self.parent().geometry())


class ToolBarWidgetAction(CustomWidgetAction):
    """An action with a tool bar.

    Attributes:
        tool_bar (QToolBar)
    """

    def __init__(self, text, parent=None, compact=False):
        """Class constructor.

        Args:
            parent (QMenu): the widget's parent
        """
        super().__init__(parent)
        self._parent_key_press_event = None
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

    def __init__(self, text, parent=None, io_files=None):
        """Class constructor.

        Args:
            text (str)
            parent (QWidget): the widget's parent
        """
        super().__init__(parent)
        self._text = text
        self._parent = parent
        layout = QHBoxLayout(self)
        if io_files:
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            layout.setContentsMargins(30, 0, 0, 0)
        layout.setSpacing(0)
        self.tool_bar = _MenuToolBar(self)
        layout.addStretch()
        layout.addWidget(self.tool_bar)
        icon_extent = qApp.style().pixelMetric(
            QStyle.PixelMetric.PM_SmallIconSize
        )  # pylint: disable=undefined-variable
        self.tool_bar.setIconSize(QSize(icon_extent, icon_extent))
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)


class ToolBarWidget(ToolBarWidgetBase):
    def __init__(self, text, parent=None, io_files=None):
        super().__init__(text, parent, io_files)
        spacing = self.fontMetrics().horizontalAdvance(self._text)  # pylint: disable=undefined-variable
        self.layout().insertSpacing(0, spacing)


class MenuItemToolBarWidget(ToolBarWidgetBase):
    """A menu item with a toolbar on the right."""

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
        icon_width = qApp.style().pixelMetric(
            QStyle.PixelMetric.PM_ToolBarIconSize
        )  # pylint: disable=undefined-variable
        spacing = text_width + 3 * icon_width
        self.option.rect.setWidth(spacing)
        self.layout().insertSpacing(0, spacing)

    def paintEvent(self, event):
        """Draws the menu item, then calls the super() method to draw the tool bar."""
        painter = QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_MenuItem, self.option, painter)
        super().paintEvent(event)


class _MenuToolBar(QToolBar):
    """A custom tool bar for ``MenuItemToolBarWidget``."""

    enabled_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._enabled = True
        self._focus_widget = None
        self._buttons = []
        self._frames = []

    def _align_buttons(self):
        """Align all buttons to bottom so frames look good."""
        layout = self.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() in self._buttons:
                item.setAlignment(Qt.AlignBottom)

    def add_frame(self, left, right, title):
        """Add frame around given actions, with given title.

        Args:
            left (QAction)
            right (QAction)
            title (str)
        """
        left = self.widgetForAction(left)
        right = self.widgetForAction(right)
        if None in (left, right):
            return
        self._frames.append((left, right, title))

    def is_enabled(self):
        return self._enabled

    def addActions(self, actions):
        """Overriden method to customize tool buttons."""
        super().addActions(actions)
        for action in actions:
            self._setup_action_button(action)
        self._align_buttons()

    def addAction(self, *args, **kwargs):
        """Overriden method to customize the tool button."""
        result = super().addAction(*args, **kwargs)
        action = result if result is not None else args[0]
        self._setup_action_button(action)
        self._align_buttons()
        return result

    def sizeHint(self):
        """Make room for frames if needed."""
        size = super().sizeHint()
        if self._frames:
            size.setHeight(size.height() + self.fontMetrics().height())
        return size

    def paintEvent(self, ev):
        """Paint the frames."""
        super().paintEvent(ev)
        if not self._frames:
            return
        painter = QPainter(self)
        fm = self.fontMetrics()
        for left, right, title in self._frames:
            top_left = left.geometry().topLeft()
            bottom_right = right.geometry().bottomRight()
            rect = QRect(top_left, bottom_right).adjusted(-1, -fm.height() / 2, 1, 1)
            painter.setPen(Qt.gray)
            painter.drawRoundedRect(rect, 1, 1)
            title_rect = fm.boundingRect(title).adjusted(-4, 0, 4, 0)
            title_rect.moveCenter(rect.center())
            title_rect.moveTop(rect.top() - fm.height() / 2)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawRect(title_rect)
            painter.setPen(Qt.black)
            painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignTop, title)
        painter.end()

    def _setup_action_button(self, action):
        """Customizes the QToolButton associated with given action:
            1. Makes sure that the text honors the action's mnemonics.
            2. Installs this as event filter on the button (see ``self.eventFilter()``).

        Must be called everytime an action is added to the tool bar.

        Args:
            action (QAction): Action to set up
        """
        button = self.widgetForAction(action)
        if not button:
            return
        self._buttons.append(button)
        button.setText(action.text())
        action.changed.connect(lambda action=action, button=button: button.setText(action.text()))
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

    class _ExecutionManager:
        """A descriptor that stores a QProcessExecutionManager.
        When ``execution_finished`` is emitted, it shows the button to copy the process log.
        """

        public_name = None
        private_name = None

        def __set_name__(self, owner, name):
            self.public_name = name
            self.private_name = "_" + name

        def __get__(self, obj, objtype=None):
            return getattr(obj, self.private_name)

        def __set__(self, obj, value):
            setattr(obj, self.private_name, value)
            try:
                value.execution_finished.connect(lambda _: obj.widget_copy.show())
            except AttributeError:
                pass

    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)
    msg_success = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)

    _exec_mngr = _ExecutionManager()

    def __init__(self, parent):
        super().__init__(parent)
        self._log = MonoSpaceFontTextBrowser(self)
        self._exec_mngr = None
        self._successful = False
        layout = QVBoxLayout(self)
        layout.addWidget(self._log)
        self.widget_copy = QWidget()
        self.widget_copy.hide()
        self._button_copy = QPushButton("Copy log")
        self._label_copy = QLabel("Log copied to clipboard.")
        self._label_copy.hide()
        layout_copy = QHBoxLayout(self.widget_copy)
        layout_copy.addWidget(self._button_copy)
        layout_copy.addWidget(self._label_copy)
        layout_copy.addStretch()
        layout.addWidget(self.widget_copy)
        self._connect_signals()

    def _connect_signals(self):
        self.msg.connect(self._add_msg)
        self.msg_warning.connect(self._add_msg_warning)
        self.msg_error.connect(self._add_msg_error)
        self.msg_success.connect(self._add_msg_success)
        self.msg_proc.connect(self._add_msg)
        self.msg_proc_error.connect(self._add_msg_error)
        self._button_copy.clicked.connect(self._handle_copy_clicked)

    @Slot(bool)
    def _handle_copy_clicked(self, _=False):
        self._label_copy.show()
        qApp.clipboard().setText(self._log.toPlainText())  # pylint: disable=undefined-variable

    @Slot(str)
    def _add_msg(self, msg):
        self._log.append(format_log_message("msg", msg, show_datetime=False))

    @Slot(str)
    def _add_msg_warning(self, msg):
        self._log.append(format_log_message("msg_warning", msg, show_datetime=False))

    @Slot(str)
    def _add_msg_error(self, msg):
        self._log.append(format_log_message("msg_error", msg, show_datetime=False))

    @Slot(str)
    def _add_msg_success(self, msg):
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
        font = QFont("Font Awesome 5 Free Solid")
        button.setFont(font)
        button.setText("\uf0c5")
        button.setToolTip("Copy text")
        layout.addSpacing(20)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        # pylint: disable=undefined-variable
        button.clicked.connect(lambda _=False, le=line_edit: qApp.clipboard().setText(le.text()))


class ElidedLabel(ElidedTextMixin, QLabel):
    """A QLabel with elided text."""


class HorizontalSpinBox(QToolBar):
    valueChanged = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validator = QIntValidator()
        self._value = None
        self._line_edit = QLineEdit(self)
        width = self.fontMetrics().horizontalAdvance("99") + 12
        self._line_edit.setFixedWidth(width)
        self._line_edit.setAlignment(Qt.AlignCenter)
        self._line_edit.textEdited.connect(self.setValue)
        self._line_edit.setValidator(self._validator)
        self.addAction("-", self._dec_value)
        self.addWidget(self._line_edit)
        self.addAction("+", self._inc_value)
        self.setStyleSheet("margin: 0px")

    def value(self):
        return self._value

    def setMinimum(self, minimum):
        try:
            self._validator.setBottom(minimum)
        except TypeError:
            pass

    def setMaximum(self, maximum):
        try:
            self._validator.setTop(maximum)
        except TypeError:
            pass

    @Slot(str)
    def setValue(self, value, strict=False):
        try:
            value = int(value)
        except ValueError:
            return
        if value == self._value:
            return
        acceptable = self._validator.validate(str(value), 0)[0] == QIntValidator.State.Acceptable
        if strict and not acceptable:
            return
        self._line_edit.setText(str(value))
        self._value = value
        if acceptable:
            self.valueChanged.emit(self._value)

    def _dec_value(self):
        self.setValue(self._value - 1, strict=True)
        self._focus_line_edit()

    def _inc_value(self):
        self.setValue(self._value + 1, strict=True)
        self._focus_line_edit()

    def _focus_line_edit(self):
        self._line_edit.selectAll()
        self._line_edit.setFocus()


class PropertyQSpinBox(UndoRedoMixin, QSpinBox):
    """A spinbox where undo and redo key strokes apply to the project."""


class SelectDatabaseItemsDialog(QDialog):
    """Dialog that lets selecting database items."""

    _warn_checked_non_data_items = True
    _ok_button_can_be_disabled = True

    def __init__(self, checked_states, ok_button_text=None, parent=None):
        """
        Args:
            checked_states (dict, optional): checked states for each item
            ok_button_text (str, optional): alternative label for the OK button
            parent (QWidget, optional): parent widget
        """
        from ..ui.select_database_items_dialog import Ui_Dialog  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self.setWindowTitle("Database purge settings")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._ui = Ui_Dialog()
        self._ui.setupUi(self)
        if ok_button_text is not None:
            self._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(ok_button_text)
        self._item_check_boxes_widget = SelectDatabaseItems(checked_states, self)
        self._ui.root_layout.insertWidget(0, self._item_check_boxes_widget)
        self._item_check_boxes_widget.checked_state_changed.connect(self._handle_check_box_state_changed)

    def show(self):
        """Sets the OK button enabled before showing the dialog"""
        self._handle_check_box_state_changed(False)
        super().show()

    def get_checked_states(self):
        """Returns current item checked states.

        Returns:
            dict: mapping from database item name to checked flag
        """
        return self._item_check_boxes_widget.checked_states()

    @Slot(int)
    def _handle_check_box_state_changed(self, _checked):
        if self._ok_button_can_be_disabled:
            self._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
                self._item_check_boxes_widget.any_checked()
            )
        if self._warn_checked_non_data_items:
            if self._item_check_boxes_widget.any_structural_item_checked():
                self._ui.warning_label.setText("Warning! Structural data items selected.")
            else:
                self._ui.warning_label.clear()


class PurgeSettingsDialog(SelectDatabaseItemsDialog):
    _ok_button_can_be_disabled = False
