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
Module for Importer icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

from PySide2.QtGui import QColor
from PySide2.QtWidgets import QGraphicsTextItem
from spinetoolbox.graphics_items import ProjectItemIcon
from ..shared.import_export_animation import ImportExportAnimation


class ImporterIcon(ProjectItemIcon):
    def __init__(self, toolbox, x, y, w, h, name):
        """Importer icon for the Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
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
            ":/icons/project_item_icons/database-import.svg",
            icon_color=QColor("#990000"),
            background_color=QColor("#ffcccc"),
        )
        src_item = QGraphicsTextItem("\uf15c")
        src_item.setDefaultTextColor("#0000ff")
        dst_item = QGraphicsTextItem("\uf1c0")
        dst_item.setDefaultTextColor("#cc33ff")
        self.animation = ImportExportAnimation(self, src_item, dst_item)
        self.start_animation = self.animation.start
        self.stop_animation = self.animation.stop
