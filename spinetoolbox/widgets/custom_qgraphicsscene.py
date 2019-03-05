######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Custom QGraphicsScene used in the Design View.

:author: P. Savolainen (VTT)
:date:   13.2.2019
"""

import logging
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QColor, QPen, QBrush
from graphics_items import DataConnectionIcon, ToolIcon, DataStoreIcon, ViewIcon
from widgets.toolbars import DraggableWidget


class CustomQGraphicsScene(QGraphicsScene):
    """A scene that handles drag and drop events of DraggableWidget sources."""

    files_dropped_on_dc = Signal("QGraphicsItem", "QVariant", name="files_dropped_on_dc")

    def __init__(self, parent, toolbox):
        """Initialize class."""
        super().__init__(parent)
        self._toolbox = toolbox
        self.item_shadow = None
        # Set background attributes
        grid = self._toolbox.qsettings().value("appSettings/bgGrid", defaultValue="false")
        self.bg_grid = False if grid == "false" else True
        bg_color = self._toolbox.qsettings().value("appSettings/bgColor", defaultValue="false")
        self.bg_color = QColor("#f5f5f5") if bg_color == "false" else bg_color

    def set_bg_color(self, color):
        """Change background color when this is changed in Settings.

        Args:
            color (QColor): Background color
        """
        self.bg_color = color

    def set_bg_grid(self, bg):
        """Enable or disable background grid.

        Args:
            bg (boolean): True to draw grid, False to fill background with a solid color
        """
        self.bg_grid = bg

    def dragLeaveEvent(self, event):
        """Accept event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a DraggableWidget (from Add Item toolbar)."""
        event.accept()
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a DraggableWidget (from Add Item toolbar)."""
        event.accept()
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of
        DraggableWidget (from Add Item toolbar).
        Capture text from event's mimedata and show the appropriate 'Add Item form.'
        """
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dropEvent(event)
            return
        if not self._toolbox.project():
            self._toolbox.msg.emit("Create or open a project first")
            event.ignore()
            return
        event.acceptProposedAction()
        text = event.mimeData().text()
        pos = event.scenePos()
        x = pos.x() - 35
        y = pos.y() - 35
        w = 70
        h = 70
        # TODO: Check if the item_shadow stays on scene or if its deleted?
        if text == "Data Store":
            self.item_shadow = DataStoreIcon(self._toolbox, x, y, w, h, "")
            self._toolbox.show_add_data_store_form(pos.x(), pos.y())
        elif text == "Data Connection":
            self.item_shadow = DataConnectionIcon(self._toolbox, x, y, w, h, "")
            self._toolbox.show_add_data_connection_form(pos.x(), pos.y())
        elif text == "Tool":
            self.item_shadow = ToolIcon(self._toolbox, x, y, w, h, "")
            self._toolbox.show_add_tool_form(pos.x(), pos.y())
        elif text == "View":
            self.item_shadow = ViewIcon(self._toolbox, x, y, w, h, "")
            self._toolbox.show_add_view_form(pos.x(), pos.y())

    def drawBackground(self, painter, rect):
        """Reimplemented method to make a custom background.

        Args:
            painter (QPainter): Painter that is used to paint background
            rect (QRectF): The exposed (viewport) rectangle in scene coordinates
        """
        rect = self.sceneRect()  # Override to only draw background for the scene rectangle
        if not self.bg_grid:
            painter.fillRect(rect, QBrush(self.bg_color))
            return
        step = 20  # Grid step
        # logging.debug("sceneRect pos:({0:.1f}, {1:.1f}) size:({2:.1f}, {3:.1f})"
        #               .format(rect.x(), rect.y(), rect.width(), rect.height()))
        painter.setPen(QPen(QColor(0, 0, 0, 40)))
        # Draw horizontal grid
        start = round(rect.top(), step)
        if start > rect.top():
            start -= step
        y = start
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += step
        # Now draw vertical grid
        start = round(rect.left(), step)
        if start > rect.left():
            start -= step
        x = start
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += step
