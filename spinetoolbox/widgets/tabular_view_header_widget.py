######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains TabularViewHeaderWidget class.

:authors: P. Vennström (VTT), M. Marin (KTH)
:date:   2.12.2019
"""

from PySide2.QtCore import Qt, QMimeData, Signal
from PySide2.QtWidgets import QFrame, QToolButton, QApplication, QLabel, QHBoxLayout
from PySide2.QtGui import QDrag, QPalette
from .custom_menus import FilterMenu


class TabularViewHeaderWidget(QFrame):
    """A draggable QWidget."""

    header_dropped = Signal(object, object, str)

    def __init__(self, parent, name, area):
        """

        Args:
            parent (QWidget): Parent widget
            name (str)
            area (str): either "top" or "left"
        """
        super().__init__(parent=parent)
        self._name = name
        self._area = area
        layout = QHBoxLayout(self)
        button = QToolButton(self)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setArrowType(Qt.DownArrow)
        button.setStyleSheet("QToolButton {border: none;}")
        self.menu = FilterMenu(self)
        # menu.filterChanged.connect(self.change_filter)
        button.setMenu(self.menu)
        self.drag_start_pos = None
        # TODO: self.setToolTip("<p>Drag-and-drop this ...</p>")
        label = QLabel(name)
        layout.addWidget(label)
        layout.addWidget(button)
        h_margin = 3
        layout.setContentsMargins(h_margin, 0, h_margin, 0)
        spacing = 16
        if area == "rows":
            h_alignment = Qt.AlignLeft
            layout.insertSpacing(1, spacing)
        elif area == "columns":
            h_alignment = Qt.AlignRight
            layout.insertSpacing(0, spacing)
        label.setAlignment(h_alignment | Qt.AlignVCenter)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Raised)
        self.setFrameShape(QFrame.Panel)
        self.setBackgroundRole(QPalette.Window)
        self.setAcceptDrops(True)

    @property
    def name(self):
        return self._name

    @property
    def area(self):
        return self._area

    def mousePressEvent(self, event):
        """Register drag start position"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    # noinspection PyArgumentList, PyUnusedLocal
    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self._name)
        drag.setMimeData(mime_data)
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        other = event.source()
        if other == self:
            return
        center = self.rect().center()
        drop = event.pos()
        if self.area == "rows":
            position = "before" if center.x() > drop.x() else "after"
        elif self.area == "columns":
            position = "before" if center.y() > drop.y() else "after"
        self.header_dropped.emit(other, self, position)
