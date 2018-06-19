#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Functions to make and handle QToolBars.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.1.2018
"""

import logging
from PySide2.QtGui import QIcon, QPixmap, QDrag, QPen, QBrush, QColor, QFont
from PySide2.QtWidgets import QToolBar, QLabel, QAction, QApplication
from PySide2.QtCore import Qt, QMimeData
from config import ICON_TOOLBAR_SS
from graphics_items import ItemImage
from helpers import item_to_pixmap

class ItemToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions"""
    def __init__(self, parent):
        """Init class"""
        super().__init__("Add Item Toolbar", parent)
        text_font = QFont("Helvetica", 24, QFont.Bold)
        text_pen = QPen(Qt.white)
        item_pen = Qt.NoPen
        label = QLabel("Add Item")
        self.addWidget(label)
        # Draw item pixmaps
        # DS
        data_store_brush = QBrush(QColor(0, 255, 255, 160))
        data_store_item = ItemImage(None, 0, 0, 70, 70, '').make_data_master(item_pen, data_store_brush)
        data_store_pixmap = item_to_pixmap(data_store_item, text="DS", pen=text_pen, font=text_font)
        data_store_widget = DraggableWidget(self, data_store_pixmap, "Data Store")
        data_store_action = self.addWidget(data_store_widget)
        # DC
        data_connection_brush = QBrush(QColor(0, 0, 255, 160))
        data_connection_item = ItemImage(None, 0, 0, 70, 70, '').make_data_master(item_pen, data_connection_brush)
        data_connection_pixmap = item_to_pixmap(data_connection_item, text="DC", pen=text_pen, font=text_font)
        data_connection_widget = DraggableWidget(self, data_connection_pixmap, "Data Connection")
        data_connection_action = self.addWidget(data_connection_widget)
        # Tool
        tool_brush = QBrush(QColor(255, 0, 0, 160))
        tool_item = ItemImage(None, 0, 0, 70, 70, '').make_master(item_pen, tool_brush)
        tool_pixmap = item_to_pixmap(tool_item, text="T", pen=text_pen, font=text_font)
        tool_widget = DraggableWidget(self, tool_pixmap, "Tool")
        tool_action = self.addWidget(tool_widget)
        # View
        view_brush = QBrush(QColor(0, 255, 0, 160))
        view_item = ItemImage(None, 0, 0, 70, 70, '').make_master(item_pen, view_brush)
        view_pixmap = item_to_pixmap(view_item, text="V", pen=text_pen, font=text_font)
        view_widget = DraggableWidget(self, view_pixmap, "View")
        view_action = self.addWidget(view_widget)
        # set remove all action
        remove_all_icon = QIcon()
        remove_all_icon.addPixmap(QPixmap(":/icons/remove_all.png"), QIcon.Normal, QIcon.On)
        remove_all = QAction(remove_all_icon, "Remove All", parent)
        remove_all.triggered.connect(parent.remove_all_items)
        self.addSeparator()
        self.addAction(remove_all)
        # Set stylesheet
        self.setStyleSheet(ICON_TOOLBAR_SS)
        self.setObjectName("ItemToolbar")


class DraggableWidget(QLabel):
    """A draggable QLabel"""
    def __init__(self, parent, pixmap, text):
        super().__init__(parent)
        self.text = text
        self.setPixmap(pixmap.scaled(28, 28))
        self.drag_start_pos = None
        self.setToolTip("""
            <p>Drag-and-drop this icon onto the project view to create a new <b>{}</b> item.</p>
        """.format(self.text))
        self.setAlignment(Qt.AlignHCenter)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def mousePressEvent(self, event):
        """Register drag start position"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.text)
        drag.setMimeData(mimeData)
        drag.setPixmap(self.pixmap())
        drag.setHotSpot(self.pixmap().rect().center())
        dropAction = drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None
