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

"""Classes for custom QGraphicsViews for the Design and Graph views."""
import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QContextMenuEvent, QCursor, QMouseEvent
from PySide6.QtCore import QTimer, Slot, Qt, QTimeLine, QRectF
from ..project_item_icon import ProjectItemIcon
from ..project_commands import AddConnectionCommand, AddJumpCommand, RemoveConnectionsCommand, RemoveJumpsCommand
from ..link import Link, JumpLink
from ..helpers import LinkType
from .custom_qgraphicsscene import DesignGraphicsScene


class CustomQGraphicsView(QGraphicsView):
    """Super class for Design and Entity QGraphicsViews."""

    DRAG_MIN_DURATION = 150

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._zoom_factor_base = 1.0015
        self._angle = 120
        self._scheduled_transformations = 0
        self.time_line = None
        self._items_fitting_zoom = 1.0
        self._max_zoom = 10.0
        self._min_zoom = 0.1
        self._previous_mouse_pos = None
        self._last_right_mouse_press = None
        self._enabled_context_menu_policy = self.contextMenuPolicy()

    @property
    def _qsettings(self):
        raise NotImplementedError()

    @property
    def zoom_factor(self):
        return self.transform().m11()  # The [1, 1] element contains the x scaling factor

    def reset_zoom(self):
        """Resets zoom to the default factor."""
        self.scene().center_items()
        self._update_zoom_limits()
        self._zoom(self._items_fitting_zoom)
        self._set_preferred_scene_rect()

    def keyPressEvent(self, event):
        """Enables zooming with plus and minus keys (comma resets zoom).

        Args:
            event (QKeyEvent): key press event
        """
        if event.key() == Qt.Key_Plus:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_Comma:
            self.reset_zoom()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Sets rubber band selection mode if Control or right mouse button is pressed.
        Enables resetting the zoom factor from the middle mouse button.
        """
        self._previous_mouse_pos = event.position().toPoint()
        item = self.itemAt(event.position().toPoint())
        if not item or not item.acceptedMouseButtons() & event.buttons():
            button = event.button()
            if button == Qt.MouseButton.LeftButton:
                self.viewport().setCursor(Qt.CrossCursor)
            elif button == Qt.MouseButton.MiddleButton:
                self.reset_zoom()
            if button == Qt.MouseButton.RightButton:
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                self._last_right_mouse_press = event.timestamp()
                event = _fake_left_button_event(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.RightButton == Qt.MouseButton.RightButton
            and self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag
            and self._drag_duration_passed(event)
        ):
            if self._previous_mouse_pos is not None:
                delta = event.position().toPoint() - self._previous_mouse_pos
                self._scroll_scene_by(delta.x(), delta.y())
            self._previous_mouse_pos = event.position().toPoint()
            event = _fake_left_button_event(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        context_menu_disabled = False
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            if self._drag_duration_passed(event):
                context_menu_disabled = True
                self.disable_context_menu()
            else:
                self.contextMenuEvent(
                    QContextMenuEvent(QContextMenuEvent.Reason.Mouse, event.pos(), event.globalPos(), event.modifiers())
                )
            event = _fake_left_button_event(event)
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._previous_mouse_pos = None
        self._last_right_mouse_press = None
        if context_menu_disabled:
            self.enable_context_menu()
        item = next(iter([x for x in self.items(event.position().toPoint()) if x.hasCursor()]), None)
        if item:
            self.viewport().setCursor(item.cursor())
        else:
            self.viewport().setCursor(Qt.ArrowCursor)

    def _scroll_scene_by(self, dx, dy):
        if dx == dy == 0:
            return
        scene_rect = self.sceneRect()
        view_scene_rect = self.mapFromScene(scene_rect).boundingRect()
        view_rect = self.viewport().rect()
        scene_dx = abs((self.mapToScene(0, 0) - self.mapToScene(dx, 0)).x())
        scene_dy = abs((self.mapToScene(0, 0) - self.mapToScene(0, dy)).y())
        if dx < 0 and view_rect.right() - dx >= view_scene_rect.right():
            scene_rect.adjust(0, 0, scene_dx, 0)
        elif dx > 0 and view_rect.left() - dx <= view_scene_rect.left():
            scene_rect.adjust(-scene_dx, 0, 0, 0)
        if dy < 0 and view_rect.bottom() - dy >= view_scene_rect.bottom():
            scene_rect.adjust(0, 0, 0, scene_dy)
        elif dy > 0 and view_rect.top() - dy <= view_scene_rect.top():
            scene_rect.adjust(0, -scene_dy, 0, 0)
        self.scene().setSceneRect(scene_rect)

    def _use_smooth_zoom(self):
        return self._qsettings.value("appSettings/smoothZoom", defaultValue="false") == "true"

    def _drag_duration_passed(self, mouse_event):
        """Test is drag duration has passed.

        Args:
            mouse_event (QMouseEvent): current mouse event
        """
        return (
            mouse_event.timestamp() - self._last_right_mouse_press > self.DRAG_MIN_DURATION
            if self._last_right_mouse_press is not None
            else False
        )

    def wheelEvent(self, event):
        """Zooms in/out.

        Args:
            event (QWheelEvent): Mouse wheel event
        """
        if event.angleDelta().x() != 0:
            event.ignore()
            return
        event.accept()
        if self._use_smooth_zoom():
            angle = event.angleDelta().y() / 8
            steps = angle / 15
            self._scheduled_transformations += steps
            if self._scheduled_transformations * steps < 0:
                self._scheduled_transformations = steps
            if self.time_line:
                self.time_line.deleteLater()
            self.time_line = QTimeLine(200, self)
            self.time_line.setUpdateInterval(20)
            self.time_line.valueChanged.connect(
                lambda x, pos=event.position().toPoint(): self._handle_zoom_time_line_advanced(pos)
            )
            self.time_line.finished.connect(self._handle_transformation_time_line_finished)
            self.time_line.start()
        else:
            angle = event.angleDelta().y()
            factor = self._zoom_factor_base ** angle
            self.gentle_zoom(factor, event.position().toPoint())
            self._set_preferred_scene_rect()

    def resizeEvent(self, event):
        """
        Updates zoom if needed when the view is resized.

        Args:
            event (QResizeEvent): a resize event
        """
        new_size = self.size()
        old_size = event.oldSize()
        if new_size != old_size:
            scene = self.scene()
            if scene is not None:
                self._update_zoom_limits()
                if self.time_line:
                    self.time_line.deleteLater()
                self.time_line = QTimeLine(200, self)
                self.time_line.finished.connect(self._handle_resize_time_line_finished)
                self.time_line.start()
        super().resizeEvent(event)

    def setScene(self, scene):
        """
        Sets a new scene to this view.

        Args:
            scene (DesignGraphicsScene): a new scene
        """
        super().setScene(scene)
        scene.item_move_finished.connect(self._handle_item_move_finished)
        self.viewport().setCursor(Qt.ArrowCursor)

    @Slot(QGraphicsItem)
    def _handle_item_move_finished(self, item):
        self._ensure_item_visible(item)
        self._update_zoom_limits()

    def _update_zoom_limits(self):
        """
        Updates the minimum zoom limit and the zoom level with which the view fits all the items in the scene.
        """
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        viewport_scene_rect = self._get_viewport_scene_rect()
        x_factor = viewport_scene_rect.width() / rect.width()
        y_factor = viewport_scene_rect.height() / rect.height()
        self._items_fitting_zoom = 0.9 * min(x_factor, y_factor)
        self._min_zoom = 0.5 * self.zoom_factor * self._items_fitting_zoom
        self._max_zoom = self._compute_max_zoom()

    def _compute_max_zoom(self):
        raise NotImplementedError()

    def _handle_zoom_time_line_advanced(self, pos):
        """Performs zoom whenever the smooth zoom time line advances."""
        factor = 1.0 + self._scheduled_transformations / 100.0
        self.gentle_zoom(factor, pos)

    @Slot()
    def _handle_transformation_time_line_finished(self):
        """Cleans up after the smooth transformation time line finishes."""
        if self._scheduled_transformations > 0:
            self._scheduled_transformations -= 1
        else:
            self._scheduled_transformations += 1
        if self.sender():
            self.sender().deleteLater()
        self.time_line = None
        self._set_preferred_scene_rect()

    @Slot()
    def _handle_resize_time_line_finished(self):
        """Cleans up after resizing time line finishes."""
        if self.sender():
            self.sender().deleteLater()
        self.time_line = None
        self._set_preferred_scene_rect()

    def zoom_in(self):
        """Perform a zoom in with a fixed scaling."""
        self.gentle_zoom(self._zoom_factor_base ** self._angle)
        self._set_preferred_scene_rect()

    def zoom_out(self):
        """Perform a zoom out with a fixed scaling."""
        self.gentle_zoom(self._zoom_factor_base ** -self._angle)
        self._set_preferred_scene_rect()

    def gentle_zoom(self, factor, zoom_focus=None):
        """
        Perform a zoom by a given factor.

        Args:
            factor (float): a scaling factor relative to the current scene scaling
            zoom_focus (QPoint): focus of the zoom, e.g. mouse pointer position
        """
        if zoom_focus is None:
            zoom_focus = self.viewport().rect().center()
        initial_focus_on_scene = self.mapToScene(zoom_focus)
        current_zoom = self.zoom_factor
        proposed_zoom = current_zoom * factor
        if proposed_zoom < self._min_zoom:
            factor = self._min_zoom / current_zoom
        elif proposed_zoom > self._max_zoom:
            factor = self._max_zoom / current_zoom
        if math.isclose(factor, 1.0):
            return
        self._zoom(factor)
        post_scaling_focus_on_scene = self.mapToScene(zoom_focus)
        center_on_scene = self.mapToScene(self.viewport().rect().center())
        focus_diff = post_scaling_focus_on_scene - initial_focus_on_scene
        self.centerOn(center_on_scene - focus_diff)

    def _zoom(self, factor):
        self.scale(factor, factor)

    def _get_viewport_scene_rect(self):
        """Returns the viewport rect mapped to the scene.

        Returns:
            QRectF
        """
        rect = self.viewport().rect()
        top_left = self.mapToScene(rect.topLeft())
        bottom_right = self.mapToScene(rect.bottomRight())
        return QRectF(top_left, bottom_right)

    def _ensure_item_visible(self, item):
        """Resets zoom if item is not visible."""
        # Because of zooming, we need to find the item scene's rect as below
        item_scene_rect = item.boundingRegion(item.sceneTransform()).boundingRect()
        viewport_scene_rect = self._get_viewport_scene_rect()
        if not viewport_scene_rect.contains(item_scene_rect.topLeft()):
            scene_rect = viewport_scene_rect.united(item_scene_rect)
            self.fitInView(scene_rect, Qt.KeepAspectRatio)
            self._set_preferred_scene_rect()

    @Slot()
    def _set_preferred_scene_rect(self):
        """Sets the scene rect to the result of uniting the scene viewport rect and the items bounding rect."""
        viewport_scene_rect = self._get_viewport_scene_rect()
        items_scene_rect = self.scene().itemsBoundingRect()
        self.scene().setSceneRect(viewport_scene_rect.united(items_scene_rect))

    @Slot()
    def disable_context_menu(self):
        """Disables the context menu."""
        self._enabled_context_menu_policy = self.contextMenuPolicy()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

    @Slot()
    def enable_context_menu(self):
        """Enables the context menu."""
        # We use timer here to delay setting the policy.
        # Otherwise, using right-click to cancel link drawing would still open the context menu.
        QTimer.singleShot(0, lambda: self.setContextMenuPolicy(self._enabled_context_menu_policy))


class DesignQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Design View."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)
        self._toolbox = None

    @property
    def _qsettings(self):
        return self._toolbox.qsettings()

    def set_ui(self, toolbox):
        """Set a new scene into the Design View when app is started."""
        self._toolbox = toolbox
        scene = DesignGraphicsScene(self, toolbox)
        scene.link_about_to_be_drawn.connect(self.disable_context_menu)
        scene.link_drawing_finished.connect(self.enable_context_menu)
        self.setScene(scene)

    def reset_zoom(self):
        super().reset_zoom()
        extent = ProjectItemIcon.ITEM_EXTENT
        factor = extent / self.mapFromScene(QRectF(0, 0, extent, 0)).boundingRect().width()
        if factor < 1:
            self._zoom(factor)

    def _compute_max_zoom(self):
        # The max zoom is the one that fits one item into the view
        # We don't allow to zoom any further than this
        item = QGraphicsRectItem(0, 0, ProjectItemIcon.ITEM_EXTENT, 0)
        self.scene().addItem(item)
        self.scene().removeItem(item)
        item_scene_rect = item.boundingRegion(item.sceneTransform()).boundingRect()
        item_view_rect = self.mapFromScene(item_scene_rect).boundingRect()
        viewport_extent = min(self.viewport().width(), self.viewport().height())
        return viewport_extent / item_view_rect.width()

    @Slot(str)
    def add_icon(self, item_name):
        """Adds project item's icon to the scene.

        Args:
            item_name (str): project item's name
        """
        project_item = self._toolbox.project().get_item(item_name)
        icon = project_item.get_icon()
        self.scene().addItem(icon)

    @Slot(str)
    def remove_icon(self, item_name):
        """Removes project item's icon from scene.

        Args:
            item_name (str): name of the icon to remove
        """
        icon = self._toolbox.project().get_item(item_name).get_icon()
        scene = self.scene()
        scene.removeItem(icon)
        self._set_preferred_scene_rect()

    def add_link(self, src_connector, dst_connector):
        """
        Pushes an AddLinkCommand to the toolbox undo stack.

        Args:
            src_connector (ConnectorButton): source connector button
            dst_connector (ConnectorButton): destination connector button
        """
        self._toolbox.undo_stack.push(
            AddConnectionCommand(
                self._toolbox.project(),
                src_connector.parent_name(),
                src_connector.position,
                dst_connector.parent_name(),
                dst_connector.position,
            )
        )

    @Slot(object)
    def do_add_link(self, connection):
        """Adds given connection to the Design view.

        Args:
            connection (Connection): the connection to add
        """
        project = self._toolbox.project()
        source_connector = project.get_item(connection.source).get_icon().conn_button(connection.source_position)
        destination_connector = (
            project.get_item(connection.destination).get_icon().conn_button(connection.destination_position)
        )
        connection.link = link = Link(self._toolbox, source_connector, destination_connector, connection)
        source_connector.links.append(link)
        destination_connector.links.append(link)
        self.scene().addItem(link)

    @Slot(object)
    def do_update_link(self, updated_connection):
        """Replaces a link on the Design view.

        Args:
            updated_connection (Connection): connection that was updated
        """
        self.do_remove_link(updated_connection)
        self.do_add_link(updated_connection)

    def remove_links(self, links):
        """Pushes a RemoveConnectionsCommand to the Toolbox undo stack.

        Args:
            links (list of Link): links to remove
        """
        connections = [l.connection for l in links if isinstance(l, Link)]
        jumps = [l.jump for l in links if isinstance(l, JumpLink)]
        self._toolbox.undo_stack.beginMacro("remove links")
        if connections:
            self._toolbox.undo_stack.push(RemoveConnectionsCommand(self._toolbox.project(), connections))
        if jumps:
            self._toolbox.undo_stack.push(RemoveJumpsCommand(self._toolbox.project(), jumps))
        self._toolbox.undo_stack.endMacro()

    @Slot(object)
    def do_remove_link(self, connection):
        """Removes a link from the scene.

        Args:
            connection (ConnectionBase): link's connection
        """
        link = next(
            (
                item
                for item in self.items()
                if isinstance(item, Link)
                and item.src_connector.parent_name() == connection.source
                and item.dst_connector.parent_name() == connection.destination
            ),
            None,
        )
        if link is not None:
            link.scene().removeItem(link)

    def remove_selected_links(self):
        self.remove_links([item for item in self.scene().selectedItems() if isinstance(item, (JumpLink, Link))])

    def take_link(self, link):
        """Remove link, then start drawing another one from the same source connector."""
        self.remove_links([link])
        scene = self.scene()
        scene.select_link_drawer(LinkType.CONNECTION if isinstance(link, Link) else LinkType.JUMP)
        link_drawer = scene.link_drawer
        link_drawer.wake_up(link.src_connector)
        # noinspection PyArgumentList
        link_drawer.tip = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        link_drawer.update_geometry()

    def add_jump(self, src_connector, dst_connector):
        """
        Pushes an AddJumpCommand to the Toolbox undo stack.

        Args:
            src_connector (ConnectorButton): source connector button
            dst_connector (ConnectorButton): destination connector button
        """
        self._toolbox.undo_stack.push(
            AddJumpCommand(
                self._toolbox.project(),
                src_connector.parent_name(),
                src_connector.position,
                dst_connector.parent_name(),
                dst_connector.position,
            )
        )

    @Slot(object)
    def do_add_jump(self, jump):
        """Adds given jump to the Design view.

        Args:
            jump (Jump): jump to add
        """
        project = self._toolbox.project()
        source_connector = project.get_item(jump.source).get_icon().conn_button(jump.source_position)
        destination_connector = project.get_item(jump.destination).get_icon().conn_button(jump.destination_position)
        jump.jump_link = jump_link = JumpLink(self._toolbox, source_connector, destination_connector, jump)
        source_connector.links.append(jump_link)
        destination_connector.links.append(jump_link)
        self.scene().addItem(jump_link)

    @Slot(object)
    def do_update_jump(self, updated_jump):
        """Replaces a jump link on the Design view.

        Args:
            updated_jump (Jump): jump that was updated
        """
        self.do_remove_jump(updated_jump)
        self.do_add_jump(updated_jump)

    @Slot(object)
    def do_remove_jump(self, jump):
        """Removes a jump from the scene.

        Args:
            jump (Jump): link's jump
        """
        for link in [item for item in self.items() if isinstance(item, JumpLink)]:
            source_name = link.src_connector.parent_name()
            destination_name = link.dst_connector.parent_name()
            if source_name == jump.source and destination_name == jump.destination:
                link.scene().removeItem(link)
                break

    def contextMenuEvent(self, event):
        """Shows context menu for the blank view

        Args:
            event (QContextMenuEvent): Event
        """
        if not self._toolbox.project():
            return
        QGraphicsView.contextMenuEvent(self, event)  # Pass the event first to see if any item accepts it
        if not event.isAccepted():
            event.accept()
            global_pos = self.viewport().mapToGlobal(event.pos())
            self._toolbox.show_project_or_item_context_menu(global_pos, None)


def _fake_left_button_event(mouse_event):
    """Makes a left-click mouse event that is otherwise close of given event.

    Args:
        mouse_event (QMouseEvent): mouse event

    Returns:
        QMouseEvent: left-click mouse event
    """
    return QMouseEvent(
        mouse_event.type(),
        mouse_event.pos(),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
