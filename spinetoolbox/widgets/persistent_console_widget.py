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

import os
import uuid
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
from PySide2.QtCore import Qt, Slot, QTimer, Signal
from PySide2.QtWidgets import QTextEdit
from PySide2.QtGui import QFontDatabase, QTextCharFormat, QFont, QTextCursor, QColor, QTextBlockFormat, QTextOption
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager


class PersistentConsoleWidget(QTextEdit):
    """A widget to interact with a persistent process."""

    _history_item_available = Signal(str, str)
    _completions_available = Signal(str, str, list)
    _flush_needed = Signal()
    _FLUSH_INTERVAL = 200
    _MAX_LINES_PER_SECOND = 2000
    _MAX_LINES_PER_CYCLE = _MAX_LINES_PER_SECOND * 1000 / _FLUSH_INTERVAL
    _MAX_LINES_COUNT = 2000

    def __init__(self, toolbox, key, language, owner=None):
        """
        Args:
            toolbox (ToolboxUI)
            key (tuple): persistent process identifier
            language (str): for syntax highlighting and prompting, etc.
            owner (ProjectItemBase, optional): console owner
        """
        super().__init__(parent=toolbox)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        cursor_width = self.fontMetrics().horizontalAdvance("x")
        self.setCursorWidth(cursor_width)
        self.document().setIndentWidth(cursor_width)
        self.document().setMaximumBlockCount(self._MAX_LINES_COUNT)
        self.setWordWrapMode(QTextOption.WrapAnywhere)
        self.setTabStopDistance(4 * cursor_width)
        self._toolbox = toolbox
        self._key = key
        self._language = language
        self.owners = {owner}
        self._prompt, self._prompt_format = self._make_prompt()
        self._prefix = None
        self._reset_prefix = True
        self._pending_command_count = 0
        self._text_buffer = []
        self._skipped = {}
        self._anchor = None
        self._style = get_style_by_name("monokai")
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token] or self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QTextEdit {{background-color: {background_color}; color: {foreground_color}; border: 0px}}"
        )
        self._highlighter = CustomSyntaxHighlighter(None)
        self._highlighter.set_style(self._style)
        try:
            self._highlighter.lexer = get_lexer_by_name(self._language)
        except ClassNotFound:
            pass
        self._ansi_esc_code_handler = AnsiEscapeCodeHandler(foreground_color, background_color)
        self._prompt_block = None
        self._current_prompt = ""
        self._make_prompt_block(prompt=self._prompt)
        self._at_bottom = True
        self.cursorPositionChanged.connect(self._handle_cursor_position_changed)
        self.document().contentsChanged.connect(self._handle_contents_changed)
        self._history_item_available.connect(self._display_history_item)
        self._completions_available.connect(self._display_completions)
        self._flush_needed.connect(self._start_flush_timer)
        self._flush_in_progress = False
        self._flush_timer = QTimer()
        self._flush_timer.setInterval(self._FLUSH_INTERVAL)
        self._flush_timer.timeout.connect(self._flush_text_buffer)
        self._flush_timer.setSingleShot(True)

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._language.capitalize()} Console - {self.owner_names}"

    @property
    def owner_names(self):
        return " & ".join(x.name for x in self.owners if x is not None)

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)
        if self.anchorAt(ev.pos()):
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.IBeamCursor)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self._anchor = self.anchorAt(ev.pos())

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        if self._anchor is None:
            return
        text_buffer = self._skipped.pop(self._anchor, None)
        if text_buffer is None:
            return
        cursor = self.cursorForPosition(ev.pos())
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.beginEditBlock()
        while text_buffer:
            text, with_prompt = text_buffer.pop(0)
            self._insert_text(cursor, text, with_prompt)
        cursor.endEditBlock()
        self._anchor = None

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        scrollbar = self.verticalScrollBar()
        self._at_bottom = scrollbar.value() == scrollbar.maximum()

    @Slot()
    def _handle_contents_changed(self):
        if self._at_bottom:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    @property
    def _input_start_pos(self):
        return self._prompt_block.position() + len(self._current_prompt)

    @Slot()
    def _handle_cursor_position_changed(self):
        self.setReadOnly(self.textCursor().position() < self._input_start_pos)
        if self._reset_prefix:
            self._prefix = None

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

    def _make_prompt_block(self, prompt=""):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock(QTextBlockFormat())
        self._prompt_block = cursor.block()
        self._insert_prompt(prompt=prompt)

    def _insert_prompt(self, prompt=""):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_block.position())
        cursor.insertText(prompt, self._prompt_format)
        cursor.movePosition(QTextCursor.End)
        self._current_prompt = prompt
        self.setTextCursor(cursor)

    def _make_continuation_block(self, cursor):
        block_format = QTextBlockFormat()
        block_format.setIndent(len(self._current_prompt.lstrip()))
        cursor.insertBlock(block_format)

    def _insert_stdin_text(self, cursor, text):
        """Inserts highlighted text.

        Args:
            cursor (QTextCursor)
            text (str)
        """
        if not text:
            cursor.insertText("")
            return
        lines = iter(text.splitlines())
        line = next(lines)
        self._do_insert_stdin_text(cursor, line)
        for line in lines:
            self._make_continuation_block(cursor)
            self._do_insert_stdin_text(cursor, line)

    def _do_insert_stdin_text(self, cursor, text):
        for start, count, text_format in self._highlighter.yield_formats(text):
            chunk = text[start : start + count]
            cursor.insertText(chunk, text_format)

    def _insert_stdout_text(self, cursor, text):
        """Inserts ansi highlighted text.

        Args:
            cursor (QTextCursor)
            text (str)
        """
        for chunk, text_format in self._ansi_esc_code_handler.parse_text(text):
            cursor.insertText(chunk, text_format)

    def _insert_text_before_prompt(self, text, with_prompt=False):
        """Inserts given text before the prompt. Used when adding input and output from external execution.

        Args:
            text (str)
        """
        self._text_buffer.append((text, with_prompt))
        if not self._flush_in_progress:
            self._flush_in_progress = True
            self._flush_needed.emit()

    @Slot()
    def _start_flush_timer(self):
        self._flush_timer.start()

    @Slot()
    def _flush_text_buffer(self):
        """Inserts all text from buffer."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        k = 0
        while self._text_buffer and k < self._MAX_LINES_PER_CYCLE:
            cursor.setPosition(self._prompt_block.position() - 1)
            text, with_prompt = self._text_buffer.pop(0)
            self._insert_text(cursor, text, with_prompt)
            k += 1
        if self._text_buffer:
            address = uuid.uuid4().hex
            char_format = cursor.charFormat()
            char_format.setBackground(QColor('white'))
            char_format.setForeground(QColor('blue'))
            char_format.setAnchor(True)
            char_format.setAnchorHref(address)
            self._skipped[address] = self._text_buffer[-self._MAX_LINES_COUNT :]
            cursor.setPosition(self._prompt_block.position() - 1)
            cursor.insertBlock(QTextBlockFormat())
            cursor.insertText(f"<--- {len(self._text_buffer)} more lines --->", char_format)
            self._text_buffer.clear()
        cursor.endEditBlock()
        self._flush_in_progress = False

    def _insert_text(self, cursor, text, with_prompt):
        cursor.insertBlock(QTextBlockFormat())
        if with_prompt:
            cursor.insertText(self._prompt, self._prompt_format)
            self._insert_stdin_text(cursor, text)
        else:
            self._insert_stdout_text(cursor, text)

    def add_stdin(self, data):
        """Adds new prompt with data. Used when adding stdin from external execution.

        Args:
            data (str)
        """
        self._insert_text_before_prompt(data, with_prompt=True)

    def add_stdout(self, data):
        """Adds new line to stdout. Used when adding stdout from external execution.

        Args:
            data (str)
        """

        self._insert_text_before_prompt(data)

    def add_stderr(self, data):
        """Adds new line to stderr. Used when adding stderr from external execution.

        Args:
            data (str)
        """
        self._insert_text_before_prompt(data)

    def _get_current_text(self):
        """Returns current text.

        Returns:
            str: the complete text
        """
        cursor = self.textCursor()
        cursor.setPosition(self._input_start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        return cursor.selectedText()

    def _get_prefix(self):
        if self._prefix is None:
            cursor = self.textCursor()
            if cursor.position() > self._input_start_pos:
                cursor.setPosition(self._input_start_pos, QTextCursor.KeepAnchor)
                self._prefix = cursor.selectedText()
            else:
                self._prefix = ""
        return self._prefix

    def _highlight_current_input(self):
        cursor = self.textCursor()
        cursor.setPosition(self._input_start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        text = cursor.selectedText()
        for start, count, text_format in self._highlighter.yield_formats(text):
            start += self._input_start_pos
            cursor.setPosition(start)
            cursor.setPosition(start + count, QTextCursor.KeepAnchor)
            cursor.setCharFormat(text_format)
        cursor.movePosition(QTextCursor.NextCharacter)
        cursor.setCharFormat(QTextCharFormat())

    def keyPressEvent(self, ev):
        self._at_bottom = True
        text = self._get_current_text()
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._issue_command(text)
        elif ev.key() == Qt.Key_Up:
            self._move_history(text, True)
        elif ev.key() == Qt.Key_Down:
            self._move_history(text, False)
        elif ev.key() == Qt.Key_Tab:
            self._autocomplete(text)
        elif ev.key() != Qt.Key_Backspace or self.textCursor().position() > self._input_start_pos:
            cursor = self.textCursor()
            super().keyPressEvent(ev)
            if cursor.position() >= self._input_start_pos and self.textCursor().position() < self._input_start_pos:
                cursor.setPosition(self._input_start_pos)
                self.setTextCursor(cursor)
            self._highlight_current_input()

    def _issue_command(self, text):
        """Issues command.

        Args:
            text (str)
        """
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        if not engine_mngr.is_persistent_command_complete(self._key, text):
            self._make_continuation_block(self.textCursor())
            return
        log_stdin = bool(self._pending_command_count)
        self._make_prompt_block(prompt="")
        self._pending_command_count += 1
        self._do_issue_command(engine_mngr, text, log_stdin)

    def _do_issue_command(self, engine_mngr, text, log_stdin):
        for msg in engine_mngr.issue_persistent_command(self._key, text):
            msg_type = msg["type"]
            if msg_type == "stdin" and log_stdin:
                self.add_stdin(msg["data"])
            elif msg_type == "stdout":
                self.add_stdout(msg["data"])
            elif msg_type == "stderr":
                self.add_stderr(msg["data"])
        self._handle_command_finished()

    def _handle_command_finished(self):
        self._pending_command_count -= 1
        if self._pending_command_count == 0:
            self._insert_prompt(prompt=self._prompt)

    def _move_history(self, text, backwards):
        """Moves history."""
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        prefix = self._get_prefix()
        history_item = engine_mngr.get_persistent_history_item(self._key, text, prefix, backwards)
        self._history_item_available.emit(history_item, prefix)

    @Slot(str, str)
    def _display_history_item(self, history_item, prefix):
        self._reset_prefix = False
        cursor = self.textCursor()
        pos = self._input_start_pos + len(prefix)
        cursor.setPosition(pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        self._insert_stdin_text(cursor, history_item[len(prefix) :])
        if prefix:
            cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self._reset_prefix = True
        self._highlight_current_input()

    def _autocomplete(self, text):
        """Autocompletes current text in the prompt (or output options if multiple matches).

        Args:
            text (str)
        """
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        prefix = self._get_prefix()
        completions = engine_mngr.get_persistent_completions(self._key, prefix)
        self._completions_available.emit(text, prefix, completions)

    @Slot(str, str, list)
    def _display_completions(self, text, prefix, completions):
        completion = os.path.commonprefix(completions)
        if prefix.endswith(completion) and len(completions) > 1:
            # Can't complete, but there is more than one option: 'commit' stdin and output options to stdout
            self.add_stdin(text)
            self.add_stdout("\t\t".join(completions))
        else:
            # Complete in current line
            cursor = self.textCursor()
            last_prefix_word = prefix.split(" ")[-1]
            cursor.insertText(completion[len(last_prefix_word) :])
            self._highlight_current_input()

    @Slot(bool)
    def _restart_persistent(self, _=False):
        """Restarts underlying persistent process."""
        self.clear()
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        self._text_buffer.clear()
        for msg in engine_mngr.restart_persistent(self._key):
            msg_type = msg["type"]
            if msg_type == "stdout":
                self.add_stdout(msg["data"])
            elif msg_type == "stderr":
                self.add_stderr(msg["data"])
        self._make_prompt_block(prompt=self._prompt)

    @Slot(bool)
    def _interrupt_persistent(self, _=False):
        """Interrupts underlying persistent process."""
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        engine_mngr = make_engine_manager(engine_server_address)
        engine_mngr.interrupt_persistent(self._key)

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


# Translated from
# https://code.qt.io/cgit/qt-creator/qt-creator.git/tree/src/libs/utils/ansiescapecodehandler.cpp?h=master
# TODO: Consider qtconsole's QtAnsiCodeProcessor
class AnsiEscapeCodeHandler:
    def __init__(self, fg_color, bg_color):
        self._previous_format_closed = True
        self._previous_format = QTextCharFormat()
        self._pending_text = ""
        self._bg_color = QColor(bg_color)
        self._fg_color = QColor(fg_color)

    def _make_default_format(self):
        default_format = QTextCharFormat()
        default_format.setBackground(self._bg_color)
        default_format.setForeground(self._fg_color)
        return default_format

    def endFormatScope(self):
        self._previous_format_closed = True

    def setFormatScope(self, char_format):
        self._previous_format = char_format
        self._previous_format_closed = False

    def parse_text(self, text):
        class AnsiEscapeCode:
            ResetFormat = 0
            BoldText = 1
            FaintText = 2
            ItalicText = 3
            NormalIntensity = 22
            NotItalic = 23
            TextColorStart = 30
            TextColorEnd = 37
            RgbTextColor = 38
            DefaultTextColor = 39
            BackgroundColorStart = 40
            BackgroundColorEnd = 47
            RgbBackgroundColor = 48
            DefaultBackgroundColor = 49
            BrightTextColorStart = 90
            BrightTextColorEnd = 97
            BrightBackgroundColorStart = 100
            BrightBackgroundColorEnd = 107

        escape = "\x1b["
        semicolon = ";"
        color_terminator = "m"
        erase_to_eol = "K"
        char_format = self._make_default_format() if self._previous_format_closed else self._previous_format
        stripped_text = self._pending_text + text
        self._pending_text = ""
        while stripped_text:
            if self._pending_text:
                break
            try:
                escape_pos = stripped_text.index(escape[0])
            except ValueError:
                yield stripped_text, char_format
                break
            if escape_pos != 0:
                yield stripped_text[:escape_pos], char_format
                stripped_text = stripped_text[escape_pos:]
            if stripped_text[0] != escape[0]:
                break
            while stripped_text and escape[0] == stripped_text[0]:
                if escape.startswith(stripped_text):
                    # control sequence is not complete
                    self._pending_text += stripped_text
                    stripped_text = ""
                    break
                if not stripped_text.startswith(escape):
                    # not a control sequence
                    self._pending_text = ""
                    yield stripped_text[:1], char_format
                    stripped_text = stripped_text[1:]
                    continue
                self._pending_text += stripped_text[: len(escape)]
                stripped_text = stripped_text[len(escape) :]
                # \e[K is not supported. Just strip it.
                if stripped_text.startswith(erase_to_eol):
                    self._pending_text = ""
                    stripped_text = stripped_text[1:]
                    continue
                # get the number
                str_number = ""
                numbers = []
                while stripped_text:
                    if stripped_text[0].isdigit():
                        str_number += stripped_text[0]
                    else:
                        if str_number:
                            numbers.append(str_number)
                        if not str_number or stripped_text[0] != semicolon:
                            break
                        str_number = ""
                    self._pending_text += stripped_text[0:1]
                    stripped_text = stripped_text[1:]
                if not stripped_text:
                    break
                # remove terminating char
                if not stripped_text.startswith(color_terminator):
                    self._pending_text = ""
                    stripped_text = stripped_text[1:]
                    break
                # got consistent control sequence, ok to clear pending text
                self._pending_text = ""
                stripped_text = stripped_text[1:]
                if not numbers:
                    char_format = self._make_default_format()
                    self.endFormatScope()
                for i in range(len(numbers)):  # pylint: disable=consider-using-enumerate
                    code = int(numbers[i])
                    if AnsiEscapeCode.TextColorStart <= code <= AnsiEscapeCode.TextColorEnd:
                        char_format.setForeground(_ansi_color(code - AnsiEscapeCode.TextColorStart))
                        self.setFormatScope(char_format)
                    elif AnsiEscapeCode.BrightTextColorStart <= code <= AnsiEscapeCode.BrightTextColorEnd:
                        char_format.setForeground(_ansi_color(code - AnsiEscapeCode.BrightTextColorStart, bright=True))
                        self.setFormatScope(char_format)
                    elif AnsiEscapeCode.BackgroundColorStart <= code <= AnsiEscapeCode.BackgroundColorEnd:
                        char_format.setBackground(_ansi_color(code - AnsiEscapeCode.BackgroundColorStart))
                        self.setFormatScope(char_format)
                    elif AnsiEscapeCode.BrightBackgroundColorStart <= code <= AnsiEscapeCode.BrightBackgroundColorEnd:
                        char_format.setBackground(
                            _ansi_color(code - AnsiEscapeCode.BrightBackgroundColorStart, bright=True)
                        )
                        self.setFormatScope(char_format)
                    else:
                        if code == AnsiEscapeCode.ResetFormat:
                            char_format = self._make_default_format()
                            self.endFormatScope()
                            break
                        if code == AnsiEscapeCode.BoldText:
                            char_format.setFontWeight(QFont.Bold)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.FaintText:
                            char_format.setFontWeight(QFont.Light)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.ItalicText:
                            char_format.setFontItalic(True)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.NormalIntensity:
                            char_format.setFontWeight(QFont.Normal)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.NotItalic:
                            char_format.setFontItalic(False)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.DefaultTextColor:
                            char_format.setForeground(self._fg_color)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.DefaultBackgroundColor:
                            char_format.setBackground(self._bg_color)
                            self.setFormatScope(char_format)
                            break
                        if code == AnsiEscapeCode.RgbBackgroundColor:
                            # See http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
                            i += 1
                            if i >= len(numbers):
                                break
                            j = int(numbers[i])
                            if j == 2:
                                # RGB set with format: 38;2;<r>;<g>;<b>
                                if i + 3 < len(numbers):
                                    color = QColor(int(numbers[i + 1]), int(numbers[i + 2]), int(numbers[i + 3]))
                                    if code == AnsiEscapeCode.RgbTextColor:
                                        char_format.setForeground(color)
                                    else:
                                        char_format.setBackground(color)
                                self.setFormatScope(char_format)
                                i += 3
                                break
                            if j == 5:
                                # 256 color mode with format: 38;5;<i>
                                index = int(numbers[i + 1])
                                color = QColor()
                                if index < 8:
                                    # The first 8 colors are standard low-intensity ANSI colors.
                                    color = _ansi_color(index)
                                elif index < 16:
                                    # The next 8 colors are standard high-intensity ANSI colors.
                                    color = _ansi_color(index - 8).lighter(150)
                                elif index < 232:
                                    # The next 216 colors are a 6x6x6 RGB cube.
                                    o = index - 16
                                    color = QColor((o / 36) * 51, ((o / 6) % 6) * 51, (o % 6) * 51)
                                else:
                                    # The last 24 colors are a greyscale gradient.
                                    grey = int((index - 232) * 11)
                                    color = QColor(grey, grey, grey)
                                if code == AnsiEscapeCode.RgbTextColor:
                                    char_format.setForeground(color)
                                else:
                                    char_format.setBackground(color)
                                self.setFormatScope(char_format)
                                i += 1
                            break
                        break


def _ansi_color(code, bright=False):
    if code >= 8:
        return QColor()
    on = 170 if not bright else 255
    off = 0 if not bright else 85
    red = on if code & 1 else off
    green = on if code & 2 else off
    blue = on if code & 4 else off
    return QColor(red, green, blue)
