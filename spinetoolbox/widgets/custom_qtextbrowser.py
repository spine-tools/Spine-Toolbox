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

"""Class for a custom QTextBrowser for showing the logs and tool output."""
from contextlib import contextmanager
from PySide6.QtCore import Slot
from PySide6.QtGui import QTextCursor, QFontDatabase, QTextBlockFormat, QTextFrameFormat, QBrush, QAction, QPalette
from PySide6.QtWidgets import QTextBrowser, QMenu
from ..config import TEXTBROWSER_SS
from ..helpers import scrolling_to_bottom


class CustomQTextBrowser(QTextBrowser):
    """Custom QTextBrowser class."""

    _ALL_RUNS = "All executions"

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        self._toolbox = None
        self.document().setMaximumBlockCount(2000)
        self.setStyleSheet(TEXTBROWSER_SS)
        self.setOpenExternalLinks(True)
        self.setOpenLinks(False)  # Don't try open file:/// links in the browser widget, we'll open them externally
        self._executions_menu = QMenu(self)
        self._item_cursors = {}
        self._item_filter_cursors = {}
        self._item_anchors = {}
        self._visible_timestamp = None
        self._executing_timestamp = None
        self._execution_blocks = {}
        self._frame_format = QTextFrameFormat()
        self._frame_format.setMargin(4)
        self._frame_format.setLeftMargin(8)
        self._frame_format.setPadding(2)
        self._frame_format.setBorder(1)
        self._selected_frame_format = QTextFrameFormat(self._frame_format)
        palette = self.palette()
        self._selected_frame_format.setBackground(QBrush(palette.color(QPalette.Highlight).darker()))
        self._executions_menu.aboutToShow.connect(self._populate_executions_menu)
        self._executions_menu.triggered.connect(self._select_execution)

    def set_toolbox(self, toolbox):
        self._toolbox = toolbox
        self._toolbox.ui.toolButton_executions.setMenu(self._executions_menu)
        self._toolbox.ui.toolButton_executions.hide()

    @Slot(str)
    def append(self, text):
        """
        Appends new text block to the end of the *original* document.

        If the document contains more text blocks after the addition than a set limit,
        blocks are deleted at the start of the contents.

        Args:
            text (str): text to add
        """
        with scrolling_to_bottom(self):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertBlock()
            cursor.insertHtml(text)

    def contextMenuEvent(self, event):
        """Reimplemented method to add a clear action into the default context menu.

        Args:
            event (QContextMenuEvent): Received event
        """
        clear_action = QAction("Clear", self)
        # noinspection PyUnresolvedReferences
        clear_action.triggered.connect(lambda: self.clear())  # pylint: disable=unnecessary-lambda
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(clear_action)
        menu.exec(event.globalPos())

    def clear(self):
        super().clear()
        self.reset_executions_button_text()
        self._item_cursors = {}
        self._item_filter_cursors = {}
        self._item_anchors = {}
        self._visible_timestamp = None
        self._execution_blocks = {}

    @Slot()
    def _populate_executions_menu(self):
        texts = [self._ALL_RUNS] + self.execution_timestamps()
        self._executions_menu.clear()
        for text in texts:
            action = self._executions_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(text == self._toolbox.ui.toolButton_executions.text())

    def reset_executions_button_text(self):
        self._toolbox.ui.toolButton_executions.setText(self._ALL_RUNS)
        self._toolbox.ui.toolButton_executions.setVisible(False)

    @Slot(QAction)
    def _select_execution(self, action):
        text = action.text()
        self._toolbox.ui.toolButton_executions.setText(text)
        if text == self._ALL_RUNS:
            self.select_all_executions()
            return
        self.select_execution(text)

    @staticmethod
    def _make_log_entry_title(title):
        return f"<b>{title}</b>"

    def make_log_entry_point(self, timestamp):
        """Creates cursors (log entry points) for given items in event log.

        Args:
            timestamp (str): time stamp
        """
        self._toolbox.ui.toolButton_executions.setVisible(True)
        self._executing_timestamp = timestamp
        self.select_execution(timestamp)

    def add_log_message(self, item_name, filter_id, message):
        """Adds a message to an item's execution log.

        Args:
            item_name (str): item name
            filter_id (str): filter identifier
            message (str): formatted message
        """
        item_blocks = self._execution_blocks.setdefault(self._executing_timestamp, {})
        if item_name not in item_blocks:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertFrame(self._frame_format)
            item_blocks[item_name] = [cursor.block()]
            self._item_anchors[self._executing_timestamp, item_name] = anchor = self._executing_timestamp + item_name
            title = self._make_log_entry_title(item_name)
            cursor.insertHtml(f'<a name="{anchor}">{title}</a>')
            self._item_cursors[self._executing_timestamp, item_name] = cursor
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            item_blocks[item_name].append(cursor.block())
            self._item_filter_cursors[self._executing_timestamp, item_name] = {}
        blocks = item_blocks[item_name]
        with scrolling_to_bottom(self):
            cursor = self._item_cursors[self._executing_timestamp, item_name]
            if filter_id:
                filter_cursors = self._item_filter_cursors[self._executing_timestamp, item_name]
                if filter_id not in filter_cursors:
                    filter_cursor = QTextCursor(cursor)
                    filter_cursor.insertFrame(self._frame_format)
                    title = self._make_log_entry_title(filter_id)
                    filter_cursor.insertHtml(title)
                    blocks.append(filter_cursor.block())
                    filter_cursors[filter_id] = filter_cursor
                    cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
                    blocks.append(cursor.block())
                cursor = filter_cursors[filter_id]
            cursor.insertBlock()
            cursor.insertHtml(message)
            blocks.append(cursor.block())
        self.set_item_log_selected(True)

    def execution_timestamps(self):
        return list(self._execution_blocks)

    def select_all_executions(self):
        for timestamp in self._execution_blocks:
            self._set_execution_visible(timestamp, True)

    def select_execution(self, timestamp):
        self._toolbox.ui.toolButton_executions.setText(timestamp)
        self._set_execution_visible(timestamp, True)
        for other_timestamp in set(self._execution_blocks) - {timestamp}:
            self._set_execution_visible(other_timestamp, False)

    def _set_execution_visible(self, timestamp, visible):
        if visible:
            if timestamp == self._visible_timestamp:
                return
            self.set_item_log_selected(False)
            self._visible_timestamp = timestamp
        block_format = QTextBlockFormat()
        if not visible:
            block_format.setLineHeight(0, QTextBlockFormat.FixedHeight.value)
        frame_format = self._frame_format if visible else QTextFrameFormat()
        item_blocks = self._execution_blocks.get(timestamp, {})
        all_blocks = [block for blocks in item_blocks.values() for block in blocks]
        cursor = self.textCursor()
        with scrolling_to_bottom(self):
            for block in all_blocks:
                block.setVisible(visible)
                cursor.setPosition(block.position())
                cursor.setBlockFormat(block_format)
                frame = cursor.currentFrame()
                if frame != self.document().rootFrame():
                    frame.setFrameFormat(frame_format)
        self.set_item_log_selected(True)

    def set_item_log_selected(self, selected):
        active_item = self._toolbox.active_project_item or self._toolbox.active_link_item
        if not active_item:
            return
        item_name = active_item.name
        anchor = self._item_anchors.get((self._visible_timestamp, item_name))
        if anchor is not None and selected:
            self.scrollToAnchor(anchor)
        cursor = self._item_cursors.get((self._visible_timestamp, item_name))
        if cursor is not None:
            frame = cursor.currentFrame()
            frame_format = self._selected_frame_format if selected else self._frame_format
            frame.setFrameFormat(frame_format)


class MonoSpaceFontTextBrowser(CustomQTextBrowser):
    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
