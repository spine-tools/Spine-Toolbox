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

from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
from PySide2.QtCore import Qt, QRunnable, QObject, Signal, QThreadPool, Slot
from PySide2.QtWidgets import QPlainTextEdit
from PySide2.QtGui import QFontDatabase
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager


class PersistentConsoleLineEdit(QPlainTextEdit):
    def __init__(self, block, parent):
        super().__init__(parent)
        self.block = block
        self.setFont(parent.font())
        self.setUndoRedoEnabled(False)
        self.document().setDocumentMargin(0)
        self.setFixedHeight(self.fontMetrics().height())
        self.setFixedWidth(self.parent().width())
        cursor_width = self.fontMetrics().horizontalAdvance("x")
        self.setCursorWidth(cursor_width)
        self.setTabStopDistance(4 * cursor_width)
        self.horizontalScrollBar().hide()
        self.verticalScrollBar().hide()
        self._highlighter = CustomSyntaxHighlighter(self)
        self._highlighter.setDocument(self.document())
        self._highlighter.set_style(parent.style())
        self._setup_lexer()

    def _setup_lexer(self):
        try:
            self._highlighter.lexer = get_lexer_by_name(self.parent().language())
            self._highlighter.rehighlight()
        except ClassNotFound:
            pass

    def keyPressEvent(self, ev):
        input_, partial_input = self._get_current_input()
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.parent().issue_command(input_)
            return
        if ev.key() == Qt.Key_Up:
            self.parent().move_history(input_, 1)
            return
        if ev.key() == Qt.Key_Down:
            self.parent().move_history(input_, -1)
            return
        if ev.key() == Qt.Key_Tab and partial_input.strip():
            self.parent().autocomplete(input_, partial_input)
            return
        super().keyPressEvent(ev)

    def _get_current_input(self):
        """

        Returns:
            str: the complete input
            str: the input before the cursor
        """
        cursor = self.textCursor()
        input_ = self.toPlainText()
        partial_input = input_[: cursor.position()]
        return input_, partial_input


class PersistentConsoleWidget(QPlainTextEdit):
    """A widget to interact with a persistent process."""

    def __init__(self, toolbox, key, language, owner=None):
        """
        Args:
            toolbox (ToolboxUI)
            key (tuple): persistent process identifier
            language (str): for syntax highlighting and prompting, etc.
            owner (ProjectItemBase, optional): console owner
        """
        super().__init__(parent=toolbox)
        self._line_edit = None
        self._line_edits = []
        self._thread_pool = QThreadPool()
        self._toolbox = toolbox
        self._key = key
        self._language = language
        self._prompt, self._cont_prompt = self._make_prompts()
        self._history_index = 0
        self._history_item_zero = ""
        self.owners = {owner}
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self._style = get_style_by_name("monokai")
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {background_color}; color: {foreground_color}; border: 0}}"
        )
        self._add_first_prompt()
        self.setReadOnly(True)

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._language.capitalize()} Console - {self.owner_names}"

    @property
    def owner_names(self):
        return "&".join(x.name for x in self.owners if x is not None)

    def style(self):
        return self._style

    def language(self):
        return self._language

    def _make_prompts(self):
        return {
            "julia": (
                '<br><span style="color:green; font-weight: bold">julia></span> ',
                "<pre>" + len("julia> ") * " " + "</pre>",
            ),
            "python": (">>> ", "... "),
        }.get(self._language, ("$", " "))

    def reposition_line_edits(self):
        for le in self._line_edits:
            block = le.block
            top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            pos = le.pos()
            le.move(pos.x(), top)

    def focusInEvent(self, _ev):
        if self._line_edit is not None:
            self._line_edit.setFocus()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        for le in self._line_edits:
            le.setFixedWidth(ev.size().width())

    def paintEvent(self, ev):
        self.reposition_line_edits()
        super().paintEvent(ev)

    def move_history(self, input_, step):
        """Moves history.

        Args:
            input_ (str)
            step (int)
        """
        if self._history_index == 0:
            self._history_item_zero = input_
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        self._history_index += step
        if self._history_index < 1:
            self._history_index = 0
            history_item = self._history_item_zero
        else:
            history_item = engine_mngr.get_persistent_history_item(self._key, self._history_index)
        self._line_edit.setPlainText(history_item)
        cursor = self._line_edit.textCursor()
        cursor.movePosition(cursor.End)
        self._line_edit.setTextCursor(cursor)

    def autocomplete(self, input_, partial_input):
        """Autocompletes current text in the prompt (or print options if multiple matches).

        Args:
            input_ (str)
            partial_input (str)
        """
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        completions = engine_mngr.get_persistent_completions(self._key, partial_input)
        if len(completions) > 1:
            # Multiple options: Print them to stdout and add new prompt
            self.add_stdin(input_)
            self.add_stdout("\t\t".join(completions))
        elif completions:
            # Unique option: Autocomplet current line
            cursor = self._line_edit.textCursor()
            last_word = partial_input.split(" ")[-1]
            cursor.insertText(completions[0][len(last_word) :])

    def _freeze_current_line_edit(self):
        self._line_edit.setReadOnly(True)
        self._line_edit.setFocusPolicy(Qt.NoFocus)
        self._line_edit = None

    def issue_command(self, input_):
        """Issues command.

        Args:
            input_ (str)
        """
        self._freeze_current_line_edit()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        issuer = CommandIssuer(engine_server_address, self._key, input_)
        issuer.stdout_msg.connect(self.add_stdout)
        issuer.stderr_msg.connect(self.add_stderr)
        issuer.finished.connect(self._add_prompt)
        issuer.finished.connect(self._reset_history_index)
        self._thread_pool.start(issuer)

    def _reset_history_index(self):
        self._history_index = 0

    def _has_prompt(self):
        """Whether or not the console has a prompt. True most of the time, except when issuing a command.

        Returns:
            bool
        """
        return self._line_edit is not None

    def _scroll_to_bottom(self):
        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.setValue(vertical_scroll_bar.maximum())

    def _insert_html_before_prompt(self, html, with_prompt=False):
        """Inserts given html before the prompt. Used when adding input and output from external execution.

        Args:
            html (str)
        """
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        if self._has_prompt():
            cursor.movePosition(cursor.PreviousBlock)
            cursor.movePosition(cursor.EndOfBlock)
            cursor.insertBlock()
        elif cursor.block().text():
            cursor.insertBlock()
        if with_prompt:
            cursor.insertHtml(self._prompt)
            self.setTextCursor(cursor)
            line_edit = PersistentConsoleLineEdit(cursor.block(), self)
            self._line_edits.append(line_edit)
            line_edit.move(self.cursorRect().topLeft())
            line_edit.textCursor().insertHtml(html)
            line_edit.show()
            line_edit.setReadOnly(True)
            line_edit.setFocusPolicy(Qt.NoFocus)
        else:
            cursor.insertHtml(html)
        self._scroll_to_bottom()
        if self._has_prompt():
            cursor.movePosition(cursor.End)
            self.setTextCursor(cursor)
            self._line_edit.move(self.cursorRect().topLeft())

    def add_stdin(self, data):
        """Adds new prompt with data. Used when adding stdin from external execution.

        Args:
            data (str)
        """
        self._insert_html_before_prompt(data, with_prompt=True)

    def add_stdout(self, data):
        """Adds new line to stdout. Used when adding stdout from external execution.

        Args:
            data (str)
        """
        self._insert_html_before_prompt(data)

    def add_stderr(self, data):
        """Adds new line to stderr. Used when adding stderr from external execution.

        Args:
            data (str)
        """
        html = '<span style="color:red">' + data + "</span>"
        self._insert_html_before_prompt(html)

    def _add_first_prompt(self):
        self._add_prompt(first=True)

    def _add_prompt(self, is_complete=True, first=False):
        """Adds a prompt at the end of the document."""
        prompt = self._prompt if is_complete else self._cont_prompt
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        if cursor.block().text() or first:
            cursor.insertBlock()
        cursor.insertHtml(prompt)
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)
        self._line_edit = PersistentConsoleLineEdit(cursor.block(), self)
        self._line_edits.append(self._line_edit)
        self._line_edit.show()
        self._line_edit.move(self.cursorRect().topLeft())
        self._line_edit.setFocus()

    def contextMenuEvent(self, event):
        """Reimplemented to add two more actions: Restart, and Interrupt."""
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction("Restart", self._restart_persistent)
        menu.addAction("Interrupt", self._interrupt_persistent)
        menu.exec_(event.globalPos())

    @Slot(bool)
    def _restart_persistent(self, _=False):
        """Restarts underlying persistent process."""
        self.clear()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        restarter = Restarter(engine_server_address, self._key)
        restarter.finished.connect(self._add_first_prompt)
        self._thread_pool.start(restarter)

    @Slot(bool)
    def _interrupt_persistent(self, _=False):
        """Interrupts underlying persistent process."""
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        interrupter = Interrupter(engine_server_address, self._key)
        self._thread_pool.start(interrupter)


class PersistentRunnableBase(QRunnable):
    """Base class for runnables that talk to the persistent process in another QThread."""

    class Signals(QObject):
        finished = Signal()

    def __init__(self, engine_server_address, persistent_key):
        """
        Args:
            engine_server_address (str): address of the remote engine, currently should always an empty string
            persistent_key (tuple): persistent process identifier
        """
        super().__init__()
        self._persistent_key = persistent_key
        self._engine_mngr = make_engine_manager(engine_server_address)
        self._signals = self.Signals()
        self.finished = self._signals.finished


class Restarter(PersistentRunnableBase):
    """A runnable that restarts a persistent process."""

    def run(self):
        self._engine_mngr.restart_persistent(self._persistent_key)
        self.finished.emit()


class Interrupter(PersistentRunnableBase):
    """A runnable that interrupts a persistent process."""

    def run(self):
        self._engine_mngr.interrupt_persistent(self._persistent_key)
        self.finished.emit()


class CommandIssuer(PersistentRunnableBase):
    """A runnable that issues a command."""

    class Signals(QObject):
        finished = Signal(bool)
        stdout_msg = Signal(str)
        stderr_msg = Signal(str)

    def __init__(self, engine_server_address, persistent_key, command):
        """
        Args:
            engine_server_address (str): address of the remote engine, currently should always an empty string
            persistent_key (tuple): persistent process identifier
            command (str): command to execute
        """
        super().__init__(engine_server_address, persistent_key)
        self._command = command
        self.stdout_msg = self._signals.stdout_msg
        self.stderr_msg = self._signals.stderr_msg

    def run(self):
        for msg in self._engine_mngr.issue_persistent_command(self._persistent_key, self._command):
            if msg["type"] == "stdout":
                self.stdout_msg.emit(msg["data"])
            elif msg["type"] == "stderr":
                self.stderr_msg.emit(msg["data"])
            elif msg["type"] == "command_finished":
                self.finished.emit(msg["is_complete"])
                break
