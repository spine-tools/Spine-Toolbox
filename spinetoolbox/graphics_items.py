######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

from math import atan2, sin, cos, pi
from PySide2.QtCore import Qt, Slot, QPointF, QLineF, QRectF, QVariantAnimation
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
from PySide2.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QTextCursor,
    QTransform,
    QPalette,
    QTextBlockFormat,
    QLinearGradient,
)
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from spinetoolbox.project_commands import MoveIconCommand


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
        pen = QPen(Qt.black, 0.5, Qt.SolidLine)
        self.setPen(pen)
        self.setBrush(self.brush)
        parent_rect = parent.rect()
        extent = 0.2 * parent_rect.width()
        rect = QRectF(0, 0, extent, extent)
        if position == "top":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.top() + extent / 2))
        elif position == "left":
            rect.moveCenter(QPointF(parent_rect.left() + extent / 2, parent_rect.center().y()))
        elif position == "bottom":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.bottom() - extent / 2))
        elif position == "right":
            rect.moveCenter(QPointF(parent_rect.right() - extent / 2, parent_rect.center().y()))
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def outgoing_links(self):
        return [l for l in self.links if l.src_connector == self]

    def incoming_links(self):
        return [l for l in self.links if l.dst_connector == self]

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
        self.setZValue(2)

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
    def __init__(self, toolbox, x, y, w, h, project_item, icon_file, icon_color, background_color):
        """Base class for project item icons drawn in Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Icon width
            h (float): Icon height
            project_item (ProjectItem): Item
            icon_file (str): Path to icon resource
            icon_color (QColor): Icon's color
            background_color (QColor): Background color
        """
        super().__init__()
        self._toolbox = toolbox
        self._project_item = project_item
        self._moved_on_scene = False
        self._previous_pos = QPointF()
        self._current_pos = QPointF()
        self.selected_icons = []
        self.renderer = QSvgRenderer()
        self.svg_item = QGraphicsSvgItem()
        self.colorizer = QGraphicsColorizeEffect()
        self.setRect(QRectF(x, y, w, h))  # Set ellipse coordinates and size
        self.text_font_size = 10  # point size
        # Make item name graphics item.
        name = project_item.name if project_item else ""
        self.name_item = QGraphicsSimpleTextItem(name)
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
        self.activate()

    def activate(self):
        """Adds items to scene and setup graphics effect.
        Called in the constructor and when re-adding the item to the project in the context of undo/redo.
        """
        scene = self._toolbox.ui.graphicsView.scene()
        scene.addItem(self)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        shadow_effect.setEnabled(False)
        self.setGraphicsEffect(shadow_effect)

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
        return self._project_item.name

    def update_name_item(self, new_name):
        """Set a new text to name item. Used when a project item is renamed."""
        self.name_item.setText(new_name)
        self.set_name_attributes()

    def set_name_attributes(self):
        """Set name QGraphicsSimpleTextItem attributes (font, size, position, etc.)"""
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

    def outgoing_links(self):
        return [l for conn in self.connectors.values() for l in conn.outgoing_links()]

    def incoming_links(self):
        return [l for conn in self.connectors.values() for l in conn.incoming_links()]

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
        super().mousePressEvent(event)
        self.selected_icons = set(x for x in self.scene().selectedItems() if isinstance(x, ProjectItemIcon))
        for icon in self.selected_icons:
            icon._previous_pos = icon.scenePos()

    def mouseMoveEvent(self, event):
        """Moves icon(s) while the mouse button is pressed.
        Update links that are connected to selected icons.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseMoveEvent(event)
        self.update_links_geometry()

    def update_links_geometry(self):
        """Updates geometry of connected links to reflect this item's most recent position."""
        links = set(link for icon in self.selected_icons for conn in icon.connectors.values() for link in conn.links)
        for link in links:
            link.update_geometry()

    def mouseReleaseEvent(self, event):
        for icon in self.selected_icons:
            icon._current_pos = icon.scenePos()
        if (self._current_pos - self._previous_pos).manhattanLength() > qApp.startDragDistance():
            self._toolbox.undo_stack.push(MoveIconCommand(self))
        super().mouseReleaseEvent(event)

    def shrink_scene_if_needed(self):
        if self._moved_on_scene:
            self._moved_on_scene = False
            scene = self.scene()
            scene.shrink_if_needed()
            scene.item_move_finished.emit(self)

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
            self._project_item._project.remove_item(self.name())
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


class LinkBase(QGraphicsPathItem):
    """Base class for Link and LinkDrawer.

    Mainly provides the `update_geometry` method for 'drawing' the link on the scene.
    """

    def __init__(self, toolbox):
        """Initializes the instance.

        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__()
        self._toolbox = toolbox
        self.arrow_angle = pi / 4
        self.magic_number = None

    @property
    def src_rect(self):
        """Returns the scene rectangle of the source connector."""
        return self.src_connector.sceneBoundingRect()

    @property
    def src_center(self):
        """Returns the center point of the source rectangle."""
        return self.src_rect.center()

    @property
    def dst_rect(self):
        """Returns the scene rectangle of the destination connector."""
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        """Returns the center point of the destination rectangle."""
        return self.dst_rect.center()

    def update_geometry(self):
        """Updates geometry."""
        self.prepareGeometryChange()
        qsettings = self._toolbox.qsettings()
        curved_links = qsettings.value("appSettings/curvedLinks", defaultValue="false") == "true"
        self.do_update_geometry(curved_links)

    def do_update_geometry(self, curved_links):
        """Sets the path for this item.

        Args:
            curved_links (bool): Whether the path should follow a curvy line or a straight line
        """
        ellipse_path = self._make_ellipse_path()
        guide_path = self._make_guide_path(curved_links)
        connecting_path = self._make_connecting_path(guide_path)
        arrow_path = self._make_arrow_path(guide_path)
        path = ellipse_path + connecting_path + arrow_path
        self.setPath(path.simplified())

    def _make_ellipse_path(self):
        """Returns an ellipse path for the link's base.

        Returns:
            QPainterPath
        """
        ellipse_path = QPainterPath()
        rect = QRectF(0, 0, 1.6 * self.magic_number, 1.6 * self.magic_number)
        rect.moveCenter(self.src_center)
        ellipse_path.addEllipse(rect)
        return ellipse_path

    def _get_src_offset(self):
        if self.src_connector == self.dst_connector:
            return {"left": QPointF(0, 1), "bottom": QPointF(1, 0), "right": QPointF(0, -1)}[
                self.src_connector.position
            ]
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.src_connector.position]

    def _get_dst_offset(self, c1):
        if not self.dst_connector:
            guide_path = QPainterPath(self.src_center)
            guide_path.quadTo(c1, self.dst_center)
            line = self._get_joint_line(guide_path).unitVector()
            return QPointF(-line.dx(), -line.dy())
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.dst_connector.position]

    def _make_guide_path(self, curved_links):
        """Returns a 'narrow' path connecting this item's source and destination.

        Args:
            curved_links (bool): Whether the path should follow a curved line or just a straight line

        Returns:
            QPainterPath
        """
        path = QPainterPath(self.src_center)
        if not curved_links:
            path.lineTo(self.dst_center)
            return path
        c_min = 2 * self.magic_number
        c_max = 8 * self.magic_number
        c_factor = QLineF(self.src_center, self.dst_center).length() / 2
        c_factor = min(c_factor, c_max)
        c_factor = max(c_factor, c_min)
        c1 = self.src_center + c_factor * self._get_src_offset()
        c2 = self.dst_center + c_factor * self._get_dst_offset(c1)
        path.cubicTo(c1, c2, self.dst_center)
        return path

    def _points_and_angles_from_path(self, path):
        """Returns a list of representative points and angles from given path.

        Args:
            path (QPainterPath)

        Returns:
            list(QPointF): points
            list(float): angles
        """
        max_incr = 0.05
        min_incr = 0.01
        max_angle_change = 0.001
        percents = list()
        angles = list()
        t = path.percentAtLength(self.src_rect.width() / 2)
        a = path.angleAtPercent(t)
        while t < 0.5:
            percents.append(t)
            angles.append(a)
            t_ref = t
            a_ref = a
            incr = max_incr
            while incr > min_incr:
                t = t_ref + incr
                a = path.angleAtPercent(t)
                try:
                    angle_change = abs((a - a_ref) / (a_ref + a) / 2)
                except ZeroDivisionError:
                    incr = min_incr
                    break
                if angle_change < max_angle_change:
                    break
                incr /= 2
            t += incr
        t = 0.5
        a = path.angleAtPercent(t)
        percents.append(t)
        angles.append(a)
        points = list(map(path.pointAtPercent, percents))
        for t in reversed(percents):
            p = path.pointAtPercent(1.0 - t)
            a = path.angleAtPercent(1.0 - t)
            points.append(p)
            angles.append(a)
        return points, angles

    def _make_connecting_path(self, guide_path):
        """Returns a 'thick' path connecting source and destination, by following the given 'guide' path.

        Args:
            guide_path (QPainterPath)

        Returns:
            QPainterPath
        """
        points, angles = self._points_and_angles_from_path(guide_path)
        outgoing_points = []
        incoming_points = []
        for point, angle in zip(points, angles):
            off = self._radius_from_point_and_angle(point, angle)
            outgoing_points.append(point + off)
            incoming_points.insert(0, point - off)
        p0 = guide_path.pointAtPercent(0)
        a0 = guide_path.angleAtPercent(0)
        off0 = self._radius_from_point_and_angle(p0, a0)
        curve_path = QPainterPath(p0 + off0)
        self._follow_points(curve_path, outgoing_points)
        curve_path.lineTo(incoming_points[0])
        self._follow_points(curve_path, incoming_points)
        curve_path.lineTo(p0 - off0)
        curve_path.closeSubpath()
        curve_path.setFillRule(Qt.WindingFill)
        return curve_path.simplified()

    @staticmethod
    def _follow_points(curve_path, points):
        points = iter(points)
        for p0 in points:
            p1 = next(points)
            curve_path.quadTo(p0, p1)

    def _radius_from_point_and_angle(self, point, angle):
        line = QLineF()
        line.setP1(point)
        line.setAngle(angle)
        normal = line.normalVector()
        normal.setLength(self.magic_number / 2)
        return QPointF(normal.dx(), normal.dy())

    def _make_arrow_path(self, guide_path):
        """Returns an arrow path for the link's tip.

        Args:
            guide_path (QPainterPath): A narrow path connecting source and destination,
                used to determine the arrow orientation.

        Returns:
            QPainterPath
        """
        angle = self._get_joint_angle(guide_path)
        arrow_p0 = self.dst_center
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
        arrow_diag = self.magic_number / sin(self.arrow_angle)
        arrow_p1 = arrow_p0 - d1 * arrow_diag
        arrow_p2 = arrow_p0 - d2 * arrow_diag
        arrow_path = QPainterPath(arrow_p1)
        arrow_path.lineTo(arrow_p0)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        return arrow_path

    def _get_joint_line(self, guide_path):
        t = 1.0 - guide_path.percentAtLength(self.src_rect.width() / 2)
        t = max(t, 0.01)
        src = guide_path.pointAtPercent(t - 0.01)
        dst = guide_path.pointAtPercent(t)
        return QLineF(src, dst)

    def _get_joint_angle(self, guide_path):
        line = self._get_joint_line(guide_path)
        return atan2(-line.dy(), line.dx())


class Link(LinkBase):
    def __init__(self, toolbox, src_connector, dst_connector):
        """A graphics item to represent the connection between two project items.

        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
        """
        super().__init__(toolbox)
        self.src_connector = src_connector  # QGraphicsRectItem
        self.dst_connector = dst_connector
        self.src_icon = src_connector._parent
        self.dst_icon = dst_connector._parent
        # Path parameters
        self.magic_number = 0.625 * self.src_rect.width()
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
        self.setZValue(0.5)  # This makes links appear on top of items because item zValue == 0.0
        self.update_geometry()

    def make_execution_animation(self):
        """Returns an animation to play when execution 'passes' through this link.

        Returns:
            QVariantAnimation
        """
        qsettings = self._toolbox.qsettings()
        duration = int(qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        animation = QVariantAnimation()
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(duration)
        animation.valueChanged.connect(self._handle_execution_animation_value_changed)
        animation.finished.connect(lambda: self.setBrush(QColor(255, 255, 0, 204)))
        animation.finished.connect(animation.deleteLater)
        return animation

    @Slot("QVariant")
    def _handle_execution_animation_value_changed(self, step):
        gradient = QLinearGradient(self.src_center, self.dst_center)
        yellow = QColor(255, 255, 0, 204)
        red = QColor(255, 0, 0, 204)
        delta = 8 * self.magic_number / QLineF(self.src_center, self.dst_center).length()
        gradient.setColorAt(0, yellow)
        gradient.setColorAt(max(0.0, step - delta), yellow)
        gradient.setColorAt(step, red)
        gradient.setColorAt(min(1.0, step + delta), yellow)
        gradient.setColorAt(1.0, yellow)
        self.setBrush(gradient)

    def has_parallel_link(self):
        """Returns whether or not this link entirely overlaps another."""
        self.parallel_link = next(
            iter(l for l in self.dst_connector.outgoing_links() if l.dst_connector == self.src_connector), None
        )
        return self.parallel_link is not None

    def send_to_bottom(self):
        """Stacks this link before the parallel one if any."""
        if self.parallel_link:
            self.stackBefore(self.parallel_link)

    def mousePressEvent(self, e):
        """Ignores event if there's a connector button underneath,
        to allow creation of new links.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if e.button() != Qt.LeftButton:
            e.ignore()
        elif any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.ignore()

    def mouseDoubleClickEvent(self, e):
        """Accepts event if there's a connector button underneath,
        to prevent unwanted creation of feedback links.
        """
        if any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.accept()

    def contextMenuEvent(self, e):
        """Selects the link and shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def keyPressEvent(self, event):
        """Removes this link if delete is pressed."""
        if event.key() == Qt.Key_Delete and self.isSelected():
            self._toolbox.ui.graphicsView.remove_link(self)

    def paint(self, painter, option, widget):
        """Sets a dashed pen if selected."""
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        """Brings selected link to top."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and value == 1:
            for item in self.collidingItems():  # TODO: try using scene().collidingItems() which is ordered
                if not isinstance(item, Link):
                    continue
                item.stackBefore(self)
            return value
        return super().itemChange(change, value)

    def wipe_out(self):
        """Removes any trace of this item from the system."""
        self.src_connector.links.remove(self)
        self.dst_connector.links.remove(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)


class LinkDrawer(LinkBase):
    def __init__(self, toolbox):
        """An item for drawing links between project items.

        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self.src_connector = None  # source connector
        self.tip = None
        self.drawing = False
        self.setBrush(QBrush(QColor(255, 0, 255, 204)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setZValue(1)  # LinkDrawer should be on top of every other item
        self.hide()

    def start_drawing_at(self, src_connector):
        """Starts drawing a link from the given connector.

        Args:
            src_connector (ConnectorButton)
        """
        self.src_connector = src_connector
        self.tip = self.src_center
        self.magic_number = 0.625 * self.src_rect.width()
        self.update_geometry()
        self.show()

    @property
    def dst_connector(self):
        items = self.scene().items(self.tip)
        # Now that feedback loops are disabled, we don't want the tip to 'snap' to any of the src
        # connector buttons.
        src_connectors = self.src_connector._parent.connectors.values()
        for conn in src_connectors:
            if conn in items:
                return None  # Return None if the tip is on any source connector button
        return next(iter(x for x in items if isinstance(x, ConnectorButton)), None)

    @property
    def dst_rect(self):
        if not self.dst_connector:
            return QRectF()
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        if not self.dst_connector:
            return self.tip
        # If link drawer tip is on a connector button, this makes
        # the tip 'snap' to the center of the connector button
        return self.dst_rect.center()
