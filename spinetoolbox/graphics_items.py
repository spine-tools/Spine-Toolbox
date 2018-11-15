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
    QGraphicsItemAnimation, QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsTextItem, QStyle
from PySide2.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath, QRadialGradient, QFont
from math import atan2, degrees, sin, cos, pi


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
            name = self.name()
            ind = self._toolbox.project_item_model.find_item(name)
            self._toolbox.remove_item(ind, delete_item=True)

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
        pixmap (QPixmap): pixmap to use
        x (float): x-coordinate of central point
        y (float): y-coordinate of central point
    """
    def __init__(self, pixmap, x, y):
        super().__init__(pixmap)
        self.setPos(x - 0.5 * self.pixmap().width(), y - 0.5 * self.pixmap().height())
        self.label_item = None
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

    def shape(self):
        """Return shape."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def set_label_item(self, item):
        self.label_item = item
        self.label_item.setPos(self.x() + self.pixmap().width(), self.y())

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def mouseMoveEvent(self, event):
        """Reset position of text, incoming and outgoing arcs."""
        super().mouseMoveEvent(event)
        self.label_item.setPos(self.x() + self.pixmap().width(), self.y())
        for item in self.outgoing_arc_items:
            item.set_source_point(self.x() + 0.5 * self.pixmap().width(), self.y() + 0.5 * self.pixmap().height())
        for item in self.incoming_arc_items:
            item.set_destination_point(self.x() + 0.5 * self.pixmap().width(), self.y() + 0.5 * self.pixmap().height())

    def hoverEnterEvent(self, event):
        """Show text on hover."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = True
        for item in self.outgoing_arc_items:
            item.is_src_hovered = True

    def hoverLeaveEvent(self, event):
        """Hide text on hover."""
        for item in self.incoming_arc_items:
            item.is_dst_hovered = False
        for item in self.outgoing_arc_items:
            item.is_src_hovered = False


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm.

    Attributes:
        x1, y1 (float): source position
        x2, y2 (float): destination position
        width (int): Preferred line width
    """
    def __init__(self, x1, y1, x2, y2, width):
        """Init class."""
        super().__init__(x1, y1, x2, y2)
        self.label_item = None
        self.width = width
        self.is_src_hovered = False
        self.is_dst_hovered = False
        pen = QPen(QColor(64, 64, 64))
        pen.setWidth(self.width)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)
        self.setZValue(-2)
        self.shape_item = QGraphicsLineItem(x1, y1, x2, y2)
        shape_pen = QPen()
        shape_pen.setWidth(3 * self.width)
        self.shape_item.setPen(shape_pen)
        self.shape_item.hide()

    def shape(self):
        return self.shape_item.shape()

    def set_label_item(self, item):
        self.label_item = item
        self.label_item.hide()

    def set_source_point(self, x, y):
        """Reset the source point. Used when moving ObjectItems around."""
        x1 = x
        y1 = y
        x2 = self.line().x2()
        y2 = self.line().y2()
        self.setLine(x1, y1, x2, y2)
        self.shape_item.setLine(x1, y1, x2, y2)

    def set_destination_point(self, x, y):
        """Reset the destination point. Used when moving ObjectItems around."""
        x1 = self.line().x1()
        y1 = self.line().y1()
        x2 = x
        y2 = y
        self.setLine(x1, y1, x2, y2)
        self.shape_item.setLine(x1, y1, x2, y2)

    def hoverEnterEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(event.pos().x(), event.pos().y())
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverMoveEvent(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(event.pos().x(), event.pos().y())
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def hoverLeaveEvent(self, event):
        """Hide label."""
        self.label_item.hide()


class ObjectLabelItem(QGraphicsRectItem):
    """Label item for objects to use with GraphViewForm.

    Attributes:
        object_name (str): object name
        font (QFont): font to display the text
        color (QColor): color to paint the label
    """
    def __init__(self, object_name, font, color):
        super().__init__()
        self.title_item = CustomTextItem(object_name, font)
        self.title_item.setParentItem(self)
        self.setRect(self.childrenBoundingRect())
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setZValue(0)


class ArcLabelItem(QGraphicsRectItem):
    """Label item for arcs to use with GraphViewForm.

    Attributes:
        relationship_class_name (str): relationship class name
        object_pixmaps (list): object pixmaps
        object_names (list): object names
        font (QFont): font to display the text
        color (QColor): color to paint the label
    """
    def __init__(self, relationship_class_name, object_pixmaps, object_names, font, color):
        super().__init__()
        self.title_item = CustomTextItem(relationship_class_name, font)
        self.title_item.setParentItem(self)
        self.object_items = []
        y_offset = self.title_item.boundingRect().height()
        for k in range(len(object_pixmaps)):
            object_pixmap = object_pixmaps[k]
            object_name = object_names[k]
            width = object_pixmap.width()
            height = object_pixmap.height()
            object_item = ObjectItem(object_pixmap, .5 * width, y_offset + (k + .5) * height)
            object_item.setParentItem(self)
            label_item = ObjectLabelItem(object_name, font, Qt.transparent)
            label_item.setParentItem(self)
            object_item.set_label_item(label_item)
            self.object_items.append(object_item)
        self.setRect(self.childrenBoundingRect())
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setZValue(1)


class CustomTextItem(QGraphicsTextItem):
    """Custom text item to use with GraphViewForm.

    Attributes:
        text (str): text to show
        font (QFont): font to display the text
    """
    def __init__(self, text, font):
        """Init class."""
        super().__init__()
        self.setHtml(text)
        font.setWeight(QFont.Black)
        self.setFont(font)
        # outline_pen = QPen(Qt.white, 2, Qt.SolidLine)
        # self.setPen(outline_pen)
