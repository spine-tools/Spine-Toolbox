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
Module for view icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

import random
from PySide2.QtGui import QColor
from PySide2.QtCore import QTimeLine, QPointF, Slot
from spinetoolbox.graphics_items import ProjectItemIcon


class CombinerIcon(ProjectItemIcon):
    _SHAKE_FACTOR = 0.05

    def __init__(self, toolbox, x, y, project_item, icon):
        """View icon for the Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            project_item (ProjectItem): Item
            icon (str): icon resource path
        """
        super().__init__(
            toolbox, x, y, project_item, icon, icon_color=QColor("#990000"), background_color=QColor("#ffcccc")
        )
        self.time_line = QTimeLine()
        self.time_line.setLoopCount(0)  # loop forever
        self.time_line.setFrameRange(0, 10)
        self.time_line.setDirection(QTimeLine.Backward)
        self.time_line.valueChanged.connect(self._handle_time_line_value_changed)
        self.time_line.stateChanged.connect(self._handle_time_line_state_changed)
        self._svg_item_pos = self.svg_item.pos()

    @Slot(float)
    def _handle_time_line_value_changed(self, value):
        rect = self.svg_item.sceneBoundingRect()
        width = rect.width()
        height = rect.height()
        x = random.uniform(-self._SHAKE_FACTOR, self._SHAKE_FACTOR) * width
        y = random.uniform(-self._SHAKE_FACTOR, self._SHAKE_FACTOR) * height
        self.svg_item.setPos(self._svg_item_pos + QPointF(x, y))

    @Slot("QTimeLine::State")
    def _handle_time_line_state_changed(self, new_state):
        if new_state == QTimeLine.NotRunning:
            self.svg_item.setPos(self._svg_item_pos)

    def start_animation(self):
        """Start the animation that plays when the Combiner associated to this GraphicsItem is running.
        """
        if self.time_line.state() == QTimeLine.Running:
            return
        self.time_line.start()

    def stop_animation(self):
        """Stop animation"""
        if self.time_line.state() != QTimeLine.Running:
            return
        self.time_line.stop()
