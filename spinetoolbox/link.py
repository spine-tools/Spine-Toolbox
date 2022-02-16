######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
:date:    4.4.2018
"""

from math import sin, cos, pi, radians
from PySide2.QtCore import Qt, Slot, QPointF, QLineF, QRectF, QVariantAnimation
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QStyle,
    QToolTip,
)
from PySide2.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QLinearGradient,
    QFont,
    QCursor,
    QFontMetrics,
    QPixmap,
    QPainter,
)
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
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
        self.selected_pen = QPen(self.pen_brush, 1, Qt.DashLine)
        self.normal_pen = QPen(self.pen_brush, 0.5)
        self._guide_path = None
        self.setBrush(QBrush(self._COLOR))

    @property
    def pen_brush(self):
        return QBrush(self._COLOR.darker())

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
        ellipse_path = self._make_ellipse_path()
        connecting_path = self._make_connecting_path()
        arrow_path = self._make_arrow_path()
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
        if p1 is None:
            return False
        return (p1 - p2).manhattanLength() < 2 * self.magic_number

    def _make_guide_path(self, curved_links=False):
        """Returns a 'narrow' path connecting this item's source and destination.

        Args:
            curved_links (bool): Whether the path should follow a curved line or just a straight line

        Returns:
            QPainterPath
        """
        c_factor = min(4.5 * self.magic_number, (self.src_center - self.dst_center).manhattanLength() / 4)
        src = self.src_center + c_factor * self._get_src_offset()
        dst = self.dst_center + c_factor * self._get_dst_offset()
        src_points = [self.src_center, src]
        dst_points = [self.dst_center, dst]
        while True:
            # Bring source points closer to destination
            new_src = self._find_new_point(src_points, dst)
            if self._close_enough(new_src, dst):
                src_points.append(new_src)
                break
            # Bring destination points closer to source
            new_dst = self._find_new_point(dst_points, src)
            if self._close_enough(new_dst, src):
                dst_points.append(new_dst)
                break
            if new_src is not None:
                src_points.append(new_src)
                src = new_src
            if new_dst is not None:
                dst_points.append(new_dst)
                dst = new_dst
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
        points[-1] = head.pointAtPercent(1 - head.percentAtLength(self.magic_number / 2))
        # Make path
        path = QPainterPath(points.pop(0))
        if not curved_links:
            for p1 in points:
                path.lineTo(p1)
            return path
        for p1, p2 in zip(points[:-2], points[1:-1]):
            path.quadTo(p1, (p1 + p2) / 2)
        path.quadTo(points[-2], points[-1])
        return path

    def _get_joint_angle(self):
        line = QLineF(self._get_dst_offset(), QPointF(0, 0))
        return radians(line.angle())

    def _points_and_angles_from_path(self, path):
        """Returns a list of representative points and angles from given path.

        Args:
            path (QPainterPath)

        Returns:
            list(QPointF): points
            list(float): angles
        """
        count = 100
        percents = [k / count for k in range(count + 1)]
        points = list(map(path.pointAtPercent, percents))
        angles = list(map(path.angleAtPercent, percents))
        return points, angles

    def _make_connecting_path(self):
        """Returns a 'thick' path connecting source and destination, by following the given 'guide' path.

        Returns:
            QPainterPath
        """
        points, angles = self._points_and_angles_from_path(self._guide_path)
        outgoing_points = []
        incoming_points = []
        for point, angle in zip(points, angles):
            off = self._radius_from_point_and_angle(point, angle)
            outgoing_points.append(point + off)
            incoming_points.insert(0, point - off)
        p0 = self._guide_path.pointAtPercent(0)
        a0 = self._guide_path.angleAtPercent(0)
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
        for p0, p1 in zip(points[:-1], points[1:]):
            curve_path.quadTo(p0, p1)
        curve_path.lineTo(points[-1])

    def _radius_from_point_and_angle(self, point, angle):
        line = QLineF()
        line.setP1(point)
        line.setAngle(angle)
        normal = line.normalVector()
        normal.setLength(self.magic_number / 2)
        return QPointF(normal.dx(), normal.dy())

    def _make_arrow_path(self):
        """Returns an arrow path for the link's tip.

        Returns:
            QPainterPath
        """
        angle = self._get_joint_angle()
        arrow_p0 = self.dst_center
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
        arrow_diag = 1.5 * self.magic_number / sin(self.arrow_angle)
        arrow_p1 = arrow_p0 - d1 * arrow_diag
        arrow_p2 = arrow_p0 - d2 * arrow_diag
        arrow_path = QPainterPath(arrow_p1)
        arrow_path.lineTo(arrow_p0)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        return arrow_path

    def itemChange(self, change, value):
        """Wipes out the link when removed from scene."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged and value is None:
            self.wipe_out()
        return super().itemChange(change, value)

    def wipe_out(self):
        """Removes any trace of this item from the system."""


class _IconBase(QGraphicsEllipseItem):
    """Base class for icons to show over a Link."""

    def __init__(self, x, y, w, h, parent, tooltip=None):
        super().__init__(x, y, w, h, parent)
        if tooltip:
            self.setToolTip(tooltip)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setBrush(qApp.palette().window())  # pylint: disable=undefined-variable

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.toolTip())

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()


class _SvgIcon(_IconBase):
    """A svg icon to show over a Link."""

    def __init__(self, x, y, w, h, parent, path, tooltip=None):
        super().__init__(x, y, w, h, parent, tooltip=tooltip)
        self._svg_item = QGraphicsSvgItem(self)
        self._renderer = QSvgRenderer()
        self._renderer.load(path)
        self._svg_item.setSharedRenderer(self._renderer)
        scale = 0.8 * self.rect().width() / self._renderer.defaultSize().width()
        self._svg_item.setScale(scale)
        self._svg_item.setPos(0, 0)
        self._svg_item.setPos(self.sceneBoundingRect().center() - self._svg_item.sceneBoundingRect().center())

    def wipe_out(self):
        """Cleans up icon's resources."""
        self._svg_item.deleteLater()
        self._renderer.deleteLater()
        self.scene().removeItem(self)


class _TextIcon(_IconBase):
    """A font awesome icon to show over a Link."""

    def __init__(self, x, y, w, h, parent, char, tooltip=None, color=None):
        super().__init__(x, y, w, h, parent, tooltip=tooltip)
        if color is None:
            color = QColor("slateblue")
        self._text_item = QGraphicsTextItem(self)
        font = QFont('Font Awesome 5 Free Solid')
        self._text_item.setFont(font)
        self._text_item.setDefaultTextColor(color)
        self._text_item.setPlainText(char)
        self._text_item.setPos(0, 0)
        self._text_item.setPos(self.sceneBoundingRect().center() - self._text_item.sceneBoundingRect().center())

    def wipe_out(self):
        """Cleans up icon's resources."""
        self._text_item.deleteLater()
        self.scene().removeItem(self)


class JumpOrLink(LinkBase):
    """Base class for Jump and Link."""

    def __init__(self, toolbox, src_connector, dst_connector):
        super().__init__(toolbox, src_connector, dst_connector)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self._icon_extent = 4 * self.magic_number
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
        delta = 0.6 / (len(self._icons) + 1)
        percent = 0.2 + delta
        for icon in self._icons:
            center = self._guide_path.pointAtPercent(percent)
            icon.setPos(center - 0.5 * QPointF(self._icon_extent, self._icon_extent))
            percent += delta

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
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            self.setPen(self.selected_pen)
            for icon in self._icons:
                icon.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
            for icon in self._icons:
                icon.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def shape(self):
        shape = super().shape()
        for icon in self._icons:
            shape.addEllipse(icon.sceneBoundingRect())
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
        animation.finished.connect(lambda: self.setBrush(self._COLOR))
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
        self.setBrush(gradient)


class Link(JumpOrLink):
    """A graphics item to represent the connection between two project items."""

    _COLOR = LINK_COLOR
    _MEMORY = "\uf538"
    _FILTERS = "\uf0b0"
    _DATAPACKAGE = ":/icons/datapkg.svg"

    def __init__(self, toolbox, src_connector, dst_connector, connection):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            connection (spine_engine.project_item.connection.Connection): connection this link represents
        """
        super().__init__(toolbox, src_connector, dst_connector)
        self._connection = connection
        self.parallel_link = None
        self.setZValue(0.5)  # This makes links appear on top of items because item zValue == 0.0
        self.update_icons()

    def update_icons(self):
        while self._icons:
            self._icons.pop(0).wipe_out()
        if self._connection.use_datapackage:
            self._icons.append(_SvgIcon(0, 0, self._icon_extent, self._icon_extent, self, self._DATAPACKAGE))
        if self._connection.has_filters():
            self._icons.append(_TextIcon(0, 0, self._icon_extent, self._icon_extent, self, self._FILTERS))
        if self._connection.use_memory_db:
            self._icons.append(_TextIcon(0, 0, self._icon_extent, self._icon_extent, self, self._MEMORY))
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
    _ISSUE_TEXT = "\uf071"
    _NORMAL_TEXT = "\uf2f9"
    _ISSUE_COLOR = QColor("red")

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
        if issues:
            text = self._ISSUE_TEXT
            color = self._ISSUE_COLOR
            tooltip = issues[0]
        else:
            text = self._NORMAL_TEXT
            color = None
            tooltip = ""
        icon = _TextIcon(0, 0, self._icon_extent, self._icon_extent, self, text, color=color, tooltip=tooltip)
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
        self.setPen(QPen(self.pen_brush, 0.5))
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

    def _get_joint_angle(self):
        return radians(self._guide_path.angleAtPercent(0.99))

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
        self.src_connector.scene().addItem(self)
        self.update_geometry()
        self.show()

    def sleep(self):
        """Removes this drawer from the scene, clears its source and destination connectors, and hides it.
        After calling this, the scene is no longer in link drawing mode.
        """
        scene = self.scene()
        scene.removeItem(self)
        scene.link_drawer = self.src_connector = self.dst_connector = self.tip = None
        self.hide()


class ConnectionLinkDrawer(LinkDrawerBase):
    """An item for drawing connection links between project items."""

    _COLOR = LINK_COLOR.lighter()

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self.setBrush(QBrush(self._COLOR))

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
        self.setBrush(QBrush(self._COLOR))

    def add_link(self):
        self._toolbox.ui.graphicsView.add_jump(self.src_connector, self.dst_connector)
        self.sleep()
