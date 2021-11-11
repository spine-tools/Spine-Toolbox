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
from PySide2.QtWidgets import QApplication, QPlainTextEdit
from PySide2.QtGui import QFontDatabase, QTextCharFormat, QFont
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager


class PersistentConsoleLineEdit(QPlainTextEdit):
    """A line edit for the prompt of PersistentConsoleWidget.

    This widget is fully transparent. It's only there to provide user interaction.
    The contents are constantly reflected in the console widget.
    """

    def __init__(self, parent):
        """
        Args:
            parent (PersistentConsoleWidget)
        """
        super().__init__(parent)
        self.setStyleSheet("QPlainTextEdit {background-color: transparent; color: transparent}")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
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
        self.textChanged.connect(self._adjust_size)
        self.textChanged.connect(self.parent().reflect_line_edit_contents)

    @Slot()
    def _adjust_size(self):
        line_count = self.document().size().height()
        height = line_count * self.fontMetrics().height()
        self.setFixedHeight(height)

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
        self.parent().keyPressEvent(ev)


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
        self.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self._thread_pool = QThreadPool()
        self._toolbox = toolbox
        self._key = key
        self._language = language
        self.owners = {owner}
        self._prompt, self._prompt_format = self._make_prompt()
        self._cont_prompt = self._make_cont_prompt()
        self._has_prompt = False
        self._history_index = 0
        self._history_item_zero = ""
        self._style = get_style_by_name("monokai")
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {background_color}; color: {foreground_color}; border: 0px}}"
        )
        self._highlighter = CustomSyntaxHighlighter(self)
        self._highlighter.set_style(self._style)
        try:
            self._highlighter.lexer = get_lexer_by_name(self._language)
        except ClassNotFound:
            pass
        self._line_edit = PersistentConsoleLineEdit(self)
        self._line_edit.show()
        self._line_edit.setFocus()
        self._line_edit_char_count = 0
        self._add_prompt()

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
        else:
            prompt = "$ "
        return prompt, text_format

    def _make_cont_prompt(self):
        if self._language == "julia":
            prompt = len("julia> ") * " "
        elif self._language == "python":
            prompt = "... "
        else:
            prompt = "  "
        return prompt

    def _reposition_line_edit(self):
        """Moves line edit vertically to the position of the last block."""
        le = self._line_edit
        block = self.document().lastBlock()
        # FIXME: Try to find where the -4 comes from. It works well on windows and linux though
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).bottom() - le.height() - 4)
        left = le.pos().x()
        le.move(left, top)

    def _insert_formatted_text(self, cursor, text):
        """Inserts formatted text.

        Args:
            cursor (QTextCursor)
            text (str)
        """
        for start, count, text_format in self._highlighter.yield_formats(text):
            chunk = text[start : start + count]
            chunk = chunk.replace("\n", "\n" + self._cont_prompt).replace("\t", 4 * " ")
            cursor.insertText(chunk, text_format)

    @Slot()
    def reflect_line_edit_contents(self):
        """Reflects contents of line edit."""
        cursor = self.cursorForPosition(self._line_edit.pos())
        cursor.movePosition(cursor.NextCharacter, cursor.KeepAnchor, n=self._line_edit_char_count)
        cursor.removeSelectedText()
        start = cursor.position()
        text = self._line_edit.toPlainText()
        self._insert_formatted_text(cursor, text)
        self._line_edit_char_count = cursor.position() - start
        self._scroll_to_bottom()

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
            QApplication.processEvents()
            self.add_stdout("\t\t".join(completions))
        elif completions:
            # Unique option: Autocomplet current line
            cursor = self._line_edit.textCursor()
            last_word = partial_text.split(" ")[-1]
            cursor.insertText(completions[0][len(last_word) :])

    def _commit_line_edit(self):
        """Clears line edit and moves it to the end of the document."""
        cursor = self.cursorForPosition(self._line_edit.pos())
        cursor.movePosition(cursor.NextCharacter, n=self._line_edit_char_count)
        cursor.insertBlock()
        self._line_edit.move(self.cursorRect(cursor).topLeft())
        self._line_edit.clear()
        self._has_prompt = False

    def issue_command(self, text):
        """Issues command.

        Args:
            text (str)
        """
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        issuer = CommandIssuer(engine_server_address, self._key, text)
        if not self._has_prompt:
            issuer.stdin_msg.connect(self.add_stdin)
        else:
            issuer.finished.connect(self._add_prompt)
        issuer.stdout_msg.connect(self.add_stdout)
        issuer.stderr_msg.connect(self.add_stderr)
        self._commit_line_edit()
        self._history_index = 0
        self._thread_pool.start(issuer)

    def _scroll_to_bottom(self):
        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.setValue(vertical_scroll_bar.maximum())

    def _cursor_at_start_of_prompt(self):
        """Returns a cursor at the start of the prompt.

        Returns:
            QTextCursor
        """
        if not self._has_prompt:
            cursor = self.textCursor()
            cursor.movePosition(cursor.End)
            return cursor
        cursor = self.cursorForPosition(self._line_edit.pos())
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock)
        return cursor

    def _insert_text_before_prompt(self, text, with_prompt=False, text_format=QTextCharFormat()):
        """Inserts given text before the prompt. Used when adding input and output from external execution.

        Args:
            text (str)
        """
        vertical_scroll_bar = self.verticalScrollBar()
        at_bottom = vertical_scroll_bar.value() == vertical_scroll_bar.maximum()
        cursor = self._cursor_at_start_of_prompt()
        if with_prompt:
            cursor.insertText(self._prompt, self._prompt_format)
            self._insert_formatted_text(cursor, text)
        else:
            cursor.insertText(text, text_format)
        cursor.insertBlock()
        if at_bottom:
            self._scroll_to_bottom()

    def add_stdin(self, data):
        """Adds new prompt with data. Used when adding stdin from external execution.

        Args:
            data (str)
        """
        self._insert_text_before_prompt(data, with_prompt=True)

    @Slot(str)
    def add_stdout(self, data):
        """Adds new line to stdout. Used when adding stdout from external execution.

        Args:
            data (str)
        """
        self._insert_text_before_prompt(data)

    @Slot(str)
    def add_stderr(self, data):
        """Adds new line to stderr. Used when adding stderr from external execution.

        Args:
            data (str)
        """
        text_format = QTextCharFormat()
        text_format.setForeground(Qt.red)
        self._insert_text_before_prompt(data, text_format=text_format)

    @Slot(bool)
    def _add_prompt(self, is_complete=True):
        """Adds a prompt at the end of the document."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        if is_complete:
            cursor.insertText(self._prompt, self._prompt_format)
        else:
            cursor.insertText(self._cont_prompt, QTextCharFormat())
        cursor.movePosition(cursor.End)
        self._line_edit.move(self.cursorRect(cursor).topLeft())
        self._has_prompt = True

    @Slot(bool)
    def _restart_persistent(self, _=False):
        """Restarts underlying persistent process."""
        self.clear()
        self._line_edit.clear()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        restarter = Restarter(engine_server_address, self._key)
        restarter.finished.connect(self._add_prompt)
        self._thread_pool.start(restarter)

    @Slot(bool)
    def _interrupt_persistent(self, _=False):
        """Interrupts underlying persistent process."""
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        interrupter = Interrupter(engine_server_address, self._key)
        self._thread_pool.start(interrupter)

    def paintEvent(self, ev):
        """Repositions line edit."""
        super().paintEvent(ev)
        self._reposition_line_edit()

    def focusInEvent(self, _ev):
        """Gives focus to the line edit."""
        self._line_edit.setFocus()

    def resizeEvent(self, ev):
        """Makes line edit as wide as this."""
        super().resizeEvent(ev)
        self._line_edit.setFixedWidth(ev.size().width())

    def _extend_menu(self, menu):
        """Adds two more actions: Restart, and Interrupt."""
        menu.addSeparator()
        menu.addAction("Restart", self._restart_persistent)
        menu.addAction("Interrupt", self._interrupt_persistent)

    def contextMenuEvent(self, event):
        """Reimplemented to extend menu with custom actions."""
        menu = self.createStandardContextMenu()
        self._extend_menu(menu)
        menu.exec_(event.globalPos())


class PersistentRunnableBase(QRunnable):
    """Base class for runnables that talk to the persistent process in another QThread."""

    class Signals(QObject):
        finished = Signal()

    def __init__(self, engine_server_address, persistent_key):
        """
        Args:
            engine_server_address (str): address of the remote engine, currently should always be an empty string
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
        stdin_msg = Signal(str)
        stdout_msg = Signal(str)
        stderr_msg = Signal(str)

    def __init__(self, engine_server_address, persistent_key, command):
        """
        Args:
            engine_server_address (str): address of the remote engine, currently should always be an empty string
            persistent_key (tuple): persistent process identifier
            command (str): command to execute
        """
        super().__init__(engine_server_address, persistent_key)
        self._command = command
        self.stdin_msg = self._signals.stdin_msg
        self.stdout_msg = self._signals.stdout_msg
        self.stderr_msg = self._signals.stderr_msg

    def run(self):
        for msg in self._engine_mngr.issue_persistent_command(self._persistent_key, self._command):
            msg_type = msg["type"]
            if msg_type == "stdin":
                self.stdin_msg.emit(msg["data"])
            elif msg_type == "stdout":
                self.stdout_msg.emit(msg["data"])
            elif msg_type == "stderr":
                self.stderr_msg.emit(msg["data"])
            elif msg_type == "process_dead":
                self.stderr_msg.emit("Console process has been killed.")
                self.finished.emit(True)
                break
            elif msg_type == "command_finished":
                self.finished.emit(msg["is_complete"])
                break
