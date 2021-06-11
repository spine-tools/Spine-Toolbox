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
Classes for custom QGraphicsViews for the Design and Graph views.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   6.2.2018
"""

import math
from PySide2.QtWidgets import QGraphicsView, QGraphicsItem, QGraphicsRectItem
from PySide2.QtGui import QCursor
from PySide2.QtCore import Slot, Qt, QTimeLine, QSettings, QRectF
from spine_engine.project_item.connection import Connection
from ..project_item_icon import ProjectItemIcon
from ..project_commands import AddConnectionCommand, RemoveConnectionsCommand
from ..link import Link
from .custom_qgraphicsscene import DesignGraphicsScene


class CustomQGraphicsView(QGraphicsView):
    """Super class for Design and Entity QGraphicsViews.

    Attributes:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent):
        """Init CustomQGraphicsView."""
        super().__init__(parent=parent)
        self._zoom_factor_base = 1.0015
        self._angle = 120
        self._scheduled_transformations = 0
        self.time_line = None
        self._items_fitting_zoom = 1.0
        self._max_zoom = 10.0
        self._min_zoom = 0.1
        self._qsettings = QSettings("SpineProject", "Spine Toolbox")

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
        """Overridden method. Enable zooming with plus and minus keys (comma resets zoom).
        Send event downstream to QGraphicsItems if pressed key is not handled here.

        Args:
            event (QKeyEvent): Pressed key
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
        """Set rubber band selection mode if Control pressed.
        Enable resetting the zoom factor from the middle mouse button.
        """
        item = self.itemAt(event.pos())
        if not item or not item.acceptedMouseButtons() & event.buttons():
            if event.modifiers() & Qt.ControlModifier:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                self.viewport().setCursor(Qt.CrossCursor)
            if event.button() == Qt.MidButton:
                self.reset_zoom()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        super().mouseReleaseEvent(event)
        item = next(iter([x for x in self.items(event.pos()) if x.hasCursor()]), None)
        was_not_rubber_band_drag = self.dragMode() != QGraphicsView.RubberBandDrag
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        if item and was_not_rubber_band_drag:
            self.viewport().setCursor(item.cursor())
        else:
            self.viewport().setCursor(Qt.ArrowCursor)

    def _use_smooth_zoom(self):
        return self._qsettings.value("appSettings/smoothZoom", defaultValue="false") == "true"

    def wheelEvent(self, event):
        """Zooms in/out.

        Args:
            event (QWheelEvent): Mouse wheel event
        """
        if event.orientation() != Qt.Vertical:
            event.ignore()
            return
        event.accept()
        if self._use_smooth_zoom():
            angle = event.delta() / 8
            steps = angle / 15
            self._scheduled_transformations += steps
            if self._scheduled_transformations * steps < 0:
                self._scheduled_transformations = steps
            if self.time_line:
                self.time_line.deleteLater()
            self.time_line = QTimeLine(200, self)
            self.time_line.setUpdateInterval(20)
            self.time_line.valueChanged.connect(lambda x, pos=event.pos(): self._handle_zoom_time_line_advanced(pos))
            self.time_line.finished.connect(self._handle_transformation_time_line_finished)
            self.time_line.start()
        else:
            angle = event.angleDelta().y()
            factor = self._zoom_factor_base ** angle
            self.gentle_zoom(factor, event.pos())
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
            scene (ShrinkingScene): a new scene
        """
        super().setScene(scene)
        scene.item_move_finished.connect(self._handle_item_move_finished)
        scene.item_removed.connect(lambda _item: self._set_preferred_scene_rect())
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
        """Sets the scene rect to the result of uniting the scene viewport rect and the items bounding rect.
        """
        viewport_scene_rect = self._get_viewport_scene_rect()
        items_scene_rect = self.scene().itemsBoundingRect()
        self.scene().setSceneRect(viewport_scene_rect.united(items_scene_rect))


class DesignQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Design View."""

    def __init__(self, parent):
        """

        Args:
            parent (QWidget): Graph View Form's (QMainWindow) central widget (self.centralwidget)
        """
        super().__init__(parent=parent)  # Parent is passed to QWidget's constructor
        self._scene = None
        self._toolbox = None

    def set_ui(self, toolbox):
        """Set a new scene into the Design View when app is started."""
        self._toolbox = toolbox
        self.setScene(DesignGraphicsScene(self, toolbox))

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

    def links(self):
        """Returns all Links in the scene.

        Returns:
            list of Link: scene's links
        """
        return [item for item in self.items() if isinstance(item, Link)]

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

    def make_link(self, src_connector, dst_connector, connection=None):
        """Constructs a Link between given connectors.

        Args:
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            connection (Connection, optional): Underlying connection

        Returns:
            Link: new link
        """
        if connection is None:
            connection = Connection(
                src_connector.project_item().name,
                src_connector.position,
                dst_connector.project_item().name,
                dst_connector.position,
            )
        return Link(self._toolbox, src_connector, dst_connector, connection)

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
        link = self.make_link(source_connector, destination_connector, connection)
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        self.scene().addItem(link)

    @Slot(object, object)
    def do_replace_link(self, original_connection, new_connection):
        """Replaces a link on the Design view.

        Args:
            original_connection (Connection): connection that was replaced
            new_connection (Connection): replacing connection
        """
        self.do_remove_link(original_connection)
        self.do_add_link(new_connection)

    def remove_links(self, links):
        """Pushes a RemoveConnectionsCommand to the Toolbox undo stack.

        Args:
            links (list of Link): links to remove
        """
        connections = list()
        for link in links:
            source = link.src_connector
            destination = link.dst_connector
            connections.append(
                Connection(source.parent_name(), source.position, destination.parent_name(), destination.position)
            )
        self._toolbox.undo_stack.push(RemoveConnectionsCommand(self._toolbox.project(), connections))

    @Slot(object)
    def do_remove_link(self, connection):
        """Removes a link from the scene.

        Args:
            connection (Connection): link's connection
        """
        for link in self.links():
            source_name = link.src_connector.parent_name()
            destination_name = link.dst_connector.parent_name()
            if source_name == connection.source and destination_name == connection.destination:
                link.wipe_out()
                break

    def remove_selected_links(self):
        self.remove_links([item for item in self.scene().selectedItems() if isinstance(item, Link)])

    def take_link(self, link):
        """Remove link, then start drawing another one from the same source connector."""
        self.remove_links([link])
        link_drawer = self.scene().link_drawer
        link_drawer.wake_up(link.src_connector)
        # noinspection PyArgumentList
        link_drawer.tip = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        link_drawer.update_geometry()

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
            self._toolbox.show_project_item_context_menu(global_pos, None)
