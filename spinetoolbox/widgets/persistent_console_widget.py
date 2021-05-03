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
from PySide2.QtGui import QFontDatabase, QTextDocumentFragment, QTextCharFormat
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager


PROMPT = 1


class PromptSyntaxHighlighter(CustomSyntaxHighlighter):
    def __init__(self, prompt, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self._prompt = prompt

    def highlightBlock(self, text):
        """Reimplemented to account for the prompt."""
        if self.lexer is None:
            return
        if self.currentBlockState() != PROMPT:
            return
        offset = len(self._prompt)
        for start, ttype, subtext in self.lexer.get_tokens_unprocessed(text[offset:]):
            while ttype not in self._formats:
                ttype = ttype.parent
            text_format = self._formats.get(ttype, QTextCharFormat())
            self.setFormat(offset + start, len(subtext), text_format)


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
        self._thread_pool = QThreadPool()
        self._toolbox = toolbox
        self._key = key
        self._language = language
        self._prompt = self._make_prompt()
        self._plain_prompt = QTextDocumentFragment.fromHtml(self._prompt).toPlainText()
        self.owners = {owner}
        self._highlighter = PromptSyntaxHighlighter(self._plain_prompt, self)
        self._highlighter.setDocument(self.document())
        self._style = get_style_by_name("monokai")
        self._highlighter.set_style(self._style)
        self._setup_lexer()
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self.setUndoRedoEnabled(False)
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token.Text]
        self.setStyleSheet(f"QPlainTextEdit {{background-color: {background_color}; color: {foreground_color};}}")
        self._add_first_prompt()
        self.setCursorWidth(self.fontMetrics().horizontalAdvance("x"))

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._language.capitalize()} Console - {self.owner_names}"

    @property
    def owner_names(self):
        return "&".join(x.name for x in self.owners if x is not None)

    def _make_prompt(self):
        return {"julia": '<br><span style="color:green; font-weight: bold">julia></span> ', "python": '>>> '}.get(
            self._language, "$"
        )

    def _setup_lexer(self):
        try:
            self._highlighter.lexer = get_lexer_by_name(self._language)
            self._highlighter.rehighlight()
        except ClassNotFound:
            pass

    def _is_block_editable(self, block):
        return block.userState() == PROMPT and block == self.document().lastBlock()

    def keyPressEvent(self, ev):
        """Reimplemented to only accept keyboard input after the prompt."""
        cursor = self.textCursor()
        if ev.modifiers() == Qt.NoModifier and (
            not self._is_block_editable(cursor.block()) or cursor.positionInBlock() < len(self._plain_prompt)
        ):
            cursor.movePosition(cursor.End)
            self.setTextCursor(cursor)
            return
        if ev.modifiers() == Qt.NoModifier and (
            cursor.positionInBlock() == len(self._plain_prompt)
            and ev.key() in (Qt.Key_Backspace, Qt.Key_Left, Qt.Key_Home)
        ):
            return
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._issue_command()
            return
        super().keyPressEvent(ev)

    def _issue_command(self):
        """Issues command in the prompt to the persistent process and adds output."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        block = cursor.block()
        cmd = block.text()[len(self._plain_prompt) :]
        cursor.insertBlock()
        cursor.movePosition(cursor.End)
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        issuer = CommandIssuer(engine_server_address, self._key, cmd)
        issuer.stdout_msg.connect(self.add_stdout)
        issuer.stderr_msg.connect(self.add_stderr)
        issuer.finished.connect(self._add_prompt)
        self._thread_pool.start(issuer)

    def _has_prompt(self):
        """Whether or not the console has a prompt. True most of the time, except when issuing a command.

        Returns:
            bool
        """
        return self.document().lastBlock().userState() == PROMPT

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
            html = self._prompt + html
            cursor.block().setUserState(PROMPT)
        cursor.insertHtml(html)

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

    def _add_prompt(self, first=False):
        """Adds a prompt at the end of the document."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        if cursor.block().text() or first:
            cursor.insertBlock()
        cursor.insertHtml(self._prompt)
        cursor.block().setUserState(PROMPT)
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)

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
        finished = Signal()
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
        self.finished.emit()
