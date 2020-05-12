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
from PySide2.QtCore import QTimeLine, QPointF
from PySide2.QtWidgets import QGraphicsItemAnimation
from spinetoolbox.graphics_items import ProjectItemIcon


class RecombinatorIcon(ProjectItemIcon):
    _SHAKE_FACTOR = 0.05

    def __init__(self, toolbox, x, y, w, h, project_item, icon):
        """View icon for the Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Width of background rectangle
            h (float): Height of background rectangle
            project_item (ProjectItem): Item
            icon (str): icon resource path
        """
        super().__init__(
            toolbox, x, y, w, h, project_item, icon, icon_color=QColor("#990000"), background_color=QColor("#ffcccc")
        )
        # animation stuff
        self.timer = QTimeLine()
        self.timer.setLoopCount(0)  # loop forever
        self.timer.setFrameRange(0, 10)
        # self.timer.setCurveShape(QTimeLine.CosineCurve)
        self.timer.valueForTime = self._value_for_time
        self.animation = QGraphicsItemAnimation()
        self.animation.setItem(self.svg_item)
        self.animation.setTimeLine(self.timer)
        self.initial_pos = self.svg_item.pos()

    @staticmethod
    def _value_for_time(msecs):
        rem = (msecs % 1000) / 1000
        return 1.0 - rem

    def start_animation(self):
        """Start the animation that plays when the Recombinator associated to this GraphicsItem is running.
        """
        if self.timer.state() == QTimeLine.Running:
            return
        initial_pos = self.svg_item.pos()
        rect = self.svg_item.sceneBoundingRect()
        width = rect.width()
        height = rect.height()
        for i in range(100):
            step = i / 100.0
            x = random.uniform(-self._SHAKE_FACTOR, self._SHAKE_FACTOR) * width
            y = random.uniform(-self._SHAKE_FACTOR, self._SHAKE_FACTOR) * height
            self.animation.setPosAt(step, initial_pos + QPointF(x, y))
        self.animation.setPosAt(0, initial_pos)
        self.timer.start()

    def stop_animation(self):
        """Stop animation"""
        if self.timer.state() != QTimeLine.Running:
            return
        self.animation.setStep(0)
        self.timer.stop()
