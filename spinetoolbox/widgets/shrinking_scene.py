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
A QGraphicsScene that can shrink sometimes.

:author: A. Soininen (VTT)
:date:   18.10.2019
"""

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QGraphicsScene


class ShrinkingScene(QGraphicsScene):
    """
    A QGraphicsScene class that can shrinks its scene rectangle.

    Shrinking can be triggered by shrink_if_needed(). It is controlled by two threshold values
    which control how far the items need to be from the scene rectangle's edges
    to trigger the shrinking.
    """

    item_move_finished = Signal("QGraphicsItem")
    """Emitted when an item has finished moving."""

    shrinking_requested = Signal()
    """Emitted when shrinking is requested."""

    def __init__(self, horizontal_shrinking_threshold, vertical_shrinking_threshold, parent):
        """
        Args:
            horizontal_shrinking_threshold (float): horizontal threshold before the scene is shrank
            vertical_shrinking_threshold (float): vertical threshold before the scene is shrank
            parent (QObject): a parent
        """
        super().__init__(parent)
        self._horizontal_threshold = horizontal_shrinking_threshold
        self._vertical_threshold = vertical_shrinking_threshold

    def shrink_if_needed(self):
        """Emits shrinking_requested signal."""
        self.shrinking_requested.emit()
