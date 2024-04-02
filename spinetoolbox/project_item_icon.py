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
import math
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsColorizeEffect,
    QGraphicsDropShadowEffect,
    QToolTip,
    QStyle,
)
from PySide6.QtGui import (
    QColor,
    QPen,
    QBrush,
    QTextCursor,
    QTextBlockFormat,
    QFont,
    QPainterPath,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from spine_engine.spine_engine import ItemExecutionFinishState
from .project_commands import MoveIconCommand
from .helpers import LinkType, fix_lightness_color


class ProjectItemIcon(QGraphicsPathItem):
    """Base class for project item icons drawn in Design View."""

    ITEM_EXTENT = 64
    FONT_SIZE_PIXELS = 12  # pixel size to prevent font scaling by system

    def __init__(self, toolbox, icon_file, icon_color):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            icon_file (str): Path to icon resource
            icon_color (QColor): Icon's color
        """
        super().__init__()
        self._toolbox = toolbox
        self._scene = None
        self._bumping = True
        self.bumped_rects = {}  # Item rect before it was bumped
        self.icon_file = icon_file
        self._icon_color = icon_color
        self._moved_on_scene = False
        self.previous_pos = QPointF()
        self.icon_group = {self}
        self.renderer = QSvgRenderer()
        self.svg_item = QGraphicsSvgItem(self)
        self.svg_item.setZValue(100)
        self.colorizer = QGraphicsColorizeEffect()
        self._rect = QRectF(-self.ITEM_EXTENT / 2, -self.ITEM_EXTENT / 2, self.ITEM_EXTENT, self.ITEM_EXTENT)
        self.component_rect = QRectF(0, 0, self.ITEM_EXTENT / 4, self.ITEM_EXTENT / 4)
        self._selection_halo = QGraphicsPathItem(self)
        # Make exclamation, rank, and execution icons
        self.exclamation_icon = ExclamationIcon(self)
        self.execution_icon = ExecutionIcon(self)
        self.rank_icon = RankIcon(self)
        # Make item name graphics item.
        self._name = ""
        self.name_item = QGraphicsTextItem(self._name)
        self.name_item.setZValue(100)
        self.set_name_attributes()  # Set font, size, position, etc.
        self.spec_item = None  # For displaying Tool Spec icon
        self.spec_item_renderer = None
        # Make connector buttons
        self.connectors = dict(
            bottom=ConnectorButton(toolbox, self, position="bottom"),
            left=ConnectorButton(toolbox, self, position="left"),
            right=ConnectorButton(toolbox, self, position="right"),
        )
        self._setup()
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        shadow_effect.setEnabled(False)
        self.setGraphicsEffect(shadow_effect)
        self._update_path()

    def add_specification_icon(self, spec_icon_path):
        """Adds an SVG icon to bottom left corner of the item icon based on Tool Specification type.

        Args:
            spec_icon_path (str): Path to icon resource file.
        """
        self.spec_item = QGraphicsSvgItem(self)
        self.spec_item_renderer = QSvgRenderer()
        loading_ok = self.spec_item_renderer.load(spec_icon_path)
        if not loading_ok:
            self._toolbox.msg_error.emit(f"Loading SVG icon from resource {spec_icon_path} failed")
            return
        size = self.spec_item_renderer.defaultSize()
        self.spec_item.setSharedRenderer(self.spec_item_renderer)
        self.spec_item.setElementId("")
        dim_max = max(size.width(), size.height())
        rect_w = 0.3 * self.rect().width()  # Parent rect width
        self.spec_item.setScale(rect_w / dim_max)
        self.spec_item.setPos(self.sceneBoundingRect().bottomLeft() - self.spec_item.sceneBoundingRect().center())

    def remove_specification_icon(self):
        """Removes the specification icon SVG from the scene."""
        self.spec_item.setParentItem(None)
        self.spec_item = None

    def rect(self):
        return self._rect

    def _update_path(self):
        rounded = self._toolbox.qsettings().value("appSettings/roundedItems", defaultValue="false") == "true"
        self._do_update_path(rounded)

    def update_path(self, rounded):
        self._do_update_path(rounded)

    def _do_update_path(self, rounded):
        radius = self.component_rect.width() / 2 if rounded else 0
        path = QPainterPath()
        path.addRoundedRect(self._rect, radius, radius)
        self.setPath(path)
        self.rank_icon.update_path(radius)
        for conn in self.connectors.values():
            conn.update_path(radius)
        # Selection halo
        pen_width = 1
        margin = 1
        path = QPainterPath()
        path.addRoundedRect(self._rect.adjusted(-margin, -margin, margin, margin), radius + margin, radius + margin)
        self._selection_halo.setPath(path)
        selection_pen = QPen(Qt.DashLine)
        selection_pen.setWidthF(pen_width)
        self._selection_halo.setPen(selection_pen)

    def finalize(self, name, x, y):
        """Names the icon and moves it by a given amount.

        Args:
            name (str): icon's name
            x (int): horizontal offset
            y (int): vertical offset
        """
        self.moveBy(x, y)
        self.update_name_item(name)

    def _setup(self):
        """Sets up item attributes."""
        self.colorizer.setColor(self._icon_color)
        background_color = fix_lightness_color(self._icon_color)
        gradient = QRadialGradient(self._rect.center(), 1 * self._rect.width())
        gradient.setColorAt(0, background_color.lighter(105))
        gradient.setColorAt(1, background_color.darker(105))
        brush = QBrush(gradient)
        pen = QPen(QBrush(background_color.darker()), 1, Qt.SolidLine)
        self.setPen(pen)
        for conn in self.connectors.values():
            conn.setPen(pen)
        self.rank_icon.bg.setPen(pen)
        self.setBrush(brush)
        # Load SVG
        loading_ok = self.renderer.load(self.icon_file)
        if not loading_ok:
            self._toolbox.msg_error.emit("Loading SVG icon from resource:{0} failed".format(self.icon_file))
            return
        size = self.renderer.defaultSize()
        self.svg_item.setSharedRenderer(self.renderer)
        self.svg_item.setElementId("")  # guess empty string loads the whole file
        dim_max = max(size.width(), size.height())
        rect_w = self.rect().width()  # Parent rect width
        margin = 32
        self.svg_item.setScale((rect_w - margin) / dim_max)
        self.svg_item.setPos(self.rect().center() - self.svg_item.sceneBoundingRect().center())
        self.svg_item.setGraphicsEffect(self.colorizer)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        # Set exclamation, execution_log, and rank icons position
        self.exclamation_icon.setPos(self.rect().topRight() - self.exclamation_icon.sceneBoundingRect().topRight())
        self.execution_icon.setPos(
            self.rect().bottomRight() - 0.5 * self.execution_icon.sceneBoundingRect().bottomRight()
        )
        self.rank_icon.setPos(self.rect().topLeft())

    def name(self):
        """Returns name of the item that is represented by this icon.

        Returns:
            str: icon's name
        """
        return self._name

    def update_name_item(self, new_name):
        """Sets a new text to name item.

        Args:
            new_name (str): icon's name
        """
        self._name = new_name
        self.name_item.setPlainText(new_name)
        self._reposition_name_item()
        self.name_item.setTextWidth(100)

    def set_name_attributes(self):
        """Sets name item attributes (font, size, style, alignment)."""
        font = self.name_item.font()
        font.setPixelSize(self.FONT_SIZE_PIXELS)
        font.setBold(True)
        self.name_item.setFont(font)
        option = self.name_item.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_item.document().setDefaultTextOption(option)

    def _reposition_name_item(self):
        """Sets name item position (centered on top of the master icon)."""
        main_rect = self.sceneBoundingRect()
        name_rect = self.name_item.sceneBoundingRect()
        self.name_item.setPos(main_rect.center().x() - name_rect.width() / 2, main_rect.y() - name_rect.height() - 4)

    def conn_button(self, position="left"):
        """Returns item's connector button.

        Args:
            position (str): "left", "right" or "bottom"

        Returns:
            QWidget: connector button
        """
        return self.connectors.get(position, self.connectors["left"])

    def outgoing_connection_links(self):
        """Collects outgoing connection links.

        Returns:
            list of LinkBase: outgoing links
        """
        return [l for conn in self.connectors.values() for l in conn.outgoing_links()]

    def incoming_links(self):
        """Collects incoming connection links.

        Returns:
            list of LinkBase: outgoing links
        """
        return [l for conn in self.connectors.values() for l in conn.incoming_links()]

    def _closest_connector(self, pos):
        """Returns the closest connector button to given scene pos."""
        connectors = list(self.connectors.values())
        distances = [(pos - connector.sceneBoundingRect().center()).manhattanLength() for connector in connectors]
        index_min = min(range(len(distances)), key=distances.__getitem__)
        return connectors[index_min]

    def _update_link_drawer_destination(self, pos=None):
        """Updates link drawer destination. If pos is None, then the link drawer would have no destination.
        Otherwise, the destination would be the connector button closest to pos.
        """
        link_drawer = self.scene().link_drawer
        if link_drawer is not None:
            if link_drawer.dst_connector is not None:
                link_drawer.dst_connector.set_normal_brush()
            if pos is not None:
                link_drawer.dst_connector = self._closest_connector(pos)
                link_drawer.dst_connector.set_hover_brush()
            else:
                link_drawer.dst_connector = None
            link_drawer.update_geometry()

    def hoverEnterEvent(self, event):
        """Sets a drop shadow effect to icon when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(True)
        event.accept()
        self._update_link_drawer_destination(event.scenePos())

    def hoverMoveEvent(self, event):
        event.accept()
        self._update_link_drawer_destination(event.scenePos())

    def hoverLeaveEvent(self, event):
        """Disables the drop shadow when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(False)
        event.accept()
        self._update_link_drawer_destination()

    def mousePressEvent(self, event):
        """Updates scene's icon group."""
        super().mousePressEvent(event)
        icon_group = set(x for x in self.scene().selectedItems() if isinstance(x, ProjectItemIcon)) | {self}
        for icon in icon_group:
            icon.previous_pos = icon.scenePos()
        self.scene().icon_group = icon_group

    def update_links_geometry(self):
        """Updates geometry of connected links to reflect this item's most recent position."""
        scene = self.scene()
        if not scene:
            return
        icon_group = scene.icon_group | {self}
        scene.dirty_links |= set(
            link for icon in icon_group for conn in icon.connectors.values() for link in conn.links
        )

    def mouseReleaseEvent(self, event):
        """Clears pre-bump rects, and pushes a move icon command if necessary."""
        for icon in self.scene().icon_group:
            icon.bumped_rects.clear()
        # pylint: disable=undefined-variable
        if (self.scenePos() - self.previous_pos).manhattanLength() > qApp.startDragDistance():
            self._toolbox.undo_stack.push(MoveIconCommand(self, self._toolbox.project()))
            event.ignore()
        super().mouseReleaseEvent(event)

    def notify_item_move(self):
        if self._moved_on_scene:
            self._moved_on_scene = False
            scene = self.scene()
            scene.item_move_finished.emit(self)

    def contextMenuEvent(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        event.accept()
        self.scene().clearSelection()
        self.setSelected(True)
        item = self._toolbox.project().get_item(self.name())
        self._toolbox.show_project_or_item_context_menu(event.screenPos(), item)

    def itemChange(self, change, value):
        """
        Reacts to item removal and position changes.

        In particular, destroys the drop shadow effect when the item is removed from a scene
        and keeps track of item's movements on the scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
             Whatever super() does with the value parameter
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
            self._reposition_name_item()
            self.update_links_geometry()
            self._handle_collisions()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            self.prepareGeometryChange()
            self.setGraphicsEffect(None)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            scene = value
            if scene is None:
                self._scene.removeItem(self.name_item)
            else:
                self._scene = scene
                self._scene.addItem(self.name_item)
                self._reposition_name_item()
        return super().itemChange(change, value)

    def set_pos_without_bumping(self, pos):
        """Sets position without bumping other items. Needed for undoing move operations.

        Args:
            pos (QPointF)
        """
        self._bumping = False
        self.setPos(pos)
        self._bumping = True

    def _handle_collisions(self):
        """Handles collisions with other items."""
        prevent_overlapping = self._toolbox.qsettings().value("appSettings/preventOverlapping", defaultValue="false")
        if not self.scene() or not self._bumping or prevent_overlapping != "true":
            return
        restablished = self._restablish_bumped_items()
        for other in set(self.collidingItems()) - restablished:
            if isinstance(other, ProjectItemIcon):
                other.make_room_for_item(self)

    def make_room_for_item(self, other):
        """Makes room for another item.

        Args:
            item (ProjectItemIcon)
        """
        if self not in other.bumped_rects:
            other.bumped_rects[self] = self.sceneBoundingRect()
            if self not in self.scene().icon_group:
                self.scene().icon_group.add(self)
                self.previous_pos = self.scenePos()
        line = QLineF(other.sceneBoundingRect().center(), self.sceneBoundingRect().center())
        intersection = other.sceneBoundingRect() & self.sceneBoundingRect()
        delta = math.atan(line.angle()) * min(intersection.width(), intersection.height())
        unit_vector = line.unitVector()
        self.moveBy(delta * unit_vector.dx(), delta * unit_vector.dy())

    def _restablish_bumped_items(self):
        """Moves bumped items back to their original position if no collision would happen anymore."""
        restablished = set()
        try:
            for other, rect in self.bumped_rects.items():
                if not self.sceneBoundingRect().intersects(rect):
                    other.setPos(rect.center())
                    restablished.add(other)
            for other in restablished:
                self.bumped_rects.pop(other, None)
        except RuntimeError:
            pass
        return restablished

    def paint(self, painter, option, widget=None):
        """Sets a dashed pen if selected."""
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        self._selection_halo.setVisible(selected)
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)


class ConnectorButton(QGraphicsPathItem):
    """Connector button graphics item. Used for Link drawing between project items."""

    # Regular and hover brushes
    brush = QBrush(QColor(255, 255, 255))  # Used in filling the item
    hover_brush = QBrush(QColor(50, 0, 50, 128))  # Used in filling the item while hovering

    def __init__(self, toolbox, parent, position="left"):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            parent (ProjectItemIcon): parent graphics item
            position (str): Either "top", "left", "bottom", or "right"
        """
        super().__init__(parent)
        self._parent = parent
        self._toolbox = toolbox
        self.position = position
        self.links = list()
        self.setBrush(self.brush)
        parent_rect = parent.rect()
        extent = 0.2 * parent_rect.width()
        self._rect = QRectF(0, 0, extent, extent)
        if position == "top":
            self._rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.top() + extent / 2))
        elif position == "left":
            self._rect.moveCenter(QPointF(parent_rect.left() + extent / 2, parent_rect.center().y()))
        elif position == "bottom":
            self._rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.bottom() - extent / 2))
        elif position == "right":
            self._rect.moveCenter(QPointF(parent_rect.right() - extent / 2, parent_rect.center().y()))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def rect(self):
        return self._rect

    def update_path(self, parent_radius):
        radius = 0.2 * parent_radius
        path = QPainterPath()
        path.addRoundedRect(self._rect, radius, radius)
        self.setPath(path)

    @property
    def parent(self):
        return self._parent

    def outgoing_links(self):
        return [l for l in self.links if l.src_connector == self]

    def incoming_links(self):
        return [l for l in self.links if l.dst_connector == self]

    def parent_name(self):
        """Returns project item name owning this connector button."""
        return self._parent.name()

    def project_item(self):
        """Returns the project item this connector button is attached to.

        Returns:
            ProjectItem: project item
        """
        return self._toolbox.project().get_item(self._parent.name())

    def mousePressEvent(self, event):
        """Connector button mouse press event.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if event.button() != Qt.LeftButton:
            event.accept()
            return
        self._start_link(event)

    def _start_link(self, event):
        scene = self.scene()
        if scene.link_drawer is None:
            scene.select_link_drawer(LinkType.JUMP if event.modifiers() & Qt.AltModifier else LinkType.CONNECTION)
            scene.link_drawer.wake_up(self)

    def set_friend_connectors_enabled(self, enabled):
        """Enables or disables all connectors in the parent.

        This is called by LinkDrawer to disable invalid connectors while drawing and reenabling them back when done.

        Args:
            enabled (bool): True to enable connectors, False to disable
        """
        for conn in self._parent.connectors.values():
            conn.setEnabled(enabled)
            conn.setBrush(conn.brush)  # Remove hover brush from src connector that was clicked

    def set_hover_brush(self):
        self.setBrush(self.hover_brush)

    def set_normal_brush(self):
        self.setBrush(self.brush)

    def hoverEnterEvent(self, event):
        """Sets a darker shade to connector button when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.set_hover_brush()

    def hoverLeaveEvent(self, event):
        """Restore original brush when mouse leaves connector button boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.set_normal_brush()

    def itemChange(self, change, value):
        """If this is being removed from the scene while it's the origin of the link drawer,
        put the latter to sleep."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            link_drawer = self.scene().link_drawer
            if link_drawer is not None and link_drawer.src_connector is self:
                link_drawer.sleep()
        return super().itemChange(change, value)


class ExecutionIcon(QGraphicsEllipseItem):
    """An icon to show information about the item's execution."""

    _CHECK = "\uf00c"  # Success
    _CROSS = "\uf00d"  # Fail
    _CLOCK = "\uf017"  # Waiting
    _SKIP = "\uf054"  # Excluded

    def __init__(self, parent):
        """
        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__(parent)
        self._parent = parent
        self._execution_state = "not started"
        self._text_item = QGraphicsTextItem(self)
        font = QFont("Font Awesome 5 Free Solid")
        self._text_item.setFont(font)
        parent_rect = parent.rect()
        self.setRect(0, 0, 0.5 * parent_rect.width(), 0.5 * parent_rect.height())
        self.setPen(Qt.NoPen)
        # pylint: disable=undefined-variable
        self.normal_brush = qApp.palette().window()
        self.selected_brush = qApp.palette().highlight()
        self.setBrush(self.normal_brush)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.hide()

    def item_name(self):
        return self._parent.name()

    def _repaint(self, text, color):
        self._text_item.prepareGeometryChange()
        self._text_item.setPos(0, 0)
        self._text_item.setPlainText(text)
        self._text_item.setDefaultTextColor(color)
        size = self._text_item.boundingRect().size()
        dim_max = max(size.width(), size.height())
        rect_w = self.rect().width()
        self._text_item.setScale(rect_w / dim_max)
        self._text_item.setPos(self.sceneBoundingRect().center() - self._text_item.sceneBoundingRect().center())
        self.show()

    def mark_execution_waiting(self):
        self._execution_state = "waiting for dependencies"
        self._repaint(self._CLOCK, QColor("orange"))

    def mark_execution_ignored(self):
        self._execution_state = "not started"
        self.hide()

    def mark_execution_started(self):
        self._execution_state = "in progress"
        self._repaint(self._CHECK, QColor("orange"))

    def mark_execution_finished(self, item_finish_state):
        if item_finish_state == ItemExecutionFinishState.SUCCESS:
            self._execution_state = "completed"
            self._repaint(self._CHECK, QColor("green"))
        elif item_finish_state == ItemExecutionFinishState.EXCLUDED:
            self._execution_state = "excluded"
            self._repaint(self._CHECK, QColor("orange"))
        elif item_finish_state == ItemExecutionFinishState.SKIPPED:
            self._execution_state = "skipped"
            self._repaint(self._SKIP, QColor("chocolate"))
        else:
            self._execution_state = "failed"
            self._repaint(self._CROSS, QColor("red"))

    def hoverEnterEvent(self, event):
        tip = f"<p><b>Execution {self._execution_state}</b>. Select this item to see Console and Log messages.</p>"
        QToolTip.showText(event.screenPos(), tip)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()


class ExclamationIcon(QGraphicsTextItem):
    """An icon to notify that a ProjectItem is missing some configuration."""

    FONT_SIZE_PIXELS = 14  # Use pixel size to prevent scaling by system.

    def __init__(self, parent):
        """
        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__(parent)
        self._parent = parent
        self._notifications = list()
        font = QFont("Font Awesome 5 Free Solid")
        font.setPixelSize(self.FONT_SIZE_PIXELS)
        self.setFont(font)
        self.setDefaultTextColor(QColor("red"))
        self.setPlainText("\uf06a")
        doc = self.document()
        doc.setDocumentMargin(0)
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

    def remove_notification(self, subtext):
        """Remove the first notification that includes given subtext."""
        k = next((i for i, text in enumerate(self._notifications) if subtext in text), None)
        if k is not None:
            self._notifications.pop(k)
            if not self._notifications:
                self.hide()

    def hoverEnterEvent(self, event):
        """Shows notifications as tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if not self._notifications:
            return
        tip = "<p>" + "<p>".join(self._notifications)
        QToolTip.showText(event.screenPos(), tip)

    def hoverLeaveEvent(self, event):
        """Hides tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        QToolTip.hideText()


class RankIcon(QGraphicsTextItem):
    """An icon to show the rank of a ProjectItem within its DAG."""

    def __init__(self, parent):
        """
        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__(parent)
        self._parent = parent
        self._rect = parent.component_rect
        self.bg = QGraphicsPathItem(self)
        bg_brush = QBrush(QColor(Qt.GlobalColor.white))
        self.bg.setBrush(bg_brush)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        font = self.font()
        font.setPixelSize(parent.FONT_SIZE_PIXELS)
        font.setBold(True)
        self.setFont(font)
        doc = self.document()
        doc.setDocumentMargin(0)

    def _make_path(self, radius):
        path = QPainterPath()
        if radius == 0:
            path.addRect(self._rect)
            return path
        path.moveTo(0, self._rect.height())
        path.lineTo(0.5 * self._rect.width(), self._rect.height())
        path.arcTo(self._rect, 270, 90)
        path.lineTo(self._rect.width(), 0)
        path.lineTo(0.5 * self._rect.width(), 0)
        path.arcTo(self._rect, 90, 90)
        path.lineTo(0, self._rect.height())
        return path

    def update_path(self, radius):
        path = self._make_path(radius)
        self.bg.setPath(path)

    def set_rank(self, rank):
        self.setPlainText(str(rank))
        self.setTextWidth(self._rect.width())
        # Align center
        fmt = QTextBlockFormat()
        fmt.setAlignment(Qt.AlignHCenter)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(fmt)
        cursor.clearSelection()
        self.setTextCursor(cursor)
