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
from PySide2.QtCore import Qt, QPointF, QLineF, QRectF, QTimeLine
from PySide2.QtWidgets import QGraphicsItem, QGraphicsPathItem, \
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsRectItem, \
    QGraphicsItemAnimation, QGraphicsPixmapItem, QStyle
from PySide2.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath
from math import atan2, degrees, sin, cos, pi  # arrow head
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
        self.x_coord = x  # x coordinate in the scene (top left corner)
        self.y_coord = y  # y coordinate in the scene (top left corner)
        self.w = w
        self.h = h
        self.connector_pen = QPen(QColor('grey'))  # QPen is used to draw the item outline
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
        # Set name item position (centered)
        bounding_rect = self.name_item.sceneBoundingRect()
        self.name_item.setPos(self.x_coord + self.w/2 - bounding_rect.width()/2, self.y_coord)  # TODO: Refine position more?
        self.connector_button = QGraphicsRectItem()
        self.connector_button.setPen(self.connector_pen)
        self.connector_button.setBrush(self.connector_brush)
        self.connector_button.setRect(QRectF(self.x_coord+25, self.y_coord+25, 20, 20))  # TODO: Refine position
        self.connector_button.setAcceptHoverEvents(True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.connector_button.is_connector = True

    def make_data_master(self, pen, brush):
        """Make a parent of all other QGraphicsItems that
        make up the icon drawn on the scene.
        NOTE: setting the parent item moves the items as one!!
        """
        # Draw ellipse on the top
        scaled_rect = QRectF(self.q_rect)
        scaled_rect.setHeight((1/4)*self.h)
        top_ellipse = QGraphicsEllipseItem(scaled_rect)
        top_ellipse.setPen(pen)
        # Draw database image segments starting from top-right corner and moving counterclockwise
        path = QPainterPath()
        path.moveTo(self.x_coord + self.w, self.y_coord + (1/4 - 1/8)*self.h)
        path.arcTo(scaled_rect, 0, 180)
        path.lineTo(self.x_coord, self.y_coord + (3/4 + 1/8)*self.h)
        scaled_rect.translate(0, (3/4)*self.h)
        path.arcTo(scaled_rect, 180, 180)
        path.closeSubpath()
        icon = QGraphicsPathItem(path)
        top_ellipse.setParentItem(icon)
        icon.setPen(pen)
        icon.setBrush(brush)
        icon.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        # icon.setAcceptHoverEvents(True)
        return icon

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
        links = self._main.connection_model.connected_links(self._name)
        for link in links:
            link.update_geometry()
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
        # TODO: If link is under mouse, then invoke Link contextMenuEvent
        item = self._main.ui.graphicsView.scene().items(event.scenePos(), Qt.IntersectsItemShape, Qt.DescendingOrder, self._main.ui.graphicsView.transform())
        logging.debug(item)
        self._master.setSelected(True)
        self._main.show_item_image_context_menu(event.screenPos(), self.name())

    def key_press_event(self, event):
        """Remove item when pressing delete if it is selected.

        Args:
            event (QKeyEvent): Key event
        """
        if event.key() == Qt.Key_Delete and self._master.isSelected():
            name = self.name()
            ind = self._main.project_item_model.find_item(name, Qt.MatchExactly | Qt.MatchRecursive).index()
            self._main.remove_item(ind, delete_item=True)

    def show_item_info(self):
        """Update GUI to show the details of the selected item in a QDockWidget."""
        self._main.show_info(self.name())

    def start_drawing(self):
        """Start drawing a link from the center point of the connector button."""
        rect = self.conn_button().sceneBoundingRect()
        self._main.ui.graphicsView.draw_links(rect, self.name())


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
        self._master = self.make_data_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
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

    def key_press_event(self, event):
        """Calls super class method."""
        return super().key_press_event(event)


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
        self._master.keyPressEvent = self.key_press_event
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

    def key_press_event(self, event):
        """Calls super class method."""
        return super().key_press_event(event)


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
        self._master = self.make_data_master(self.pen, self.brush)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
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

    def key_press_event(self, event):
        """Calls super class method."""
        return super().key_press_event(event)


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
        self._master.keyPressEvent = self.key_press_event
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

    def key_press_event(self, event):
        """Calls super class method."""
        return super().key_press_event(event)


class Link(QGraphicsPathItem):
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
        self.setZValue(1)
        conn_width = self.src_connector.rect().width()
        self.arrow_angle = pi/4
        self.ellipse_angle = 30
        self.feedback_size = 10
        # Path parameters
        self.line_width = conn_width/2
        self.arrow_length = self.line_width
        self.arrow_diag = self.arrow_length / sin(self.arrow_angle)
        arrow_base = 2 * self.arrow_diag * cos(self.arrow_angle)
        self.t1 = (arrow_base - self.line_width) / 2 / arrow_base
        self.t2 = 1.0 - self.t1
        self.inner_rect = QRectF(0, 0, 7.5*self.feedback_size, 6*self.feedback_size - self.line_width)
        self.outer_rect = QRectF(0, 0, 8*self.feedback_size, 6*self.feedback_size + self.line_width)
        self.inner_angle = degrees(atan2(conn_width/2, self.inner_rect.height()/2))
        self.outer_angle = degrees(atan2(conn_width/2, self.outer_rect.height()/2))
        # Tooltip
        self.setToolTip("<html><p>Connection from <b>{0}</b>'s output "
                        "to <b>{1}</b>'s input<\html>".format(self.src_icon.name(), self.dst_icon.name()))
        # self.selected_brush = QBrush(QColor(255, 0, 255, 204))
        # self.normal_brush = QBrush(QColor(255, 255, 0, 204))
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.selected_pen = QPen(Qt.DashLine)
        self.normal_pen = Qt.NoPen
        self.setData(ITEM_TYPE, "link")
        self.model_index = None
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.update_geometry()

    def find_model_index(self):
        """Find model index from connection model."""
        row = self._qmainwindow.connection_model.header.index(self.src_icon.name())
        column = self._qmainwindow.connection_model.header.index(self.dst_icon.name())
        self.model_index = self._qmainwindow.connection_model.index(row, column)

    def find_parallel_link(self):
        """Find parallel link."""
        self.parallel_link = None
        for item in self.collidingItems():
            try:
                if item.src_icon == self.dst_icon and item.dst_icon == self.src_icon:
                    self.parallel_link = item
                    break
            except AttributeError:
                continue

    def send_to_bottom(self):
        """"""
        if self.parallel_link:
            self.stackBefore(self.parallel_link)

    def mousePressEvent(self, e):
        """Trigger slot button if it is underneath.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if e.button() != Qt.LeftButton:
            e.ignore()
        else:
            # Trigger connector button if underneath
            if self.src_icon.conn_button().isUnderMouse():
                self.src_icon.mousePressEvent(e)
            elif self.dst_icon.conn_button().isUnderMouse():
                self.dst_icon.mousePressEvent(e)

    def contextMenuEvent(self, e):
        """Show context menu unless mouse is over one of the slot buttons.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self.find_model_index()
        self.find_parallel_link()
        self._qmainwindow.show_link_context_menu(e.screenPos(), self)

        # if self.src_icon.conn_button().isUnderMouse() or self.dst_icon.conn_button().isUnderMouse():
        #     e.ignore()
        # else:
        #     self.setSelected(True)
        #     self.find_model_index()
        #     self.find_parallel_link()
        #     self._qmainwindow.show_link_context_menu(e.screenPos(), self)

    def keyPressEvent(self, event):
        """Remove associated connection if this is selected and delete is pressed"""
        if event.key() == Qt.Key_Delete and self.isSelected():
            self.find_model_index()
            self._qmainwindow.ui.graphicsView.remove_link(self.model_index)

    def shape(self):
        """Reimplemented to enable selecting the link by right-clicking on the arrow head and starting ellipse."""
        # TODO: Apparently this is not needed due to this being a QGraphicsPathItem now
        path = super().shape()
        # path.addPolygon(self.arrow_head)
        # if self.src_center is not None:
        #     path.addEllipse(self.src_center, self.ellipse_radius, self.ellipse_radius)
        return path

    def update_geometry(self):
        """Update path."""
        self.prepareGeometryChange()
        src_rect = self.src_connector.sceneBoundingRect()
        dst_rect = self.dst_connector.sceneBoundingRect()
        src_center = src_rect.center()
        dst_center = dst_rect.center()
        # Angle between connector centers
        angle = atan2(src_center.y() - dst_center.y(), dst_center.x() - src_center.x())
        # Path coordinates. We just need to draw the arrow and the ellipse, lines are drawn automatically
        arrow_p0 = dst_center
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi-self.arrow_angle)), cos(angle + (pi-self.arrow_angle)))
        arrow_p1 = arrow_p0 - d1 * self.arrow_diag
        arrow_p2 = arrow_p0 - d2 * self.arrow_diag
        line = QLineF(arrow_p1, arrow_p2)
        p1 = line.pointAt(self.t1)
        p2 = line.pointAt(self.t2)
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.moveTo(p2)
        path.lineTo(arrow_p2)
        path.lineTo(arrow_p0)
        path.lineTo(arrow_p1)
        path.lineTo(p1)
        # Draw inner part of feedback link
        if self.src_connector == self.dst_connector:
            self.inner_rect.moveCenter(dst_center - QPointF(0, self.inner_rect.height()/2 + self.line_width/2))
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2*self.inner_angle - 360)
        path.arcTo(src_rect, (180/pi)*angle + self.ellipse_angle, 360 - 2*self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_connector == self.dst_connector:
            self.outer_rect.moveCenter(dst_center - QPointF(0, self.outer_rect.height()/2 - self.line_width/2))
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2*self.outer_angle)
        path.closeSubpath()
        self.setPath(path)

    def paint(self, painter, option, widget):
        """Paint ellipse and arrow at from and to positions, respectively."""
        # logging.debug("paint link")
        # Set brush according to selection state
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            # self.setBrush(self.selected_brush)
            self.setPen(self.selected_pen)
        else:
            painter.setPen(Qt.NoPen)
            # self.setBrush(self.normal_brush)
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)


class LinkDrawer(QGraphicsPathItem):
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
        self.arrow_angle = pi/4
        self.ellipse_angle = 30
        self.feedback_size = 10
        # Path parameters
        self.ellipse_width = None
        self.line_width = None
        self.arrow_length = None
        self.arrow_diag = None
        self.src_rect = None
        self.ellipse_rect = None
        self.t1 = None
        self.t2 = None
        self.inner_rect = None
        self.outer_rect = None
        self.inner_angle = None
        self.outer_angle = None
        self.setBrush(QBrush(QColor(255, 0, 255, 204)))
        self.setZValue(2)  # TODO: is this better than stackBefore?
        self.hide()
        self.setData(ITEM_TYPE, "link-drawer")
        self.setPen(QPen(Qt.gray))

    def start_drawing_at(self, src_rect):
        """Start drawing from the center point of the clicked button.

        Args:
            src_rect (QRecF): Rectangle of the clicked button
        """
        self.src_rect = src_rect
        self.src = self.src_rect.center()
        self.dst = self.src
        # Path parameters
        conn_width = self.src_rect.width()
        self.ellipse_width = (3/4)*conn_width
        self.line_width = self.ellipse_width/2
        self.arrow_length = self.line_width
        self.arrow_diag = self.arrow_length / sin(self.arrow_angle)
        self.ellipse_rect = QRectF(0, 0, self.ellipse_width, self.ellipse_width)
        self.ellipse_rect.moveCenter(self.src)
        arrow_base = 2 * self.arrow_diag * cos(self.arrow_angle)
        self.t1 = (arrow_base - self.line_width) / 2 / arrow_base
        self.t2 = 1.0 - self.t1
        self.inner_rect = QRectF(0, 0, 7.5*self.feedback_size, 6*self.feedback_size - self.line_width)
        self.outer_rect = QRectF(0, 0, 8*self.feedback_size, 6*self.feedback_size + self.line_width)
        self.inner_angle = degrees(atan2(self.ellipse_width/2, self.inner_rect.height()/2))
        self.outer_angle = degrees(atan2(self.ellipse_width/2, self.outer_rect.height()/2))
        self.show()

    def update_geometry(self):
        """Update path."""
        self.prepareGeometryChange()
        # Angle between connector centers
        if self.src_rect.contains(self.dst):
            angle = 0
            self.dst = self.src
        else:
            angle = atan2(self.src.y() - self.dst.y(), self.dst.x() - self.src.x())
        # Path coordinates
        arrow_p0 = self.dst
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi-self.arrow_angle)), cos(angle + (pi-self.arrow_angle)))
        arrow_p1 = arrow_p0 - d1 * self.arrow_diag
        arrow_p2 = arrow_p0 - d2 * self.arrow_diag
        line = QLineF(arrow_p1, arrow_p2)
        p1 = line.pointAt(self.t1)
        p2 = line.pointAt(self.t2)
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.moveTo(p2)
        path.lineTo(arrow_p2)
        path.lineTo(arrow_p0)
        path.lineTo(arrow_p1)
        path.lineTo(p1)
        # Draw inner part of feedback link
        if self.src_rect.contains(self.dst):
            self.inner_rect.moveCenter(self.dst - QPointF(0, self.inner_rect.height()/2 + self.line_width/2))
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2*self.inner_angle - 360)
        path.arcTo(self.ellipse_rect, (180/pi)*angle + self.ellipse_angle, 360 - 2*self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_rect.contains(self.dst):
            self.outer_rect.moveCenter(self.dst - QPointF(0, self.outer_rect.height()/2 - self.line_width/2))
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2*self.outer_angle)
        path.closeSubpath()
        self.setPath(path)
