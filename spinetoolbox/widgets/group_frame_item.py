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

"""A dashed outline drawn behind a stack's member icons in the Design View."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem

_MARGIN = 14


class GroupFrameItem(QGraphicsRectItem):
    """Dashed, non-interactive outline for a stack, with its name in the top-left corner."""

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
        self.setBrush(Qt.BrushStyle.NoBrush)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(False)
        self.setZValue(-1)

    def shape(self) -> QPainterPath:
        """Limits hit-testing to the border, so the frame never steals clicks from icons on top of it."""
        path = QPainterPath()
        path.addRect(self.rect())
        return path

    def set_rect_from_members(self, icons: list) -> None:
        """Fits the frame around the union of the given icons' scene bounding rects, plus a margin."""
        if not icons:
            return
        rect = icons[0].sceneBoundingRect()
        for icon in icons[1:]:
            rect = rect.united(icon.sceneBoundingRect())
        rect = rect.adjusted(-_MARGIN, -_MARGIN, _MARGIN, _MARGIN)
        self.setRect(rect)

    def paint(self, painter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setPen(self.pen())
        painter.drawText(
            self.rect().adjusted(4, 2, -4, -2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self._name
        )
