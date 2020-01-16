######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

from PySide2.QtCore import Slot
from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import QTextBrowser, QAction


class CustomQTextBrowser(QTextBrowser):
    """Custom QTextBrowser class.

    Attributes:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._max_blocks = 2000

    @Slot(str, name="append")
    def append(self, text):
        """
        Appends new text block to the end of the current contents.

        If the widget contains more text blocks after the addition than a set limit,
        blocks will be deleted at the start of the contents.

        Args:
            text (str): text to add
        """
        super().append(text)
        block_count = super().document().blockCount()
        if block_count > self._max_blocks:
            blocks_to_remove = block_count - self._max_blocks
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(blocks_to_remove):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove the trailing newline

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
        """Returns the upper limit of text blocks that can be appended to the widget."""
        return self._max_blocks

    @max_blocks.setter
    def max_blocks(self, new_max):
        """Sets the upper limit of text blocks that can be appended to the widget."""
        self._max_blocks = new_max if new_max > 0 else 2000
