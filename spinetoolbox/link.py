######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes for drawing graphics items on QGraphicsScene."""
import functools
from math import sin, cos, pi, radians
from PySide6.QtCore import Qt, Slot, QPointF, QLineF, QRectF, QVariantAnimation
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QStyle,
    QToolTip,
    QGraphicsColorizeEffect,
)
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath, QLinearGradient, QFont, QCursor, QPainterPathStroker
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from spinetoolbox.helpers import color_from_index
from .project_item_icon import ConnectorButton

LINK_COLOR = color_from_index(0, 2, base_hue=60)
JUMP_COLOR = color_from_index(1, 2, base_hue=60)


class LinkBase(QGraphicsPathItem):
    """Base class for Link and LinkDrawer.

    Mainly provides the ``update_geometry`` method for 'drawing' the link on the scene.
    """

    _COLOR = QColor(0, 0, 0, 0)

    def __init__(self, toolbox, src_connector, dst_connector):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton, optional): Source connector button
            dst_connector (ConnectorButton): Destination connector button
        """
        super().__init__()
        self._toolbox = toolbox
        self.src_connector = src_connector
        self.dst_connector = dst_connector
        self.arrow_angle = pi / 4
        self.setCursor(Qt.PointingHandCursor)
        self._guide_path = None
        self._pen = QPen(self._COLOR)
        self._pen.setWidthF(self.magic_number)
        self._pen.setJoinStyle(Qt.MiterJoin)
        self.setPen(self._pen)
        self.selected_pen = QPen(self.outline_color, 2, Qt.DotLine)
        self.normal_pen = QPen(self.outline_color, 1)
        self._outline = QGraphicsPathItem(self)
        self._outline.setFlag(QGraphicsPathItem.ItemStacksBehindParent)
        self._outline.setPen(self.normal_pen)
        self._stroker = QPainterPathStroker()
        self._stroker.setWidth(self.magic_number)
        self._stroker.setJoinStyle(Qt.MiterJoin)
        self._shape = QPainterPath()

    def shape(self):
        return self._shape

    @property
    def outline_color(self):
        return self._COLOR.darker()

    @property
    def magic_number(self):
        return 0.625 * self.src_rect.width()

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

    def moveBy(self, _dx, _dy):
        """Does nothing. This item is not moved the regular way, but follows the ConnectorButtons it connects."""

    def update_geometry(self, curved_links=None):
        """Updates geometry."""
        self.prepareGeometryChange()
        if curved_links is None:
            qsettings = self._toolbox.qsettings()
            curved_links = qsettings.value("appSettings/curvedLinks", defaultValue="false") == "true"
        self._guide_path = self._make_guide_path(curved_links)
        self._do_update_geometry()

    def guide_path(self):
        """For tests."""
        return self._guide_path

    def _do_update_geometry(self):
        """Sets the path for this item."""
        path = QPainterPath(self._guide_path)
        self._add_arrow_path(path)
        self._add_ellipse_path(path)
        self.setPath(path)
        stroke = self._stroker.createStroke(path)
        self._outline.setPath(stroke)
        self._shape.clear()
        self._shape.addPath(stroke)

    def _add_ellipse_path(self, path):
        """Adds an ellipse for the link's base.

        Args:
            QPainterPath
        """
        radius = 0.5 * self.magic_number
        rect = QRectF(0, 0, radius, radius)
        rect.moveCenter(self.src_center)
        path.addEllipse(rect)

    def _get_joint_angle(self):
        return radians(self._guide_path.angleAtPercent(0.99))

    def _add_arrow_path(self, path):
        """Returns an arrow path for the link's tip.

        Args:
            QPainterPath
        """
        angle = self._get_joint_angle()
        arrow_p0 = self.dst_center + 0.5 * self.magic_number * self._get_dst_offset()
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
        arrow_diag = 1.5 / sin(self.arrow_angle)
        arrow_p1 = arrow_p0 - d1 * arrow_diag
        arrow_p2 = arrow_p0 - d2 * arrow_diag
        path.moveTo(arrow_p1)
        path.lineTo(arrow_p0)
        path.lineTo(arrow_p2)
        path.closeSubpath()

    @staticmethod
    def _get_offset(button):
        return {"top": QPointF(0, -1), "left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[
            button.position
        ]

    def _get_src_offset(self):
        return self._get_offset(self.src_connector)

    def _get_dst_offset(self):
        return self._get_offset(self.dst_connector)

    def _find_new_point(self, points, target):
        """Finds a new point that approximates points to target in a smooth trajectory.
        Returns the new point, or None if no need for approximation.

        Args:
            points (list(QPointF))
            target (QPointF)

        Returns:
            QPointF or None
        """
        line = QLineF(*points[-2:])
        line_to_target = QLineF(points[-1], target)
        angle = line.angleTo(line_to_target)
        corrected_angle = angle if angle < 180 else angle - 360
        if abs(corrected_angle) <= 90:
            return None
        sign = abs(corrected_angle) // corrected_angle
        new_angle = line.angle() + 90 * sign
        foot = sin if angle > 0 else cos
        new_length = max(abs(foot(radians(angle))) * line_to_target.length(), 3 * self.magic_number)
        line_to_target.setAngle(new_angle)
        line_to_target.setLength(new_length)
        return line_to_target.center()

    def _close_enough(self, p1, p2):
        return (p1 - p2).manhattanLength() < 2 * self.magic_number

    def _make_guide_path(self, curved_links=False):
        """Returns a 'narrow' path connecting this item's source and destination.

        Args:
            curved_links (bool): Whether the path should follow a curved line or just a straight line

        Returns:
            QPainterPath
        """
        c_factor = 3 * self.magic_number
        src = self.src_center + c_factor * self._get_src_offset()
        dst = self.dst_center + c_factor * self._get_dst_offset()
        src_points = [self.src_center, src]
        dst_points = [self.dst_center, dst]
        while True:
            # Bring source points closer to destination
            new_src = self._find_new_point(src_points, dst)
            if new_src is not None:
                src_points.append(new_src)
                src = new_src
            if self._close_enough(src, dst):
                break
            # Bring destination points closer to source
            new_dst = self._find_new_point(dst_points, src)
            if new_dst is not None:
                dst_points.append(new_dst)
                dst = new_dst
            if self._close_enough(src, dst):
                break
            if new_src is new_dst is None:
                break
        points = src_points + list(reversed(dst_points))
        points = list(map(lambda xy: QPointF(*xy), dict.fromkeys((p.x(), p.y()) for p in points)))
        if len(points) == 1:
            path = QPainterPath(points[0])
            path.lineTo(points[0] + QPointF(1, 1))
            return path
        # Correct last point so it doesn't go beyond the arrow
        head = QPainterPath(points[-2])
        head.lineTo(points[-1])
        points[-1] = head.pointAtPercent(1 - head.percentAtLength(self.magic_number))
        # Make path
        path = QPainterPath(points.pop(0))
        if not curved_links:
            for p1 in points:
                path.lineTo(p1)
            return path
        for p1, p2 in zip(points[:-2], points[1:-1]):
            path.quadTo(p1, (p1 + p2) / 2)
        if len(points) == 1:
            path.lineTo(points[-1])
        else:
            path.quadTo(points[-2], points[-1])
        return path

    def itemChange(self, change, value):
        """Wipes out the link when removed from scene."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged and value is None:
            self.wipe_out()
        return super().itemChange(change, value)

    def wipe_out(self):
        """Removes any trace of this item from the system."""


class _IconBase(QGraphicsEllipseItem):
    """Base class for icons to show over a Link."""

    def __init__(self, x, y, w, h, parent, tooltip=None, active=True):
        super().__init__(x, y, w, h, parent)
        palette = qApp.palette()  # pylint: disable=undefined-variable
        brush = palette.highlight() if active else palette.mid()
        self._fg_color = brush.color()
        if tooltip:
            self.setToolTip(tooltip)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setBrush(palette.window())

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.toolTip())

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()


class _SvgIcon(_IconBase):
    """A svg icon to show over a Link."""

    def __init__(self, parent, extent, path, tooltip=None, active=False):
        super().__init__(0, 0, extent, extent, parent, tooltip=tooltip, active=active)
        self._svg_item = QGraphicsSvgItem(self)
        self._renderer = QSvgRenderer()
        self._renderer.load(path)
        self._colorizer = QGraphicsColorizeEffect()
        self._colorizer.setColor(self._fg_color)
        self._svg_item.setSharedRenderer(self._renderer)
        self._svg_item.setGraphicsEffect(self._colorizer)
        scale = 0.8 * self.rect().width() / self._renderer.defaultSize().width()
        self._svg_item.setScale(scale)
        self._svg_item.setPos(self.sceneBoundingRect().center() - self._svg_item.sceneBoundingRect().center())
        self.setPen(Qt.NoPen)

    def wipe_out(self):
        """Cleans up icon's resources."""
        self._svg_item.deleteLater()
        self._renderer.deleteLater()
        self.scene().removeItem(self)


class _TextIcon(_IconBase):
    """A font awesome icon to show over a Link."""

    def __init__(self, parent, extent, char, tooltip=None, active=False):
        super().__init__(0, 0, extent, extent, parent, tooltip=tooltip, active=active)
        self._text_item = QGraphicsTextItem(self)
        font = QFont("Font Awesome 5 Free Solid", weight=QFont.Bold)
        self._text_item.setFont(font)
        self._text_item.setDefaultTextColor(self._fg_color)
        self._text_item.setPlainText(char)
        self._text_item.setPos(self.sceneBoundingRect().center() - self._text_item.sceneBoundingRect().center())
        self.setPen(Qt.NoPen)

    def wipe_out(self):
        """Cleans up icon's resources."""
        self._text_item.deleteLater()
        self.scene().removeItem(self)


class _WarningTextIcon(_TextIcon):
    """A font awesome icon to show over a Link."""

    def __init__(self, parent, extent, char, tooltip):
        super().__init__(parent, extent, char, tooltip, active=True)
        self._fg_color = QColor("red")
        self._text_item.setDefaultTextColor(self._fg_color)


class JumpOrLink(LinkBase):
    """Base class for Jump and Link."""

    def __init__(self, toolbox, src_connector, dst_connector):
        super().__init__(toolbox, src_connector, dst_connector)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self._icon_extent = 3 * self.magic_number
        self._icons = []
        self._anim = self._make_execution_animation()
        self.update_geometry()

    @property
    def item(self):
        raise NotImplementedError()

    def _do_update_geometry(self):
        """See base class."""
        super()._do_update_geometry()
        self._place_icons()

    def _place_icons(self):
        center = self._guide_path.pointAtPercent(0.5)
        icon_count = len(self._icons)
        if not icon_count:
            return
        icon_extent = self._icon_extent / (icon_count ** (1 / 4))
        offset = 0.5 * QPointF(icon_extent, icon_extent)
        if icon_count == 1:
            self._icons[0].setPos(center - offset)
            return
        points = list(_regular_polygon_points(icon_count, icon_extent, self._guide_path.angleAtPercent(0.5)))
        points_center = functools.reduce(lambda a, b: a + b, points) / icon_count
        offset += points_center - center
        scale = icon_extent / self._icon_extent
        for icon, point in zip(self._icons, points):
            icon.setScale(scale)
            icon.setPos(point - offset)

    def mousePressEvent(self, e):
        """Ignores event if there's a connector button underneath,
        to allow creation of new links.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.ignore()

    def contextMenuEvent(self, e):
        """Selects the link and shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def paint(self, painter, option, widget=None):
        """Sets a dashed pen if selected."""
        if option.state & QStyle.StateFlag.State_Selected:
            option.state &= ~QStyle.StateFlag.State_Selected
            self._outline.setPen(self.selected_pen)
            for icon in self._icons:
                icon.setPen(self.selected_pen)
        else:
            self._outline.setPen(self.normal_pen)
            for icon in self._icons:
                icon.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def shape(self):
        shape = super().shape()
        for icon in self._icons:
            path = QPainterPath()
            path.addEllipse(icon.sceneBoundingRect())
            shape += path
        return shape

    def wipe_out(self):
        """Removes any trace of this item from the system."""
        self.src_connector.links.remove(self)
        self.dst_connector.links.remove(self)

    def _make_execution_animation(self):
        """Returns an animation to play when execution 'passes' through this link.

        Returns:
            QVariantAnimation
        """
        animation = QVariantAnimation()
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.valueChanged.connect(self._handle_execution_animation_value_changed)
        animation.finished.connect(lambda: self.setPen(self._pen))
        return animation

    def run_execution_animation(self):
        """Runs execution animation."""
        qsettings = self._toolbox.qsettings()
        duration = int(qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        self._anim.setDuration(duration)
        self._anim.start()

    @Slot(object)
    def _handle_execution_animation_value_changed(self, step):
        exec_color = QColor("red")
        gradient = QLinearGradient(self.src_center, self.dst_center)
        delta = 8 * self.magic_number / QLineF(self.src_center, self.dst_center).length()
        gradient.setColorAt(0, self._COLOR)
        gradient.setColorAt(max(0.0, step - delta), self._COLOR)
        gradient.setColorAt(step, exec_color)
        gradient.setColorAt(min(1.0, step + delta), self._COLOR)
        gradient.setColorAt(1.0, self._COLOR)
        pen = QPen(self._pen)
        pen.setBrush(gradient)
        self.setPen(pen)


class Link(JumpOrLink):
    """A graphics item to represent the connection between two project items."""

    _COLOR = LINK_COLOR
    _MEMORY = "\uf538"
    _FILTERS = "\uf0b0"
    _PURGE = "\uf0e7"
    _WARNING = "\uf06a"
    _DATAPACKAGE = ":/icons/datapkg.svg"

    def __init__(self, toolbox, src_connector, dst_connector, connection):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            connection (LoggingConnection): connection this link represents
        """
        super().__init__(toolbox, src_connector, dst_connector)
        self._connection = connection
        self.setZValue(0.5)  # This makes links appear on top of items because item zValue == 0.0

    def update_icons(self):
        while self._icons:
            self._icons.pop(0).wipe_out()
        if self._connection.may_use_datapackage():
            active = self._connection.use_datapackage
            self._icons.append(_SvgIcon(self, self._icon_extent, self._DATAPACKAGE, active=active))
        if self._connection.may_have_filters():
            active = self._connection.has_filters()
            self._icons.append(_TextIcon(self, self._icon_extent, self._FILTERS, active=active))
        if self._connection.may_use_memory_db():
            active = self._connection.use_memory_db
            self._icons.append(_TextIcon(self, self._icon_extent, self._MEMORY, active=active))
        if self._connection.may_purge_before_writing():
            active = self._connection.purge_before_writing
            self._icons.append(_TextIcon(self, self._icon_extent, self._PURGE, active=active))
        if self._connection.may_have_write_index():
            sibling_conns = self._toolbox.project().incoming_connections(self.connection.destination)
            active = any(l.write_index > 1 for l in sibling_conns)
            self._icons.append(_TextIcon(self, self._icon_extent, str(self._connection.write_index), active=active))
        notifications = self._connection.notifications()
        if notifications:
            tooltip = "Check Link properties. " + " ".join(notifications)
            self._icons.append(_WarningTextIcon(self, self._icon_extent, self._WARNING, tooltip))
        self._place_icons()

    @property
    def name(self):
        return self._connection.name

    @property
    def connection(self):
        return self._connection

    @property
    def item(self):
        return self.connection

    def itemChange(self, change, value):
        """Brings selected link to top."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and value == 1:
            for item in self.collidingItems():  # TODO: try using scene().collidingItems() which is ordered
                if not isinstance(item, Link):
                    continue
                item.stackBefore(self)
        return super().itemChange(change, value)


class JumpLink(JumpOrLink):
    """A graphics icon to represent a jump connection between items."""

    _COLOR = JUMP_COLOR
    _ISSUE = "\uf071"

    def __init__(self, toolbox, src_connector, dst_connector, jump):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            jump (spine_engine.project_item.connection.Jump): connection this link represents
        """
        super().__init__(toolbox, src_connector, dst_connector)
        self._jump = jump
        self.setZValue(0.6)
        self.update_icons()

    @property
    def jump(self):
        return self._jump

    @property
    def item(self):
        return self.jump

    @property
    def name(self):
        return self._jump.name

    def issues(self):
        """Checks if jump is well-defined.

        Returns:
            list of str: issues regarding the jump
        """
        return self._toolbox.project().jump_issues(self.jump)

    def update_icons(self):
        while self._icons:
            self._icons.pop(0).wipe_out()
        issues = self.issues()
        if not issues:
            return
        icon = _TextIcon(self, self._icon_extent, self._ISSUE, active=True, tooltip="\n".join(issues))
        self._icons.append(icon)
        self._place_icons()


class LinkDrawerBase(LinkBase):
    """A base class for items intended for drawing links between project items."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox, None, None)
        self.tip = None
        self.setZValue(1)  # A drawer should be on top of every other item.

    @property
    def src_rect(self):
        if not self.src_connector:
            return QRectF()
        return self.src_connector.sceneBoundingRect()

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

    def _get_dst_offset(self):
        if self.dst_connector is None:
            return QPointF(0, 0)
        return super()._get_dst_offset()

    def add_link(self):
        """Makes link between source and destination connectors."""
        raise NotImplementedError()

    def wake_up(self, src_connector):
        """Sets the source connector, shows this item and adds it to the scene.
        After calling this, the scene is in link drawing mode.

        Args:
            src_connector (ConnectorButton): source connector
        """
        view = self._toolbox.ui.graphicsView
        self.tip = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
        self.src_connector = src_connector
        scene = self.src_connector.scene()
        scene.addItem(self)
        self._stroker.setWidth(self.magic_number)
        self._pen.setWidthF(self.magic_number)
        self.setPen(self._pen)
        self.update_geometry()
        self.show()
        scene.link_about_to_be_drawn.emit()

    def sleep(self):
        """Removes this drawer from the scene, clears its source and destination connectors, and hides it.
        After calling this, the scene is no longer in link drawing mode.
        """
        scene = self.scene()
        scene.removeItem(self)
        scene.link_drawer = self.src_connector = self.dst_connector = self.tip = None
        self.hide()
        scene.link_drawing_finished.emit()


class ConnectionLinkDrawer(LinkDrawerBase):
    """An item for drawing connection links between project items."""

    _COLOR = LINK_COLOR.lighter()

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self._pen.setBrush(QBrush(self._COLOR))

    def add_link(self):
        self._toolbox.ui.graphicsView.add_link(self.src_connector, self.dst_connector)
        self.sleep()

    def wake_up(self, src_connector):
        super().wake_up(src_connector)
        self.src_connector.set_friend_connectors_enabled(False)

    def sleep(self):
        self.src_connector.set_friend_connectors_enabled(True)
        super().sleep()


class JumpLinkDrawer(LinkDrawerBase):
    """An item for drawing jump connections between project items."""

    _COLOR = JUMP_COLOR.lighter()

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self._pen.setBrush(QBrush(self._COLOR))

    def add_link(self):
        self._toolbox.ui.graphicsView.add_jump(self.src_connector, self.dst_connector)
        self.sleep()


def _regular_polygon_points(n, side, initial_angle=0):
    internal_angle = 180 * (n - 2) / n
    angle_inc = 180 - internal_angle
    current_angle = initial_angle
    point = QPointF(0, 0)
    for _ in range(n):
        yield point
        line = QLineF(point, point + QPointF(side, 0))
        line.setAngle(current_angle)
        point = line.p2()
        current_angle += angle_inc
