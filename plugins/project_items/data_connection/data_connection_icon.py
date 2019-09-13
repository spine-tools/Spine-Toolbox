######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Module for data connection icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

from graphics_items import ProjectItemIcon
from PySide2.QtGui import QColor, QPen, QBrush
from PySide2.QtCore import Qt


class DataConnectionIcon(ProjectItemIcon):
    """Data Connection icon for the Design View.

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of master icon
        h (int): Height of master icon
        name (str): Item name
    """

    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(Qt.NoPen)  # QPen for the background rectangle
        self.brush = QBrush(QColor("#e6e6ff"))  # QBrush for the background rectangle
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/file-alt.svg", QColor(0, 0, 255, 160))
        self.setAcceptDrops(True)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)
        self.drag_over = False

    def dragEnterEvent(self, event):
        """Drag and drop action enters.
        Accept file drops from the filesystem.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        urls = event.mimeData().urls()
        for url in urls:
            if not url.isLocalFile():
                event.ignore()
                return
            if not os.path.isfile(url.toLocalFile()):
                event.ignore()
                return
        event.accept()
        event.setDropAction(Qt.CopyAction)
        if self.drag_over:
            return
        self.drag_over = True
        QTimer.singleShot(100, self.select_on_drag_over)

    def dragLeaveEvent(self, event):
        """Drag and drop action leaves.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        event.accept()
        self.drag_over = False

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit files_dropped_on_dc signal from scene,
        with this instance, and a list of files for each dropped url."""
        self.scene().files_dropped_on_dc.emit(self, [url.toLocalFile() for url in event.mimeData().urls()])

    def select_on_drag_over(self):
        """Called when the timer started in drag_enter_event is elapsed.
        Select this item if the drag action is still over it.
        """
        if not self.drag_over:
            return
        self.drag_over = False
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self.setSelected(True)
        self.show_item_info()
