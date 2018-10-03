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

:author: P. Savolainen (VTT)
:date:   6.2.2018
"""

import logging
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene
from PySide2.QtCore import Signal, Slot, Qt, QRectF
from PySide2.QtGui import QColor, QPen, QBrush
from graphics_items import LinkDrawer, Link, ItemImage
from widgets.toolbars import DraggableWidget


class CustomQGraphicsView(QGraphicsView):
    """Custom QGraphicsView class.

    Attributes:
        parent (QWidget): Application central widget (self.centralwidget)
    """
    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent=parent)  # Parent is passed to QWidget's constructor
        self._scene = None
        self._toolbox = None
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.max_sw_width = 0
        self.max_sw_height = 0
        self.active_subwindow = None
        self.src_widget = None  # source widget when drawing links
        self.dst_widget = None  # destination widget when drawing links
        self.show()

    def set_ui(self, toolbox):
        """Set the main ToolboxUI instance."""
        self._toolbox = toolbox
        self._scene = CustomQGraphicsScene(self, toolbox)
        self.setScene(self._scene)
        self.make_link_drawer()
        self.init_scene()

    @Slot("QList", name='scene_changed')
    def scene_changed(self, changed_qrects):
        """Resize scene as it changes."""
        # logging.debug("scene changed. {0}".format(changed_qrects))
        self.resize_scene()

    def make_new_scene(self):
        """Make a new, clean scene. Needed when clearing the UI for a new project
        so that new items are correctly placed."""
        self._scene.changed.disconnect(self.scene_changed)
        self._scene = CustomQGraphicsScene(self, self._toolbox)
        self.setScene(self._scene)
        self._scene.addItem(self.link_drawer)

    def init_scene(self):
        """Resize the scene and connect its `changed` signal. Needed after
        loading a new project.
        """
        self._scene.changed.connect(self.scene_changed)
        self.resize_scene(recenter=True)
        # TODO: try to make a nice scene background, or remove if nothing seems good
        # pixmap = QPixmap(":/symbols/Spine_symbol.png").scaled(64, 64)
        # painter = QPainter(pixmap)
        # alpha = QPixmap(pixmap.size())
        # alpha.fill(QColor(255, 255, 255, 255-24))
        # painter.drawPixmap(0, 0, alpha)
        # painter.end()
        # self.setBackgroundBrush(QBrush(pixmap))

    def resize_scene(self, recenter=False):
        """Make the scene at least as big as the viewport."""
        view_rect = self.mapToScene(self.rect()).boundingRect()
        items_rect = self._scene.itemsBoundingRect()
        if recenter:
            view_rect.moveCenter(items_rect.center())
            self.centerOn(items_rect.center())
        self._scene.setSceneRect(view_rect | items_rect)

    def make_link_drawer(self):
        """Make new LinkDrawer and add it scene. Needed when opening a new project."""
        self.link_drawer = LinkDrawer(self._toolbox)
        self.scene().addItem(self.link_drawer)

    def set_project_item_model(self, model):
        """Set project item model."""
        self._project_item_model = model

    def set_connection_model(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        self._connection_model.rowsAboutToBeRemoved.connect(self.connection_rows_removed)
        self._connection_model.columnsAboutToBeRemoved.connect(self.connection_columns_removed)

    def add_link(self, src_name, dst_name, index):
        """Draws link between source and sink items on scene and
        appends connection model. Refreshes View references if needed."""
        flags = Qt.MatchExactly | Qt.MatchRecursive
        src_item = self._project_item_model.find_item(src_name, flags).data(Qt.UserRole)
        dst_item = self._project_item_model.find_item(dst_name, flags).data(Qt.UserRole)
        link = Link(self._toolbox, src_item.get_icon(), dst_item.get_icon())
        self.scene().addItem(link)
        self._connection_model.setData(index, link)
        # Refresh View references
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()

    def remove_link(self, index):
        """Removes link between source and sink items on scene and
        updates connection model. Refreshes View references if needed."""
        link = self._connection_model.data(index, Qt.UserRole)
        if not link:
            logging.error("Link not found. This should not happen.")
            return False
        # Find destination item
        dst_name = link.dst_icon.name()
        flags = Qt.MatchExactly | Qt.MatchRecursive
        dst_item = self._project_item_model.find_item(dst_name, flags).data(Qt.UserRole)
        self.scene().removeItem(link)
        self._connection_model.setData(index, None)
        # Refresh View references
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()

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
                    link = Link(self._toolbox, src_item.get_icon(), dst_item.get_icon())
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
            self.src_widget = name
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.dst_widget = name
            # create connection
            row = self._connection_model.header.index(self.src_widget)
            column = self._connection_model.header.index(self.dst_widget)
            index = self._connection_model.createIndex(row, column)
            if self._connection_model.data(index, Qt.DisplayRole) == "False":
                self.add_link(self.src_widget, self.dst_widget, index)
                self._toolbox.msg.emit("<b>{}</b>'s output is now connected to <b>{}</b>'s input."
                                       .format(self.src_widget, self.dst_widget))
            elif self._connection_model.data(index, Qt.DisplayRole) == "True":
                self._toolbox.msg.emit("<b>{}</b>'s output is already connected to <b>{}</b>'s input."
                                       .format(self.src_widget, self.dst_widget))
            self.emit_connection_information_message()

    def emit_connection_information_message(self):
        """Inform user about what connections are implemented and how they work."""
        if self.src_widget == self.dst_widget:
            self._toolbox.msg_warning.emit("\t<b>Not implemented</b>. The functionality for feedback "
                                           "links is not implemented yet.")
        else:
            src_item = self._project_item_model.find_item(self.src_widget, Qt.MatchExactly | Qt.MatchRecursive)
            if not src_item:
                logging.error("Item {0} not found".format(self.dst_widget))
                return
            src_item_type = src_item.data(Qt.UserRole).item_type
            dst_item = self._project_item_model.find_item(self.dst_widget, Qt.MatchExactly | Qt.MatchRecursive)
            if not dst_item:
                logging.error("Item {0} not found".format(self.dst_widget))
                return
            dst_item_type = dst_item.data(Qt.UserRole).item_type
            if src_item_type == 'Data Connection' and dst_item_type == 'Tool':
                self._toolbox.msg.emit("\t-> Input files for <b>{0}</b>'s execution will be looked "
                                       "up in <b>{1}</b>'s references and data directory."
                                       .format(self.dst_widget, self.src_widget))
            elif src_item_type == 'Data Store' and dst_item_type == 'Tool':
                self._toolbox.msg.emit("\t-> Input files for <b>{0}</b>'s execution will be looked "
                                       "up in <b>{1}</b>'s data directory."
                                       .format(self.dst_widget, self.src_widget))
            elif src_item_type == 'Tool' and dst_item_type in ['Data Connection', 'Data Store']:
                self._toolbox.msg.emit("\t-> Output files from <b>{0}</b>'s execution will be passed "
                                       "as reference to <b>{1}</b>'s data directory."
                                       .format(self.src_widget, self.dst_widget))
            elif src_item_type in ['Data Connection', 'Data Store']\
                    and dst_item_type in ['Data Connection', 'Data Store']:
                self._toolbox.msg.emit("\t-> Input files for a tool's execution will be looked up "
                                       "in <b>{0}</b> if not found in <b>{1}</b>."
                                       .format(self.src_widget, self.dst_widget))
            elif src_item_type == 'Data Store' and dst_item_type == 'View':
                self._toolbox.msg_warning.emit("\t-> Database references in <b>{0}</b> will be viewed "
                                               "by <b>{1}</b>."
                                               .format(self.src_widget, self.dst_widget))
            elif src_item_type == 'Tool' and dst_item_type == 'Tool':
                self._toolbox.msg_warning.emit("\t<b>Not implemented</b>. Interaction between Tool "
                                               "items is not implemented yet.")
            else:
                self._toolbox.msg_warning.emit("\t<b>Not implemented</b>. Whatever you are trying to do "
                                               "is not implemented yet :)")

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.drawing:
            self.link_drawer.dst = self.mapToScene(e.pos())
            self.link_drawer.update_geometry()
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        """Manage drawing of links. Handle the case where a link is being
        drawn and the user doesn't hit a connector button.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        was_drawing = self.link_drawer.drawing if self.link_drawer else None
        # This below will trigger connector button if any
        super().mousePressEvent(e)
        if was_drawing:
            self.link_drawer.hide()
            # If `drawing` is still `True` here, it means we didn't hit a connector
            if self.link_drawer.drawing:
                self.link_drawer.drawing = False
                if e.button() != Qt.LeftButton:
                    return
                self._toolbox.msg_warning.emit("Unable to make connection. "
                                          "Try landing the connection onto a connector button.")

    def showEvent(self, event):
        """Make the scene at least as big as the viewport."""
        super().showEvent(event)
        self.resize_scene(recenter=True)

    def resizeEvent(self, event):
        """Make the scene at least as big as the viewport."""
        super().resizeEvent(event)
        self.resize_scene(recenter=True)


class CustomQGraphicsScene(QGraphicsScene):
    """A scene that handles drag and drop events."""
    files_dropped_on_dc = Signal("QGraphicsItem", "QVariant", name="files_dropped_on_dc")

    def __init__(self, parent, toolbox):
        """Initialize class."""
        super().__init__(parent)
        self._toolbox = toolbox
        self.item_shadow = None

    def dragLeaveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a DraggableWidget (from Add Item toolbar)."""
        event.accept()
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dragLeaveEvent(event)

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
        pen = QPen(QColor('white'))
        x = pos.x() - 35
        y = pos.y() - 35
        w = 70
        h = 70
        if text == "Data Store":
            brush = QBrush(QColor(0, 255, 255, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._toolbox.show_add_data_store_form(pos.x(), pos.y())
        elif text == "Data Connection":
            brush = QBrush(QColor(0, 0, 255, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._toolbox.show_add_data_connection_form(pos.x(), pos.y())
        elif text == "Tool":
            brush = QBrush(QColor(255, 0, 0, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._toolbox.show_add_tool_form(pos.x(), pos.y())
        elif text == "View":
            brush = QBrush(QColor(0, 255, 0, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._toolbox.show_add_view_form(pos.x(), pos.y())
        self.addItem(self.item_shadow)
