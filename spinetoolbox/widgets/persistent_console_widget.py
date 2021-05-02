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


class PromptSyntaxHighlighter(CustomSyntaxHighlighter):
    def __init__(self, prompt, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self._prompt = prompt

    def highlightBlock(self, text):
        """Reimplemented to account for the prompt."""
        if self.lexer is None:
            return
        if not text.startswith(self._prompt):
            return
        offset = len(self._prompt)
        for start, ttype, subtext in self.lexer.get_tokens_unprocessed(text[offset:]):
            while ttype not in self._formats:
                ttype = ttype.parent
            text_format = self._formats.get(ttype, QTextCharFormat())
            self.setFormat(offset + start, len(subtext), text_format)


class PersistentConsoleWidget(QPlainTextEdit):
    """A widget to interact with a persistent process."""

    def __init__(self, toolbox, key, lexer_name, prompt, owner=None):
        """
        Args:
            toolbox (ToolboxUI)
            key (tuple): persistent process identifier
            lexer_name (str): for syntax highlighting
            prompt (str): prompt
            owner (ProjectItemBase, optional): console owner
        """
        super().__init__(parent=toolbox)
        self._thread_pool = QThreadPool()
        self._editable = 1
        self._non_editable = -1
        self._toolbox = toolbox
        self._key = key
        self._lexer_name = lexer_name
        self._prompt = prompt
        self._plain_prompt = QTextDocumentFragment.fromHtml(prompt).toPlainText()
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
        self.add_prompt()

    def name(self):
        """Returns console name for display purposes."""
        return f"{' '.join(self._key)} Console"

    @property
    def owner_names(self):
        return "&".join(x.name for x in self.owners if x is not None)

    def _setup_lexer(self):
        try:
            self._highlighter.lexer = get_lexer_by_name(self._lexer_name)
            self._highlighter.rehighlight()
        except ClassNotFound:
            pass

    def keyPressEvent(self, ev):
        """Reimplemented to only accept keyboard input after the prompt."""
        if ev.modifiers() != Qt.NoModifier:
            super().keyPressEvent(ev)
            return
        cursor = self.textCursor()
        if cursor.block().userState() == self._non_editable or cursor.positionInBlock() < len(self._plain_prompt):
            cursor.movePosition(cursor.End)
            self.setTextCursor(cursor)
            return
        if cursor.positionInBlock() == len(self._plain_prompt) and ev.key() in (
            Qt.Key_Backspace,
            Qt.Key_Left,
            Qt.Key_Home,
        ):
            return
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._issue_command()
            return
        super().keyPressEvent(ev)

    def _issue_command(self):
        """Issues command in the prompt to the persistent process and adds output."""
        self.setCursorWidth(0)
        block = self.document().lastBlock()
        cmd = block.text()[len(self._plain_prompt) :]
        block.setUserState(self._non_editable)
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        issuer = CommandIssuer(engine_server_address, self._key, cmd)
        issuer.stdout_msg.connect(self.add_stdout)
        issuer.stderr_msg.connect(self.add_stderr)
        issuer.finished.connect(self.add_prompt)
        issuer.finished.connect(lambda: self.setCursorWidth(1))
        self._thread_pool.start(issuer)

    def _has_prompt(self):
        """Whether or not the console has a prompt. True most of the time, except when issuing a command.

        Returns:
            bool
        """
        return self.document().lastBlock().userState() == self._editable

    def _insert_html_before_prompt(self, html):
        """Inserts given html before the prompt. Used when adding input and output from external execution.

        Args:
            html (str)
        """
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.PreviousBlock)
        cursor.movePosition(cursor.EndOfBlock)
        cursor.insertBlock()
        cursor.insertHtml(html)

    def add_stdin(self, data):
        """Adds new prompt with data. Used when adding stdin from external execution.

        Args:
            data (str)
        """
        html = self._prompt + data
        if self._has_prompt():
            self._insert_html_before_prompt(html)
        else:
            self.appendHtml(html)

    def add_stdout(self, data):
        """Adds new line to stdout. Used when adding stdout from external execution.

        Args:
            data (str)
        """
        if self._has_prompt():
            self._insert_html_before_prompt(data)
        else:
            self.appendPlainText(data)

    def add_stderr(self, data):
        """Adds new line to stderr. Used when adding stderr from external execution.

        Args:
            data (str)
        """
        html = '<span style="color:red">' + data + "</span>"
        if self._has_prompt():
            self._insert_html_before_prompt(html)
        else:
            self.appendHtml(html)

    def add_prompt(self):
        """Adds a prompt at the end of the document."""
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertBlock()
        cursor.insertHtml(self._prompt)
        cursor.block().setUserState(self._editable)
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
        self.setCursorWidth(0)
        self.clear()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        restarter = Restarter(engine_server_address, self._key)
        restarter.finished.connect(self.add_prompt)
        restarter.finished.connect(lambda: self.setCursorWidth(1))
        self._thread_pool.start(restarter)

    @Slot(bool)
    def _interrupt_persistent(self, _=False):
        """Interrupts underlying persistent process."""
        self.setCursorWidth(0)
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        interrupter = Interrupter(engine_server_address, self._key)
        interrupter.finished.connect(lambda: self.setCursorWidth(1))
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
