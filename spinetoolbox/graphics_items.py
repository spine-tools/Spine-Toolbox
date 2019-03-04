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
from PySide2.QtCore import Qt, QPointF, QLineF, QRectF, QTimeLine, QTimer, Slot
from PySide2.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, \
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsRectItem, \
    QGraphicsItemAnimation, QGraphicsPixmapItem, QGraphicsLineItem, QStyle, \
    QGraphicsColorizeEffect, QGraphicsDropShadowEffect
from PySide2.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath, QRadialGradient, \
    QFont, QTextCursor
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from math import atan2, degrees, sin, cos, pi
from spinedatabase_api import SpineDBAPIError


class ProjectItemIcon(QGraphicsRectItem):
    """Base class for Tool and View project item icons drawn in Design View.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Icon width
        h (int): Icon height
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__()
        self._toolbox = toolbox
        self.renderer = QSvgRenderer()
        self.svg_item = QGraphicsSvgItem()
        self.colorizer = QGraphicsColorizeEffect()
        self.setRect(QRectF(x, y, w, h))  # Set ellipse coordinates and size
        self.name_font_size = 8  # point size
        # Make item name graphics item.
        self.name_item = QGraphicsSimpleTextItem(name)
        self.set_name_attributes()  # Set font, size, position, etc.
        # Make pen and brush for the connector button
        # connector_pen = QPen(QColor('black'))  # Used in drawing the item outline
        # connector_pen.setStyle(Qt.DotLine)
        connector_pen = QPen(Qt.NoPen)
        self.connector_brush = QBrush(QColor(255, 255, 255, 0))  # Used in filling the item
        self.connector_hover_brush = QBrush(QColor(50, 0, 50, 128))
        # Make connector button graphics item
        self.connector_button = QGraphicsRectItem()
        self.connector_button.setPen(connector_pen)
        self.connector_button.setBrush(self.connector_brush)
        self.connector_button.setRect(self.rect().adjusted(2.5*w/7, 2.5*h/7, -2.5*w/7, -2.5*h/7))
        self.connector_button.setAcceptHoverEvents(True)

    def setup(self, pen, brush, svg, svg_color):
        """Setup item's attributes according to project item type.
        Intended to be called in the constructor's of classes that inherit from ItemImage class.

        Args:
            pen (QPen): Used in drawing the background rectangle outline
            brush (QBrush): Used in filling the background rectangle
            svg (str): Path to SVG icon file
            svg_color (QColor): Color of SVG icon
        """
        self.setPen(pen)  # Qt.NoPen
        self.setBrush(brush)
        self.colorizer.setColor(svg_color)
        # Load SVG
        loading_ok = self.renderer.load(svg)
        if not loading_ok:
            self._toolbox.msg_error.emit("Loading SVG icon from resource:{0} failed".format(svg))
            return
        size = self.renderer.defaultSize()
        # logging.debug("Icon default size:{0}".format(size))
        self.svg_item.setSharedRenderer(self.renderer)
        self.svg_item.setElementId("")  # guess empty string loads the whole file
        dim_max = max(size.width(), size.height())
        # logging.debug("p_max:{0}".format(p_max))
        rect_w = self.rect().width() # Parent rect width
        margin = 5
        self.svg_item.setScale((rect_w - margin)/dim_max)
        x_offset = (rect_w - self.svg_item.sceneBoundingRect().width()) / 2
        y_offset = (rect_w - self.svg_item.sceneBoundingRect().height()) / 2
        self.svg_item.setPos(self.rect().x() + x_offset, self.rect().y() + y_offset)
        scaled_img_rect = self.svg_item.sceneBoundingRect()
        # logging.debug("scaled rect:{0}".format(scaled_img_rect))
        self.svg_item.setGraphicsEffect(self.colorizer)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

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
        font.setPointSize(self.name_font_size)
        font.setBold(True)
        self.name_item.setFont(font)
        # Set name item position (centered on top of the master icon)
        name_width = self.name_item.boundingRect().width()
        self.name_item.setPos(self.rect().x() + self.rect().width()/2 - name_width/2, self.rect().y() - 20)

    def conn_button(self):
        """Returns items connector button (QWidget)."""
        return self.connector_button

    def hoverEnterEvent(self, event):
        """Set a darker shade to icon when mouse enters icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        self.setGraphicsEffect(shadow_effect)
        event.accept()

    def hoverLeaveEvent(self, event):
        """Restore original brush when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.setGraphicsEffect(None)
        event.accept()

    def mousePressEvent(self, event):
        """Update UI to show details of this item. Prevents dragging
        multiple items with a mouse (also with the Ctrl-button pressed).

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self.show_item_info()

    def mouseMoveEvent(self, event):
        """Move icon while the mouse button is pressed.
        Update links that are connected to this icon.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseMoveEvent(event)
        links = self._toolbox.connection_model.connected_links(self.name())
        for link in links:
            link.update_geometry()

    def mouseReleaseEvent(self, event):
        """Mouse button is released.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseReleaseEvent(event)

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
        self.connector_button.setBrush(self.connector_hover_brush)

    def connector_hover_leave_event(self, event):
        """Restore original brush when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.connector_button.setBrush(self.connector_brush)

    def contextMenuEvent(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_item_image_context_menu(event.screenPos(), self.name())

    def keyPressEvent(self, event):
        """Remove item when pressing delete if it is selected.

        Args:
            event (QKeyEvent): Key event
        """
        if event.key() == Qt.Key_Delete and self.isSelected():
            ind = self._toolbox.project_item_model.find_item(self.name())
            self._toolbox.remove_item(ind, delete_item=self._toolbox._config.getboolean("settings", "delete_data"))
            event.accept()
        else:
            super().keyPressEvent(event)

    def show_item_info(self):
        """Update GUI to show the details of the selected item."""
        ind = self._toolbox.project_item_model.find_item(self.name())
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)

    def draw_link(self):
        """Start or stop drawing a link from or to the center point of the connector button."""
        rect = self.conn_button().sceneBoundingRect()
        self._toolbox.ui.graphicsView.draw_links(rect, self.name())


class DataConnectionIcon(ProjectItemIcon):
    """Data Connection icon for the Design View.

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
        self.pen = QPen(Qt.NoPen)  # QPen for the background rectangle
        self.brush = QBrush(QColor("#e6e6ff"))  # QBrush for the background rectangle
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/file-alt.svg", QColor(0, 0, 255, 160))
        self.setAcceptDrops(True)
        # Overridden events in order to avoid subclassing QGraphicsRectItem for a custom connector_button
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        self.connector_button.mouseDoubleClickEvent = lambda e: e.accept()
        # Group the drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        self.connector_button.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)
        self.drag_over = False

    def dragEnterEvent(self, event):
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
        QTimer.singleShot(100, self.select_on_drag_over)

    def dragLeaveEvent(self, event):
        """Drag and drop action leaves.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        event.accept()
        self.drag_over = False

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit files_dropped_on_dc signal from scene,
        with this instance, and a list of files for each dropped url."""
        self.scene().files_dropped_on_dc.emit(self, [url.toLocalFile() for url in event.mimeData().urls()])

    def select_on_drag_over(self):
        """Called when the timer started in drag_enter_event is elapsed.
        Select this item if the drag action is still over it.
        """
        if not self.drag_over:
            return
        self.drag_over = False
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self.setSelected(True)
        self.show_item_info()


class ToolIcon(ProjectItemIcon):
    """Tool image with a rectangular background, an SVG icon, a name label, and a connector button.

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
        self.pen = QPen(Qt.NoPen)  # Background rectangle pen
        self.brush = QBrush(QColor("#ffe6e6"))  # Background rectangle brush
        # Draw icon
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/hammer.svg", QColor("red"))
        self.setAcceptDrops(False)
        # Override connector button events
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        self.connector_button.mouseDoubleClickEvent = lambda e: e.accept()
        # Group drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        # NOTE: setting the parent item moves the items as one!!
        self.name_item.setParentItem(self)
        self.connector_button.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)  # Adds also child items automatically
        # animation stuff
        self.wheel = QGraphicsPixmapItem()
        pixmap = QPixmap(":/icons/wheel.png").scaled(0.5*self.rect().width(), 0.5*self.rect().height())
        self.wheel.setPixmap(pixmap)
        self.wheel_w = pixmap.width()
        self.wheel_h = pixmap.height()
        self.wheel.setPos(self.sceneBoundingRect().center())
        self.wheel.moveBy(-0.5*self.wheel_w, -0.5*self.wheel_h)
        self.wheel_center = self.wheel.sceneBoundingRect().center()
        self.wheel.setParentItem(self)
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


class DataStoreIcon(ProjectItemIcon):
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
        self.pen = QPen(Qt.NoPen)  # Pen for the bg rect outline
        self.brush = QBrush(QColor("#f9e6ff"))  # Brush for filling the bg rect
        # Setup icons and attributes
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/database.svg", QColor("#cc33ff"))
        self.setAcceptDrops(False)
        # Override connector button events
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        self.connector_button.mouseDoubleClickEvent = lambda e: e.accept()
        # Group drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        self.connector_button.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)


class ViewIcon(ProjectItemIcon):
    """View icon for the Design View

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of background rectangle
        h (int): Height of background rectangle
        name (str): Item name
    """
    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(Qt.NoPen)  # Pen for the bg rect outline
        self.brush = QBrush(QColor("#ebfaeb"))  # Brush for filling the bg rect
        # Setup icons and attributes
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/binoculars.svg", QColor("#33cc33"))
        self.setAcceptDrops(False)
        # Override connector button events
        self.connector_button.mousePressEvent = self.connector_mouse_press_event
        self.connector_button.hoverEnterEvent = self.connector_hover_enter_event
        self.connector_button.hoverLeaveEvent = self.connector_hover_leave_event
        self.connector_button.mouseDoubleClickEvent = lambda e: e.accept()
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        self.connector_button.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)


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
                        "to <b>{1}</b>'s input</html>".format(self.src_icon.name(), self.dst_icon.name()))
        # self.selected_brush = QBrush(QColor(255, 0, 255, 204))
        # self.normal_brush = QBrush(QColor(255, 255, 0, 204))
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.selected_pen = QPen(Qt.black, 0.5, Qt.DashLine)
        self.normal_pen = QPen(Qt.black, 0.5)
        self.model_index = None
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setCursor(Qt.PointingHandCursor)
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
        elif self.src_icon.conn_button().isUnderMouse() or self.dst_icon.conn_button().isUnderMouse():
            # Ignore event so it gets propagated to the connector button.
            e.ignore()

    def mouseDoubleClickEvent(self, e):
        """Accept event to prevent unwanted feedback icons to be created when propagating this event
        to connector buttons underneath.
        """
        if self.src_icon.conn_button().isUnderMouse() or self.dst_icon.conn_button().isUnderMouse():
            e.accept()

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
    def __init__(self):
        """Initializes instance."""
        super().__init__()
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
        object_class_name (str): object class name (for finding the pixmap)
        x (float): x-coordinate of central point
        y (float): y-coordinate of central point
        extent (int): preferred extent
        label_font (QFont): label font
        label_color (QColor): label bg color
        label_position (str)
    """
    def __init__(self, graph_view_form, object_id, object_name, object_class_id, object_class_name,
                 x, y, extent, label_font=QFont(), label_color=Qt.transparent, label_position="under_icon"):
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id = object_id
        self.object_name = object_name
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._extent = extent
        self._label_color = label_color
        self._label_position = label_position
        self.label_item = ObjectLabelItem(self, object_name, extent, label_font, label_color)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.is_template = False
        self.template_id_dim = {}  # NOTE: for a template item this should have one and only one entry
        self.question_item = None  # In case this becomes a template
        self._original_pos = None
        self._merge_target = None
        self._merge = False
        self._bounce = False
        self._views_cursor = {}
        self.shade = QGraphicsRectItem()
        self._selected_color = graph_view_form.palette().highlight()
        pixmap = self._graph_view_form.object_icon(object_class_name).pixmap(extent)
        self.setPixmap(pixmap.scaled(extent, extent))
        self.setPos(x, y)
        self.setOffset(-0.5 * extent, -0.5 * extent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.shade.setRect(self.boundingRect())
        self.shade.setBrush(self._selected_color)
        self.shade.setPen(Qt.NoPen)
        self.shade.setParentItem(self)
        self.shade.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
        self.shade.hide()
        self.setZValue(0)
        self.label_item.setZValue(1)

    def shape(self):
        """Make the entire bounding rect to be the shape."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            if self.label_item.hasFocus():
                self.shade.hide()
                self.label_item.set_bg_color(self._label_color)
            else:
                self.shade.show()
                self.label_item.set_bg_color(self._selected_color)
            option.state &= ~QStyle.State_Selected
        else:
            self.shade.hide()
            self.label_item.set_bg_color(self._label_color)
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
        """Put label item in position and align its text."""
        x = self.x() - self.label_item.boundingRect().width() / 2
        y = self.y() + self.offset().y() + (self.boundingRect().height() - self.label_item.boundingRect().height()) / 2
        alignment = Qt.AlignCenter
        if self._label_position == "under_icon":
            y += self._extent / 2 + self.label_item.boundingRect().height() / 2
        elif self._label_position == "over_icon":
            y -= self._extent / 2 + self.label_item.boundingRect().height() / 2
        elif self._label_position == "beside_icon":
            x += self._extent / 2 + self.label_item.boundingRect().width() / 2
            alignment = Qt.AlignLeft
        self.label_item.setPos(x, y)
        option = self.label_item.document().defaultTextOption()
        option.setAlignment(alignment)
        self.label_item.document().setDefaultTextOption(option)

    def make_template(self):
        """Make this object par of a template for a relationship."""
        self.is_template = True
        font = QFont("", 0.75 * self._extent)
        brush = QBrush(Qt.white)
        outline_pen = QPen(Qt.black, 8, Qt.SolidLine)
        self.question_item = OutlinedTextItem("?", font, brush=brush, outline_pen=outline_pen)
        self.question_item.setParentItem(self)
        rect = self.boundingRect()
        question_rect = self.question_item.boundingRect()
        x = rect.center().x() - question_rect.width() / 2
        y = rect.center().y() - question_rect.height() / 2
        self.question_item.setPos(x, y)
        if self.template_id_dim:
            self.setToolTip("""
                <html>
                This item is part of a <i>template</i> for a relationship
                and needs to be associated with an object.
                Please do one of the following:
                <ul>
                <li>Give this item a name to create a new <b>{0}</b> object (select it and press F2).</li>
                <li>Drag-and-drop this item onto an existing <b>{0}</b> object (or viceversa)</li>
                </ul>
                </html>""".format(self.object_class_name))
        else:
            self.setToolTip("""
                <html>
                This item is a <i>template</i> for a <b>{0}</b>.
                Please give it a name to create a new <b>{0}</b> object (select it and press F2).
                </html>""".format(self.object_class_name))

    def remove_template(self):
        """Make this arc no longer a template."""
        self.is_template = False
        self.scene().removeItem(self.question_item)
        self.setToolTip("")

    def edit_name(self):
        """Start editing object name."""
        self.setSelected(True)
        self.label_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.label_item.setFocus()
        cursor = QTextCursor(self.label_item._cursor)
        cursor.select(QTextCursor.Document)
        self.label_item.setTextCursor(cursor)

    def finish_name_editing(self):
        """Called by the label item when editing finishes."""
        self.label_item.setTextInteractionFlags(Qt.NoTextInteraction)
        name = self.label_item.toPlainText()
        if self.is_template:
            try:
                kwargs = dict(class_id=self.object_class_id, name=name)
                object_ = self._graph_view_form.db_map.add_objects(kwargs)
                self._graph_view_form.add_objects(object_)
                self.object_name = name
                self.object_id = object_.first().id
                if self.template_id_dim:
                    self.add_into_relationship()
                self.remove_template()
            except SpineDBAPIError as e:
                self.label_item.setPlainText(self.object_name)
                self._graph_view_form.msg_error.emit(e.msg)
        else:
            try:
                kwargs = dict(id=self.object_id, name=name)
                object_ = self._graph_view_form.db_map.update_objects(kwargs)
                self._graph_view_form.update_objects(object_)
                self.object_name = name
            except SpineDBAPIError as e:
                self.label_item.setPlainText(self.object_name)
                self._graph_view_form.msg_error.emit(e.msg)

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def keyPressEvent(self, event):
        """Trigger editing name."""
        if event.key() == Qt.Key_F2:
            self.edit_name()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Triger editing name."""
        self.edit_name()
        event.accept()

    def mousePressEvent(self, event):
        """Save original position."""
        super().mousePressEvent(event)
        self._original_pos = self.pos()

    def mouseMoveEvent(self, event):
        """Call move related items and check for a merge target."""
        super().mouseMoveEvent(event)
        # Move selected items together
        object_items = [x for x in self.scene().selectedItems() if isinstance(x, ObjectItem)]
        for item in object_items:
            item.move_related_items_by(event.scenePos() - event.lastScenePos())
        self.check_for_merge_target(event.scenePos())
        # Depending on the value of merge target and bounce, set drop indicator cursor
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

    def mouseReleaseEvent(self, event):
        """Merge, bounce, or just do nothing."""
        super().mouseReleaseEvent(event)
        if self._merge_target:
            if not self.merge_item(self._merge_target):
                self._bounce = True
            self._merge_target = None
        if self._bounce:
            self.move_related_items_by(self._original_pos - self.pos())
            self.setPos(self._original_pos)
            self._original_pos = None

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
            if item.is_template != self.is_template and item.object_class_name == self.object_class_name:
                self._merge_target = item
            else:
                self._bounce = True
            break

    def merge_item(self, other):
        """Merge this item with other.
        Try and create a relationship if needed."""
        if not other:
            return False
        if self.is_template == other.is_template:
            return False
        if self.object_class_id != other.object_class_id:
            return False
        if not self.is_template:
            # Do the merging on the template, by convention
            return other.merge_item(self)
        # Set the object_name attribute assuming everything will go fine.
        template_object_name = self.object_name
        self.object_name = other.object_name
        if not self.add_into_relationship():
            # Restablish object name, since something went wrong (not that it matters too much, though)
            self.object_name = template_object_name
            return False
        # Add template id-dimension to other
        other.template_id_dim.update(self.template_id_dim)
        self.move_related_items_by(other.pos() - self.pos())
        for arc_item in self.outgoing_arc_items:
            arc_item.src_item = other
        for arc_item in self.incoming_arc_items:
            arc_item.dst_item = other
        other.incoming_arc_items.extend(self.incoming_arc_items)
        other.outgoing_arc_items.extend(self.outgoing_arc_items)
        self.scene().removeItem(self.label_item)
        self.scene().removeItem(self)
        return True

    def add_into_relationship(self):
        """Try and add a this item into a relationship between the buddies."""
        template_id = list(self.template_id_dim)[0]
        items = self.scene().items()
        template_buddies = [x for x in items if isinstance(x, ObjectItem) and template_id in x.template_id_dim]
        if [x for x in template_buddies if x.is_template and x != self]:
            # There are more templates left, so everything is fine
            return True
        # Here, the only template left in the relationship is this item
        return self._graph_view_form.add_relationship(template_id, template_buddies)

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
        if not self.isSelected() and not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        self._graph_view_form.show_object_item_context_menu(e, self)

    def set_all_visible(self, on):
        """Set visible status for this item and all related ones."""
        self.label_item.setVisible(on)
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            item.setVisible(on)
        self.setVisible(on)

    def wipe_out(self):
        """Remove this item and all related from the scene."""
        scene = self.scene()
        scene.removeItem(self.label_item)
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            if not item.scene():
                # Already removed
                continue
            scene.removeItem(item)
        scene.removeItem(self)


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm.

    Attributes:
        graph_view_form (GraphViewForm): 'owner'
        object_id_list (str): object id comma separated list (for filtering parameters)
        relationship_class_id (int): relationship class id (for filtering parameters)
        object_class_name_list (str): object class name comma separated list (for finding the pixmap)
        src_item (ObjectItem): source item
        dst_item (ObjectItem): destination item
        width (int): Preferred line width
        arc_color (QColor): arc color
        token_color (QColor): bg color for the token
        label_color (QColor): color
        label_parts (tuple): tuple of ObjectItem and ArcItem instances lists
    """
    def __init__(self, graph_view_form, object_id_list, relationship_class_id, object_class_name_list,
                 src_item, dst_item, width, arc_color, token_color=QColor(), label_color=QColor(), label_parts=()):
        """Init class."""
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id_list = object_id_list
        self.relationship_class_id = relationship_class_id
        self.object_class_name_list = object_class_name_list
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
        self.normal_pen.setColor(arc_color)
        self.normal_pen.setStyle(Qt.SolidLine)
        self.normal_pen.setCapStyle(Qt.RoundCap)
        self.selected_pen = QPen(self.normal_pen)
        self.selected_pen.setColor(graph_view_form.palette().highlight().color())
        self.setPen(self.normal_pen)
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
        self.setAcceptHoverEvents(True)
        viewport = self._graph_view_form.ui.graphicsView.viewport()
        self.viewport_cursor = viewport.cursor()
        # Token item
        self.token_item = QGraphicsPixmapItem()
        if object_class_name_list:
            extent = 3 * width
            join_object_class_name_list = ",".join(object_class_name_list)
            pixmap = self._graph_view_form.relationship_icon(join_object_class_name_list).pixmap(extent)
            self.token_item.setPixmap(pixmap.scaled(extent, extent))
            self.token_item.setOffset(-0.5 * extent, -0.5 * extent)
            diameter = extent / sin(pi / 4)
            delta = (diameter - extent) / 2
            rectf = self.token_item.boundingRect().adjusted(-delta, -delta, delta, delta)
            ellipse_item = QGraphicsEllipseItem(rectf)
            ellipse_item.setParentItem(self.token_item)
            ellipse_item.setPen(Qt.NoPen)
            ellipse_item.setBrush(token_color)
            ellipse_item.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
            # Override hover events
            self.token_item.hoverEnterEvent = self.token_hover_enter_event
            self.token_item.hoverMoveEvent = self.token_hover_move_event
            self.token_item.hoverLeaveEvent = self.token_hover_leave_event
            self.token_item.shape = ellipse_item.shape
            self.token_item.setAcceptHoverEvents(True)

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            self.setPen(self.selected_pen)
            option.state &= ~QStyle.State_Selected
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        """Add label and pixmap item to same scene if added as top level item."""
        if change == QGraphicsItem.ItemSceneChange and value and self.topLevelItem() == self:
            scene = value
            value.addItem(self.label_item)
            value.addItem(self.token_item)
            self.label_item.hide()
            self.label_item.setZValue(2)  # Arc label over everything
            self.place_token_item()
            self.token_item.setZValue(-1)  # Arc pixmap only above arc
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
        self.place_token_item()

    def move_dst_by(self, pos_diff):
        """Move destination point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)
        self.shape_item.setLine(line)
        self.place_token_item()

    def place_token_item(self):
        """Put pixmap item in position."""
        middle = (self.dst_item.pos() + self.src_item.pos()) / 2
        self.token_item.setPos(middle)

    def token_hover_enter_event(self, event):
        """Set viewport's cursor to arrow; show label if src and dst are not hovered."""
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # self.viewport_cursor = viewport.cursor()
        # viewport.setCursor(Qt.ArrowCursor)
        self.label_item.setPos(
            event.scenePos().x() - self.label_item.boundingRect().x() + 16,
            event.scenePos().y() - self.label_item.boundingRect().y() + 16)
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def token_hover_move_event(self, event):
        """Show label if src and dst are not hovered."""
        self.label_item.setPos(
            event.scenePos().x() - self.label_item.boundingRect().x() + 16,
            event.scenePos().y() - self.label_item.boundingRect().y() + 16)
        if self.is_src_hovered or self.is_dst_hovered:
            return
        self.label_item.show()

    def token_hover_leave_event(self, event):
        """Restore viewport's cursor and hide label."""
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # viewport.setCursor(self.viewport_cursor)
        self.label_item.hide()

    def hoverEnterEvent(self, event):
        """Set viewport's cursor to arrow, to signify that this item is not draggable."""
        pass
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # self.viewport_cursor = viewport.cursor()
        # viewport.setCursor(Qt.ArrowCursor)

    def hoverLeaveEvent(self, event):
        """Restore viewport's cursor."""
        pass
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # viewport.setCursor(self.viewport_cursor)


class ObjectLabelItem(QGraphicsTextItem):
    """Object label item to use with GraphViewForm.

    Attributes:
        object_item (ObjectItem): the ObjectItem instance
        text (str): text
        width (int): maximum width
        font (QFont): font to display the text
        bg_color (QColor): color to paint the label
    """
    def __init__(self, object_item, text, width, font, bg_color):
        """Init class."""
        super().__init__()
        self.object_item = object_item
        self._text = text
        self._width = width
        self._font = font
        self.bg = QGraphicsRectItem()
        self.setFont(font)
        self.setPlainText(text)
        self.setTextWidth(width)
        self.bg.setParentItem(self)
        self.set_bg_color(bg_color)
        self.bg.setPen(Qt.NoPen)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setAcceptHoverEvents(False)
        self._cursor = self.textCursor()

    def set_bg_color(self, bg_color):
        """Set background color."""
        self.bg.setBrush(QBrush(bg_color))

    def setTextWidth(self, width):
        super().setTextWidth(width)
        self.bg.setRect(self.boundingRect())

    def keyPressEvent(self, event):
        """Give up focus when the user presses Enter or Return.
        In the meantime, adapt item geometry so text is always centered.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
        else:
            super().keyPressEvent(event)
        self.bg.setRect(self.boundingRect())

    def focusOutEvent(self, event):
        """Call method to finish name editing in object item."""
        super().focusOutEvent(event)
        self.object_item.finish_name_editing()
        self.setTextCursor(self._cursor)


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
        for item in object_items:
            item._label_position = 'beside_icon'
            item.label_item.setTextWidth(-1)
        for item in object_items + arc_items:
            item.setParentItem(self)
        rect = self.childrenBoundingRect()
        self.setBrush(color)
        self.setPen(Qt.NoPen)
        self.setRect(rect)


class OutlinedTextItem(QGraphicsSimpleTextItem):
    """Outlined text item to use with GraphViewForm.

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


class CustomTextItem(QGraphicsTextItem):
    """Custom text item to use with GraphViewForm.

    Attributes:
        html (str): text to show
        font (QFont): font to display the text
    """
    def __init__(self, html, font):
        super().__init__()
        self.setHtml(html)
        # font.setWeight(QFont.Black)
        self.setFont(font)
        self.adjustSize()
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # self.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
