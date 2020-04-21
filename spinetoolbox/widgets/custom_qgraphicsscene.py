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

from PySide2.QtCore import Slot, QItemSelectionModel
from PySide2.QtGui import QColor, QPen, QBrush
from ..graphics_items import ProjectItemIcon
from .shrinking_scene import ShrinkingScene
from ..mvcmodels.project_item_factory_models import ProjectItemFactoryModel, ProjectItemSpecFactoryModel


class CustomQGraphicsScene(ShrinkingScene):
    """A scene that handles drag and drop events of ProjectItemFactoryModel or ProjectItemSpecFactoryModel sources."""

    def __init__(self, parent, toolbox):
        """
        Args:
            parent (QObject): scene's parent object
            toolbox (ToolboxUI): reference to the main window
        """
        super().__init__(400.0, 300.0, parent)
        self._toolbox = toolbox
        self.item_shadow = None
        self.sync_selection = True
        # Set background attributes
        settings = toolbox.qsettings()
        grid = settings.value("appSettings/bgGrid", defaultValue="false")
        self.bg_grid = grid != "false"
        bg_color = settings.value("appSettings/bgColor", defaultValue="false")
        self.bg_color = QColor("#f5f5f5") if bg_color == "false" else bg_color
        self.connect_signals()

    def connect_signals(self):
        """Connect scene signals."""
        self.changed.connect(self.scene_changed)
        self.selectionChanged.connect(self.handle_selection_changed)

    def resize_scene(self):
        """Resize scene to be at least the size of items bounding rectangle.
        Does not let the scene shrink."""
        scene_rect = self.sceneRect()
        items_rect = self.itemsBoundingRect()
        union_rect = scene_rect | items_rect
        self.setSceneRect(union_rect)

    @Slot("QList<QRectF>")
    def scene_changed(self, rects):
        """Resize scene as it changes."""
        scene_rect = self.sceneRect()
        if all(scene_rect.contains(rect) for rect in rects):
            return
        self.resize_scene()

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

    def set_bg_grid(self, bg):
        """Enable or disable background grid.

        Args:
            bg (boolean): True to draw grid, False to fill background with a solid color
        """
        self.bg_grid = bg

    @staticmethod
    def _is_project_item_drag(source):
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
        factory_name, spec = event.mimeData().text().split(",")
        pos = event.scenePos()
        w = 70
        h = 70
        x = pos.x() - w / 2
        y = pos.y() - h / 2
        factory = self._toolbox.item_factories[factory_name]
        self.item_shadow = factory.make_icon(self._toolbox, x, y, w, h, None)
        self._toolbox.show_add_project_item_form(factory_name, pos.x(), pos.y(), spec=spec)

    def drawBackground(self, painter, rect):
        """Reimplemented method to make a custom background.

        Args:
            painter (QPainter): Painter that is used to paint background
            rect (QRectF): The exposed (viewport) rectangle in scene coordinates
        """
        scene_rect = self.sceneRect()
        rect = rect.intersected(scene_rect)  # Limit to only draw background for the scene rectangle
        if not self.bg_grid:
            painter.fillRect(rect, QBrush(self.bg_color))
            return
        step = 20  # Grid step
        painter.setPen(QPen(QColor(0, 0, 0, 40)))
        # Draw horizontal grid
        start = round(rect.top(), step)
        if start > rect.top():
            start -= step
        y = start
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += step
        # Now draw vertical grid
        start = round(rect.left(), step)
        if start > rect.left():
            start -= step
        x = start
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += step
