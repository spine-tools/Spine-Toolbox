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
Class for a custom QGraphicsView for visualizing project items and connections.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   6.2.2018
"""

import logging
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene
from PySide2.QtCore import Slot, Qt, QRectF
from PySide2.QtGui import QColor, QPen, QBrush
from graphics_items import LinkDrawer, Link, ItemImage
from widgets.toolbars import DraggableWidget


class CustomQGraphicsView(QGraphicsView):
    """Custom QGraphicsView class.

    Attributes:
        parent (QWidget): This is a QSplitter object
    """
    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._ui = parent.parent().parent()  # ToolboxUI (QMainWindow) instance
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.item_shadow = None
        self.make_link_drawer()
        self.max_sw_width = 0
        self.max_sw_height = 0
        self.scene().changed.connect(self.scene_changed)
        self.scene().selectionChanged.connect(self.selection_changed)
        self.active_subwindow = None
        self.from_widget = None
        self.to_widget = None
        self.show()

    @Slot("QList", name='scene_changed')
    def scene_changed(self, changed_qrects):
        """Make the scene larger as items get moved."""
        # logging.debug("scene changed. {0}".format(changed_qrects))
        qrect = self.sceneRect()
        for changed in changed_qrects:
            qrect |= changed
        self.setSceneRect(qrect)

    @Slot(name='selection_changed')
    def selection_changed(self):
        """Bring selected item to top."""
        # logging.debug("selection changed: {}.".format(self.scene().selectedItems()))
        for selected in self.scene().selectedItems():
            # Bring selected to top
            if not selected.zValue():
                continue
            for item in selected.collidingItems():
                if item != selected and item.zValue() == selected.zValue():
                    item.stackBefore(selected)

    def reset_scene(self):
        """Get a new, clean scene. Needed when clearing the UI for a new project
        so that new items are correctly placed."""
        self.scene().changed.disconnect(self.scene_changed)
        self.scene().selectionChanged.disconnect(self.selection_changed)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.scene().changed.connect(self.scene_changed)
        self.scene().selectionChanged.connect(self.selection_changed)
        self.setSceneRect(QRectF(0, 0, 0, 0))
        self.scene().addItem(self.link_drawer)

    def make_link_drawer(self):
        """Make new LinkDrawer and add it scene. Needed when opening a new project."""
        self.link_drawer = LinkDrawer(self._ui)
        self.scene().addItem(self.link_drawer)

    def set_project_item_model(self, model):
        """Set project item model."""
        self._project_item_model = model

    def set_connection_model(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        # self._connection_model.dataChanged.connect(self.connection_data_changed)
        self._connection_model.rowsAboutToBeRemoved.connect(self.connection_rows_removed)
        self._connection_model.columnsAboutToBeRemoved.connect(self.connection_columns_removed)

    def add_link(self, src_name, dst_name, index):
        """Draw link between source and sink items on scene and add Link instance to connection model."""
        # Find items from project model
        flags = Qt.MatchExactly | Qt.MatchRecursive
        src_item = self._project_item_model.find_item(src_name, flags).data(Qt.UserRole)
        dst_item = self._project_item_model.find_item(dst_name, flags).data(Qt.UserRole)
        logging.debug("Adding link {0} -> {1}".format(src_name, dst_name))
        link = Link(self._ui, src_item.get_icon(), dst_item.get_icon())
        self.scene().addItem(link)
        self._connection_model.setData(index, link)

    def remove_link(self, index):
        """Remove link between source and sink items
        on scene and remove Link instance from connection model."""
        link = self._connection_model.data(index, Qt.UserRole)
        if not link:
            logging.error("Link not found. This should not happen.")
            return False
        logging.debug("Removing link in ({0},{1})".format(index.row(), index.column()))
        self.scene().removeItem(link)
        self._connection_model.setData(index, None)

    def restore_links(self):
        """Iterate connection model and draw links to all that are 'True'
        Should be called only when a project is loaded from a save file."""
        rows = self._connection_model.rowCount()
        columns = self._connection_model.columnCount()
        for row in range(rows):
            for column in range(columns):
                index = self._connection_model.index(row, column)
                data = self._connection_model.data(index, Qt.DisplayRole)  # NOTE: data DisplayRole returns a string
                src_name = self._connection_model.headerData(row, Qt.Vertical, Qt.DisplayRole)
                dst_name = self._connection_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
                flags = Qt.MatchExactly | Qt.MatchRecursive
                src_item = self._project_item_model.find_item(src_name, flags).data(Qt.UserRole)
                dst_item = self._project_item_model.find_item(dst_name, flags).data(Qt.UserRole)
                if data == "True":
                    # logging.debug("Cell ({0},{1}):{2} -> Adding link".format(row, column, data))
                    link = Link(self._ui, src_item.get_icon(), dst_item.get_icon())
                    self.scene().addItem(link)
                    self._connection_model.setData(index, link)
                else:
                    # logging.debug("Cell ({0},{1}):{2} -> No link".format(row, column, data))
                    self._connection_model.setData(index, None)

    @Slot("QModelIndex", "int", "int", name='connection_rows_removed')
    def connection_rows_removed(self, index, first, last):
        """Update view when connection model changes."""
        for i in range(first, last+1):
            for j in range(self._connection_model.columnCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connection_columns_removed')
    def connection_columns_removed(self, index, first, last):
        """Update view when connection model changes."""
        for j in range(first, last+1):
            for i in range(self._connection_model.rowCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    def draw_links(self, src_rect, name):
        """Draw links when slot button is clicked.

        Args:
            src_rect (QRectF): Position on scene where to start drawing. Rect of connector button.
            name (str): Name of item where to start drawing
        """
        if not self.link_drawer.drawing:
            # start drawing and remember connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(src_rect)
            self.from_widget = name  # owner is Name of Item (e.g. DC1)
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.to_widget = name
            # create connection
            row = self._connection_model.header.index(self.from_widget)
            column = self._connection_model.header.index(self.to_widget)
            index = self._connection_model.createIndex(row, column)
            if self._connection_model.data(index, Qt.DisplayRole) == "False":
                self.add_link(self.from_widget, self.to_widget, index)
                self._ui.msg.emit("<b>{}</b>'s output is now connected to <b>{}</b>'s input."
                                  .format(self.from_widget, self.to_widget))
            elif self._connection_model.data(index, Qt.DisplayRole) == "True":
                self._ui.msg.emit("<b>{}</b>'s output is already connected to <b>{}</b>'s input."
                                  .format(self.from_widget, self.to_widget))

    def dragLeaveEvent(self, event):
        """Accept event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Only accept drops of DraggableWidget instances (from Add Item toolbar).
        Expand scene so as to fit the viewport. In this way, when the new item is created in the drop position
        the scene does not need to get bigger and recenter itself at that point (causing all items in the view
        to abruptly shift)."""
        source = event.source()
        if not isinstance(source, DraggableWidget):
            event.ignore()
        else:
            event.accept()
            top_left = self.mapToScene(self.viewport().frameGeometry().topLeft())
            bottom_right = self.mapToScene(self.viewport().frameGeometry().bottomRight())
            qrect = QRectF(top_left, bottom_right)
            qrect |= self.sceneRect()
            self.setSceneRect(qrect)

    def dragMoveEvent(self, event):
        """Only accept drops of DraggableWidget instances (from Add Item toolbar)"""
        source = event.source()
        if not isinstance(source, DraggableWidget):
            event.ignore()
        else:
            event.accept()

    def dropEvent(self, event):
        """Capture text from event's mimedata and show the appropriate 'Add Item form'"""
        text = event.mimeData().text()
        pos = self.mapToScene(event.pos())
        pen = QPen(QColor('white'))
        x = pos.x() - 35
        y = pos.y() - 35
        w = 70
        h = 70
        # self.item_shadow = self.scene().addEllipse(0, 0, 70, 70)
        if text == "Data Store":
            brush = QBrush(QColor(0, 255, 255, 128))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._ui.show_add_data_store_form(pos.x(), pos.y())
        elif text == "Data Connection":
            brush = QBrush(QColor(0, 0, 255, 128))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._ui.show_add_data_connection_form(pos.x(), pos.y())
        elif text == "Tool":
            brush = QBrush(QColor(255, 0, 0, 128))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._ui.show_add_tool_form(pos.x(), pos.y())
        elif text == "View":
            brush = QBrush(QColor(0, 255, 0, 128))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._ui.show_add_view_form(pos.x(), pos.y())
        self.scene().addItem(self.item_shadow)

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.src:
            self.link_drawer.dst = self.mapToScene(e.pos())
            self.link_drawer.update_geometry()
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        """If link lands on slot button, trigger click.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.drawing:
            self.link_drawer.hide()
            if e.button() != Qt.LeftButton:
                self.link_drawer.drawing = False
            else:
                connectors = [item for item in self.items(e.pos()) if hasattr(item, 'is_connector')]
                if not connectors:
                    self.link_drawer.drawing = False
                    self._ui.msg_warning.emit("Unable to make connection. "
                                              "Try landing the connection onto a connector button.")
        super().mousePressEvent(e)
