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
from PySide2.QtCore import Signal, Slot, QItemSelectionModel, QEvent, QPointF
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QColor, QPen, QBrush
from ..graphics_items import ProjectItemIcon
from ..mvcmodels.project_item_factory_models import ProjectItemFactoryModel, ProjectItemSpecFactoryModel


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

    Mainly, it handles drag and drop events of ProjectItemFactoryModel or ProjectItemSpecFactoryModel sources.
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
        self.connect_signals()

    def connect_signals(self):
        """Connect scene signals."""
        self.selectionChanged.connect(self.handle_selection_changed)

    @Slot()
    def handle_selection_changed(self):
        """Synchronize selection with the project tree."""
        if not self.sync_selection:
            return
        selected_items = [item for item in self.selectedItems() if isinstance(item, ProjectItemIcon)]
        selected_inds = [self._toolbox.project_item_model.find_item(item.name()) for item in selected_items]
        self._toolbox.ui.treeView_project.clearSelection()
        for ind in selected_inds:
            self._toolbox.ui.treeView_project.selectionModel().select(ind, QItemSelectionModel.Select)
        # Make last item selected the current index in project tree view
        if bool(selected_inds):
            self._toolbox.ui.treeView_project.selectionModel().setCurrentIndex(
                selected_inds[-1], QItemSelectionModel.NoUpdate
            )

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
        if not hasattr(source, "model"):
            return False
        return callable(source.model) and isinstance(
            source.model(), (ProjectItemFactoryModel, ProjectItemSpecFactoryModel)
        )

    def dragLeaveEvent(self, event):
        """Accept event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemFactoryModel or ProjectItemSpecFactoryModel."""
        event.accept()
        source = event.source()
        if not self._is_project_item_drag(source):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a ProjectItemFactoryModel or ProjectItemSpecFactoryModel."""
        event.accept()
        source = event.source()
        if not self._is_project_item_drag(source):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of
        ProjectItemFactoryModel or ProjectItemSpecFactoryModel.
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
        self.item_shadow = factory.make_icon(self._toolbox, x, y, None)
        self._toolbox.show_add_project_item_form(item_type, pos.x(), pos.y(), spec=spec)

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
        # Draw horizontal grid
        start = round(self.bg_origin.y())
        for y in range(start, round(rect.bottom()), step):
            painter.drawLine(rect.left(), y, rect.right(), y)
        for y in range(start, round(rect.top()), -step):
            painter.drawLine(rect.left(), y, rect.right(), y)
        # Now draw vertical grid
        start = round(self.bg_origin.x())
        for x in range(start, round(rect.right()), step):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for x in range(start, round(rect.left()), -step):
            painter.drawLine(x, rect.top(), x, rect.bottom())

    def _draw_tree_bg(self, painter, rect):
        """Draws 'tree of life' bg."""
        painter.setPen(QPen(self.bg_color))
        radius = ProjectItemIcon.ITEM_EXTENT

        def draw_column(y):
            orig_to_bottom_count = round((rect.bottom() - y) / radius) + 1
            for j in range(orig_to_bottom_count):
                painter.drawEllipse(QPointF(i * dx, y + j * radius), radius, radius)
            orig_to_top_count = round((y - rect.top()) / radius) + 1
            for j in range(-1, -orig_to_top_count, -1):
                painter.drawEllipse(QPointF(i * dx, y + j * radius), radius, radius)

        dx = math.sin(math.pi / 3) * radius
        dy = math.cos(math.pi / 3) * radius
        x_orig = self.bg_origin.x()
        y_orig = self.bg_origin.y()
        orig_to_right_count = round((rect.right() - x_orig) / dx) + 1
        orig_to_left_count = round((x_orig - rect.left()) / dx) + 1
        for k, i in enumerate(range(orig_to_right_count)):
            draw_column(y_orig + k * dy)
        for k, i in enumerate(range(-1, -orig_to_left_count, -1)):
            draw_column(y_orig - (k + 1) * dy)
