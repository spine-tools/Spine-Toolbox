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
from PySide2.QtGui import QFontDatabase, QTextCharFormat, QFont
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager


class PersistentConsoleLineEdit(QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFont(parent.font())
        self.setUndoRedoEnabled(False)
        self.document().setDocumentMargin(0)
        self.setFixedHeight(self.fontMetrics().height())
        self.setFixedWidth(self.parent().width())
        cursor_width = self.fontMetrics().horizontalAdvance("x")
        self.setCursorWidth(cursor_width)
        self.setTabStopDistance(4 * cursor_width)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.parent().highlighter.setDocument(self.document())
        self.textChanged.connect(self._adjust_size)

    def _adjust_size(self):
        height = self.document().size().height() * self.fontMetrics().height()
        self.setFixedHeight(height)

    def wheelEvent(self, ev):
        self.parent().wheelEvent(ev)

    def contextMenuEvent(self, event):
        """Reimplemented to extend menu with custom actions from parent."""
        menu = self.createStandardContextMenu()
        self.parent().extend_menu(menu)
        menu.exec_(event.globalPos())

    def keyPressEvent(self, ev):
        text, partial_text = self._get_current_text()
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.parent().issue_command(text)
            return
        if ev.key() == Qt.Key_Up:
            self.parent().move_history(text, 1)
            return
        if ev.key() == Qt.Key_Down:
            self.parent().move_history(text, -1)
            return
        if ev.key() == Qt.Key_Tab and partial_text.strip():
            self.parent().autocomplete(text, partial_text)
            return
        super().keyPressEvent(ev)

    def _get_current_text(self):
        """Returns current text.

        Returns:
            str: the complete text
            str: the text before the cursor (for autocompletion)
        """
        cursor = self.textCursor()
        text = self.toPlainText()
        partial_text = text[: cursor.position()]
        return text, partial_text


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
        self._thread_pool = QThreadPool()
        self._toolbox = toolbox
        self._key = key
        self._language = language
        self._prompt, self._prompt_format = self._make_prompt()
        self._cont_prompt = self._make_cont_prompt()
        self._history_index = 0
        self._history_item_zero = ""
        self.owners = {owner}
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self._style = get_style_by_name("monokai")
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {background_color}; color: {foreground_color}; border: 0px}}"
        )
        self.setReadOnly(True)
        self.highlighter = CustomSyntaxHighlighter(self)
        self.highlighter.set_style(self._style)
        try:
            self.highlighter.lexer = get_lexer_by_name(self._language)
        except ClassNotFound:
            pass
        self._add_first_prompt()

    def _insert_formatted_text(self, cursor, text):
        """Inserts formatted text.

        Args:
            cursor (QTextCursor)
            text (str)
        """
        for start, count, text_format in self.highlighter.yield_formats(text):
            chunk = text[start : start + count]
            chunk = chunk.replace("\n", "\n" + self._cont_prompt).replace("\t", 4 * " ")
            cursor.insertText(chunk, text_format)

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._language.capitalize()} Console - {self.owner_names}"

    @property
    def owner_names(self):
        return "&".join(x.name for x in self.owners if x is not None)

    def _make_prompt(self):
        text_format = QTextCharFormat()
        if self._language == "julia":
            prompt = "\njulia> "
            text_format.setForeground(Qt.darkGreen)
            text_format.setFontWeight(QFont.Bold)
        elif self._language == "python":
            prompt = ">>> "
        return prompt, text_format

    def _make_cont_prompt(self):
        if self._language == "julia":
            prompt = len("julia> ") * " "
        elif self._language == "python":
            prompt = "... "
        return prompt

    def _reposition_line_edit(self):
        """Moves line edit vertically to the position of the last block."""
        le = self._line_edit
        block = self.document().lastBlock()
        # FIXME: Find where the -4 comes from
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).bottom()
            - self.fontMetrics().height()
            - 4
        )
        left = le.pos().x()
        le.move(left, top)

    def focusInEvent(self, _ev):
        """Gives focus to the line edit."""
        if self._line_edit is not None:
            self._line_edit.setFocus()

    def resizeEvent(self, ev):
        """Makes line edit as wide as this."""
        super().resizeEvent(ev)
        if self._line_edit is not None:
            self._line_edit.setFixedWidth(ev.size().width())

    def paintEvent(self, ev):
        """Repositions line edit."""
        super().paintEvent(ev)
        if self._line_edit is not None:
            self._reposition_line_edit()

    def move_history(self, text, step):
        """Moves history.

        Args:
            text (str)
            step (int)
        """
        if self._history_index == 0:
            self._history_item_zero = text
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

    def autocomplete(self, text, partial_text):
        """Autocompletes current text in the prompt (or print options if multiple matches).

        Args:
            text (str)
            partial_text (str)
        """
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        completions = engine_mngr.get_persistent_completions(self._key, partial_text)
        if len(completions) > 1:
            # Multiple options: Print them to stdout and add new prompt
            self.add_stdin(text)
            self.add_stdout("\t\t".join(completions))
        elif completions:
            # Unique option: Autocomplet current line
            cursor = self._line_edit.textCursor()
            last_word = partial_text.split(" ")[-1]
            cursor.insertText(completions[0][len(last_word) :])

    def _commit_line(self):
        """Copies text from the line edit into the last block and deletes the line edit."""
        block = self.document().lastBlock()
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(cursor.EndOfBlock)
        text = self._line_edit.toPlainText()
        self._insert_formatted_text(cursor, text)
        cursor.insertBlock()
        self._line_edit.deleteLater()
        self._line_edit = None

    def issue_command(self, text):
        """Issues command.

        Args:
            text (str)
        """
        self._commit_line()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        issuer = CommandIssuer(engine_server_address, self._key, text)
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
            if self._prompt.startswith("\n"):
                cursor.movePosition(cursor.PreviousBlock)
                cursor.movePosition(cursor.EndOfBlock)
            else:
                cursor.movePosition(cursor.StartOfBlock)
        if with_prompt:
            cursor.insertText(self._prompt, self._prompt_format)
            self._insert_formatted_text(cursor, html)
        else:
            cursor.insertHtml(html)
        cursor.insertBlock()
        self._scroll_to_bottom()

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
        if self._line_edit is not None:
            self._line_edit.deleteLater()
        self._add_prompt()

    def _add_prompt(self, is_complete=True):
        """Adds a prompt at the end of the document."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        if is_complete:
            cursor.insertText(self._prompt, self._prompt_format)
        else:
            cursor.insertText(self._cont_prompt, QTextCharFormat())
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)
        self._line_edit = PersistentConsoleLineEdit(self)
        self._line_edit.move(self.cursorRect().topLeft())
        self._line_edit.show()
        self._line_edit.setFocus()
        self._reposition_line_edit()

    def extend_menu(self, menu):
        """Add two more actions: Restart, and Interrupt."""
        menu.addSeparator()
        menu.addAction("Restart", self._restart_persistent)
        menu.addAction("Interrupt", self._interrupt_persistent)

    def contextMenuEvent(self, event):
        """Reimplemented to extend menu with custom actions."""
        menu = self.createStandardContextMenu()
        self.extend_menu(menu)
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
