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
from PySide2.QtCore import Slot, Qt, QTimer, QPointF, QRectF, QMarginsF
from PySide2.QtGui import QColor, QPen, QBrush
from graphics_items import LinkDrawer, Link
from config import ITEM_TYPE
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
        self._qmainwindow = parent.parent().parent()
        self._parent = self._qmainwindow
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.item_shadow = None
        self.make_link_drawer()
        self.max_sw_width = 0
        self.max_sw_height = 0
        self.scene().changed.connect(self.scene_changed)
        self.active_subwindow = None
        self.from_widget = None
        self.to_widget = None
        self.show()

    @Slot(name='scene_changed')
    def scene_changed(self, changed_qrects):
        """Make the scene larger as items get moved."""
        # logging.debug("scene changed. {0}".format(changed_qrects))
        qrect = self.sceneRect()
        for changed in changed_qrects:
            qrect |= changed
        self.setSceneRect(qrect)

    def reset_scene(self):
        """Get a new, clean scene. Needed when clearing the UI for a new project
        so that new items are correctly placed."""
        self.scene().changed.disconnect(self.scene_changed)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.scene().changed.connect(self.scene_changed)
        self.setSceneRect(QRectF(0, 0, 0, 0))

    def make_link_drawer(self):
        """Make new LinkDrawer and add it scene. Needed when opening a new project."""
        self.link_drawer = LinkDrawer(self._qmainwindow)
        self.scene().addItem(self.link_drawer)

    def setProjectItemModel(self, model):
        """Set project item model and connect signals."""
        self._project_item_model = model

    def setConnectionModel(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        self._connection_model.dataChanged.connect(self.connectionDataChanged)
        self._connection_model.rowsAboutToBeRemoved.connect(self.connectionRowsRemoved)
        self._connection_model.columnsAboutToBeRemoved.connect(self.connectionColumnsRemoved)

    def project_item_model(self):
        """Return project item model."""
        return self._project_item_model

    def connection_model(self):
        """Return connection model."""
        return self._connection_model

    # def subWindowList(self):
    #     """Return list of subwindows (replicate QMdiArea.subWindowList)."""
    #     # TODO: This returns an empty list now since no items have that type
    #     # TODO: But I believe it isn't needed at all -Manuel
    #     return [x for x in self.scene().items() if x.data(ITEM_TYPE) == 'subwindow']

    @Slot("QModelIndex", "QModelIndex", name='connectionDataChanged')
    def connectionDataChanged(self, top_left, bottom_right, roles=None):
        """Add or remove Link on scene between items when connection model changes."""
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom+1):
            for column in range(left, right+1):
                index = self.connection_model().index(row, column)
                data = self.connection_model().data(index, Qt.DisplayRole)
                from_name = self.connection_model().headerData(row, Qt.Vertical, Qt.DisplayRole)
                to_name = self.connection_model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
                from_item = self._parent.find_item(from_name, Qt.MatchExactly | Qt.MatchRecursive).data(Qt.UserRole)
                to_item = self._parent.find_item(to_name, Qt.MatchExactly | Qt.MatchRecursive).data(Qt.UserRole)
                if data:  # connection made, add link widget
                    link = Link(self._qmainwindow, from_item.get_icon(), to_item.get_icon())
                    self.scene().addItem(link)
                    self.connection_model().save_link(row, column, link)
                    # append link to ItemImage instances
                    from_item.get_icon().links.append(link)
                    to_item.get_icon().links.append(link)
                else:   # connection destroyed, remove link widget
                    link = self.connection_model().link(row, column)
                    if link:
                        self.scene().removeItem(link)
                        # remove link from ItemImage instances
                        try:
                            from_item.get_icon().links.remove(link)
                            to_item.get_icon().links.remove(link)
                        except ValueError:
                            pass


    @Slot("QModelIndex", "int", "int", name='connectionRowsRemoved')
    def connectionRowsRemoved(self, index, first, last):
        """Update view when connection model changes."""
        # logging.debug("conn. rows removed")
        for i in range(first, last+1):
            for j in range(self.connection_model().columnCount()):
                link = self.connection_model().link(i, j)
                if link:
                    self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connectionColumnsRemoved')
    def connectionColumnsRemoved(self, index, first, last):
        """Update view when connection model changes."""
        # logging.debug("conn. columns removed")
        for j in range(first, last+1):
            for i in range(self.connection_model().rowCount()):
                link = self.connection_model().link(i, j)
                if link:
                    self.scene().removeItem(link)

    def draw_links(self, src_point, name):
        """Draw links when slot button is clicked.

        Args:
            src_point (QPointF): Position on scene where to start drawing. Center point of connector button.
            name (str): Name of item where to start drawing
        """
        if not self.link_drawer.drawing:
            # start drawing and remember connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(src_point)
            self.from_widget = name  # owner is Name of Item (e.g. DC1)
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.to_widget = name
            # create connection
            row = self.connection_model().header.index(self.from_widget)
            column = self.connection_model().header.index(self.to_widget)
            index = self.connection_model().createIndex(row, column)
            if not self.connection_model().data(index, Qt.DisplayRole):
                self.connection_model().setData(index, "value", Qt.EditRole)  # value not used
                self._parent.msg.emit("<b>{}</b>'s output is now connected to"
                                      " <b>{}</b>'s input.".format(self.from_widget, self.to_widget))
            else:
                self._parent.msg.emit("<b>{}</b>'s output is already connected to"
                                      " <b>{}</b>'s input.".format(self.from_widget, self.to_widget))

    def dragLeaveEvent(self, event):
        """Accept event"""
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
        self.item_shadow = self.scene().addEllipse(0, 0, 70, 70)
        self.item_shadow.setPos(pos.x() - 35, pos.y() - 35)
        if text == "Data Store":
            self.item_shadow.setBrush(QBrush(QColor(0, 255, 255, 128)))
            self._qmainwindow.show_add_data_store_form(pos.x(), pos.y())
        elif text == "Data Connection":
            self.item_shadow.setBrush(QBrush(QColor(0, 0, 255, 128)))
            self._qmainwindow.show_add_data_connection_form(pos.x(), pos.y())
        elif text == "Tool":
            self.item_shadow.setBrush(QBrush(QColor(255, 0, 0, 128)))
            self._qmainwindow.show_add_tool_form(pos.x(), pos.y())
        elif text == "View":
            self.item_shadow.setBrush(QBrush(QColor(0, 255, 0, 128)))
            self._qmainwindow.show_add_view_form(pos.x(), pos.y())
