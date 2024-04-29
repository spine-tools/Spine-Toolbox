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

"""Unit tests for the jump properties widget."""
from tempfile import TemporaryDirectory
import unittest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication
from spine_items.data_connection.data_connection import DataConnection
from spinetoolbox.project_item.logging_connection import LoggingConnection, LoggingJump
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
        widget_count = 0
        for widget in self._toolbox.link_properties_widgets.values():
            if isinstance(widget, JumpPropertiesWidget):
                widget_count += 1
        self.assertEqual(widget_count, 1)

    def test_set_link(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        self.assertEqual(properties_widget._ui.condition_script_edit.toPlainText(), "exit(23)")

    def test_unset_link(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        self.assertEqual(properties_widget._ui.condition_script_edit.toPlainText(), "exit(23)")
        QApplication.processEvents()
        properties_widget.unset_link()
        self.assertEqual(properties_widget._ui.condition_script_edit.toPlainText(), "exit(23)")

    def test_edit_condition(self):
        properties_widget = self._find_widget()
        self._set_link(properties_widget)
        cursor = properties_widget._ui.condition_script_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.removeSelectedText()
        cursor.insertText("exit(5)")
        self.assertEqual(properties_widget._ui.condition_script_edit.toPlainText(), "exit(5)")

    def _set_link(self, properties_widget):
        project = self._toolbox.project()
        item1 = DataConnection("dc 1", "", 0.0, 0.0, self._toolbox, project)
        item2 = DataConnection("dc 2", "", 50.0, 0.0, self._toolbox, project)
        project.add_item(item1)
        project.add_item(item2)
        project.add_connection(LoggingConnection("dc 1", "right", "dc 2", "left", toolbox=self._toolbox))
        project.add_jump(
            LoggingJump(
                "dc 2",
                "bottom",
                "dc 1",
                "bottom",
                {"type": "python-script", "script": "exit(23)", "specification": ""},
                toolbox=self._toolbox,
            )
        )
        link = next(item for item in self._toolbox.ui.graphicsView.items() if isinstance(item, JumpLink))
        properties_widget.set_link(link.item)

    def _find_widget(self):
        for widget in self._toolbox.link_properties_widgets.values():
            if isinstance(widget, JumpPropertiesWidget):
                return widget
        return None


if __name__ == "__main__":
    unittest.main()
