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

"""Custom QGraphicsScene used in the Design View."""
import math
from PySide6.QtCore import Qt, Signal, Slot, QPointF, QEvent, QTimer
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene
from PySide6.QtGui import QColor, QPen, QBrush
from ..project_item_icon import ProjectItemIcon
from ..ui.resources.cat import Cat
from ..link import JumpLink, JumpLinkDrawer, Link, ConnectionLinkDrawer
from ..helpers import LinkType
from .project_item_drag import ProjectItemDragMixin


class CustomGraphicsScene(QGraphicsScene):
    """
    A custom QGraphicsScene. It provides signals to notify about items,
    and a method to center all items in the scene.

    At the moment it's used by DesignGraphicsScene and the GraphViewMixin
    """

    item_move_finished = Signal(QGraphicsItem)
    """Emitted when an item has finished moving."""

    def center_items(self):
        """Centers toplevel items in the scene."""
        self.setSceneRect(self.itemsBoundingRect())


class DesignGraphicsScene(CustomGraphicsScene):
    """A scene for the Design view.

    Mainly, it handles drag and drop events of ProjectItemDragMixin sources.
    """

    link_about_to_be_drawn = Signal()
    link_drawing_finished = Signal()

    def __init__(self, parent, toolbox):
        """
        Args:
            parent (QObject): scene's parent object
            toolbox (ToolboxUI): reference to the main window
        """
        super().__init__(parent)
        self._toolbox = toolbox
        self.item_shadow = None
        self._last_selected_items = set()
        # Set background attributes
        settings = toolbox.qsettings()
        self.bg_choice = settings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = settings.value("appSettings/bgColor", defaultValue="false")
        self.bg_color = QColor("#f5f5f5") if bg_color == "false" else bg_color
        self._connection_drawer = ConnectionLinkDrawer(toolbox)
        self._connection_drawer.hide()
        self._jump_drawer = JumpLinkDrawer(toolbox)
        self._jump_drawer.hide()
        self.link_drawer = None
        self.icon_group = set()  # Group of project item icons that are moving together
        self.dirty_links = set()
        self._timer = QTimer(self)
        self._timer.setInterval(5)
        self._timer.timeout.connect(self._handle_timeout)
        self._timer.start()
        self._cat = Cat(self)
        self.connect_signals()

    @Slot()
    def _handle_timeout(self):
        for link in self.dirty_links:
            link.update_geometry()
        self.dirty_links.clear()

    def clear_icons_and_links(self):
        for item in self.items():
            if isinstance(item, (Link, JumpLink, ProjectItemIcon)):
                self.removeItem(item)

    def mouseMoveEvent(self, event):
        """Moves link drawer."""
        if self.link_drawer is not None:
            self.link_drawer.tip = event.scenePos()
            self.link_drawer.update_geometry()
            event.setButtons(Qt.NoButton)  # this is so super().mouseMoveEvent sends hover events to connector buttons
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Puts link drawer to sleep and logs message if it looks like the user doesn't know what they're doing."""
        if self.link_drawer is not None:
            if event.button() == Qt.MouseButton.RightButton:
                return
            if (
                self._toolbox.qsettings().value("appSettings/dragToDrawLinks", defaultValue="false") == "false"
                and event.button() == Qt.MouseButton.LeftButton
                and self._finish_link()
            ):
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Makes link if drawer is released over a valid connector button or cancel link drawing on right button."""
        if self.link_drawer is not None:
            if event.button() == Qt.MouseButton.RightButton:
                self.link_drawer.sleep()
                event.accept()
                return
            if (
                self._toolbox.qsettings().value("appSettings/dragToDrawLinks", defaultValue="false") == "true"
                and event.button() == Qt.MouseButton.LeftButton
                and self._finish_link()
            ):
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def _finish_link(self):
        if self.link_drawer.src_connector.isUnderMouse():
            self.link_drawer.sleep()
            return False
        if self.link_drawer.dst_connector is None:
            self.link_drawer.sleep()
            self.emit_connection_failed()
            return False
        if self.link_drawer.src_connector == self.link_drawer.dst_connector:
            self.link_drawer.sleep()
            return False
        self.link_drawer.dst_connector.set_normal_brush()
        self.link_drawer.add_link()
        return True

    def emit_connection_failed(self):
        self._toolbox.msg_warning.emit(
            "Unable to make connection. Try landing the connection onto a valid connector button."
        )

    def keyPressEvent(self, event):
        """Puts link drawer to sleep if user presses ESC."""
        super().keyPressEvent(event)
        if self.link_drawer is not None and event.key() == Qt.Key_Escape:
            self.link_drawer.sleep()

    def connect_signals(self):
        """Connect scene signals."""
        self.selectionChanged.connect(self.handle_selection_changed)

    def project_item_icons(self):
        return [item for item in self.items() if isinstance(item, ProjectItemIcon)]

    @Slot()
    def handle_selection_changed(self):
        """Activates items or links based on currently selected items (or links)."""
        selected_items = set(self.selectedItems())
        if self._last_selected_items == selected_items:
            return
        self._last_selected_items = selected_items
        project_item_icons = []
        links = []
        for item in self.selectedItems():
            if isinstance(item, ProjectItemIcon):
                project_item_icons.append(item)
            elif isinstance(item, (Link, JumpLink)):
                links.append(item)
        # Set active project item and active link in toolbox
        active_project_item = (
            self._toolbox.project().get_item(project_item_icons[0].name()) if len(project_item_icons) == 1 else None
        )
        active_link_item = links[0].item if len(links) == 1 else None
        selected_item_names = {icon.name() for icon in project_item_icons}
        selected_link_icons = [conn.parent for link in links for conn in (link.src_connector, link.dst_connector)]
        selected_item_names |= set(icon.name() for icon in selected_link_icons)
        self._toolbox.refresh_active_elements(active_project_item, active_link_item, selected_item_names)
        self._toolbox.override_console_and_execution_list()

    def set_bg_color(self, color):
        """Change background color when this is changed in Settings.

        Args:
            color (QColor): Background color
        """
        self.bg_color = color

    def set_bg_choice(self, bg_choice):
        """Set background choice when this is changed in Settings.

        Args:
            bg (str): "grid", "tree", or "solid"
        """
        self.bg_choice = bg_choice

    def dragLeaveEvent(self, event):
        """Accepts event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemDragMixin."""
        source = event.source()
        event.setAccepted(isinstance(source, ProjectItemDragMixin))

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemDragMixin."""
        source = event.source()
        event.setAccepted(isinstance(source, ProjectItemDragMixin))

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of ProjectItemDragMixin.
        Capture text from event's mimedata and show the appropriate 'Add Item form.'
        """
        source = event.source()
        if not isinstance(source, ProjectItemDragMixin):
            return
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please open or create a project first")
            event.ignore()
            return
        event.acceptProposedAction()
        item_type, spec = event.mimeData().text().split(",")
        pos = event.scenePos()
        x = pos.x()
        y = pos.y()
        factory = self._toolbox.item_factories[item_type]
        self.item_shadow = factory.make_icon(self._toolbox)
        self.item_shadow.finalize("", x, y)
        self.addItem(self.item_shadow)
        self._toolbox.show_add_project_item_form(item_type, x, y, spec=spec)

    def event(self, event):
        """Accepts GraphicsSceneHelp events without doing anything, to not interfere with our usage of
        QToolTip.showText in graphics_items.ExclamationIcon.
        """
        if event.type() == QEvent.GraphicsSceneHelp:
            event.accept()
            return True
        return super().event(event)

    def drawBackground(self, painter, rect):
        """Reimplemented method to make a custom background.

        Args:
            painter (QPainter): Painter that is used to paint background
            rect (QRectF): The exposed (viewport) rectangle in scene coordinates
        """
        {"solid": self._draw_solid_bg, "grid": self._draw_grid_bg, "tree": self._draw_tree_bg}.get(
            self.bg_choice, self._draw_solid_bg
        )(painter, rect)

    def _draw_solid_bg(self, painter, rect):
        """Draws solid bg."""
        painter.fillRect(rect, QBrush(self.bg_color))

    def _draw_grid_bg(self, painter, rect):
        """Draws grid bg."""
        step = round(ProjectItemIcon.ITEM_EXTENT / 3)  # Grid step
        painter.setPen(QPen(self.bg_color))
        top_left = rect.topLeft()
        x_start = round(top_left.x() / step)
        y_start = round(top_left.y() / step)
        x_stop = x_start + round(rect.width() / step) + 1
        y_stop = y_start + round(rect.height() / step) + 1
        x_ticks = [step * i for i in range(x_start, x_stop)]
        y_ticks = [step * i for i in range(y_start, y_stop)]
        x_zero = next((x for x in x_ticks if abs(x) < step), None)
        y_zero = next((y for y in y_ticks if abs(y) < step), None)
        for x in x_ticks:
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in y_ticks:
            painter.drawLine(rect.left(), y, rect.right(), y)
        painter.setPen(QPen(self.bg_color.darker(110)))
        if x_zero is not None:
            painter.drawLine(x_zero, rect.top(), x_zero, rect.bottom())
        if y_zero is not None:
            painter.drawLine(rect.left(), y_zero, rect.right(), y_zero)

    def _draw_tree_bg(self, painter, rect):
        """Draws 'tree of life' bg."""
        painter.setPen(QPen(self.bg_color))
        radius = ProjectItemIcon.ITEM_EXTENT
        dx = math.sin(math.pi / 3) * radius
        dy = math.cos(math.pi / 3) * radius
        top_left = rect.topLeft()
        x_start = round(top_left.x() / dx)
        y_start = round(top_left.y() / radius)
        x_stop = x_start + round(rect.width() / dx) + 1
        y_stop = y_start + round(rect.height() / radius) + 1
        centers = list()
        centers_append = centers.append
        for i in range(x_start, x_stop):
            ref = QPointF(i * dx, (i & 1) * dy)
            for j in range(y_start, y_stop):
                center = ref + QPointF(0, j * radius)
                centers_append(center)
        for center in centers:
            painter.drawEllipse(center, radius, radius)
        center = next((c for c in centers if (c - QPointF(0, 0)).manhattanLength() < radius), None)
        if center is not None:
            painter.setPen(QPen(self.bg_color.darker(110)))
            painter.drawEllipse(center, 2 * radius, 2 * radius)

    def select_link_drawer(self, drawer_type):
        """Selects current link drawer.

        Args:
            drawer_type (LinkType): selected link drawer's type
        """
        self.link_drawer = self._connection_drawer if drawer_type == LinkType.CONNECTION else self._jump_drawer
