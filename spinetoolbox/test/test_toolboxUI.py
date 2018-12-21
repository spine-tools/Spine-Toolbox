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
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import SIGNAL
from ui_main import ToolboxUI
from project import SpineToolboxProject


class TestToolboxUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Overridden method. Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project so
        we need to mock CONFIGURATION_FILE to prevent loading user's own configs from settings.conf.
        """
        with mock.patch("ui_main.CONFIGURATION_FILE") as mocked_file_path, \
                mock.patch("os.path.split") as mock_split, \
                mock.patch("configuration.create_dir") as mock_create_dir:
            # # Set logging level to Error to silence "Logging level: All messages" print
            logging.disable(level=logging.ERROR)  # Disable logging
            self.mw = ToolboxUI()
            logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.mw = None

    def test_init_project_item_model_without_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done without a project open.
        """
        self.assertIsNone(self.mw.project())  # Make sure that there is no project open
        self.mw.init_project_item_model()
        self.check_init_project_item_model()

    def test_init_project_item_model_with_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done with a project.
        Mock save_project() and create_dir() so that .proj file and project directory (and work directory) are
        not actually created. Looks like CONFIGURATION_FILE needs to be mocked as well because it only stays
        mocked for the duration of with statement.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("ui_main.CONFIGURATION_FILE") as mock_confs:
            self.mw.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.mw.project(), SpineToolboxProject)  # Check that a project is open
        self.mw.init_project_item_model()
        self.check_init_project_item_model()

    def check_init_project_item_model(self):
        n = self.mw.project_item_model.rowCount()
        self.assertEqual(n, 4)
        # Check that there's only one column
        self.assertEqual(self.mw.project_item_model.columnCount(), 1)
        # Check that the items DisplayRoles are (In this particular order)
        item1 = self.mw.project_item_model.root().child(0)
        self.assertTrue(item1.name == "Data Stores", "Item on row 0 is not 'Data Stores'")
        self.assertTrue(item1.parent().is_root, "Parent item of category item on row 0 should be root")
        item2 = self.mw.project_item_model.root().child(1)
        self.assertTrue(item2.name == "Data Connections", "Item on row 1 is not 'Data Connections'")
        self.assertTrue(item2.parent().is_root, "Parent item of category item on row 1 should be root")
        item3 = self.mw.project_item_model.root().child(2)
        self.assertTrue(item3.name == "Tools", "Item on row 2 is not 'Tools'")
        self.assertTrue(item3.parent().is_root, "Parent item of category item on row 2 should be root")
        item4 = self.mw.project_item_model.root().child(3)
        self.assertTrue(item4.name == "Views", "Item on row 3 is not 'Views'")
        self.assertTrue(item4.parent().is_root, "Parent item of category item on row 3 should be root")

    def test_init_tool_template_model(self):
        """Check that tool template model only has the "No Tool" string and that
        signals are connected just once.
        """
        self.assertIsNone(self.mw.project())  # Make sure that there is no project open
        self.mw.init_tool_template_model(list())
        self.assertEqual(self.mw.tool_template_model.rowCount(), 1)
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.mw.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.mw.ui.listView_tool_templates.receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        self.assertEqual(n_context_menu_recv, 1)
        # Initialize ToolTemplateModel again and see that the signals are connected only once
        self.mw.init_tool_template_model(list())
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.mw.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.mw.ui.listView_tool_templates.receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        self.assertEqual(n_context_menu_recv, 1)
        # Check that there's still just one item in the model
        self.assertEqual(self.mw.tool_template_model.rowCount(), 1)

    def test_init_connection_model(self):
        """Test that ConnectionModel is empty when initialized."""
        self.assertIsNone(self.mw.project())  # Make sure that there is no project open
        self.mw.init_connection_model()
        rows = self.mw.connection_model.rowCount()
        columns = self.mw.connection_model.columnCount()
        self.assertEqual(rows, 0)
        self.assertEqual(columns, 0)

    def test_create_project(self):
        """Test that method makes a SpineToolboxProject instance.
        Skips creating a .proj file and creating directories.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("ui_main.CONFIGURATION_FILE") as mock_confs:
            self.mw.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.mw.project(), SpineToolboxProject)  # Check that a project is open

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
