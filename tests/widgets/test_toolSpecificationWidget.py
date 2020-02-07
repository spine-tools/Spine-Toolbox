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
Unit tests for ToolSpecificationWidget class.

:author: M. Marin (KTH)
:date:   8.1.2019
"""

import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
from spinetoolbox.widgets.tool_specification_widget import ToolSpecificationWidget
from ..mock_helpers import create_toolboxui


class MockQWidget(QWidget):
    def __init__(self):
        super().__init__()

    # noinspection PyMethodMayBeStatic
    def test_push_vars(self):
        return True


class TestToolSpecificationWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test."""
        self.toolbox = create_toolboxui()
        self.tool_specification_widget = ToolSpecificationWidget(self.toolbox)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tool_specification_widget.deleteLater()
        self.tool_specification_widget = None
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_create_minimal_tool_specification(self):
        """Test that a minimal tool specification can be created by specifying name, type and main program file."""
        with mock.patch("spinetoolbox.widgets.tool_specification_widget.QFileDialog") as mock_file_dialog, mock.patch(
            "spinetoolbox.widgets.tool_specification_widget.ToolSpecificationWidget.call_add_tool_specification"
        ) as mock_add, mock.patch(
            "spinetoolbox.widgets.tool_specification_widget.ToolSpecificationWidget.close"
        ) as mock_close:
            self.tool_specification_widget.ui.comboBox_tooltype.setCurrentIndex(1)
            self.tool_specification_widget.ui.lineEdit_name.setText("test_tool")
            self.tool_specification_widget.ui.lineEdit_main_program.setText(__file__)
            mock_file_dialog.getSaveFileName.return_value = ['test_tool.json']
            self.tool_specification_widget.ui.pushButton_ok.click()
        mock_add.assert_called_once()
        mock_close.assert_called_once()

    def test_add_cmdline_tag_url_inputs(self):
        self._test_add_cmdline_tag_on_empty_args_field("@@url_inputs@@")

    def test_add_cmdline_tag_url_inputs_middle_of_other_tags(self):
        self._test_add_cmdline_tag_middle_of_other_tags("@@url_inputs@@")

    def test_add_cmdline_tag_url_inputs_no_space_before_regular_arg(self):
        self._test_add_cmdline_tag_adds_no_space_before_regular_arg("@@url_inputs@@")

    def test_add_cmdline_tag_url_outputs(self):
        self._test_add_cmdline_tag_on_empty_args_field("@@url_outputs@@")

    def test_add_cmdline_tag_url_outputs_middle_of_other_tags(self):
        self._test_add_cmdline_tag_middle_of_other_tags("@@url_outputs@@")

    def test_add_cmdline_tag_url_outputs_no_space_before_regular_arg(self):
        self._test_add_cmdline_tag_adds_no_space_before_regular_arg("@@url_outputs@@")

    def test_add_cmdline_tag_data_store_url(self):
        self._test_add_cmdline_tag_on_empty_args_field("@@url:<data-store-name>@@")
        selection = self.tool_specification_widget.ui.lineEdit_args.selectedText()
        self.assertEqual(selection, "<data-store-name>")

    def test_add_cmdline_tag_data_store_url_middle_of_other_tags(self):
        self._test_add_cmdline_tag_middle_of_other_tags("@@url:<data-store-name>@@")
        selection = self.tool_specification_widget.ui.lineEdit_args.selectedText()
        self.assertEqual(selection, "<data-store-name>")

    def test_add_cmdline_tag_data_store_url_no_space_before_regular_arg(self):
        self._test_add_cmdline_tag_adds_no_space_before_regular_arg("@@url:<data-store-name>@@")
        selection = self.tool_specification_widget.ui.lineEdit_args.selectedText()
        self.assertEqual(selection, "<data-store-name>")

    def test_add_cmdline_tag_optional_inputs(self):
        self._test_add_cmdline_tag_on_empty_args_field("@@optional_inputs@@")

    def test_add_cmdline_tag_optional_inputs_middle_of_other_tags(self):
        self._test_add_cmdline_tag_middle_of_other_tags("@@optional_inputs@@")

    def test_add_cmdline_tag_optional_inputs_no_space_before_regular_arg(self):
        self._test_add_cmdline_tag_adds_no_space_before_regular_arg("@@optional_inputs@@")

    def _find_action(self, action_text, actions):
        found_action = None
        for action in actions:
            if action.text() == action_text:
                found_action = action
                break
        self.assertIsNotNone(found_action)
        return found_action

    def _test_add_cmdline_tag_on_empty_args_field(self, tag):
        menu = self.tool_specification_widget.ui.toolButton_add_cmdline_tag.menu()
        url_inputs_action = self._find_action(tag, menu.actions())
        url_inputs_action.trigger()
        args = self.tool_specification_widget.ui.lineEdit_args.text()
        expected = tag + " "
        self.assertEqual(args, expected)
        if not self.tool_specification_widget.ui.lineEdit_args.hasSelectedText():
            cursor_position = self.tool_specification_widget.ui.lineEdit_args.cursorPosition()
            self.assertEqual(cursor_position, len(expected))

    def _test_add_cmdline_tag_middle_of_other_tags(self, tag):
        self.tool_specification_widget.ui.lineEdit_args.setText("@@optional_inputs@@@@url_outputs@@")
        self.tool_specification_widget.ui.lineEdit_args.setCursorPosition(len("@@optional_inputs@@"))
        menu = self.tool_specification_widget.ui.toolButton_add_cmdline_tag.menu()
        url_inputs_action = self._find_action(tag, menu.actions())
        url_inputs_action.trigger()
        args = self.tool_specification_widget.ui.lineEdit_args.text()
        self.assertEqual(args, f"@@optional_inputs@@ {tag} @@url_outputs@@")
        if not self.tool_specification_widget.ui.lineEdit_args.hasSelectedText():
            cursor_position = self.tool_specification_widget.ui.lineEdit_args.cursorPosition()
            self.assertEqual(cursor_position, len(f"@@optional_inputs@@ {tag} "))

    def _test_add_cmdline_tag_adds_no_space_before_regular_arg(self, tag):
        self.tool_specification_widget.ui.lineEdit_args.setText("--tag=")
        self.tool_specification_widget.ui.lineEdit_args.setCursorPosition(len("--tag="))
        menu = self.tool_specification_widget.ui.toolButton_add_cmdline_tag.menu()
        url_inputs_action = self._find_action(tag, menu.actions())
        url_inputs_action.trigger()
        args = self.tool_specification_widget.ui.lineEdit_args.text()
        self.assertEqual(args, f"--tag={tag} ")
        if not self.tool_specification_widget.ui.lineEdit_args.hasSelectedText():
            cursor_position = self.tool_specification_widget.ui.lineEdit_args.cursorPosition()
            self.assertEqual(cursor_position, len(f"--tag={tag} "))


if __name__ == '__main__':
    unittest.main()
