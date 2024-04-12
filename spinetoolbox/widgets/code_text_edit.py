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

"""Provides simple text editor for programming purposes."""
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QPlainTextDocumentLayout
from PySide6.QtGui import QColor, QFontMetrics, QFontDatabase, QPainter
from PySide6.QtCore import QSize, Slot, QRect, Qt
from spinetoolbox.helpers import CustomSyntaxHighlighter


class CodeTextEdit(QPlainTextEdit):
    """A plain text edit with syntax highlighting and line numbers."""

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self._highlighter = CustomSyntaxHighlighter(self)
        self._style = get_style_by_name("monokai")
        self._highlighter.set_style(self._style)
        self._line_number_area = LineNumberArea(self)
        self._right_margin = 16
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.setFont(font)
        self.foreground_color = self._style.styles[Token]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {self._style.background_color}; color: {self.foreground_color};}}"
        )
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._cursor_block = None
        self.cursorPositionChanged.connect(self._update_line_number_area_cursor_position)
        self._update_line_number_area_width()
        self._file_selected = False

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())

    def file_selected(self, status):
        self._file_selected = status

    def set_lexer_name(self, lexer_name):
        try:
            self._highlighter.lexer = get_lexer_by_name(lexer_name)
            self._highlighter.rehighlight()
        except ClassNotFound:
            # No lexer for aliases 'gams' nor 'executable'
            pass

    def setPlainText(self, text):
        doc = self.document()
        doc.setPlainText(text)
        self.setDocument(doc)

    def setDocument(self, doc):
        doc.setDocumentLayout(QPlainTextDocumentLayout(doc))
        super().setDocument(doc)
        self._highlighter.setDocument(doc)
        doc.setDefaultFont(self.font())
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(4 * " "))

    def line_number_area_width(self):
        digits = 1
        m = max(1, self.blockCount())
        while m > 10:
            m /= 10
            digits += 1
        return self._right_margin / 2 + self.fontMetrics().horizontalAdvance("9") * digits + self._right_margin

    @Slot(int)
    def _update_line_number_area_width(self, _new_block_count=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    @Slot(QRect, int)
    def _update_line_number_area(self, rect, dy):
        if dy != 0:
            self._line_number_area.scroll(0, dy)
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

    @Slot()
    def _update_line_number_area_cursor_position(self):
        if self._cursor_block is None:
            self._cursor_block = self.textCursor().block()
        elif self._cursor_block.blockNumber() == self.textCursor().blockNumber():
            return
        new_cursor_block = self.textCursor().block()
        old_top = round(self.blockBoundingGeometry(self._cursor_block).translated(self.contentOffset()).top())
        new_top = round(self.blockBoundingGeometry(new_cursor_block).translated(self.contentOffset()).top())
        old_bottom = old_top + round(self.blockBoundingGeometry(self._cursor_block).height())
        new_bottom = new_top + round(self.blockBoundingGeometry(new_cursor_block).height())
        top = min(old_top, new_top)
        bottom = max(old_bottom, new_bottom)
        self._line_number_area.update(0, top, self._line_number_area.width(), bottom - top)
        self._cursor_block = new_cursor_block

    def set_enabled_with_greyed(self, enabled):
        super().setEnabled(enabled)
        if enabled:
            x = f"QPlainTextEdit {{background-color: {self._style.background_color}; color: {self.foreground_color};}}"
        else:
            x = f"QPlainTextEdit {{background-color: #737373; color: {self.foreground_color};}}"
        self.setStyleSheet(x)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self._line_number_area.setGeometry(QRect(rect.left(), rect.top(), self.line_number_area_width(), rect.height()))

    def line_number_area_paint_event(self, ev):
        foreground_color = QColor(self._highlighter.formats[Token.Text].foreground().color()).darker(120)
        painter = QPainter(self._line_number_area)
        painter.setFont(self.font())
        painter.setPen(foreground_color)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        width = self._line_number_area.width()
        while block.isValid() and top <= ev.rect().bottom():
            if self._file_selected:
                if block.isVisible() and bottom >= ev.rect().top():
                    if block_number == self.textCursor().blockNumber():
                        painter.fillRect(0, top, width, bottom - top, foreground_color.darker())
                    number = str(block_number + 1)
                    painter.drawText(0, top, width - self._right_margin, bottom - top, Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
        painter.end()


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, ev):
        self._editor.line_number_area_paint_event(ev)
