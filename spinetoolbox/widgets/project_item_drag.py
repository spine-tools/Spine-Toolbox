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

"""Classes for custom QListView."""
from textwrap import fill
from PySide6.QtCore import Qt, Signal, Slot, QMimeData
from PySide6.QtGui import QDrag, QIcon, QPainter, QBrush, QColor, QIconEngine, QCursor
from PySide6.QtWidgets import QToolButton, QApplication, QToolTip


class ProjectItemDragMixin:
    """Custom class with dragging support."""

    drag_about_to_start = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reset()

    def _reset(self):
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        super().mouseMoveEvent(event)
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.position().toPoint() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        drag.setPixmap(self.pixmap)
        drag.setMimeData(self.mime_data)
        drag.setHotSpot(self.pixmap.rect().center())
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None
        self.drag_about_to_start.emit()
        drag.exec()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        super().mouseReleaseEvent(event)
        self._reset()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setCursor(Qt.OpenHandCursor)


class NiceButton(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)

    def setText(self, text):
        super().setText(fill(text, width=12, break_long_words=False))

    def set_orientation(self, orientation):
        if orientation == Qt.Orientation.Horizontal:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.setStyleSheet("QToolButton{margin: 16px 2px 2px 2px;}")
        else:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.setStyleSheet("QToolButton{margin: 2px;}")


class ProjectItemButtonBase(ProjectItemDragMixin, NiceButton):
    def __init__(self, toolbox, item_type, icon, parent=None):
        super().__init__(parent=parent)
        self._toolbox = toolbox
        self.item_type = item_type
        self._icon = icon
        self.setIcon(icon)
        self.setMouseTracking(True)
        self.drag_about_to_start.connect(self._handle_drag_about_to_start)
        self.clicked.connect(self._show_tool_tip)

    @Slot(bool)
    def _show_tool_tip(self, _=False):
        QToolTip.showText(QCursor.pos(), self.toolTip())

    def set_colored_icons(self, colored):
        self._icon.set_colored(colored)

    @Slot()
    def _handle_drag_about_to_start(self):
        self.setDown(False)
        self.update()

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            self.pixmap = self.icon().pixmap(self.iconSize())
            self.mime_data = QMimeData()
            self.mime_data.setText(self._make_mime_data_text())

    def _make_mime_data_text(self):
        raise NotImplementedError()


class ProjectItemButton(ProjectItemButtonBase):
    double_clicked = Signal()

    def __init__(self, toolbox, item_type, icon, parent=None):
        super().__init__(toolbox, item_type, icon, parent=parent)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")
        self.setText(item_type)

    def _make_mime_data_text(self):
        return ",".join([self.item_type, ""])

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()


class ProjectItemSpecButton(ProjectItemButtonBase):
    def __init__(self, toolbox, item_type, icon, spec_name="", parent=None):
        super().__init__(toolbox, item_type, icon, parent=parent)
        self._spec_name = None
        self._index = None
        self.spec_name = spec_name
        self.setText(self.spec_name)

    @property
    def spec_name(self):
        return self._spec_name

    @spec_name.setter
    def spec_name(self, spec_name):
        self._spec_name = spec_name
        self.setText(self._spec_name)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{self.spec_name}</b> item.</p>")

    def _make_mime_data_text(self):
        return ",".join([self.item_type, self.spec_name])

    def contextMenuEvent(self, event):
        index = self._toolbox.specification_model.specification_index(self.spec_name)
        self._toolbox.show_specification_context_menu(index, event.globalPos())

    def mouseDoubleClickEvent(self, event):
        index = self._toolbox.specification_model.specification_index(self.spec_name)
        self._toolbox.edit_specification(index, None)


class ShadeMixin:
    def paintEvent(self, ev):
        painter = QPainter(self)
        brush = QBrush(QColor(255, 255, 255, a=96))
        rect = ev.rect()
        painter.fillRect(rect, brush)
        painter.end()
        super().paintEvent(ev)


class ShadeProjectItemSpecButton(ShadeMixin, ProjectItemSpecButton):
    def clone(self):
        return ShadeProjectItemSpecButton(self._toolbox, self.item_type, self.icon(), self.spec_name)


class ShadeButton(ShadeMixin, NiceButton):
    pass


class _ChoppedIcon(QIcon):
    def __init__(self, icon, size):
        self._engine = _ChoppedIconEngine(icon, size)
        super().__init__(self._engine)

    def update(self):
        self._engine.update()


class _ChoppedIconEngine(QIconEngine):
    def __init__(self, icon, size):
        super().__init__()
        self._pixmap = None
        self._icon = icon
        self._size = size
        self.update()

    def update(self):
        self._pixmap = self._icon.pixmap(self._icon.actualSize(self._size))

    def pixmap(self, size, mode, state):
        return self._pixmap
