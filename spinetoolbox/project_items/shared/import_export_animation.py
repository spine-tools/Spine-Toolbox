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
Animation class for the Exporter and Importer items.

:authors: M. Marin (KTH)
:date:   12.11.2019
"""

from PySide2.QtGui import QFont
from PySide2.QtCore import Slot, QTimeLine
from PySide2.QtWidgets import QGraphicsItemAnimation, QGraphicsOpacityEffect


class ImportExportAnimation:
    def __init__(self, parent_item, src_item, dst_item, duration=2000):
        """Initializes animation stuff.

        Args:
            parent_item (QGraphicsItem): The item on top of which the animation should play.
            src_item (QGraphicsItem): The source item.
            dst_item (QGraphicsItem): The destination item.
            duration (int. optional): The desired duration of each loop in milliseconds, defaults to 1000.
        """
        self._parent_item = parent_item
        self.src_item = src_item
        self.dst_item = dst_item
        font = QFont('Font Awesome 5 Free Solid')
        size = 0.875 * round(parent_item.rect().height() / 2)
        font.setPixelSize(size)
        self.src_item.setFont(font)
        self.dst_item.setFont(font)
        self.src_opacity_effect = QGraphicsOpacityEffect()
        self.src_item.setGraphicsEffect(self.src_opacity_effect)
        self.dst_opacity_effect = QGraphicsOpacityEffect()
        self.dst_item.setGraphicsEffect(self.dst_opacity_effect)
        self.timer = QTimeLine()
        self.timer.setLoopCount(0)  # loop forever
        self.timer.setFrameRange(0, 10)
        self.timer.valueChanged.connect(self._handle_timer_value_changed)
        self.timer.setDuration(duration)
        self.src_animation = QGraphicsItemAnimation()
        self.src_animation.setItem(self.src_item)
        self.src_animation.setTimeLine(self.timer)
        self.dst_animation = QGraphicsItemAnimation()
        self.dst_animation.setItem(self.dst_item)
        self.dst_animation.setTimeLine(self.timer)

    @Slot(float)
    def _handle_timer_value_changed(self, value):
        self.src_opacity_effect.setOpacity(1.0 - 2 * value)
        self.dst_opacity_effect.setOpacity(2 * value - 1.0)

    def start(self):
        """Starts the animation."""
        rect = self._parent_item.rect()
        dx = self.src_item.boundingRect().width()
        dy = self.dst_item.boundingRect().height()
        rect.adjust(0, 0, -dx, -dy)
        src, dst = rect.topLeft(), rect.bottomRight()
        vec = dst - src
        self.src_item.setParentItem(self._parent_item)
        self.dst_item.setParentItem(self._parent_item)
        self.src_item.setPos(src)
        self.dst_item.setPos(src)
        self.src_opacity_effect.setOpacity(0.0)
        self.dst_opacity_effect.setOpacity(0.0)
        for i in range(100):
            step = i / 100.0
            self.src_animation.setPosAt(step, src + vec * step)
            self.dst_animation.setPosAt(step, src + vec * step)
        self.timer.start()

    def stop(self):
        """Stops the animation"""
        self.timer.stop()
        self.src_item.setParentItem(None)
        self.dst_item.setParentItem(None)
        self.src_item.scene().removeItem(self.src_item)
        self.dst_item.scene().removeItem(self.dst_item)
        self.timer.setCurrentTime(999)
