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
from PySide6.QtGui import QColor, QFontMetricsF, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsRectItem

from ..project_item_icon import ProjectItemIcon

_MARGIN = 14
_HEADER_HEIGHT = 26


class GroupFrameItem(QGraphicsRectItem):
    """Dashed, non-interactive outline for a stack, with its name in the top-left corner."""

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
        self.setBrush(Qt.BrushStyle.NoBrush)
        # Frame itself should not become the selected item; clicking it selects its members instead
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.stack_key = None
        self.setZValue(-1)

    def shape(self) -> QPainterPath:
        """Limits hit-testing to the border, so the frame never steals clicks from icons on top of it."""
        path = QPainterPath()
        path.addRect(self.rect())
        return path

    def set_rect_from_members(self, icons: list) -> None:
        """Fits the frame around member icons and labels, leaving room for the group title."""
        if not icons:
            return
        rect = icons[0].sceneBoundingRect().united(icons[0].name_item.sceneBoundingRect())
        for icon in icons[1:]:
            rect = rect.united(icon.sceneBoundingRect()).united(icon.name_item.sceneBoundingRect())
        rect = rect.adjusted(-_MARGIN, -_MARGIN - _HEADER_HEIGHT, _MARGIN, _MARGIN)
        title_width = QFontMetricsF(QApplication.font()).horizontalAdvance(self._name) + 2 * _MARGIN
        rect.setWidth(max(rect.width(), title_width))
        self.setRect(rect)

    def paint(self, painter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setPen(self.pen())
        title_rect = self.rect().adjusted(8, 4, -8, 0)
        title_rect.setHeight(_HEADER_HEIGHT - 4)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self._name)

    def mousePressEvent(self, event) -> None:
        """Selects all project item icons that belong to this group when the frame is clicked."""
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        scene = self.scene()
        if scene is None or self.stack_key is None:
            return super().mousePressEvent(event)
        # Get stack member names from the project via the scene's toolbox
        try:
            project = scene._toolbox.project()
        except Exception:
            project = None
        if project is None:
            return super().mousePressEvent(event)
        stack = project.stacks.get(self.stack_key)
        if not stack:
            return super().mousePressEvent(event)
        member_names = set(stack.get("items", []))
        # Clear existing selection and select matching icons
        scene.clearSelection()
        for item in scene.items():
            if isinstance(item, ProjectItemIcon) and item.name() in member_names:
                item.setSelected(True)
        event.accept()
