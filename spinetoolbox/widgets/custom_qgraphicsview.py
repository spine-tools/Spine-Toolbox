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
        self._qmainwindow = parent.parent().parent()
        self._parent = self._qmainwindow
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.make_link_drawer()
        self.max_sw_width = 0
        self.max_sw_height = 0
        # self.scene().changed.connect(self.scene_changed)
        self.active_subwindow = None
        self.from_widget = None
        self.to_widget = None
        self.show()

    @Slot(name='scene_changed')
    def scene_changed(self, changed_qrects):
        """Not in use at the moment."""
        logging.debug("scene changed. {0}".format(changed_qrects))

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

    def find_link(self, src_icon, dst_icon):
        """Find link in scene, by model index"""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if item.src_icon == src_icon and item.dst_icon == dst_icon:
                    return item
        return None

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
