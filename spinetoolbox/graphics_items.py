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
Classes for drawing graphics items on QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

import logging
import os
from PySide2.QtCore import Qt, QPointF, QLineF, QRectF, QTimeLine, QTimer
from PySide2.QtWidgets import QGraphicsItem, QGraphicsPathItem, \
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsRectItem, \
    QGraphicsItemAnimation, QGraphicsPixmapItem, QGraphicsLineItem, QStyle
from PySide2.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath, QRadialGradient, QFont, QTransform
from math import atan2, degrees, sin, cos, pi
from helpers import object_pixmap


class SceneBackground(QGraphicsRectItem):
    """Experimental. This should be used to paint the scene background white."""
    def __init__(self, toolbox):
        super().__init__(toolbox.ui.graphicsView.scene().sceneRect())
        self._toolbox = toolbox
        self.bg_pen = QPen(QColor('blue'))  # QPen is used to draw the item outline
        self.bg_brush = QBrush(QColor(0, 0, 0, 128))  # QBrush is used to fill the item
        self.setPen(self.bg_pen)
        self.setBrush(self.bg_brush)
        self.setZValue(-1)
        self._toolbox.ui.graphicsView.scene().addItem(self)

    # @Slot("QRectF", name="update_scene_bg")
    # def update_scene_bg(self, rect):
    #     self.setRect(rect)

    def update_bg(self):
        """Work in progress."""
        self.setRect(self._toolbox.ui.graphicsView.scene().sceneRect())


class ItemImage(QGraphicsItem):
    """Base class for all Item icons drawn on QGraphicsScene.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__()
        self._toolbox = toolbox
        self.x_coord = x  # x coordinate in the scene (top left corner)
        self.y_coord = y  # y coordinate in the scene (top left corner)
        self.w = w
        self.h = h
        self.connector_pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.connector_pen.setStyle(Qt.DotLine)
        self.connector_brush = QBrush(QColor(255, 255, 255, 0))  # QBrush is used to fill the item
        self.connector_hover_brush = QBrush(QColor(50, 0, 50, 128))  # QBrush is used to fill the item
        self.font_size = 8  # point size
        self.q_rect = QRectF(self.x_coord, self.y_coord, self.w, self.h)  # Position and size of the drawn item
        # Make QGraphicsSimpleTextItem for item name.
        self.name_item = QGraphicsSimpleTextItem(name)
        self.name_width = 12  # Initial value (not used)
        self.set_name_attributes()  # Set font, size, position, etc.
        self.connector_button = QGraphicsRectItem()
        self.connector_button.setPen(self.connector_pen)
        self.connector_button.setBrush(self.connector_brush)
        self.connector_button.setRect(self.q_rect.adjusted(2.5*w/7, 2.5*h/7, -2.5*w/7, -2.5*h/7))
        self.connector_button.setAcceptHoverEvents(True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.connector_button.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)

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
        gradient = QRadialGradient(self.q_rect.topLeft(), self.w)
        gradient.setColorAt(1, brush.color().darker())
        gradient.setColorAt(0, brush.color().lighter())
        icon.setBrush(QBrush(gradient))
        # icon.setBrush(brush)
        icon.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        # icon.setAcceptHoverEvents(True)
        icon.setAcceptDrops(True)
        return icon

    def make_master(self, pen, brush):
        """Make a parent of all other QGraphicsItems that
        make up the icon drawn on the scene.
        NOTE: setting the parent item moves the items as one!!
        """
        icon = QGraphicsEllipseItem(self.q_rect)
        icon.setPen(pen)
        gradient = QRadialGradient(self.q_rect.topLeft(), self.w)
        gradient.setColorAt(1, brush.color().darker())
        gradient.setColorAt(0, brush.color().lighter())
        icon.setBrush(QBrush(gradient))
        # icon.setBrush(brush)
        icon.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        icon.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        # icon.setAcceptHoverEvents(True)
        icon.setAcceptDrops(True)
        return icon

    def name(self):
        """Returns name of the item that is represented by this icon."""
        return self.name_item.text()

    def update_name_item(self, new_name):
        """Set a new text to name item. Used when a project item is renamed."""
        self.name_item.setText(new_name)
        self.set_name_attributes()

    def set_name_attributes(self):
        """Set name QGraphicsSimpleTextItem attributes (font, size, position, etc.)"""
        self.name_item.setZValue(3)
        # Set font size and style
        font = self.name_item.font()
        font.setPointSize(self.font_size)
        font.setBold(True)
        self.name_item.setFont(font)
        # Set name item position (centered on top of the master icon)
        self.name_width = self.name_item.sceneBoundingRect().width()
        self.name_item.setPos(self.x_coord + self.w/2 - self.name_width/2, self.y_coord - 20)

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
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self.show_item_info()

    def mouse_move_event(self, event):
        """Move icon while the mouse button is pressed.
        Update links that are connected to this icon.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        QGraphicsItem.mouseMoveEvent(self._master, event)
        links = self._toolbox.connection_model.connected_links(self.name())
        for link in links:
            link.update_geometry()
        master_rect = self._master.sceneBoundingRect()
        self.name_item.setPos(master_rect.left() + self.w/2 - self.name_width/2, master_rect.top() - 20)
        self.x_coord = master_rect.x()
        self.y_coord = master_rect.y()

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
            self.draw_link()

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
        self._master.setSelected(True)
        self._toolbox.show_item_image_context_menu(event.screenPos(), self.name())

    def key_press_event(self, event):
        """Remove item when pressing delete if it is selected.

        Args:
            event (QKeyEvent): Key event
        """
        if event.key() == Qt.Key_Delete and self._master.isSelected():
            ind = self._toolbox.project_item_model.find_item(self.name())
            self._toolbox.remove_item(ind, delete_item=self._toolbox._config.getboolean("settings", "delete_data"))

    def show_item_info(self):
        """Update GUI to show the details of the selected item."""
        ind = self._toolbox.project_item_model.find_item(self.name())
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)

    def draw_link(self):
        """Start or stop drawing a link from or to the center point of the connector button."""
        rect = self.conn_button().sceneBoundingRect()
        self._toolbox.ui.graphicsView.draw_links(rect, self.name())

    def item_change(self, change, value):
        """Remove name_item when master is removed from scene."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            self._master.scene().removeItem(self.name_item)
            return value
        return QGraphicsItem.itemChange(self._master, change, value)


class DataConnectionImage(ItemImage):
    """Data Connection item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 0, 255, 160))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 0, 204, 128))  # QBrush while hovering
        # Draw ellipse
        self._master = self.make_data_master(self.pen, self.brush)
        self._master.setAcceptDrops(True)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
        self._master.itemChange = self.item_change
        self._master.dragEnterEvent = self.drag_enter_event
        self._master.dragLeaveEvent = self.drag_leave_event
        self._master.dragMoveEvent = self.drag_move_event
        self._master.dropEvent = self.drop_event
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self._master)
        self._toolbox.ui.graphicsView.scene().addItem(self.name_item)
        # Group the drawn items together by setting the master as the parent of other QGraphicsItems
        # self.name_item.setParentItem(self._master)
        self.connector_button.setParentItem(self._master)
        self.drag_over = False

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

    def item_change(self, change, value):
        """Calls super class method."""
        return super().item_change(change, value)

    def drag_enter_event(self, event):
        """Drag and drop action enters.
        Accept file drops from the filesystem.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        urls = event.mimeData().urls()
        for url in urls:
            if not url.isLocalFile():
                event.ignore()
                return
            if not os.path.isfile(url.toLocalFile()):
                event.ignore()
                return
        event.accept()
        event.setDropAction(Qt.CopyAction)
        if self.drag_over:
            return
        self.drag_over = True
        QTimer.singleShot(500, self.select_on_drag_over)

    def drag_leave_event(self, event):
        """Drag and drop action leaves.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        event.accept()
        self.drag_over = False

    def drag_move_event(self, event):
        """Accept event."""
        event.accept()

    def drop_event(self, event):
        """Emit files_dropped_on_dc signal from scene,
        with this instance, and a list of files for each dropped url."""
        self._master.scene().files_dropped_on_dc.emit(self, [url.toLocalFile() for url in event.mimeData().urls()])

    def select_on_drag_over(self):
        """Called when the timer started in drag_enter_event is elapsed.
        Select this item if the drag action is still over it.
        """
        if not self.drag_over:
            return
        self.drag_over = False
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self._master.setSelected(True)
        self.show_item_info()


class ToolImage(ItemImage):
    """Tool item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(255, 0, 0, 160))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(204, 0, 0, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_master(self.pen, self.brush)
        self._master.setAcceptDrops(False)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
        self._master.itemChange = self.item_change
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self._master)
        self._toolbox.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        # self.name_item.setParentItem(self._master)
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

    def item_change(self, change, value):
        """Calls super class method."""
        return super().item_change(change, value)


class DataStoreImage(ItemImage):
    """Data Store item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 255, 255, 160))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 204, 204, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_data_master(self.pen, self.brush)
        self._master.setAcceptDrops(False)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
        self._master.itemChange = self.item_change
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self._master)
        self._toolbox.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        # self.name_item.setParentItem(self._master)
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

    def item_change(self, change, value):
        """Calls super class method."""
        return super().item_change(change, value)


class ViewImage(ItemImage):
    """View item that is drawn into QGraphicsScene. NOTE: Make sure
    to set self._master as the parent of all drawn items. This groups the
    individual QGraphicsItems together.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(QColor('black'))  # QPen is used to draw the item outline
        self.brush = QBrush(QColor(0, 255, 0, 160))  # QBrush is used to fill the item
        self.hover_brush = QBrush(QColor(0, 204, 0, 128))  # QBrush while hovering
        # Draw icon
        self._master = self.make_master(self.pen, self.brush)
        self._master.setAcceptDrops(False)
        # Override event handlers
        self._master.mousePressEvent = self.mouse_press_event
        self._master.mouseReleaseEvent = self.mouse_release_event
        self._master.mouseMoveEvent = self.mouse_move_event
        self._master.hoverEnterEvent = self.hover_enter_event
        self._master.hoverLeaveEvent = self.hover_leave_event
        self._master.contextMenuEvent = self.context_menu_event
        self._master.keyPressEvent = self.key_press_event
        self._master.itemChange = self.item_change
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self._master)
        self._toolbox.ui.graphicsView.scene().addItem(self.name_item)
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        # self.name_item.setParentItem(self._master)
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

    def item_change(self, change, value):
        """Calls super class method."""
        return super().item_change(change, value)


class Link(QGraphicsPathItem):
    """An item that represents a connection between project items.

    Attributes:
        toolbox (ToolboxUI): main UI class instance
        src_icon (ItemImage): Source icon
        dst_icon(ItemImage): Destination icon
    """
    def __init__(self, toolbox, src_icon, dst_icon):
        """Initializes item."""
        super().__init__()
        self._toolbox = toolbox
        self.src_icon = src_icon
        self.dst_icon = dst_icon
        self.src_connector = self.src_icon.conn_button()  # QGraphicsRectItem
        self.dst_connector = self.dst_icon.conn_button()
        self.setZValue(1)
        self.conn_width = self.src_connector.rect().width()
        self.arrow_angle = pi/4  # In rads
        self.ellipse_angle = 30  # In degrees
        self.feedback_size = 12
        # Path parameters
        self.line_width = self.conn_width/2
        self.arrow_length = self.line_width
        self.arrow_diag = self.arrow_length / sin(self.arrow_angle)
        arrow_base = 2 * self.arrow_diag * cos(self.arrow_angle)
        self.t1 = (arrow_base - self.line_width) / arrow_base/2
        self.t2 = 1.0 - self.t1
        # Inner rect of feedback link (works, but it's probably too hard)
        self.inner_rect = QRectF(0, 0, 7.5*self.feedback_size, 6*self.feedback_size - self.line_width)
        inner_shift_x = self.arrow_length/2
        angle = atan2(self.conn_width, self.inner_rect.height())
        inner_shift_y = (self.inner_rect.height()*cos(angle) + self.line_width)/2
        self.inner_shift = QPointF(inner_shift_x, inner_shift_y)
        self.inner_angle = degrees(atan2(inner_shift_x + self.conn_width/2, inner_shift_y - self.line_width/2))
        # Outer rect of feedback link
        self.outer_rect = QRectF(0, 0, 8*self.feedback_size, 6*self.feedback_size + self.line_width)
        outer_shift_x = self.arrow_length/2
        angle = atan2(self.conn_width, self.outer_rect.height())
        outer_shift_y = (self.outer_rect.height()*cos(angle) - self.line_width)/2
        self.outer_shift = QPointF(outer_shift_x, outer_shift_y)
        self.outer_angle = degrees(atan2(outer_shift_x + self.conn_width/2, outer_shift_y + self.line_width/2))
        # Tooltip
        self.setToolTip("<html><p>Connection from <b>{0}</b>'s output "
                        "to <b>{1}</b>'s input<\html>".format(self.src_icon.name(), self.dst_icon.name()))
        # self.selected_brush = QBrush(QColor(255, 0, 255, 204))
        # self.normal_brush = QBrush(QColor(255, 255, 0, 204))
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.selected_pen = QPen(Qt.black, 0.5, Qt.DashLine)
        self.normal_pen = QPen(Qt.black, 0.5)
        self.model_index = None
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.update_geometry()

    def find_model_index(self):
        """Find model index from connection model."""
        row = self._toolbox.connection_model.header.index(self.src_icon.name())
        column = self._toolbox.connection_model.header.index(self.dst_icon.name())
        self.model_index = self._toolbox.connection_model.index(row, column)

    def find_parallel_link(self):
        """Find parallel link."""
        self.parallel_link = None
        for item in self.collidingItems():
            if not isinstance(item, Link):
                continue
            if item.src_icon == self.dst_icon and item.dst_icon == self.src_icon:
                self.parallel_link = item
                break

    def send_to_bottom(self):
        """Send link behind other links."""
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
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def keyPressEvent(self, event):
        """Remove associated connection if this is selected and delete is pressed."""
        if event.key() == Qt.Key_Delete and self.isSelected():
            self.find_model_index()
            self._toolbox.ui.graphicsView.remove_link(self.model_index)

    def update_geometry(self):
        """Update path."""
        self.prepareGeometryChange()
        src_rect = self.src_connector.sceneBoundingRect()
        dst_rect = self.dst_connector.sceneBoundingRect()
        src_center = src_rect.center()
        dst_center = dst_rect.center()
        # Angle between connector centers
        if self.src_connector == self.dst_connector:  # feedback link
            arrow_p0 = QPointF(dst_rect.left(), dst_rect.center().y())  # arrow tip is the center left side of button
            angle = 0
        else:  # normal link
            line = QLineF(src_center, dst_center)
            try:
                t = (line.length() - self.conn_width/2) / line.length()
            except ZeroDivisionError:
                t = 1
            arrow_p0 = line.pointAt(t)  # arrow tip is where the line intersects the button
            angle = atan2(-line.dy(), line.dx())
        # Path coordinates. We just need to draw the arrow and the ellipse, lines are drawn automatically
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
            self.inner_rect.moveCenter(dst_center - self.inner_shift)
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2*self.inner_angle - 360)
        path.arcTo(src_rect, degrees(angle) + self.ellipse_angle, 360 - 2*self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_connector == self.dst_connector:
            self.outer_rect.moveCenter(dst_center - self.outer_shift)
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2*self.outer_angle)
        path.closeSubpath()
        self.setPath(path)

    def paint(self, painter, option, widget):
        """Set pen according to selection state."""
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        """Bring selected link to top."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and value == 1:
            for item in self.collidingItems():  # TODO: try using scene().collidingItems() which is ordered
                if not isinstance(item, Link):
                    continue
                item.stackBefore(self)
            return value
        return super().itemChange(change, value)


class LinkDrawer(QGraphicsPathItem):
    """An item that allows one to draw links between slot buttons in QGraphicsView.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
    """
    def __init__(self, toolbox):
        """Initializes instance."""
        super().__init__()
        self._toolbox = toolbox
        self.src = None  # source point
        self.dst = None  # destination point
        self.drawing = False
        self.arrow_angle = pi/4
        self.ellipse_angle = 30
        self.feedback_size = 12
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
        self.setPen(QPen(Qt.black, 0.5))
        self.setZValue(2)  # TODO: is this better than stackBefore?
        self.hide()

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
        self.t1 = (arrow_base - self.line_width) / arrow_base/2
        self.t2 = 1.0 - self.t1
        # Inner rect of feedback link
        self.inner_rect = QRectF(0, 0, 7.5*self.feedback_size, 6*self.feedback_size - self.line_width)
        inner_shift_x = self.arrow_length/2
        angle = atan2(self.ellipse_width, self.inner_rect.height())
        inner_shift_y = (self.inner_rect.height()*cos(angle) + self.line_width)/2
        self.inner_shift = QPointF(inner_shift_x, inner_shift_y)
        self.inner_angle = degrees(atan2(inner_shift_x + self.ellipse_width/2, inner_shift_y - self.line_width/2))
        # Outer rect of feedback link
        self.outer_rect = QRectF(0, 0, 8*self.feedback_size, 6*self.feedback_size + self.line_width)
        outer_shift_x = self.arrow_length/2
        angle = atan2(self.ellipse_width, self.outer_rect.height())
        outer_shift_y = (self.outer_rect.height()*cos(angle) - self.line_width)/2
        self.outer_shift = QPointF(outer_shift_x, outer_shift_y)
        self.outer_angle = degrees(atan2(outer_shift_x + self.ellipse_width/2, outer_shift_y + self.line_width/2))
        self.update_geometry()
        self.show()

    def update_geometry(self):
        """Update path."""
        self.prepareGeometryChange()
        # Angle between connector centers
        if self.src_rect.contains(self.dst):
            angle = 0
            arrow_p0 = QPointF(self.src_rect.left(), self.src_rect.center().y())
        else:
            angle = atan2(self.src.y() - self.dst.y(), self.dst.x() - self.src.x())
            arrow_p0 = self.dst
        # Path coordinates
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
            self.inner_rect.moveCenter(self.src - self.inner_shift)
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2*self.inner_angle - 360)
        path.arcTo(self.ellipse_rect, (180/pi)*angle + self.ellipse_angle, 360 - 2*self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_rect.contains(self.dst):
            self.outer_rect.moveCenter(self.src - self.outer_shift)
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2*self.outer_angle)
        path.closeSubpath()
        self.setPath(path)


class ObjectItem(QGraphicsPixmapItem):
    """Object item to use with GraphViewForm.

    Attributes:
        graph_view_form (GraphViewForm): 'owner'
        object_id (int): object id (for filtering parameters)
        object_name (str): object name
        object_class_id (int): object class id (for filtering parameters)
        object_class_name (str): object class name
        x (float): x-coordinate of central point
        y (float): y-coordinate of central point
        extent (int): preferred extent
        label_font (QFont): label font
        label_color (QColor): label bg color
        label_position (str)
    """
    def __init__(self, graph_view_form, object_id, object_name, object_class_id, object_class_name,
                 x, y, extent, label_font=QFont(), label_color=QColor(), label_position="under_icon"):
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id = object_id
        self.object_name = object_name
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._extent = extent
        self._label_color = label_color
        self._label_position = label_position
        self.label_item = ObjectLabelItem(object_name, label_font, label_color)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.is_template = False
        self.template_id_dim = {}  # NOTE: for a template item this should have one and only one entry
        self._original_pos = None
        self._merge_target = None
        self._merge = False
        self._bounce = False
        self._views_cursor = {}
        self.shade = QGraphicsRectItem()
        self._selected_color = graph_view_form.palette().highlight()
        pixmap = self._graph_view_form.object_icon(object_class_name).pixmap(extent)
        self.setPixmap(pixmap.scaled(extent, extent))
        self.setZValue(-1)
        self.setPos(x, y)
        self.setOffset(-0.5 * extent, -0.5 * extent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.shade.setRect(self.boundingRect())
        self.shade.setBrush(self._selected_color)
        self.shade.setPen(Qt.NoPen)
        self.shade.setParentItem(self)
        self.shade.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
        self.shade.hide()

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            self.shade.show()
            self.label_item.setBrush(self._selected_color)
            option.state &= ~QStyle.State_Selected
        else:
            self.shade.hide()
            self.label_item.setBrush(self._label_color)
        super().paint(painter, option, widget)

    def setParentItem(self, parent):
        """Set same parent for label item."""
        super().setParentItem(parent)
        self.label_item.setParentItem(parent)
        self.place_label_item()

    def itemChange(self, change, value):
        """Add label item to same scene if added as top level item."""
        if change == QGraphicsItem.ItemSceneChange and value and self.topLevelItem() == self:
            scene = value
            value.addItem(self.label_item)
            self.place_label_item()
        return super().itemChange(change, value)

    def place_label_item(self):
        """Put label item in position."""
        x = self.x() - self.label_item.boundingRect().width() / 2
        y = self.y() + self.offset().y() + (self.boundingRect().height() - self.label_item.boundingRect().height()) / 2
        if self._label_position == "under_icon":
            y += self._extent
        elif self._label_position == "over_icon":
            y -= self._extent
        elif self._label_position == "beside_icon":
            x += self._extent / 2 + self.label_item.boundingRect().width() / 2
        self.label_item.setPos(x, y)

    def make_template(self):
        """Make this object par of a template for a relationship."""
        self.is_template = True
        font = QFont("", 0.75 * self._extent)
        brush = QBrush(Qt.white)
        outline_pen = QPen(Qt.black, 8, Qt.SolidLine)
        question_item = CustomTextItem("?", font, brush=brush, outline_pen=outline_pen)
        question_item.setParentItem(self)
        rect = self.boundingRect()
        question_rect = question_item.boundingRect()
        x = rect.center().x() - question_rect.width() / 2
        y = rect.center().y() - question_rect.height() / 2
        question_item.setPos(x, y)
        self.setToolTip("<html>Drag-and-drop this onto a <b>{}</b> object "
                        "(or viceversa) to complete this relationship.".format(self.object_class_name))

    def shape(self):
        """Make the entire bounding rect to be the shape."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def mousePressEvent(self, event):
        """Save original position."""
        super().mousePressEvent(event)
        self._original_pos = self.pos()

    def mouseMoveEvent(self, event):
        """Call move related items and check for a merge target."""
        super().mouseMoveEvent(event)
        object_items = [x for x in self.scene().selectedItems() if isinstance(x, ObjectItem)]
        for item in object_items:
            item.move_related_items_by(event.scenePos() - event.lastScenePos())
        self.check_for_merge_target(event.scenePos())
        # Depending on the value of merge target and bounce, set the drop indicator cursor
        for view in self.scene().views():
            if view not in self._views_cursor:
                self._views_cursor[view] = view.viewport().cursor()
            if self._merge_target:
                view.viewport().setCursor(Qt.DragCopyCursor)
            elif self._bounce:
                view.viewport().setCursor(Qt.ForbiddenCursor)
            else:
                try:
                    view.viewport().setCursor(self._views_cursor[view])
                except KeyError:
                    pass

    def check_for_merge_target(self, scene_pos):
        """Check if this item is touching another item so they can merge
        (this happens when building a relationship)."""
        self._merge_target = None
        self._bounce = False
        for item in self.scene().items(scene_pos):
            if item == self:
                continue
            if not isinstance(item, ObjectItem):
                continue
            if item.is_template != self.is_template:
                if item.object_class_name == self.object_class_name:
                    self._merge_target = item
                    break
            self._bounce = True
            break

    def mouseReleaseEvent(self, event):
        """Merge, bounce, or just do nothing."""
        super().mouseReleaseEvent(event)
        if self._merge_target:
            if not self.merge_item():
                self._bounce = True
        if self._bounce:
            self.move_related_items_by(self._original_pos - self.pos())
            self.setPos(self._original_pos)
            self._original_pos = None

    def merge_item(self):
        """Merge this item with the one from the _merge_target attribute.
        Try and create a relationship if needed."""
        if self.is_template:
            template = self
            instance = self._merge_target
        else:
            template = self._merge_target
            instance = self
        # Set the object_name attribute of template, assuming everything will go fine.
        template_object_name = template.object_name
        template.object_name = instance.object_name
        template_buddies = template.template_buddies()
        if not [x for x in template_buddies if x.is_template and x != template]:
            # The only template left is the one we're merging
            template_id = list(template.template_id_dim)[0]
            if not self._graph_view_form.add_relationship(template_id, template_buddies):
                # Restablish template object name, since something went wrong (not that it matters too much, though)
                template.object_name = template_object_name
                return False
        # Add template id-dimension to instance
        instance.template_id_dim.update(template.template_id_dim)
        template.move_related_items_by(instance.pos() - template.pos())
        for arc_item in template.outgoing_arc_items:
            arc_item.src_item = instance
        for arc_item in template.incoming_arc_items:
            arc_item.dst_item = instance
        instance.incoming_arc_items.extend(template.incoming_arc_items)
        instance.outgoing_arc_items.extend(template.outgoing_arc_items)
        self.scene().removeItem(template.label_item)
        self.scene().removeItem(template)
        return True

    def template_buddies(self):
        """A list of all object items in the same template."""
        if not self.is_template:  # NOTE: This shouldn't happen
            logging.debug("template_buddies method shouldn't be called on a non-template item.")
            return []
        template_id = list(self.template_id_dim)[0]  # NOTE: a template item should have one and only one template
        return [x for x in self.scene().items() if isinstance(x, ObjectItem) and template_id in x.template_id_dim]

    def move_related_items_by(self, pos_diff):
        """Move related items."""
        self.label_item.moveBy(pos_diff.x(), pos_diff.y())
        for item in self.outgoing_arc_items:
            item.move_src_by(pos_diff)
        for item in self.incoming_arc_items:
            item.move_dst_by(pos_diff)

    def hoverEnterEvent(self, event):
        """Make related arcs know that this is hovered."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = True
        for item in self.outgoing_arc_items:
            item.is_src_hovered = True

    def hoverLeaveEvent(self, event):
        """Make related arcs know that this isn't hovered."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = False
        for item in self.outgoing_arc_items:
            item.is_src_hovered = False

    def contextMenuEvent(self, e):
        """Show context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        e.accept()
        if not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        self._graph_view_form.show_object_item_context_menu(e, self)

    def set_all_visible(self, on):
        """Set visible attribute for this item and all related ones."""
        self.label_item.setVisible(on)
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            item.setVisible(on)
        self.setVisible(on)


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm.

    Attributes:
        graph_view_form (GraphViewForm): 'owner'
        object_id_list (str): object id comma separated list
        relationship_class_id (int): relationship class id (for filtering parameters)
        src_item (ObjectItem): source item
        dst_item (ObjectItem): destination item
        width (int): Preferred line width
        color (QColor): color
        label_color (QColor): color
        label_parts (tuple): tuple of ObjectItem and ArcItem instances lists
    """
    def __init__(self, graph_view_form, object_id_list, relationship_class_id, src_item, dst_item,
                 width, color, label_color=QColor(), label_parts=()):
        """Init class."""
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id_list = object_id_list
        self.relationship_class_id = relationship_class_id
        self.src_item = src_item
        self.dst_item = dst_item
        self.width = width
        self.label_item = ArcLabelItem(label_color, *label_parts)
        self.is_src_hovered = False
        self.is_dst_hovered = False
        self.is_template = False
        self.template_id = None
        src_x = src_item.x()
        src_y = src_item.y()
        dst_x = dst_item.x()
        dst_y = dst_item.y()
        self.setLine(src_x, src_y, dst_x, dst_y)
        self.normal_pen = QPen()
        self.normal_pen.setWidth(self.width)
        self.normal_pen.setColor(color)
        self.normal_pen.setStyle(Qt.SolidLine)
        self.normal_pen.setCapStyle(Qt.RoundCap)
        self.selected_pen = QPen(self.normal_pen)
        self.selected_pen.setColor(graph_view_form.palette().highlight().color())
        self.setPen(self.normal_pen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setZValue(-2)
        self.shape_item = QGraphicsLineItem()
        self.shape_item.setLine(src_x, src_y, dst_x, dst_y)
        shape_pen = QPen()
        shape_pen.setWidth(3 * self.width)
        self.shape_item.setPen(shape_pen)
        self.shape_item.hide()
        src_item.add_outgoing_arc_item(self)
        dst_item.add_incoming_arc_item(self)

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            self.setPen(self.selected_pen)
            option.state &= ~QStyle.State_Selected
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        """Add label item to same scene if added as top level item."""
        if change == QGraphicsItem.ItemSceneChange and value and self.topLevelItem() == self:
            scene = value
            value.addItem(self.label_item)
            self.label_item.hide()
            self.label_item.setZValue(0)
        return super().itemChange(change, value)

    def make_template(self):
        """Make this arc part of a template for a relationship."""
        self.is_template = True
        self.normal_pen.setStyle(Qt.DotLine)
        self.selected_pen.setStyle(Qt.DotLine)

    def remove_template(self):
        """Make this arc no longer part of a template for a relationship."""
        self.is_template = False
        self.normal_pen.setStyle(Qt.SolidLine)
        self.selected_pen.setStyle(Qt.SolidLine)

    def shape(self):
        """Shape is a the shape of a slightly thicker line."""
        return self.shape_item.shape()

    def move_src_by(self, pos_diff):
        """Move source point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP1(line.p1() + pos_diff)
        self.setLine(line)
        self.shape_item.setLine(line)

    def move_dst_by(self, pos_diff):
        """Move destination point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)
        self.shape_item.setLine(line)

    def hoverEnterEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(
            event.scenePos().x() - self.label_item.boundingRect().x() + 16,
            event.scenePos().y() - self.label_item.boundingRect().y() + 16)
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverMoveEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(
            event.scenePos().x() - self.label_item.boundingRect().x() + 16,
            event.scenePos().y() - self.label_item.boundingRect().y() + 16)
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverLeaveEvent(self, event):
        """Hide label."""
        self.label_item.hide()


class ObjectLabelItem(QGraphicsRectItem):
    """Object label item to use with GraphViewForm.

    Attributes:
        text (str): text
        font (QFont): font to display the text
        color (QColor): color to paint the label
    """
    def __init__(self, text, font, color):
        super().__init__()
        self.text = text
        self.text_item = CustomTextItem(text, font)
        self.text_item.setParentItem(self)
        self.setRect(self.childrenBoundingRect())
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setZValue(0)


class ArcLabelItem(QGraphicsRectItem):
    """Arc label item to use with GraphViewForm.

    Attributes:
        color (QColor): color to paint the label
        object_items (list): ObjectItem instances
        arc_items (list): ArcItem instances
    """
    def __init__(self, color, object_items=[], arc_items=[]):
        """A QGraphicsRectItem with a relationship to use as arc label"""
        super().__init__()
        for item in object_items + arc_items:
            item.setParentItem(self)
        rect = self.childrenBoundingRect()
        self.setBrush(color)
        self.setPen(Qt.NoPen)
        self.setRect(rect)
        # label.setZValue(-2)


class CustomTextItem(QGraphicsSimpleTextItem):
    """Custom text item to use with GraphViewForm.

    Attributes:
        text (str): text to show
        font (QFont): font to display the text
        brush (QBrus)
        outline_pen (QPen)
    """
    def __init__(self, text, font, brush=QBrush(Qt.black), outline_pen=QPen(Qt.white, 3, Qt.SolidLine)):
        """Init class."""
        super().__init__()
        self.setText(text)
        font.setWeight(QFont.Black)
        self.setFont(font)
        self.setBrush(brush)
        self.setPen(outline_pen)
