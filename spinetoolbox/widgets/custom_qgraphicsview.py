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
from PySide2.QtCore import Slot, Qt, QTimer
from graphics_items import LinkDrawer, Link
from config import ITEM_TYPE, FPS


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
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_viewport)
        self.timer.start(1000/FPS)   # Adjust frames per second
        self._qmainwindow = parent.parent().parent()
        self._parent = self._qmainwindow
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.make_link_drawer(self._scene, self._qmainwindow)
        # self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.max_sw_width = 0
        self.max_sw_height = 0
        # self.scene().changed.connect(self.scene_changed)  # TODO: Check if this is needed
        self.active_subwindow = None
        self.from_widget = None
        self.to_widget = None
        self.show()

    @Slot(name="update_viewport")
    def update_viewport(self):
        # logging.debug("timeout")
        self.viewport().update()

    @Slot(name='scene_changed')
    def scene_changed(self):
        """Check if active subwindow has changed and emit signal accordingly."""
        # logging.debug("scene changed")
        current_active_sw = self.scene().activeWindow()
        if current_active_sw and current_active_sw.data(ITEM_TYPE) == "subwindow":
            if current_active_sw != self.active_subwindow:
                self.active_subwindow = current_active_sw
                self.subWindowActivated.emit(self.active_subwindow)

    def make_link_drawer(self, scene, qmainwindow):
        """Make new LinkDrawer and add it scene. Needed when opening a new project."""
        self.link_drawer = LinkDrawer(scene, qmainwindow)
        self.scene().addItem(self.link_drawer)

    def setProjectItemModel(self, model):
        """Set project item model and connect signals."""
        self._project_item_model = model
        self._project_item_model.rowsInserted.connect(self.projectRowsInserted)
        self._project_item_model.rowsAboutToBeRemoved.connect(self.projectRowsRemoved)

    def setConnectionModel(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        self._connection_model.dataChanged.connect(self.connectionDataChanged)
        # note: since rows and columns are always removed together in our model,
        # only one of these two lines below is strictly needed
        self._connection_model.rowsRemoved.connect(self.connectionsRemoved)
        # self._connection_model.columnsRemoved.connect(self.connectionsRemoved)

    def project_item_model(self):
        """Return project item model."""
        return self._project_item_model

    def connection_model(self):
        """Return connection model."""
        return self._connection_model

    def subWindowList(self):
        """Return list of subwindows (replicate QMdiArea.subWindowList)."""
        # TODO: Check if needed
        return [x for x in self.scene().items() if x.data(ITEM_TYPE) == 'subwindow']

    def setActiveSubWindow(self, item):
        """Replicate QMdiArea.setActiveWindow."""
        # TODO: Check if needed
        self.scene().setActiveWindow(item)

    def activeSubWindow(self):
        """Replicate QMdiArea.activeSubWindow."""
        # TODO: Check if needed
        act_w = self.scene().activeWindow()
        if not act_w:
            return None
        # logging.debug("activeWindow type is now:{0}".format(act_w.type))
        return self.scene().activeWindow()

    def removeSubWindow(self, sw):
        """OBSOLETE! Remove subwindow and any attached links from the scene."""
        # TODO: Check if needed
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if sw.widget() == item.from_item or sw.widget() == item.to_item:
                    self.scene().removeItem(item)
        self.scene().removeItem(sw)

    def find_link(self, src_icon, dst_icon):
        """Find link in scene, by model index"""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if item.src_icon == src_icon and item.dst_icon == dst_icon:
                    return item
        return None

    @Slot("QModelIndex", "int", "int", name='projectRowsInserted')
    def projectRowsInserted(self, item, first, last):
        """Update view when an item is inserted to project."""
        # TODO: Check if needed
        # TODO: This does not really do anything. To be removed.
        if not first-last == 0:
            logging.error("Adding more than one item at a time is not allowed. first:{0} last:{1}".format(first, last))
            return
        data = item.child(first, 0).data(role=Qt.UserRole)
        widget = data.get_widget()

    @Slot("QModelIndex", "int", "int", name='projectRowsRemoved')
    def projectRowsRemoved(self, item, first, last):
        """Update view when an item is removed from project."""
        # TODO: Check if needed
        # logging.debug("project rows removed")
        for ind in range(first, last+1):
            sw = item.child(ind, 0).data(role=Qt.UserRole).get_widget().parent()
            self.scene().removeItem(sw)

    @Slot("QModelIndex", "QModelIndex", name='connectionDataChanged')
    def connectionDataChanged(self, top_left, bottom_right, roles=None):
        """update view when model changes."""
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
                    link = Link(self._parent, from_item.get_icon(), to_item.get_icon())
                    self.scene().addItem(link)  # TODO: try QPersistentModelIndex to keep track of Links
                    # TODO: Probably a better idea would be to store Link instances into
                    # TODO: ConnectionModel (QAbstractTableModel)
                else:   # connection destroyed, remove link widget
                    link = self.find_link(from_item.get_icon(), to_item.get_icon())
                    if link is not None:
                        self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connectionsRemoved')
    def connectionsRemoved(self, index, first, last):
        """Update view when connection model changes."""
        # logging.debug("conns. removed")
        for i in range(first, last+1):
            removed_name = self.connection_model().headerData(i, orientation=Qt.Horizontal)
            for item in self.scene().items():
                if item.data(ITEM_TYPE) == "link":
                    src_name = item.src_icon.name()
                    dst_name = item.dst_icon.name()
                    if removed_name == src_name or removed_name == dst_name:
                        self.scene().removeItem(item)

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
