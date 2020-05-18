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
Classes for custom QGraphicsViews for the Design and Graph views.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   6.2.2018
"""

import logging
import math
from PySide2.QtWidgets import QGraphicsView
from PySide2.QtGui import QCursor
from PySide2.QtCore import QEventLoop, QParallelAnimationGroup, Signal, Slot, Qt, QTimeLine, QSettings, QRectF
from spine_engine import ExecutionDirection, SpineEngineState
from ..graphics_items import Link
from ..project_commands import AddLinkCommand, RemoveLinkCommand
from ..mvcmodels.entity_list_models import EntityListModel
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
        self._num_scheduled_scalings = 0
        self.time_line = None
        self._items_fitting_zoom = 1.0
        self._max_zoom = 10.0
        self._min_zoom = 0.1
        self._qsettings = QSettings("SpineProject", "Spine Toolbox")

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

    def enterEvent(self, event):
        """Overridden method. Do not show the stupid open hand mouse cursor.

        Args:
            event (QEvent): event
        """
        super().enterEvent(event)
        self.viewport().setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Set rubber band selection mode if Control pressed.
        Enable resetting the zoom factor from the middle mouse button.
        """
        item = self.itemAt(event.pos())
        # print(not item, not int(item.acceptedMouseButtons() & event.buttons()))
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
        item = self.itemAt(event.pos())
        if not item or not item.acceptedMouseButtons():
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """Zoom in/out.

        Args:
            event (QWheelEvent): Mouse wheel event
        """
        if event.orientation() != Qt.Vertical:
            event.ignore()
            return
        event.accept()
        smooth_zoom = self._qsettings.value("appSettings/smoothZoom", defaultValue="false")
        if smooth_zoom == "true":
            num_degrees = event.delta() / 8
            num_steps = num_degrees / 15
            self._num_scheduled_scalings += num_steps
            if self._num_scheduled_scalings * num_steps < 0:
                self._num_scheduled_scalings = num_steps
            if self.time_line:
                self.time_line.deleteLater()
            self.time_line = QTimeLine(200, self)
            self.time_line.setUpdateInterval(20)
            self.time_line.valueChanged.connect(lambda x, pos=event.pos(): self._handle_zoom_time_line_advanced(pos))
            self.time_line.finished.connect(self._handle_zoom_time_line_finished)
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
                if new_size.width() > old_size.width() or new_size.height() > old_size.height():
                    transform = self.transform()
                    zoom = transform.m11()
                    if zoom < self._min_zoom:
                        # Reset the zoom if the view has grown and the current zoom is too small
                        self.reset_zoom()
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

    @Slot("QGraphicsItem")
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
        fitting_margin = 70
        size = self.size()
        x_factor = size.width() / (rect.width() + fitting_margin)
        y_factor = size.height() / (rect.height() + fitting_margin)
        self._items_fitting_zoom = min(x_factor, y_factor)
        self._min_zoom = min(self._items_fitting_zoom, 0.1)

    def _handle_zoom_time_line_advanced(self, pos):
        """Performs zoom whenever the smooth zoom time line advances."""
        factor = 1.0 + self._num_scheduled_scalings / 100.0
        self.gentle_zoom(factor, pos)

    @Slot()
    def _handle_zoom_time_line_finished(self):
        """Cleans up after the smooth zoom time line finishes."""
        if self._num_scheduled_scalings > 0:
            self._num_scheduled_scalings -= 1
        else:
            self._num_scheduled_scalings += 1
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

    def reset_zoom(self):
        """Resets zoom to the default factor."""
        self.resetTransform()
        self.scene().center_items()
        self._update_zoom_limits()
        self.scale(self._items_fitting_zoom, self._items_fitting_zoom)
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
        transform = self.transform()
        current_zoom = transform.m11()  # The [1, 1] element contains the x scaling factor
        proposed_zoom = current_zoom * factor
        if proposed_zoom < self._min_zoom:
            factor = self._min_zoom / current_zoom
        elif proposed_zoom > self._max_zoom:
            factor = self._max_zoom / current_zoom
        if math.isclose(factor, 1.0):
            return False
        self.scale(factor, factor)
        post_scaling_focus_on_scene = self.mapToScene(zoom_focus)
        center_on_scene = self.mapToScene(self.viewport().rect().center())
        focus_diff = post_scaling_focus_on_scene - initial_focus_on_scene
        self.centerOn(center_on_scene - focus_diff)
        return True

    def _get_viewport_scene_rect(self):
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
        self._project_item_model = None

    def set_ui(self, toolbox):
        """Set a new scene into the Design View when app is started."""
        self._toolbox = toolbox
        self.setScene(DesignGraphicsScene(self, toolbox))

    def set_project_item_model(self, model):
        """Set project item model."""
        self._project_item_model = model

    def remove_icon(self, icon):
        """Removes icon and all connected links from scene."""
        links = set(link for conn in icon.connectors.values() for link in conn.links)
        for link in links:
            self.scene().removeItem(link)
            # Remove Link from connectors
            link.src_connector.links.remove(link)
            link.dst_connector.links.remove(link)
        scene = self.scene()
        scene.removeItem(icon)
        self._set_preferred_scene_rect()

    def links(self):
        """Returns all Links in the scene.
        Used for saving the project."""
        return [item for item in self.items() if isinstance(item, Link)]

    def add_link(self, src_connector, dst_connector):
        """
        Pushes an AddLinkCommand to the toolbox undo stack.
        """
        self._toolbox.undo_stack.push(AddLinkCommand(self, src_connector, dst_connector))
        self.notify_destination_items(src_connector, dst_connector)

    def make_link(self, src_connector, dst_connector):
        """Returns a Link between given connectors.

        Args:
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button

        Returns:
            Link
        """
        return Link(self._toolbox, src_connector, dst_connector)

    def do_add_link(self, src_connector, dst_connector):
        """Makes a Link between given source and destination connectors and adds it to the project.

        Args:
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
        """
        link = self.make_link(src_connector, dst_connector)
        self._add_link(link)

    def _add_link(self, link):
        """Adds given Link to the project.

        Args:
            link (Link): the link to add
        """
        replaced_link = self._remove_redundant_link(link)
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        self.scene().addItem(link)
        src_name = link.src_icon._project_item.name
        dst_name = link.dst_icon._project_item.name
        self._toolbox.project().dag_handler.add_graph_edge(src_name, dst_name)
        return replaced_link

    @staticmethod
    def _remove_redundant_link(link):
        """Checks if there's a link with the same source and destination as the given one,
        wipes it out and returns it.

        Args:
            link (Link): a new link being added to the project.

        Returns
            Link, NoneType
        """
        for replaced_link in link.src_connector._parent.outgoing_links():
            if replaced_link.dst_connector._parent == link.dst_connector._parent:
                replaced_link.wipe_out()
                return replaced_link
        return None

    def remove_link(self, link):
        """Pushes a RemoveLinkCommand to the toolbox undo stack.
        """
        self._toolbox.undo_stack.push(RemoveLinkCommand(self, link))

    def do_remove_link(self, link):
        """Removes link from the project."""
        link.wipe_out()
        # Remove edge (connection link) from dag
        src_name = link.src_icon.name()
        dst_name = link.dst_icon.name()
        self._toolbox.project().dag_handler.remove_graph_edge(src_name, dst_name)

    def take_link(self, link):
        """Remove link, then start drawing another one from the same source connector."""
        self.remove_link(link)
        link_drawer = link.src_connector.start_link()
        # noinspection PyArgumentList
        link_drawer.tip = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        link_drawer.update_geometry()

    def restore_links(self, connections):
        """Creates Links from the given connections list.

        - List of dicts is accepted, e.g.

        .. code-block::

            [
                {"from": ["DC1", "right"], "to": ["Tool1", "left"]},
                ...
            ]

        Args:
            connections (list): List of connections.
        """
        if not connections:
            return
        for conn in connections:
            src_name, src_anchor = conn["from"]
            dst_name, dst_anchor = conn["to"]
            # Do not restore feedback links
            if src_name == dst_name:
                continue
            src_ind = self._project_item_model.find_item(src_name)
            dst_ind = self._project_item_model.find_item(dst_name)
            if not src_ind or not dst_ind:
                self._toolbox.msg_warning.emit("Restoring a connection failed")
                continue
            src_item = self._project_item_model.item(src_ind).project_item
            src_connector = src_item.get_icon().conn_button(src_anchor)
            dst_item = self._project_item_model.item(dst_ind).project_item
            dst_connector = dst_item.get_icon().conn_button(dst_anchor)
            self.do_add_link(src_connector, dst_connector)

    def notify_destination_items(self, src_connector, dst_connector):
        """Notify destination items that they have been connected to a source item."""
        src_item_name = src_connector.parent_name()
        dst_item_name = dst_connector.parent_name()
        src_leaf_item = self._project_item_model.get_item(src_item_name)
        if src_leaf_item is None:
            logging.error("Item %s not found", src_item_name)
            return
        dst_leaf_item = self._project_item_model.get_item(dst_item_name)
        if dst_leaf_item is None:
            logging.error("Item %s not found", dst_item_name)
            return
        src_item = src_leaf_item.project_item
        dst_item = dst_leaf_item.project_item
        dst_item.notify_destination(src_item)

    @Slot("QVariant")
    def connect_engine_signals(self, engine):
        """Connects signals needed for icon animations from given engine."""
        engine.dag_node_execution_started.connect(self._start_animation)
        engine.dag_node_execution_finished.connect(self._stop_animation)
        engine.dag_node_execution_finished.connect(self._run_leave_animation)

    @Slot(str, "QVariant")
    def _start_animation(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        if direction == ExecutionDirection.BACKWARD:
            return
        item = self._project_item_model.get_item(item_name).project_item
        icon = item.get_icon()
        if hasattr(icon, "start_animation"):
            icon.start_animation()

    @Slot(str, "QVariant", "QVariant")
    def _stop_animation(self, item_name, direction, _):
        """Stops item icon animation when executing forward."""
        if direction == ExecutionDirection.BACKWARD:
            return
        item = self._project_item_model.get_item(item_name).project_item
        icon = item.get_icon()
        if hasattr(icon, "stop_animation"):
            icon.stop_animation()

    @Slot(str, "QVariant", "QVariant")
    def _run_leave_animation(self, item_name, direction, engine_state):
        """
        Runs the animation that represents execution leaving this item.
        Blocks until the animation is finished.
        """
        if direction == ExecutionDirection.BACKWARD or engine_state != SpineEngineState.RUNNING:
            return
        loop = QEventLoop()
        animation = self._make_execution_leave_animation(item_name)
        animation.finished.connect(loop.quit)
        animation.start()
        if animation.state() == QParallelAnimationGroup.Running:
            loop.exec_()

    def _make_execution_leave_animation(self, item_name):
        """
        Returns animation to play when execution leaves this item.

        Returns:
            QParallelAnimationGroup
        """
        item = self._project_item_model.get_item(item_name).project_item
        icon = item.get_icon()
        links = set(link for conn in icon.connectors.values() for link in conn.links if link.src_connector == conn)
        animation_group = QParallelAnimationGroup(item)
        for link in links:
            animation_group.addAnimation(link.make_execution_animation())
        return animation_group


class EntityQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Entity Graph View."""

    item_dropped = Signal("QPoint", "QString")

    context_menu_requested = Signal("QPoint")

    def dragLeaveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not EntityListModel."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not EntityListModel."""
        event.accept()
        source = event.source()
        if not isinstance(source.model(), EntityListModel):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not EntityListModel."""
        event.accept()
        source = event.source()
        if not isinstance(source.model(), EntityListModel):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of EntityListModel.
        Capture text from event's mimedata and emit signal.
        """
        source = event.source()
        if not isinstance(source.model(), EntityListModel):
            super().dropEvent(event)
            return
        entity_type = source.model().entity_type
        event.acceptProposedAction()
        entity_class_id = event.mimeData().text()
        pos = event.pos()
        text = entity_type + ":" + entity_class_id
        self.item_dropped.emit(pos, text)

    def contextMenuEvent(self, e):
        """Show context menu.

        Args:
            e (QContextMenuEvent): Context menu event
        """
        super().contextMenuEvent(e)
        if e.isAccepted():
            return
        e.accept()
        self.context_menu_requested.emit(e.globalPos())

    def gentle_zoom(self, factor, zoom_focus=None):
        """
        Perform a zoom by a given factor.

        Args:
            factor (float): a scaling factor relative to the current scene scaling
            zoom_focus (QPoint): focus of the zoom, e.g. mouse pointer position
        """
        if not super().gentle_zoom(factor, zoom_focus=zoom_focus):
            return False
        self.adjust_items_to_zoom()
        return True

    def scale(self, x, y):
        super().scale(x, y)
        self.adjust_items_to_zoom()

    def adjust_items_to_zoom(self):
        """
        Update items geometry after performing a zoom.

        Some items (e.g. ArcItem) need this to stay the same size after a zoom.
        """
        for item in self.items():
            if hasattr(item, "adjust_to_zoom"):
                item.adjust_to_zoom(self.transform())
