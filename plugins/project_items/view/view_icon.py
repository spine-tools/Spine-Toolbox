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
Module for view icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

from graphics_items import ProjectItemIcon
from PySide2.QtGui import QColor, QPen, QBrush
from PySide2.QtCore import Qt


class ViewIcon(ProjectItemIcon):
    """View icon for the Design View

    Attributes:
        toolbox (ToolBoxUI): QMainWindow instance
        x (int): Icon x coordinate
        y (int): Icon y coordinate
        w (int): Width of background rectangle
        h (int): Height of background rectangle
        name (str): Item name
    """

    def __init__(self, toolbox, x, y, w, h, name):
        """Class constructor."""
        super().__init__(toolbox, x, y, w, h, name)
        self.pen = QPen(Qt.NoPen)  # Pen for the bg rect outline
        self.brush = QBrush(QColor("#ebfaeb"))  # Brush for filling the bg rect
        # Setup icons and attributes
        self.setup(self.pen, self.brush, ":/icons/project_item_icons/binoculars.svg", QColor("#33cc33"))
        self.setAcceptDrops(False)
        # Add items to scene
        self._toolbox.ui.graphicsView.scene().addItem(self)
