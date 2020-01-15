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
Module for data connection icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

import os
from PySide2.QtGui import QColor
from PySide2.QtCore import QObject, Qt, QTimer, Signal
from spinetoolbox.graphics_items import ProjectItemIcon


class DataConnectionIcon(ProjectItemIcon):
    class _SignalHolder(QObject):
        files_dropped_on_icon = Signal("QGraphicsItem", list)
        """A signal that it triggered when files are dragged and dropped on the item."""

    def __init__(self, toolbox, x, y, w, h, name):
        """Data Connection icon for the Design View.

        Args:
            toolbox (ToolboxUI): main window instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Width of master icon
            h (float): Height of master icon
            name (str): Item name
        """
        super().__init__(
            toolbox,
            x,
            y,
            w,
            h,
            name,
            ":/icons/project_item_icons/file-alt.svg",
            icon_color=QColor(0, 0, 255),
            background_color=QColor("#e6e6ff"),
        )
        self.setAcceptDrops(True)
        self._drag_over = False
        self._signal_holder = DataConnectionIcon._SignalHolder()
        self.files_dropped_on_icon = self._signal_holder.files_dropped_on_icon

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
        if self._drag_over:
            return
        self._drag_over = True
        QTimer.singleShot(100, self.select_on_drag_over)

    def dragLeaveEvent(self, event):
        """Drag and drop action leaves.

        Args:
            event (QGraphicsSceneDragDropEvent): Event
        """
        event.accept()
        self._drag_over = False

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit files_dropped_on_dc signal from scene,
        with this instance, and a list of files for each dropped url."""
        self.files_dropped_on_icon.emit(self, [url.toLocalFile() for url in event.mimeData().urls()])

    def select_on_drag_over(self):
        """Called when the timer started in drag_enter_event is elapsed.
        Select this item if the drag action is still over it.
        """
        if not self._drag_over:
            return
        self._drag_over = False
        self._toolbox.ui.graphicsView.scene().clearSelection()
        self.setSelected(True)
        self.show_item_info()
