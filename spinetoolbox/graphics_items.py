######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

import os
from PySide2.QtCore import Qt, QPointF, QLineF, QRectF, QTimeLine, QTimer
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QGraphicsSimpleTextItem,
    QGraphicsRectItem,
    QGraphicsItemAnimation,
    QGraphicsPixmapItem,
    QGraphicsLineItem,
    QStyle,
    QGraphicsColorizeEffect,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide2.QtGui import QColor, QPen, QBrush, QPainterPath, QFont, QTextCursor, QTransform, QFontMetrics
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from math import atan2, degrees, sin, cos, pi
from spinedb_api import SpineDBAPIError, SpineIntegrityError


class ConnectorButton(QGraphicsRectItem):
    """Connector button graphics item. Used for Link drawing between project items.

    Attributes:
        parent (QGraphicsItem): Project item bg rectangle
        toolbox (ToolBoxUI): QMainWindow instance
        position (str): Either "top", "left", "bottom", or "right"
    """

    def __init__(self, parent, toolbox, position="left"):
        """Class constructor."""
        super().__init__()
        self._parent = parent
        self._toolbox = toolbox
        self.position = position
        self.setPen(QPen(Qt.black, 0.5, Qt.SolidLine))
        # self.setPen(QPen(Qt.NoPen))
        # Regular and hover brushes
        self.brush = QBrush(QColor(255, 255, 255))  # Used in filling the item
        self.hover_brush = QBrush(QColor(50, 0, 50, 128))  # Used in filling the item while hovering
        self.setBrush(self.brush)
        extent = 12
        rect = QRectF(0, 0, extent, extent)
        parent_rect = parent.rect()
        if position == "top":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.top() + extent / 2))
        elif position == "left":
            rect.moveCenter(QPointF(parent_rect.left() + extent / 2 + 1, parent_rect.center().y()))
        elif position == "bottom":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.bottom() - extent / 2 - 1))
        elif position == "right":
            rect.moveCenter(QPointF(parent_rect.right() - extent / 2 - 1, parent_rect.center().y()))
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def parent_name(self):
        """Returns project item name owning this connector button."""
        return self._parent.name()

    def mousePressEvent(self, event):
        """Connector button mouse press event. Starts drawing a link.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if not event.button() == Qt.LeftButton:
            event.accept()
        else:
            self._parent.show_item_info()
            # Start drawing a link
            self._toolbox.ui.graphicsView.draw_links(self)

    def mouseDoubleClickEvent(self, event):
        """Connector button mouse double click event. Makes sure the LinkDrawer is hidden.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        event.accept()

    def hoverEnterEvent(self, event):
        """Sets a darker shade to connector button when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.setBrush(self.hover_brush)

    def hoverLeaveEvent(self, event):
        """Restore original brush when mouse leaves connector button boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.setBrush(self.brush)


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
        self.name_font_size = 10  # point size
        # Make item name graphics item.
        self.name_item = QGraphicsSimpleTextItem(name)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        shadow_effect.setEnabled(False)
        self.setGraphicsEffect(shadow_effect)
        self.set_name_attributes()  # Set font, size, position, etc.
        # Make connector buttons
        self.connectors = dict(
            bottom=ConnectorButton(self, toolbox, position="bottom"),
            left=ConnectorButton(self, toolbox, position="left"),
            right=ConnectorButton(self, toolbox, position="right"),
        )

    def setup(self, pen, brush, svg, svg_color):
        """Setup item's attributes according to project item type.
        Intended to be called in the constructor's of classes that inherit from ItemImage class.

        Args:
            pen (QPen): Used in drawing the background rectangle outline
            brush (QBrush): Used in filling the background rectangle
            svg (str): Path to SVG icon file
            svg_color (QColor): Color of SVG icon
        """
        self.setPen(QPen(Qt.black, 1, Qt.SolidLine))  # Override Qt.NoPen to make an outline for all items
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
        rect_w = self.rect().width()  # Parent rect width
        margin = 24
        self.svg_item.setScale((rect_w - margin) / dim_max)
        x_offset = (rect_w - self.svg_item.sceneBoundingRect().width()) / 2
        y_offset = (rect_w - self.svg_item.sceneBoundingRect().height()) / 2
        self.svg_item.setPos(self.rect().x() + x_offset, self.rect().y() + y_offset)
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
        name_height = self.name_item.boundingRect().height()
        self.name_item.setPos(
            self.rect().x() + self.rect().width() / 2 - name_width / 2, self.rect().y() - name_height - 4
        )

    def conn_button(self, position="left"):
        """Returns items connector button (QWidget)."""
        try:
            connector = self.connectors[position]
        except KeyError:
            connector = self.connectors["left"]
        return connector

    def hoverEnterEvent(self, event):
        """Sets a drop shadow effect to icon when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(True)
        event.accept()

    def hoverLeaveEvent(self, event):
        """Disables the drop shadow when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(False)
        event.accept()

    def mousePressEvent(self, event):
        """Update UI to show details of this item. Prevents dragging
        multiple items with a mouse (also with the Ctrl-button pressed).

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Moves icon(s) while the mouse button is pressed.
        Update links that are connected to selected icons.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseMoveEvent(event)
        selected_icons = set([x for x in self.scene().selectedItems() if isinstance(x, ProjectItemIcon)] + [self])
        links = set(y for x in selected_icons for y in self._toolbox.connection_model.connected_links(x.name()))
        for link in links:
            link.update_geometry()

    def mouseReleaseEvent(self, event):
        """Mouse button is released.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_item_image_context_menu(event.screenPos(), self.name())

    def keyPressEvent(self, event):
        """Handles deleting and rotating the selected
        item when dedicated keys are pressed.

        Args:
            event (QKeyEvent): Key event
        """
        if event.key() == Qt.Key_Delete and self.isSelected():
            ind = self._toolbox.project_item_model.find_item(self.name())
            delete_int = int(self._toolbox.qsettings().value("appSettings/deleteData", defaultValue="0"))
            delete_bool = delete_int != 0
            self._toolbox.remove_item(ind, delete_item=delete_bool)
            event.accept()
        elif event.key() == Qt.Key_R and self.isSelected():
            # TODO:
            # 1. Change name item text direction when rotating
            # 2. Save rotation into project file
            rect = self.mapToScene(self.boundingRect()).boundingRect()
            center = rect.center()
            t = QTransform()
            t.translate(center.x(), center.y())
            t.rotate(90)
            t.translate(-center.x(), -center.y())
            self.setPos(t.map(self.pos()))
            self.setRotation(self.rotation() + 90)
            links = self._toolbox.connection_model.connected_links(self.name())
            for link in links:
                link.update_geometry()
            event.accept()
        else:
            super().keyPressEvent(event)

    def itemChange(self, change, value):
        """
        Destroys the drop shadow effect when the items is removed from a scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
             Whatever super() does with the value parameter
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            self.prepareGeometryChange()
            self.setGraphicsEffect(None)
        return super().itemChange(change, value)

    def show_item_info(self):
        """Update GUI to show the details of the selected item."""
        ind = self._toolbox.project_item_model.find_item(self.name())
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)


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
        # Group the drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        # NOTE: setting the parent item moves the items as one!
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
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
        # Group drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)  # Adds also child items automatically
        # animation stuff
        self.timer = QTimeLine()
        self.timer.setLoopCount(0)  # loop forever
        self.timer.setFrameRange(0, 10)
        # self.timer.setCurveShape(QTimeLine.CosineCurve)
        self.timer.valueForTime = self.value_for_time
        self.tool_animation = QGraphicsItemAnimation()
        self.tool_animation.setItem(self.svg_item)
        self.tool_animation.setTimeLine(self.timer)
        # self.timer.frameChanged.connect(self.test)
        self.delta = 0.25 * self.svg_item.sceneBoundingRect().height()

    def value_for_time(self, msecs):
        rem = (msecs % 1000) / 1000
        return 1.0 - rem

    def start_animation(self):
        """Start the animation that plays when the Tool associated to this GraphicsItem is running.
        """
        self.svg_item.moveBy(0, -self.delta)
        offset = 0.75 * self.svg_item.sceneBoundingRect().height()
        for angle in range(1, 45):
            step = angle / 45.0
            self.tool_animation.setTranslationAt(step, 0, offset)
            self.tool_animation.setRotationAt(step, angle)
            self.tool_animation.setTranslationAt(step, 0, -offset)
            self.tool_animation.setPosAt(step, QPointF(self.svg_item.pos().x(), self.svg_item.pos().y() + offset))
        self.timer.start()

    def stop_animation(self):
        """Stop animation"""
        self.timer.stop()
        self.svg_item.moveBy(0, self.delta)
        self.timer.setCurrentTime(999)


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
        # Group drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
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
        # Group drawn items together by setting the master as the parent of other QGraphicsItems
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
        self.svg_item.setParentItem(self)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)


class Link(QGraphicsPathItem):
    """An item that represents a connection between project items.

    Attributes:
        toolbox (ToolboxUI): main UI class instance
        src_connector (ConnectorButton): Source connector button
        dst_connector (ConnectorButton): Destination connector button
    """

    def __init__(self, toolbox, src_connector, dst_connector):
        """Initializes item."""
        super().__init__()
        self._toolbox = toolbox
        self.src_connector = src_connector  # QGraphicsRectItem
        self.dst_connector = dst_connector
        self.src_icon = src_connector._parent
        self.dst_icon = dst_connector._parent
        self.setZValue(1)
        self.conn_width = 1.25 * self.src_connector.rect().width()
        self.arrow_angle = pi / 4  # In rads
        self.ellipse_angle = 30  # In degrees
        self.feedback_size = 12
        # Path parameters
        self.ellipse_rect = QRectF(0, 0, self.conn_width, self.conn_width)
        self.line_width = self.conn_width / 2
        self.arrow_length = self.line_width
        self.arrow_diag = self.arrow_length / sin(self.arrow_angle)
        arrow_base = 2 * self.arrow_diag * cos(self.arrow_angle)
        self.t1 = (arrow_base - self.line_width) / arrow_base / 2
        self.t2 = 1.0 - self.t1
        # Inner rect of feedback link
        self.inner_rect = QRectF(0, 0, 7.5 * self.feedback_size, 6 * self.feedback_size - self.line_width)
        inner_shift_x = self.arrow_length / 2
        angle = atan2(self.conn_width, self.inner_rect.height())
        inner_shift_y = (self.inner_rect.height() * cos(angle) + self.line_width) / 2
        self.inner_shift = QPointF(inner_shift_x, inner_shift_y)
        self.inner_angle = degrees(atan2(inner_shift_x + self.conn_width / 2, inner_shift_y - self.line_width / 2))
        # Outer rect of feedback link
        self.outer_rect = QRectF(0, 0, 8 * self.feedback_size, 6 * self.feedback_size + self.line_width)
        outer_shift_x = self.arrow_length / 2
        angle = atan2(self.conn_width, self.outer_rect.height())
        outer_shift_y = (self.outer_rect.height() * cos(angle) - self.line_width) / 2
        self.outer_shift = QPointF(outer_shift_x, outer_shift_y)
        self.outer_angle = degrees(atan2(outer_shift_x + self.conn_width / 2, outer_shift_y + self.line_width / 2))
        # Tooltip
        self.setToolTip(
            "<html><p>Connection from <b>{0}</b>'s output "
            "to <b>{1}</b>'s input</html>".format(self.src_icon.name(), self.dst_icon.name())
        )
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.selected_pen = QPen(Qt.black, 1, Qt.DashLine)
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
        elif any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.ignore()

    def mouseDoubleClickEvent(self, e):
        """Accept event to prevent unwanted feedback links to be created when propagating this event
        to connector buttons underneath.
        """
        if any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
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
            arrow_p0 = dst_center
            angle = atan2(-line.dy(), line.dx())
        # Path coordinates. We just need to draw the arrow and the ellipse, lines are drawn automatically
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
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
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2 * self.inner_angle - 360)
        self.ellipse_rect.moveCenter(src_rect.center())
        path.arcTo(self.ellipse_rect, degrees(angle) + self.ellipse_angle, 360 - 2 * self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_connector == self.dst_connector:
            self.outer_rect.moveCenter(dst_center - self.outer_shift)
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2 * self.outer_angle)
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
    """An item that allows one to draw links between slot buttons in QGraphicsView."""

    def __init__(self):
        """Initializes instance."""
        super().__init__()
        self.src = None  # source point
        self.dst = None  # destination point
        self.drawing = False
        self.arrow_angle = pi / 4
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
        self.ellipse_width = conn_width
        self.line_width = self.ellipse_width / 2
        self.arrow_length = self.line_width
        self.arrow_diag = self.arrow_length / sin(self.arrow_angle)
        self.ellipse_rect = QRectF(0, 0, self.ellipse_width, self.ellipse_width)
        self.ellipse_rect.moveCenter(self.src)
        arrow_base = 2 * self.arrow_diag * cos(self.arrow_angle)
        self.t1 = (arrow_base - self.line_width) / arrow_base / 2
        self.t2 = 1.0 - self.t1
        # Inner rect of feedback link
        self.inner_rect = QRectF(0, 0, 7.5 * self.feedback_size, 6 * self.feedback_size - self.line_width)
        inner_shift_x = self.arrow_length / 2
        angle = atan2(self.ellipse_width, self.inner_rect.height())
        inner_shift_y = (self.inner_rect.height() * cos(angle) + self.line_width) / 2
        self.inner_shift = QPointF(inner_shift_x, inner_shift_y)
        self.inner_angle = degrees(atan2(inner_shift_x + self.ellipse_width / 2, inner_shift_y - self.line_width / 2))
        # Outer rect of feedback link
        self.outer_rect = QRectF(0, 0, 8 * self.feedback_size, 6 * self.feedback_size + self.line_width)
        outer_shift_x = self.arrow_length / 2
        angle = atan2(self.ellipse_width, self.outer_rect.height())
        outer_shift_y = (self.outer_rect.height() * cos(angle) - self.line_width) / 2
        self.outer_shift = QPointF(outer_shift_x, outer_shift_y)
        self.outer_angle = degrees(atan2(outer_shift_x + self.ellipse_width / 2, outer_shift_y + self.line_width / 2))
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
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
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
            path.arcTo(self.inner_rect, 270 - self.inner_angle, 2 * self.inner_angle - 360)
        path.arcTo(self.ellipse_rect, (180 / pi) * angle + self.ellipse_angle, 360 - 2 * self.ellipse_angle)
        # Draw outer part of feedback link
        if self.src_rect.contains(self.dst):
            self.outer_rect.moveCenter(self.src - self.outer_shift)
            path.arcTo(self.outer_rect, 270 + self.outer_angle, 360 - 2 * self.outer_angle)
        path.closeSubpath()
        self.setPath(path)


class ObjectItem(QGraphicsPixmapItem):
    """Object item to use with GraphViewForm.

    Attributes:
        graph_view_form (GraphViewForm): 'owner'
        object_name (str): object name
        object_class_id (int): object class id
        object_class_name (str): object class name
        x (float): x-coordinate of central point
        y (float): y-coordinate of central point
        extent (int): preferred extent
        object_id (int): object id (for filtering parameters)
        label_font (QFont): label font
        label_color (QColor): label bg color
    """

    def __init__(
        self,
        graph_view_form,
        object_name,
        object_class_id,
        object_class_name,
        x,
        y,
        extent,
        object_id=0,
        label_color=Qt.transparent,
    ):
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id = object_id
        self.object_name = object_name
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._extent = extent
        self._label_color = label_color
        self.label_item = ObjectLabelItem(self, object_name, extent, label_color)
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
        pixmap = self._graph_view_form.icon_mngr.object_icon(object_class_name).pixmap(extent)
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
            else:
                self.shade.show()
            option.state &= ~QStyle.State_Selected
        else:
            self.shade.hide()
        super().paint(painter, option, widget)

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
            self.setToolTip(
                """
                <html>
                This item is part of a <i>template</i> for a relationship
                and needs to be associated with an object.
                Please do one of the following:
                <ul>
                <li>Give this item a name to create a new <b>{0}</b> object (select it and press F2).</li>
                <li>Drag-and-drop this item onto an existing <b>{0}</b> object (or viceversa)</li>
                </ul>
                </html>""".format(
                    self.object_class_name
                )
            )
        else:
            self.setToolTip(
                """
                <html>
                This item is a <i>template</i> for a <b>{0}</b>.
                Please give it a name to create a new <b>{0}</b> object (select it and press F2).
                </html>""".format(
                    self.object_class_name
                )
            )

    def remove_template(self):
        """Make this arc no longer a template."""
        self.is_template = False
        self.scene().removeItem(self.question_item)
        self.setToolTip("")

    def edit_name(self):
        """Start editing object name."""
        self.setSelected(True)
        self.label_item.set_full_text()
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
                object_, _ = self._graph_view_form.db_map.add_objects(kwargs, strict=True)
                self._graph_view_form.add_objects(object_)
                self.object_name = name
                self.object_id = object_.first().id
                if self.template_id_dim:
                    self.add_into_relationship()
                self.remove_template()
            except (SpineDBAPIError, SpineIntegrityError) as e:
                self._graph_view_form.msg_error.emit(e.msg)
            finally:
                self.label_item.set_text(self.object_name)
        else:
            try:
                kwargs = dict(id=self.object_id, name=name)
                object_, _ = self._graph_view_form.db_map.update_objects(kwargs, strict=True)
                self._graph_view_form.update_objects(object_)
                self.object_name = name
            except (SpineDBAPIError, SpineIntegrityError) as e:
                self._graph_view_form.msg_error.emit(e.msg)
            finally:
                self.label_item.set_text(self.object_name)

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
        for item in self.outgoing_arc_items:
            item.move_src_by(pos_diff)
        for item in self.incoming_arc_items:
            item.move_dst_by(pos_diff)

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
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            item.setVisible(on)
        self.setVisible(on)

    def wipe_out(self):
        """Remove this item and all related from the scene."""
        scene = self.scene()
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
        relationship_class_id (int): relationship class id
        src_item (ObjectItem): source item
        dst_item (ObjectItem): destination item
        width (int): Preferred line width
        arc_color (QColor): arc color
        object_id_list (str): object id comma separated list
        token_extent (int): token preferred extent
        token_color (QColor): token bg color
        token_name_tuple_list (list): token (object class name, object name) tuple list
    """

    def __init__(
        self,
        graph_view_form,
        relationship_class_id,
        src_item,
        dst_item,
        width,
        arc_color,
        object_id_list="",
        token_color=QColor(),
        token_object_extent=0,
        token_object_label_color=QColor(),
        token_object_name_tuple_list=None,
    ):
        """Init class."""
        super().__init__()
        self._graph_view_form = graph_view_form
        self.object_id_list = object_id_list
        self.relationship_class_id = relationship_class_id
        self.src_item = src_item
        self.dst_item = dst_item
        self.width = width
        self.is_template = False
        self.template_id = None
        src_x = src_item.x()
        src_y = src_item.y()
        dst_x = dst_item.x()
        dst_y = dst_item.y()
        self.setLine(src_x, src_y, dst_x, dst_y)
        self.token_item = ArcTokenItem(
            self, token_color, token_object_extent, token_object_label_color, *token_object_name_tuple_list
        )
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
        src_item.add_outgoing_arc_item(self)
        dst_item.add_incoming_arc_item(self)
        self.setAcceptHoverEvents(True)
        viewport = self._graph_view_form.ui.graphicsView.viewport()
        self.viewport_cursor = viewport.cursor()

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            self.setPen(self.selected_pen)
            option.state &= ~QStyle.State_Selected
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

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

    def move_src_by(self, pos_diff):
        """Move source point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP1(line.p1() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def move_dst_by(self, pos_diff):
        """Move destination point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def hoverEnterEvent(self, event):
        """Set viewport's cursor to arrow."""
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # self.viewport_cursor = viewport.cursor()
        # viewport.setCursor(Qt.ArrowCursor)

    def hoverLeaveEvent(self, event):
        """Restore viewport's cursor."""
        # viewport = self._graph_view_form.ui.graphicsView.viewport()
        # viewport.setCursor(self.viewport_cursor)


class ObjectLabelItem(QGraphicsTextItem):
    """Object label item to use with GraphViewForm.

    Attributes:
        object_item (ObjectItem): the ObjectItem instance
        text (str): text
        width (int): maximum width
        bg_color (QColor): color to paint the label
    """

    def __init__(self, object_item, text, width, bg_color):
        """Init class."""
        super().__init__(object_item)
        self.object_item = object_item
        self._width = width
        self._font = QApplication.font()
        self._font.setPointSize(width / 8)
        self.setFont(self._font)
        self.set_text(text)
        self.setTextWidth(self._width)
        self.bg = QGraphicsRectItem()
        self.bg.setRect(self.boundingRect())
        self.bg.setParentItem(self)
        self.set_bg_color(bg_color)
        # self.bg.setPen(Qt.NoPen)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.bg.setRect(self.boundingRect())
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setAcceptHoverEvents(False)
        self._cursor = self.textCursor()
        # Position
        x = -self.boundingRect().width() / 2
        y = -self.boundingRect().height() / 2
        self.setPos(x, y)
        option = self.document().defaultTextOption()
        option.setAlignment(Qt.AlignCenter)
        self.document().setDefaultTextOption(option)

    def set_bg_color(self, bg_color):
        """Set background color."""
        self.bg.setBrush(QBrush(bg_color))

    def set_full_text(self):
        self.setPlainText(self._text)

    def set_text(self, text):
        """Store real text, and then try and fit it as best as possible in the width
        (reduce font point size, elide text...)
        """
        self._text = text
        factor = max(0.75, 0.9 * self._width / QFontMetrics(self._font).width(text))
        if factor < 1:
            scaled_font = QFont(self._font)
            scaled_font.setPointSizeF(scaled_font.pointSize() * factor)
            self.setFont(scaled_font)
        else:
            self.setFont(self._font)
        elided = QFontMetrics(self.font()).elidedText(text, Qt.ElideMiddle, self._width)
        self.setPlainText(elided)

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


class ArcTokenItem(QGraphicsEllipseItem):
    """Arc token item to use with GraphViewForm.

    Attributes:
        arc_item (ArcItem): the ArcItem instance
        color (QColor): color to paint the token
        object_extent (int): Preferred extent
        object_label_color (QColor): Preferred extent
        object_name_tuples (Iterable): one or more (object class name, object name) tuples
    """

    def __init__(self, arc_item, color, object_extent, object_label_color, *object_name_tuples):
        """A QGraphicsRectItem with a relationship to use as arc label"""
        super().__init__(arc_item)
        self.arc_item = arc_item
        x = 0
        for j, name_tuple in enumerate(object_name_tuples):
            object_item = SimpleObjectItem(self, object_extent, object_label_color, *name_tuple)
            if j % 2 == 0:
                y = 0
            else:
                y = -0.875 * 0.75 * object_item.boundingRect().height()
                object_item.setZValue(-1)
            object_item.setPos(x, y)
            x += 0.875 * 0.5 * object_extent
        rectf = self.childrenBoundingRect()
        offset = -rectf.topLeft()
        for item in self.childItems():
            item.setOffset(offset)

        rectf = self.childrenBoundingRect()
        width = rectf.width()
        height = rectf.height()
        if width > height:
            delta = width - height
            rectf.adjust(0, -delta / 2, 0, delta / 2)
        else:
            delta = height - width
            rectf.adjust(-delta / 2, 0, delta / 2, 0)
        self.setRect(rectf)
        self.setPen(Qt.NoPen)
        self.setBrush(color)
        self.update_pos()

    def update_pos(self):
        """Put token item in position."""
        center = self.arc_item.line().center()
        rectf = self.rect()
        rectf.moveCenter(center)
        self.setPos(rectf.topLeft())


class SimpleObjectItem(QGraphicsPixmapItem):
    """Object item to use with GraphViewForm.

    Attributes:
        parent (ArcTokenItem): arc token item
        extent (int): preferred extent
        label_color (QColor): label bg color
        object_class_name (str): object class name
        object_name (str): object name
    """

    def __init__(self, parent, extent, label_color, object_class_name, object_name):
        super().__init__(parent)
        pixmap = parent.arc_item._graph_view_form.icon_mngr.object_pixmap(object_class_name).scaledToWidth(extent)
        self.setPixmap(pixmap)
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setTextWidth(extent)
        font = QApplication.font()
        point_size = font.setPointSize(extent / 8)
        factor = max(0.75, 0.9 * extent / QFontMetrics(font).width(object_name))
        if factor < 1:
            font.setPointSizeF(font.pointSize() * factor)
        self.text_item.setFont(font)
        elided = QFontMetrics(font).elidedText(object_name, Qt.ElideMiddle, extent)
        self.text_item.setPlainText(elided)
        x = (self.boundingRect().width() - self.text_item.boundingRect().width()) / 2
        y = (self.boundingRect().height() - self.text_item.boundingRect().height()) / 2
        self.text_item.setPos(x, y)
        option = self.text_item.document().defaultTextOption()
        option.setAlignment(Qt.AlignCenter)
        self.text_item.document().setDefaultTextOption(option)
        self.bg = QGraphicsRectItem(self.text_item.boundingRect(), self.text_item)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.bg.setBrush(QBrush(label_color))

    def setOffset(self, offset):
        super().setOffset(offset)
        self.text_item.moveBy(offset.x(), offset.y())


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
