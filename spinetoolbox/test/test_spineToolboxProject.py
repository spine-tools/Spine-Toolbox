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
Unit tests for SpineToolboxProject class.

:author: P. Savolainen (VTT)
:date:   14.11.2018
"""

import unittest
from unittest import mock
import logging
import sys
from ui_main import ToolboxUI


class TestSpineToolboxProject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project so
        we need to mock CONFIGURATION_FILE to prevent loading user's own configs from settings.conf.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("ui_main.CONFIGURATION_FILE") as mock_confs, \
                mock.patch("os.path.split") as mock_split, \
                mock.patch("configuration.create_dir") as mock_create_dir2:
            # logging.disable(level=logging.ERROR)  # Disable logging
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")
            # logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        self.toolbox = None

    def test_add_data_store(self):
        """Test adding a Data Store to project."""
        name = self.add_ds()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Store
        self.assertEqual(found_item.item_type, "Data Store")
        # Check that connection model has been updated
        self.assertEqual(self.toolbox.connection_model.rowCount(), 1)
        self.assertEqual(self.toolbox.connection_model.columnCount(), 1)
        self.assertEqual(self.toolbox.connection_model.find_index_in_header(name), 0)

    def test_add_data_connection(self):
        """Test adding a Data Connection to project."""
        name = self.add_dc()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Connection
        self.assertEqual(found_item.item_type, "Data Connection")
        # Check that connection model has been updated
        self.assertEqual(self.toolbox.connection_model.rowCount(), 1)
        self.assertEqual(self.toolbox.connection_model.columnCount(), 1)
        self.assertEqual(self.toolbox.connection_model.find_index_in_header(name), 0)

    def test_add_tool(self):
        """Test adding a Tool to project."""
        name = self.add_tool()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Tool
        self.assertEqual(found_item.item_type, "Tool")
        # Check that connection model has been updated
        self.assertEqual(self.toolbox.connection_model.rowCount(), 1)
        self.assertEqual(self.toolbox.connection_model.columnCount(), 1)
        self.assertEqual(self.toolbox.connection_model.find_index_in_header(name), 0)

    def test_add_view(self):
        """Test adding a View to project."""
        name = self.add_view()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a View
        self.assertEqual(found_item.item_type, "View")
        # Check that connection model has been updated
        self.assertEqual(self.toolbox.connection_model.rowCount(), 1)
        self.assertEqual(self.toolbox.connection_model.columnCount(), 1)
        self.assertEqual(self.toolbox.connection_model.find_index_in_header(name), 0)

    def test_add_four_items(self):
        """Test that adding multiple item works as expected. Four items are added in order DS->DC->Tool->View."""

        # Add items
        ds_name = self.add_ds()
        dc_name = self.add_dc()
        tool_name = self.add_tool()
        view_name = self.add_view()
        # Check that the items are found from project item model
        ds = self.toolbox.project_item_model.project_item(self.toolbox.project_item_model.find_item(ds_name))
        self.assertEqual(ds.name, ds_name)
        dc = self.toolbox.project_item_model.project_item(self.toolbox.project_item_model.find_item(dc_name))
        self.assertEqual(dc.name, dc_name)
        tool = self.toolbox.project_item_model.project_item(self.toolbox.project_item_model.find_item(tool_name))
        self.assertEqual(tool.name, tool_name)
        view = self.toolbox.project_item_model.project_item(self.toolbox.project_item_model.find_item(view_name))
        self.assertEqual(view.name, view_name)
        # Connection model should now have four rows and four columns
        self.assertEqual(self.toolbox.connection_model.rowCount(), 4)
        self.assertEqual(self.toolbox.connection_model.columnCount(), 4)
        # Check that the names match in connection model
        self.assertEqual(self.toolbox.connection_model.find_index_in_header(ds_name), 0)

        # # Add Data Connection item
        # dc_name = "DC"
        # with mock.patch("data_connection.create_dir") as mock_create_dir:
        #     dc_item = DataConnection(self.mw, dc_name, "", references=None, x=0, y=0)
        # retval = self.mw.add_item_to_model("Data Connections", dc_name, dc_item)
        # self.assertTrue(retval)
        # # Check that new item is found from project_item_model
        # found_item = self.mw.project_item_model.find_item(dc_name, Qt.MatchExactly | Qt.MatchRecursive)
        # self.assertEqual(found_item.data(Qt.UserRole), dc_item)
        # # Check that connection model has been updated
        # self.assertEqual(self.mw.connection_model.rowCount(), 2)
        # self.assertEqual(self.mw.connection_model.columnCount(), 2)
        # self.assertEqual(self.mw.connection_model.find_index_in_header(dc_name), 1)
        #
        # # Add Tool item
        # tool_name = "Tool"
        # with mock.patch("tool.create_dir") as mock_create_dir:
        #     tool_item = Tool(self.mw, tool_name, "", tool_template=None, x=0, y=0)
        # retval = self.mw.add_item_to_model("Tools", tool_name, tool_item)
        # self.assertTrue(retval)
        # # Check that new item is found from project_item_model
        # found_item = self.mw.project_item_model.find_item(tool_name, Qt.MatchExactly | Qt.MatchRecursive)
        # self.assertEqual(found_item.data(Qt.UserRole), tool_item)
        # # Check that connection model has been updated
        # self.assertEqual(self.mw.connection_model.rowCount(), 3)
        # self.assertEqual(self.mw.connection_model.columnCount(), 3)
        # self.assertEqual(self.mw.connection_model.find_index_in_header(tool_name), 2)
        #
        # # Add View item
        # view_name = "View"
        # view_item = View(self.mw, view_name, "", 0, 0)
        # retval = self.mw.add_item_to_model("Views", view_name, view_item)
        # self.assertTrue(retval)
        # # Check that new item is found from project_item_model
        # found_item = self.mw.project_item_model.find_item(view_name, Qt.MatchExactly | Qt.MatchRecursive)
        # self.assertEqual(found_item.data(Qt.UserRole), view_item)
        # # Check that connection model has been updated
        # self.assertEqual(self.mw.connection_model.rowCount(), 4)
        # self.assertEqual(self.mw.connection_model.columnCount(), 4)
        # self.assertEqual(self.mw.connection_model.find_index_in_header(view_name), 3)
        # # There should now be 4 items in the model
        # self.assertEqual(self.mw.project_item_model.n_items("all"), 4)

    # def test_add_item_to_model_in_random_order(self):
    #     """Add items to model in order DC->View->Tool->DS and check that it still works."""
    #     self.fail()
    #
    # def test_change_name(self):
    #     self.fail()
    #
    # def test_set_description(self):
    #     self.fail()
    #
    # def test_change_filename(self):
    #     self.fail()
    #
    # def test_change_work_dir(self):
    #     self.fail()
    #
    # def test_rename_project(self):
    #     self.fail()
    #
    # def test_save(self):
    #     self.fail()
    #
    # def test_load(self):
    #     self.fail()
    #
    # def test_load_tool_template_from_file(self):
    #     self.fail()
    #
    # def test_load_tool_template_from_dict(self):
    #     self.fail()
    #
    # def test_append_connection_model(self):
    #     self.fail()
    #
    # def test_set_item_selected(self):
    #     self.fail()

    def add_ds(self):
        """Helper method to add Data Store. Returns created items name."""
        with mock.patch("data_store.create_dir") as mock_create_dir:
            self.toolbox.project().add_data_store("DS", "", reference=None)
        return "DS"

    def add_dc(self):
        """Helper method to add Data Connection. Returns created items name."""
        with mock.patch("data_connection.create_dir") as mock_create_dir:
            self.toolbox.project().add_data_connection("DC", "", references=list())
        return "DC"

    def add_tool(self):
        """Helper method to add Tool. Returns created items name."""
        with mock.patch("tool.create_dir") as mock_create_dir:
            self.toolbox.project().add_tool("tool", "", tool_template=None)
        return "tool"

    def add_view(self):
        """Helper method to add View. Returns created items name."""
        with mock.patch("view.create_dir") as mock_create_dir:
            self.toolbox.project().add_view("view", "")
        return "view"


if __name__ == '__main__':
    unittest.main()
