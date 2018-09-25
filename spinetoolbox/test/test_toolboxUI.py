#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Unit tests for ToolboxUI class.

:author: P. Savolainen (VTT)
:date:   22.8.2018
"""

import unittest
from unittest import mock
import logging
import os
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, SIGNAL
from ui_main import ToolboxUI
from project import SpineToolboxProject
from data_store import DataStore
from data_connection import DataConnection
from tool import Tool
from view import View


class TestToolboxUI(unittest.TestCase):

    app = QApplication()  # QApplication must be instantiated here unless you want a segmentation fault

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Overridden method. Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project so
        we need to mock CONFIGURATION_FILE to prevent loading user's own configs from settings.conf.
        """
        with mock.patch('ui_main.CONFIGURATION_FILE') as mocked_file_path:
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
        item1 = self.mw.project_item_model.item(0, 0)
        self.assertTrue(item1.data(Qt.DisplayRole) == "Data Stores", "Item (0,0) is not 'Data Stores'")
        self.assertFalse(item1.index().parent().isValid(), "Parent index of item (0,0) is valid. Should be invalid.")
        item2 = self.mw.project_item_model.item(1, 0)
        self.assertTrue(item2.data(Qt.DisplayRole) == "Data Connections", "Item (1,0) is not 'Data Connections'")
        self.assertFalse(item2.index().parent().isValid(), "Parent index of item (1,0) is valid. Should be invalid.")
        item3 = self.mw.project_item_model.item(2, 0)
        self.assertTrue(item3.data(Qt.DisplayRole) == "Tools", "Item (2,0) is not 'Tools'")
        self.assertFalse(item3.index().parent().isValid(), "Parent index of item (0,0) is valid. Should be invalid.")
        item4 = self.mw.project_item_model.item(3, 0)
        self.assertTrue(item4.data(Qt.DisplayRole) == "Views", "Item (3,0) is not 'Views'")
        self.assertFalse(item4.index().parent().isValid(), "Parent index of item (0,0) is valid. Should be invalid.")

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

    def test_add_item_to_model(self):
        """Test that adding items works as expected. Four items are added in order DS->DC->Tool->View.
        NOTE: ToolboxUI project_refs list is updated in SpineToolboxProject add_data_store() method
        TODO: Update project_refs list in add_item_model() method
        """
        # Create project
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("ui_main.CONFIGURATION_FILE") as mock_confs:
            self.mw.create_project("Unit Test Project", "Project for unit tests.")

        # Add Data Store item
        ds_name = "DS"
        with mock.patch("data_store.create_dir") as mock_create_dir:
            ds_item = DataStore(self.mw, ds_name, "", references=None, x=0, y=0)
        retval = self.mw.add_item_to_model("Data Stores", ds_name, ds_item)
        self.assertTrue(retval)
        # Check that new item is found from project_item_model
        found_item = self.mw.project_item_model.find_item(ds_name, Qt.MatchExactly | Qt.MatchRecursive)  # QStandardItem
        self.assertEqual(found_item.data(Qt.UserRole), ds_item)
        # Check that connection model has been updated
        self.assertEqual(self.mw.connection_model.rowCount(), 1)
        self.assertEqual(self.mw.connection_model.columnCount(), 1)
        self.assertEqual(self.mw.connection_model.find_index_in_header(ds_name), 0)

        # Add Data Connection item
        dc_name = "DC"
        with mock.patch("data_connection.create_dir") as mock_create_dir:
            dc_item = DataConnection(self.mw, dc_name, "", references=None, x=0, y=0)
        retval = self.mw.add_item_to_model("Data Connections", dc_name, dc_item)
        self.assertTrue(retval)
        # Check that new item is found from project_item_model
        found_item = self.mw.project_item_model.find_item(dc_name, Qt.MatchExactly | Qt.MatchRecursive)
        self.assertEqual(found_item.data(Qt.UserRole), dc_item)
        # Check that connection model has been updated
        self.assertEqual(self.mw.connection_model.rowCount(), 2)
        self.assertEqual(self.mw.connection_model.columnCount(), 2)
        self.assertEqual(self.mw.connection_model.find_index_in_header(dc_name), 1)

        # Add Tool item
        tool_name = "Tool"
        with mock.patch("tool.create_dir") as mock_create_dir:
            tool_item = Tool(self.mw, tool_name, "", tool_template=None, x=0, y=0)
        retval = self.mw.add_item_to_model("Tools", tool_name, tool_item)
        self.assertTrue(retval)
        # Check that new item is found from project_item_model
        found_item = self.mw.project_item_model.find_item(tool_name, Qt.MatchExactly | Qt.MatchRecursive)
        self.assertEqual(found_item.data(Qt.UserRole), tool_item)
        # Check that connection model has been updated
        self.assertEqual(self.mw.connection_model.rowCount(), 3)
        self.assertEqual(self.mw.connection_model.columnCount(), 3)
        self.assertEqual(self.mw.connection_model.find_index_in_header(tool_name), 2)

        # Add View item
        view_name = "View"
        with mock.patch("view.create_dir") as mock_create_dir:
            view_item = View(self.mw, view_name, "", 0, 0)
        retval = self.mw.add_item_to_model("Views", view_name, view_item)
        self.assertTrue(retval)
        # Check that new item is found from project_item_model
        found_item = self.mw.project_item_model.find_item(view_name, Qt.MatchExactly | Qt.MatchRecursive)
        self.assertEqual(found_item.data(Qt.UserRole), view_item)
        # Check that connection model has been updated
        self.assertEqual(self.mw.connection_model.rowCount(), 4)
        self.assertEqual(self.mw.connection_model.columnCount(), 4)
        self.assertEqual(self.mw.connection_model.find_index_in_header(view_name), 3)
        # There should now be 4 items in the model
        self.assertEqual(self.mw.project_item_model.n_items("all"), 4)

    @unittest.skip("TODO")
    def test_add_item_to_model_in_random_order(self):
        """Add items to model in order DC->View->Tool->DS and check that it still works."""
        self.fail()

    @unittest.skip("TODO")
    def test_remove_item(self):
        self.fail()

    @unittest.skip("TODO")
    def test_add_tool_template(self):
        self.fail()

    @unittest.skip("TODO")
    def test_reattach_tool_templates(self):
        self.fail()

    @unittest.skip("TODO")
    def test_remove_tool_template(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()
