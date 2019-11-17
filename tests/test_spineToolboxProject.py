######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
from PySide2.QtCore import QItemSelectionModel, QVariantAnimation
from PySide2.QtWidgets import QApplication
from spinetoolbox.executioner import ExecutionState
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


# noinspection PyUnusedLocal
class TestSpineToolboxProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
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
        """Runs before each test. Makes an instance of ToolboxUI class."""
        self.toolbox = create_toolboxui_with_project()

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolboxui_with_project(self.toolbox)

    def test_add_data_store(self):
        """Test adding a Data Store to project."""
        name = self.add_ds()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Store
        self.assertEqual(found_item.item_type(), "Data Store")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def check_dag_handler(self, name):
        """Check that project dag handler contains only one
        graph, which has one node and its name matches the
        given argument."""
        dag = self.toolbox.project().dag_handler
        self.assertTrue(len(dag.dags()) == 1)
        g = dag.dag_with_node(name)
        self.assertTrue(len(g.nodes()) == 1)
        for node_name in g.nodes():
            self.assertTrue(node_name == name)

    def test_add_data_connection(self):
        """Test adding a Data Connection to project."""
        name = self.add_dc()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Connection
        self.assertEqual(found_item.item_type(), "Data Connection")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_tool(self):
        """Test adding a Tool to project."""
        name = self.add_tool()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Tool
        self.assertEqual(found_item.item_type(), "Tool")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_view(self):
        """Test adding a View to project."""
        name = self.add_view()
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.project_item(found_index)
        self.assertEqual(found_item.name, name)
        # Check that the created item is a View
        self.assertEqual(found_item.item_type(), "View")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_four_items(self):
        """Test that adding multiple items works as expected.
        Four items are added in order DS->DC->Tool->View."""

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
        # DAG handler should now have four graphs, each with one item
        dag_hndlr = self.toolbox.project().dag_handler
        n_dags = len(dag_hndlr.dags())
        self.assertEqual(n_dags, 4)
        # Check that all previously created items are found in graphs
        ds_graph = dag_hndlr.dag_with_node(ds_name)  # Returns None if graph is not found
        self.assertIsNotNone(ds_graph)
        dc_graph = dag_hndlr.dag_with_node(dc_name)
        self.assertIsNotNone(dc_graph)
        tool_graph = dag_hndlr.dag_with_node(tool_name)
        self.assertIsNotNone(tool_graph)
        view_graph = dag_hndlr.dag_with_node(view_name)
        self.assertIsNotNone(view_graph)

    def test_execute_project_with_single_item(self):
        item_name = self.add_tool()
        item_index = self.toolbox.project_item_model.find_item(item_name)
        item = self.toolbox.project_item_model.project_item(item_index)
        item._do_execute = mock.MagicMock(return_value=ExecutionState.CONTINUE)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().execute_project()
        qApp.processEvents()
        item._do_execute.assert_called_with([], [])

    def test_execute_project_with_two_dags(self):
        item1_name = self.add_tool()
        item1_index = self.toolbox.project_item_model.find_item(item1_name)
        item1 = self.toolbox.project_item_model.project_item(item1_index)
        item1._do_execute = mock.MagicMock(return_value=ExecutionState.CONTINUE)
        item2_name = self.add_view()
        item2_index = self.toolbox.project_item_model.find_item(item2_name)
        item2 = self.toolbox.project_item_model.project_item(item2_index)
        item2._do_execute = mock.MagicMock(return_value=ExecutionState.CONTINUE)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item1.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        item2.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().execute_project()
        # We have to process events for each item that gets executed
        qApp.processEvents()
        qApp.processEvents()
        item1._do_execute.assert_called_with([], [])
        item2._do_execute.assert_called_with([], [])

    def test_execute_selected(self):
        item1_name = self.add_tool()
        item1_index = self.toolbox.project_item_model.find_item(item1_name)
        item1 = self.toolbox.project_item_model.project_item(item1_index)
        item1._do_execute = mock.MagicMock(return_value=ExecutionState.CONTINUE)
        item2_name = self.add_view()
        item2_index = self.toolbox.project_item_model.find_item(item2_name)
        item2 = self.toolbox.project_item_model.project_item(item2_index)
        item2._do_execute = mock.MagicMock(return_value=ExecutionState.CONTINUE)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item1.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        item2.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.ui.treeView_project.selectionModel().select(item2_index, QItemSelectionModel.Select)
        self.toolbox.project().execute_selected()
        qApp.processEvents()
        item1._do_execute.assert_not_called()
        item2._do_execute.assert_called_with([], [])

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
    # def test_load_tool_specification_from_file(self):
    #     self.fail()
    #
    # def test_load_tool_specification_from_dict(self):
    #     self.fail()
    #
    # def test_append_connection_model(self):
    #     self.fail()
    #
    # def test_set_item_selected(self):
    #     self.fail()

    def add_ds(self):
        """Helper method to add Data Store. Returns created items name."""
        item = dict(name="DS", description="", url=dict(), x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Data Stores", item)
        return "DS"

    def add_dc(self):
        """Helper method to add Data Connection. Returns created items name."""
        item = dict(name="DC", description="", references=list(), x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Data Connections", item)
        return "DC"

    def add_tool(self):
        """Helper method to add Tool. Returns created items name."""
        item = dict(name="tool", description="", tool="", execute_in_work=False, x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Tools", item)
        return "tool"

    def add_view(self):
        """Helper method to add View. Returns created items name."""
        item = dict(name="view", description="", x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Views", item)
        return "view"


if __name__ == '__main__':
    unittest.main()
