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
Module for tool icon class.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

from PySide2.QtGui import QColor
from PySide2.QtCore import QTimeLine, QPointF
from PySide2.QtWidgets import QGraphicsItemAnimation
from spinetoolbox.graphics_items import ProjectItemIcon


class ToolIcon(ProjectItemIcon):
    def __init__(self, toolbox, x, y, w, h, project_item, icon):
        """Tool icon for the Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Width of master icon
            h (float): Height of master icon
            project_item (ProjectItem): Item
            icon (str): icon resource path
        """
        super().__init__(
            toolbox, x, y, w, h, project_item, icon, icon_color=QColor("red"), background_color=QColor("#ffe6e6")
        )
        # animation stuff
        self.time_line = QTimeLine()
        self.time_line.setLoopCount(0)  # loop forever
        self.time_line.setFrameRange(0, 10)
        # self.time_line.setCurveShape(QTimeLine.CosineCurve)
        self.time_line.valueForTime = self._value_for_time
        self.animation = QGraphicsItemAnimation()
        self.animation.setItem(self.svg_item)
        self.animation.setTimeLine(self.time_line)
        self.delta = 0.25 * self.svg_item.sceneBoundingRect().height()

    @staticmethod
    def _value_for_time(msecs):
        rem = (msecs % 1000) / 1000
        return 1.0 - rem

    def start_animation(self):
        """Start the animation that plays when the Tool associated to this GraphicsItem is running.
        """
        if self.time_line.state() == QTimeLine.Running:
            return
        self.svg_item.moveBy(0, -self.delta)
        offset = 0.75 * self.svg_item.sceneBoundingRect().height()
        for angle in range(1, 45):
            step = angle / 45.0
            self.animation.setTranslationAt(step, 0, offset)
            self.animation.setRotationAt(step, angle)
            self.animation.setTranslationAt(step, 0, -offset)
            self.animation.setPosAt(step, QPointF(self.svg_item.pos().x(), self.svg_item.pos().y() + offset))
        self.time_line.start()

    def stop_animation(self):
        """Stop animation"""
        if self.time_line.state() != QTimeLine.Running:
            return
        self.time_line.stop()
        self.svg_item.moveBy(0, self.delta)
        self.time_line.setCurrentTime(999)
