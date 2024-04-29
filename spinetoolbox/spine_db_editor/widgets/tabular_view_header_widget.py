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

"""Contains TabularViewHeaderWidget class."""
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtWidgets import QFrame, QToolButton, QApplication, QLabel, QHBoxLayout, QWidget
from PySide6.QtGui import QDrag
from ..mvcmodels.colors import PIVOT_TABLE_HEADER_COLOR


class TabularViewHeaderWidget(QFrame):
    """A draggable QWidget."""

    header_dropped = Signal(QWidget, QWidget, str)
    _H_MARGIN = 3
    _SPACING = 16

    def __init__(self, identifier, area, menu=None, parent=None):
        """

        Args:
            identifier (str)
            area (str): either "rows", "columns", or "frozen"
            menu (FilterMenu, optional)
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent=parent)
        self._identifier = identifier
        self._area = area
        layout = QHBoxLayout(self)
        button = QToolButton(self)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setStyleSheet("QToolButton {border: none;}")
        button.setEnabled(menu is not None)
        if menu:
            self.menu = menu
            button.setMenu(self.menu)
            self.menu.anchor = self
        self.drag_start_pos = None
        label = QLabel(identifier)
        layout.addWidget(label)
        layout.addWidget(button)
        layout.setContentsMargins(self._H_MARGIN, 0, self._H_MARGIN, 0)
        if area == "rows":
            h_alignment = Qt.AlignLeft
            layout.insertSpacing(1, self._SPACING)
            button.setArrowType(Qt.DownArrow)
        elif area == "columns":
            h_alignment = Qt.AlignRight
            layout.insertSpacing(0, self._SPACING)
            button.setArrowType(Qt.RightArrow)
        elif area == "frozen":
            h_alignment = Qt.AlignHCenter
        label.setAlignment(h_alignment | Qt.AlignVCenter)
        label.setStyleSheet("QLabel {font-weight: bold;}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Raised)
        self.setFrameShape(QFrame.Panel)
        self.setStyleSheet(f"QFrame {{background: {PIVOT_TABLE_HEADER_COLOR.name()};}}")
        self.setAcceptDrops(True)
        self.setToolTip(
            "<p>This is a draggable header. </p>"
            "<p>Drag-and-drop it onto another header to pivot the table, "
            "or onto the Frozen table to freeze this dimension.</p>"
        )
        self.adjustSize()
        self.setMinimumWidth(self.size().width())

    @property
    def identifier(self):
        return self._identifier

    @property
    def area(self):
        return self._area

    def mousePressEvent(self, event):
        """Register drag start position"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.position().toPoint()

    # noinspection PyArgumentList, PyUnusedLocal
    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.position().toPoint() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        drag.setMimeData(mime_data)
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        other = event.source()
        if other is self:
            return
        center = self.rect().center()
        drop = event.pos()
        if self.area in ("rows", "frozen"):
            position = "before" if center.x() > drop.x() else "after"
        elif self.area == "columns":
            position = "before" if center.y() > drop.y() else "after"
        else:
            raise RuntimeError(f"Logic error: invalid area '{self.area}'")
        self.header_dropped.emit(other, self, position)
