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
from PySide2.QtCore import Signal, Slot, QPoint, Qt, QTimer
from views import LinkDrawer, Link
from config import ITEM_TYPE, FPS


class CustomQGraphicsView(QGraphicsView):
    """Custom QGraphicsView class.

    Attributes:
        parent (QWidget): This is a QSplitter object
    """

    subWindowActivated = Signal("QGraphicsProxyWidget", name="subWindowActivated")

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
        #     self.link_drawer = LinkDrawer(parent)  # TODO: Pekka
        self.link_drawer = LinkDrawer(self._scene, self._qmainwindow)
        self.scene().addItem(self.link_drawer)
        # self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.max_sw_width = 0
        self.max_sw_height = 0
        self.scene().changed.connect(self.scene_changed)
        self.active_subwindow = None
        self.from_widget = None
        self.to_widget = None
        self.show()

    @Slot(name="update_viewport")
    def update_viewport(self):
        #logging.debug("timeout")
        self.viewport().update()

    @Slot(name='scene_changed')
    def scene_changed(self):
        """Check if active subwindow has changed and emit signal accordingly."""
        #logging.debug("scene changed")
        current_active_sw = self.scene().activeWindow()
        if current_active_sw and current_active_sw.data(ITEM_TYPE) == "subwindow":
            if current_active_sw != self.active_subwindow:
                self.active_subwindow = current_active_sw
                self.subWindowActivated.emit(self.active_subwindow)

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
        return [x for x in self.scene().items() if x.data(ITEM_TYPE) == 'subwindow']

    def setActiveSubWindow(self, item):
        """Replicate QMdiArea.setActiveWindow."""
        self.scene().setActiveWindow(item)

    def activeSubWindow(self):
        """Replicate QMdiArea.activeSubWindow."""
        act_w = self.scene().activeWindow()
        if not act_w:
            return None
        # logging.debug("activeWindow type is now:{0}".format(act_w.type))
        return self.scene().activeWindow()

    def removeSubWindow(self, sw):  # this method will be obsolete, since it doesn't coordinate with the model
        """Remove subwindow and any attached links from the scene."""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if sw.widget() == item.from_item or sw.widget() == item.to_item:
                    self.scene().removeItem(item)
        self.scene().removeItem(sw)

    def find_link(self, from_widget, to_widget):
        """Find link in scene, by model index"""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if item.from_widget == from_widget and item.to_widget == to_widget:
                    return item
        return None

    @Slot("QModelIndex", "int", "int", name='projectRowsInserted')
    def projectRowsInserted(self, item, first, last):
        """Update view when an item is inserted to project."""
        for ind in range(first, last+1):
            data = item.child(ind, 0).data(role=Qt.UserRole)
            widget = data.get_widget()
            logging.debug("Inserting {0}. first:{1} last:{2}".format(data.name, first, last))
            flags = Qt.Window
            proxy = self.scene().addWidget(widget, flags)
            proxy.setData(ITEM_TYPE, "subwindow")
            #figure out the best position on the view
            sw_geom = proxy.windowFrameGeometry()
            self.max_sw_width = max(self.max_sw_width, sw_geom.width())
            self.max_sw_height = max(self.max_sw_height, sw_geom.height())
            position = QPoint(item.row() * self.max_sw_width, ind * self.max_sw_height)
            proxy.setPos(position)
            # proxy.setFlag(QGraphicsItem.ItemIsSelectable, True)
            proxy.widget().activateWindow()

    @Slot("QModelIndex", "int", "int", name='projectRowsRemoved')
    def projectRowsRemoved(self, item, first, last):
        """Update view when an item is removed from project."""
        # logging.debug("project rows removed")
        for ind in range(first, last+1):
            sw = item.child(ind, 0).data(role=Qt.UserRole).get_widget().parent()
            self.scene().removeItem(sw)

    @Slot("QModelIndex", "QModelIndex", name='connectionDataChanged')
    def connectionDataChanged(self, top_left, bottom_right, roles=None):
        """update view when model changes"""
        # logging.debug("conn data changed")
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
                sub_windows = self.subWindowList()
                sw_owners = list(sw.widget().owner() for sw in sub_windows)
                fr = sw_owners.index(from_name)
                to = sw_owners.index(to_name)
                from_widget = sub_windows[fr].widget()
                to_widget = sub_windows[to].widget()
                if data:  # connection made, add link widget
                    link = Link(self._parent, from_widget, to_widget)
                    self.scene().addItem(link) #TODO: try QPersistentModelIndex to keep track of Links
                else:   # connection destroyed, remove link widget
                    link = self.find_link(from_widget, to_widget)
                    if link is not None:
                        self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connectionsRemoved')
    def connectionsRemoved(self, index, first, last):
        """update view when connection model changes"""
        # logging.debug("conns. removed")
        for i in range(first,last+1):
            removed_name = self.connection_model().headerData(i, orientation=Qt.Horizontal)
            for item in self.scene().items():
                if item.data(ITEM_TYPE) == "link":
                    from_name = item.from_widget.owner()
                    to_name = item.to_widget.owner()
                    if removed_name == from_name or removed_name == to_name:
                        self.scene().removeItem(item)


    def draw_links(self, button):
        """Draw links when slot button is clicked"""
        if not self.link_drawer.drawing:
            # start drawing and remember connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(button)
            self.from_widget = button.parent().owner()
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.to_widget = button.parent().owner()
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
