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

"""
Class for a custom QTextBrowser for showing the logs and tool output.

:author: P. Savolainen (VTT)
:date:   6.2.2018
"""

from contextlib import contextmanager
from PySide2.QtCore import Slot, Signal
from PySide2.QtGui import QTextCursor, QFontDatabase
from PySide2.QtWidgets import QTextBrowser, QAction
from ..config import TEXTBROWSER_SS


class CustomQTextBrowser(QTextBrowser):
    """Custom QTextBrowser class."""

    #FIXME: When clear(), we need to reset execution stuff in toolbox
    cleared = Signal()

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        self.setStyleSheet(TEXTBROWSER_SS)
        self._max_blocks = 2000
        self.setOpenExternalLinks(True)
        self.setOpenLinks(False)  # Don't try open file:/// links in the browser widget, we'll open them externally

    @Slot()
    def scroll_to_bottom(self):
        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.setValue(vertical_scroll_bar.maximum())

    @contextmanager
    def housekeeping(self):
        """A context manager to keep the text browser at bottom and manage the maximum number of blocks."""
        scrollbar = self.verticalScrollBar()
        keep_at_bottom = scrollbar.value() in (scrollbar.maximum(), 0)
        try:
            yield None
        finally:
            block_count = self.document().blockCount()
            if block_count > self._max_blocks:
                blocks_to_remove = block_count - self._max_blocks
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Start)
                for _ in range(blocks_to_remove):
                    cursor.select(QTextCursor.BlockUnderCursor)
                    cursor.removeSelectedText()
                    cursor.deleteChar()  # Remove the trailing newline
            if keep_at_bottom:
                self.scroll_to_bottom()

    @Slot(str)
    def append(self, text):
        """
        Appends new text block to the end of the *original* document.

        If the document contains more text blocks after the addition than a set limit,
        blocks are deleted at the start of the contents.

        Args:
            text (str): text to add
        """
        with self.housekeeping():
            cursor = self.textCursor()
            cursor.movePosition(cursor.End)
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
        menu.exec_(event.globalPos())

    @property
    def max_blocks(self):
        """int: the upper limit of text blocks that can be appended to the widget."""
        return self._max_blocks

    @max_blocks.setter
    def max_blocks(self, new_max):
        self._max_blocks = new_max if new_max > 0 else 2000

    def clear(self):
        super().clear()
        self.cleared.emit()

class MonoSpaceFontTextBrowser(CustomQTextBrowser):
    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
