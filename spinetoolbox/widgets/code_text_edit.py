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
Provides simple text editor for programming purposes.

:author: M. Marin (KTH)
:date:   28.1.2020
"""

from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token
from PySide2.QtWidgets import QWidget, QPlainTextEdit, QPlainTextDocumentLayout
from PySide2.QtGui import QColor, QFontMetrics, QFontDatabase, QPainter
from PySide2.QtCore import QSize, Slot, QRect, Qt
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
        foreground_color = self._style.styles[Token.Text]
        self.setStyleSheet(
            f"QPlainTextEdit {{background-color: {self._style.background_color}; color: {foreground_color};}}"
        )
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width()

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())

    def set_lexer_name(self, lexer_name):
        try:
            self._highlighter.lexer = get_lexer_by_name(lexer_name)
            self._highlighter.rehighlight()
        except ClassNotFound:
            # No lexer for aliases 'gams' nor 'executable'
            pass

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
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self._line_number_area.setGeometry(QRect(rect.left(), rect.top(), self.line_number_area_width(), rect.height()))

    def line_number_area_paint_event(self, ev):
        foreground_color = QColor(self._style.styles[Token.Text]).darker()
        painter = QPainter(self._line_number_area)
        painter.setFont(self.font())
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= ev.rect().bottom():
            if block.isVisible() and bottom >= ev.rect().top():
                if block == self.textCursor().block():
                    painter.fillRect(
                        0, top, self._line_number_area.width(), self.fontMetrics().height(), foreground_color.darker()
                    )
                number = str(block_number + 1)
                painter.setPen(foreground_color)
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - self._right_margin,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
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
