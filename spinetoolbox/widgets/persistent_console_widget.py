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
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QPlainTextEdit
from PySide2.QtGui import QFontDatabase, QTextDocumentFragment, QTextCharFormat
from spinetoolbox.helpers import CustomSyntaxHighlighter


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
    def __init__(self, toolbox, key, lexer_name, prompt, owner=None):
        super().__init__(parent=toolbox)
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

    def _setup_lexer(self):
        try:
            self._highlighter.lexer = get_lexer_by_name(self._lexer_name)
            self._highlighter.rehighlight()
        except ClassNotFound:
            pass

    def keyPressEvent(self, ev):
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
        block = self.document().lastBlock()
        cmd = block.text()[len(self._plain_prompt) :]
        block.setUserState(self._non_editable)
        for msg in self._toolbox.issue_persistent_command(self._key, cmd):
            if msg["type"] == "stdout":
                self.add_stdout(msg["data"])
            elif msg["type"] == "stderr":
                self.add_stderr(msg["data"])
        self.add_prompt()

    def _has_prompt(self):
        return self.document().lastBlock().userState() == self._editable

    def _insert_html_before_prompt(self, html):
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.PreviousBlock)
        cursor.movePosition(cursor.EndOfBlock)
        cursor.insertBlock()
        cursor.insertHtml(html)

    def add_stdin(self, data):
        html = self._prompt + data
        if self._has_prompt():
            self._insert_html_before_prompt(html)
        else:
            self.appendHtml(html)

    def add_stdout(self, data):
        if self._has_prompt():
            self._insert_html_before_prompt(data)
        else:
            self.appendPlainText(data)

    def add_stderr(self, data):
        html = '<span style="color:red">' + data + "</span>"
        if self._has_prompt():
            self._insert_html_before_prompt(html)
        else:
            self.appendHtml(html)

    def add_prompt(self):
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertBlock()
        cursor.insertHtml(self._prompt)
        cursor.block().setUserState(self._editable)
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)
