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
Custom QGraphicsScene used in the Design View.

:author: P. Savolainen (VTT)
:date:   13.2.2019
"""

import math
from PySide2.QtCore import Qt, Signal, Slot, QItemSelectionModel, QPointF, QEvent
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QColor, QPen, QBrush
from spinetoolbox.graphics_items import ProjectItemIcon, Link
from .project_item_drag import ProjectItemDragMixin
from ..graphics_items import LinkDrawer


class CustomGraphicsScene(QGraphicsScene):
    """
    A custom QGraphicsScene. It provides signals to notify about items,
    and a method to center all items in the scene.

    At the moment it's used by DesignGraphicsScene and the GraphViewMixin
    """

    item_move_finished = Signal("QGraphicsItem")
    """Emitted when an item has finished moving."""

    item_removed = Signal("QGraphicsItem")
    """Emitted when an item has been removed."""

    def center_items(self):
        """Centers toplevel items in the scene."""
        rect = self.itemsBoundingRect()
        delta = -rect.center()
        for item in self.items():
            if item.topLevelItem() != item:
                continue
            item.moveBy(delta.x(), delta.y())
        self.setSceneRect(rect.translated(delta))


class DesignGraphicsScene(CustomGraphicsScene):
    """A scene for the Design view.

    Mainly, it handles drag and drop events of ProjectItemDragMixin sources.
    """

    def __init__(self, parent, toolbox):
        """
        Args:
            parent (QObject): scene's parent object
            toolbox (ToolboxUI): reference to the main window
        """
        super().__init__(parent)
        self._toolbox = toolbox
        self.item_shadow = None
        self.sync_selection = True
        # Set background attributes
        settings = toolbox.qsettings()
        self.bg_choice = settings.value("appSettings/bgChoice", defaultValue="solid")
        bg_color = settings.value("appSettings/bgColor", defaultValue="false")
        self.bg_color = QColor("#f5f5f5") if bg_color == "false" else bg_color
        self.bg_origin = None
        self.link_drawer = LinkDrawer(toolbox)
        self.link_drawer.hide()
        self.connect_signals()

    def mouseMoveEvent(self, event):
        """Moves link drawer."""
        if self.link_drawer.isVisible():
            self.link_drawer.tip = event.scenePos()
            self.link_drawer.update_geometry()
            event.setButtons(Qt.NoButton)  # this is so super().mouseMoveEvent sends hover events to connector buttons
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Puts link drawer to sleep and log message if it looks like the user doesn't know what they're doing."""
        was_drawing = self.link_drawer.isVisible()
        super().mousePressEvent(event)
        if was_drawing and self.link_drawer.isVisible():
            self.link_drawer.sleep()
            if event.button() == Qt.LeftButton:
                self.emit_connection_failed()

    def mouseReleaseEvent(self, event):
        """Makes link if drawer is released over a valid connector button."""
        super().mouseReleaseEvent(event)
        if not self.link_drawer.isVisible() or self.link_drawer.src_connector.isUnderMouse():
            return
        if self.link_drawer.dst_connector is None:
            self.link_drawer.sleep()
            self.emit_connection_failed()
            return
        self.link_drawer.add_link()

    def emit_connection_failed(self):
        self._toolbox.msg_warning.emit(
            "Unable to make connection. Try landing the connection onto a valid connector button."
        )

    def keyPressEvent(self, event):
        """Puts link drawer to sleep if user presses ESC."""
        super().keyPressEvent(event)
        if self.link_drawer.isVisible() and event.key() == Qt.Key_Escape:
            self.link_drawer.sleep()

    def connect_signals(self):
        """Connect scene signals."""
        self.selectionChanged.connect(self.handle_selection_changed)

    def project_item_icons(self):
        return [item for item in self.items() if isinstance(item, ProjectItemIcon)]

    @Slot()
    def handle_selection_changed(self):
        """Synchronizes selection with the project tree."""
        if not self.sync_selection:
            return
        selected_item_names = [item.name() for item in self.selectedItems() if isinstance(item, ProjectItemIcon)]
        for ind in self._toolbox.project_item_model.leaf_indexes():
            item_name = self._toolbox.project_item_model.item(ind).name
            cmd = QItemSelectionModel.Select if item_name in selected_item_names else QItemSelectionModel.Deselect
            self._toolbox.ui.treeView_project.selectionModel().select(ind, cmd)
        selected_inds = [self._toolbox.project_item_model.find_item(name) for name in selected_item_names]
        # Make last item selected the current index in project tree view
        if selected_inds:
            self._toolbox.ui.treeView_project.selectionModel().setCurrentIndex(
                selected_inds[-1], QItemSelectionModel.NoUpdate
            )
        if len(selected_inds) == 1:
            new_active_project_item = self._toolbox.project_item_model.item(selected_inds[0]).project_item
        else:
            new_active_project_item = None
        links = [item for item in self.selectedItems() if isinstance(item, Link)]
        if len(links) == 1:
            new_active_link = links[0]
        else:
            new_active_link = None
        self._toolbox.refresh_active_elements(new_active_project_item, new_active_link)

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

    @staticmethod
    def _is_project_item_drag(source):
        """Checks whether or not source corresponds to a project item being dragged into the scene.
        """
        return isinstance(source, ProjectItemDragMixin)

    def dragLeaveEvent(self, event):
        """Accept event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemDragMixin."""
        event.accept()
        source = event.source()
        if not self._is_project_item_drag(source):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemDragMixin."""
        event.accept()
        source = event.source()
        if not self._is_project_item_drag(source):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of ProjectItemDragMixin.
        Capture text from event's mimedata and show the appropriate 'Add Item form.'
        """
        source = event.source()
        if not self._is_project_item_drag(source):
            super().dropEvent(event)
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
        self.item_shadow.update("", x, y)
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
        if self.bg_origin is None:
            self.bg_origin = rect.center()
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
        delta = rect.topLeft() - self.bg_origin
        x_start = round(delta.x() / step)
        y_start = round(delta.y() / step)
        x_stop = x_start + round(rect.width() / step) + 1
        y_stop = y_start + round(rect.height() / step) + 1
        for i in range(x_start, x_stop):
            x = step * i
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for j in range(y_start, y_stop):
            y = step * j
            painter.drawLine(rect.left(), y, rect.right(), y)
        painter.setPen(QPen(self.bg_color.darker(110)))
        painter.drawLine(self.bg_origin.x(), rect.top(), self.bg_origin.x(), rect.bottom())
        painter.drawLine(rect.left(), self.bg_origin.y(), rect.right(), self.bg_origin.y())

    def _draw_tree_bg(self, painter, rect):
        """Draws 'tree of life' bg."""
        painter.setPen(QPen(self.bg_color))
        radius = ProjectItemIcon.ITEM_EXTENT
        dx = math.sin(math.pi / 3) * radius
        dy = math.cos(math.pi / 3) * radius
        delta = rect.topLeft() - self.bg_origin
        x_start = round(delta.x() / dx)
        y_start = round(delta.y() / radius)
        x_stop = x_start + round(rect.width() / dx) + 1
        y_stop = y_start + round(rect.height() / radius) + 1
        for i in range(x_start, x_stop):
            ref = QPointF(i * dx, (i & 1) * dy)
            for j in range(y_start, y_stop):
                painter.drawEllipse(ref + QPointF(0, j * radius), radius, radius)
        painter.setPen(QPen(self.bg_color.darker(110)))
        painter.drawEllipse(self.bg_origin, 2 * radius, 2 * radius)
