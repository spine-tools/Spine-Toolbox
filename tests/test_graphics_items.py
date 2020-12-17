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
Unit tests for ``graphics_items`` module.

:authors: A. Soininen (VTT)
:date:    17.12.2020
"""
import unittest
from PySide2.QtCore import QEvent, Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from spinetoolbox.graphics_items import ProjectItemIcon, Link
from spinetoolbox.project_commands import MoveIconCommand
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestProjectItemIcon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._toolbox = create_toolboxui_with_project()

    def tearDown(self):
        clean_up_toolboxui_with_project(self._toolbox)

    def test_init(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        self.assertEqual(icon.name(), "")
        self.assertEqual(icon.x(), 0)
        self.assertEqual(icon.y(), 0)
        self.assertIn(icon, self._toolbox.ui.graphicsView.scene().items())
        self.assertEqual(icon.incoming_links(), [])
        self.assertEqual(icon.outgoing_links(), [])

    def test_finalize(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        icon.finalize("new name", -43, 314)
        self.assertEqual(icon.name(), "new name")
        self.assertEqual(icon.x(), -43)
        self.assertEqual(icon.y(), 314)

    def test_conn_button(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        button = icon.conn_button("left")
        self.assertEqual(button.position, "left")
        button = icon.conn_button("right")
        self.assertEqual(button.position, "right")
        button = icon.conn_button("bottom")
        self.assertEqual(button.position, "bottom")

    def test_outgoing_and_incoming_links(self):
        source_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        target_icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        link = Link(self._toolbox, source_icon.conn_button("bottom"), target_icon.conn_button("bottom"))
        link.src_connector.links.append(link)
        link.dst_connector.links.append(link)
        self.assertEqual(source_icon.outgoing_links(), [link])
        self.assertEqual(target_icon.incoming_links(), [link])

    def test_drag_icon(self):
        icon = ProjectItemIcon(self._toolbox, "", QColor(Qt.gray), QColor(Qt.green))
        self.assertEqual(icon.x(), 0.0)
        self.assertEqual(icon.y(), 0.0)
        icon.mousePressEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMousePress))
        icon.mouseMoveEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseMove))
        icon.moveBy(99.0, 88.0)
        icon.mouseReleaseEvent(QGraphicsSceneMouseEvent(QEvent.GraphicsSceneMouseRelease))
        self.assertEqual(icon.x(), 99.0)
        self.assertEqual(icon.y(), 88.0)
        self.assertEqual(self._toolbox.undo_stack.count(), 1)
        move_command = self._toolbox.undo_stack.command(0)
        self.assertIsInstance(move_command, MoveIconCommand)


if __name__ == "__main__":
    unittest.main()
