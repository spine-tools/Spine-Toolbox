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

from math import atan2, degrees, sin, cos, pi
from PySide2.QtCore import Qt, QPointF, QLineF, QRectF
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsSimpleTextItem,
    QGraphicsRectItem,
    QStyle,
    QGraphicsColorizeEffect,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide2.QtGui import QColor, QPen, QBrush, QPainterPath, QTextCursor, QTransform, QPalette, QTextBlockFormat
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer


class ConnectorButton(QGraphicsRectItem):

    # Regular and hover brushes
    brush = QBrush(QColor(255, 255, 255))  # Used in filling the item
    hover_brush = QBrush(QColor(50, 0, 50, 128))  # Used in filling the item while hovering

    def __init__(self, parent, toolbox, position="left"):
        """Connector button graphics item. Used for Link drawing between project items.

        Args:
            parent (QGraphicsItem): Project item bg rectangle
            toolbox (ToolBoxUI): QMainWindow instance
            position (str): Either "top", "left", "bottom", or "right"
        """
        super().__init__()
        self._parent = parent
        self._toolbox = toolbox
        self.position = position
        self.links = list()
        self.setPen(QPen(Qt.black, 0.5, Qt.SolidLine))
        # self.setPen(QPen(Qt.NoPen))
        self.setBrush(self.brush)
        parent_rect = parent.rect()
        extent = 0.2 * parent_rect.width()
        rect = QRectF(0, 0, extent, extent)
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


class ExclamationIcon(QGraphicsSvgItem):
    def __init__(self, parent):
        """Exclamation icon graphics item.
        Used to notify that a ProjectItem is missing some configuration.

        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__()
        self._parent = parent
        self._notifications = list()
        self.renderer = QSvgRenderer()
        self.colorizer = QGraphicsColorizeEffect()
        self.colorizer.setColor(QColor("red"))
        # Load SVG
        loading_ok = self.renderer.load(":/icons/project_item_icons/exclamation-circle.svg")
        if not loading_ok:
            return
        size = self.renderer.defaultSize()
        self.setSharedRenderer(self.renderer)
        dim_max = max(size.width(), size.height())
        rect_w = parent.rect().width()  # Parent rect width
        self.setScale(0.2 * rect_w / dim_max)
        self.setGraphicsEffect(self.colorizer)
        self._notification_list_item = NotificationListItem()
        self._notification_list_item.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.hide()

    def clear_notifications(self):
        """Clear all notifications."""
        self._notifications.clear()
        self.hide()

    def add_notification(self, text):
        """Add a notification."""
        self._notifications.append(text)
        self.show()

    def hoverEnterEvent(self, event):
        """Shows notifications as tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if not self._notifications:
            return
        tip = "<p>" + "<p>".join(self._notifications)
        self._notification_list_item.setHtml(tip)
        self.scene().addItem(self._notification_list_item)
        self._notification_list_item.setPos(self.sceneBoundingRect().topRight() + QPointF(1, 0))

    def hoverLeaveEvent(self, event):
        """Hides tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.scene().removeItem(self._notification_list_item)


class NotificationListItem(QGraphicsTextItem):
    def __init__(self):
        """Notification list graphics item.
        Used to show notifications for a ProjectItem
        """
        super().__init__()
        self.bg = QGraphicsRectItem(self.boundingRect(), self)
        bg_brush = QApplication.palette().brush(QPalette.ToolTipBase)
        self.bg.setBrush(bg_brush)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)

    def setHtml(self, html):
        super().setHtml(html)
        self.adjustSize()
        self.bg.setRect(self.boundingRect())


class RankIcon(QGraphicsTextItem):
    def __init__(self, parent):
        """Rank icon graphics item.
        Used to show the rank of a ProjectItem within its DAG

        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__(parent)
        self._parent = parent
        rect_w = parent.rect().width()  # Parent rect width
        self.text_margin = 0.05 * rect_w
        self.bg = QGraphicsRectItem(self.boundingRect(), self)
        bg_brush = QApplication.palette().brush(QPalette.ToolTipBase)
        self.bg.setBrush(bg_brush)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        font = self.font()
        font.setPointSize(parent.text_font_size)
        font.setBold(True)
        self.setFont(font)
        doc = self.document()
        doc.setDocumentMargin(0)

    def set_rank(self, rank):
        self.setPlainText(str(rank))
        self.adjustSize()
        self.setTextWidth(self.text_margin + self.textWidth())
        self.bg.setRect(self.boundingRect())
        # Align center
        fmt = QTextBlockFormat()
        fmt.setAlignment(Qt.AlignHCenter)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(fmt)
        cursor.clearSelection()
        self.setTextCursor(cursor)


class ProjectItemIcon(QGraphicsRectItem):
    def __init__(self, toolbox, x, y, w, h, name, icon_file, icon_color, background_color):
        """Base class for project item icons drawn in Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Icon width
            h (float): Icon height
            name (str): Item name
            icon_file (str): Path to icon resource
            icon_color (QColor): Icon's color
            background_color (QColor): Background color
        """
        super().__init__()
        self._toolbox = toolbox
        self._moved_on_scene = False
        self.renderer = QSvgRenderer()
        self.svg_item = QGraphicsSvgItem()
        self.colorizer = QGraphicsColorizeEffect()
        self.setRect(QRectF(x, y, w, h))  # Set ellipse coordinates and size
        self.text_font_size = 10  # point size
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
        # Make exclamation and rank icons
        self.exclamation_icon = ExclamationIcon(self)
        self.rank_icon = RankIcon(self)
        # Group the drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        # NOTE: setting the parent item moves the items as one!
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
        self.svg_item.setParentItem(self)
        self.exclamation_icon.setParentItem(self)
        self.rank_icon.setParentItem(self)
        brush = QBrush(background_color)
        self._setup(brush, icon_file, icon_color)
        # Add items to scene
        scene = self._toolbox.ui.graphicsView.scene()
        scene.addItem(self)

    def _setup(self, brush, svg, svg_color):
        """Setup item's attributes.

        Args:
            brush (QBrush): Used in filling the background rectangle
            svg (str): Path to SVG icon file
            svg_color (QColor): Color of SVG icon
        """
        self.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self.setBrush(brush)
        self.colorizer.setColor(svg_color)
        # Load SVG
        loading_ok = self.renderer.load(svg)
        if not loading_ok:
            self._toolbox.msg_error.emit("Loading SVG icon from resource:{0} failed".format(svg))
            return
        size = self.renderer.defaultSize()
        self.svg_item.setSharedRenderer(self.renderer)
        self.svg_item.setElementId("")  # guess empty string loads the whole file
        dim_max = max(size.width(), size.height())
        rect_w = self.rect().width()  # Parent rect width
        margin = 32
        self.svg_item.setScale((rect_w - margin) / dim_max)
        x_offset = (rect_w - self.svg_item.sceneBoundingRect().width()) / 2
        y_offset = (rect_w - self.svg_item.sceneBoundingRect().height()) / 2
        self.svg_item.setPos(self.rect().x() + x_offset, self.rect().y() + y_offset)
        self.svg_item.setGraphicsEffect(self.colorizer)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        # Set exclamation and rank icons position
        self.exclamation_icon.setPos(self.rect().topRight() - self.exclamation_icon.sceneBoundingRect().topRight())
        self.rank_icon.setPos(self.rect().topLeft())

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
        font.setPointSize(self.text_font_size)
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
        return self.connectors.get(position, self.connectors["left"])

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

    def mouseMoveEvent(self, event):
        """Moves icon(s) while the mouse button is pressed.
        Update links that are connected to selected icons.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseMoveEvent(event)
        selected_icons = set(x for x in self.scene().selectedItems() if isinstance(x, ProjectItemIcon))
        links = set(link for icon in selected_icons for conn in icon.connectors.values() for link in conn.links)
        for link in links:
            link.update_geometry()

    def mouseReleaseEvent(self, event):
        if self._moved_on_scene:
            self._moved_on_scene = False
            self.scene().shrink_if_needed()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        self.scene().clearSelection()
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
            links = set(lnk for conn in self.connectors.values() for lnk in conn.links)
            for link in links:
                link.update_geometry()
            event.accept()
        else:
            super().keyPressEvent(event)

    def itemChange(self, change, value):
        """
        Reacts to item removal and position changes.

        In particular, destroys the drop shadow effect when the items is removed from a scene
        and keeps track of item's movements on the scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
             Whatever super() does with the value parameter
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            self.prepareGeometryChange()
            self.setGraphicsEffect(None)
        return super().itemChange(change, value)

    def show_item_info(self):
        """Update GUI to show the details of the selected item."""
        ind = self._toolbox.project_item_model.find_item(self.name())
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)


class Link(QGraphicsPathItem):
    def __init__(self, toolbox, src_connector, dst_connector):
        """An item that represents a connection between project items.

        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
        """
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
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setCursor(Qt.PointingHandCursor)
        self.update_geometry()

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
        self.find_parallel_link()
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def keyPressEvent(self, event):
        """Remove associated connection if this is selected and delete is pressed."""
        if event.key() == Qt.Key_Delete and self.isSelected():
            self._toolbox.ui.graphicsView.remove_link(self)

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
    def __init__(self):
        """An item that allows one to draw links between slot buttons in QGraphicsView."""
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
        self.inner_shift = None
        self.outer_shift = None
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
