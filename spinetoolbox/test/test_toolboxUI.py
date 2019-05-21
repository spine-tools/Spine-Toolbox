######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for ToolboxUI class.

:author: P. Savolainen (VTT)
:date:   22.8.2018
"""

import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import SIGNAL
from ui_main import ToolboxUI
from project import SpineToolboxProject


class MockQWidget(QWidget):
    def __init__(self):
        super().__init__()

    # noinspection PyMethodMayBeStatic
    def test_push_vars(self):
        return True


# noinspection PyUnusedLocal
class TestToolboxUI(unittest.TestCase):
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
        """Overridden method. Runs before each test. Makes an instance of ToolboxUI class."""
        with mock.patch("ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
            "ui_main.PythonReplWidget"
        ) as mock_python_repl, mock.patch("ui_main.ToolboxUI.init_project") as mock_init_project, mock.patch(
            "ui_main.ToolboxUI.restore_ui"
        ) as mock_restore_ui:
            # Replace Julia and Python REPLs with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()  # Hack, because QWidget does not have test_push_vars()
            self.toolbox = ToolboxUI()

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_init_project_item_model_without_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done without a project open.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_project_item_model()
        self.check_init_project_item_model()

    def test_init_project_item_model_with_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done with a project.
        Mock save_project() and create_dir() so that .proj file and project directory (and work directory) are
        not actually created. Looks like CONFIGURATION_FILE needs to be mocked as well because it only stays
        mocked for the duration of with statement.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, mock.patch(
            "project.create_dir"
        ) as mock_create_dir:
            self.toolbox.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open
        self.toolbox.init_project_item_model()
        self.check_init_project_item_model()

    def check_init_project_item_model(self):
        n = self.toolbox.project_item_model.rowCount()
        self.assertEqual(n, 4)
        # Check that there's only one column
        self.assertEqual(self.toolbox.project_item_model.columnCount(), 1)
        # Check that the items DisplayRoles are (In this particular order)
        item1 = self.toolbox.project_item_model.root().child(0)
        self.assertTrue(item1.name == "Data Stores", "Item on row 0 is not 'Data Stores'")
        self.assertTrue(item1.parent().is_root, "Parent item of category item on row 0 should be root")
        item2 = self.toolbox.project_item_model.root().child(1)
        self.assertTrue(item2.name == "Data Connections", "Item on row 1 is not 'Data Connections'")
        self.assertTrue(item2.parent().is_root, "Parent item of category item on row 1 should be root")
        item3 = self.toolbox.project_item_model.root().child(2)
        self.assertTrue(item3.name == "Tools", "Item on row 2 is not 'Tools'")
        self.assertTrue(item3.parent().is_root, "Parent item of category item on row 2 should be root")
        item4 = self.toolbox.project_item_model.root().child(3)
        self.assertTrue(item4.name == "Views", "Item on row 3 is not 'Views'")
        self.assertTrue(item4.parent().is_root, "Parent item of category item on row 3 should be root")

    def test_init_tool_template_model(self):
        """Check that tool template model has no items after init and that
        signals are connected just once.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_tool_template_model(list())
        self.assertEqual(self.toolbox.tool_template_model.rowCount(), 0)
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.toolbox.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.toolbox.ui.listView_tool_templates.receivers(
            SIGNAL("customContextMenuRequested(QPoint)")
        )
        self.assertEqual(n_context_menu_recv, 1)
        # Initialize ToolTemplateModel again and see that the signals are connected only once
        self.toolbox.init_tool_template_model(list())
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.toolbox.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.toolbox.ui.listView_tool_templates.receivers(
            SIGNAL("customContextMenuRequested(QPoint)")
        )
        self.assertEqual(n_context_menu_recv, 1)
        # Check that there's still no items in the model
        self.assertEqual(self.toolbox.tool_template_model.rowCount(), 0)

    def test_init_connection_model(self):
        """Test that ConnectionModel is empty when initialized."""
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_connection_model()
        rows = self.toolbox.connection_model.rowCount()
        columns = self.toolbox.connection_model.columnCount()
        self.assertEqual(rows, 0)
        self.assertEqual(columns, 0)

    def test_create_project(self):
        """Test that create_project method makes a SpineToolboxProject instance.
        Skips creating a .proj file and creating directories.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, mock.patch(
            "project.create_dir"
        ) as mock_create_dir:
            self.toolbox.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open

    @unittest.skip("TODO")
    def test_remove_item(self):
        self.fail()

    @unittest.skip("TODO")
    def test_add_tool_template(self):
        self.fail()

    @unittest.skip("TODO")
    def test_remove_tool_template(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()
