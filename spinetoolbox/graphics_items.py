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
Classes for drawing graphics items on QGraphicsScene.

:authors: Manuel Marin <manuelma@kth.se>, Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   4.4.2018
"""

import logging
from PySide2.QtCore import Qt, QPoint, QPointF, QLineF, QRectF, QTimeLine, QEvent
from PySide2.QtWidgets import QGraphicsItem, QGraphicsLineItem, \
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsRectItem, \
    QGraphicsItemAnimation, QGraphicsPixmapItem
from PySide2.QtGui import QColor, QPen, QPolygonF, QBrush, QPixmap
from math import atan2, sin, cos, pi  # arrow head
from config import ITEM_TYPE


class SceneBackground(QGraphicsRectItem):
    """Experimental. This should be used to paint the scene background white."""
    def __init__(self, main):
        super().__init__(main.ui.graphicsView.scene().sceneRect())
        self._main = main
        self.bg_pen = QPen(QColor('blue'))  # QPen is used to draw the item outline
        self.bg_brush = QBrush(QColor(0, 0, 0, 128))  # QBrush is used to fill the item
        self.setPen(self.bg_pen)
        self.setBrush(self.bg_brush)
        self.setZValue(-1)
        self._main.ui.graphicsView.scene().addItem(self)

    # @Slot("QRectF", name="update_scene_bg")
    # def update_scene_bg(self, rect):
    #     self.setRect(rect)

    def update_bg(self):
        """Work in progress."""
        self.setRect(self._main.ui.graphicsView.scene().sceneRect())


class ItemImage(QGraphicsItem):
    """Base class for all Item icons drawn on QGraphicsScene.

    Attributes:
        main (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, main, x, y, w, h, name):
        """Class constructor."""
        super().__init__()
        self._main = main
        self.x_coord = x  # x coordinate in the scene
        self.y_coord = y  # y coordinate in the scene
        self.w = w
        self.h = h
        self.connector_pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.connector_pen.setStyle(Qt.DotLine)
        self.connector_brush = QBrush(QColor(255, 255, 255, 0))  # QBrush is used to fill the item
        self.connector_hover_brush = QBrush(QColor(50, 0, 50, 128))  # QBrush is used to fill the item
        self._name = name
        self.font_size = 8  # point size
        self.q_rect = QRectF(self.x_coord, self.y_coord, self.w, self.h)  # Position and size of the drawn item
        # Make QGraphicsSimpleTextItem for item name.
        self.name_item = QGraphicsSimpleTextItem(self._name)
        # Set font size and style
        font = self.name_item.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.name_item.setFont(font)
        self.name_item.setPos(self.x_coord, self.y_coord)  # TODO: Refine position
        self.connector_button = QGraphicsRectItem()
        self.connector_button.setPen(self.connector_pen)
        self.connector_button.setBrush(self.connector_brush)
        self.connector_button.setRect(QRectF(self.x_coord+25, self.y_coord+25, 20, 20))  # TODO: Refine position
        self.connector_button.setAcceptHoverEvents(True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.connector_button.is_connector = True

    def make_master(self, pen, brush):
        """Make a parent of all other QGraphicsItems that
        make up the icon drawn on the scene.
        NOTE: setting the parent item moves the items as one!!
        """
        icon = QGraphicsEllipseItem(self.q_rect)
        icon.setPen(pen)
        icon.setBrush(brush)
        icon.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        # icon.setAcceptHoverEvents(True)
        return icon

    def links(self):
        """Returns a list of Link items that are connected to this item."""
        link_list = list()
        for item in self._main.ui.graphicsView.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if item.src_icon == self or item.dst_icon == self:
                    # logging.debug("Found link for item: {0}".format(self.name()))
                    link_list.append(item)
        return link_list

    def name(self):
        """Returns name of the item that is represented by this icon."""
        return self._name

    def conn_button(self):
        """Returns items connector button (QWidget)."""
        return self.connector_button

    def master(self):
        """Return the parent QGraphicsItem of this Item."""
        return self._master

    def hover_enter_event(self, event):
        """Set a darker shade to icon when mouse enters icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        # NOTE: This is disabled. setAcceptHoverEvents(True) to master to enable this.
        self._master.setBrush(self.hover_brush)
        event.accept()

    def hover_leave_event(self, event):
        """Restore original brush when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        # NOTE: This is disabled. setAcceptHoverEvents(True) to master to enable this.
        self._master.setBrush(self.brush)
        event.accept()

    def mouse_press_event(self, event):
        """Update UI to show details of this item. Prevents dragging
        multiple items with a mouse (also with the Ctrl-button pressed).

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self._main.ui.graphicsView.scene().clearSelection()
        self.show_item_info()

    def mouse_move_event(self, event):
        """Move icon while the mouse button is pressed.
        Update links that are connected to this icon.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        link_list = self.links()
        for link in link_list:
            link.update_line()
        QGraphicsItem.mouseMoveEvent(self._master, event)

    def mouse_release_event(self, event):
        """Mouse button is released.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        QGraphicsItem.mouseReleaseEvent(self._master, event)

    def connector_mouse_press_event(self, event):
        """Catch connector button click. Starts drawing a link."""
        if not event.button() == Qt.LeftButton:
            event.accept()
        else:
            self.show_item_info()
            self.start_drawing()

    def connector_hover_enter_event(self, event):
        """Set a darker shade to connector button when mouse enters icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        # TODO: Try setting QGraphicsEffect(QGraphicsItem.shadow) or something
        self.connector_button.setBrush(self.connector_hover_brush)

    def connector_hover_leave_event(self, event):
        """Restore original brush when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        # TODO: Try setting QGraphicsEffect(QGraphicsItem.not_shadow) or something
        self.connector_button.setBrush(self.connector_brush)

    def context_menu_event(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        self._main.show_item_image_context_menu(event.screenPos(), self.name())

    def show_item_info(self):
        """Update GUI to show the details of the selected item in a QDockWidget."""
        self._main.show_info(self.name())

    def start_drawing(self):
        """Start drawing a link from the center point of the connector button."""
        center_point = self.conn_button().sceneBoundingRect().center()
        self._main.ui.graphicsView.draw_links(center_point, self.name())


class DataConnectionImage(ItemImage):
    """Data Connection item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        main (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, main, x, y, w, h, name):
        """Class constructor."""
        super().__init__(main, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 0, 255, 128))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 0, 204, 128))  # QBrush while hovering
        # Draw ellipse
        self._master = self.make_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._main.ui.graphicsView.scene().addItem(self._master)
        self._main.ui.graphicsView.scene().addItem(self.name_item)
        # Group the drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self._master)
        self.connector_button.setParentItem(self._master)

    def make_master(self, pen, brush):
        """Calls super class method."""
        return super().make_master(pen, brush)

    def mouse_press_event(self, event):
        """Calls super class method."""
        super().mouse_press_event(event)

    def mouse_release_event(self, event):
        """Calls super class method."""
        super().mouse_release_event(event)

    def mouse_move_event(self, event):
        """Calls super class method."""
        super().mouse_move_event(event)

    def hover_enter_event(self, event):
        """Calls super class method."""
        super().hover_enter_event(event)

    def hover_leave_event(self, event):
        """Calls super class method."""
        super().hover_leave_event(event)

    def connector_mouse_press_event(self, event):
        """Calls super class method."""
        super().connector_mouse_press_event(event)

    def connector_hover_enter_event(self, event):
        """Calls super class method."""
        super().connector_hover_enter_event(event)

    def connector_hover_leave_event(self, event):
        """Calls super class method."""
        super().connector_hover_leave_event(event)

    def context_menu_event(self, event):
        """Calls super class method."""
        return super().context_menu_event(event)


class ToolImage(ItemImage):
    """Tool item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        main (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, main, x, y, w, h, name):
        """Class constructor."""
        super().__init__(main, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(255, 0, 0, 128))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(204, 0, 0, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._main.ui.graphicsView.scene().addItem(self._master)
        self._main.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self._master)
        self.connector_button.setParentItem(self._master)
        # animation stuff
        self.wheel = QGraphicsPixmapItem()
        pixmap = QPixmap(":/icons/wheel.png").scaled(0.5*self.w, 0.5*self.h)
        self.wheel.setPixmap(pixmap)
        self.wheel_w = pixmap.width()
        self.wheel_h = pixmap.height()
        self.wheel.setPos(self._master.sceneBoundingRect().center())
        self.wheel.moveBy(-0.5*self.wheel_w, -0.5*self.wheel_h)
        self.wheel_center = self.wheel.sceneBoundingRect().center()
        self.wheel.setParentItem(self._master)
        self.wheel.hide()
        self.timer = QTimeLine()
        self.timer.setLoopCount(0)  # loop forever
        self.timer.setFrameRange(0, 10)
        self.wheel_animation = QGraphicsItemAnimation()
        self.wheel_animation.setItem(self.wheel)
        self.wheel_animation.setTimeLine(self.timer)
        # self.timer.frameChanged.connect(self.test)

    def test(self, frame):
        logging.debug(self.wheel_center)

    def start_wheel_animation(self):
        """Start the animation that plays when the Tool associated to this GraphicsItem
        is running (spinning wheel).
        """
        for angle in range(360):
            step = angle / 360.0
            self.wheel_animation.setTranslationAt(step, 0.5*self.wheel_w, 0.5*self.wheel_h)
            self.wheel_animation.setRotationAt(step, angle)
            self.wheel_animation.setTranslationAt(step, -0.5*self.wheel_w, -0.5*self.wheel_h)
            self.wheel_animation.setPosAt(step, self.wheel_center)
        self.wheel.show()
        self.timer.start()

    def stop_wheel_animation(self):
        """Stop wheel animation"""
        self.timer.stop()
        self.timer.setCurrentTime(0)
        self.wheel.hide()

    def make_master(self, pen, brush):
        """Calls super class method."""
        return super().make_master(pen, brush)

    def mouse_press_event(self, event):
        """Calls super class method."""
        super().mouse_press_event(event)

    def mouse_release_event(self, event):
        """Calls super class method."""
        super().mouse_release_event(event)

    def mouse_move_event(self, event):
        """Calls super class method."""
        super().mouse_move_event(event)

    def hover_enter_event(self, event):
        """Calls super class method."""
        super().hover_enter_event(event)

    def hover_leave_event(self, event):
        """Calls super class method."""
        super().hover_leave_event(event)

    def connector_mouse_press_event(self, event):
        """Calls super class method."""
        super().connector_mouse_press_event(event)

    def connector_hover_enter_event(self, event):
        """Calls super class method."""
        super().connector_hover_enter_event(event)

    def connector_hover_leave_event(self, event):
        """Calls super class method."""
        super().connector_hover_leave_event(event)

    def context_menu_event(self, event):
        """Calls super class method."""
        return super().context_menu_event(event)


class DataStoreImage(ItemImage):
    """Data Store item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        main (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, main, x, y, w, h, name):
        """Class constructor."""
        super().__init__(main, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 255, 255, 128))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 204, 204, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._main.ui.graphicsView.scene().addItem(self._master)
        self._main.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self._master)
        self.connector_button.setParentItem(self._master)

    def make_master(self, pen, brush):
        """Calls super class method."""
        return super().make_master(pen, brush)

    def mouse_press_event(self, event):
        """Calls super class method."""
        super().mouse_press_event(event)

    def mouse_release_event(self, event):
        """Calls super class method."""
        super().mouse_release_event(event)

    def mouse_move_event(self, event):
        """Calls super class method."""
        super().mouse_move_event(event)

    def hover_enter_event(self, event):
        """Calls super class method."""
        super().hover_enter_event(event)

    def hover_leave_event(self, event):
        """Calls super class method."""
        super().hover_leave_event(event)

    def connector_mouse_press_event(self, event):
        """Calls super class method."""
        super().connector_mouse_press_event(event)

    def connector_hover_enter_event(self, event):
        """Calls super class method."""
        super().connector_hover_enter_event(event)

    def connector_hover_leave_event(self, event):
        """Calls super class method."""
        super().connector_hover_leave_event(event)

    def context_menu_event(self, event):
        """Calls super class method."""
        return super().context_menu_event(event)


class ViewImage(ItemImage):
    """View item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        main (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, main, x, y, w, h, name):
        """Class constructor."""
        super().__init__(main, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 255, 0, 128))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 204, 0, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._main.ui.graphicsView.scene().addItem(self._master)
        self._main.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self._master)
        self.connector_button.setParentItem(self._master)

    def make_master(self, pen, brush):
        """Calls super class method."""
        return super().make_master(pen, brush)

    def mouse_press_event(self, event):
        """Calls super class method."""
        super().mouse_press_event(event)

    def mouse_release_event(self, event):
        """Calls super class method."""
        super().mouse_release_event(event)

    def mouse_move_event(self, event):
        """Calls super class method."""
        super().mouse_move_event(event)

    def hover_enter_event(self, event):
        """Calls super class method."""
        super().hover_enter_event(event)

    def hover_leave_event(self, event):
        """Calls super class method."""
        super().hover_leave_event(event)

    def connector_mouse_press_event(self, event):
        """Calls super class method."""
        super().connector_mouse_press_event(event)

    def connector_hover_enter_event(self, event):
        """Calls super class method."""
        super().connector_hover_enter_event(event)

    def connector_hover_leave_event(self, event):
        """Calls super class method."""
        super().connector_hover_leave_event(event)

    def context_menu_event(self, event):
        """Calls super class method."""
        return super().context_menu_event(event)


class Link(QGraphicsLineItem):
    """An item that represents a connection between project items.

    Attributes:
        qmainwindow (ToolboxUI): main UI class instance
        src_icon (ItemImage): Source icon
        dst_icon(ItemImage): Destination icon
    """
    def __init__(self, qmainwindow, src_icon, dst_icon):
        """Initializes item."""
        super().__init__()
        self._qmainwindow = qmainwindow
        self.src_icon = src_icon
        self.dst_icon = dst_icon
        self.src_connector = self.src_icon.conn_button()  # QGraphicsRectItem
        self.dst_connector = self.dst_icon.conn_button()
        self.setZValue(1)   # TODO: is this better than stackBefore?
        self.normal_color = QColor(255, 255, 0, 204)
        self.pen_width = 10
        self.arrow_size = 20
        self.setToolTip("<html><p>Connection from <b>{0}</b>'s output "
                        "to <b>{1}</b>'s input<\html>".format(self.src_icon.name(), self.dst_icon.name()))
        self.setPen(QPen(self.normal_color, self.pen_width))
        self.src_rect = self.src_connector.sceneBoundingRect()
        self.dst_rect = self.dst_connector.sceneBoundingRect()
        self.arrow_head = QPolygonF()
        self.update_line()
        self.setData(ITEM_TYPE, "link")
        self.src_center = None
        self.dst_center = None

    def update_line(self):
        """Update source and destination connector positions and repaint line."""
        self.src_rect = self.src_connector.sceneBoundingRect()
        self.dst_rect = self.dst_connector.sceneBoundingRect()
        self.src_center = self.src_rect.center()
        self.dst_center = self.dst_rect.center()
        self.setLine(self.src_center.x(), self.src_center.y(), self.dst_center.x(), self.dst_center.y())

    def mousePressEvent(self, e):
        """Trigger slot button if it is underneath.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if e.button() != Qt.LeftButton:
            e.ignore()
        else:
            if self.src_icon.conn_button().isUnderMouse():
                self.src_icon.mousePressEvent(e)
            elif self.dst_icon.conn_button().isUnderMouse():
                self.dst_icon.mousePressEvent(e)
                self.dst_icon.conn_button().animateClick()

    def contextMenuEvent(self, e):
        """Show context menu unless mouse is over one of the slot buttons.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        # TODO: Context menu must be shown on feedback Links as well
        if self.src_icon.conn_button().isUnderMouse() or self.dst_icon.conn_button().isUnderMouse():
            e.ignore()
        else:
            self._qmainwindow.show_link_context_menu(e.screenPos(), self.src_icon.name(), self.dst_icon.name())

    def paint(self, painter, option, widget):
        """Paint ellipse and arrow at from and to positions, respectively."""
        self.src_rect = self.src_connector.sceneBoundingRect()
        self.dst_rect = self.dst_connector.sceneBoundingRect()
        self.src_center = self.src_rect.center()
        self.dst_center = self.dst_rect.center()
        # Make line shorter to make room for an arrow head
        line = QLineF(self.src_center.x(), self.src_center.y(), self.dst_center.x(), self.dst_center.y())
        angle = atan2(-line.dy(), line.dx())
        arrow_p0 = line.p2()
        line.setLength(line.length() - self.arrow_size)
        self.setLine(line)
        arrow_p1 = arrow_p0 - QPointF(sin(angle + pi / 3) * self.arrow_size,
                                      cos(angle + pi / 3) * self.arrow_size)
        arrow_p2 = arrow_p0 - QPointF(sin(angle + pi - pi / 3) * self.arrow_size,
                                      cos(angle + pi - pi / 3) * self.arrow_size)
        self.arrow_head.clear()
        self.arrow_head.append(arrow_p0)
        self.arrow_head.append(arrow_p1)
        self.arrow_head.append(arrow_p2)
        brush = QBrush(self.normal_color, Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(self.src_center, self.pen_width, self.pen_width)
        painter.drawPolygon(self.arrow_head)
        self.setPen(QPen(self.normal_color, self.pen_width))
        super().paint(painter, option, widget)


class LinkDrawer(QGraphicsLineItem):
    """An item that allows one to draw links between slot buttons in QGraphicsView.

    Attributes:
        qmainwindow (ToolboxUI): QMainWindow instance
    """
    def __init__(self, qmainwindow):
        """Initializes instance."""
        super().__init__()
        self._qmainwindow = qmainwindow
        self.src = None  # source point
        self.dst = None  # destination point
        self.drawing = False
        # set pen
        self.pen_color = QColor(255, 0, 255)
        self.pen_width = 6
        self.arrow_size = 12
        self.arrow_head = QPolygonF()
        self.setPen(QPen(self.pen_color, self.pen_width))
        self.setZValue(2)  # TODO: is this better than stackBefore?
        self.hide()
        self.setData(ITEM_TYPE, "link-drawer")

    def start_drawing_at(self, src_point):
        """Start drawing from the center point of the clicked button.

        Args:
            src_point (QPointF): Center point of the clicked button
        """
        self.src = src_point
        self.dst = self.src
        self.setLine(self.src.x(), self.src.y(), self.src.x(), self.src.y())
        self.show()
        self.grabMouse()

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.src is not None:
            self.dst = e.scenePos()  # QPointF. The same as e.pos()
            self.update()

    def mousePressEvent(self, e):
        """If link lands on slot button, trigger click.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.ungrabMouse()
        self.hide()
        if e.button() != Qt.LeftButton:
            self.drawing = False
        else:
            pos = e.scenePos()
            view_pos = self._qmainwindow.ui.graphicsView.mapFromScene(pos)
            for item in self._qmainwindow.ui.graphicsView.items(view_pos):
                # logging.debug("item:{0}".format(item))
                if isinstance(item, QGraphicsRectItem):  # TODO: Is this test needed?
                    # logging.debug("QGraphicsRectItem found")
                    if hasattr(item, 'is_connector'):  # only a connector_button should have this
                        # Send mousePressEvent to QGraphicsRectItem (connector_button)
                        item.mousePressEvent(e)
                        return
            self.drawing = False
            self._qmainwindow.msg_error.emit("Unable to make connection."
                                             " Try landing the connection onto a connector button.")

    def paint(self, painter, option, widget):
        """Draw ellipse at begin position and arrowhead at end position."""
        # Make the drawn line shorter so that the arrow head has room
        line = QLineF(self.src.x(), self.src.y(), self.dst.x(), self.dst.y())
        angle = atan2(-line.dy(), line.dx())
        arrow_p0 = line.p2()
        line.setLength(line.length() - self.arrow_size)
        self.setLine(line)
        arrow_p1 = arrow_p0 - QPointF(sin(angle + pi / 3) * self.arrow_size,
                                      cos(angle + pi / 3) * self.arrow_size)
        arrow_p2 = arrow_p0 - QPointF(sin(angle + pi - pi / 3) * self.arrow_size,
                                      cos(angle + pi - pi / 3) * self.arrow_size)
        # Paint arrow head in the end of the line
        self.arrow_head.clear()
        self.arrow_head.append(arrow_p0)
        self.arrow_head.append(arrow_p1)
        self.arrow_head.append(arrow_p2)
        brush = QBrush(self.pen_color, Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(self.src, self.pen_width, self.pen_width)
        painter.drawPolygon(self.arrow_head)
        super().paint(painter, option, widget)
