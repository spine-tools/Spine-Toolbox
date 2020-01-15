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
Unit tests for ShrinkingScene.

:author: A. Soininen (VTT)
:date:   18.10.2019
"""

import unittest
from PySide2.QtCore import QRectF
from PySide2.QtWidgets import QApplication, QGraphicsRectItem
from spinetoolbox.widgets.shrinking_scene import ShrinkingScene


class TestShrinkingScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        horizontal_threshold = 1.0
        vertical_threshold = 3.0
        self.scene = ShrinkingScene(horizontal_threshold, vertical_threshold, None)
        item_size = 1.0
        self.fixed_item = QGraphicsRectItem(0.0, 0.0, item_size, item_size)
        self.item = QGraphicsRectItem(0.0, 0.0, item_size, item_size)
        self.item.setPos(10.0, 10.0)
        self.scene.addItem(self.fixed_item)
        self.scene.addItem(self.item)
        self.assertEqual(self.scene.sceneRect(), QRectF(-0.5, -0.5, 12.0, 12.0))

    def test_shrink_if_needed_doesnt_shrink_within_thresholds(self):
        self.item.setPos(9.1, 7.1)
        self.scene.shrink_if_needed()
        self.assertEqual(self.scene.sceneRect(), QRectF(-0.5, -0.5, 12.0, 12.0))

    def test_shrink_if_needed(self):
        self.item.setPos(8.9, 6.1)
        self.scene.shrink_if_needed()
        self.assertEqual(self.scene.sceneRect(), QRectF(-0.5, -0.5, 11.9, 11.1))

    def test_shrink_if_needed_doesnt_shink_too_much(self):
        self.item.setPos(0.0, 0.0)
        self.scene.shrink_if_needed()
        self.assertEqual(self.scene.sceneRect(), QRectF(-0.5, -0.5, 3.0, 5.0))


if __name__ == '__main__':
    unittest.main()
