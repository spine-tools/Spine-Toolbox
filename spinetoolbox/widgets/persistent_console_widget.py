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

"""Contains a widget acting as a console for Julia & Python REPL's."""
import os
import uuid
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
from PySide6.QtCore import Qt, Slot, QTimer, Signal, QRect
from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy
from PySide6.QtGui import (
    QFontDatabase,
    QTextCharFormat,
    QFont,
    QTextCursor,
    QColor,
    QTextBlockFormat,
    QTextOption,
    QKeySequence,
)
from spinetoolbox.helpers import CustomSyntaxHighlighter
from spinetoolbox.spine_engine_manager import make_engine_manager
from spinetoolbox.qthread_pool_executor import QtBasedThreadPoolExecutor
from spine_engine.exception import RemoteEngineInitFailed


class _CustomLineEdit(QPlainTextEdit):
    def __init__(self, console):
        super().__init__(console)
        self._updating = False
        self._console = console
        self._current_prompt = ""
        self.setStyleSheet("QPlainTextEdit {background-color: transparent; color: transparent; border:none;}")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setTabChangesFocus(False)
        self.setUndoRedoEnabled(False)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.cursorPositionChanged.connect(self._handle_cursor_position_changed)
        self.textChanged.connect(self._handle_text_changed)

    @property
    def min_pos(self):
        return len(self._current_prompt)

    @property
    def new_line_indent(self):
        return len(self._current_prompt.lstrip())  # lstrip() is to remove leading '\n'

    def reset(self, current_prompt):
        self._current_prompt = current_prompt
        self.setPlainText(current_prompt)

    def new_line(self):
        cursor = self.textCursor()
        cursor.insertText("\n")

    def formatted_text(self):
        text = self.raw_text()
        if not text:
            return ""
        lines = iter(text.splitlines())
        new_lines = [next(lines).rstrip()] + [line.rstrip()[self.new_line_indent :] for line in lines]
        return "\n".join(new_lines)

    def raw_text(self):
        return self.toPlainText()[self.min_pos :]

    def set_raw_text(self, text):
        self.setPlainText(self._current_prompt + text)

    @Slot()
    def _handle_text_changed(self):
        """Add indent to new lines."""
        if self._updating:
            return
        if not self.raw_text():
            return
        self._updating = True
        cursor = self.textCursor()
        for i in range(self.document().blockCount()):
            block = self.document().findBlockByNumber(i)
            if block.position() < self.min_pos:
                continue
            if not block.text().startswith(self.new_line_indent * " "):
                cursor.setPosition(block.position())
                cursor.insertText(self.new_line_indent * " ")
        self._updating = False

    @Slot()
    def _handle_cursor_position_changed(self):
        """Move cursor away from indent areas."""
        if self._updating:
            return
        self._updating = True
        cursor = self.textCursor()
        if cursor.position() < self.min_pos:
            cursor.setPosition(self.min_pos)
        elif cursor.positionInBlock() < self.new_line_indent:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, n=self.new_line_indent)
        self.setTextCursor(cursor)
        self._updating = False

    def keyPressEvent(self, ev):
        if ev.matches(QKeySequence.Copy):
            ev.ignore()
            return
        if ev.key() == Qt.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() == self.min_pos:
                return
            if cursor.positionInBlock() == self.new_line_indent:
                cursor.movePosition(
                    QTextCursor.MoveOperation.PreviousCharacter,
                    QTextCursor.MoveMode.KeepAnchor,
                    n=self.new_line_indent + 1,
                )
                cursor.removeSelectedText()
                return
        if ev.key() == Qt.Key_Left:
            cursor = self.textCursor()
            if cursor.positionInBlock() == self.new_line_indent:
                cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, n=self.new_line_indent + 1)
                self.setTextCursor(cursor)
                return
        if ev.key() == Qt.Key_Delete:
            cursor = self.textCursor()
            if cursor.atBlockEnd():
                cursor.movePosition(
                    QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, n=self.new_line_indent + 1
                )
                cursor.removeSelectedText()
                return
        if self._console.key_press_event(ev):
            return
        super().keyPressEvent(ev)


class PersistentConsoleWidget(QPlainTextEdit):
    """A widget to interact with a persistent process."""

    _command_checked = Signal(str, bool)
    _msg_available = Signal(str, str)
    _command_finished = Signal()
    _history_item_available = Signal(str, str)
    _completions_available = Signal(str, str, list)
    _restarted = Signal()
    _killed = Signal(bool)
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
        self._executor = QtBasedThreadPoolExecutor(max_workers=1)
        self._updating = False
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self.setMaximumBlockCount(self._MAX_LINES_COUNT)
        self._toolbox = toolbox
        self._key = key
        self._is_dead = False
        self._language = language
        self.owners = {owner}
        self._prompt, self._prompt_format = self._make_prompt()
        self._prefix = None
        self._pending_command_count = 0
        self._text_buffer = []
        self._skipped = {}
        self._anchor = None
        self._style = get_style_by_name("monokai")
        background_color = self._style.background_color
        foreground_color = self._style.styles[Token] or self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {background_color}; color: {foreground_color}; border: 0px}}"
        )
        cursor_width = self.fontMetrics().horizontalAdvance("x")
        self.setWordWrapMode(QTextOption.WrapAnywhere)
        self.setTabStopDistance(4 * cursor_width)
        self._line_edit = _CustomLineEdit(self)
        self._line_edit.setFont(font)
        self._line_edit.setCursorWidth(cursor_width)
        self._line_edit.setWordWrapMode(QTextOption.WrapAnywhere)
        self._line_edit.setTabStopDistance(4 * cursor_width)
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
        self._flush_in_progress = False
        self._flush_timer = QTimer()
        self._flush_timer.setInterval(self._FLUSH_INTERVAL)
        self._flush_timer.timeout.connect(self._flush_text_buffer)
        self._flush_timer.setSingleShot(True)
        self.engine_mngr = None
        self.setReadOnly(True)
        self.document().contentsChanged.connect(self._handle_contents_changed)
        self.updateRequest.connect(self._handle_update_request)
        self.selectionChanged.connect(self._handle_selection_changed)
        self.cursorPositionChanged.connect(self._handle_cursor_position_changed)
        self._flush_needed.connect(self._start_flush_timer)
        self._line_edit.textChanged.connect(self._update_user_input)
        self._command_checked.connect(self._handle_command_checked)
        self._msg_available.connect(self._handle_msg_available)
        self._command_finished.connect(self._handle_command_finished)
        self._history_item_available.connect(self._display_history_item)
        self._completions_available.connect(self._display_completions)
        self._restarted.connect(self._handle_restarted)
        self._killed.connect(self._do_set_killed)

    def closeEvent(self, ev):
        super().closeEvent(ev)
        self._executor.shutdown()

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._language.capitalize()} Console - {self.owner_names}"

    @property
    def prompt(self):
        return self._prompt

    @property
    def owner_names(self):
        return " & ".join(x.name for x in self.owners if x is not None)

    @property
    def _input_start_pos(self):
        return self._prompt_block.position() + len(self._current_prompt)

    def focusInEvent(self, ev):
        self._line_edit.setFocus()

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)
        if self.anchorAt(ev.position().toPoint()):
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.IBeamCursor)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self._anchor = self.anchorAt(ev.position().toPoint())

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        if self._anchor is None:
            return
        text_buffer = self._skipped.pop(self._anchor, None)
        if text_buffer is None:
            return
        cursor = self.cursorForPosition(ev.position().toPoint())
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

    @Slot()
    def _handle_selection_changed(self):
        if self._updating:
            return
        cursor = self.textCursor()
        le_cursor = self._line_edit.textCursor()
        le_selection_start = cursor.selectionStart() - self._prompt_block.position()
        le_selection_end = cursor.selectionEnd() - self._prompt_block.position()
        if le_selection_start < self._line_edit.min_pos and le_selection_end < self._line_edit.min_pos:
            le_cursor.clearSelection()
        else:
            le_selection_start = max(self._line_edit.min_pos, le_selection_start)
            le_selection_end = max(self._line_edit.min_pos, le_selection_end)
            le_cursor.setPosition(le_selection_start)
            le_cursor.setPosition(le_selection_end, QTextCursor.MoveMode.KeepAnchor)
        self._line_edit.setTextCursor(le_cursor)

    @Slot()
    def _handle_cursor_position_changed(self):
        if self._updating:
            return
        cursor = self.textCursor()
        le_cursor = self._line_edit.textCursor()
        le_position = cursor.position() - self._prompt_block.position()
        if self._line_edit.min_pos <= le_position < self._line_edit.document().characterCount():
            le_cursor.setPosition(le_position)
            self._line_edit.setTextCursor(le_cursor)

    @Slot(QRect, int)
    def _handle_update_request(self, _rect, _dy):
        """Move line edit to input start pos."""
        if not self._updating:
            self._move_and_resize_line_edit()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if not self._updating:
            self._move_and_resize_line_edit()

    def _move_and_resize_line_edit(self):
        if self._prompt_block is None:
            return
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_block.position())
        rect = self.cursorRect(cursor)
        self._line_edit.move(rect.topLeft())
        width = self.geometry().width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        cursor_width = self._line_edit.cursorWidth()
        width = (width // cursor_width) * cursor_width
        self._line_edit.setFixedWidth(width)

    @Slot()
    def _update_user_input(self):
        self._updating = True
        cursor = self.textCursor()
        cursor.setPosition(self._input_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        text = self._line_edit.raw_text()
        cursor.insertText(text)
        self._highlight_current_input()
        self._updating = False
        self._move_and_resize_line_edit()

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
            char_format.setBackground(QColor("white"))
            char_format.setForeground(QColor("blue"))
            char_format.setAnchor(True)
            char_format.setAnchorHref(address)
            self._skipped[address] = self._text_buffer[-self._MAX_LINES_COUNT :]
            cursor.setPosition(self._prompt_block.position() - 1)
            cursor.insertBlock(QTextBlockFormat())
            cursor.insertText(f"<--- {len(self._text_buffer)} more lines --->", char_format)
            self._text_buffer.clear()
        cursor.endEditBlock()
        self._flush_in_progress = False

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
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()
        self._prompt_block = cursor.block()
        self._insert_prompt(prompt=prompt)

    def _insert_prompt(self, prompt=""):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_block.position())
        cursor.insertText(prompt, self._prompt_format)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._current_prompt = prompt
        self._line_edit.reset(self._current_prompt)
        self._move_and_resize_line_edit()

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
            cursor.insertText("\n")
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

    def _insert_text(self, cursor, text, with_prompt):
        cursor.insertBlock(QTextBlockFormat())
        if with_prompt:
            cursor.insertText(self._prompt, self._prompt_format)
            self._insert_stdin_text(cursor, text)
        else:
            self._insert_stdout_text(cursor, text)

    def set_killed(self, killed):
        """Emits the ``killed`` signal.

        Args:
            killed (bool): if True, may the console rest in peace
        """
        self._killed.emit(killed)

    @Slot(bool)
    def _do_set_killed(self, killed):
        """Sets the console as killed or alive.

        Args:
            killed (bool): if True, may the console rest in peace
        """
        self._is_dead = killed
        self._line_edit.setVisible(not killed)
        if killed:
            self._make_prompt_block("Console killed (can be restarted from the right-click context menu)")

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
        return self._line_edit.formatted_text()

    def _get_prefix(self):
        le_cursor = self._line_edit.textCursor()
        le_cursor.setPosition(self._line_edit.min_pos, QTextCursor.MoveMode.KeepAnchor)
        return le_cursor.selectedText().rstrip()

    def _highlight_current_input(self):
        cursor = self.textCursor()
        cursor.setPosition(self._input_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        text = cursor.selectedText()
        for start, count, text_format in self._highlighter.yield_formats(text):
            start += self._input_start_pos
            cursor.setPosition(start)
            cursor.setPosition(start + count, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(text_format)
        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
        cursor.setCharFormat(QTextCharFormat())

    def key_press_event(self, ev):
        """Handles key press event from line edit.

        Returns:
            True if handled, False if not.
        """
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
        else:
            return False
        return True

    def create_engine_manager(self):
        """Returns a new local or remote spine engine manager or
        an existing remote spine engine manager.
        Returns None if connecting to Spine Engine Server fails."""
        exec_remotely = self._toolbox.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        if exec_remotely:
            if self.engine_mngr:
                return self.engine_mngr
            self.engine_mngr = make_engine_manager(exec_remotely)
            host, port, security, sec_folder = self._toolbox.engine_server_settings()
            try:
                self.engine_mngr.make_engine_client(host, port, security, sec_folder)
            except RemoteEngineInitFailed as e:
                self._toolbox.msg_error.emit(f"Connecting to Spine Engine Server failed. {e}")
                return None
            return self.engine_mngr
        else:
            engine_mngr = make_engine_manager(exec_remotely)
            return engine_mngr

    def _issue_command(self, text):
        """Issues command.

        Args:
            text (str)
        """
        self._executor.submit(self._do_check_command, text)

    def _do_check_command(self, text):
        if not text.strip():  # Don't send empty command to execution manager
            self._make_prompt_block(prompt=self._prompt)
            return
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        complete = engine_mngr.is_persistent_command_complete(self._key, text)
        self._command_checked.emit(text, complete)

    @Slot(str, bool)
    def _handle_command_checked(self, text, complete):
        """Issues command.

        Args:
            text (str)
        """
        if not complete:
            self._line_edit.new_line()
            return
        self._make_prompt_block(prompt="")
        self._executor.submit(self._do_issue_command, text)

    def _do_issue_command(self, text):
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        log_stdin = bool(self._pending_command_count)
        self._pending_command_count += 1
        for msg in engine_mngr.issue_persistent_command(self._key, text):
            if msg["type"] != "stdin" or log_stdin:
                self._msg_available.emit(msg["type"], msg["data"])
        self._command_finished.emit()

    @Slot(str, str)
    def _handle_msg_available(self, msg_type, text):
        if msg_type == "stdin":
            self.add_stdin(text)
        elif msg_type == "stdout":
            self.add_stdout(text)
        elif msg_type == "stderr":
            self.add_stderr(text)

    @Slot()
    def _handle_command_finished(self):
        self._pending_command_count -= 1
        if self._pending_command_count == 0:
            self._insert_prompt(prompt=self._prompt)

    def _move_history(self, text, backwards):
        """Moves history."""
        self._executor.submit(self._do_move_history, text, backwards)

    def _do_move_history(self, text, backwards):
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        prefix = self._get_prefix()
        history_item = engine_mngr.get_persistent_history_item(self._key, text, prefix, backwards)
        self._history_item_available.emit(history_item, prefix)

    @Slot(str, str)
    def _display_history_item(self, history_item, prefix):
        self._line_edit.set_raw_text(history_item)
        if prefix:
            le_cursor = self._line_edit.textCursor()
            le_cursor.setPosition(self._line_edit.min_pos + len(prefix))
            self._line_edit.setTextCursor(le_cursor)

    def _autocomplete(self, text):
        """Autocompletes current text in the prompt (or output options if multiple matches).

        Args:
            text (str)
        """
        prev_char = self._line_edit.document().characterAt(self._line_edit.textCursor().position() - 1)
        if prev_char.isspace():
            le_cursor = self._line_edit.textCursor()
            le_cursor.insertText(4 * " ")
            self._line_edit.setTextCursor(le_cursor)
            return
        self._executor.submit(self._do_autocomplete, text)

    def _do_autocomplete(self, text):
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
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
            le_cursor = self._line_edit.textCursor()
            self._line_edit.set_raw_text(text)
            self._line_edit.setTextCursor(le_cursor)
        else:
            # Complete in current line
            last_prefix_word = prefix.split(" ")[-1]
            text_to_insert = completion[len(last_prefix_word) :]
            index = len(prefix)
            new_text = text[:index] + text_to_insert + text[index:]
            self._line_edit.set_raw_text(new_text)
            le_cursor = self._line_edit.textCursor()
            le_cursor.setPosition(self._line_edit.min_pos + index + len(text_to_insert))
            self._line_edit.setTextCursor(le_cursor)

    @Slot(bool)
    def _restart_persistent(self, _=False):
        """Restarts underlying persistent process."""
        self._updating = True
        self.clear()
        self._make_prompt_block("")
        self._updating = False
        self._text_buffer.clear()
        self._executor.submit(self._do_restart_persistent)

    def _do_restart_persistent(self):
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        for msg in engine_mngr.restart_persistent(self._key):
            self._msg_available.emit(msg["type"], msg["data"])
        self._restarted.emit()

    @Slot()
    def _handle_restarted(self):
        self._do_set_killed(False)
        self._make_prompt_block(prompt=self._prompt)

    @Slot(bool)
    def _interrupt_persistent(self, _=False):
        """Sends a task to executor which will interrupt the underlying persistent process."""
        self._executor.submit(self._do_interrupt_persistent)

    def _do_interrupt_persistent(self):
        """Interrupts the underlying persistent process."""
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        engine_mngr.interrupt_persistent(self._key)

    @Slot(bool)
    def _kill_persistent(self, _=False):
        """Sends a task to executor which will kill the underlying persistent process."""
        self._do_set_killed(True)
        self._executor.submit(self._do_kill_persistent)

    def _do_kill_persistent(self):
        """Kills underlying persistent process."""
        engine_mngr = self.create_engine_manager()
        if not engine_mngr:
            return
        engine_mngr.kill_persistent(self._key)

    def _extend_menu(self, menu):
        """Appends two more actions: Restart, and Interrupt.

        Args:
            menu (QMenu): where to append
        """
        menu.addSeparator()
        menu.addAction("Restart", self._restart_persistent)
        menu.addAction("Interrupt", self._interrupt_persistent).setEnabled(not self._is_dead)
        menu.addAction("Kill", self._kill_persistent).setEnabled(not self._is_dead)

    def contextMenuEvent(self, ev):
        """Reimplemented to extend menu with custom actions."""
        le_geom = self._line_edit.frameGeometry()
        menu = (
            self._line_edit.createStandardContextMenu()
            if le_geom.contains(ev.pos())
            else self.createStandardContextMenu()
        )
        self._extend_menu(menu)
        menu.exec(ev.globalPos())


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
