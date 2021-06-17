######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the jump properties widget.

:authors: A. Soininen (VTT)
:date:    6.7.2021
"""
from tempfile import TemporaryDirectory
import unittest
from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import QApplication
from spine_items.data_connection.data_connection import DataConnection
from spine_engine.project_item.connection import Connection, Jump
from spinetoolbox.widgets.jump_properties_widget import JumpPropertiesWidget
from spinetoolbox.link import JumpLink
from tests.mock_helpers import clean_up_toolbox, create_toolboxui_with_project


class TestJumpPropertiesWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_properties_widget_in_toolbox(self):
        tab_widget = self._toolbox.ui.tabWidget_item_properties
        widget_count = 0
        for i in range(tab_widget.count()):
            widget = tab_widget.widget(i)
            if isinstance(widget, JumpPropertiesWidget):
                widget_count += 1
                self.assertEqual(tab_widget.tabText(i), "Loop properties")
        self.assertEqual(widget_count, 1)

    def test_set_link(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        self.assertEqual(properties_widget._ui.condition_edit.toPlainText(), "exit(23)")

    def test_unset_link(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        self.assertEqual(properties_widget._ui.condition_edit.toPlainText(), "exit(23)")
        properties_widget.unset_link()
        self.assertEqual(properties_widget._ui.condition_edit.toPlainText(), "")

    def test_edit_condition(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        cursor = properties_widget._ui.condition_edit.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.removeSelectedText()
        cursor.insertText("exit(5)")
        self.assertEqual(properties_widget._ui.condition_edit.toPlainText(), "exit(5)")

    def _set_link(self, properties_widget):
        project = self._toolbox.project()
        item1 = DataConnection("dc 1", "", 0.0, 0.0, self._toolbox, project)
        item2 = DataConnection("dc 2", "", 50.0, 0.0, self._toolbox, project)
        project.add_item(item1)
        item1.set_up()
        project.add_item(item2)
        item2.set_up()
        project.add_connection(Connection("dc 1", "right", "dc 2", "left"))
        project.add_jump(Jump("dc 2", "bottom", "dc 1", "bottom", "exit(23)"))
        link = next(item for item in self._toolbox.ui.graphicsView.items() if isinstance(item, JumpLink))
        properties_widget.set_link(link)

    def _find_widget(self):
        tab_widget = self._toolbox.ui.tabWidget_item_properties
        for i in range(tab_widget.count()):
            widget = tab_widget.widget(i)
            if isinstance(widget, JumpPropertiesWidget):
                return widget
        return None


if __name__ == '__main__':
    unittest.main()
