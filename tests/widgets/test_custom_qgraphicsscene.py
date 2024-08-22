######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for custom graphics scenes."""
from tempfile import TemporaryDirectory
import unittest
from PySide6.QtWidgets import QGraphicsRectItem
from spinetoolbox.widgets.custom_qgraphicsscene import CustomGraphicsScene
from tests.mock_helpers import TestCaseWithQApplication


class TestCustomGraphicsScene(TestCaseWithQApplication):
    def test_center_items(self):
        scene = CustomGraphicsScene()
        rect = scene.addRect(-120.0, 66.0, 1.0, 1.0)
        child_rect = QGraphicsRectItem(23.3, -5.5, 0.3, 0.3, rect)  # pylint: disable=unused-variable
        scene.center_items()
        self.assertEqual(scene.itemsBoundingRect(), scene.sceneRect())
        scene.deleteLater()


if __name__ == "__main__":
    unittest.main()
