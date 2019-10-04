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
Icon class for the Gdx Export project item.

:authors: A. Soininen (VTT)
:date:   25.9.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QBrush, QColor, QPen
from graphics_items import ProjectItemIcon


class GdxExportIcon(ProjectItemIcon):
    def __init__(self, toolbox, x, y, w, h, name):
        """Gdx Export icon for the Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Width of master icon
            h (float): Height of master icon
            name (str): Item name
        """
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(Qt.NoPen)  # QPen for the background rectangle
        self.brush = QBrush(QColor("#ffcccc"))  # QBrush for the background rectangle
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/file-export-solid.svg", QColor("#990000"))
        self.setAcceptDrops(True)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)
